"""
LangGraph example: all Frontier dynamic UI elements and file download.

This app is a user guide and test harness. It uses the dict-based response contract:
return a plain dict with "content", "elements", and/or "file" — no json.dumps.

Run this graph with LangGraph Studio or deploy to LangGraph Cloud, then point
Frontier's LangGraph agent at it. Flow:

  1. Welcome + Stats + button
  2. Table + search_bar + button (submit selection)
  3. Markdown table (rendered in chat with CSV download)
  4. Text input (multiline) + button
  5. Long-running process simulation (30s sleep)
  6. File download
  7. Clear panel + goodbye
"""

import base64
import sys
import time
from pathlib import Path

# Allow importing shared schema when running from example_apps or langgraph_example
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import AIMessageChunk
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from schema import State
from shared.schema import AgentResponse, FileAttachment

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
        step_name="Welcome",
        step_description="Greets the user and displays sample stats with a Get Started button.",
        content="Welcome to the Frontier elements demo. Below are sample **stats** and a button.",
        elements=[
            {
                "type": "stats",
                "id": "welcome_metrics",
                "title": "Overview",
                "layout": "row",
                "stats": [
                    {
                        "label": "Requests/s",
                        "value": 1250,
                        "unit": "req/s",
                        "color": "green",
                        "trend": "up",
                    },
                    {
                        "label": "Error rate",
                        "value": 0.2,
                        "unit": "%",
                        "color": "green",
                        "trend": "down",
                    },
                    {
                        "label": "P99 latency",
                        "value": 145,
                        "unit": "ms",
                        "color": "yellow",
                    },
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
        step_name="Table Selection",
        step_description="Presents a searchable, multi-select data table for company selection.",
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


# ---- Step 3: Markdown table (rendered in chat) ----


def markdown_table_step(state: State) -> dict:
    """Return a markdown table in the content field so it renders in the chat bubble.

    The frontend adds Copy and Download CSV buttons automatically.
    """
    table_md = (
        "Here is a summary report:\n\n"
        "| Metric | Q1 | Q2 | Q3 | Q4 |\n"
        "|---|---|---|---|---|\n"
        "| Revenue | $1.2M | $1.5M | $1.8M | $2.1M |\n"
        "| Users | 12,400 | 15,800 | 19,200 | 24,500 |\n"
        "| Churn | 3.2% | 2.8% | 2.5% | 2.1% |\n"
        "\nYou can download this table as CSV or copy it using the buttons above the table."
    )
    payload = AgentResponse(
        step_name="Markdown Table",
        step_description="Displays a markdown table with CSV download and copy support.",
        content=table_md,
    ).model_dump(exclude_none=True)
    interrupt(payload)
    return {"step": 3}


# ---- Step 4: Text input (multiline) + Button ----


def form_step(state: State) -> dict:
    """Show a multiline text input and submit button."""
    payload = AgentResponse(
        step_name="Form Input",
        step_description="Collects free-form notes from the user via a multiline text area.",
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
    return {"step": 4}


# ---- Step 5: Long-running process simulation ----


LLM_CHUNKS = [
    "Let me analyze the data ",
    "you provided.\n\n",
    "Based on the quarterly metrics, ",
    "revenue shows a **strong upward trend** ",
    "growing from $1.2M to $2.1M — ",
    "a 75% increase year-over-year.\n\n",
    "User growth is equally impressive, ",
    "with the base nearly **doubling** ",
    "from 12,400 to 24,500 users.\n\n",
    "Meanwhile, churn has steadily decreased ",
    "from 3.2% to 2.1%, ",
    "indicating improved retention.\n\n",
    "Overall, these are very healthy indicators ",
    "for the business.",
]


def long_running_step(state: State) -> dict:
    """Simulate LLM-style streaming: yield text chunks with pauses between them."""
    writer = get_stream_writer()
    for chunk in LLM_CHUNKS:
        writer(AIMessageChunk(content=chunk))
        time.sleep(2)
    payload = AgentResponse(
        step_name="Long Process",
        step_description="Simulates LLM-style streaming with pauses between chunks.",
        content="Analysis complete.",
    ).model_dump(exclude_none=True)
    interrupt(payload)
    return {"step": 5}


# ---- Step 6: File download ----


def file_download_step(state: State) -> dict:
    """Return a small file for download (dict with content + file)."""
    sample_content = b"Frontier elements demo - file download.\n\nThis file was generated by the LangGraph example."
    b64 = base64.b64encode(sample_content).decode("ascii")
    payload = AgentResponse(
        step_name="File Download",
        step_description="Generates a sample text file and returns it as a base64 download.",
        content="Here is your demo file. Click the download link in the message.",
        file=FileAttachment(name="demo_download.txt", type="text/plain", content=b64),
    ).model_dump(exclude_none=True)
    interrupt(payload)
    return {"step": 6}


# ---- Step 7: Clear panel + goodbye ----


def goodbye_step(state: State) -> dict:
    """Clear the panel and send a goodbye message."""
    payload = AgentResponse(
        step_name="Goodbye",
        step_description="Clears the dynamic panel and sends a farewell message.",
        content="Thanks for trying the Frontier elements demo. The panel is now cleared.",
        elements=[],
    ).model_dump(exclude_none=True)
    interrupt(payload)
    return {"step": 7}


# ---- Router: next step from user message ----


def route_after_welcome(state: State) -> str:
    """Route to the table step after welcome."""
    return "table"


def route_after_table(state: State) -> str:
    """Route to the markdown table step after table."""
    return "markdown_table"


def route_after_markdown_table(state: State) -> str:
    """Route to long-running step after markdown table to test loading display."""
    return "long_running"


def route_after_form(state: State) -> str:
    """Route to long-running process after form."""
    return "long_running"


def route_after_long_running(state: State) -> str:
    """Route to file download after long-running process."""
    return "file_download"


def route_after_file(state: State) -> str:
    """Route to goodbye after file download."""
    return "goodbye"


def route_after_goodbye(state: State) -> str:
    """End the graph after goodbye."""
    return END


# ---- Graph ----


def build_graph():
    """Build and compile the LangGraph state machine."""
    builder = StateGraph(State)
    builder.add_node("welcome", welcome)
    builder.add_node("table", table_step)
    builder.add_node("markdown_table", markdown_table_step)
    builder.add_node("form", form_step)
    builder.add_node("long_running", long_running_step)
    builder.add_node("file_download", file_download_step)
    builder.add_node("goodbye", goodbye_step)

    builder.add_edge(START, "welcome")
    builder.add_conditional_edges("welcome", route_after_welcome)
    builder.add_conditional_edges("table", route_after_table)
    builder.add_conditional_edges("markdown_table", route_after_markdown_table)
    builder.add_conditional_edges("form", route_after_form)
    builder.add_conditional_edges("long_running", route_after_long_running)
    builder.add_conditional_edges("file_download", route_after_file)
    builder.add_conditional_edges("goodbye", route_after_goodbye)

    return builder.compile()


graph = build_graph()
