# User Journey Map: Conduit AI Chat Platform

## Overview

This document maps the complete user experience across Conduit's primary user journeys, identifying emotional states, pain points, and optimization opportunities at each touchpoint.

---

## Journey 1: End User - First-Time Experience to Daily Usage

**Persona**: Sarah, Product Manager
**Goal**: Get AI assistance for product planning and team collaboration
**Context**: First time using Conduit after team adoption
**Duration**: 15 minutes (first session) → 2-5 minutes (daily sessions)

---

### Stage 1: Discovery & Access

**User Goal**: Learn about Conduit and gain access

**Actions**:
- Receives invitation email or Slack message from team lead
- Clicks link to Conduit platform
- Arrives at login page

**Touchpoints**: Email, Slack, Login page

**Emotions**: 😐 **Neutral → Curious**
*"Another tool to learn? Hope this is worth it."*

**Pain Points**:
- **Unclear value proposition**: No context on why this is better than ChatGPT
- **Access uncertainty**: Unsure if credentials will work (LDAP vs local)
- **Onboarding gap**: No welcome message or quick start guide

**Opportunities**:
- ✨ Add splash screen with 30-second value prop video
- ✨ Show "What makes Conduit different" on login page
- ✨ Display authentication method clearly (SSO vs username/password)
- ✨ Send welcome email with quick start guide

**Metrics**:
- Time from invitation to first login
- Login success rate (first attempt)
- Bounce rate on login page

---

### Stage 2: Authentication

**User Goal**: Successfully log in to the platform

**Actions**:
- Enters LDAP credentials (or username/password)
- Submits login form
- Waits for authentication

**Touchpoints**: Login form, LDAP server, JWT token generation

**Emotions**: 😰 **Anxious → 😊 Relieved**
*"Will my work credentials work here? Oh good, I'm in!"*

**Pain Points**:
- **Slow LDAP response**: 3-5 second wait with no feedback
- **Generic errors**: "Authentication failed" without explanation
- **Password confusion**: Unclear if using work password or new password
- **No "Remember me"**: Must re-login frequently

**Opportunities**:
- ✨ Add loading spinner with "Authenticating with LDAP..." message
- ✨ Specific error messages: "LDAP server unavailable" vs "Invalid credentials"
- ✨ Add "Remember this device" checkbox for 30-day sessions
- ✨ Show authentication method on login page ("Use your work credentials")

**Metrics**:
- Average authentication time
- Authentication failure rate
- Support tickets related to login issues

---

### Stage 3: Project Selection

**User Goal**: Find and access the right project

**Actions**:
- Views list of available projects
- Scans project names and descriptions
- Clicks on "Product Roadmap Q1" project

**Touchpoints**: Project list dashboard

**Emotions**: 😐 **Neutral → 😤 Slightly Frustrated**
*"Which project am I supposed to use? There are 12 here..."*

**Pain Points**:
- **Information overload**: Too many projects without clear organization
- **No search/filter**: Hard to find specific project in long list
- **Unclear membership**: Can't tell which projects I'm active in
- **No favorites**: Can't pin frequently used projects to top

**Opportunities**:
- ✨ Add search bar and filter by "My Projects" vs "All Projects"
- ✨ Show "Last accessed" timestamp and sort by recency
- ✨ Add star/favorite functionality for quick access
- ✨ Group projects by team or category
- ✨ Show member count and activity indicators

**Metrics**:
- Time to find target project
- Number of projects viewed before selection
- Frequency of project switching

---

### Stage 4: Conversation Discovery

**User Goal**: Resume existing conversation or start new one

**Actions**:
- Views conversation list in sidebar
- Scans conversation titles
- Decides between resuming or starting fresh
- Clicks "Feature Prioritization Discussion"

**Touchpoints**: Sidebar, Conversation list

**Emotions**: 😊 **Satisfied**
*"Great, I can see my history. Let me continue where I left off."*

**Pain Points**:
- **Long conversation titles**: Truncated, hard to distinguish
- **No preview**: Can't see last message without clicking
- **No search**: Hard to find old conversations
- **No organization**: All conversations in flat list
- **Unclear timestamps**: "2 days ago" vs specific date

**Opportunities**:
- ✨ Show last message preview (first 50 chars)
- ✨ Add conversation search with keyword highlighting
- ✨ Add folders or tags for organization
- ✨ Show conversation participant count (if multi-user)
- ✨ Add "Archive" feature to hide old conversations

**Metrics**:
- Conversation retrieval time
- Number of conversations viewed before selection
- Search usage rate (if implemented)

---

### Stage 5: Message History Review

