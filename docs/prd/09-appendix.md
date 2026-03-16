# Appendix

## Glossary

### Core Concepts

**Agent**
An AI model or service that responds to user messages. Configured per project with specific endpoints, authentication, and parameters.

**Agent Connector**
A software component that interfaces between Frontier and an AI agent. Implements the `BaseAgentConnector` interface with `stream()` and `close()` methods.

**Conversation**
A thread of messages between a user and an AI agent. Belongs to a specific project and user.

**LAN ID**
Local Area Network Identifier. A unique username used in enterprise LDAP/Active Directory systems.

**Message**
A single exchange in a conversation. Can be from the user (role: "user") or the AI agent (role: "assistant").

**Project**
An isolated workspace with dedicated database tables, agent configurations, and team members. The fundamental unit of organization in Frontier.

**Project Member**
A user who has been granted access to a project with a specific role (owner, admin, or member).

**RBAC (Role-Based Access Control)**
A permission system where access rights are assigned based on roles. Frontier uses three roles: owner, admin, and member.

**SSE (Server-Sent Events)**
A web technology for streaming data from server to client over HTTP. Used for real-time message streaming in Frontier.

**Thread**
In LangGraph context, a persistent conversation state maintained by the agent. Mapped to Frontier conversation IDs.

**Token**
The smallest unit of text processed by AI models. Used for billing and usage tracking. Roughly 4 characters per token in English.

### Technical Terms

**AD Group (Active Directory Group)**
A collection of users in Active Directory. Can be associated with Frontier projects to grant bulk access.

**Bearer Token**
An authentication method where the token itself grants access. Format: `Authorization: Bearer <token>`

**Dynamic Table Creation**
Frontier's approach of creating project-specific database tables at runtime rather than using a shared table with filtering.

**JWT (JSON Web Token)**
A compact, URL-safe token format used for authentication. Contains encoded user information and expiration.

**LDAP (Lightweight Directory Access Protocol)**
A protocol for accessing and maintaining directory services. Used for enterprise authentication.

**Neo-Brutalist Design**
A design style characterized by bold typography, high contrast, thick borders, and a raw, unpolished aesthetic.

**ORM (Object-Relational Mapping)**
A technique for converting between database tables and programming objects. Frontier uses SQLAlchemy.

**Prometheus**
An open-source monitoring and alerting toolkit. Frontier exposes metrics in Prometheus format.

**Sanitization**
The process of converting project names to valid SQL identifiers (e.g., "My Project!" → "my_project").

**Streaming Response**
Delivering AI-generated text incrementally as it's produced, rather than waiting for the complete response.

---

## API Quick Reference

### Authentication

```bash
# Login
POST /api/auth/login
Body: {"username": "user", "password": "pass"}
Response: {"access_token": "jwt_token", "token_type": "bearer"}

# Use token in subsequent requests
Authorization: Bearer <jwt_token>
```

### Projects

```bash
# List projects
GET /api/projects

# Create project
POST /api/projects
Body: {"name": "My Project", "description": "Description"}

# Get project details
GET /api/projects/{project_id}

# Update project
PUT /api/projects/{project_id}
Body: {"name": "Updated Name", "description": "Updated Description"}

# Delete project
DELETE /api/projects/{project_id}
```

### Conversations

```bash
# List conversations
GET /api/conversations/{project_name}

# Create conversation
POST /api/conversations/{project_name}
Body: {"title": "Conversation Title"}

# Rename conversation
PUT /api/conversations/{project_name}/{conversation_id}
Body: {"title": "New Title"}

# Delete conversation
DELETE /api/conversations/{project_name}/{conversation_id}
```

### Chat

```bash
# Stream chat response (SSE)
POST /api/chat/stream
Body: {
  "project_name": "my_project",
  "conversation_id": "123",
  "message": "Hello, AI!",
  "agent_id": 1
}
Response: text/event-stream

# Get message history
GET /api/chat/history/{project_name}/{conversation_id}
```

