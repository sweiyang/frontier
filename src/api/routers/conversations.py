"""Conversations and messages: /conversations, /conversations/{id}/messages."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from api.deps.auth import get_current_user
from api.deps.project import get_project_from_header, verify_project_membership
from api.schema import ConversationCreate
from core.auth.jwt import CurrentUser
from core.db import db_chat

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(
    current_user: CurrentUser = Depends(get_current_user),
    project: Optional[str] = Depends(get_project_from_header),
):
    """List all conversations for the authenticated user, optionally filtered by project."""
    if project:
        verify_project_membership(project, current_user.user_id, current_user.ad_groups)
    conversations = db_chat.list_conversations(current_user.username, project=project)
    return JSONResponse({"conversations": conversations, "project": project})


@router.post("")
async def create_conversation(
    request: ConversationCreate,
    current_user: CurrentUser = Depends(get_current_user),
    project: Optional[str] = Depends(get_project_from_header),
):
    """Create a new conversation for the authenticated user within a project."""
    if project:
        verify_project_membership(project, current_user.user_id, current_user.ad_groups)
    conversation = db_chat.create_conversation(
        current_user.username, request.title, project=project
    )
    return JSONResponse(conversation)


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    project: Optional[str] = Depends(get_project_from_header),
):
    """Get all messages for a conversation."""
    if not project:
        raise HTTPException(status_code=400, detail="Project name is required in header")
    verify_project_membership(project, current_user.user_id, current_user.ad_groups)
    messages = db_chat.get_messages(conversation_id, project=project)
    return JSONResponse({"messages": messages})