**User Goal**: Understand conversation context before continuing

**Actions**:
- Scrolls through previous messages
- Reads AI's last response
- Identifies where conversation left off

**Touchpoints**: Chat area, Message history

**Emotions**: 😊 **Confident**
*"Perfect, I remember this. Now I can ask my follow-up."*

**Pain Points**:
- **Slow loading**: Large conversations take 2-3 seconds to load
- **No jump to bottom**: Must scroll through entire history
- **No message search**: Can't find specific point in conversation
- **Unclear agent**: Can't tell which AI model provided each response
- **No timestamps**: Hard to know when messages were sent

**Opportunities**:
- ✨ Lazy load messages (show recent 20, load more on scroll)
- ✨ Add "Jump to latest" button
- ✨ Add in-conversation search (Ctrl+F enhancement)
- ✨ Show agent name/icon next to each AI response
- ✨ Add relative timestamps ("2 hours ago") on hover

**Metrics**:
- Message history load time
- Scroll depth before sending new message
- Conversation length at which users start new conversations

---

### Stage 6: Composing Message

**User Goal**: Ask a clear, well-formed question

**Actions**:
- Clicks in message input box
- Types question: "Based on our discussion, what should be the top 3 priorities?"
- Reviews message for clarity
- Presses Enter or clicks Send

**Touchpoints**: Message input box, Send button

**Emotions**: 😊 **Engaged**
*"This is easy. Just like texting."*

**Pain Points**:
- **No formatting**: Can't bold, italicize, or add code blocks
- **No file attachment**: Can't easily add context documents
- **No draft saving**: Lose message if accidentally navigate away
- **No character limit indicator**: Unsure if message is too long
- **No multi-line support**: Enter sends instead of new line

**Opportunities**:
- ✨ Add Shift+Enter for new line, Enter to send
- ✨ Add markdown formatting toolbar (bold, italic, code)
- ✨ Add drag-and-drop file upload
- ✨ Auto-save drafts every 5 seconds
- ✨ Show character count and suggested max length

**Metrics**:
- Average message length
- Message edit/delete rate
- File attachment usage rate (if implemented)

---

### Stage 7: Waiting for Response

**User Goal**: Get fast, relevant answer

**Actions**:
- Watches for response to appear
- Sees "..." typing indicator
- Waits for streaming to begin

**Touchpoints**: Chat area, Agent API, SSE connection

**Emotions**: 😰 **Anxious → 😤 Frustrated**
*"Why is this taking so long? Is it working?"*

**Pain Points**:
- **Slow initial response**: 3-5 seconds before first token appears
- **No progress indicator**: Unclear if request is processing
- **Connection failures**: SSE drops without clear error
- **No cancel option**: Can't stop generation if question was wrong
- **Unclear agent status**: Don't know which model is responding

**Opportunities**:
- ✨ Show "Thinking..." with animated indicator
- ✨ Display estimated response time based on message length
- ✨ Add "Cancel generation" button
- ✨ Show agent name/model prominently during generation
- ✨ Retry automatically on connection failure (with notification)

**Metrics**:
- Time to first token (p50, p95, p99)
- SSE connection failure rate
- User cancellation rate (if implemented)

---

### Stage 8: Receiving Streaming Response

**User Goal**: Read and understand AI's answer

**Actions**:
- Watches tokens appear in real-time
- Reads response as it generates
- Evaluates quality and relevance

**Touchpoints**: Chat area, Streaming SSE

**Emotions**: 😊 **Delighted**
*"This is exactly what I needed! And it's so fast!"*

**Pain Points**:
- **Too fast to read**: Streaming speed makes it hard to follow
- **No pause**: Can't pause generation to think
- **Formatting issues**: Code blocks or lists render poorly during streaming
- **No copy button**: Hard to copy specific parts of response
- **No feedback mechanism**: Can't rate response quality

**Opportunities**:
- ✨ Add adjustable streaming speed control
- ✨ Add "Pause" button during generation
- ✨ Improve streaming markdown rendering (buffer until complete block)
- ✨ Add "Copy" button to each message
- ✨ Add 👍/👎 feedback buttons to each response

**Metrics**:
- Streaming tokens per second
- User engagement during streaming (scroll, click away)
- Response quality ratings (if implemented)

---

### Stage 9: Follow-Up or Context Switch

**User Goal**: Continue conversation or move to different task

**Actions**:
- Decides whether to ask follow-up or switch context
- Either types new message or navigates to different conversation/project

**Touchpoints**: Message input, Sidebar, Project selector

**Emotions**: 😊 **Satisfied → 😐 Neutral**
*"Got what I needed. Time to move on."*

