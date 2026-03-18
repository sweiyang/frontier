# Frontier Architecture Documentation

## 1. Project Structure

```
frontier/
├── src/
│   ├── api/                    # FastAPI application layer
│   │   ├── main.py            # Application entry point, router registration
│   │   ├── routers/           # REST API endpoints
│   │   │   ├── auth.py        # Authentication endpoints
│   │   │   ├── chat.py        # Chat streaming endpoints (SSE)
│   │   │   ├── conversations.py  # Conversation CRUD
│   │   │   ├── projects.py    # Project management
│   │   │   ├── agents.py      # Agent configuration
│   │   │   ├── rbac_groups.py # RBAC group management
│   │   │   ├── rbac_members.py # Project member management
│   │   │   ├── langgraph.py   # LangGraph-specific endpoints
│   │   │   ├── openai_models.py # OpenAI model listing
│   │   │   ├── metrics.py     # System metrics
│   │   │   ├── usage.py       # Usage tracking
│   │   │   ├── ldap.py        # LDAP integration
│   │   │   └── config.py      # Configuration endpoints
│   │   ├── services/          # Business logic layer
│   │   │   ├── chat_service.py      # Chat orchestration
│   │   │   ├── langgraph_service.py # LangGraph integration
│   │   │   ├── openai_service.py    # OpenAI integration
│   │   │   └── rbac_service.py      # RBAC logic
│   │   ├── middleware/        # HTTP middleware
│   │   │   └── cors.py        # CORS configuration
│   │   └── static/            # Static file serving
│   │       └── spa.py         # SPA mounting logic
│   ├── core/                  # Core business logic
│   │   ├── config.py          # YAML configuration loader
│   │   ├── db/                # Database layer
│   │   │   ├── db.py          # SQLAlchemy setup, global tables
│   │   │   ├── db_chat.py     # Dynamic per-project tables
│   │   │   └── db_project.py  # Project-specific operations
│   │   ├── agent/             # Agent connector framework
│   │   │   ├── base_connector.py    # Abstract base class
│   │   │   ├── agent_manager.py     # Agent lifecycle management
│   │   │   └── connectors/          # Connector implementations
│   │   │       ├── langgraph_connector.py  # LangGraph integration
│   │   │       ├── openai_connector.py     # OpenAI-compatible APIs
│   │   │       ├── http_connector.py       # Generic HTTP streaming
│   │   │       └── schema.py               # Connector data models
│   │   ├── auth/              # Authentication & authorization
│   │   │   ├── auth.py        # Password hashing, LDAP integration
│   │   │   └── jwt.py         # JWT token generation/validation
│   │   ├── http_client/       # HTTP client utilities
│   │   │   └── http_client.py # Async HTTP client wrapper
│   │   ├── metrics/           # Metrics collection
│   │   │   └── metrics.py     # Prometheus-style metrics
│   │   ├── logging.py         # Centralized logging configuration
│   │   └── utils/             # Utility functions
│   │       └── token_counter.py # Token counting for usage tracking
│   ├── sdk/                   # Python SDK
│   │   └── __init__.py        # serve() function wrapper
│   └── frontend/              # Svelte SPA
│       ├── src/
│       │   ├── App.svelte     # Root component
│       │   ├── lib/           # Reusable components
│       │   │   ├── ChatArea.svelte       # Main chat interface
│       │   │   ├── Sidebar.svelte        # Navigation & conversations
│       │   │   ├── ModelSelector.svelte  # Agent selection
│       │   │   ├── ProjectSettings.svelte # Project configuration
│       │   │   ├── Login.svelte          # Authentication UI
│       │   │   ├── CreateProject.svelte  # Project creation
│       │   │   ├── DynamicPanel.svelte   # Dynamic UI rendering
│       │   │   └── dynamic/              # Dynamic UI components
│       │   │       ├── DynamicButton.svelte
│       │   │       ├── DynamicSearchBar.svelte
│       │   │       ├── DynamicStats.svelte
│       │   │       ├── DynamicTable.svelte
│       │   │       └── DynamicTextInput.svelte
│       │   ├── lib/markdown.js  # Markdown rendering
│       │   └── lib/utils.js     # Frontend utilities
│       ├── dist/              # Production build output
│       ├── package.json       # Node.js dependencies
│       └── vite.config.js     # Vite build configuration
├── data/                      # Runtime data directory
│   └── uploads/              # User-uploaded files
├── config.yaml               # Application configuration
├── config.yaml.example       # Configuration template
├── project.py                # CLI entry point
├── pyproject.toml            # Python project metadata
└── README.md                 # Project documentation
```

