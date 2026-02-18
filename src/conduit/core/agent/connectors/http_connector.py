import httpx
import json
from typing import AsyncIterator, Optional, List, Dict, Any

from ..base_connector import BaseAgentConnector


class HTTPAgentConnector(BaseAgentConnector):
    """HTTP streaming connector for agents."""
    
    async def stream(
        self, 
        messages_history: list,
        message: str,
        conversation_id: Optional[int] = None,
        files: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """Stream response from an HTTP endpoint.
        
        Supports both SSE format (data: ...) and raw text streaming.
        Files are passed as base64-encoded attachments in the payload.
        Metadata (user details) is included in the payload if provided.
        
        Args:
            messages_history: List of previous conversation messages (dicts with 'role' and 'content')
            message: The new user message string
            conversation_id: The conversation ID
            files: Optional list of file attachments with 'filename', 'content_type', and 'data' (base64)
            metadata: Optional metadata dict containing user details and other context
        """
        # Combine messages history with new message
        messages = messages_history + [{"role": "user", "content": message}]
        
        payload = {
            "messages": messages,
            **self.extras
        }
        
        # Include file attachments if provided
        if files:
            payload["files"] = files
        
        # Include metadata (user details) if provided
        if metadata:
            payload["metadata"] = metadata
        
        # Build headers with authentication
        headers = {"Content-Type": "application/json"}
        headers.update(self.get_auth_headers())
        
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", self.endpoint, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    yield f"Agent error: {response.status_code}"
                    return
                
                content_type = response.headers.get("content-type", "")
                
                # Handle application/json (non-streaming structured response)
                if "application/json" in content_type and "text/event-stream" not in content_type:
                    # For JSON, we need to read the whole body
                    await response.read()
                    try:
                        data = response.json()
                        
                        # Extract content and elements
                        content = data.get("content", "")
                        elements = data.get("elements")
                        
                        # Yield the content
                        if content:
                            yield content
                        
                        # Yield the elements block if present
                        if elements:
                            yield f"\n[ELEMENTS]{json.dumps({'elements': elements})}[/ELEMENTS]"
                            
                    except json.JSONDecodeError:
                        yield "Error: Invalid JSON response from agent"
                    return

                # Handle streaming response (SSE or raw text)
                async for chunk in response.aiter_text():
                    if chunk:
                        # Check for SSE format (data: ...)
                        if chunk.startswith("data: "):
                            data = chunk[6:].strip()
                            if data and data != "[DONE]":
                                yield data
                        else:
                            # Raw text streaming
                            yield chunk
    
    async def close(self):
        """No cleanup needed - httpx client is context-managed."""
        pass

