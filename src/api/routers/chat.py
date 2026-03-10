"""Chat streaming: /chat."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from api.deps.auth import get_current_user
from api.deps.project import get_project_from_header
from api.schema import ChatRequest
from api.services.chat_service import agent_stream_processor
from core.agent.connectors.schema import MetadataUser
from core.auth.jwt import CurrentUser
from core.db import db_chat, db_project
from core.utils.token_counter import estimate_tokens

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def stream_chat(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    project: Optional[str] = Depends(get_project_from_header),
):
    """Stream chat response for the authenticated user within a project context."""
    if not project:
        raise HTTPException(status_code=400, detail="Project name is required in header")

    user_token_count = estimate_tokens(request.message)
    db_chat.save_message(
        request.conversation_id, "user", request.message, project, request.model, user_token_count
    )

    agent = None
    project_data = db_project.get_project_by_name(project)
    if project_data:
        if request.agent_id:
            agent = db_project.get_agent_by_id(request.agent_id)
            if agent and agent["project_id"] != project_data["id"]:
                agent = None
        if not agent:
            agent = db_project.get_default_agent_for_project(project_data["id"])
        if not agent and request.model and request.model != "default":
            agent = db_project.get_agent_by_name(project_data["id"], request.model)

    if not agent:
        raise HTTPException(status_code=404, detail="No agent configured for this project")

    messages_history = db_chat.get_messages(request.conversation_id, project=project)
    history = [{"role": m["role"], "content": m["content"]} for m in messages_history[:-1]]

    user_metadata = MetadataUser(
        user_id=str(current_user.user_id),
        username=current_user.username,
        ad_group=[],
    )

    return StreamingResponse(
        agent_stream_processor(
            request.message,
            request.conversation_id,
            agent,
            history,
            project,
            user_metadata=user_metadata,
            files=request.files,
            client_context=request.client_context,
        ),
        media_type="text/plain",
    )
