# Shared schema for Conduit example apps

This package defines the **standardised request/response schema** used by both the LangGraph and HTTP example apps so they stay consistent with the Conduit agent contract.

## Contents

- **AgentResponse** — Response payload: `content` (str), `elements` (list of UI element dicts), `file` (optional `FileAttachment`). Use `.model_dump(exclude_none=True)` to get the dict to send (e.g. to `interrupt()` or `JSONResponse()`).
- **FileAttachment** — File for download: `name`, `type` (MIME), `content` (base64 str).
- **ChatRequest** — Incoming HTTP request from Conduit: `messages`, `metadata`, `context`, `files`.

## Usage

Both examples add `example_apps` to `sys.path` so they can run from their own directory and still import:

```python
from shared.schema import AgentResponse, ChatRequest, FileAttachment
```

Run from the repo root or from `example_apps` with:

```bash
# From example_apps
cd example_apps && python -m http_example.app

# Or from repo root (PYTHONPATH must include example_apps for shared)
PYTHONPATH=example_apps python -m http_example.app
```

LangGraph example keeps its own `schema.py` for graph **State** (messages, step) because that is LangGraph-specific; it imports `AgentResponse` and `FileAttachment` from `shared.schema` for building responses.
