
from typing import TypedDict, Optional, Dict, Any, Literal
from langgraph.types import interrupt, Command
from ..schema import State
from langchain_core.messages import AIMessage
from langgraph.graph import END


def approval_gate(state: State) -> Command[Literal["cancel", END]]:
    print(f"[LangGraph] State: {state}")
    last = state["messages"][-1]
    print(f"[LangGraph] Last message: {last}")
    # If the last message is NOT an AI message, just finish safely
    if not isinstance(last, AIMessage):
        return Command(goto="end")

    # If there are no tool calls, we can finish
    tool_calls = getattr(last, "tool_calls", None)
    print(f"[LangGraph] Tool calls: {tool_calls}")

    if not tool_calls:
        return Command(goto="end")

    # Interrupt -> UI should ask user for approval
    """
        recommended structure 
            interrupt({
            "type": "approval_required",
            "reason": "tool_call",
            "title": "Approve tool execution",
            "message": "The agent wants to call `send_email`.",
            "context": {
                "tool_name": "send_email",
                "tool_args": {
                    "to": "user@example.com",
                    "subject": "Invoice",
                }
            },
            "actions": [
                {"id": "approve", "label": "Approve"},
                {"id": "deny", "label": "Deny"},
                {"id": "edit", "label": "Edit & approve"}
            ]
        })
    """
    print(f"[LangGraph] proceed to interrupt")

    # approved = interrupt({
    #     "type": "approval_required",
    #     "question": "Approve executing these tool calls?",
    #     "tool_calls": tool_calls,
    # })

    approved = interrupt(State(
        messages= [AIMessage(content="Approve executing these tool calls?")],
        metadata= None,
        attachments= None,
        context= None
    ))

    return Command(goto="tools" if approved else "end")