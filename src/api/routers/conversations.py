"""Conversations and messages: /conversations, /conversations/{id}/messages."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from api.deps.auth import get_current_user
from api.deps.project import get_project_from_header, verify_project_membership
from api.schema import ConversationCreate, ConversationUpdate
from core.auth.jwt import CurrentUser
from core.db import db_chat

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(
    agent_id: Optional[int] = None,
    current_user: CurrentUser = Depends(get_current_user),
    project: Optional[str] = Depends(get_project_from_header),
):
    """List all conversations for the authenticated user, optionally filtered by project and agent."""
    if project:
        await run_in_threadpool(verify_project_membership, project, current_user.user_id, current_user.ad_groups)
    conversations = await run_in_threadpool(db_chat.list_conversations, current_user.username, project, agent_id)
    return JSONResponse({"conversations": conversations, "project": project})


@router.post("")
async def create_conversation(
    request: ConversationCreate,
    current_user: CurrentUser = Depends(get_current_user),
    project: Optional[str] = Depends(get_project_from_header),
):
    """Create a new conversation for the authenticated user within a project."""
    if project:
        await run_in_threadpool(verify_project_membership, project, current_user.user_id, current_user.ad_groups)
    conversation = await run_in_threadpool(
        db_chat.create_conversation, current_user.username, request.title, project, request.agent_id
    )
    return JSONResponse(conversation)


@router.patch("/{conversation_id}")
async def rename_conversation(
    conversation_id: int,
    request: ConversationUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    project: Optional[str] = Depends(get_project_from_header),
):
    """Rename a conversation."""
    if not project:
        raise HTTPException(status_code=400, detail="Project name is required in header")
    await run_in_threadpool(verify_project_membership, project, current_user.user_id, current_user.ad_groups)
    result = await run_in_threadpool(db_chat.rename_conversation, conversation_id, request.title, project, current_user.user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return JSONResponse(result)


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    project: Optional[str] = Depends(get_project_from_header),
):
    """Delete a conversation and its messages."""
    if not project:
        raise HTTPException(status_code=400, detail="Project name is required in header")
    await run_in_threadpool(verify_project_membership, project, current_user.user_id, current_user.ad_groups)
    try:
        await run_in_threadpool(db_chat.delete_conversation, conversation_id, project, current_user.user_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return JSONResponse({"status": "deleted"})


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    project: Optional[str] = Depends(get_project_from_header),
):
    """Get all messages for a conversation."""
    if not project:
        raise HTTPException(status_code=400, detail="Project name is required in header")
    await run_in_threadpool(verify_project_membership, project, current_user.user_id, current_user.ad_groups)

    # Enforce ownership: verify conversation belongs to current user before returning messages
    conversation = await run_in_threadpool(db_chat.get_conversation, conversation_id, project, current_user.user_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await run_in_threadpool(
        db_chat.get_messages,
        conversation_id,
        project,
        current_user.user_id,
        ["system"],
    )
    return JSONResponse({"messages": messages})
