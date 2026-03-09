"""Agent stream processor and saving messages logic."""
from conduit.core.agent.connectors import get_connector
from conduit.core.agent.connectors.schema import MetadataUser
from conduit.core.db import db_chat
from conduit.core.utils.token_counter import estimate_tokens, estimate_tokens_for_messages


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

    agent_name = agent["name"]
    full_response = ""
    connector = None

    try:
        connector = get_connector(agent)

        # Combine messages for token counting
        combined_messages = messages_history + [{"role": "user", "content": message}]
        input_tokens = estimate_tokens_for_messages(combined_messages)

        file_attachments = None
        if files:
            file_attachments = [
                {"filename": f.filename, "content_type": f.content_type, "data": f.data}
                for f in files
            ]
            
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

        async for chunk in connector.stream(
            messages_history, message,
            conversation_id=conversation_id,
            files=file_attachments,
            metadata=metadata,
            attachments=None,
            context=client_context,
            thread_id=thread_id,
        ):
            full_response += chunk
            yield chunk

        if full_response:
            output_tokens = estimate_tokens(full_response)
            db_chat.save_message(
                conversation_id,
                "assistant",
                full_response,
                project,
                agent_name,
                output_tokens,
            )
    except Exception as e:
        error_msg = f"Error communicating with agent '{agent_name}': {str(e)}"
        yield error_msg
        error_tokens = estimate_tokens(error_msg)
        db_chat.save_message(
            conversation_id, "assistant", error_msg, project, agent_name, error_tokens
        )
    finally:
        if connector:
            await connector.close()