### Agents

```bash
# List agents for project
GET /api/agents/{project_id}

# Create agent
POST /api/agents
Body: {
  "project_id": 1,
  "name": "GPT-4",
  "agent_type": "openai",
  "endpoint": "https://api.openai.com/v1/chat/completions",
  "auth": {"auth_type": "bearer", "credentials": "sk-..."},
  "extras": {"model": "gpt-4"},
  "is_default": true
}

# Update agent
PUT /api/agents/{agent_id}

# Delete agent
DELETE /api/agents/{agent_id}
```

### RBAC

```bash
# List project members
GET /api/rbac/projects/{project_id}/members

# Add member
POST /api/rbac/projects/{project_id}/members
Body: {"user_id": 2, "role": "member"}

# Update member role
PUT /api/rbac/projects/{project_id}/members/{user_id}
Body: {"role": "admin"}

# Remove member
DELETE /api/rbac/projects/{project_id}/members/{user_id}
```

### Metrics

```bash
# Prometheus metrics
GET /metrics

# Usage statistics
GET /api/usage/{project_name}
```

---

## Configuration Reference

### config.yaml Structure

```yaml
app:
  host: "0.0.0.0"
  port: 8000
  debug: false

database:
  type: "sqlite"  # or "postgresql"
  path: "data/conduit.db"  # for SQLite
  # For PostgreSQL:
  # host: "localhost"
  # port: 5432
  # database: "conduit"
  # username: "conduit_user"
  # password: "secure_password"

jwt:
  secret_key: "your-secret-key-here"
  algorithm: "HS256"
  expire_minutes: 1440  # 24 hours

ldap:
  enabled: false
  server: "ldap://ldap.example.com"
  port: 389
  use_ssl: false
  search_base: "dc=example,dc=com"
  search_filter: "(uid={username})"
  bind_dn: "cn=admin,dc=example,dc=com"
  bind_password: "admin_password"

cors:
  origins:
    - "http://localhost:5173"  # Frontend dev server
    - "http://localhost:8000"  # Production
```

### Environment Variables

```bash
# Override config file location
export CONFIG_FILE=/path/to/config.yaml

# Database connection (alternative to config.yaml)
export DATABASE_URL=postgresql://user:pass@localhost/conduit

# JWT secret (alternative to config.yaml)
export JWT_SECRET_KEY=your-secret-key
```

---

## File Structure Reference

```
conduit/
├── project.py                        # Entry point
├── config.yaml                       # Configuration (root only)
├── src/
│   ├── api/
│   │   ├── main.py                  # FastAPI app
│   │   └── routers/                 # API endpoints
│   │       ├── auth.py
│   │       ├── chat.py
│   │       ├── projects.py
│   │       ├── agents.py
│   │       ├── conversations.py
│   │       ├── rbac.py
│   │       ├── metrics.py
│   │       └── usage.py
│   ├── core/
│   │   ├── agent/
│   │   │   ├── base_connector.py
│   │   │   └── connectors/
│   │   │       ├── langgraph_connector.py
│   │   │       ├── openai_connector.py
│   │   │       └── http_connector.py
│   │   ├── db/
│   │   │   ├── models.py
│   │   │   ├── database.py
│   │   │   └── db_chat.py
│   │   ├── auth/
│   │   │   ├── jwt.py
│   │   │   └── ldap.py
│   │   └── config.py
│   ├── sdk/                         # serve() in __init__.py
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── lib/
│   │   │   │   ├── ChatArea.svelte
│   │   │   │   ├── Sidebar.svelte
│   │   │   │   ├── ProjectSettings.svelte
│   │   │   │   └── ModelSelector.svelte
│   │   │   └── App.svelte
│   │   ├── dist/                    # Build output
│   │   └── package.json
│   └── data/
│       ├── conduit.db               # SQLite database
│       └── uploads/                 # Uploaded files
├── scripts/
│   ├── install_env.sh
│   ├── build_fe.sh
│   └── run.sh
├── docs/
│   ├── ard/                         # Architecture (C4, deployment)
│   ├── prd/                         # This PRD
│   ├── user-guide/                  # Connectors, supported elements
│   ├── feature/                     # Feature docs (dynamic UI, etc.)
│   └── user-journey/                # User journey maps
├── CLAUDE.md                        # Technical docs
└── ard/
    └── DATABASE_SCHEMA.md            # Schema docs
```

