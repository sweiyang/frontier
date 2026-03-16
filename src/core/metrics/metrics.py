"""Prometheus metrics collection and formatting for Frontier."""

from typing import Dict, List, Optional
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.core import CollectorRegistry, REGISTRY


# Create a custom registry for Frontier metrics
registry = CollectorRegistry()

# Define Prometheus metrics
messages_total = Counter(
    'conduit_messages_total',
    'Total number of messages',
    ['project', 'agent', 'role'],
    registry=registry
)

tokens_total = Counter(
    'conduit_tokens_total',
    'Total number of tokens used',
    ['project', 'agent', 'role'],
    registry=registry
)

users_total = Gauge(
    'conduit_users_total',
    'Total unique users',
    ['project', 'agent'],
    registry=registry
)

active_users = Gauge(
    'conduit_active_users',
    'Active users in last 7 days',
    ['project', 'agent'],
    registry=registry
)

conversations_total = Gauge(
    'conduit_conversations_total',
    'Total conversations',
    ['project'],
    registry=registry
)

agents_total = Gauge(
    'conduit_agents_total',
    'Total agents configured',
    ['project'],
    registry=registry
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
    lines.append("# HELP conduit_messages_total Total number of messages")
    lines.append("# TYPE conduit_messages_total counter")
    lines.append("")
    lines.append("# HELP conduit_tokens_total Total number of tokens used")
    lines.append("# TYPE conduit_tokens_total counter")
    lines.append("")
    lines.append("# HELP conduit_users_total Total unique users")
    lines.append("# TYPE conduit_users_total gauge")
    lines.append("")
    lines.append("# HELP conduit_active_users Active users in last 7 days")
    lines.append("# TYPE conduit_active_users gauge")
    lines.append("")
    lines.append("# HELP conduit_conversations_total Total conversations")
    lines.append("# TYPE conduit_conversations_total gauge")
    lines.append("")
    lines.append("# HELP conduit_agents_total Total agents configured")
    lines.append("# TYPE conduit_agents_total gauge")
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
            
            # All messages from agents are assistant messages
            assistant_messages += message_count
            assistant_tokens += total_tokens
            
            # Add agent-specific metrics
            lines.append(f'conduit_messages_total{{project="{project_name_escaped}",agent="{agent_name_escaped}",role="assistant"}} {message_count}')
            lines.append(f'conduit_tokens_total{{project="{project_name_escaped}",agent="{agent_name_escaped}",role="assistant"}} {total_tokens}')
            lines.append(f'conduit_users_total{{project="{project_name_escaped}",agent="{agent_name_escaped}"}} {total_users}')
            lines.append(f'conduit_active_users{{project="{project_name_escaped}",agent="{agent_name_escaped}"}} {active_users_count}')
        
        # Get user messages (no agent specified)
        total_messages = project_data.get("total_messages", 0)
        total_tokens = project_data.get("total_tokens", 0)
        user_messages = total_messages - assistant_messages
        user_tokens = total_tokens - assistant_tokens
        
        # Add user message metrics (aggregated across all agents)
        if user_messages > 0:
            lines.append(f'conduit_messages_total{{project="{project_name_escaped}",agent="unknown",role="user"}} {user_messages}')
            lines.append(f'conduit_tokens_total{{project="{project_name_escaped}",agent="unknown",role="user"}} {user_tokens}')
        
        # Add project-level metrics
        total_conversations = project_data.get("total_conversations", 0)
        total_agents = project_data.get("total_agents", 0)
        
        lines.append(f'conduit_conversations_total{{project="{project_name_escaped}"}} {total_conversations}')
        lines.append(f'conduit_agents_total{{project="{project_name_escaped}"}} {total_agents}')
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


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST

