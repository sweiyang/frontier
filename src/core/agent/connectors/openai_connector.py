import json
import httpx
from typing import AsyncIterator, Optional, List, Dict, Any

from ..base_connector import BaseAgentConnector
from core.logging import get_logger

logger = get_logger(__name__)


class OpenAIConnector(BaseAgentConnector):
    """Connector for OpenAI-compatible chat completions endpoints.
    
    Supports any endpoint that implements the /v1/chat/completions API
    (OpenAI, Azure OpenAI, vLLM, Ollama, LiteLLM, etc.).
    
    Expects extras: { "model": "gpt-4o", "system_prompt": "..." (optional) }
    """

    def __init__(self, agent: dict):
        """
        Initialize the OpenAI connector.
        
        Args:
            agent: Agent config dict with 'endpoint', 'auth', and 'extras'.
                   extras.model: Model name (default: 'gpt-4o').
                   extras.system_prompt: Optional system prompt.
        """
        super().__init__(agent)
        self.model = self.extras.get("model", "gpt-4o")
        self.system_prompt = self.extras.get("system_prompt")

    def _build_endpoint_url(self) -> str:
        """Resolve the chat completions URL.
        
        If the endpoint already ends with /chat/completions, use as-is.
        Otherwise append /v1/chat/completions (stripping trailing slash).
        """
        ep = self.endpoint.rstrip("/")
        if ep.endswith("/chat/completions"):
            return ep
        if ep.endswith("/v1"):
            return f"{ep}/chat/completions"
        return f"{ep}/v1/chat/completions"

    def _build_messages(self, messages_history: list, message: str) -> list:
        """Construct the messages array with optional system prompt."""
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.extend(messages_history)
        messages.append({"role": "user", "content": message})
        return messages

    async def stream(
        self,
        messages_history: list,
        message: str,
        conversation_id: Optional[int] = None,
        files: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream response from an OpenAI-compatible chat completions endpoint.

        Sends a streaming request and yields text deltas as they arrive.
        """
        url = self._build_endpoint_url()
        messages = self._build_messages(messages_history, message)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }

        # Forward any extra parameters (temperature, max_tokens, etc.)
        for key in ("temperature", "max_tokens", "top_p", "frequency_penalty",
                     "presence_penalty", "stop"):
            if key in self.extras:
                payload[key] = self.extras[key]

        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        headers.update(self.get_auth_headers())

        logger.debug("OpenAI request to %s with model %s", url, self.model)

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    try:
                        err = json.loads(body)
                        detail = err.get("error", {}).get("message", body.decode())
                    except Exception:
                        logger.debug("Failed to parse OpenAI error response as JSON", exc_info=True)
                        detail = body.decode()
                    logger.error("OpenAI API error (%d): %s", response.status_code, detail)
                    yield f"OpenAI API error ({response.status_code}): {detail}"
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        logger.debug("Failed to parse OpenAI stream chunk: %s", data)
                        continue

    async def close(self):
        """No persistent resources to clean up."""
        pass
