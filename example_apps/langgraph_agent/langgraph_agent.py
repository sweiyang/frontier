"""
LangGraph Agent with Mock Streaming LLM

A chat agent that simulates streaming responses (no real LLM required).
Serve with: langgraph dev --host 0.0.0.0 --port 9000
"""

import time
from typing import Annotated, TypedDict, List, Iterator, Any, Optional

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
        content = self._build_response(messages)
        
        # Stream word by word
        words = content.split(" ")
        for i, word in enumerate(words):
            token = f" {word}" if i > 0 else word
            time.sleep(self.delay)
            chunk = ChatGenerationChunk(message=AIMessageChunk(content=token))
            if run_manager:
                run_manager.on_llm_new_token(token)
            yield chunk
    
    def _build_response(self, messages: List[BaseMessage]) -> str:
        """Build a mock response based on input."""
        last_message = messages[-1] if messages else None
        if last_message:
            user_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            return f"I received your message: '{user_content}'. This is a mock streaming response from the LangGraph agent. Each word is streamed individually to simulate real LLM behavior!"
        return "Hello! I'm a mock streaming LangGraph agent. How can I help you today?"


class MessagesState(TypedDict):
    """State containing the conversation messages."""
    messages: Annotated[list, add_messages]


# Initialize the mock streaming LLM
model = MockStreamingLLM()


# Build the graph using the model directly for proper streaming
builder = StateGraph(MessagesState)

# Use a lambda that calls the model - LangGraph will handle streaming
builder.add_node("chat", lambda state: {"messages": [model.invoke(state["messages"])]})

builder.add_edge(START, "chat")
builder.add_edge("chat", END)

# Compile the graph
graph = builder.compile()