**Pain Points**:
- **Lost context**: Switching projects loses current conversation state
- **No multi-tasking**: Can't have multiple conversations open
- **No notifications**: Miss responses if navigating away
- **No conversation linking**: Can't reference other conversations
- **No export**: Can't easily share conversation with team

**Opportunities**:
- ✨ Add tabs for multiple conversations
- ✨ Add browser notifications for new responses
- ✨ Add "Share conversation" link generation
- ✨ Add export to Markdown/PDF
- ✨ Add conversation linking with @mentions

**Metrics**:
- Average conversation length (messages per session)
- Context switch frequency
- Export/share usage rate (if implemented)

---

## Journey 2: Project Admin - Project Setup & Team Onboarding

**Persona**: Alex, Engineering Manager
**Goal**: Set up new project and onboard team
**Context**: New team initiative requiring AI assistance
**Duration**: 10-15 minutes (setup) + 5 minutes (per team member)

---

### Stage 1: Project Creation

**User Goal**: Create new project workspace

**Actions**:
- Clicks "Create Project" button
- Enters project name "Code Review Assistant"
- Adds description
- Submits form

**Touchpoints**: Project creation form

**Emotions**: 😊 **Optimistic**
*"This looks straightforward. Let's get the team set up."*

**Pain Points**:
- **Name validation unclear**: Don't know if special characters are allowed
- **No templates**: Must configure everything from scratch
- **No preview**: Can't see what project will look like before creating
- **Unclear next steps**: After creation, unsure what to do next

**Opportunities**:
- ✨ Add real-time name validation with clear rules
- ✨ Provide project templates (Engineering, Product, Research)
- ✨ Add setup wizard with guided steps
- ✨ Show "Next: Configure Agent" prompt after creation

**Metrics**:
- Project creation time
- Form abandonment rate
- Projects created vs projects with activity

---

### Stage 2: Agent Configuration

**User Goal**: Connect AI agent to project

**Actions**:
- Navigates to Agent Settings
- Clicks "Add Agent"
- Selects "OpenAI" type
- Enters API endpoint and key
- Chooses "gpt-4" model
- Saves configuration

**Touchpoints**: Agent configuration form, Agent API (test connection)

**Emotions**: 😤 **Frustrated → 😰 Anxious**
*"Where do I find my API key? Is this endpoint correct?"*

**Pain Points**:
- **Technical complexity**: Requires understanding of API endpoints and keys
- **No validation**: Can save invalid configuration
- **Security concerns**: API key visible in plain text
- **No guidance**: Unclear what each field means
- **No test before save**: Must save to test if it works

**Opportunities**:
- ✨ Add "Test Connection" button before saving
- ✨ Provide endpoint templates for common providers
- ✨ Add tooltips explaining each field
- ✨ Mask API keys with ••••• after entry
- ✨ Add "Import from environment variable" option

**Metrics**:
- Agent configuration success rate (first attempt)
- Time spent on agent configuration
- Support tickets related to agent setup

---

### Stage 3: Agent Testing

**User Goal**: Verify agent works correctly

**Actions**:
- Sends test message "Hello, can you hear me?"
- Waits for response
- Evaluates response quality

**Touchpoints**: Test chat interface, Agent API

**Emotions**: 😰 **Anxious → 😊 Relieved**
*"Please work... Yes! It's responding!"*

**Pain Points**:
- **No dedicated test interface**: Must create conversation to test
- **Unclear errors**: "Connection failed" without details
- **No retry**: Must reconfigure and save to try again
- **No comparison**: Can't test multiple agents side-by-side

**Opportunities**:
- ✨ Add dedicated "Test Agent" modal with sample prompts
- ✨ Show detailed error logs for debugging
- ✨ Add "Retry" button on failure
- ✨ Provide agent comparison tool

**Metrics**:
- Agent test success rate
- Number of test attempts before success
- Time from configuration to successful test

---

### Stage 4: Team Member Invitation

**User Goal**: Add team members with appropriate permissions

**Actions**:
- Navigates to Members tab
- Clicks "Add Member"
- Enters usernames: john.doe, jane.smith, etc.
- Assigns roles (member, admin)
- Sends invitations

**Touchpoints**: Member management interface

**Emotions**: 😐 **Neutral → 😤 Tedious**
*"Why do I have to add them one by one? This is taking forever."*

**Pain Points**:
- **One-by-one addition**: No bulk import
- **Username lookup**: Must know exact usernames
- **No email invites**: Can't invite via email
- **Role confusion**: Unclear difference between admin and member
- **No AD group sync**: Must manually add each person

