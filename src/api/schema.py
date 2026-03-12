"""API request and response schemas using Pydantic models."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class FileAttachment(BaseModel):
    """File attachment for chat messages."""
    filename: str
    content_type: str
    data: str  # Base64 encoded


class ChatRequest(BaseModel):
    """Chat message request payload."""
    message: str
    conversation_id: int
    agent_id: Optional[int] = None
    model: str = "default"  # Deprecated
    files: Optional[List[FileAttachment]] = None
    client_context: Optional[Dict[str, Any]] = None


class LoginRequest(BaseModel):
    """User login credentials."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response after successful login."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    display_name: Optional[str] = None


class ConversationCreate(BaseModel):
    """Request to create a new conversation."""
    title: Optional[str] = None


class ProjectCreate(BaseModel):
    """Request to create a new project."""
    project_name: str
    disable_authentication: bool = False
    disable_message_storage: bool = False


class ProjectUpdate(BaseModel):
    """Request to update project settings."""
    project_name: Optional[str] = None
    disable_authentication: Optional[bool] = None
    disable_message_storage: Optional[bool] = None


class ConversationResponse(BaseModel):
    """Conversation details response."""
    id: int
    title: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Chat message response."""
    id: int
    role: str
    content: str
    model: Optional[str]
    token_count: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


class AgentCreate(BaseModel):
    """Request to create a new agent."""
    name: str
    endpoint: str
    connection_type: str
    is_default: bool = False
    extras: Optional[Dict[str, Any]] = None
    auth: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None


class AgentUpdate(BaseModel):
    """Request to update an agent."""
    name: Optional[str] = None
    endpoint: Optional[str] = None
    connection_type: Optional[str] = None
    is_default: Optional[bool] = None
    extras: Optional[Dict[str, Any]] = None
    auth: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None


class AgentResponse(BaseModel):
    """Agent configuration response."""
    id: int
    project_id: int
    name: str
    endpoint: str
    connection_type: str
    is_default: bool
    extras: Optional[Dict[str, Any]]
    auth: Optional[Dict[str, Any]]
    icon: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class LangGraphAssistantsRequest(BaseModel):
    """Request to list LangGraph assistants."""
    endpoint: str
    graph_id: Optional[str] = None
    auth: Optional[Dict[str, Any]] = None


class OpenAIModelsRequest(BaseModel):
    """Request to list OpenAI models."""
    endpoint: str
    auth: Optional[Dict[str, Any]] = None


class ADGroupCreate(BaseModel):
    """Request to add an AD group to a project."""
    group_dn: str
    group_name: str
    role: str = "member"
    agent_ids: Optional[List[int]] = None


class ADGroupUpdate(BaseModel):
    """Request to update AD group settings."""
    role: Optional[str] = None
    agent_ids: Optional[List[int]] = None


class ADGroupResponse(BaseModel):
    """AD group membership response."""
    id: int
    project_id: int
    group_dn: str
    group_name: str
    role: str
    added_at: str
    agent_ids: List[int] = []

    class Config:
        from_attributes = True


class MemberCreate(BaseModel):
    """Request to add a member to a project."""
    username: str
    role: str = "member"
    agent_ids: Optional[List[int]] = None


class MemberUpdate(BaseModel):
    """Request to update member settings."""
    role: Optional[str] = None
    agent_ids: Optional[List[int]] = None


class MemberResponse(BaseModel):
    """Project member response."""
    user_id: int
    username: str
    role: str
    is_owner: bool = False
    joined_at: Optional[str] = None
    agent_ids: List[int] = []

    class Config:
        from_attributes = True


class LDAPSearchResult(BaseModel):
    """Single LDAP search result."""
    dn: str
    name: str
    type: str


class LDAPSearchResponse(BaseModel):
    """LDAP search results response."""
    results: List[LDAPSearchResult]


# --- Approval Workflow Schemas ---

class ApproverCreate(BaseModel):
    """Request to add an approver to a project."""
    username: str


class ApproverResponse(BaseModel):
    """Project approver response."""
    id: int
    project_id: int
    user_id: int
    username: str
    added_by: int
    created_at: str

    class Config:
        from_attributes = True


class ApprovalSettingsUpdate(BaseModel):
    """Request to update approval settings."""
    approval_type: str  # "any", "all", or "majority"


class ApprovalSettingsResponse(BaseModel):
    """Project approval settings response."""
    id: Optional[int] = None
    project_id: int
    approval_type: str
    approval_required: bool = False
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class ApprovalActionCreate(BaseModel):
    """Request to approve or reject a change request."""
    comment: Optional[str] = None


class ApprovalActionResponse(BaseModel):
    """Individual approval action response."""
    id: int
    user_id: int
    username: str
    action: str  # "approve" or "reject"
    comment: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class ChangeRequestResponse(BaseModel):
    """Change request response."""
    id: int
    project_id: int
    agent_id: Optional[int] = None
    request_type: str  # "create", "update", "delete"
    requested_by: int
    payload: Dict[str, Any]
    status: str  # "pending", "approved", "rejected"
    approval_type: str
    required_approvals: int
    current_approvals: int
    approvals: List[ApprovalActionResponse] = []
    created_at: str
    resolved_at: Optional[str] = None

    class Config:
        from_attributes = True


class AgentVersionResponse(BaseModel):
    """Agent version history response."""
    id: int
    agent_id: int
    version_number: int
    snapshot: Dict[str, Any]
    created_by: int
    change_request_id: Optional[int] = None
    created_at: str

    class Config:
        from_attributes = True
