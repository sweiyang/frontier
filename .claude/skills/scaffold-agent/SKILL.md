---
name: scaffold-agent
description: Scaffold a new Frontier agent app (HTTP, OpenAI, or LangGraph) with boilerplate code, shared schema, and registration script. Use when the user wants to create a new agent, connector, or integrate an external service with Frontier.
---

# Scaffold Agent

Generate a complete, runnable agent app for Frontier with the correct connector boilerplate, shared schema imports, and a registration script — ready to start and connect.

## Workflow

### Step 1: Ask for Connector Type

Ask the user which connector type they want:

- **http** — A FastAPI app that Frontier calls via its HTTP connector (supports JSON and SSE responses)
- **openai** — A FastAPI app exposing `/v1/chat/completions` (OpenAI-compatible), so Frontier's OpenAI connector can call it
- **langgraph** — A LangGraph graph with state management, `interrupt()` support, and `AgentResponse` usage

### Step 2: Gather Configuration

Ask the user for:

1. **Agent name** (used as directory name and in registration) — validate: lowercase, alphanumeric + underscores
2. **Port** (default: 9100)
3. **Type-specific config:**
   - HTTP: response mode preference (JSON, SSE, or both as examples)
   - OpenAI: model name to advertise (default: agent name)
   - LangGraph: whether to include `interrupt()` / human-in-the-loop pattern
4. **Optional**: system prompt, description

### Step 3: Read Reference Files

Read the following files to understand the current patterns before generating code. Do NOT generate code from memory — always read first.

**All types — always read these:**

- `example_apps/shared/schema.py` — shared `AgentResponse`, `ChatRequest`, `MetadataUser`, `Metadata`, `FileAttachment` models
- `example_apps/shared/__init__.py` — exports
- `src/core/agent/base_connector.py` — the `BaseAgentConnector` interface (stream + close contract)
- `src/core/agent/connectors/__init__.py` — connector registry showing valid `connection_type` values

**HTTP type — also read:**

- `example_apps/http_example/app.py` — full HTTP agent example (FastAPI, JSON/SSE/text response modes, user metadata access)

**OpenAI type — also read:**

- `src/core/agent/connectors/openai_connector.py` — how Frontier calls OpenAI-compatible endpoints (URL resolution, SSE parsing, extras)
- `example_apps/openai_ollama_example/register_agent.py` — registration pattern with `connection_type: "openai"` and `extras.model`

**LangGraph type — also read:**

- `example_apps/langgraph_example/app.py` — full LangGraph graph with `StateGraph`, `interrupt()`, `AgentResponse` usage
- `example_apps/langgraph_example/schema.py` — LangGraph `State` definition
- `example_apps/langgraph_example/langgraph.json` — LangGraph manifest
- `src/core/agent/connectors/langgraph_connector.py` — how Frontier calls LangGraph (thread management, config metadata)

### Step 4: Generate Files

Create the following files under `example_apps/<agent_name>/`:

| File | All Types | HTTP | OpenAI | LangGraph |
|------|-----------|------|--------|-----------|
| `app.py` | Yes | Yes | Yes | Yes |
| `register_agent.py` | Yes | Yes | Yes | Yes |
| `README.md` | Yes | Yes | Yes | Yes |
| `schema.py` | No | No | No | Yes |
| `langgraph.json` | No | No | No | Yes |

### Step 5: Print Instructions

After generating files, print:

1. How to install dependencies (`pip install fastapi uvicorn` or `pip install langgraph`)
2. How to start the agent (`uvicorn <name>.app:app --port <port>` or `langgraph dev`)
3. How to register with Frontier (`python example_apps/<name>/register_agent.py --url ... --project ... --token ...`)

## Adaptation Rules

When generating code from the reference examples, apply these rules:

### Import Pattern

Always use the `sys.path.insert` pattern for shared schema imports, matching the existing examples:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared.schema import ChatRequest, AgentResponse
```

Do NOT define Pydantic models inline — always import from `shared.schema`.

### HTTP Type

- Generate a FastAPI app with both JSON and SSE response examples (as separate endpoints or a mode toggle), adapted from `http_example/app.py`
- Include a metadata access example showing how to read `req.metadata.user` for personalization
- Set `connection_type: "http"` in the registration script

### OpenAI Type

- Generate a FastAPI app that exposes `POST /v1/chat/completions` with SSE streaming
- The response format must match OpenAI's chat completion SSE format (`data: {"choices": [{"delta": {"content": "..."}}]}`) so Frontier's `openai_connector.py` can parse it
- Include a `/v1/models` endpoint listing the agent's model name
- Set `connection_type: "openai"` in the registration script
- Include `extras: {"model": "<model_name>"}` in registration payload

### LangGraph Type

- Generate a `StateGraph` with at least one node and proper state management, adapted from `langgraph_example/`
- Include the `interrupt()` pattern if the user requested human-in-the-loop
- Generate a `schema.py` with the graph's `State` TypedDict
- Generate a `langgraph.json` manifest pointing to the graph
- Set `connection_type: "langgraph"` in the registration script

### Registration Script

The generated `register_agent.py` must:

- Accept CLI args: `--url` (Frontier base URL), `--project` (project name), `--token` (JWT token), `--name` (agent display name), `--endpoint` (agent URL)
- Fall back to environment variables: `FRONTIER_URL`, `FRONTIER_PROJECT`, `FRONTIER_TOKEN`
- POST to `{url}/projects/{project}/agents` with the correct payload:
  - `name`: agent display name
  - `endpoint`: agent URL (e.g., `http://localhost:9100`)
  - `connection_type`: `http`, `openai`, or `langgraph`
  - `extras`: type-specific config (e.g., `{"model": "..."}` for openai)
- Print success/failure with the response

### README

Generate a short README.md containing:

1. What the agent does (one paragraph)
2. Prerequisites (Python, pip packages)
3. How to run it
4. How to register it with Frontier
5. How to test it (a sample curl command)