**Opportunities**:
- ✨ Add bulk import via CSV or paste list
- ✨ Add user search/autocomplete
- ✨ Send email invitations with project link
- ✨ Add role comparison table in UI
- ✨ Enable AD group-based access (already in backend!)

**Metrics**:
- Average time per member addition
- Bulk vs individual addition ratio
- Member invitation acceptance rate

---

### Stage 5: Usage Monitoring

**User Goal**: Track team adoption and costs

**Actions**:
- Navigates to Usage Metrics
- Views conversation count, message count
- Checks token usage
- Identifies heavy users

**Touchpoints**: Metrics dashboard

**Emotions**: 😊 **Satisfied → 😤 Concerned**
*"Good adoption! Wait, why is token usage so high?"*

**Pain Points**:
- **No cost estimates**: Token count doesn't translate to dollars
- **No alerts**: Don't know when usage spikes
- **Limited time ranges**: Can't view custom date ranges
- **No export**: Can't share metrics with leadership
- **No per-user breakdown**: Hard to identify optimization opportunities

**Opportunities**:
- ✨ Add cost calculator with configurable rates
- ✨ Add usage alerts (email/Slack when threshold exceeded)
- ✨ Add custom date range picker
- ✨ Add CSV/PDF export
- ✨ Add per-user usage breakdown with charts

**Metrics**:
- Metrics dashboard usage frequency
- Average time spent on metrics page
- Cost-related support tickets

---

## Journey 3: Platform Admin - Initial Deployment

**Persona**: Jordan, DevOps Engineer
**Goal**: Deploy Conduit for organization
**Context**: New platform rollout
**Duration**: 30-60 minutes (initial setup)

---

### Stage 1: Installation

**User Goal**: Get Conduit running locally

**Actions**:
- Clones repository
- Runs `python project.py`
- Sees server start

**Touchpoints**: Terminal, Documentation

**Emotions**: 😊 **Pleased**
*"Wow, that was easy! No complex setup."*

**Pain Points**:
- **Dependency issues**: Python version mismatches
- **No health check**: Unclear if server is fully ready
- **Port conflicts**: Default port 8000 already in use
- **No logs**: Hard to debug if something fails

**Opportunities**:
- ✨ Add dependency version check on startup
- ✨ Add `/health` endpoint check in startup script
- ✨ Auto-detect and suggest alternative port if 8000 is busy
- ✨ Add structured logging with log levels

**Metrics**:
- Time from clone to running server
- Installation failure rate
- Support tickets during deployment

---

### Stage 2: Configuration

**User Goal**: Configure for production (database, LDAP, CORS)

**Actions**:
- Copies `config.yaml.example` to `config.yaml`
- Updates database connection string
- Adds LDAP settings
- Configures CORS origins
- Restarts server

**Touchpoints**: config.yaml file, Documentation

**Emotions**: 😐 **Neutral → 😤 Frustrated**
*"Which LDAP fields are required? The docs don't say."*

**Pain Points**:
- **Unclear required fields**: Don't know what's mandatory vs optional
- **No validation**: Invalid config only discovered at runtime
- **No examples**: LDAP config example is generic
- **Restart required**: Must restart server to test config changes
- **No secrets management**: API keys in plain text config file

**Opportunities**:
- ✨ Add config validation command: `python project.py --validate-config`
- ✨ Add inline comments in config.yaml.example explaining each field
- ✨ Support environment variables for secrets
- ✨ Add hot-reload for non-critical config changes
- ✨ Provide organization-specific config templates

**Metrics**:
- Configuration errors per deployment
- Time spent on configuration
- Config-related support tickets

---

### Stage 3: LDAP Integration Testing

**User Goal**: Verify SSO works for users

**Actions**:
- Attempts login with LDAP credentials
- Checks logs for LDAP connection
- Tests with multiple users

**Touchpoints**: Login page, LDAP server, Application logs

**Emotions**: 😰 **Anxious → 😡 Angry**
*"Why isn't LDAP working? The error message is useless!"*

**Pain Points**:
- **Generic errors**: "LDAP authentication failed" without details
- **No test tool**: Must use actual login to test
- **Unclear logs**: LDAP errors buried in application logs
- **No fallback**: Can't login locally if LDAP is down
- **Connection timeout**: Long wait before failure

**Opportunities**:
- ✨ Add LDAP test command: `python project.py --test-ldap`
- ✨ Detailed error messages: "LDAP server unreachable at ldap://..."
- ✨ Separate LDAP logs from application logs
- ✨ Add local admin account as fallback
- ✨ Add connection timeout configuration

