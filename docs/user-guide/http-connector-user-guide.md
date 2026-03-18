# Frontier HTTP Connector — User Guide

This guide explains how to build a custom HTTP agent that integrates with
Frontier via the **HTTP connector** (`connection_type: "http"`).

The HTTP connector sends the same structured request payload as the LangGraph
connector, so your agent receives full context — messages, user metadata,
attachments, and more — over a single `POST` request.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Request Payload](#request-payload)
3. [Response Formats](#response-formats)
4. [Structured Elements](#structured-elements)
5. [Configuration in Frontier](#configuration-in-frontier)
6. [Authentication](#authentication)
7. [Sample Code](#sample-code)
8. [Extras — Custom Fields](#extras--custom-fields)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements_pip.txt

# Run the example agent
uvicorn frontier_agent:app --host 0.0.0.0 --port 8000 --reload
```

Then configure an HTTP agent in Frontier pointing to
`http://localhost:8000/stream` (or any of the other endpoints).

---

## Request Payload

Every request from Frontier's HTTP connector is a `POST` with a JSON body:

```json
{
  "messages": [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "What is the weather?"}
  ],
  "metadata": {
    "user": {
      "user_id": "u123",
      "username": "alice",
      "ad_group": ["engineers", "admins"]
    },
    "conversation": {
      "conversation_id": "42"
    },
    "project": "my-project"
  },
  "attachments": [
    {
      "id": "att-1",
      "name": "report.pdf",
      "mime": "application/pdf",
      "uri": "s3://bucket/report.pdf"
    }
  ],
  "context": {
    "timezone": "Asia/Singapore",
    "locale": "en-SG"
  },
  "files": [
    {
      "filename": "photo.png",
      "content_type": "image/png",
      "data": "<base64-encoded>"
    }
  ],
  "thread_id": "optional-thread-uuid"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `messages` | `list[dict]` | Conversation history + latest user message. Each dict has `role` (`"user"` / `"assistant"`) and `content` (string). |
| `metadata` | `dict` | User info, conversation ID, project name, and frontend context. |
| `attachments` | `list[dict]` | URI-based attachments (e.g. S3 links). |
| `context` | `dict` | Client-side context like timezone and locale. |
| `files` | `list[dict]` | Base64-encoded file uploads from the chat UI. |
| `thread_id` | `string` | Thread identifier for conversation persistence (if applicable). |

Any additional fields defined in the agent's `extras` config are merged
into the top-level payload.

---

## Response Formats

Your agent can respond in one of three ways. Frontier auto-detects the
format from the `Content-Type` header.

### 1. Streaming Plain Text

Return a `StreamingResponse` with `media_type="text/plain"`. Frontier
displays chunks in real time as they arrive.

```python
from fastapi.responses import StreamingResponse

async def generate():
    for word in "Hello world!".split():
        yield word + " "

@app.post("/stream")
async def stream(request: AgentRequest):
    return StreamingResponse(generate(), media_type="text/plain")
```

### 2. SSE (Server-Sent Events)

Return a `StreamingResponse` with `media_type="text/event-stream"`.
Each chunk must be prefixed with `data: ` and terminated with `\n\n`.
Send `data: [DONE]\n\n` to signal the end.

```python
async def generate():
    yield "data: Hello \n\n"
    yield "data: world!\n\n"
    yield "data: [DONE]\n\n"

@app.post("/stream-sse")
async def stream_sse(request: AgentRequest):
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### 3. JSON (Single Response)

Return a regular JSON response. Frontier reads the body, extracts
`content` and optional `elements` / `file` fields.

```python
@app.post("/json")
async def json_response(request: AgentRequest):
    return {
        "content": "Here is your data.",
        "elements": [ ... ]
    }
```

---

## Structured Elements

The JSON response (or an SSE `data:` line) can include an `elements`
list to render rich UI components in the Frontier chat:

```json
{
  "content": "Here are the results:",
  "elements": [
    {
      "type": "table",
      "id": "weather_table",
      "title": "Weather Forecast",
      "columns": [
        {"key": "city", "label": "City"},
        {"key": "temp", "label": "Temperature"}
      ],
      "rows": [
        {"id": 1, "city": "Tokyo", "temp": "32°C"},
        {"id": 2, "city": "London", "temp": "18°C"}
      ]
    }
  ]
}
```

Table elements support additional options:

| Option | Type | Description |
|--------|------|-------------|
| `searchable` | `bool` | Enable a search bar on the table |
| `select_mode` | `"single"` / `"multi"` | Allow row selection |

For the full list of supported element types (button, text_input, search_bar, table) and their options, see [Supported Elements User Guide](./supported-elements-user-guide.md).

---

## Configuration in Frontier

Create an HTTP agent via the Frontier admin UI or API:

```json
{
  "name": "my-http-agent",
  "endpoint": "http://localhost:8000/stream",
  "connection_type": "http",
  "is_default": true,
  "extras": {
    "temperature": 0.7
  },
  "auth": {
    "auth_type": "bearer",
    "credentials": "my-secret-token"
  }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name for the agent in the chat UI |
| `endpoint` | Yes | Full URL to your agent's endpoint |
| `connection_type` | Yes | Must be `"http"` |
| `is_default` | No | Set `true` to make this the default agent for the project |
| `extras` | No | Arbitrary JSON merged into every request payload |
| `auth` | No | Authentication config (see [Authentication](#authentication)) |
| `icon` | No | URL or path to an icon for the agent |

---

## Authentication

Frontier supports three auth methods. The credentials are sent as HTTP
headers on every request:

### Bearer Token
```json
{"auth_type": "bearer", "credentials": "my-token"}
```
Header: `Authorization: Bearer my-token`

### API Key
```json
{"auth_type": "api_key", "credentials": "my-api-key"}
```
Header: `X-API-Key: my-api-key`

### Basic Auth
```json
{
  "auth_type": "basic",
  "credentials": {"username": "admin", "password": "secret"}
}
```
Header: `Authorization: Basic <base64(admin:secret)>`

---

## Sample Code

See `example_apps/http_agent/frontier_agent.py` for a complete, runnable
example with five endpoints:

| Endpoint | Response Mode | Description |
|----------|--------------|-------------|
| `POST /stream` | Streaming text | Word-by-word streaming |
| `POST /stream-sse` | SSE | Server-Sent Events |
| `POST /json` | JSON | Structured response with elements |
| `POST /stream-sse-json` | SSE + JSON | Mixed text and structured SSE |
| `POST /echo` | JSON | Echoes the full request for debugging |

### Minimal Agent (10 lines)

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

async def generate(messages):
    last_msg = messages[-1]["content"] if messages else ""
    for word in f"You said: {last_msg}".split():
        yield word + " "

@app.post("/")
async def agent(request: dict):
    return StreamingResponse(
        generate(request.get("messages", [])),
        media_type="text/plain",
    )
```

### Agent with Metadata Access

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

app = FastAPI()

class AgentRequest(BaseModel):
    messages: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    thread_id: Optional[str] = None

@app.post("/")
async def agent(request: AgentRequest):
    username = "anonymous"
    if request.metadata and request.metadata.get("user"):
        username = request.metadata["user"].get("username", username)

    project = request.metadata.get("project", "unknown") if request.metadata else "unknown"
    tz = request.context.get("timezone", "UTC") if request.context else "UTC"

    return {
        "content": f"Hello **{username}** from project *{project}* (tz: {tz})!"
    }
```

---

## Extras — Custom Fields

The `extras` dict in the agent config is spread into the top level of
every request payload. Use this to pass model parameters, feature flags,
or any custom configuration to your agent:

```json
{
  "extras": {
    "model": "gpt-4o",
    "temperature": 0.3,
    "max_tokens": 2048,
    "feature_flag": "v2"
  }
}
```

Your agent receives:

```json
{
  "messages": [...],
  "metadata": {...},
  "model": "gpt-4o",
  "temperature": 0.3,
  "max_tokens": 2048,
  "feature_flag": "v2"
}
```

---

## Troubleshooting

### Enable Debug Logging

Set the log level to `DEBUG` in `config.yaml` to see detailed HTTP connector activity:

```yaml
logging:
  level: DEBUG
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

Debug logs include:
- HTTP request URLs and endpoints
- Response status codes and errors
- Streaming chunk details

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `Agent error (400)` | Invalid request format | Check agent endpoint and auth config |
| `Agent error (401)` | Authentication failed | Verify auth credentials in agent config |
| `Agent error (500)` | Agent server error | Check agent logs; ensure endpoint is running |
| Connection timeout | Agent not responding | Verify endpoint URL; check network connectivity |

### Log Output Example

```
2026-03-11 10:15:23 - core.agent.connectors.http_connector - DEBUG - HTTP request to http://localhost:8100/
2026-03-11 10:15:23 - core.agent.connectors.http_connector - ERROR - HTTP agent error (500): Internal Server Error
```
