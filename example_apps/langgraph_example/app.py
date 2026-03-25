"""
LangGraph example: all Frontier dynamic UI elements and file download.

This app is a user guide and test harness. It uses the dict-based response contract:
return a plain dict with "content", "elements", and/or "file" — no json.dumps.

Run this graph with LangGraph Studio or deploy to LangGraph Cloud, then point
Frontier's LangGraph agent at it. Flow:

  1. Welcome + Stats + button
  2. Table + search_bar + button (submit selection)
  3. Text input (multiline) + button
  4. File download
  5. Clear panel + goodbye
"""

import base64
import sys
from pathlib import Path

# Allow importing shared schema when running from example_apps or langgraph_example
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt

from shared.schema import AgentResponse, FileAttachment
from schema import State


# ---- Step 1: Welcome + Stats + Button ----

def welcome(state: State) -> dict:
    """Send stats elements and a Get Started button. Interrupt for user click.

    Frontier forwards user metadata in the run config. In a LangGraph node you
    can access it via the RunnableConfig:

        from langchain_core.runnables import RunnableConfig

        def my_node(state: State, config: RunnableConfig) -> dict:
            metadata = config.get("configurable", {}).get("metadata", {})
            user = metadata.get("user", {})
            username = user.get("username")
            display_name = user.get("display_name")
            email = user.get("email")
            ad_groups = user.get("ad_group", [])
    """
    payload = AgentResponse(
        content="Welcome to the Frontier elements demo. Below are sample **stats** and a button.",
        elements=[
            {
                "type": "stats",
                "id": "welcome_metrics",
                "title": "Overview",
                "layout": "row",
                "stats": [
                    {"label": "Requests/s", "value": 1250, "unit": "req/s", "color": "green", "trend": "up"},
                    {"label": "Error rate", "value": 0.2, "unit": "%", "color": "green", "trend": "down"},
                    {"label": "P99 latency", "value": 145, "unit": "ms", "color": "yellow"},
                ],
            },
            {
                "type": "button",
                "id": "get_started",
                "label": "Get Started",
                "variant": "primary",
                "action": "send_message",
                "payload_template": "start",
            },
        ],
    ).model_dump(exclude_none=True)
    interrupt(payload)
    return {"step": 1}


# ---- Step 2: Table + Search bar + Button ----

TABLE_ROWS = [
    {"id": 1, "name": "Acme <br/> Corp", "role": "Vendor"},
    {"id": 2, "name": "Globex", "role": "Partner"},
    {"id": 3, "name": "Initech", "role": "Customer"},
]


def table_step(state: State) -> dict:
    """Show a table with search_bar and a submit button. Interrupt for selection."""
    payload = AgentResponse(
        content="Select one or more rows from the table. Use the search bar to filter. Then click Submit.",
        elements=[
            {
                "type": "search_bar",
                "id": "company_search",
                "target": "companies_table",
                "placeholder": "Filter companies...",
            },
            {
                "type": "table",
                "id": "companies_table",
                "title": "Companies",
                "columns": [
                    {"key": "name", "label": "Name", "sortable": True},
                    {"key": "role", "label": "Role"},
                ],
                "rows": TABLE_ROWS,
                "select_mode": "multi",
                "searchable": True,
                "page_size": 10,
            },
            {
                "type": "button",
                "id": "submit_selection",
                "label": "Submit Selection",
                "action": "send_message",
                "payload_template": "Selected: {{companies_table.selected}}",
            },
        ],
    ).model_dump(exclude_none=True)
    interrupt(payload)
    return {"step": 2}


# ---- Step 3: Text input (multiline) + Button ----

def form_step(state: State) -> dict:
    """Show a multiline text input and submit button."""
    payload = AgentResponse(
        content="Enter your notes in the text area below, then click Submit.",
        elements=[
            {
                "type": "text_input",
                "id": "notes_input",
                "label": "Notes",
                "placeholder": "Type here...",
                "multiline": True,
                "value": "",
            },
            {
                "type": "button",
                "id": "submit_notes",
                "label": "Submit Notes",
                "action": "send_message",
                "payload_template": "Notes: {{notes_input.value}}",
            },
        ],
    ).model_dump(exclude_none=True)
    interrupt(payload)
    return {"step": 3}


# ---- Step 4: File download ----

def file_download_step(state: State) -> dict:
    """Return a small file for download (dict with content + file)."""
    sample_content = b"Frontier elements demo - file download.\n\nThis file was generated by the LangGraph example."
    b64 = base64.b64encode(sample_content).decode("ascii")
    payload = AgentResponse(
        content="Here is your demo file. Click the download link in the message.",
        file=FileAttachment(name="demo_download.txt", type="text/plain", content=b64),
    ).model_dump(exclude_none=True)
    interrupt(payload)
    return {"step": 4}


# ---- Step 5: Clear panel + goodbye ----

def goodbye_step(state: State) -> dict:
    """Clear the panel and send a goodbye message."""
    payload = AgentResponse(
        content="Thanks for trying the Frontier elements demo. The panel is now cleared.",
        elements=[],
    ).model_dump(exclude_none=True)
    interrupt(payload)
    return {"step": 5}


# ---- Router: next step from user message ----

def route_after_welcome(state: State) -> str:
    return "table"


def route_after_table(state: State) -> str:
    return "form"


def route_after_form(state: State) -> str:
    return "file_download"


def route_after_file(state: State) -> str:
    return "goodbye"


def route_after_goodbye(state: State) -> str:
    return END


# ---- Graph ----

def build_graph():
    builder = StateGraph(State)
    builder.add_node("welcome", welcome)
    builder.add_node("table", table_step)
    builder.add_node("form", form_step)
    builder.add_node("file_download", file_download_step)
    builder.add_node("goodbye", goodbye_step)

    builder.add_edge(START, "welcome")
    builder.add_conditional_edges("welcome", route_after_welcome)
    builder.add_conditional_edges("table", route_after_table)
    builder.add_conditional_edges("form", route_after_form)
    builder.add_conditional_edges("file_download", route_after_file)
    builder.add_conditional_edges("goodbye", route_after_goodbye)

    return builder.compile()


graph = build_graph()
