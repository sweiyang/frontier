"""Prometheus metrics collection and formatting for Frontier."""

from typing import Dict, List

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge
from prometheus_client.core import CollectorRegistry

# Create a custom registry for Frontier metrics
registry = CollectorRegistry()

# Define Prometheus metrics
messages_total = Counter(
    "frontier_messages_total",
    "Total number of messages",
    ["project", "agent", "role"],
    registry=registry,
)

tokens_total = Counter(
    "frontier_tokens_total",
    "Total number of tokens used",
    ["project", "agent", "role"],
    registry=registry,
)

users_total = Gauge(
    "frontier_users_total",
    "Total unique users",
    ["project", "agent"],
    registry=registry,
)

active_users = Gauge(
    "frontier_active_users",
    "Active users in last 7 days",
    ["project", "agent"],
    registry=registry,
)

conversations_total = Gauge(
    "frontier_conversations_total",
    "Total conversations",
    ["project"],
    registry=registry,
)

agents_total = Gauge(
    "frontier_agents_total", "Total agents configured", ["project"], registry=registry
)

interactions_total = Gauge(
    "frontier_interactions_total",
    "Total interactions (1 user message + 1 assistant response)",
    ["project", "agent"],
    registry=registry,
)


def format_metrics_from_usage_data(all_projects_usage: List[Dict]) -> str:
    """
    Format usage data into Prometheus metrics format.

    Args:
        all_projects_usage: List of project usage dictionaries with structure:
            {
                "project_name": "...",
                "total_messages": 100,
                "total_tokens": 5000,
                "by_agent": {
                    "agent-name": {
                        "message_count": 50,
                        "total_tokens": 2500,
                        "total_users": 5,
                        "active_users": 3
                    }
                },
                "total_conversations": 25,
                "total_agents": 3
            }

    Returns:
        Prometheus-formatted metrics string
    """
    # Reset all metrics to zero first (since we're calculating from scratch)
    # Note: Counters can't be reset, so we'll use labels to track current state
    # For Gauges, we'll set the values directly

    lines = []

    # Add HELP and TYPE declarations
    lines.append("# HELP frontier_messages_total Total number of messages")
    lines.append("# TYPE frontier_messages_total counter")
    lines.append("")
    lines.append("# HELP frontier_tokens_total Total number of tokens used")
    lines.append("# TYPE frontier_tokens_total counter")
    lines.append("")
    lines.append("# HELP frontier_users_total Total unique users")
    lines.append("# TYPE frontier_users_total gauge")
    lines.append("")
    lines.append("# HELP frontier_active_users Active users in last 7 days")
    lines.append("# TYPE frontier_active_users gauge")
    lines.append("")
    lines.append("# HELP frontier_conversations_total Total conversations")
    lines.append("# TYPE frontier_conversations_total gauge")
    lines.append("")
    lines.append("# HELP frontier_agents_total Total agents configured")
    lines.append("# TYPE frontier_agents_total gauge")
    lines.append("")
    lines.append(
        "# HELP frontier_interactions_total Total interactions (1 user message + 1 assistant response)"
    )
    lines.append("# TYPE frontier_interactions_total gauge")
    lines.append("")
    lines.append("# HELP frontier_site_page_views_total Total site page views")
    lines.append("# TYPE frontier_site_page_views_total gauge")
    lines.append("")
    lines.append("# HELP frontier_site_unique_users Unique site visitors")
    lines.append("# TYPE frontier_site_unique_users gauge")
    lines.append("")
    lines.append(
        "# HELP frontier_site_interactions_total Total site interactions by type"
    )
    lines.append("# TYPE frontier_site_interactions_total gauge")
    lines.append("")

    # Process each project
    for project_data in all_projects_usage:
        project_name = project_data.get("project_name", "unknown")
        project_name_escaped = _escape_label_value(project_name)

        # Get message counts by role and agent
        by_agent = project_data.get("by_agent", {})

        # Track messages and tokens by role
        user_messages = 0
        user_tokens = 0
        assistant_messages = 0
        assistant_tokens = 0

        # Process each agent
        for agent_name, agent_stats in by_agent.items():
            agent_name_escaped = _escape_label_value(agent_name)
            message_count = agent_stats.get("message_count", 0)
            total_tokens = agent_stats.get("total_tokens", 0)
            total_users = agent_stats.get("total_users", 0)
            active_users_count = agent_stats.get("active_users", 0)
            interactions_count = agent_stats.get("interactions", 0)

            # All messages from agents are assistant messages
            assistant_messages += message_count
            assistant_tokens += total_tokens

            # Add agent-specific metrics
            lines.append(
                f'frontier_messages_total{{project="{project_name_escaped}",agent="{agent_name_escaped}",role="assistant"}} {message_count}'
            )
            lines.append(
                f'frontier_tokens_total{{project="{project_name_escaped}",agent="{agent_name_escaped}",role="assistant"}} {total_tokens}'
            )
            lines.append(
                f'frontier_users_total{{project="{project_name_escaped}",agent="{agent_name_escaped}"}} {total_users}'
            )
            lines.append(
                f'frontier_active_users{{project="{project_name_escaped}",agent="{agent_name_escaped}"}} {active_users_count}'
            )
            lines.append(
                f'frontier_interactions_total{{project="{project_name_escaped}",agent="{agent_name_escaped}"}} {interactions_count}'
            )

        # Get user messages (no agent specified)
        total_messages = project_data.get("total_messages", 0)
        total_tokens = project_data.get("total_tokens", 0)
        user_messages = total_messages - assistant_messages
        user_tokens = total_tokens - assistant_tokens

        # Add user message metrics (aggregated across all agents)
        if user_messages > 0:
            lines.append(
                f'frontier_messages_total{{project="{project_name_escaped}",agent="unknown",role="user"}} {user_messages}'
            )
            lines.append(
                f'frontier_tokens_total{{project="{project_name_escaped}",agent="unknown",role="user"}} {user_tokens}'
            )

        # Add project-level metrics
        total_conversations = project_data.get("total_conversations", 0)
        total_agents = project_data.get("total_agents", 0)

        lines.append(
            f'frontier_conversations_total{{project="{project_name_escaped}"}} {total_conversations}'
        )
        lines.append(
            f'frontier_agents_total{{project="{project_name_escaped}"}} {total_agents}'
        )

        # Site analytics metrics
        site_analytics = project_data.get("site_analytics")
        if site_analytics:
            summary = site_analytics.get("summary", {})
            lines.append(
                f'frontier_site_page_views_total{{project="{project_name_escaped}"}} {summary.get("page_views", 0)}'
            )
            lines.append(
                f'frontier_site_unique_users{{project="{project_name_escaped}"}} {summary.get("unique_users", 0)}'
            )
            for interaction_type, count in site_analytics.get("by_type", {}).items():
                type_escaped = _escape_label_value(interaction_type)
                lines.append(
                    f'frontier_site_interactions_total{{project="{project_name_escaped}",type="{type_escaped}"}} {count}'
                )

        lines.append("")

    return "\n".join(lines)


