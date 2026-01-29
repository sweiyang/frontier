from schema import State

def propose_action(state: State) -> State:
    text = state["user_request"].lower()

    if "weather" in text:
        # naive extraction for demo
        city = "Tokyo" if "tokyo" in text else "Singapore"
        return {
            "proposed_action": {"tool": "get_weather", "args": {"city": city}},
            "tool_result": None,
            "final_answer": None,
        }

    # No tool needed
    return {
        "proposed_action": None,
        "tool_result": None,
        "final_answer": "No tool needed. Here’s a direct response...",
    }