---

## Common Workflows

### Setting Up a New Project

1. Login to Frontier
2. Click "Create Project"
3. Enter project name and description
4. Navigate to project settings
5. Add an agent:
   - Select agent type (LangGraph, OpenAI, HTTP)
   - Enter endpoint URL
   - Configure authentication
   - Set as default
6. Invite team members:
   - Add by username
   - Assign roles (owner/admin/member)
7. Start chatting!

### Switching Between Agents

1. Open a conversation
2. Click the model selector dropdown
3. Select a different agent
4. Continue chatting (agent switch applies to new messages)

### Monitoring Usage

1. Navigate to project settings
2. Click "Usage Metrics"
3. View conversation count, message count, token usage
4. Export data for reporting

### Deploying to Production

1. Clone repository
2. Run `sh scripts/install_env.sh`
3. Create `config.yaml` with production settings:
   - PostgreSQL connection
   - LDAP configuration
   - CORS origins
4. Run `sh scripts/build_fe.sh`
5. Run `sh scripts/run.sh` (or use systemd/Docker)
6. Configure Prometheus to scrape `/metrics`
7. Set up reverse proxy (Nginx) with HTTPS

---

## Troubleshooting

### Common Issues

**Issue**: "Authentication failed" when using LDAP
**Solution**:
- Verify LDAP server is reachable
- Check `search_base` and `search_filter` in config
- Test with `ldapsearch` command
- Check bind DN and password

**Issue**: "Agent connection failed"
**Solution**:
- Verify agent endpoint URL is correct
- Check authentication credentials
- Test endpoint with `curl`
- Review agent logs for errors

**Issue**: "Database connection error"
**Solution**:
- Verify database is running
- Check connection string in config
- Ensure database user has correct permissions
- Check firewall rules

**Issue**: "Streaming response is slow"
**Solution**:
- Check agent API response time
- Verify network latency to agent
- Review server resource utilization
- Check for rate limiting on agent API

**Issue**: "Frontend not loading"
**Solution**:
- Verify frontend was built (`sh scripts/build_fe.sh`)
- Check `dist/` directory exists
- Review CORS configuration
- Check browser console for errors

---

## Support & Resources

### Documentation

- **Technical Docs**: [CLAUDE.md](../../CLAUDE.md)
- **Database Schema**: [DATABASE_SCHEMA.md](../ard/DATABASE_SCHEMA.md)
- **Documentation index**: [docs/README.md](../README.md)
- **User guides** (connectors, elements): [docs/user-guide/](../user-guide/)
- **This PRD**: [docs/prd/](../prd/)

### Community

- **GitHub Repository**: [Link to repo]
- **Issue Tracker**: [Link to issues]
- **Discussions**: [Link to discussions]
- **Community Forum**: [Link to forum]

### Getting Help

1. **Documentation**: Check docs first
2. **Search Issues**: Someone may have had the same problem
3. **Ask Community**: Post in discussions or forum
4. **File Issue**: If it's a bug or feature request
5. **Contact Support**: For enterprise customers

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | March 2026 | Initial PRD release |

---

## Contributors

This PRD was created by analyzing the Frontier codebase and working backwards from the implementation to document the product vision, features, and roadmap.

**Acknowledgments**:
- Frontier development team
- Early adopters and beta testers
- Community contributors

---

## License

[Specify license information]

---

**End of PRD**

For questions or feedback about this PRD, please open an issue or contact the product team.
