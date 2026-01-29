from langgraph.graph import StateGraph, START, END
from src.chat import chatbot
from src.schema import State

builder = StateGraph(State)   
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

graph = builder.compile()

if __name__ == "__main__":
    # Invoke the graph
    result = graph.invoke(
        {"messages": [{"role": "user", "content": "what is langgraph?"}]}
    )
    # Print the result
    print(result["messages"][-1].content)