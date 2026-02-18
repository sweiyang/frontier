import json
import base64
import os
from src.schema import State
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver, InMemorySaver
from langgraph.types import interrupt, Command
from typing import Literal


def choice_node(state: State) -> Command[Literal["companies_table", "full_scan", "end"]]:
    """Present choices to the user via interrupt."""
    print(f"[Choice Node] State: {state}")
    
    choice = interrupt({
        "type": "choice_required",
        "title": "Select an action",
        "content": "Welcome to CPCR Mockup. Please select an action. Quick Scan or Full Scan",
    })
    choice = choice["messages"][0]["content"]
    print(f"[LangGraph] Choice: {choice}")
    if choice and isinstance(choice, str):
        if choice == "quick scan":
            return Command(goto="companies_table")
        elif choice == "full_scan":
            return Command(goto="full_scan")
    # Default to end if no valid choice
    return Command(goto="end")

def quick_scan(state: State):
    """Run quick scan flow; accumulate user choices in state['elements']."""
    # Start from previous state so we carry forward any existing elements
    elements = dict(state.get("elements") or {})

    companies_table = [
        {
            "type": "table",
            "id": "companies_table",
            "title": "Companies List",
            "columns": [{"key": "name", "label": "Name"}],
            "rows": [{"id": 1, "name": "Company 1"}, {"id": 2, "name": "Company 2"}],
            "searchable": True,
            "select_mode": "multi",
        }
    ]
    msg_content = json.dumps({
        "content": "Please select your company, you can select more than one. Type done in the chatbox after you are done :)",
        "elements": companies_table,
    })
    choice = interrupt(AIMessage(content=msg_content))
    print(f"[LangGraph] Choice: {choice}")
    metadata = choice.get("metadata") or {}
    frontend = metadata.get("frontend") or {}
    frontend_choice = frontend.get("companies_table", {}).get("selected", [])
    print(f"[LangGraph] Frontend Choice: {frontend_choice}")

    # Persist companies selection and optional snapshot for downstream
    elements["companies_selected"] = frontend_choice
    elements["companies_table_snapshot"] = companies_table

    if len(frontend_choice) > 0:
        msg_content = json.dumps({
            "content": f"Awesome! You have selected {len(frontend_choice)} companies. Kindly input the questions you would like to ask in order to generate a quick scan report! :D",
        })
        choice = interrupt(AIMessage(content=msg_content))
        print(f"[LangGraph] questions Choice: {choice}")
        questions_text = (choice.get("messages") or [{}])[0].get("content") or ""
        elements["quick_scan_questions"] = questions_text

    results_table = [
        {
            "type": "table",
            "id": "results_table",
            "title": "Results List",
            "columns": [
                {"key": "company_name", "label": "company_name"},
                {"key": "cif", "label": "CIF"},
                {"key": "model_type", "label": "Model Type"},
                {"key": "risk", "label": "Risk"},
                {"key": "mitigation", "label": "Mitigation"},
            ],
            "rows": [
                {"id": 1, "company_name": "Company 1", "cif": "1234567890", "model_type": "Model Type 1", "risk": "Risk 1", "mitigation": "Mitigation 1"},
                {"id": 2, "company_name": "Company 2", "cif": "1234567890", "model_type": "Model Type 2", "risk": "Risk 2", "mitigation": "Mitigation 2"},
            ],
            "searchable": True,
            "select_mode": "multi",
        }
    ]
    msg_content = json.dumps({
        "content": "Awesome great questions! Here are the results for your quick scan report shown on your right! </br> Kindly perform the following actions. </br> 1. Select the results that you disagree with </br> 2. Reply \"ask more questions\" to ask more questions </br> 3. Reply \"select more companies\" to select more companies or </br> 4. Reply \"generate full report\" to proceed to generate a full report or </br> 5. Reply \"end\" to end the conversation! :D",
        "elements": results_table,
    })
    choice = interrupt(AIMessage(content=msg_content))
    print(f"[LangGraph] results Choice: {choice}")
    metadata = choice.get("metadata") or {}
    frontend = metadata.get("frontend") or {}
    results_selected = frontend.get("results_table", {}).get("selected", [])
    elements["results_selected"] = results_selected
    elements["results_table_snapshot"] = results_table

    return Command(update={"elements": elements}, goto="end")


def companies_table(state: State):
    """Run quick scan flow; accumulate user choices in state['elements']."""
    # Start from previous state so we carry forward any existing elements
    elements = dict(state.get("elements") or {})
    print(f"[LangGraph] companies_table state elements: {list(elements.keys())}")
    companies_table = [
        {
            "type": "table",
            "id": "companies_table",
            "title": "Companies List",
            "columns": [{"key": "name", "label": "Name"}],
            "rows": [{"id": 1, "name": "Company 1"}, {"id": 2, "name": "Company 2"}],
            "searchable": True,
            "select_mode": "multi",
        }
    ]
    msg_content = json.dumps({
        "content": "Please select your company, you can select more than one. Type done in the chatbox after you are done :)",
        "elements": companies_table,
    })
    choice = interrupt(AIMessage(content=msg_content))
    print(f"[LangGraph] Choice: {choice}")
    metadata = choice.get("metadata") or {}
    frontend = metadata.get("frontend") or {}
    frontend_choice = frontend.get("companies_table", {}).get("selected", [])
    print(f"[LangGraph] Frontend Choice: {frontend_choice}")
    # Persist companies selection and optional snapshot for downstream
    elements["companies_selected"] = frontend_choice
    elements["companies_table_snapshot"] = companies_table
    return Command(update={"elements": elements})


