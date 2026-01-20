from typing import AsyncIterator, Optional, List, Dict, Any

from ..base_connector import BaseAgentConnector


class LangGraphConnector(BaseAgentConnector):
    """LangGraph SDK connector for agents.
    
    Uses the LangGraph SDK to communicate with LangGraph Cloud or 
    self-hosted LangGraph API servers.
    
    Supports the assistant -> thread -> run pattern:
    - Initialize with a graph_id to fetch available assistants
    - Create threads for persistent conversations
    - Run assistants on threads to generate responses
    """
    
    def __init__(self, agent: dict):
        super().__init__(agent)
        self._client = None
        self.graph_id = agent.get("graph_id")
        self.assistant_list: List[Dict[str, Any]] = []
        self._threads: Dict[str, str] = {}  # Maps conversation_id to thread_id
        self._initialized = False
    
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
    
    async def initialize(self):
        """Initialize the connector by fetching assistants for the graph_id.
        
        This should be called after construction to load the assistant list.
        """
        if self._initialized:
            return
        
        client = self._get_client()
        
        if self.graph_id:
            print(f"[LangGraph] Fetching assistants for graph_id: {self.graph_id}")
            try:
                # Search for assistants associated with this graph
                assistants = await client.assistants.search(graph_id=self.graph_id)
                self.assistant_list = list(assistants) if assistants else []
                print(f"[LangGraph] Found {len(self.assistant_list)} assistant(s)")
                for assistant in self.assistant_list:
                    name = assistant.get("name", "unnamed") if isinstance(assistant, dict) else getattr(assistant, "name", "unnamed")
                    assistant_id = assistant.get("assistant_id", "unknown") if isinstance(assistant, dict) else getattr(assistant, "assistant_id", "unknown")
                    print(f"[LangGraph]   - {name} (id: {assistant_id})")
            except Exception as e:
                print(f"[LangGraph] Error fetching assistants: {e}")
                self.assistant_list = []
        else:
            print("[LangGraph] No graph_id provided, skipping assistant fetch")
        
        self._initialized = True
    
    def get_assistant_list(self) -> List[Dict[str, Any]]:
        """Get the list of assistants associated with this graph."""
        return self.assistant_list
    
    def get_assistant_by_name(self, assistant_name: str) -> Optional[Dict[str, Any]]:
        """Get an assistant by name from the cached list."""
        for assistant in self.assistant_list:
            name = assistant.get("name") if isinstance(assistant, dict) else getattr(assistant, "name", None)
            if name == assistant_name:
                return assistant
        return None
    
    def get_assistant_id(self, assistant_name: str) -> Optional[str]:
        """Get the assistant ID for a given assistant name."""
        assistant = self.get_assistant_by_name(assistant_name)
        if assistant:
            return assistant.get("assistant_id") if isinstance(assistant, dict) else getattr(assistant, "assistant_id", None)
        return None
    
    async def create_thread(self, conversation_id: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new thread for conversation persistence.
        
        Args:
            conversation_id: Optional conversation ID to associate with the thread
            metadata: Optional metadata to attach to the thread
            
        Returns:
            The thread ID
        """
        client = self._get_client()
        
        thread_metadata = metadata or {}
        if conversation_id is not None:
            thread_metadata["conversation_id"] = conversation_id
        
        print(f"[LangGraph] Creating new thread with metadata: {thread_metadata}")
        thread = await client.threads.create(metadata=thread_metadata)
        
        thread_id = thread.get("thread_id") if isinstance(thread, dict) else getattr(thread, "thread_id", str(thread))
        print(f"[LangGraph] Created thread: {thread_id}")
        
        # Cache the thread mapping
        if conversation_id is not None:
            self._threads[str(conversation_id)] = thread_id
        
        return thread_id
    
    async def get_or_create_thread(self, conversation_id: int, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Get existing thread for conversation or create a new one.
        
        Args:
            conversation_id: The conversation ID
            metadata: Optional metadata for new thread creation
            
        Returns:
            The thread ID
        """
        conv_key = str(conversation_id)
        
        # Check cache first
        if conv_key in self._threads:
            print(f"[LangGraph] Using cached thread for conversation {conversation_id}: {self._threads[conv_key]}")
            return self._threads[conv_key]
        
        # Create new thread
        return await self.create_thread(conversation_id=conversation_id, metadata=metadata)
    
    async def get_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get thread details by ID.
        
        Args:
            thread_id: The thread ID
            
        Returns:
            Thread details or None if not found
        """
        client = self._get_client()
        try:
            thread = await client.threads.get(thread_id)
            return thread
        except Exception as e:
            print(f"[LangGraph] Error getting thread {thread_id}: {e}")
            return None
    
    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread.
        
        Args:
            thread_id: The thread ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        client = self._get_client()
        try:
            await client.threads.delete(thread_id)
            # Remove from cache
            for key, value in list(self._threads.items()):
                if value == thread_id:
                    del self._threads[key]
            print(f"[LangGraph] Deleted thread: {thread_id}")
            return True
        except Exception as e:
            print(f"[LangGraph] Error deleting thread {thread_id}: {e}")
            return False

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
        files: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None
    ) -> AsyncIterator[str]:
        """Stream response from a LangGraph agent using the assistant -> thread -> run pattern.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            conversation_id: The conversation ID (used to get/create thread if thread_id not provided)
            files: Optional list of file attachments
            metadata: Optional metadata dict containing user details
            thread_id: Optional thread ID. If not provided, will get or create based on conversation_id
            
        Yields:
            Text chunks from the agent response
        """
        client = self._get_client()
        
        # Ensure initialized
        if not self._initialized:
            await self.initialize()
        
        # Get or create thread for this conversation
        if thread_id is None:
            thread_id = await self.get_or_create_thread(conversation_id, metadata=metadata)
        
        # Use agent name as assistant_id for LangGraph connections
        assistant_id = self.name
        agent_id = self.agent.get("id")
        run_config = self.extras.get("run_config", {})
        stream_mode = self.extras.get("stream_mode", "values")  # Default to values for reliability
        
        # Build input data - must match MessagesState schema exactly
        input_data = {"messages": messages}
        
        # Include agent_id if available (matches MessagesState schema)
        if agent_id is not None:
            input_data["agent_id"] = agent_id
        
        # Include graph_id if available (matches MessagesState schema)
        if self.graph_id:
            input_data["graph_id"] = self.graph_id
        
        # Include thread_id (matches MessagesState schema)
        if thread_id:
            input_data["thread_id"] = thread_id
        
        # Include metadata (user details) if provided (matches MessagesState schema)
        if metadata:
            input_data["metadata"] = metadata
            user_info = metadata.get("user", {})
            if user_info:
                print(f"[LangGraph] Including user metadata - user_id: {user_info.get('user_id')}, username: {user_info.get('username')}")
        
        # Handle files - attach to the last user message if provided
        # Note: files are not in MessagesState, so we attach them to the last message instead
        if files:
            print(f"[LangGraph] Including {len(files)} file attachment(s)")
            # Attach files to the last message (which should be the user message)
            if messages and len(messages) > 0:
                last_message = messages[-1]
                if isinstance(last_message, dict):
                    # Create a copy to avoid modifying the original
                    last_message_with_files = last_message.copy()
                    last_message_with_files["files"] = files
                    # Replace the last message with the one that has files
                    updated_messages = messages[:-1] + [last_message_with_files]
                    input_data["messages"] = updated_messages
        
        # Log with thread_id, agent_id and assistant_id
        log_info = f"thread_id: {thread_id}, agent_id: {agent_id}, assistant_id: {assistant_id} (agent name), mode: {stream_mode}"
        print(f"[LangGraph] Starting run - {log_info}")
        print(f"[LangGraph] Input data keys: {list(input_data.keys())}")
        print(f"[LangGraph] Messages count: {len(messages)}")
        
        try:
            if stream_mode == "messages":
                async for chunk in self._stream_messages(client, thread_id, assistant_id, input_data, run_config):
                    yield chunk
            else:
                async for chunk in self._stream_values(client, thread_id, assistant_id, input_data, run_config):
                    yield chunk
                    
            print(f"[LangGraph] Run completed successfully - thread_id: {thread_id}, assistant_id: {assistant_id}")
        except Exception as e:
            print(f"[LangGraph] ERROR - thread_id: {thread_id}, assistant_id: {assistant_id}, error: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"LangGraph error: {str(e)}"
    
    async def _stream_messages(self, client, thread_id: str, assistant_id: str, input_data: dict, run_config: dict) -> AsyncIterator[str]:
        """Stream using messages mode (for streaming LLMs).
        
        Args:
            client: The LangGraph client
            thread_id: The thread ID for this conversation
            assistant_id: The assistant ID to use
            input_data: Input data for the run
            run_config: Configuration for the run
        """
        last_content_length = 0
        has_streamed = False
        
        async for event in client.runs.stream(
            thread_id=thread_id,
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
    
    async def _stream_values(self, client, thread_id: str, assistant_id: str, input_data: dict, run_config: dict) -> AsyncIterator[str]:
        """Stream using values mode (works with any agent).
        
        Args:
            client: The LangGraph client
            thread_id: The thread ID for this conversation
            assistant_id: The assistant ID to use
            input_data: Input data for the run
            run_config: Configuration for the run
        """
        last_message_content = None
        
        async for event in client.runs.stream(
            thread_id=thread_id,
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
