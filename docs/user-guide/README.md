# User guides

How-to guides for using and integrating with Frontier.

| Guide | Description |
|-------|-------------|
| [Supported elements](supported-elements-user-guide.md) | Dynamic UI elements (button, table, text input, search bar, stats) and file download — agent response contract and examples |
| [OpenAI connector](openai-connector-user-guide.md) | Connect OpenAI-compatible APIs (OpenAI, Ollama, vLLM, etc.) via the OpenAI connector |
| [LangGraph connector](langgraph-connector-user-guide.md) | Connect LangGraph agents (threads, assistants, interrupts, structured output) |
| [HTTP connector](http-connector-user-guide.md) | Build custom HTTP agents that receive Frontier's request payload and return structured responses |

**Example apps:** See [example_apps/](../../example_apps/) for runnable demos (LangGraph, HTTP, OpenAI/Ollama).

---

## Debugging & Logging

Frontier includes centralized logging for debugging agent connections and platform operations. Configure logging in `config.yaml`:

```yaml
logging:
  level: DEBUG   # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

| Log Level | Use Case |
|-----------|----------|
| `DEBUG` | Full diagnostic output — agent requests, streaming chunks, DB queries |
| `INFO` | Normal operations — startup, connections (default) |
| `WARNING` | Recoverable issues — retries, fallbacks |
| `ERROR` | Failures — auth errors, API errors, exceptions |

Each connector guide includes a **Troubleshooting** section with common issues and log examples.
