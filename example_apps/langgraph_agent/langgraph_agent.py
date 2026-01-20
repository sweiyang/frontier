"""
LangGraph Agent with Mock Streaming LLM

A chat agent that simulates streaming responses (no real LLM required).
Serve with: langgraph dev --host 0.0.0.0 --port 9000
"""

from os import name
import time
from typing import Annotated, TypedDict, List, Iterator, Any, Optional, Dict

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


class MockStreamingLLM(BaseChatModel):
    """A fake LLM that simulates streaming responses."""
    
    delay: float = 0.03  # Delay between tokens in seconds
    
    @property
    def _llm_type(self) -> str:
        return "mock-streaming"
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a complete response (non-streaming fallback)."""
        # agent_id = kwargs.get("agent_id")
        # Note: metadata is reserved by LangChain, so we don't extract it from kwargs
        # If needed, it should be accessed from the state/context instead
        content = self._build_response(messages)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])
    
    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Stream the response token by token."""
        agent_id = kwargs.get("agent_id")
        # Note: metadata is reserved by LangChain, so we don't extract it from kwargs
        # If needed, it should be accessed from the state/context instead
        content = self._build_response(messages, agent_id=agent_id)
        
        # Stream word by word
        words = content.split(" ")
        for i, word in enumerate(words):
            token = f" {word}" if i > 0 else word
            time.sleep(self.delay)
            chunk = ChatGenerationChunk(message=AIMessageChunk(content=token))
            if run_manager:
                run_manager.on_llm_new_token(token)
            yield chunk
    
    def _build_response(self, messages: List[BaseMessage], agent_id: Optional[int] = None) -> str:
        """Build a mock response based on input."""
        last_message = messages[-1] if messages else None
        if last_message:
            user_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            metadata_info = ""
            parts = []
            if agent_id is not None:
                parts.append(f"agent_id: {agent_id}")
            # Note: metadata is not passed here to avoid conflicts with LangChain's reserved parameter
            # If you need user/project info in the response, access it from the state in chat_node
            # graph_id and thread_id are reflected in chat_node after model invocation
            if parts:
                metadata_info = f" [Metadata: {', '.join(parts)}]"
            return f"I received your message: '{user_content}'. This is a mock streaming response from the LangGraph agent. Each word is streamed individually to simulate real LLM behavior!{metadata_info}"
        return "Hello! I'm a mock streaming LangGraph agent. How can I help you today?"


class MessagesState(TypedDict):
    """State containing the conversation messages and metadata."""
    messages: Annotated[list, add_messages]
    agent_id: Optional[int]  # Agent ID from the conduit system
    metadata: Optional[Dict[str, Any]]  # Metadata containing user details and other context
    graph_id: Optional[str]  # Graph ID (graph name)
    thread_id: Optional[str]  # Thread ID for this conversation


# Initialize the mock streaming LLM
model = MockStreamingLLM()


# Build the graph using the model directly for proper streaming
builder = StateGraph(MessagesState)

def chat_node(state: MessagesState) -> dict:
    """Chat node that processes messages with agent_id, graph_id, thread_id and user metadata."""
    messages = state.get("messages", [])
    agent_id = state.get("agent_id")
    metadata = state.get("metadata")
    graph_id = state.get("graph_id")
    thread_id = state.get("thread_id")
    
    # Log the metadata for debugging
    metadata_parts = []
    if graph_id:
        metadata_parts.append(f"graph_id={graph_id}")
    if thread_id:
        metadata_parts.append(f"thread_id={thread_id}")
    if agent_id is not None:
        metadata_parts.append(f"agent_id={agent_id}")
    if metadata:
        user_info = metadata.get("user", {})
        if user_info:
            user_id = user_info.get("user_id")
            username = user_info.get("username")
            if user_id or username:
                metadata_parts.append(f"user_id={user_id}, username={username}")
        project = metadata.get("project")
        if project:
            metadata_parts.append(f"project={project}")
    
    if metadata_parts:
        print(f"[LangGraph Agent] Processing with {', '.join(metadata_parts)}")
    
    # Invoke the model - don't pass metadata as it conflicts with LangChain's reserved parameter
    # Metadata is still available in state for logging/processing, but we don't pass it to invoke()
    # If you need metadata in the response, access it from state and include it separately
    response = model.invoke(
        messages,
        agent_id=agent_id
        # Note: metadata is reserved by LangChain, so we access it from state instead
    )
    
    # Include graph_id and thread_id in the response content
    if isinstance(response, AIMessage):
        original_content = response.content if hasattr(response, 'content') else str(response)
        reflection_parts = []
        if graph_id:
            reflection_parts.append(f"graph_id: {graph_id}")
        if thread_id:
            reflection_parts.append(f"thread_id: {thread_id}")
        
        if reflection_parts:
            reflection_info = f" [Reflected: {', '.join(reflection_parts)}]"
            # Modify the response to include the reflection
            response.content = original_content + reflection_info
    
    return {"messages": [response]}

builder.add_node("chat", chat_node)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)

# Compile the graph
graph = builder.compile(name="lg")
