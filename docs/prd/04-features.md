# Features & Capabilities

## Overview

Frontier's features are organized into eight core categories, each designed to serve specific user needs while maintaining the platform's principles of project isolation, flexibility, and enterprise-grade controls.

---

## Feature Categories

### 1. Authentication & Identity

#### JWT-Based Authentication
**What**: Token-based authentication with configurable expiry
**Who**: All users
**Why**: Stateless, scalable authentication without session management
**Priority**: P0 (Core)

**Capabilities**:
- Login with username/password
- JWT token generation with configurable expiry
- Automatic token refresh
- Secure password hashing

**Technical**: `src/api/routers/auth.py`, `src/core/auth/`

#### LDAP/Active Directory Integration
**What**: Optional SSO integration with enterprise directory services
**Who**: Platform Admins, End Users (transparent)
**Why**: Seamless integration with existing identity systems
**Priority**: P1 (Enterprise)

**Capabilities**:
- LDAP server connection configuration
- User authentication via LDAP
- Fallback to local authentication
- Configurable LDAP search base and filters

**Technical**: `src/core/auth/ldap.py`, configured via `config.yaml`

#### User Management
**What**: User profile and credential management
**Who**: Platform Admins
**Why**: Centralized user administration
**Priority**: P0 (Core)

**Capabilities**:
- Create/update/delete users
- Password management
- User profile information (LAN ID, display name)
- User status tracking

**Technical**: `src/core/db/models.py` (User model)

---

### 2. Project Management

#### Multi-Project Architecture
**What**: Isolated workspaces with dedicated database tables
**Who**: Project Admins, End Users
**Why**: Complete data isolation between teams and use cases
**Priority**: P0 (Core)

**Capabilities**:
- Create projects with unique names
- Automatic database table creation per project
- Project-specific configurations
- Project metadata (description, created date)

**Technical**: `src/core/db/db_chat.py` (dynamic table creation)

#### Project CRUD Operations
**What**: Full lifecycle management for projects
**Who**: Project Admins (owners)
**Why**: Self-service project administration
**Priority**: P0 (Core)

**Capabilities**:
- Create new projects
- Update project details
- Delete projects (cascades to conversations/messages)
- List projects with member counts

**Technical**: `src/api/routers/projects.py`

#### Project Discovery
**What**: Browse and search available projects
**Who**: All authenticated users
**Why**: Find relevant projects to join
**Priority**: P1 (Collaboration)

**Capabilities**:
- List all projects (with permission filtering)
- Search projects by name/description
- View project member counts
- See project agent configurations

**Technical**: `GET /api/projects` endpoint

---

### 3. Role-Based Access Control (RBAC)

#### Project Membership
**What**: User-to-project associations with roles
**Who**: Project Admins
**Why**: Control who can access each project
**Priority**: P0 (Core)

**Capabilities**:
- Three roles: `owner`, `admin`, `member`
- Add/remove project members
- Role-based permission checks
- Membership listing and search

**Technical**: `src/core/db/models.py` (ProjectMember model)

**Role Permissions**:
| Action | Owner | Admin | Member |
|--------|-------|-------|--------|
| Chat in project | ✅ | ✅ | ✅ |
| Create conversations | ✅ | ✅ | ✅ |
| Delete own conversations | ✅ | ✅ | ✅ |
| Add members | ✅ | ✅ | ❌ |
| Remove members | ✅ | ✅ | ❌ |
| Configure agents | ✅ | ✅ | ❌ |
| Delete project | ✅ | ❌ | ❌ |

#### AD Group-Based Access
**What**: Grant project access via Active Directory groups
**Who**: Platform Admins, Project Admins
**Why**: Leverage existing organizational structure for access control
**Priority**: P1 (Enterprise)

**Capabilities**:
- Associate AD groups with projects
- Automatic access for group members
- Multiple groups per project
- Group-based role assignment

**Technical**: `src/core/db/models.py` (ProjectADGroup model)

#### Permission Enforcement
**What**: API-level authorization checks
**Who**: System (transparent to users)
**Why**: Ensure users only access authorized resources
**Priority**: P0 (Core)

**Capabilities**:
- JWT token validation on all protected endpoints
- Project membership verification
- Role-based action authorization
- Graceful permission denial (403 responses)

**Technical**: Dependency injection in FastAPI routers

---

### 4. AI Agent Management

#### Agent Configuration
**What**: Define and configure AI agent connections
**Who**: Project Admins
**Why**: Flexible integration with multiple AI backends
**Priority**: P0 (Core)

**Capabilities**:
- Create agent configurations
- Specify agent type (langgraph, openai, http)
- Configure endpoint URLs and parameters
- Set authentication credentials
- Mark default agent per project

