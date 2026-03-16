import httpx
import json
from typing import AsyncIterator, Optional, List, Dict, Any, Union

from ..base_connector import BaseAgentConnector
from core.logging import get_logger

logger = get_logger(__name__)


class HTTPAgentConnector(BaseAgentConnector):
    """HTTP streaming connector for agents.

    Sends the same structured request payload as the LangGraph connector:
        {messages, metadata, attachments, context, ...extras}

    Supports three response modes from the server:
        1. SSE (text/event-stream) — lines prefixed with ``data: ``
        2. Raw text streaming — plain chunked text
        3. JSON (application/json) — single structured response with
           optional ``content``, ``elements``, and ``file`` fields (yielded as dict).
    """

    async def stream(
        self,
        messages_history: list,
        message: str,
        conversation_id: Optional[int] = None,
        files: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[Union[str, dict]]:
        """Stream response from an HTTP endpoint. Yields raw str or dict for chat service to convert to NDJSON.

        Accepts the same parameters as ``LangGraphConnector.stream()`` and
        forwards them as a JSON payload to the configured endpoint so that
        HTTP agents receive the full Frontier request schema.

        Args:
            messages_history: Previous conversation messages (dicts with 'role' and 'content').
            message: The new user message string.
            conversation_id: Optional conversation ID.
            files: Optional base64-encoded file attachments.
            metadata: Optional dict with user details, conversation info, project, etc.
            attachments: Optional list of attachment dicts ({id, name, mime, uri}).
            context: Optional dict with timezone, locale, etc.
            thread_id: Optional thread ID for conversation persistence.
        """
        messages = messages_history + [{"role": "user", "content": message}]

        payload: Dict[str, Any] = {
            "messages": messages,
            **self.extras,
        }

        if files:
            payload["files"] = files
        if metadata:
            if "user" in metadata and hasattr(metadata.get("user"), "model_dump"):
                metadata = {**metadata, "user": metadata["user"].model_dump()}
            payload["metadata"] = metadata
        if attachments:
            payload["attachments"] = attachments
        if context:
            payload["context"] = context
        if thread_id:
            payload["thread_id"] = thread_id

        headers = {"Content-Type": "application/json"}
        headers.update(self.get_auth_headers())

        logger.debug("HTTP request to %s", self.endpoint)

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", self.endpoint, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    try:
                        err = json.loads(body)
                        detail = err.get("error", {}).get("message", body.decode())
                    except Exception:
                        logger.debug("Failed to parse HTTP agent error response as JSON", exc_info=True)
                        detail = body.decode()
                    logger.error("HTTP agent error (%d): %s", response.status_code, detail)
                    yield f"Agent error ({response.status_code}): {detail}"
                    return

                content_type = response.headers.get("content-type", "")

                if "application/json" in content_type and "text/event-stream" not in content_type:
                    await response.aread()
                    try:
                        data = response.json()
                        yield data
                    except json.JSONDecodeError:
                        logger.error("Invalid JSON response from HTTP agent at %s", self.endpoint, exc_info=True)
                        yield "Error: Invalid JSON response from agent"
                    return

                async for chunk in response.aiter_text():
                    if not chunk:
                        continue
                    if chunk.startswith("data: "):
                        data = chunk[6:].strip()
                        if data and data != "[DONE]":
                            try:
                                parsed = json.loads(data)
                                if isinstance(parsed, dict) and ("content" in parsed or "elements" in parsed or "file" in parsed):
                                    yield parsed
                                else:
                                    yield data
                            except json.JSONDecodeError:
                                logger.debug("Failed to parse HTTP agent SSE data as JSON, yielding raw: %s", data[:100])
                                yield data
                    else:
                        yield chunk

    async def close(self):
        """No cleanup needed — httpx client is context-managed."""
        pass
