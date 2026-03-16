# HTTP Agent Example — Frontier Elements Demo

This example is a **standalone FastAPI app** that acts as an HTTP agent for Frontier. It uses the shared schema from `example_apps/shared/schema.py` so request/response shapes stay consistent with the LangGraph example.

## Response contract

Return a dict with any of:

- `content` (str): message text
- `elements` (list): UI elements (button, text_input, search_bar, table, stats)
- `file` (dict): `{ "name", "type", "content" }` (base64) for download

**JSON response** (single object, using shared schema):

```python
from shared.schema import AgentResponse

return JSONResponse(AgentResponse(
    content="Here are the results",
    elements=[{"type": "table", "id": "data", "columns": [...], "rows": [...]}],
).model_dump(exclude_none=True))
```

**SSE streaming**: send multiple `data:` lines; each line is a JSON object with `content`, `elements`, and/or `file`. Frontier converts these to NDJSON for the frontend.

## Demos

Send a message containing:

- `show stats` — stats panel
- `show table` — table + search_bar + submit button
- `show form` — text_input (multiline) + submit button
- `download file` — file attachment
- `stream demo` — SSE: text chunks, then elements, then file
- anything else — echo as plain text

## Run

```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8100
```

In Frontier, add an HTTP agent with endpoint `http://localhost:8100/` and use it in a project. Send the demo messages above to try each element.