**Technical**: `src/api/routers/agents.py`, `src/core/db/models.py` (Agent model)

#### Agent Types

##### LangGraph Connector
**What**: Integration with LangGraph-based agents
**Who**: Developers building LangGraph agents
**Why**: Support for stateful, graph-based AI workflows
**Priority**: P0 (Core)

**Capabilities**:
- Thread-based conversation management
- Streaming response support
- Custom configuration via `extras` JSON
- Bearer/Basic/API key authentication

**Technical**: `src/core/agent/connectors/langgraph_connector.py`

##### OpenAI Connector
**What**: Integration with OpenAI-compatible APIs
**Who**: Teams using OpenAI, Azure OpenAI, or compatible services
**Why**: Broad compatibility with OpenAI ecosystem
**Priority**: P0 (Core)

**Capabilities**:
- Model selection (gpt-4, gpt-3.5-turbo, etc.)
- Streaming chat completions
- System prompt configuration
- Temperature and parameter tuning

**Technical**: `src/core/agent/connectors/openai_connector.py`

##### HTTP Connector
**What**: Generic HTTP streaming connector
**Who**: Developers with custom AI backends
**Why**: Maximum flexibility for any HTTP-based agent
**Priority**: P1 (Extensibility)

**Capabilities**:
- Custom endpoint configuration
- Flexible request/response formats
- Streaming support via SSE or chunked transfer
- Custom headers and authentication

**Technical**: `src/core/agent/connectors/http_connector.py`

#### Agent Authentication
**What**: Secure credential management for agent APIs
**Who**: Project Admins
**Why**: Protect API keys and credentials
**Priority**: P0 (Core)

**Capabilities**:
- Three auth types: `bearer`, `basic`, `api_key`
- Encrypted credential storage
- Per-agent authentication configuration
- Automatic header generation

**Technical**: `BaseAgentConnector.get_auth_headers()`

---

### 5. Chat Interface

#### Real-Time Streaming
**What**: SSE-based message streaming from agents
**Who**: End Users
**Why**: Responsive, ChatGPT-like experience
**Priority**: P0 (Core)

**Capabilities**:
- Server-Sent Events (SSE) for streaming
- Token-by-token response rendering
- Graceful error handling
- Connection management

**Technical**: `src/api/routers/chat.py` (streaming endpoint)

#### Conversation Management
**What**: Organize chats into named conversations
**Who**: End Users
**Why**: Maintain context and find past discussions
**Priority**: P0 (Core)

**Capabilities**:
- Create new conversations
- List conversations by project
- Rename conversations
- Delete conversations
- Automatic conversation creation on first message

**Technical**: Project-specific `{project}_conversation` tables

#### Message History
**What**: Persistent storage of all chat messages
**Who**: End Users
**Why**: Reference past conversations and maintain context
**Priority**: P0 (Core)

**Capabilities**:
- Store user and assistant messages
- Retrieve conversation history
- Message metadata (timestamp, token count)
- Chronological ordering

**Technical**: Project-specific `{project}_messages` tables

#### File Uploads
**What**: Attach files to chat messages
**Who**: End Users
**Why**: Provide context documents to AI agents
**Priority**: P1 (Enhanced UX)

**Capabilities**:
- Upload files via chat interface
- Store files in project-specific directories
- Associate files with messages
- Serve uploaded files securely

**Technical**: `src/data/uploads/`, file handling in chat router

---

### 6. User Interface

#### Modern Chat Interface
**What**: Svelte-based responsive chat UI
**Who**: End Users
**Why**: Familiar, intuitive chat experience
**Priority**: P0 (Core)

**Capabilities**:
- Message input with multi-line support
- Real-time streaming message display
- Conversation list sidebar
- Project and agent selection
- File upload interface

**Technical**: `src/frontend/src/lib/ChatArea.svelte`

#### Neo-Brutalist Design System
**What**: Modern, distinctive UI design language
**Who**: All users
**Why**: Professional, accessible, and memorable interface
**Priority**: P1 (Branding)

**Capabilities**:
- Bold, high-contrast design
- Accessible color schemes
- Consistent component styling
- Responsive layouts

**Technical**: `src/frontend/src/lib/` components, `SIDEBAR_REDESIGN.md`

#### Project Settings UI
**What**: Self-service project configuration interface
**Who**: Project Admins
**Why**: Manage projects without backend access
**Priority**: P1 (Self-Service)

**Capabilities**:
- Edit project details
- Manage team members
- Configure agents
- View project statistics

**Technical**: `src/frontend/src/lib/ProjectSettings.svelte`

