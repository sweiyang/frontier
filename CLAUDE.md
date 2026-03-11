# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Conduit is a multi-project AI chat platform with a FastAPI backend and Svelte frontend. It provides project-based isolation, RBAC with LDAP integration, and supports multiple AI agent connectors (LangGraph, OpenAI, HTTP). Each project gets its own dynamically-created database tables for conversations and messages.

## Architecture

### Backend (Python/FastAPI)
- **Entry point**: [project.py](project.py) - CLI wrapper that calls `conduit.sdk.serve()`
- **FastAPI app**: [src/api/main.py](src/api/main.py) - Application setup, router registration, and SPA mounting
- **Core modules** ([src/core/](src/core/)):
  - `agent/`: Agent connector framework
    - [base_connector.py](src/core/agent/base_connector.py): Abstract base class defining `stream()` and `close()` methods
    - `connectors/`: Implementations for `langgraph_connector.py`, `openai_connector.py`, `http_connector.py`
  - `db/`: SQLAlchemy models and database operations
  - `auth/`: JWT authentication and LDAP integration
  - [config.py](src/core/config.py): YAML-based configuration loader with defaults
- **API routers** ([src/api/routers/](src/api/routers/)): REST endpoints for auth, chat, projects, agents, conversations, RBAC, metrics, usage
- **SDK** ([src/sdk/](src/sdk/)): Simple wrapper for starting the server

### Frontend (Svelte + Vite)
- **Location**: [src/frontend/](src/frontend/)
- **Build output**: `src/frontend/dist/` (served by FastAPI as static SPA)
- **Key components** ([src/frontend/src/lib/](src/frontend/src/lib/)):
  - [ChatArea.svelte](src/frontend/src/lib/ChatArea.svelte): Main chat interface with streaming support
  - [Sidebar.svelte](src/frontend/src/lib/Sidebar.svelte): Navigation and conversation list
  - [ProjectSettings.svelte](src/frontend/src/lib/ProjectSettings.svelte): Project configuration UI
  - [ModelSelector.svelte](src/frontend/src/lib/ModelSelector.svelte): Agent/model selection dropdown
  - [DynamicPanel.svelte](src/frontend/src/lib/DynamicPanel.svelte): Dynamic UI rendering

### Database Architecture
- **Supports**: PostgreSQL and YugabyteDB only (SQLite not supported)
- **Environment-based config**: Database settings under `database.<env>` in config.yaml (host, port, dbname, user, credential, schema)
- **Schema support**: Optional schema isolation via `database.<env>.schema` (uses PostgreSQL `search_path`)
- **Dynamic tables**: Each project gets isolated `{project_name}_conversation` and `{project_name}_messages` tables created automatically on first use
- **Global tables**: `users`, `projects`, `project_members`, `agents`, `project_ad_groups`
- **Project name sanitization**: Special characters replaced with underscores, names lowercased, max 63 chars
- See [docs/ard/DATABASE_SCHEMA.md](docs/ard/DATABASE_SCHEMA.md) for complete schema documentation

## Development Commands

### Running the Application
```bash
# Start backend server (from repository root)
python project.py
# With custom host/port:
python project.py --host 0.0.0.0 --port 8000

# Start frontend dev server (for development)
cd src/frontend && npm run dev

# Build frontend for production
cd src/frontend && npm run build
```

### Frontend Development
```bash
# Install dependencies
cd src/frontend && npm install

# Development server (hot reload)
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

### Configuration
- Copy [config.yaml.example](config.yaml.example) to `config.yaml` and customize
- Set `CONFIG_FILE` environment variable to use a different config path
- App runs with built-in defaults if no config file exists
- Key config sections: `app`, `database`, `jwt`, `ldap`, `cors`

## Key Patterns

### Agent Connectors
All agent connectors inherit from `BaseAgentConnector` ([src/core/agent/base_connector.py](src/core/agent/base_connector.py)) and implement:
- `stream(messages_history, message, conversation_id, files, metadata, **kwargs)`: Async generator yielding text chunks
- `close()`: Cleanup resources
- `get_auth_headers()`: Build auth headers from agent config (supports bearer, basic, api_key)

Connector types registered in [src/core/agent/connectors/__init__.py](src/core/agent/connectors/__init__.py):
- `langgraph`: LangGraph connector with thread management
- `openai`: OpenAI-compatible API connector
- `http`: Generic HTTP streaming connector

### Project Isolation
- Each project has its own conversation/message tables created dynamically via `db_chat.get_db(project_name)`
- Project names are sanitized to valid SQL identifiers (e.g., "my-project" → "my_project_conversation")
- Tables created automatically using SQLAlchemy's `create_all(checkfirst=True)`
- Foreign keys reference project-specific tables

### Authentication & Authorization
- JWT-based auth with configurable expiry (`jwt.secret_key`, `jwt.expire_minutes` in config)
- Optional LDAP integration for user authentication
- RBAC via `project_members` table with roles: `owner`, `admin`, `member`
- AD group-based access via `project_ad_groups` table

### Frontend-Backend Communication
- REST API for CRUD operations (all routers in [src/api/routers/](src/api/routers/))
- SSE (Server-Sent Events) for streaming chat responses
- Static file uploads stored in `data/uploads/` and served at `/uploads`
- SPA served from `frontend/dist/` with fallback to `index.html`

## File Locations

- **Python source**: [src/](src/)
- **Frontend source**: [src/frontend/src/](src/frontend/src/)
- **Frontend build**: `src/frontend/dist/`
- **Database**: PostgreSQL/YugabyteDB (configured in config.yaml)
- **Uploads**: `data/uploads/`
- **Config**: [config.yaml](config.yaml) (root directory)
- **Documentation**: [docs/README.md](docs/README.md) — [ard](docs/ard/) (architecture), [prd](docs/prd/) (product), [user-guide](docs/user-guide/) (connectors, elements), [feature](docs/feature/), [user-journey](docs/user-journey/)

## Important Notes

- Frontend must be built before production deployment (FastAPI serves the dist folder)
- Database tables are created automatically on first use per project
- Agent configurations stored in `agents` table with JSON `extras` field for connector-specific config
- Agent auth stored in `auth` field as JSON: `{"auth_type": "bearer|basic|api_key", "credentials": ...}`
- CORS origins must be configured in `config.yaml` for frontend access
- The `is_default` flag on agents ensures only one default agent per project
