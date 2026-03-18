# Success Metrics

## Overview

Success metrics for Frontier are organized into three categories: User Engagement, System Performance, and Business Impact. These metrics guide product decisions and measure the platform's effectiveness.

---

## User Engagement Metrics

### Active Users

**Definition**: Unique users who send at least one message in a given time period

**Measurement**:
- Daily Active Users (DAU)
- Weekly Active Users (WAU)
- Monthly Active Users (MAU)

**Targets**:
- DAU/MAU ratio > 40% (indicates strong daily engagement)
- WAU growth rate > 10% month-over-month
- User retention > 70% after 30 days

**Data Source**: `project_members` table + message timestamps

**Query Example**:
```sql
SELECT COUNT(DISTINCT user_id) as dau
FROM {project}_messages
WHERE DATE(timestamp) = CURRENT_DATE;
```

### Messages per User

**Definition**: Average number of messages sent per active user

**Measurement**:
- Messages per user per day
- Messages per user per session
- Distribution of power users vs. casual users

**Targets**:
- Average 10+ messages per user per day
- 80/20 rule: 20% of users generate 80% of messages
- Increasing trend over time (indicates growing reliance)

**Data Source**: `{project}_messages` table

**Insights**:
- Low messages/user → Onboarding or UX issues
- High messages/user → Strong product-market fit
- Declining trend → Feature gaps or competition

### Conversation Depth

**Definition**: Number of messages per conversation

**Measurement**:
- Average messages per conversation
- Distribution of short (< 5 messages) vs. long (> 20 messages) conversations
- Conversation completion rate

**Targets**:
- Average 15+ messages per conversation
- 30%+ of conversations have > 20 messages (deep engagement)
- < 10% abandoned after 1 message (indicates relevance)

**Data Source**: `{project}_conversation` and `{project}_messages` tables

**Insights**:
- Short conversations → Users getting quick answers (good)
- Long conversations → Complex problem-solving (good)
- Many 1-message conversations → Poor initial responses (bad)

### Project Activity

**Definition**: Number of active projects with recent activity

**Measurement**:
- Projects with messages in last 7 days
- Projects with new conversations in last 30 days
- Project churn rate (inactive > 90 days)

**Targets**:
- 80%+ of projects active in last 30 days
- < 10% project churn rate
- Average 3+ active users per project

**Data Source**: `projects` table + message timestamps

**Insights**:
- High churn → Projects not finding value
- Low activity → Need better onboarding or features
- Growing active projects → Successful adoption

---

## System Performance Metrics

### Response Time

**Definition**: Time from user message submission to first token received

**Measurement**:
- P50 (median) response time
- P95 response time
- P99 response time

**Targets**:
- P50 < 1 second
- P95 < 2 seconds
- P99 < 5 seconds

**Data Source**: Prometheus metrics, application logs

**Metric Name**: `frontier_response_time_seconds`

**Insights**:
- High P95/P99 → Agent API latency or network issues
- Increasing trend → Scaling issues or degraded agent performance
- Spikes → Investigate specific agent or time period

### Streaming Performance

**Definition**: Token delivery rate during streaming responses

**Measurement**:
- Tokens per second
- Time to complete response
- Streaming interruptions/errors

**Targets**:
- 20+ tokens per second
- < 1% streaming errors
- Smooth, consistent token delivery

**Data Source**: Application logs, frontend telemetry

**Insights**:
- Low tokens/sec → Agent API throttling or network issues
- High error rate → Connection stability problems
- Inconsistent delivery → Buffering or processing delays

### System Uptime

**Definition**: Percentage of time the platform is available and functional

**Measurement**:
- HTTP 200 response rate on `/health` endpoint
- Successful authentication rate
- Database connection success rate

**Targets**:
- 99.9% uptime (< 43 minutes downtime per month)
- 99.99% authentication success rate
- 100% database connection success rate

**Data Source**: Prometheus, external monitoring (Pingdom, UptimeRobot)

**Metric Name**: `frontier_uptime_seconds`

**Insights**:
- Downtime patterns → Identify maintenance windows or recurring issues
- Authentication failures → LDAP connectivity or JWT issues
- Database failures → Connection pool exhaustion or DB issues

### Error Rate

**Definition**: Percentage of requests that result in errors

**Measurement**:
- HTTP 5xx error rate
- HTTP 4xx error rate (excluding 401/403)
- Agent connection failures

**Targets**:
- < 0.1% 5xx error rate
- < 1% 4xx error rate (excluding auth)
- < 2% agent connection failures

**Data Source**: Prometheus metrics, application logs

**Metric Name**: `frontier_errors_total`

**Insights**:
- High 5xx rate → Application bugs or infrastructure issues
- High 4xx rate → Client errors or API misuse
- Agent failures → External API issues or configuration problems

---

## Business Impact Metrics

### Project Creation Rate

**Definition**: Number of new projects created over time

**Measurement**:
- Projects created per week
- Projects created per user
- Time to first project creation (new users)

**Targets**:
- 5+ new projects per week (for 100-user org)
- 50%+ of users create at least one project
- < 1 day from signup to first project

**Data Source**: `projects` table

**Insights**:
- Increasing rate → Growing adoption
- Low rate → Barriers to project creation or unclear value
- High rate but low activity → Projects not finding value