#### Model/Agent Selector
**What**: Dropdown to switch between configured agents
**Who**: End Users
**Why**: Experiment with different AI models
**Priority**: P1 (Flexibility)

**Capabilities**:
- List available agents for project
- Switch agent mid-conversation
- Display agent metadata
- Highlight default agent

**Technical**: `src/frontend/src/lib/ModelSelector.svelte`

---

### 7. Metrics & Monitoring

#### Usage Metrics
**What**: Track conversations, messages, and token usage
**Who**: Platform Admins, Project Admins
**Why**: Monitor adoption and costs
**Priority**: P1 (Observability)

**Capabilities**:
- Conversation count per project
- Message count per user
- Token usage tracking
- Active user metrics

**Technical**: `src/api/routers/metrics.py`

#### Prometheus Integration
**What**: Expose metrics in Prometheus format
**Who**: Platform Admins
**Why**: Integrate with existing monitoring infrastructure
**Priority**: P1 (Observability)

**Capabilities**:
- `/metrics` endpoint
- Standard Prometheus metric types
- Custom application metrics
- System health indicators

**Technical**: Prometheus client library integration

#### System Health
**What**: Monitor application and database health
**Who**: Platform Admins
**Why**: Ensure platform reliability
**Priority**: P0 (Core)

**Capabilities**:
- Database connection health checks
- API response time tracking
- Error rate monitoring
- Resource utilization metrics

**Technical**: Built-in FastAPI metrics, custom health checks

#### Structured Logging
**What**: Centralized, configurable application logging
**Who**: Platform Admins, Developers
**Why**: Debug issues, monitor operations, audit activities
**Priority**: P0 (Core)

**Capabilities**:
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Customizable log format
- Module-specific loggers with consistent naming
- Exception stack traces for errors
- Logs to stdout for easy capture

**Configuration**:
```yaml
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

**Log Categories**:
| Level | Use Case |
|-------|----------|
| DEBUG | Agent requests, DB queries, detailed diagnostics |
| INFO | Startup, connections, normal operations |
| WARNING | Retries, fallbacks, recoverable issues |
| ERROR | Auth failures, API errors, exceptions |

**Technical**: `src/core/logging.py`, integrated across all modules

---

### 8. Configuration & Deployment

#### YAML Configuration
**What**: File-based application configuration
**Who**: Platform Admins
**Why**: Flexible, version-controllable settings
**Priority**: P0 (Core)

**Capabilities**:
- Database connection settings
- JWT configuration
- LDAP settings
- CORS origins
- Application host/port
- Logging level and format

**Technical**: `config.yaml`, `src/core/config.py`

#### Database Flexibility
**What**: Support for PostgreSQL and YugabyteDB
**Who**: Platform Admins
**Why**: Scale from development to production
**Priority**: P0 (Core)

**Capabilities**:
- PostgreSQL for development and production
- YugabyteDB for distributed deployments
- Schema isolation via PostgreSQL search_path
- Automatic table creation per project

**Technical**: SQLAlchemy with PostgreSQL-compatible models

#### Single-Command Deployment
**What**: Simple startup with embedded frontend
**Who**: Platform Admins
**Why**: Reduce deployment complexity
**Priority**: P0 (Core)

**Capabilities**:
- `python project.py` starts server
- Embedded frontend (no separate web server)
- Sensible defaults (no config required)
- Custom host/port via CLI args

**Technical**: `project.py` (repo root), `src/sdk`

---

## Feature Priority Matrix

| Category | P0 (Core) | P1 (Important) | P2 (Nice-to-Have) |
|----------|-----------|----------------|-------------------|
| **Authentication** | JWT auth, User mgmt | LDAP integration | OAuth, SAML |
| **Projects** | CRUD, Multi-project | Discovery | Templates, Cloning |
| **RBAC** | Membership, Roles | AD groups | Conversation-level |
| **Agents** | LangGraph, OpenAI | HTTP connector | More connectors |
| **Chat** | Streaming, History | File uploads | Rich media, Search |
| **UI** | Chat interface | Neo-brutalist design | Customization |
| **Metrics** | System health, Logging | Prometheus, Usage | Analytics dashboard |
| **Deployment** | Single command | Config flexibility | Docker, K8s |

---

## Feature Gaps & Future Enhancements

See [Roadmap](08-roadmap.md) for planned features including:
- Soft deletes for conversations/messages
- Conversation search and filtering
- Enhanced file handling (preview, annotations)
- Conversation-level permissions
- Advanced analytics dashboard
- Additional agent connectors (Anthropic, Azure, Gemini)

---

**Next**: [User Journeys](05-user-journeys.md) - Step-by-step workflows
