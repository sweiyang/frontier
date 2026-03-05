# Conduit HTTP Agent — Example

This directory contains a sample HTTP agent that works with Conduit's **HTTP connector** (`connection_type: "http"`).

## Quick Start

```bash
# From the project root, install dependencies
pip install -r requirements_pip.txt

# Run the example agent
uvicorn conduit_agent:app --host 0.0.0.0 --port 8000 --reload
```

Then in Conduit, add an HTTP agent with endpoint `http://localhost:8000/stream` (or `/stream-sse`, `/json`, etc.).

## Full documentation

For the complete HTTP connector user guide (request payload, response formats, structured elements, auth, and configuration), see:

**[docs/http-connector-user-guide.md](../../docs/http-connector-user-guide.md)**

## Endpoints in this example

| Endpoint | Description |
|----------|-------------|
| `POST /stream` | Streaming plain text |
| `POST /stream-sse` | Server-Sent Events |
| `POST /json` | JSON with elements (e.g. table) |
| `POST /stream-sse-json` | SSE with structured JSON |
| `POST /echo` | Echo request (debugging) |
