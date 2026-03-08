# Executive Summary

## What is Conduit?

Conduit is a **multi-project AI chat platform** that enables organizations to deploy isolated AI workspaces with enterprise-grade access controls. It provides a unified interface for teams to interact with multiple AI agents while maintaining strict project boundaries, role-based permissions, and comprehensive audit trails.

**Elevator Pitch**: Conduit is like Slack for AI conversations—multiple projects, team-based access, and flexible AI agent integrations—all in one platform with enterprise security.

## Key Capabilities at a Glance

| Capability | Description | User Benefit |
|------------|-------------|--------------|
| **Multi-Project Isolation** | Each project gets dedicated database tables and configurations | Teams work independently without data leakage |
| **Flexible Agent Connectors** | Support for LangGraph, OpenAI, and custom HTTP agents | Use any AI backend without vendor lock-in |
| **Enterprise Authentication** | JWT + optional LDAP/AD integration | Seamless SSO with existing identity systems |
| **Role-Based Access Control** | Project-level permissions (owner/admin/member) + AD groups | Granular control over who accesses what |
| **Streaming Chat Interface** | Real-time SSE-based message streaming | Responsive, ChatGPT-like user experience |
| **Usage Metrics & Monitoring** | Prometheus-compatible metrics endpoint | Track costs, performance, and adoption |

## Target Users

### Primary Personas

1. **End Users** (Chat Interface Users)
   - Need: AI assistance for daily tasks within project context
   - Value: Simple, fast chat interface with conversation history

2. **Project Admins** (Team Leads, Product Managers)
   - Need: Manage team access, configure AI agents, monitor usage
   - Value: Self-service project management without IT involvement

3. **Platform Admins** (IT/DevOps)
   - Need: Deploy, monitor, and maintain the platform
   - Value: Single deployment serving multiple teams with centralized metrics

4. **Developers** (Integration Engineers)
   - Need: Connect custom AI agents and extend functionality
   - Value: Clean connector API with multiple reference implementations

## Core Use Cases

### 1. Team-Based AI Workspaces
**Scenario**: A product team needs a dedicated AI assistant for their project with controlled access.

**Flow**: Admin creates project → configures agent → invites team → members chat with AI

**Value**: Isolated workspace with team-specific context and permissions

### 2. Multi-Agent Experimentation
**Scenario**: Data science team wants to compare responses from different AI models.

**Flow**: Configure multiple agents (GPT-4, Claude, custom) → switch between them in chat → compare outputs

**Value**: Flexible agent selection without switching platforms

### 3. Enterprise AI Deployment
**Scenario**: Organization needs centralized AI chat with SSO and audit trails.

**Flow**: Deploy Conduit → integrate LDAP → create projects for departments → monitor usage via metrics

**Value**: Enterprise-grade security and compliance with self-service for teams

## Value Propositions

### For Organizations
- **Centralized AI Management**: One platform for all team AI interactions
- **Cost Control**: Track token usage and costs per project
- **Security & Compliance**: RBAC, LDAP integration, audit trails
- **Vendor Flexibility**: Switch AI providers without changing user experience

### For Teams
- **Project Isolation**: Dedicated workspace with team-specific configurations
- **Self-Service**: Create projects and manage access without IT tickets
- **Conversation History**: Persistent chat history with search and organization
- **Familiar Interface**: ChatGPT-like experience with team collaboration features

### For Developers
- **Extensible Architecture**: Clean connector API for custom agents
- **Multiple Backends**: LangGraph, OpenAI, or any HTTP-based AI service
- **Modern Stack**: FastAPI + Svelte with comprehensive API documentation
- **Easy Deployment**: Single command startup with sensible defaults

## Technical Highlights

- **Backend**: Python FastAPI with SQLAlchemy ORM
- **Frontend**: Svelte + Vite with modern UI components
- **Database**: SQLite (default) or PostgreSQL/YugabyteDB for production
- **Authentication**: JWT with optional LDAP integration
- **Deployment**: Single binary with embedded frontend, Docker-ready
- **Monitoring**: Prometheus metrics for observability

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Active Projects | Growing adoption | Count of projects with recent activity |
| Daily Active Users | User engagement | Unique users per day across all projects |
| Messages per User | Usage depth | Average messages sent per active user |
| Agent Response Time | Performance | P95 latency < 2s for streaming start |
| System Uptime | Reliability | 99.9% availability |

## Current State (v1.0)

Conduit is **production-ready** with all core features implemented:
- ✅ Multi-project architecture with dynamic table creation
- ✅ Three agent connector types (LangGraph, OpenAI, HTTP)
- ✅ JWT authentication with LDAP support
- ✅ RBAC with project-level permissions and AD groups
- ✅ Streaming chat interface with file uploads
- ✅ Conversation management (create, list, delete, rename)
- ✅ Usage metrics and monitoring
- ✅ Neo-brutalist UI redesign with modern components

## What's Next?

See the [Roadmap](08-roadmap.md) for planned enhancements including:
- Soft deletes for conversations and messages
- Enhanced UI components across the platform
- Additional agent connector types (Anthropic, Azure OpenAI)
- Conversation-level permissions
- Advanced analytics dashboard

---

**Quick Links**:
- [Product Vision](02-product-vision.md) - Mission and positioning
- [Features](04-features.md) - Complete feature catalog
- [User Journeys](05-user-journeys.md) - Detailed workflows
- [Architecture](06-architecture.md) - Technical overview
