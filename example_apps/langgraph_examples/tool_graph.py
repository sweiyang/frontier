from langchain_ollama import ChatOllama
from src.tool import get_weather, route_tools
from src.schema import State
from src.chat import llm
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode


llm_with_tools = llm.bind_tools([get_weather])
tool_node = ToolNode([get_weather])

builder = StateGraph(State)

# Add nodes
builder.add_node("chatbot", lambda s: {"messages": [llm_with_tools.invoke(s["messages"])]})
builder.add_node("tools", tool_node)

builder.add_edge(START, "chatbot")

# route to using tools, routs_tools is the function that determines if the last message is a tool call
#  {"tools": "tools", END: END} is mapping the return value of route_tools. For eg: {"<returned by the fuction>": node_name_initialised}
builder.add_conditional_edges("chatbot", route_tools, {"tools": "tools", END: END})

# Loop back to chatbot
builder.add_edge("tools", "chatbot")
# Compile the graph
graph = builder.compile()

if __name__ == "__main__":
    # Invoke the graph
    result = graph.invoke(
        {"messages": [{"role": "user", "content": "what is the weather in Tokyo?"}]}
    )
    # Print the result
    print(result["messages"][-1].content)