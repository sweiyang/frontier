"""Pydantic schemas for the LangGraph connector.

Defines the request (inputs to stream()) and response (yielded chunks) shapes
for the LangGraph connector's assistant -> thread -> run pattern.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

# --- Request: input to LangGraphConnector.stream() ---


class Attachment(BaseModel):
    """File or document attachment referenced by URI."""

    id: str
    name: str
    mime: str
    uri: str


class MetadataUser(BaseModel):
    user_id: str
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    ad_group: List[str]


class MetadataConversation(BaseModel):
    conversation_id: str


class Metadata(BaseModel):
    user: Optional[MetadataUser] = None
    conversation: Optional[MetadataConversation] = None


class Context(BaseModel):
    timezone: Optional[str] = None
    locale: Optional[str] = None


class request_schema(BaseModel):
    """Request payload for LangGraphConnector.stream().

    Attributes:
        messages: Conversation history + current user message. Each has "role" and "content".
        metadata: User and conversation info.
        attachments: Optional attachments referenced by URI (e.g. S3).
        context: Optional timezone, locale, etc.
    """

    messages: List[Dict[str, Any]]  # [{"role", "content"}, ...]
    metadata: Optional[Metadata] = None
    attachments: Optional[List[Attachment]] = None
    context: Optional[Context] = None


# --- Response: each value yielded by stream() ---
class response_schema(BaseModel):
    """A single text chunk yielded by LangGraphConnector.stream().

    The stream yields raw str; this schema describes the logical shape of each chunk.
    """

    content: str
