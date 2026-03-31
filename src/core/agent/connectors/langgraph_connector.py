from typing import Any, AsyncIterator, Dict, List, Optional, Union

from langgraph_sdk.schema import Command

from core.logging import get_logger

from ..base_connector import BaseAgentConnector

logger = get_logger(__name__)

interrupt_thread_id = []


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
        """
        Initialize the LangGraph connector.

        Args:
            agent: Agent config dict with 'endpoint', 'auth', and 'extras'.
                   extras.graph_id: ID of the LangGraph graph to use.
                   extras.graph_id: ID of the LangGraph graph.
        """
        super().__init__(agent)
        self._client = None
        self.graph_id = agent.get("graph_id") or self.extras.get("graph_id")
        self.assistant_list: List[Dict[str, Any]] = []
        self._initialized = False

    def _get_client(self):
        """Lazy initialization of LangGraph client."""
        if self._client is None:
            try:
                from langgraph_sdk import get_client

                logger.debug(
                    "Initializing LangGraph client for endpoint: {}", self.endpoint
                )

                auth_headers = self.get_auth_headers()
                if auth_headers:
                    self._client = get_client(url=self.endpoint, headers=auth_headers)
                    logger.debug("LangGraph client initialized with authentication")
                else:
                    self._client = get_client(url=self.endpoint)
                    logger.debug("LangGraph client initialized successfully")
            except ImportError:
                logger.error("langgraph-sdk not installed")
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
            logger.debug("Fetching assistants for graph_id: {}", self.graph_id)
            try:
                assistants = await client.assistants.search(graph_id=self.graph_id)
                self.assistant_list = list(assistants) if assistants else []
                logger.debug("Found {} assistant(s)", len(self.assistant_list))
                for assistant in self.assistant_list:
                    name = (
                        assistant.get("name", "unnamed")
                        if isinstance(assistant, dict)
                        else getattr(assistant, "name", "unnamed")
                    )
                    assistant_id = (
                        assistant.get("assistant_id", "unknown")
                        if isinstance(assistant, dict)
                        else getattr(assistant, "assistant_id", "unknown")
                    )
                    logger.debug("  - {} (id: {})", name, assistant_id)
            except Exception:
                logger.opt(exception=True).error(
                    "Error fetching assistants for graph_id {}", self.graph_id
                )
                self.assistant_list = []
        else:
            logger.warning("No graph_id provided, skipping assistant fetch")

        self._initialized = True

    def get_assistant_list(self) -> List[Dict[str, Any]]:
        """Get the list of assistants associated with this graph."""
        return self.assistant_list

    def get_assistant_by_name(self, assistant_name: str) -> Optional[Dict[str, Any]]:
        """Get an assistant by name from the cached list."""
        for assistant in self.assistant_list:
            name = (
                assistant.get("name")
                if isinstance(assistant, dict)
                else getattr(assistant, "name", None)
            )
            if name == assistant_name:
                return assistant
        return None

    def get_assistant_id(self, assistant_name: str) -> Optional[str]:
        """Get the assistant ID for a given assistant name."""
        assistant = self.get_assistant_by_name(assistant_name)
        if assistant:
            return (
                assistant.get("assistant_id")
                if isinstance(assistant, dict)
                else getattr(assistant, "assistant_id", None)
            )
        return None

    async def create_thread(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new thread for conversation persistence.

        Args:
            metadata: Optional metadata to attach to the thread

        Returns:
            The thread ID
        """
        client = self._get_client()
        thread_metadata = metadata or {}
        logger.debug("Creating new thread with metadata: {}", thread_metadata)
        thread = await client.threads.create(metadata=thread_metadata)
        thread_id = (
            thread.get("thread_id")
            if isinstance(thread, dict)
            else getattr(thread, "thread_id", str(thread))
        )
        logger.debug("Created thread: {}", thread_id)
        return thread_id

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
        except Exception:
            logger.opt(exception=True).error("Error getting thread {}", thread_id)
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
            logger.debug("Deleted thread: {}", thread_id)
            return True
        except Exception:
            logger.opt(exception=True).error("Error deleting thread {}", thread_id)
            return False

    def _prepare_messages(self, messages_history: list, message: str) -> list:
        """Prepare messages for LangGraph SDK.

        Passes message history as-is (may not be compatible, but that's expected).
        Appends new message as HumanMessage object.

        Args:
            messages_history: List of previous conversation messages (passed as-is)
            message: New user message string

        Returns:
            List of messages: messages_history + [HumanMessage(content=message)]
        """
        from langchain_core.messages import HumanMessage

        # Pass message history as-is, append new message as HumanMessage
        messages = list(messages_history) + [HumanMessage(content=message)]
        return messages

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
    ) -> AsyncIterator[Union[str, dict]]:
        """Stream response from a LangGraph agent using the assistant -> thread -> run pattern.
        Yields raw message content (str or dict with content/elements/file keys) for the chat service to convert to NDJSON.

        Args:
            messages_history: List of previous conversation messages (dicts with 'role' and 'content')
            message: The new user message string
            conversation_id: Not used by LangGraph connector (kept for interface compatibility)
            files: Not used by LangGraph connector (kept for interface compatibility)
            metadata: Optional {user: {user_id, username, ad_group}, conversation: {conversation_id}}
            attachments: Optional list of {id, name, mime, uri}
            context: Optional {timezone, locale}
            thread_id: Thread ID for this conversation. If not provided, creates a new thread
                (caller should persist it via db_chat.set_conversation_thread_id).

        Yields:
            Text chunks from the agent response
        """
        # Prepare messages: pass history as-is, append new message as HumanMessage
        messages = self._prepare_messages(messages_history, message)

        client = self._get_client()
        input_data = {
            "messages": messages,
            "metadata": metadata,
            "attachments": attachments,
            "context": context,
        }

        # # print(f"[LangGraph] Input data: {input_data}")
        # Ensure initialized
        if not self._initialized:
            await self.initialize()

        # Normalize metadata["user"] to dict if it is a Pydantic model (for JSON serialization)
        if (
            metadata
            and "user" in metadata
            and hasattr(metadata.get("user"), "model_dump")
        ):
            metadata = {**metadata, "user": metadata["user"].model_dump()}

        # Create thread when none provided (caller is responsible for persisting thread_id)
        if thread_id is None:
            thread_id = await self.create_thread(metadata=metadata)

        # Agent name is the selected assistant name — use it as the assistant_id
        assistant_id = self.name
        agent_id = self.agent.get("id")

        run_config = self.extras.get("run_config", {})
        if "configurable" not in run_config:
            run_config["configurable"] = {"configurable": {"thread_id": thread_id}}
        else:
            run_config["configurable"]["thread_id"] = thread_id

        logger.debug(
            "Starting run - thread_id: {}, agent_id: {}, assistant_id: {}",
            thread_id,
            agent_id,
            assistant_id,
        )
        logger.debug(
            "Input data keys: {}, messages count: {}",
            list(input_data.keys()),
            len(messages),
        )

        try:
            command = {}
            if thread_id in interrupt_thread_id:
                logger.debug("Resume from interrupt - thread_id: {}", thread_id)
                interrupt_thread_id.remove(thread_id)
                command = Command(resume=input_data)
            async for chunk in self._stream_messages(
                client, thread_id, assistant_id, input_data, run_config, command
            ):
                yield chunk
            logger.debug(
                "Run completed successfully - thread_id: {}, assistant_id: {}",
                thread_id,
                assistant_id,
            )
        except Exception as e:
            logger.opt(exception=True).error(
                "LangGraph error - thread_id: {}, assistant_id: {}",
                thread_id,
                assistant_id,
            )
            yield f"LangGraph error: {str(e)}"

    async def _stream_messages(
        self,
        client,
        thread_id: str,
        assistant_id: str,
        input_data: dict,
        run_config: dict,
        command: Optional[List[Command]] = None,
    ) -> AsyncIterator[Union[str, dict]]:
        """Stream using messages mode (for streaming LLMs).

        Args:
            client: The LangGraph client
            thread_id: The thread ID for this conversation
            assistant_id: The assistant ID to use
            input_data: Input data for the run
            run_config: Configuration for the run
        """

        async for event in client.runs.stream(
            thread_id=thread_id,
            command=command,
            assistant_id=assistant_id,
            input=input_data,
            config=run_config,
            stream_mode=["messages-tuple", "updates"],
        ):
            logger.debug("Event: {}", event.event)
            if "__interrupt__" in event.data:
                interrupt_data = event.data["__interrupt__"]
                interrupt_thread_id.append(thread_id)
                if isinstance(interrupt_data, list) and len(interrupt_data) > 0:
                    interrupt_item = interrupt_data[0]
                    if isinstance(interrupt_item, dict) and "value" in interrupt_item:
                        value = interrupt_item["value"]
                        if value:
                            yield value
                            continue
                yield str(interrupt_data)
            if event.event == "messages" or event.event == "updates":
                data = event.data
                msg = data[0] if isinstance(data, list) and len(data) > 0 else data
                raw = (
                    msg.get("content")
                    if isinstance(msg, dict)
                    else getattr(msg, "content", None)
                )
                if raw:
                    yield raw

    async def _stream_values(
        self,
        client,
        thread_id: str,
        assistant_id: str,
        input_data: dict,
        run_config: dict,
    ) -> AsyncIterator[Union[str, dict]]:
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
            logger.debug("Event: {}", event.event)

            if event.event == "values":
                data = event.data
                if isinstance(data, dict) and "messages" in data:
                    msgs = data["messages"]
                    if msgs and len(msgs) > 0:
                        last_msg = msgs[-1]
                        role = (
                            last_msg.get("type", "")
                            if isinstance(last_msg, dict)
                            else getattr(last_msg, "type", "")
                        )
                        if role in ("ai", "assistant", "AIMessage") or not role:
                            raw = (
                                last_msg.get("content")
                                if isinstance(last_msg, dict)
                                else getattr(last_msg, "content", None)
                            )
                            if raw and raw != last_message_content:
                                last_message_content = raw
                                yield raw

    async def close(self):
        """Close the LangGraph client if initialized."""
        if self._client is not None:
            logger.debug("Releasing LangGraph client reference")
            self._client = None