## 2. System Diagram

### C4 Context Diagram (Level 1)

```mermaid
C4Context
    title System Context - Frontier AI Chat Platform

    Person(user, "End User", "Interacts with AI agents through web interface")
    Person(admin, "Administrator", "Manages projects, users, and agents")

    System(frontier, "Frontier Platform", "Multi-project AI chat platform with RBAC")

    System_Ext(ldap, "LDAP Server", "Corporate directory for authentication")
    System_Ext(langgraph, "LangGraph Agent", "LangGraph-based AI agent")
    System_Ext(openai, "OpenAI API", "OpenAI-compatible AI service")
    System_Ext(http_agent, "HTTP Agent", "Custom HTTP streaming agent")

    Rel(user, frontier, "Uses", "HTTPS")
    Rel(admin, frontier, "Manages", "HTTPS")
    Rel(frontier, ldap, "Authenticates", "LDAP")
    Rel(frontier, langgraph, "Streams messages", "HTTP/SSE")
    Rel(frontier, openai, "Streams messages", "HTTP/SSE")
    Rel(frontier, http_agent, "Streams messages", "HTTP/SSE")
```

### C4 Container Diagram (Level 2)

```mermaid
C4Container
    title Container Diagram - Frontier Platform

    Person(user, "User", "End user or administrator")

    Container(spa, "Web Application", "Svelte, Vite", "Single-page application for chat interface")
    Container(api, "API Server", "FastAPI, Python 3.9+", "REST API and SSE streaming")
    ContainerDb(db, "Database", "YugabyteDB", "Stores users, projects, conversations, messages")
    Container(uploads, "File Storage", "Filesystem", "Stores uploaded files")

    System_Ext(ldap, "LDAP Server", "Authentication")
    System_Ext(agents, "AI Agents", "LangGraph, OpenAI, HTTP")

    Rel(user, spa, "Uses", "HTTPS")
    Rel(spa, api, "API calls", "JSON/REST, SSE")
    Rel(api, db, "Reads/Writes", "SQL")
    Rel(api, uploads, "Stores/Retrieves", "Filesystem")
    Rel(api, ldap, "Authenticates", "LDAP")
    Rel(api, agents, "Streams", "HTTP/SSE")
```

### C4 Component Diagram (Level 3)

```mermaid
C4Component
    title Component Diagram - API Server

    Container(spa, "Web Application", "Svelte")

    Component(routers, "API Routers", "FastAPI", "HTTP endpoints for REST operations")
    Component(services, "Business Services", "Python", "Chat, RBAC, agent orchestration")
    Component(connectors, "Agent Connectors", "Python", "Pluggable agent integrations")
    Component(auth, "Auth Module", "Python", "JWT and LDAP authentication")
    Component(db_layer, "Database Layer", "SQLAlchemy", "ORM and dynamic table management")
    Component(config, "Config Module", "Python", "YAML configuration loader")

    ContainerDb(db, "Database", "YugabyteDB")
    System_Ext(agents, "AI Agents")
    System_Ext(ldap, "LDAP")

    Rel(spa, routers, "HTTP requests", "JSON/SSE")
    Rel(routers, services, "Calls")
    Rel(routers, auth, "Validates tokens")
    Rel(services, connectors, "Streams messages")
    Rel(services, db_layer, "CRUD operations")
    Rel(connectors, agents, "HTTP/SSE")
    Rel(auth, ldap, "LDAP bind")
    Rel(db_layer, db, "SQL")
    Rel(routers, config, "Reads settings")
```

## 3. Core Components

### 3.1 FastAPI Application ([src/api/main.py](src/api/main.py))

**Purpose**: Application entry point that registers routers, configures middleware, and mounts the SPA.

**Key Responsibilities**:
- Initialize database on startup via lifespan context manager
- Register 12 API routers for different functional areas
- Configure CORS middleware with allowed origins from config
- Mount static file serving for uploads at `/uploads`
- Mount Svelte SPA with fallback routing to `index.html`

**Dependencies**: All routers, CORS middleware, SPA mounting logic, database initialization

### 3.2 API Routers ([src/api/routers/](src/api/routers/))

**Purpose**: REST API endpoints organized by functional domain.

