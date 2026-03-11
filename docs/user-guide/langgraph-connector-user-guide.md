# Frontier LangGraph Connector — User Guide

This guide explains how to connect Frontier to a **LangGraph** agent using the **LangGraph connector** (`connection_type: "langgraph"`). The connector uses the [LangGraph SDK](https://github.com/langchain-ai/langgraph-sdk) to talk to LangGraph Cloud or a self-hosted LangGraph API.

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration in Frontier](#configuration-in-conduit)
3. [Request Payload (Input to Your Graph)](#request-payload-input-to-your-graph)
4. [Thread Lifecycle](#thread-lifecycle)
5. [Assistants and graph_id](#assistants-and-graph_id)
6. [Interrupts and Resuming](#interrupts-and-resuming)
7. [Structured Output (Elements and Files)](#structured-output-elements-and-files)
8. [Example Graphs](#example-graphs)

---

## Overview

- Frontier uses the **assistant → thread → run** pattern: each conversation has a **thread**, and each user message triggers a **run** for the configured **assistant** on that thread.
- The connector **streams** the assistant’s reply and supports **interrupts**: when your graph calls `interrupt(...)`, the interrupt payload is sent to the client; when the user replies or clicks a button, Frontier **resumes** the run with the new input.
- **Dynamic UI elements** (tables, buttons, text inputs, etc.) and **file downloads** are supported via structured content in assistant messages (see [Structured Output](#structured-output-elements-and-files)).

**Requirements:** `langgraph-sdk` must be installed (`pip install langgraph-sdk`).

---

## Configuration in Frontier

Create a LangGraph agent in the Frontier admin UI or via the API:

```json
{
  "name": "My LangGraph Agent",
  "endpoint": "https://api.langchain.com",
  "connection_type": "langgraph",
  "graph_id": "my-graph-id",
  "is_default": false,
  "extras": {
    "assistant_id": "my-assistant-id",
    "run_config": {}
  },
  "auth": {
    "auth_type": "bearer",
    "credentials": "your-langgraph-api-key"
  },
  "icon": null
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name in the chat UI. |
| `endpoint` | Yes | LangGraph API base URL (e.g. `https://api.langchain.com` or your self-hosted URL). |
| `connection_type` | Yes | Must be `"langgraph"`. |
| `graph_id` | No* | Graph ID used to **list assistants** for this agent. Stored on the agent or in `extras.graph_id`. |
| `extras.assistant_id` | No** | Assistant ID to run. If omitted, the connector uses the agent’s **name** as the assistant ID. |
| `extras.run_config` | No | Optional run config. The connector always sets `configurable.thread_id` (and nested `configurable.thread_id`) for the current thread. |
| `auth` | No | Same as HTTP connector: `bearer`, `api_key`, or `basic`. Sent as headers to the LangGraph API. |
| `icon` | No | URL or path for the agent icon. |

\* If you use the Frontier UI to pick an assistant from a list, `graph_id` is needed so Frontier can fetch assistants.  
\** Your deployed graph must have an assistant whose ID matches `extras.assistant_id` or the agent `name`.

---

## Request Payload (Input to Your Graph)

For each user message, the connector sends an **input** dict to `runs.stream(...)` with:

| Key | Type | Description |
|-----|------|-------------|
| `messages` | `list` | Conversation history (as LangChain message objects) plus the new user message as a `HumanMessage`. |
| `metadata` | `dict` | Frontier metadata: `user` (e.g. `user_id`, `username`, `ad_group`), `conversation` (e.g. `conversation_id`), `project`. Also includes **`frontend`**: the dynamic panel state (selections, text input values, etc.) from the last user action. |
| `attachments` | `list` | URI-based attachments (e.g. S3). |
| `context` | `dict` | Client context passed through from the chat request (e.g. timezone, locale, or the same panel state). Frontier passes the frontend panel state here as well as in `metadata.frontend`. |

So your graph state can read:

- **Last user message and history:** from `messages`.
- **Who is talking to the agent:** from `metadata.user` and `metadata.project`.
- **Panel state (e.g. table selections, text field values):** from `metadata.frontend` or `context` (depending on how Frontier is configured; the chat service puts panel state in both).

---

## Thread Lifecycle

- **First message in a conversation:** Frontier has no thread ID. The connector **creates a new thread** via the LangGraph API and then starts a run on it. Frontier stores the returned `thread_id` on the conversation.
- **Later messages:** Frontier passes the stored `thread_id` into the connector so the run is on the same thread (same conversation).
- **Interrupt:** When your graph calls `interrupt(...)`, the connector streams the interrupt content to the user. Frontier marks that conversation as “interrupted” so the **next** request for that conversation is sent as a **resume** with the same thread ID and the new user input (message + panel state).

So you do not create or delete threads in your graph; the connector and Frontier manage creation and persistence.

---

## Assistants and graph_id

- **Listing assistants:** If the agent has a `graph_id` (on the agent or in `extras`), Frontier can call the LangGraph API to **search assistants** for that graph. This is used by the UI to show a list of assistants (e.g. to set `assistant_id`).
- **Which assistant runs:** For each run, the connector uses `extras.assistant_id` if set; otherwise it uses the agent’s **name** as the assistant ID. Your deployed graph must expose an assistant with that ID.

---

## Interrupts and Resuming

1. **In your graph:** Call `interrupt(value)` (e.g. from a LangGraph node). `value` can be a string, a dict, or an `AIMessage` (or other message-like object). The connector will **extract content** from it (see below) and stream it to the client.
2. **User action:** The user types a reply or uses a dynamic element (e.g. button). Frontier sends the next request with the new message and updated panel state.
3. **Resume:** For that conversation, the connector sees that the thread was interrupted and sends a **resume** to the LangGraph API: `Command(resume=input_data)` with the same `input_data` shape (messages, metadata, attachments, context). Your graph continues from the interrupt with that input.

**Content extraction for interrupts:**  
If the interrupt value is or contains a **dict** with `"content"`, the connector uses that for the streamed text. If that dict also has `"elements"` or `"file"`, they are serialized into the same `[ELEMENTS]` / `[FILE]` blocks the frontend expects (see [Structured Output](#structured-output-elements-and-files)). So you can interrupt with an AIMessage whose content is a JSON string like `{"content": "...", "elements": [...], "file": {...}}` and the connector will parse it and stream text + elements + file to the client.

---

## Structured Output (Elements and Files)

For the chat UI to show **dynamic elements** (tables, buttons, text inputs, search bars) or **file downloads**, the assistant’s message content must follow the format the frontend expects. The LangGraph connector supports this in two ways:

1. **Structured content in interrupts:** If your graph interrupts with a value that parses to a dict with `content`, `elements`, or `file`, the connector:
   - Sends the main text from `content`.
   - Appends `[ELEMENTS]{...}[/ELEMENTS]` when `elements` is present.
   - Appends `[FILE]{...}[/FILE]` when `file` is present (with `name`, `type`, `content` base64).

2. **Structured content in normal streamed messages:** When the run streams message or update events, the connector calls `_extract_content` on each message. If the message content is a **dict** with `content`, `elements`, or `file`, it again produces the same text + `[ELEMENTS]` + `[FILE]` blocks.

So from inside your graph, you can:

- Emit an **AIMessage** whose `content` is a **JSON string** of the form:
  ```json
  {
    "content": "Here are the results:",
    "elements": [
      { "type": "table", "id": "results", "title": "Results", "columns": [...], "rows": [...] }
    ]
  }
  ```
- Or pass a **dict** with `content`, `elements`, and optionally `file` when using a custom message format that the connector knows how to traverse.

Element and file formats are the same as for the HTTP connector; see [Supported Elements User Guide](./supported-elements-user-guide.md) and the [HTTP Connector](./http-connector-user-guide.md) file download section.

---

## Example Graphs

- **`example_apps/langgraph_examples/approval_interrupt_graph.py`** — Uses `interrupt()` with choices and with structured content (table + elements).
- **`example_apps/langgraph_examples/cpcr_mockup.py`** — Multi-step flow with tables, buttons, and interrupts; reads panel state from the resume payload.

Run the examples with the LangGraph CLI or your preferred runner, then in Frontier create a LangGraph agent with the appropriate `endpoint`, `graph_id`, and `assistant_id` (or name) so Frontier uses the same graph and assistant.

---

## Troubleshooting

### Enable Debug Logging

Set the log level to `DEBUG` in `config.yaml` to see detailed LangGraph connector activity:

```yaml
logging:
  level: DEBUG
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

Debug logs include:
- LangGraph client initialization
- Thread creation and management
- Run execution and streaming events
- Interrupt handling and resumption

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `langgraph-sdk not installed` | Missing dependency | Run `pip install langgraph-sdk` |
| Thread creation failed | Invalid endpoint or auth | Verify endpoint URL and credentials |
| No assistant found | Assistant ID mismatch | Check `assistant_id` in extras matches deployed graph |
| Streaming timeout | Long-running graph | Increase client timeout or optimize graph |

### Log Output Example

```
2026-03-11 10:15:23 - core.agent.connectors.langgraph_connector - DEBUG - Initializing LangGraph client for endpoint: http://localhost:8123
2026-03-11 10:15:24 - core.agent.connectors.langgraph_connector - DEBUG - Created thread abc123 for conversation 42
2026-03-11 10:15:24 - core.agent.connectors.langgraph_connector - DEBUG - Starting run with assistant default_agent
```
