"""
HTTP agent example: all Frontier elements and file download.

Frontier sends POST with body: { messages, metadata, context, files?, ... }.
Return a dict with "content", "elements", and/or "file" — no special encoding.

Response modes:
  - application/json: single dict with content / elements / file
  - text/event-stream: SSE with data: lines (each line a JSON object with content/elements/file)
  - Plain text: chunked text (yielded as-is)

Trigger demos by sending a message that starts with:
  - "show stats" -> stats elements
  - "show table" -> table + search_bar + button
  - "show form" -> text_input + button
  - "download file" -> file attachment
  - "stream demo" -> SSE: text, then elements, then file
  - anything else -> echo as plain text
"""

import base64
import json
import sys
from pathlib import Path

# Allow importing shared schema when running from example_apps or http_example
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse

from shared.schema import AgentResponse, ChatRequest, FileAttachment

app = FastAPI(title="Frontier HTTP Agent Example")


def _stats_response() -> dict:
    return AgentResponse(
        content="Here are sample **stats**. You can use these for KPIs or dashboards.",
        elements=[
            {
                "type": "stats",
                "id": "http_metrics",
                "title": "Service health",
                "layout": "row",
                "stats": [
                    {"label": "Requests/s", "value": 1250, "unit": "req/s", "color": "green", "trend": "up"},
                    {"label": "Error rate", "value": 0.2, "unit": "%", "color": "green", "trend": "down"},
                    {"label": "P99", "value": 145, "unit": "ms", "color": "yellow"},
                ],
            },
        ],
    ).model_dump(exclude_none=True)


def _table_response() -> dict:
    return AgentResponse(
        content="Select rows from the table. Use the search bar to filter, then click Submit.",
        elements=[
            {
                "type": "search_bar",
                "id": "search",
                "target": "data_table",
                "placeholder": "Filter...",
            },
            {
                "type": "table",
                "id": "data_table",
                "title": "Data",
                "columns": [{"key": "name", "label": "Name", "sortable": True}, {"key": "role", "label": "Role"}],
                "rows": [
                    {"id": 1, "name": "Acme", "role": "Vendor"},
                    {"id": 2, "name": "Globex", "role": "Partner"},
                ],
                "select_mode": "multi",
                "searchable": True,
            },
            {
                "type": "button",
                "id": "submit_btn",
                "label": "Submit",
                "action": "send_message",
                "payload_template": "Selected: {{data_table.selected}}",
            },
        ],
    ).model_dump(exclude_none=True)


def _form_response() -> dict:
    return AgentResponse(
        content="Enter text below and click Submit.",
        elements=[
            {
                "type": "text_input",
                "id": "user_input",
                "label": "Your input",
                "placeholder": "Type here...",
                "multiline": True,
            },
            {
                "type": "button",
                "id": "submit_btn",
                "label": "Submit",
                "action": "send_message",
                "payload_template": "{{user_input.value}}",
            },
        ],
    ).model_dump(exclude_none=True)


def _file_response() -> dict:
    data = b"Frontier HTTP example - file download.\n"
    b64 = base64.b64encode(data).decode("ascii")
    return AgentResponse(
        content="Your file is ready. Download it from the link in the message.",
        file=FileAttachment(name="example.txt", type="text/plain", content=b64),
    ).model_dump(exclude_none=True)


async def _stream_demo():
    """SSE stream: send dicts with content / elements / file (Frontier contract)."""
    yield f"data: {json.dumps({'content': 'Streaming demo: '})}\n\n"
    yield f"data: {json.dumps({'content': 'first chunk. '})}\n\n"
    yield f"data: {json.dumps({'content': 'second chunk.'})}\n\n"
    yield f"data: {json.dumps({'elements': [_stats_response()['elements'][0]]})}\n\n"
    data = b"Streamed file content.\n"
    b64 = base64.b64encode(data).decode("ascii")
    yield f"data: {json.dumps({'file': FileAttachment(name='streamed.txt', type='text/plain', content=b64).model_dump()})}\n\n"


@app.post("/")
async def chat(req: ChatRequest):
    body = req.model_dump()
    messages = body.get("messages", [])
    last_content = ""
    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, dict):
            last_content = (last_msg.get("content") or "").strip().lower()
        else:
            last_content = str(getattr(last_msg, "content", "") or "").strip().lower()

    # Stream demo: SSE
    if last_content == "stream demo":
        return StreamingResponse(
            _stream_demo(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    # JSON responses
    if last_content.startswith("show stats"):
        return JSONResponse(_stats_response())
    if last_content.startswith("show table"):
        return JSONResponse(_table_response())
    if last_content.startswith("show form"):
        return JSONResponse(_form_response())
    if last_content.startswith("download file"):
        return JSONResponse(_file_response())

    # Default: plain text echo
    return JSONResponse(
        AgentResponse(
            content=last_content or "Send 'show stats', 'show table', 'show form', 'download file', or 'stream demo'."
        ).model_dump(exclude_none=True)
    )