**Routers**:
- `auth.py`: User login, registration, token refresh
- `chat.py`: SSE streaming endpoint for real-time chat
- `conversations.py`: CRUD operations for conversations
- `projects.py`: Project creation, listing, updates, deletion
- `agents.py`: Agent configuration and management
- `rbac_groups.py`: AD group-based access control
- `rbac_members.py`: Project member management
- `langgraph.py`: LangGraph-specific operations (threads, runs)
- `openai_models.py`: List available OpenAI models
- `metrics.py`: System metrics and health checks
- `usage.py`: Token usage tracking and reporting
- `ldap.py`: LDAP user search and validation
- `config.py`: Application configuration retrieval

**Authentication**: Most endpoints require JWT bearer token via `deps/auth.py` dependency

### 3.3 Agent Connector Framework ([src/core/agent/](src/core/agent/))

**Purpose**: Pluggable architecture for integrating different AI agent backends.

**Base Class** ([base_connector.py](src/core/agent/base_connector.py)):
```python
class BaseAgentConnector(ABC):
    @abstractmethod
    async def stream(messages_history, message, conversation_id, files, metadata, **kwargs):
        """Async generator yielding text chunks"""

    @abstractmethod
    async def close():
        """Cleanup resources"""

    def get_auth_headers():
        """Build auth headers from agent config"""
```

**Connector Implementations**:
- **LangGraph** ([langgraph_connector.py](src/core/agent/connectors/langgraph_connector.py)): Manages threads, streams from LangGraph agents
- **OpenAI** ([openai_connector.py](src/core/agent/connectors/openai_connector.py)): OpenAI-compatible API streaming
- **HTTP** ([http_connector.py](src/core/agent/connectors/http_connector.py)): Generic HTTP streaming for custom agents

**Agent Manager** ([agent_manager.py](src/core/agent/agent_manager.py)): Factory for creating connector instances based on agent type

### 3.4 Database Layer ([src/core/db/](src/core/db/))

**Purpose**: SQLAlchemy-based data persistence with dynamic per-project table creation.

**Global Tables** ([db.py](src/core/db/db.py)):
- `users`: User accounts (username, hashed password, email)
- `projects`: Project definitions (name, description, owner)
- `project_members`: User-project associations with roles (owner, admin, member)
- `agents`: Agent configurations (name, type, URL, auth, extras)
- `project_ad_groups`: AD group-based project access

**Dynamic Tables** ([db_chat.py](src/core/db/db_chat.py)):
- `{project_name}_conversation`: Conversations per project
- `{project_name}_messages`: Messages per project

**Key Features**:
- Project name sanitization (lowercase, special chars → underscores, max 63 chars)
- Automatic table creation on first access via `create_all(checkfirst=True)`
- Support for PostgreSQL and YugabyteDB (SQLite not supported)
- Schema isolation via PostgreSQL `search_path`
- Foreign key relationships within project-specific tables

### 3.5 Authentication & Authorization ([src/core/auth/](src/core/auth/))

**JWT Module** ([jwt.py](src/core/auth/jwt.py)):
- Token generation with configurable expiry (default 60 minutes)
- Token validation and payload extraction
- Secret key from config (default: dev key, must change in production)

**Auth Module** ([auth.py](src/core/auth/auth.py)):
- Password hashing using bcrypt
- LDAP authentication integration
- User creation and validation

**RBAC**:
- Project-level roles: `owner`, `admin`, `member`
- AD group-based access via `project_ad_groups` table
- Role checks in router dependencies ([deps/project.py](src/api/deps/project.py))

### 3.6 Configuration Management ([src/core/config.py](src/core/config.py))

**Purpose**: YAML-based configuration with sensible defaults.

**Configuration Sections**:
- `app`: Application name, splash text, default project, logo, footnote
- `database`: Database URL (SQLite, PostgreSQL, YugabyteDB)
- `jwt`: Secret key, token expiry
- `ldap`: Server, base DN, SSL, users DN
- `cors`: Allowed origins for API access
- `contact`: Email and Jira integration for support
- `faq`: FAQ URL and button text
- `logging`: Log level and format configuration

**Loading Strategy**:
- Reads from `CONFIG_FILE` env var or `config.yaml` in CWD
- Falls back to built-in defaults if file missing
- Requires PyYAML for config file support

### 3.7 Logging System ([src/core/logging.py](src/core/logging.py))

**Purpose**: Centralized logging configuration with configurable levels and formats.

**Key Functions**:
```python
def setup_logging(level: str = None, format_str: str = None) -> None:
    """Initialize logging system with config values or defaults"""

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module"""
```

