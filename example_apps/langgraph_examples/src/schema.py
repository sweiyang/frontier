from typing import TypedDict, Annotated, Optional, Dict, Any
from langgraph.graph.message import add_messages
from typing import List

# class State(TypedDict):
#     messages: Annotated[list, add_messages]
#     user_request: str
#     proposed_action: Optional[Dict[str, Any]]  # {"tool": str, "args": dict}
#     tool_result: Optional[str]
#     final_answer: Optional[str]

class State(TypedDict):
    """Request payload for LangGraphConnector.stream().

    Attributes:
        messages: Conversation history + current user message. Each has "role" and "content".
        metadata: User and conversation info.
        attachments: Optional attachments referenced by URI (e.g. S3).
        context: Optional timezone, locale, etc.
    """

    messages: List[Dict[str, Any]]  # [{"role", "content"}, ...]
    metadata: any
    attachments: any
    context: any