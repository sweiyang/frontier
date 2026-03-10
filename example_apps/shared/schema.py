"""
Standardised Conduit agent request/response schema for example apps.

Use these types so LangGraph and HTTP examples stay consistent with the
Conduit response contract: content (str), elements (list), file (dict).
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class FileAttachment(BaseModel):
    """File offered for download (agent → user). Content is base64-encoded bytes."""

    name: str
    type: str = "application/octet-stream"
    content: str = Field(..., description="Base64-encoded file content")


class AgentResponse(BaseModel):
    """
    Agent response payload. Conduit converts this to NDJSON for the frontend.

    - content: Optional message text.
    - elements: Optional list of dynamic UI elements (button, table, text_input, etc.).
    - file: Optional file for download (name, type, base64 content).
    """

    content: Optional[str] = None
    elements: Optional[list[dict[str, Any]]] = None
    file: Optional[FileAttachment] = None


class ChatRequest(BaseModel):
    """Incoming request from Conduit to an HTTP agent (POST body)."""

    messages: list[Any] = Field(default_factory=list)
    metadata: Optional[dict[str, Any]] = None
    context: Optional[dict[str, Any]] = None
    files: Optional[list[Any]] = None