**Log Levels**:
- `DEBUG`: Detailed diagnostic information (agent requests, DB queries)
- `INFO`: Normal operational events (startup, connections, requests)
- `WARNING`: Unexpected but recoverable situations (retries, fallbacks)
- `ERROR`: Failures requiring attention (auth failures, API errors)

**Configuration** (in `config.yaml`):
```yaml
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

**Usage Pattern**:
```python
from core.logging import get_logger
logger = get_logger(__name__)

logger.info("Processing request")
logger.error("Operation failed", exc_info=True)
```

**Instrumented Modules**:
- Application lifecycle (startup, shutdown)
- Authentication (LDAP bind, JWT validation)
- Database operations (connection, table creation)
- Agent connectors (requests, streaming, errors)
- API endpoints (errors, warnings)

### 3.8 Frontend Application ([src/frontend/](src/frontend/))

**Technology Stack**:
- **Framework**: Svelte 4
- **Build Tool**: Vite 5
- **Styling**: Custom CSS
- **Markdown**: Custom renderer with syntax highlighting

**Key Components**:
- **ChatArea.svelte**: Main chat interface with SSE streaming, markdown rendering, file uploads
- **Sidebar.svelte**: Project navigation, conversation list, user menu
- **ModelSelector.svelte**: Agent/model selection dropdown
- **ProjectSettings.svelte**: Project configuration UI (members, agents, AD groups)
- **DynamicPanel.svelte**: Renders dynamic UI elements from agent responses

**State Management**:
- Local component state with Svelte stores
- JWT token stored in localStorage
- Current project/conversation in URL parameters

**API Communication**:
- REST API calls via `fetch()`
- SSE streaming for chat messages via `EventSource`
- File uploads via `FormData`

## 4. Data Stores

### 4.1 YugabyteDB (Production)

**Purpose**: Distributed SQL database for high availability and horizontal scalability.

**Connection**: PostgreSQL-compatible driver (`psycopg2-binary`)
**URL Format**: `postgresql://yugabyte:password@host:5433/yugabyte`

**Schema**:
- Global tables: `users`, `projects`, `project_members`, `agents`, `project_ad_groups`
- Dynamic per-project tables: `{project_name}_conversation`, `{project_name}_messages`

**Key Features**:
- Multi-region replication for disaster recovery
- ACID transactions for data consistency
- Horizontal scaling for growing workloads

### 4.2 PostgreSQL (Development/Production)

**Purpose**: Standard relational database for local development and production.

**Connection**: PostgreSQL driver (`psycopg2-binary`)
**URL Format**: `postgresql://user:password@localhost:5432/frontier`

**Configuration** (`config.yaml`):
```yaml
database:
  dev:
    host: localhost
    port: 5432
    dbname: frontier
    user: postgres
    credential: password
```

**Features**:
- Full ACID compliance
- Connection pooling
- Suitable for most deployments

### 4.3 File Storage

**Purpose**: Store user-uploaded files (images, documents).

**Location**: `data/uploads/`
**Access**: Served via FastAPI `StaticFiles` at `/uploads` endpoint
**Organization**: Flat directory structure with unique filenames

## 5. External Integrations

### 5.1 LDAP Server

**Purpose**: Corporate directory integration for user authentication.

**Configuration**:
- Server URL: `ldap://` or `ldaps://` (SSL)
- Base DN: `dc=example,dc=com`
- Users DN: Optional custom user path

**Authentication Flow**:
1. User submits username/password
2. Backend attempts LDAP bind with credentials
3. On success, create/update user in local database
4. Issue JWT token for subsequent requests

**Fallback**: Local password authentication if LDAP unavailable

### 5.2 LangGraph Agents

**Purpose**: LangGraph-based AI agents with stateful conversation threads.

**Integration**: [langgraph_connector.py](src/core/agent/connectors/langgraph_connector.py)

**Features**:
- Thread management for conversation context
- Streaming responses via SSE
- Metadata passing for custom agent behavior

**Authentication**: Bearer token, Basic auth, or API key

### 5.3 OpenAI-Compatible APIs

**Purpose**: OpenAI API and compatible services (Azure OpenAI, local models).

**Integration**: [openai_connector.py](src/core/agent/connectors/openai_connector.py)

**Features**:
- Chat completions with streaming
- Model selection
- Message history management

**Authentication**: API key in `Authorization` header

### 5.4 Custom HTTP Agents

**Purpose**: Generic HTTP streaming agents with custom protocols.

**Integration**: [http_connector.py](src/core/agent/connectors/http_connector.py)

**Features**:
- Flexible request/response format
- SSE or line-delimited JSON streaming
- Custom authentication schemes

