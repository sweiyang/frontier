# Architecture Documentation Package

Generated on: 2026-03-09

## Files Created

### 1. ARCHITECTURE.md (26 KB)
Comprehensive architecture documentation covering all 11 required sections:
- Project structure with detailed directory layout
- System diagrams (C4 Context, Container, Component)
- Core components (FastAPI, routers, agent framework, database, auth, config, frontend)
- Data stores (YugabyteDB production, SQLite dev, file storage)
- External integrations (LDAP, LangGraph, OpenAI, HTTP agents)
- Deployment architecture (on-premise, HA setup)
- Security (JWT, RBAC, CORS, encryption)
- Development workflow and testing
- Future considerations (caching, message queue, CDN, features)
- Project identification and glossary

### 2. Mermaid Diagrams (5 files)

#### 01-context.mmd (905 B)
C4 Context diagram showing Conduit in its broader ecosystem with users, administrators, and external systems (LDAP, AI agents).

#### 02-container.mmd (865 B)
C4 Container diagram showing the main application containers: Svelte SPA, FastAPI server, YugabyteDB, and file storage.

#### 03-component.mmd (1.1 KB)
C4 Component diagram detailing the internal structure of the API server: routers, services, connectors, auth, database layer, and config.

#### 04-dataflow.mmd (2.3 KB)
Data flow diagram showing how requests flow from users through the frontend, API layer, service layer, core layer, to external agents and back via SSE streaming.

#### 05-deployment.mmd (2.8 KB)
C4 Deployment diagram showing the on-premise infrastructure: load balancer, 3-node application cluster, 3-node YugabyteDB cluster, shared NFS storage, LDAP server, and external AI agents.

### 3. openapi.json (21 KB)
OpenAPI 3.0 specification documenting the REST API with:
- 6 main endpoint groups (auth, projects, chat, conversations, agents, rbac)
- 15+ API operations with request/response schemas
- JWT bearer authentication
- SSE streaming for chat endpoint
- Complete data models for all entities

## How to Use

### View Diagrams
The .mmd files can be rendered using:
- Mermaid Live Editor: https://mermaid.live
- VS Code with Mermaid extension
- GitHub (renders Mermaid automatically in markdown)
- Documentation sites (GitBook, Docusaurus, etc.)

### API Documentation
The openapi.json can be used with:
- Swagger UI: https://editor.swagger.io
- Postman: Import as OpenAPI 3.0 collection
- API documentation generators (Redoc, Stoplight)
- Code generation tools (OpenAPI Generator)

### Architecture Documentation
ARCHITECTURE.md is ready for:
- Developer onboarding
- Technical reviews
- Stakeholder presentations
- Compliance documentation
- System maintenance reference

## Key Architectural Highlights

### Multi-Tenancy
- Project-based isolation with dynamic table creation
- Each project gets `{project_name}_conversation` and `{project_name}_messages` tables
- RBAC with owner/admin/member roles

### Agent Framework
- Pluggable connector architecture (LangGraph, OpenAI, HTTP)
- Streaming responses via SSE
- Flexible authentication (Bearer, Basic, API key)

### High Availability
- YugabyteDB 3-node cluster with replication
- Stateless application servers (horizontal scaling)
- Shared NFS storage for uploads

### Security
- JWT authentication with LDAP integration
- Project-level RBAC with AD group support
- CORS protection and input validation

## Next Steps

1. Review ARCHITECTURE.md for accuracy and completeness
2. Render Mermaid diagrams to verify visual representation
3. Import openapi.json into API testing tools
4. Share documentation with team for feedback
5. Consider adding to version control and CI/CD pipeline