def _escape_label_value(value: str) -> str:
    """
    Escape label values for Prometheus format.

    Prometheus label values must escape:
    - Backslashes as \\
    - Double quotes as \"
    - Newlines as \n
    """
    if not isinstance(value, str):
        value = str(value)
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def format_monthly_metrics(monthly_usage: Dict) -> str:
    """
    Format monthly usage data into Prometheus metrics format.
    Limits output to last 12 months to avoid unbounded cardinality.
    """
    lines = []

    lines.append("# HELP frontier_monthly_interactions Total interactions per month")
    lines.append("# TYPE frontier_monthly_interactions gauge")
    lines.append("")
    lines.append("# HELP frontier_monthly_unique_users Unique users per month")
    lines.append("# TYPE frontier_monthly_unique_users gauge")
    lines.append("")
    lines.append("# HELP frontier_monthly_active_projects Active projects per month")
    lines.append("# TYPE frontier_monthly_active_projects gauge")
    lines.append("")

    months = monthly_usage.get("months", [])[:12]
    for entry in months:
        month = _escape_label_value(entry.get("month", "unknown"))
        interactions = entry.get("interactions", 0)
        unique_users = entry.get("unique_users", 0)
        active_projects = entry.get("active_projects", 0)

        lines.append(f'frontier_monthly_interactions{{month="{month}"}} {interactions}')
        lines.append(f'frontier_monthly_unique_users{{month="{month}"}} {unique_users}')
        lines.append(
            f'frontier_monthly_active_projects{{month="{month}"}} {active_projects}'
        )

    lines.append("")
    return "\n".join(lines)


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST
