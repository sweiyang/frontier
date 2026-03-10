# Conduit OpenAI Connector — User Guide

This guide explains how to connect Conduit to an **OpenAI-compatible** chat API using the **OpenAI connector** (`connection_type: "openai"`). The connector calls the `/v1/chat/completions` (or equivalent) endpoint with streaming, so it works with OpenAI, Azure OpenAI, vLLM, Ollama, LiteLLM, and other compatible servers.

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration in Conduit](#configuration-in-conduit)
3. [Request Format](#request-format)
4. [Extras (Model and API Parameters)](#extras-model-and-api-parameters)
5. [Authentication](#authentication)
6. [Limitations](#limitations)

---

## Overview

- The OpenAI connector **only supports streaming**. It sends a single request with `stream: true` and yields **content deltas** from the response SSE stream.
- The request body is the standard chat completions payload: `model`, `messages`, `stream: true`, plus any optional parameters you pass via `extras`.
- **No dynamic elements or file downloads** are produced by the connector itself; the model’s reply is plain text (and the frontend can still render markdown).

---

## Configuration in Conduit

Create an OpenAI-type agent in the Conduit admin UI or via the API:

```json
{
  "name": "GPT-4o",
  "endpoint": "https://api.openai.com/v1",
  "connection_type": "openai",
  "is_default": true,
  "extras": {
    "model": "gpt-4o",
    "system_prompt": "You are a helpful assistant.",
    "temperature": 0.7,
    "max_tokens": 2048
  },
  "auth": {
    "auth_type": "bearer",
    "credentials": "sk-..."
  }
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name in the chat UI. |
| `endpoint` | Yes | Base URL of the API. The connector will use this as-is if it already ends with `/chat/completions`, otherwise it appends `/v1/chat/completions` (or `/v1` → `/chat/completions`). Examples: `https://api.openai.com/v1`, `https://your-server.com/v1/chat/completions`. |
| `connection_type` | Yes | Must be `"openai"`. |
| `extras.model` | No | Model name (e.g. `gpt-4o`, `gpt-4o-mini`). Default: `"gpt-4o"`. |
| `extras.system_prompt` | No | If set, added as a single `system` message at the start of the `messages` array. |
| `extras` (others) | No | Optional parameters forwarded to the API (see [Extras](#extras-model-and-api-parameters)). |
| `auth` | No | Same as other connectors: `bearer`, `api_key`, or `basic`. |

---

## Request Format

For each user message, the connector:

1. Builds a **messages** array:
   - If `extras.system_prompt` is set, one `{"role": "system", "content": "..."}`.
   - Then the conversation **history** (as returned by Conduit: list of `role`/`content` dicts).
   - Then the **new user message** as `{"role": "user", "content": "..."}`.
2. Sends a **POST** to the chat completions URL with:
   - `model`: from `extras.model` (default `gpt-4o`).
   - `messages`: as above.
   - `stream`: `true`.
   - Any additional keys from `extras` that are known (e.g. `temperature`, `max_tokens`).
3. Reads the response as **SSE**, parses each `data:` line as JSON, and yields `delta.content` for each chunk until `[DONE]`.

So the upstream API receives a standard OpenAI-style streaming chat request; no Conduit-specific fields are required.

---

## Extras (Model and API Parameters)

These `extras` keys are passed through to the request body when present:

| Key | Description |
|-----|--------------|
| `model` | Model identifier (default `gpt-4o`). |
| `system_prompt` | Prepended as a system message; not sent as a separate API parameter. |
| `temperature` | Sampling temperature. |
| `max_tokens` | Maximum tokens to generate. |
| `top_p` | Top-p sampling. |
| `frequency_penalty` | Frequency penalty. |
| `presence_penalty` | Presence penalty. |
| `stop` | Stop sequences. |

Any other `extras` are **not** automatically forwarded; only the list above is. If you need another parameter, add it in the connector code or use an HTTP connector and call the OpenAI API yourself.

---

## Authentication

Configure `auth` the same way as for the [HTTP connector](./http-connector-user-guide.md#authentication):

- **Bearer:** `{"auth_type": "bearer", "credentials": "sk-..."}` → `Authorization: Bearer ...`
- **API key:** `{"auth_type": "api_key", "credentials": "..."}` → `X-API-Key: ...`
- **Basic:** `{"auth_type": "basic", "credentials": {"username": "...", "password": "..."}}` → `Authorization: Basic ...`

These headers are sent on the chat completions request.

---

## Limitations

- **No thread or conversation object:** The connector does not create or pass a thread ID; it only sends the message list Conduit provides. Conversation persistence is handled by Conduit (history) and the upstream API (if it supports it via your own mechanism).
- **No structured elements or files:** Only the model’s text stream is returned. For tables, buttons, or file downloads, use the HTTP or LangGraph connector and have your backend emit `[ELEMENTS]` / `[FILE]` blocks.
- **No file uploads in the connector:** The connector does not currently map Conduit file attachments into the OpenAI “vision” or “file” message format. To support images or documents, you would need to extend the connector or use an HTTP agent that builds the request yourself.

For full control over request/response and rich UI, use the [HTTP connector](./http-connector-user-guide.md) and call the OpenAI API (or any other API) from your own server.
