"""API request and response schemas using Pydantic models."""

import base64
import re
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

# 10 MB limit for file attachments (in bytes)
_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


class FileAttachment(BaseModel):
    """File attachment for chat messages."""

    filename: str
    content_type: str
    data: str  # Base64 encoded

    @field_validator("data")
    @classmethod
    def validate_base64_data(cls, v: str) -> str:
        """Validate that data is valid base64 and does not exceed 10 MB decoded."""
        try:
            decoded = base64.b64decode(v, validate=True)
        except Exception:
            raise ValueError("File data must be valid base64-encoded content.")
        if len(decoded) > _MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size exceeds the 10 MB limit (decoded size: {len(decoded)} bytes).")
        return v


class ChatRequest(BaseModel):
    """Chat message request payload."""

    message: str = Field(..., max_length=32000)
    conversation_id: int
    agent_id: Optional[int] = None
    model: str = "default"  # Deprecated
    files: Optional[List[FileAttachment]] = None
    client_context: Optional[Dict[str, Any]] = None
    is_system: bool = False


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
    agent_id: Optional[int] = None


def _validate_project_name(name: str) -> str:
    """Validate a project name is URL-safe."""
    name = name.strip().lower()
    if not name:
        raise ValueError("Project name cannot be empty.")
    if len(name) > 63:
        raise ValueError("Project name cannot exceed 63 characters.")
    if name[0] in ("-", "_"):
        raise ValueError("Project name cannot start with a hyphen or underscore.")
    if not re.fullmatch(r"[a-z0-9_-]+", name):
        raise ValueError("Project name can only contain lowercase letters, numbers, hyphens, and underscores.")
    return name


class ProjectCreate(BaseModel):
    """Request to create a new project."""

    project_name: str
    disable_authentication: bool = False
    disable_message_storage: bool = True

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        """Validate the project name format."""
        return _validate_project_name(v)


class ProjectUpdate(BaseModel):
    """Request to update project settings."""

    project_name: Optional[str] = None
    disable_authentication: Optional[bool] = None
    disable_message_storage: Optional[bool] = None
    description: Optional[str] = None
    default_view: Optional[str] = None
    view_locked: Optional[bool] = None
    logo: Optional[str] = None

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate the project name format if provided."""
        if v is None:
            return v
        return _validate_project_name(v)


class ConversationResponse(BaseModel):
    """Conversation details response."""

    id: int
    title: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        """Pydantic model configuration."""

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
        """Pydantic model configuration."""

        from_attributes = True


def _validate_agent_endpoint(v: Optional[str]) -> Optional[str]:
    """Validate that the endpoint is a valid http/https URL when provided."""
    if not v:
        return v
    v = v.strip()
    if not v:
        return v
    if not re.match(r"^https?://", v):
        raise ValueError("Endpoint must be a valid URL starting with http:// or https://.")
    return v


class AgentCreate(BaseModel):
    """Request to create a new agent."""

    name: str
    endpoint: str
    connection_type: Literal["http", "langgraph", "openai"]
    is_default: bool = False
    extras: Optional[Dict[str, Any]] = None
    auth: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None
    is_artefact: bool = False
    description: Optional[str] = None
    approval_required: bool = False

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        """Validate the agent endpoint URL."""
        result = _validate_agent_endpoint(v)
        return result if result is not None else v


class AgentUpdate(BaseModel):
    """Request to update an agent."""

    name: Optional[str] = None
    endpoint: Optional[str] = None
    connection_type: Optional[Literal["http", "langgraph", "openai"]] = None
    is_default: Optional[bool] = None
    extras: Optional[Dict[str, Any]] = None
    auth: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None
    is_artefact: Optional[bool] = None
    description: Optional[str] = None
    approval_required: Optional[bool] = None

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, v: Optional[str]) -> Optional[str]:
        """Validate the agent endpoint URL if provided."""
        return _validate_agent_endpoint(v)


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
    is_artefact: bool = False
    approval_required: bool = False
    created_at: str
    updated_at: str

    class Config:
        """Pydantic model configuration."""

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


ALLOWED_ROLES = {"member", "admin", "developer"}


def _validate_role(role: str) -> str:
    """Validate that a role is one of the allowed values."""
    if role not in ALLOWED_ROLES:
        raise ValueError(f"Role must be one of: {', '.join(sorted(ALLOWED_ROLES))}")
    return role


class ADGroupCreate(BaseModel):
    """Request to add an AD group to a project."""

    group_dn: str
    group_name: str
    role: str = "member"
    agent_ids: Optional[List[int]] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate the role value."""
        return _validate_role(v)

    @field_validator("group_dn")
    @classmethod
    def validate_group_dn(cls, v: str) -> str:
        """Validate that group_dn looks like a basic LDAP distinguished name."""
        v = v.strip()
        if not re.match(r"^[A-Za-z]+=.+,.+$", v):
            raise ValueError(
                "group_dn must be a valid LDAP distinguished name " "(e.g. 'CN=my-group,OU=Groups,DC=example,DC=com')."
            )
        return v


