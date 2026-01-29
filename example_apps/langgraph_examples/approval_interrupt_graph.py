from src.schema import State
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver, InMemorySaver
from langgraph.types import interrupt, Command
from langchain_core.tools import tool
from typing import Literal


# Simple tools that can be executed based on user choice
@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city."""
    return f"The weather in {city} is sunny, 32°C"


@tool
def get_time(timezone: str = "UTC") -> str:
    """Get the current time for a given timezone."""
    return f"Current time in {timezone} is 10:30 AM"


@tool
def calculate(expression: str) -> str:
    """Calculate a simple mathematical expression."""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except:
        return f"Error: Could not calculate {expression}"


# Choice node that interrupts with options
def choice_node(state: State) -> Command[Literal["weather", "time", "calculate", "end"]]:
    """Present choices to the user via interrupt."""
    print(f"[Choice Node] State: {state}")
    
    # Interrupt with choices - the interrupt returns the selected action ID when resumed
    choice = interrupt({
        "type": "choice_required",
        "title": "Select an action",
        "message": "What would you like to do?",
        "actions": [
            {"id": "weather", "label": "Get Weather"},
            {"id": "time", "label": "Get Time"},
            {"id": "calculate", "label": "Calculate"},
            {"id": "end", "label": "Exit"}
        ]
    })
    print(f"[LangGraph] Choice: {choice}")
    # The interrupt returns the selected action ID (or None/False if cancelled)
    # Route based on user's choice
    if choice and isinstance(choice, str):
        if choice == "weather":
            return Command(goto="weather")
        elif choice == "time":
            return Command(goto="time")
        elif choice == "calculate":
            return Command(goto="calculate")
        elif choice == "end":
            return Command(goto="end")
    
    # Default to end if no valid choice
    return Command(goto="end")


# Tool execution nodes
def weather_node(state: State) -> State:
    """Execute weather tool."""
    # In a real scenario, you'd extract parameters from state
    # For simplicity, using a default city
    result = get_weather.invoke({"city": "Tokyo"})
    return {
        "messages": state["messages"] + [AIMessage(content=result)],
        "metadata": state.get("metadata"),
        "attachments": state.get("attachments"),
        "context": state.get("context"),
    }


def time_node(state: State) -> State:
    """Execute time tool."""
    result = get_time.invoke({"timezone": "UTC"})
    return {
        "messages": state["messages"] + [AIMessage(content=result)],
        "metadata": state.get("metadata"),
        "attachments": state.get("attachments"),
        "context": state.get("context"),
    }


def calculate_node(state: State) -> State:
    """Execute calculate tool."""
    # In a real scenario, you'd extract the expression from state
    result = calculate.invoke({"expression": "2 + 2"})
    return {
        "messages": state["messages"] + [AIMessage(content=result)],
        "metadata": state.get("metadata"),
        "attachments": state.get("attachments"),
        "context": state.get("context"),
    }


def end_node(state: State) -> State:
    """End node."""
    return {
        "messages": state["messages"] + [AIMessage(content="Goodbye!")],
        "metadata": state.get("metadata"),
        "attachments": state.get("attachments"),
        "context": state.get("context"),
    }


# Checkpointer REQUIRED for interrupt resume
builder = StateGraph(State)

# Add nodes
builder.add_node("choice", choice_node)
builder.add_node("weather", weather_node)
builder.add_node("time", time_node)
builder.add_node("calculate", calculate_node)
builder.add_node("end", end_node)

# Add edges
builder.add_edge(START, "choice")
builder.add_edge("weather", END)
builder.add_edge("time", END)
builder.add_edge("calculate", END)
builder.add_edge("end", END)

# Compile the graph
if __name__ == "__main__":
    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "choice-demo-001"}}

    # First invoke: should INTERRUPT with choices
    first = graph.invoke(
        {"messages": [HumanMessage(content="I need help")]},
        config=config,
    )

    print(f"[LangGraph] First: {first}")

    if "__interrupt__" in first:
        print("\n=== INTERRUPTED (choices presented) ===")
        print(first["__interrupt__"])

        # User selects a choice (e.g., "weather")
        # In real usage, the choice would come from the UI
        # For demo, we'll simulate selecting "weather"
        # The resume value should match the action ID from the interrupt
        result = graph.invoke(Command(resume="weather"), config=config)
        print("\n=== AFTER CHOICE (weather) ===")
        print(result["messages"][-1].content)
    else:
        print("\n=== DONE ===")
        print(first["messages"][-1].content)
else:
    # checkpointer = InMemorySaver()
    graph = builder.compile()   