### Agent Adoption

**Definition**: Usage of different agent types and configurations

**Measurement**:
- Number of configured agents per project
- Distribution of agent types (LangGraph, OpenAI, HTTP)
- Agent switching frequency

**Targets**:
- Average 2+ agents per project
- Balanced distribution across agent types
- 30%+ of users try multiple agents

**Data Source**: `agents` table, message metadata

**Insights**:
- Single agent dominance → Other connectors not meeting needs
- Low agent count → Users not aware of flexibility
- High switching → Users comparing models (good)

### Token Usage & Costs

**Definition**: Total tokens consumed and estimated costs

**Measurement**:
- Total tokens per project per month
- Cost per user per month (estimated)
- Token usage growth rate

**Targets**:
- Predictable, linear growth with user count
- Cost per user < $10/month (for typical usage)
- 80%+ of tokens from active conversations (not abandoned)

**Data Source**: `{project}_messages` metadata, agent API responses

**Metric Name**: `frontier_tokens_total`

**Insights**:
- Exponential growth → Investigate heavy users or inefficient prompts
- High cost per user → Need usage limits or optimization
- Low token usage → Users not engaging deeply

### Team Collaboration

**Definition**: Multi-user activity within projects

**Measurement**:
- Average team size per project
- Percentage of projects with 3+ active users
- Conversation sharing/handoff rate

**Targets**:
- Average 5+ users per project
- 60%+ of projects have 3+ active users
- Growing team sizes over time

**Data Source**: `project_members` table, message activity

**Insights**:
- Small teams → Individual use cases, not team collaboration
- Large teams → True team adoption
- Growing teams → Viral adoption within organizations

---

## Measurement Framework

### Data Collection

**Prometheus Metrics** (`/metrics` endpoint):
```
# User engagement
frontier_active_users{period="daily"} 45
frontier_messages_total{project="product_roadmap"} 1234

# System performance
frontier_response_time_seconds{quantile="0.95"} 1.8
frontier_errors_total{type="agent_connection"} 12

# Business metrics
frontier_projects_total 23
frontier_tokens_total{project="code_review"} 456789
```

**Database Queries**:
- Scheduled queries for engagement metrics
- Real-time queries for dashboards
- Historical analysis for trends

**Application Logs**:
- Structured logging (JSON format)
- Error tracking and alerting
- Performance profiling

### Dashboards

**Admin Dashboard** (for Platform Admins):
- System health overview
- Active users and projects
- Error rates and uptime
- Resource utilization

**Project Dashboard** (for Project Admins):
- Project-specific metrics
- Team activity and engagement
- Token usage and costs
- Agent performance comparison

**Executive Dashboard** (for Leadership):
- High-level KPIs
- Growth trends
- Cost analysis
- Adoption metrics

### Alerting

**Critical Alerts** (immediate response):
- System downtime > 5 minutes
- Error rate > 5%
- Database connection failures

**Warning Alerts** (investigate within 24h):
- Response time P95 > 3 seconds
- Error rate > 1%
- Disk space < 20%

**Informational Alerts** (weekly review):
- Unusual usage patterns
- Project churn
- Token usage spikes

---

## Success Criteria by Persona

### End Users
- ✅ Response time < 2 seconds (P95)
- ✅ 90%+ user satisfaction (surveys)
- ✅ 10+ messages per user per day
- ✅ 70%+ retention after 30 days

### Project Admins
- ✅ Project setup time < 5 minutes
- ✅ Real-time usage visibility
- ✅ Zero unauthorized access incidents
- ✅ 80%+ team adoption within project

### Platform Admins
- ✅ 99.9% uptime
- ✅ < 0.1% error rate
- ✅ All metrics exposed via Prometheus
- ✅ < 30 minute deployment time

### Developers
- ✅ Connector implementation < 2 days
- ✅ 100% API documentation coverage
- ✅ Zero breaking changes without migration guide
- ✅ Active community contributions

---

## Quarterly Goals (Example)

### Q1 2026
- **Adoption**: 50 active projects, 200 active users
- **Engagement**: 15 messages per user per day
- **Performance**: P95 response time < 2s
- **Reliability**: 99.9% uptime

### Q2 2026
- **Adoption**: 100 active projects, 500 active users
- **Engagement**: 20 messages per user per day
- **Performance**: P95 response time < 1.5s
- **Reliability**: 99.95% uptime

### Q3 2026
- **Adoption**: 200 active projects, 1000 active users
- **Engagement**: 25 messages per user per day
- **Performance**: P95 response time < 1s
- **Reliability**: 99.99% uptime

---

## Metric Review Cadence

| Frequency | Metrics | Audience | Action |
|-----------|---------|----------|--------|
| **Real-time** | System health, errors | Platform Admins | Incident response |
| **Daily** | Active users, messages | Product Team | Identify anomalies |
| **Weekly** | Engagement, performance | Product + Eng | Sprint planning |
| **Monthly** | Business metrics, costs | Leadership | Strategic decisions |
| **Quarterly** | Growth, retention, goals | All stakeholders | OKR review |

---

**Next**: [Roadmap](08-roadmap.md) - Current state and future enhancements
