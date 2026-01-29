"""Conversations and messages: /conversations, /conversations/{id}/messages."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from conduit.api.deps.auth import get_current_user
from conduit.api.deps.project import get_project_from_header
from conduit.api.schema import ConversationCreate
from conduit.core.auth.jwt import CurrentUser
from conduit.core.db import db_chat

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(
    current_user: CurrentUser = Depends(get_current_user),
    project: Optional[str] = Depends(get_project_from_header),
):
    """List all conversations for the authenticated user, optionally filtered by project."""
    conversations = db_chat.list_conversations(current_user.username, project=project)
    return JSONResponse({"conversations": conversations, "project": project})


@router.post("")
async def create_conversation(
    request: ConversationCreate,
    current_user: CurrentUser = Depends(get_current_user),
    project: Optional[str] = Depends(get_project_from_header),
):
    """Create a new conversation for the authenticated user within a project."""
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
    messages = db_chat.get_messages(conversation_id, project=project)
    return JSONResponse({"messages": messages})
