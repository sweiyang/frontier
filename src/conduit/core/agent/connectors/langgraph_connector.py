from typing import AsyncIterator, Optional, List, Dict, Any

from ..base_connector import BaseAgentConnector


class LangGraphConnector(BaseAgentConnector):
    """LangGraph SDK connector for agents.
    
    Uses the LangGraph SDK to communicate with LangGraph Cloud or 
    self-hosted LangGraph API servers.
    """
    
    def __init__(self, agent: dict):
        super().__init__(agent)
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of LangGraph client."""
        if self._client is None:
            try:
                from langgraph_sdk import get_client
                print(f"[LangGraph] Initializing client for endpoint: {self.endpoint}")
                
                # Build client with auth headers if configured
                auth_headers = self.get_auth_headers()
                if auth_headers:
                    self._client = get_client(url=self.endpoint, headers=auth_headers)
                    print(f"[LangGraph] Client initialized with authentication")
                else:
                    self._client = get_client(url=self.endpoint)
                    print(f"[LangGraph] Client initialized successfully")
            except ImportError:
                print("[LangGraph] ERROR: langgraph-sdk not installed")
                raise ImportError(
                    "langgraph-sdk is required for LangGraph connections. "
                    "Install it with: pip install langgraph-sdk"
                )
        return self._client
    
    def _extract_content(self, msg) -> str:
        """Extract text content from a message object."""
        if isinstance(msg, dict):
            content = msg.get("content", "")
            if isinstance(content, list):
                return "".join(
                    c.get("text", "") if isinstance(c, dict) else str(c)
                    for c in content
                )
            return content if isinstance(content, str) else ""
        elif hasattr(msg, "content"):
            content = msg.content
            if isinstance(content, list):
                return "".join(
                    c.get("text", "") if isinstance(c, dict) else str(c)
                    for c in content
                )
            return content if isinstance(content, str) else ""
        return ""
    
    async def stream(
        self, 
        messages: list,
        conversation_id: int,
        files: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncIterator[str]:
        """Stream response from a LangGraph agent.
        
        Tries streaming with messages mode first, falls back to values mode.
        Files are attached to the last user message if provided.
        """
        client = self._get_client()
        
        assistant_id = self.extras.get("assistant_id", "agent")
        run_config = self.extras.get("run_config", {})
        stream_mode = self.extras.get("stream_mode", "values")  # Default to values for reliability
        
        # If files are provided, attach them to the input
        input_data = {"messages": messages}
        if files:
            # Include files as attachments in the input
            input_data["files"] = files
            print(f"[LangGraph] Including {len(files)} file attachment(s)")
        
        print(f"[LangGraph] Starting stream - assistant_id: {assistant_id}, mode: {stream_mode}")
        print(f"[LangGraph] Messages: {messages}")
        
        try:
            if stream_mode == "messages":
                async for chunk in self._stream_messages(client, assistant_id, input_data, run_config):
                    yield chunk
            else:
                async for chunk in self._stream_values(client, assistant_id, input_data, run_config):
                    yield chunk
                    
            print("[LangGraph] Stream completed successfully")
        except Exception as e:
            print(f"[LangGraph] ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"LangGraph error: {str(e)}"
    
    async def _stream_messages(self, client, assistant_id, input_data, run_config) -> AsyncIterator[str]:
        """Stream using messages mode (for streaming LLMs)."""
        last_content_length = 0
        has_streamed = False
        
        async for event in client.runs.stream(
            thread_id=None,
            assistant_id=assistant_id,
            input=input_data,
            config=run_config,
            stream_mode="messages",
        ):
            print(f"[LangGraph] Event: {event.event}")
            
            if event.event == "messages/partial":
                data = event.data
                if isinstance(data, list) and len(data) > 0:
                    msg = data[0]
                    content = self._extract_content(msg)
                    if len(content) > last_content_length:
                        new_content = content[last_content_length:]
                        last_content_length = len(content)
                        if new_content:
                            print(f"[LangGraph] Chunk: {new_content[:50]}...")
                            has_streamed = True
                            yield new_content
                            
            elif event.event == "messages/complete":
                if not has_streamed:
                    data = event.data
                    if isinstance(data, list) and len(data) > 0:
                        msg = data[0]
                        content = self._extract_content(msg)
                        if content:
                            print(f"[LangGraph] Complete: {content[:100]}...")
                            yield content
    
    async def _stream_values(self, client, assistant_id, input_data, run_config) -> AsyncIterator[str]:
        """Stream using values mode (works with any agent)."""
        last_message_content = None
        
        async for event in client.runs.stream(
            thread_id=None,
            assistant_id=assistant_id,
            input=input_data,
            config=run_config,
            stream_mode="values",
        ):
            print(f"[LangGraph] Event: {event.event}")
            
            if event.event == "values":
                data = event.data
                if isinstance(data, dict) and "messages" in data:
                    msgs = data["messages"]
                    if msgs and len(msgs) > 0:
                        # Get the last message (assistant response)
                        last_msg = msgs[-1]
                        content = self._extract_content(last_msg)
                        
                        # Check if it's an assistant message and new content
                        role = last_msg.get("type", "") if isinstance(last_msg, dict) else getattr(last_msg, "type", "")
                        if role in ("ai", "assistant", "AIMessage") or not role:
                            if content and content != last_message_content:
                                print(f"[LangGraph] Response: {content[:100]}...")
                                last_message_content = content
                                yield content
    
    async def close(self):
        """Close the LangGraph client if initialized."""
        if self._client is not None:
            print("[LangGraph] Releasing client reference")
            self._client = None
