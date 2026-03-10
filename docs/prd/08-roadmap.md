# Roadmap

## Current State (v1.0)

Conduit is **production-ready** with a comprehensive feature set for multi-project AI chat with enterprise controls.

### Implemented Features

#### Core Platform ✅
- Multi-project architecture with dynamic table creation
- Project CRUD operations
- Project-specific database isolation
- SQLite and PostgreSQL/YugabyteDB support

#### Authentication & Authorization ✅
- JWT-based authentication
- LDAP/Active Directory integration
- Role-based access control (owner/admin/member)
- AD group-based project access
- Project membership management

#### AI Agent Integration ✅
- Three connector types: LangGraph, OpenAI, HTTP
- Flexible agent configuration
- Multiple authentication methods (bearer, basic, api_key)
- Default agent per project
- Agent switching within conversations

#### Chat Experience ✅
- Real-time streaming via Server-Sent Events
- Conversation management (create, list, rename, delete)
- Message history persistence
- File upload support
- Multi-line message input

#### User Interface ✅
- Modern Svelte-based SPA
- Neo-brutalist design system
- Responsive chat interface
- Project and conversation navigation
- Model/agent selector
- Project settings UI

#### Monitoring & Operations ✅
- Prometheus metrics endpoint
- Usage tracking (conversations, messages, tokens)
- System health monitoring
- YAML-based configuration
- Single-command deployment

---

## Planned Enhancements (v1.x)

### Phase 1: Data Management & UX Polish

#### Soft Deletes for Conversations & Messages
**Status**: Planned
**Priority**: P1
**Rationale**: Noted in [DATABASE_SCHEMA.md](../ard/DATABASE_SCHEMA.md) as not implemented

**Features**:
- Add `deleted_at` timestamp to conversation and message tables
- Soft delete instead of hard delete
- "Trash" view for recovering deleted conversations
- Permanent delete after 30 days
- Admin override for immediate permanent delete

**User Benefit**: Recover accidentally deleted conversations

**Technical Changes**:
- Add `deleted_at` column to dynamic table creation
- Update delete endpoints to set timestamp instead of DELETE
- Filter queries to exclude soft-deleted records
- Add recovery endpoint

#### Enhanced Conversation Management
**Status**: Planned
**Priority**: P1

**Features**:
- Search conversations by title or content
- Filter conversations by date range
- Tag/label conversations
- Pin important conversations
- Archive old conversations
- Bulk operations (delete, archive, tag)

**User Benefit**: Better organization and discoverability

#### Rich File Handling
**Status**: Planned
**Priority**: P2

**Features**:
- File preview (images, PDFs, text)
- File search within conversations
- File annotations and comments
- Support for more file types
- Drag-and-drop file upload
- File size limits and validation

**User Benefit**: Better context sharing with AI agents

### Phase 2: Enhanced UI Components

#### Extended Neo-Brutalist Design
**Status**: In Progress
**Priority**: P1
**Rationale**: SIDEBAR_REDESIGN.md shows UI modernization effort

**Features**:
- Apply neo-brutalist design to all components
- Consistent color scheme and typography
- Improved accessibility (WCAG 2.1 AA)
- Dark mode support
- Customizable themes per project
- Component library documentation

**User Benefit**: Polished, professional interface

#### Advanced Chat Features
**Status**: Planned
**Priority**: P2

**Features**:
- Message editing and deletion
- Message reactions and annotations
- Code syntax highlighting
- Markdown rendering improvements
- Message threading/replies
- Export conversations (PDF, Markdown, JSON)

**User Benefit**: More powerful chat interactions

#### Improved Model Selector
**Status**: Planned
**Priority**: P2

**Features**:
- Agent comparison view
- Agent performance metrics
- Agent cost estimates
- Agent descriptions and capabilities
- Favorite agents
- Recent agents quick access

**User Benefit**: Easier agent selection and comparison

### Phase 3: Collaboration & Sharing

#### Conversation-Level Permissions
**Status**: Planned
**Priority**: P1
**Rationale**: Natural extension of existing RBAC system

**Features**:
- Share conversations with specific users
- Read-only vs. edit permissions
- Public conversation links (with expiry)
- Conversation ownership transfer
- Team conversations (multiple owners)

**User Benefit**: Collaborate on specific conversations

#### Team Features
**Status**: Planned
**Priority**: P2

**Features**:
- @mention team members in conversations
- Conversation handoff (assign to user)
- Team activity feed
- Shared conversation templates
- Team-wide agent configurations

**User Benefit**: Better team collaboration

#### Notifications
**Status**: Planned
**Priority**: P2

**Features**:
- In-app notifications
- Email notifications (optional)
- Notification preferences per project
- @mention notifications
- Conversation activity notifications

**User Benefit**: Stay informed of team activity

---

## Future Enhancements (v2.x)

### Intelligence Layer

#### Conversation Analytics
**Status**: Future
**Priority**: P2

**Features**:
- Conversation sentiment analysis
- Topic extraction and clustering
- Usage patterns and insights
- Agent performance comparison
- Cost optimization recommendations

**User Benefit**: Data-driven insights into AI usage

#### Smart Organization
**Status**: Future
**Priority**: P2

**Features**:
- Auto-tagging conversations
- Suggested conversation titles
- Related conversation recommendations
- Smart search with semantic similarity
- Conversation summarization

**User Benefit**: Effortless organization

#### Agent Recommendations
**Status**: Future
**Priority**: P2

**Features**:
- Suggest best agent for query type
- Agent performance tracking
- A/B testing different agents
- Cost vs. quality trade-off analysis

**User Benefit**: Optimal agent selection