class ADGroupUpdate(BaseModel):
    """Request to update AD group settings."""

    role: Optional[str] = None
    agent_ids: Optional[List[int]] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        """Validate the role value if provided."""
        if v is None:
            return v
        return _validate_role(v)


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
        """Pydantic model configuration."""

        from_attributes = True


class MemberCreate(BaseModel):
    """Request to add a member to a project."""

    username: str
    role: str = "member"
    agent_ids: Optional[List[int]] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate the role value."""
        return _validate_role(v)


class MemberUpdate(BaseModel):
    """Request to update member settings."""

    role: Optional[str] = None
    agent_ids: Optional[List[int]] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        """Validate the role value if provided."""
        if v is None:
            return v
        return _validate_role(v)


class MemberResponse(BaseModel):
    """Project member response."""

    user_id: int
    username: str
    role: str
    is_owner: bool = False
    joined_at: Optional[str] = None
    agent_ids: List[int] = []

    class Config:
        """Pydantic model configuration."""

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
        """Pydantic model configuration."""

        from_attributes = True


class ApprovalSettingsUpdate(BaseModel):
    """Request to update approval settings."""

    approval_type: Literal["any", "all", "majority"]


class ApprovalSettingsResponse(BaseModel):
    """Project approval settings response."""

    id: Optional[int] = None
    project_id: int
    approval_type: str
    approval_required: bool = False
    updated_at: Optional[str] = None

    class Config:
        """Pydantic model configuration."""

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
        """Pydantic model configuration."""

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
        """Pydantic model configuration."""

        from_attributes = True


# --- Site / Dashboard Schemas (Site Builder) ---


class SiteComponent(BaseModel):
    """A single component on a site page (canvas positioning in pixels, 8px grid)."""

    id: str
    type: str  # "button", "form", "chat_window", "text"
    x: int = 0
    y: int = 0
    w: int = 160
    h: int = 44
    fullscreen: bool = False
    props: Dict[str, Any] = {}


class SitePage(BaseModel):
    """A page in a site with an ordered list of components."""

    pageId: str
    title: str
    path: str = "/"
    components: List[SiteComponent] = []


class SiteUpdate(BaseModel):
    """
    Site document for the visual site builder.
    Stored as the project's site (one site per project).
    """

    siteId: Optional[str] = None
    name: str = ""
    theme: str = "default"
    subdomain_slug: Optional[str] = None
    canvasWidth: int = 800
    pages: List[SitePage] = []


class FormSubmitRequest(BaseModel):
    """Form submission from a site builder form component."""

    fields: Dict[str, Any]


# --- Site Analytics Schemas ---


class SiteAnalyticsEventSchema(BaseModel):
    """A single site analytics event."""

    event_type: str  # page_view, button_click, form_submit, table_action
    page_id: Optional[str] = None
    page_path: Optional[str] = None
    component_id: Optional[str] = None
    component_type: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SiteAnalyticsBatch(BaseModel):
    """Batch of site analytics events (max 50)."""

    events: List[SiteAnalyticsEventSchema]

    @field_validator("events")
    @classmethod
    def validate_events_count(cls, v: list) -> list:
        """Validate that no more than 50 events are submitted per batch."""
        if len(v) > 50:
            raise ValueError("Maximum 50 events per batch")
        return v


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
        """Pydantic model configuration."""

        from_attributes = True


# --- Artefacts Schemas ---


class WorkbenchAccessGrantCreate(BaseModel):
    """Request to add a workbench access grant."""

    grant_type: Literal["user", "ad_group"]
    grant_value: str = Field(..., max_length=512)
    display_name: Optional[str] = Field(None, max_length=255)


class ArtefactSettings(BaseModel):
    """Request to configure artefact settings for a project."""

    is_artefact: bool
    artefact_visibility: str = "org"  # 'private', 'org', 'public'


class ArtefactResponse(BaseModel):
    """Artefact agent response."""

    agent_id: int
    agent_name: str
    icon: Optional[str] = None
    project_name: Optional[str] = None
    project_id: Optional[str] = None
    connection_type: str

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


class BannerCreate(BaseModel):
    """Request to create a platform notification banner."""

    message: str = Field(..., max_length=1000)
    tag: str = Field("UPDATE", max_length=50)
    tag_color: str = Field("#ED1C24", max_length=7)
    link_url: Optional[str] = Field(None, max_length=1000)
    is_active: bool = True
    expires_at: Optional[str] = None


class BannerReorder(BaseModel):
    """Request to reorder platform banners."""

    banner_ids: List[int]


class BannerUpdate(BaseModel):
    """Request to update a platform notification banner."""

    message: Optional[str] = Field(None, max_length=1000)
    tag: Optional[str] = Field(None, max_length=50)
    tag_color: Optional[str] = Field(None, max_length=7)
    link_url: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    expires_at: Optional[str] = None
