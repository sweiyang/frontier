from ..schema import State
from langchain_core.messages import AIMessage
def cancel_node(state: State) -> State:
    return {
        "messages": [
            AIMessage(content="Understood. I won’t execute that tool call. Tell me what you’d like to do instead.")
        ]
    }