## 6. Deployment

### 6.1 On-Premise Deployment

**Infrastructure**: Self-hosted on company servers

**Components**:
- **Application Server**: Python 3.9+ with FastAPI/Uvicorn
- **Database**: YugabyteDB cluster (3+ nodes for HA)
- **Reverse Proxy**: Nginx or similar for HTTPS termination
- **File Storage**: Network-attached storage or local disk

**Deployment Steps**:
1. Install Python 3.9+ and dependencies via `pip install -e .`
2. Build frontend: `cd src/frontend && npm install && npm run build`
3. Configure `config.yaml` with production settings
4. Set up YugabyteDB connection string
5. Configure LDAP integration
6. Start application: `python project.py --host 0.0.0.0 --port 8000`
7. Configure reverse proxy for HTTPS and load balancing

### 6.2 Process Management

**Recommended**: systemd service or supervisor for process management

**Example systemd unit**:
```ini
[Unit]
Description=Frontier AI Chat Platform
After=network.target

[Service]
Type=simple
User=frontier
WorkingDirectory=/opt/frontier
Environment="CONFIG_FILE=/etc/frontier/config.yaml"
ExecStart=/usr/bin/python3 /opt/frontier/project.py --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### 6.3 High Availability

**Database**: YugabyteDB multi-node cluster with replication factor 3
**Application**: Multiple Frontier instances behind load balancer
**Session Management**: Stateless JWT tokens enable horizontal scaling
**File Storage**: Shared network storage or object storage for uploads

### 6.4 Monitoring

**Metrics Endpoint**: `/api/metrics` provides Prometheus-compatible system health metrics

**Structured Logging**:
- Centralized logging via `src/core/logging.py`
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Consistent format: `timestamp - module - level - message`
- All modules instrumented with appropriate log levels
- Exception stack traces included for ERROR level
- Application logs to stdout (capture via systemd or supervisor)

**Database Monitoring**: YugabyteDB built-in monitoring and alerting

## 7. Security

### 7.1 Authentication

**JWT Tokens**:
- HS256 algorithm with configurable secret key
- 60-minute expiry (configurable)
- Payload includes user ID and username
- Stored in localStorage on frontend

**LDAP Integration**:
- Optional corporate directory authentication
- SSL/TLS support for secure LDAP connections
- Fallback to local password authentication

**Password Storage**:
- Bcrypt hashing with salt
- Minimum 8 characters (enforced in frontend)

### 7.2 Authorization

**Project-Level RBAC**:
- Roles: `owner`, `admin`, `member`
- Owners: Full project control including deletion
- Admins: Manage members and agents
- Members: Read/write conversations

**AD Group-Based Access**:
- Projects can be associated with AD groups
- Users in AD groups automatically get project access
- Managed via `project_ad_groups` table

### 7.3 API Security

**CORS**:
- Configurable allowed origins
- Default: `http://localhost:5173` for development
- Production: Restrict to application domain

**Input Validation**:
- Pydantic models for request validation
- SQL injection prevention via SQLAlchemy ORM
- File upload validation (size, type)

**Agent Authentication**:
- Support for Bearer token, Basic auth, API key
- Credentials stored in `agents.auth` JSON field
- Transmitted securely to agent backends

### 7.4 Data Protection

**Database**:
- Connection encryption via SSL/TLS (YugabyteDB)
- Project-level data isolation via separate tables
- No cross-project data leakage

**File Uploads**:
- Stored outside web root
- Served via controlled endpoint
- Access control via JWT authentication

**Secrets Management**:
- JWT secret key in config file (not in code)
- Agent credentials in database (encrypted at rest)
- LDAP credentials never stored

## 8. Development

### 8.1 Local Setup

**Prerequisites**:
- Python 3.9 or higher
- Node.js 18+ and npm
- Git

**Backend Setup**:
```bash
# Clone repository
git clone <repository-url>
cd frontier

# Install Python dependencies
pip install -e .

# Copy and configure config file
cp config.yaml.example config.yaml
# Edit config.yaml with your settings

# Run backend server
python project.py
# Server starts at http://localhost:8000
```

**Frontend Setup**:
```bash
# Navigate to frontend directory
cd src/frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Frontend starts at http://localhost:5173

# Build for production
npm run build
# Output in src/frontend/dist/
```

### 8.2 Development Workflow

**Backend Development**:
- FastAPI auto-reload enabled by default
- API documentation at `http://localhost:8000/docs`
- Add new routers in `src/api/routers/`
- Register routers in `src/api/main.py`