def ask_questions(state: State):
    """Ask questions to the user."""
    elements = dict(state.get("elements") or {})
    print(f"[LangGraph] ask questions elements: {elements}")
    frontend_choice = elements.get("companies_selected") or []
    msg_content = json.dumps({
        "content": f"Awesome! You have selected {len(frontend_choice)} companies. Kindly input the questions you would like to ask in order to generate a quick scan report! If you already have done so, type \"next\" to proceed to the next step. ",
    })
    state_questions = state.get("quick_scan_questions") or []
    print(f"[LangGraph] state questions 1: {state_questions}")
    choice = interrupt(AIMessage(content=msg_content))
    print(f"[LangGraph] questions Choice: {choice}")
    questions_text = (choice.get("messages") or [{}])[0].get("content") or ""
    state_questions = elements.get("quick_scan_questions") or []
    print(f"[LangGraph] state questions 2: {state_questions}")
    elements["quick_scan_questions"] = state_questions + [questions_text]
    print(f"[LangGraph] questions: {elements['quick_scan_questions']}")
    return Command(update={"elements": elements})
    
def results_table(state: State) -> Command[Literal["ask_questions", "companies_table", "full_scan", "end"]]:
    elements = dict(state.get("elements") or {})
    questions_row = []

    for questions in elements.get("quick_scan_questions", []):
        questions_row.append({
            "id": len(questions_row) + 1,
            "question": questions,
        })
    results_table = [
        {
            "type": "table",
            "id": "questions_table",
            "title": "Questions List",
            "columns": [{"key": "question", "label": "Question"}],
            "rows": questions_row,
            "searchable": True,
            # "select_mode": "multi",
        },

        {
            "type": "table",
            "id": "results_table",
            "title": "Results List",
            "columns": [
                {"key": "company_name", "label": "company_name"},
                {"key": "cif", "label": "CIF"},
                {"key": "model_type", "label": "Model Type"},
                {"key": "risk", "label": "Risk"},
                {"key": "mitigation", "label": "Mitigation"},
            ],
            "rows": [
                {"id": 1, "company_name": "Company 1", "cif": "1234567890", "model_type": "Model Type 1", "risk": "Risk 1", "mitigation": "Mitigation 1"},
                {"id": 2, "company_name": "Company 2", "cif": "1234567890", "model_type": "Model Type 2", "risk": "Risk 2", "mitigation": "Mitigation 2"},
            ],
            "searchable": True,
            "select_mode": "multi",
        }
    ]
    # Read Chat2VIS.pdf and base64 encode it for file download
    pdf_path = os.path.join(os.path.dirname(__file__), "Chat2VIS.pdf")
    pdf_b64 = ""
    try:
        with open(pdf_path, "rb") as f:
            pdf_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"[CPCR] Error reading PDF: {e}")

    msg_content = json.dumps({
        "content": "Awesome great questions! Here are the results for your quick scan report shown on your right! </br> Kindly perform the following actions. </br> 1. Select the results that you disagree with </br> 2. Reply \"ask more questions\" to ask more questions </br> 3. Reply \"select more companies\" to select more companies or </br> 4. Reply \"generate full report\" to proceed to generate a full report or </br> 5. Reply \"end\" to end the conversation! :D",
        "elements": results_table,
        "file": {
            "name": "Chat2VIS.pdf",
            "type": "application/pdf",
            "content": pdf_b64,
        },
    })
    choice = interrupt(AIMessage(content=msg_content))
    print(f"[LangGraph] results Choice: {choice}")
    print(choice.get("messages")[0])
    msg = choice.get("messages")[0].get("content") or ""
    metadata = choice.get("metadata") or {}
    frontend = metadata.get("frontend") or {}
    results_selected = frontend.get("results_table", {}).get("selected", [])
    elements["results_selected"] = results_selected
    elements["results_table_snapshot"] = results_table
    print(f"[LangGraph] elements: {elements}")
    if msg == "ask more questions":
        return Command(update={"elements": elements},goto="ask_questions")
    elif msg == "select more companies":
        return Command(update={"elements": elements},goto="companies_table")
    elif msg == "generate full report":
        return Command(update={"elements": elements},goto="full_scan")
    elif msg == "end":
        return Command(update={"elements": elements},goto="end")
    

def full_scan(state: State):
    """Full scan path; can use state['elements'] from previous steps (e.g. quick_scan)."""
    elements = state.get("elements") or {}
    # Example: use companies_selected or results_selected for full report
    print(f"[LangGraph] full_scan state elements: {list(elements.keys())}")
    return Command(goto="end")

def end_node(state: State):
    return {
        "messages": [AIMessage(content="Thank you for using CPCR Mockup. Goodbye!")],
    }
# Checkpointer REQUIRED for interrupt resume
builder = StateGraph(State)

# Add nodes
builder.add_node("choice", choice_node)
builder.add_node("quick_scan", quick_scan)
builder.add_node("companies_table", companies_table)
builder.add_node("ask_questions", ask_questions)
builder.add_node("results_table", results_table)
builder.add_node("full_scan", full_scan)
builder.add_node("end", end_node)

# Add edges
builder.add_edge(START, "choice")
builder.add_edge("choice", "companies_table")
# builder.add_edge("quick_scan", "end")
# builder.add_edge("full_scan", "end")
builder.add_edge("companies_table", "ask_questions")
builder.add_edge("ask_questions", "results_table")
# builder.add_edge("results_table", "full_scan")
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