### Additional Agent Connectors

#### Anthropic Claude Connector
**Status**: Planned
**Priority**: P1
**Rationale**: Major AI provider, high user demand

**Features**:
- Native Claude API integration
- Support for Claude 3 models (Opus, Sonnet, Haiku)
- Streaming support
- Tool use / function calling

#### Azure OpenAI Connector
**Status**: Planned
**Priority**: P1
**Rationale**: Enterprise customers often use Azure

**Features**:
- Azure-specific authentication
- Deployment-based model selection
- Azure-specific rate limiting
- Integration with Azure monitoring

#### Google Gemini Connector
**Status**: Future
**Priority**: P2

**Features**:
- Gemini API integration
- Multi-modal support (text, images)
- Streaming support

#### Custom Connector Marketplace
**Status**: Future
**Priority**: P2

**Features**:
- Community-contributed connectors
- Connector discovery and installation
- Connector ratings and reviews
- Connector documentation templates

**User Benefit**: Ecosystem growth and flexibility

---

## Platform Ecosystem (v3.x)

### Workflow Automation

**Features**:
- Scheduled conversations (daily summaries, reports)
- Webhook integrations
- Zapier/Make.com integration
- Custom automation scripts
- Conversation triggers and actions

**User Benefit**: Automate repetitive AI tasks

### Multi-Modal Support

**Features**:
- Voice input and output
- Image generation and analysis
- Document processing and extraction
- Video analysis
- Audio transcription

**User Benefit**: Richer AI interactions

### Advanced Compliance & Governance

**Features**:
- Comprehensive audit logs
- Data retention policies
- Compliance reports (GDPR, HIPAA, SOC 2)
- Data export and deletion tools
- Encryption at rest and in transit
- Role-based audit log access

**User Benefit**: Meet regulatory requirements

### Enterprise Features

**Features**:
- Single Sign-On (SAML, OAuth)
- Custom branding and white-labeling
- Multi-region deployment
- High availability and disaster recovery
- SLA guarantees
- Dedicated support

**User Benefit**: Enterprise-grade platform

---

## Roadmap Inference Methodology

This roadmap was inferred from the existing codebase by analyzing:

1. **Explicit TODOs**: [DATABASE_SCHEMA.md](../ard/DATABASE_SCHEMA.md) mentions soft deletes not implemented
2. **Design Patterns**: Extensible connector architecture suggests more connector types
3. **UI Evolution**: SIDEBAR_REDESIGN.md shows ongoing UI modernization
4. **RBAC Foundation**: Project-level permissions naturally extend to conversation-level
5. **Metrics Infrastructure**: Prometheus integration enables analytics dashboard
6. **File Handling**: Basic support suggests enhanced features coming
7. **Configuration Flexibility**: YAML-based config suggests UI-based admin panel
8. **Market Trends**: Major AI providers (Anthropic, Azure, Google) are logical additions

---

## Release Timeline (Estimated)

| Version | Target | Focus |
|---------|--------|-------|
| **v1.0** | ✅ Current | Core platform with multi-project chat |
| **v1.1** | Q2 2026 | Soft deletes, conversation search, UI polish |
| **v1.2** | Q3 2026 | Conversation-level permissions, Anthropic connector |
| **v1.3** | Q4 2026 | Advanced chat features, Azure OpenAI connector |
| **v2.0** | Q1 2027 | Analytics dashboard, smart organization |
| **v2.1** | Q2 2027 | Workflow automation, Gemini connector |
| **v3.0** | Q3 2027 | Multi-modal support, advanced compliance |

**Note**: Timeline is estimated based on typical development velocity and assumes a small team (2-4 engineers).

---

## Community Contributions

### Open Source Opportunities

**Connector Contributions**:
- Community members can build and share custom connectors
- Reference implementations provided
- Connector testing framework
- Documentation templates

**UI Components**:
- Custom themes and designs
- Accessibility improvements
- Internationalization (i18n)

**Integrations**:
- Third-party service integrations
- Webhook handlers
- Export formats

### Contribution Guidelines

1. **Connector Development**:
   - Inherit from `BaseAgentConnector`
   - Include comprehensive tests
   - Document configuration options
   - Provide example usage

2. **UI Contributions**:
   - Follow neo-brutalist design system
   - Ensure accessibility compliance
   - Include responsive design
   - Add Storybook stories

3. **Documentation**:
   - Update relevant docs
   - Include examples
   - Add to changelog

---

## Feature Requests & Feedback

### How to Request Features

1. **GitHub Issues**: Open an issue with the `feature-request` label
2. **Community Forum**: Discuss ideas with other users
3. **User Surveys**: Participate in quarterly feedback surveys
4. **Direct Feedback**: Contact the product team

### Prioritization Criteria

Features are prioritized based on:
1. **User Impact**: How many users benefit?
2. **Strategic Alignment**: Does it support core mission?
3. **Technical Feasibility**: Can we build it well?
4. **Resource Availability**: Do we have capacity?
5. **Community Demand**: How many requests?

---

## Deprecation Policy

### Breaking Changes

- **Major versions** (v1.x → v2.x): May include breaking changes
- **Minor versions** (v1.1 → v1.2): Backward compatible
- **Patch versions** (v1.1.0 → v1.1.1): Bug fixes only

### Deprecation Process

1. **Announcement**: Feature marked as deprecated in release notes
2. **Grace Period**: Minimum 6 months before removal
3. **Migration Guide**: Provided for all breaking changes
4. **Warnings**: Logged when deprecated features are used
5. **Removal**: Only in major version releases

---

**Next**: [Appendix](09-appendix.md) - Glossary and references