**Frontend Development**:
- Vite hot module replacement for instant updates
- Add components in `src/frontend/src/lib/`
- Update `App.svelte` for routing changes

**Database Changes**:
- Modify models in `src/core/db/db.py` or `db_chat.py`
- SQLAlchemy auto-creates tables on startup
- For migrations, consider Alembic (not currently integrated)

### 8.3 Testing

**Backend Testing**:
- Unit tests: Test individual functions and classes
- Integration tests: Test API endpoints with test database
- Agent connector tests: Mock external agent APIs

**Frontend Testing**:
- Component tests: Test Svelte components in isolation
- E2E tests: Test full user workflows with Playwright or Cypress

**Manual Testing**:
- Use `/docs` endpoint for API testing
- Test SSE streaming with browser DevTools
- Verify RBAC with different user roles

### 8.4 Code Organization

**Backend Patterns**:
- Routers: Thin layer, delegate to services
- Services: Business logic, orchestration
- Core modules: Reusable utilities and frameworks
- Dependencies: Shared dependencies via FastAPI Depends

**Frontend Patterns**:
- Components: Reusable UI elements
- Stores: Shared state management
- Utils: Helper functions for API calls, formatting

**Configuration**:
- All environment-specific settings in `config.yaml`
- No hardcoded URLs or credentials in code
- Use environment variables for sensitive data

## 9. Future Considerations

### 9.1 Scalability Enhancements

**Caching Layer**:
- Redis for session caching and rate limiting
- Cache frequently accessed project/agent configurations
- Reduce database load for read-heavy operations

**Message Queue**:
- RabbitMQ or Kafka for async task processing
- Offload long-running operations (file processing, analytics)
- Improve responsiveness for user-facing operations

**CDN Integration**:
- Serve static assets (frontend, uploads) via CDN
- Reduce latency for geographically distributed users
- Offload bandwidth from application servers

### 9.2 Feature Roadmap

**Multi-Modal Support**:
- Image generation and analysis
- Voice input/output
- Video processing

**Advanced RBAC**:
- Fine-grained permissions (read-only, comment-only)
- Custom roles beyond owner/admin/member
- Audit logging for compliance

**Agent Marketplace**:
- Discover and install community agents
- Agent versioning and updates
- Agent performance metrics

**Collaboration Features**:
- Shared conversations with real-time updates
- Comments and annotations on messages
- Conversation branching and merging

### 9.3 Operational Improvements

**Observability** (Partially Implemented):
- ✅ Structured logging with configurable levels and formats
- Correlation IDs for request tracing (future)
- Distributed tracing via OpenTelemetry (future)
- Application performance monitoring (APM) (future)

**Database Migrations**:
- Integrate Alembic for schema versioning
- Automated migration testing
- Rollback procedures

**CI/CD Pipeline**:
- Automated testing on pull requests
- Containerization with Docker
- Kubernetes deployment manifests
- Blue-green or canary deployments

### 9.4 Security Enhancements

**OAuth2/OIDC**:
- Support for enterprise SSO providers
- Social login (Google, GitHub)
- Multi-factor authentication (MFA)

**API Rate Limiting**:
- Per-user and per-project rate limits
- Prevent abuse and ensure fair usage
- Configurable limits via admin interface

**Encryption at Rest**:
- Database encryption for sensitive data
- Encrypted file storage for uploads
- Key rotation procedures

## 10. Project Identification

**Project Name**: Frontier
**Repository**: [Internal Repository URL]
**Primary Contact**: [Team/Email]
**Last Updated**: 2026-03-11
**Version**: 0.1.0
**Status**: Production (On-Premise Deployment)

## 11. Glossary

**Agent**: An AI service that processes user messages and generates responses. Can be LangGraph, OpenAI, or custom HTTP-based.

**Connector**: A Python class that implements the interface for communicating with a specific agent type.

**Conversation**: A thread of messages between a user and an agent within a project.

**Dynamic Tables**: Database tables created automatically for each project to store conversations and messages.

**LDAP**: Lightweight Directory Access Protocol, used for corporate authentication.

**Project**: An isolated workspace with its own conversations, agents, and members.

**RBAC**: Role-Based Access Control, the authorization system for project access.

**SSE**: Server-Sent Events, a protocol for streaming data from server to client.

**Thread**: In LangGraph, a stateful conversation context that persists across multiple messages.

**YugabyteDB**: A distributed SQL database compatible with PostgreSQL, used for production deployments.
