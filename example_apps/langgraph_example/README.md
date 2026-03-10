# LangGraph Example — Conduit Elements Demo

This example demonstrates **all** Conduit dynamic UI elements and file download using the **dict-based response contract**. It uses the shared schema from `example_apps/shared/schema.py` so responses stay consistent with the HTTP example.

## Response contract

Return from your nodes (e.g. via `interrupt()`) either:

- **Plain string**: `"Hello world"`
- **Structured dict** with optional keys:
  - `content` (str): message text
  - `elements` (list): UI elements (button, text_input, search_bar, table, stats)
  - `file` (dict): `{ "name", "type", "content" }` (base64) for download

Example (using shared schema):

```python
from shared.schema import AgentResponse, FileAttachment

interrupt(AgentResponse(
    content="Select your company",
    elements=[
        {"type": "table", "id": "companies", "title": "Companies", "columns": [...], "rows": [...]},
        {"type": "button", "id": "submit", "label": "Submit", "action": "send_message", "payload_template": "{{companies.selected}}"},
    ],
).model_dump(exclude_none=True))
```

## Flow

1. **Welcome** — Stats panel + "Get Started" button  
2. **Table** — Table with search_bar, multi-select, "Submit Selection" button  
3. **Form** — Multiline text_input + "Submit Notes" button  
4. **File download** — Message + file attachment  
5. **Goodbye** — Clear panel (`elements: []`) + message  

## Run

Use with [LangGraph Studio](https://github.com/langchain-ai/langgraph-studio) or deploy to LangGraph Cloud, then register the graph in Conduit as a LangGraph agent. The Conduit frontend will receive NDJSON events and render elements in the dynamic panel.

## Dependencies

See `requirements.txt`. Install with:

```bash
pip install -r requirements.txt
```
