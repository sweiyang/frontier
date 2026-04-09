"""Agent stream processor and saving messages logic."""

import asyncio
import json

from core.agent.connectors import get_connector
from core.agent.connectors.schema import MetadataUser
from core.db import db_chat
from core.logging import get_logger
from core.utils.token_counter import estimate_tokens, estimate_tokens_for_messages

logger = get_logger(__name__)


def to_stream_events(data) -> str:
    """Convert connector output (str or dict) to NDJSON lines for the frontend.

    Connectors yield either plain text (str) or a structured dict with optional
    keys: content, elements, file. This function turns them into typed events.
    """
    if isinstance(data, str):
        return json.dumps({"type": "text", "content": data}) + "\n"

    lines = []
    if data.get("step_name") or data.get("step_description"):
        meta = {"type": "metadata"}
        if data.get("step_name"):
            meta["step_name"] = data["step_name"]
        if data.get("step_description"):
            meta["step_description"] = data["step_description"]
        lines.append(json.dumps(meta))
    if data.get("content"):
        lines.append(json.dumps({"type": "text", "content": data["content"]}))
    if data.get("elements") or data.get("remove_ids"):
        event = {"type": "elements"}
        if data.get("elements"):
            event["elements"] = data["elements"]
        if data.get("remove_ids"):
            event["remove_ids"] = data["remove_ids"]
        lines.append(json.dumps(event))
    if data.get("file"):
        lines.append(json.dumps({"type": "file", "file": data["file"]}))
    return "\n".join(lines) + "\n" if lines else ""


async def agent_stream_processor(
    message: str,
    conversation_id: int,
    agent: dict,
    messages_history: list,
    project: str,
    user_metadata: MetadataUser,
    files: list = None,
    client_context: dict = None,
):
    """Stream response using the appropriate agent connector based on connection_type.

    Args:
        message: The user's message
        conversation_id: The conversation ID
        agent: Agent configuration dict
        messages_history: Previous messages in the conversation
        project: Project name
        user_metadata: User details (user_id, username, ad_group)
        files: Optional file attachments
    """
    if not project:
        raise ValueError("Project name is required")

    # Maximum time (seconds) for the entire streaming operation before forced cancellation
    STREAM_TIMEOUT = 300

    agent_name = agent["name"]
    full_response = ""
    last_step_name = None
    last_step_description = None
    connector = None

    try:
        async with asyncio.timeout(STREAM_TIMEOUT):
            connector = get_connector(agent)

            # Combine messages for token counting
            combined_messages = messages_history + [{"role": "user", "content": message}]
            estimate_tokens_for_messages(combined_messages)

            file_attachments = None
            if files:
                file_attachments = [{"filename": f.filename, "content_type": f.content_type, "data": f.data} for f in files]

            # build user metadata here
            metadata = {
                "user": user_metadata,
                "conversation": {"conversation_id": str(conversation_id)},
                "project": project,
            }

            # Merge client context (frontend state) into metadata
            if client_context:
                metadata["frontend"] = client_context
            # print("metadata chat service: ", metadata)

            thread_id = None
            if agent.get("connection_type") == "langgraph":
                conv = db_chat.get_conversation(conversation_id, project)
                thread_id = conv.get("thread_id") if conv else None
                if thread_id is None:
                    thread_id = await connector.create_thread(metadata=metadata)
                    db_chat.set_conversation_thread_id(conversation_id, thread_id, project)

            # Send agent name as metadata so the frontend can label the message
            yield json.dumps({"type": "metadata", "agent_name": agent_name}) + "\n"

            async for chunk in connector.stream(
                messages_history,
                message,
                conversation_id=conversation_id,
                files=file_attachments,
                metadata=metadata,
                attachments=None,
                context=client_context,
                thread_id=thread_id,
            ):
                if isinstance(chunk, str):
                    full_response += chunk
                elif isinstance(chunk, dict):
                    if chunk.get("content"):
                        full_response += chunk["content"]
                    if chunk.get("step_name"):
                        last_step_name = chunk["step_name"]
                    if chunk.get("step_description"):
                        last_step_description = chunk["step_description"]
                ndjson = to_stream_events(chunk)
                if ndjson:
                    yield ndjson

            if full_response:
                output_tokens = estimate_tokens(full_response)
                db_chat.save_message(
                    conversation_id,
                    "assistant",
                    full_response,
                    project,
                    agent_name,
                    output_tokens,
                    step_name=last_step_name,
                    step_description=last_step_description,
                )
                # Always record usage event regardless of disable_message_storage
                try:
                    from core.db.db_project import (
                        get_project_by_name,
                        record_chat_interaction,
                    )

                    project_data = get_project_by_name(project)
                    if project_data:
                        record_chat_interaction(
                            project_id=project_data["id"],
                            agent_id=agent.get("id"),
                            user_id=(int(user_metadata.user_id) if user_metadata and user_metadata.user_id else None),
                        )
                except Exception as e:
                    logger.warning("Failed to record usage event for project '{}': {}", project, e)
    except asyncio.TimeoutError:
        logger.error("Streaming timed out after {}s for agent '{}'", STREAM_TIMEOUT, agent_name)
        yield to_stream_events(f"Error: Response from agent '{agent_name}' timed out after {STREAM_TIMEOUT}s")
    except Exception as e:
        logger.opt(exception=True).error("Error communicating with agent '{}'", agent_name)
        error_msg = f"Error communicating with agent '{agent_name}': {str(e)}"
        yield to_stream_events(error_msg)
        try:
            error_tokens = estimate_tokens(error_msg)
            db_chat.save_message(conversation_id, "assistant", error_msg, project, agent_name, error_tokens)
        except Exception:
            logger.opt(exception=True).warning("Failed to save error message to database")
    finally:
        if connector:
            try:
                await connector.close()
            except Exception:
                logger.opt(exception=True).warning("Error closing connector for agent '{}'", agent_name)
