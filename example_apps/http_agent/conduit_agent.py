"""
Conduit HTTP Agent — Example Server
====================================

A FastAPI application that demonstrates how to build an HTTP agent
compatible with the Conduit HTTP connector.

The server receives the same structured request payload that the
LangGraph connector uses (messages, metadata, attachments, context)
and shows three response modes:

    1. Streaming plain text
    2. SSE (Server-Sent Events)
    3. JSON with structured elements (tables, files, etc.)

Run:
    uvicorn conduit_agent:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request schema — mirrors Conduit's connector request_schema
# ---------------------------------------------------------------------------

class MetadataUser(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None
    ad_group: Optional[List[str]] = None


class Metadata(BaseModel):
    user: Optional[MetadataUser] = None
    conversation: Optional[Dict[str, Any]] = None
    project: Optional[str] = None
    frontend: Optional[Dict[str, Any]] = None


class Attachment(BaseModel):
    id: str
    name: str
    mime: str
    uri: str


class Context(BaseModel):
    timezone: Optional[str] = None
    locale: Optional[str] = None


class FileAttachment(BaseModel):
    filename: str
    content_type: str
    data: str  # base64-encoded


class AgentRequest(BaseModel):
    """Full request payload sent by Conduit's HTTP connector."""
    messages: List[Dict[str, Any]]
    metadata: Optional[Metadata] = None
    attachments: Optional[List[Attachment]] = None
    context: Optional[Context] = None
    files: Optional[List[FileAttachment]] = None
    thread_id: Optional[str] = None


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Conduit HTTP Agent Example")


# ---------------------------------------------------------------------------
# 1. Streaming plain-text response
# ---------------------------------------------------------------------------

async def _text_streamer(text: str):
    """Yield words one at a time to simulate token-level streaming."""
    for word in text.split():
        yield word + " "
        await asyncio.sleep(0.05)


@app.post("/stream")
async def stream_text(request: AgentRequest):
    """Streaming plain-text endpoint.

    Conduit will read chunked text as it arrives and display it in
    the chat UI in real time.
    """
    last_user_msg = ""
    for msg in reversed(request.messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break

    reply = (
        f"Hello{', ' + request.metadata.user.username if request.metadata and request.metadata.user and request.metadata.user.username else ''}! "
        f"You said: \"{last_user_msg}\". "
        "This response is streamed word-by-word over plain text."
    )

    return StreamingResponse(_text_streamer(reply), media_type="text/plain")


# ---------------------------------------------------------------------------
# 2. SSE (Server-Sent Events) response
# ---------------------------------------------------------------------------

async def _sse_streamer(text: str):
    """Yield SSE-formatted events."""
    for word in text.split():
        yield f"data: {word} \n\n"
        await asyncio.sleep(0.05)
    yield "data: [DONE]\n\n"


@app.post("/stream-sse")
async def stream_sse(request: AgentRequest):
    """SSE endpoint.

    Each chunk is sent as ``data: <text>\\n\\n``.  Conduit strips the
    ``data: `` prefix automatically.
    """
    last_user_msg = ""
    for msg in reversed(request.messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break

    reply = f"SSE echo: {last_user_msg}"
    return StreamingResponse(_sse_streamer(reply), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# 3. JSON response with structured elements
# ---------------------------------------------------------------------------

@app.post("/json")
async def json_response(request: AgentRequest):
    """JSON endpoint returning structured content with elements.

    The ``elements`` list can contain tables, charts, or other UI
    components that Conduit's frontend renders inline.
    """
    username = "there"
    if request.metadata and request.metadata.user and request.metadata.user.username:
        username = request.metadata.user.username

    return {
        "content": f"Hello {username}! Here is a sample table element.",
        "elements": [
            {
                "type": "table",
                "id": "sample_table",
                "title": "Sample Data",
                "columns": [
                    {"key": "name", "label": "Name"},
                    {"key": "value", "label": "Value"},
                ],
                "rows": [
                    {"id": 1, "name": "Temperature", "value": "32°C"},
                    {"id": 2, "name": "Humidity", "value": "65%"},
                    {"id": 3, "name": "Wind", "value": "12 km/h"},
                ],
            }
        ],
    }


# ---------------------------------------------------------------------------
# 4. SSE with structured JSON chunks (elements mid-stream)
# ---------------------------------------------------------------------------

async def _sse_json_streamer(username: str):
    """Yield SSE events where some are structured JSON with elements."""
    yield f"data: Hello {username}! Let me look that up... \n\n"
    await asyncio.sleep(0.3)
    yield "data: Here are the results:\n\n"
    await asyncio.sleep(0.2)

    structured = json.dumps({
        "content": "",
        "elements": [
            {
                "type": "table",
                "id": "sse_table",
                "title": "Live Results",
                "columns": [
                    {"key": "item", "label": "Item"},
                    {"key": "status", "label": "Status"},
                ],
                "rows": [
                    {"id": 1, "item": "Service A", "status": "Healthy"},
                    {"id": 2, "item": "Service B", "status": "Degraded"},
                ],
            }
        ],
    })
    yield f"data: {structured}\n\n"
    await asyncio.sleep(0.1)
    yield "data: [DONE]\n\n"


@app.post("/stream-sse-json")
async def stream_sse_json(request: AgentRequest):
    """SSE endpoint that mixes plain text and structured JSON events.

    Conduit auto-detects when an SSE data line is a JSON object with
    ``content`` / ``elements`` keys and extracts them accordingly.
    """
    username = "there"
    if request.metadata and request.metadata.user and request.metadata.user.username:
        username = request.metadata.user.username

    return StreamingResponse(
        _sse_json_streamer(username),
        media_type="text/event-stream",
    )


# ---------------------------------------------------------------------------
# 5. Echo endpoint — useful for debugging the request payload
# ---------------------------------------------------------------------------

@app.post("/echo")
async def echo(request: AgentRequest):
    """Returns the full request payload as JSON for debugging."""
    return request.model_dump()