**Metrics**:
- LDAP integration success rate
- Time to successful LDAP login
- LDAP-related support tickets

---

### Stage 4: Monitoring Setup

**User Goal**: Integrate with Prometheus and alerting

**Actions**:
- Adds Conduit `/metrics` endpoint to Prometheus config
- Creates Grafana dashboard
- Sets up alerts for errors and high usage

**Touchpoints**: Prometheus, Grafana, /metrics endpoint

**Emotions**: 😊 **Satisfied**
*"Great, standard Prometheus metrics. Easy to integrate."*

**Pain Points**:
- **No dashboard template**: Must create Grafana dashboard from scratch
- **Limited metrics**: Missing some key application metrics
- **No alert templates**: Must define alert rules manually
- **No documentation**: Unclear what each metric measures

**Opportunities**:
- ✨ Provide Grafana dashboard JSON template
- ✨ Add more application-specific metrics (conversation rate, agent errors)
- ✨ Provide Prometheus alert rule examples
- ✨ Document all metrics in /metrics endpoint or docs

**Metrics**:
- Time to first metric scraped
- Dashboard creation time
- Monitoring coverage (% of key metrics tracked)

---

## Cross-Journey Insights

### Emotional Journey Summary

```
Discovery → Authentication → Project Selection → Conversation → Response
   😐           😰→😊              😤                😊           😰→😊

Setup → Configuration → Testing → Onboarding → Monitoring
  😊        😤→😰         😰→😊        😤           😊→😤
```

### Critical Moments (Make or Break)

1. **First Login** (Stage 2): If authentication fails, users may abandon platform
2. **First Response** (Stage 7-8): If slow or irrelevant, users lose trust
3. **Agent Configuration** (Journey 2, Stage 2): If too complex, admins need support
4. **LDAP Integration** (Journey 3, Stage 3): If fails, blocks entire org rollout

### Top 5 Pain Points Across All Journeys

1. **Slow response times** (3-5 seconds to first token)
2. **Generic error messages** (authentication, agent config, LDAP)
3. **No search functionality** (projects, conversations, messages)
4. **Manual bulk operations** (adding team members one-by-one)
5. **Limited visibility** (no cost estimates, no usage alerts)

### Top 5 Opportunities for Impact

1. **Add comprehensive search** (projects, conversations, in-message)
   - Impact: Reduces time to find information by 70%
   - Effort: Medium (2-3 weeks)

2. **Improve error messages with actionable guidance**
   - Impact: Reduces support tickets by 50%
   - Effort: Low (1 week)

3. **Add bulk operations** (member import, conversation export)
   - Impact: Reduces admin time by 60%
   - Effort: Medium (2 weeks)

4. **Add cost estimation and alerts**
   - Impact: Increases admin confidence, reduces surprise costs
   - Effort: Low (1 week)

5. **Optimize first token latency** (< 1 second)
   - Impact: Dramatically improves perceived performance
   - Effort: High (4-6 weeks, requires agent optimization)

---

## Metrics Dashboard

### User Satisfaction Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Time to first response | < 2s | 3-5s | 🔴 Needs improvement |
| Login success rate (first attempt) | > 95% | ~85% | 🟡 Acceptable |
| Project setup time | < 5 min | ~10 min | 🟡 Acceptable |
| Conversation retrieval time | < 1s | < 1s | 🟢 Good |
| Agent config success rate | > 90% | ~70% | 🔴 Needs improvement |

### Engagement Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Daily active users | Track growth | Count unique users per day |
| Messages per user per day | > 5 | Average messages sent |
| Conversation length | > 10 messages | Average messages per conversation |
| Project switching frequency | < 3 per session | Count project changes |
| Return rate (7-day) | > 80% | Users active in week 2 after first use |

---

## Next Steps

### Immediate (Next Sprint)
1. Improve error messages across authentication and agent configuration
2. Add search to project list and conversation sidebar
3. Add "Test Connection" button to agent configuration

### Short-term (Next Quarter)
1. Implement bulk member import via CSV
2. Add cost estimation to usage metrics
3. Optimize first token latency (caching, connection pooling)
4. Add Grafana dashboard template

### Long-term (Next 6 Months)
1. Implement full-text search across all conversations
2. Add conversation export and sharing
3. Build admin analytics dashboard
4. Add mobile-responsive design improvements

---

**Related Documents**:
- [User Personas](docs/prd/03-user-personas.md)
- [User Journeys](docs/prd/05-user-journeys.md)
- [Features & Capabilities](docs/prd/04-features.md)
- [Success Metrics](docs/prd/07-success-metrics.md)
