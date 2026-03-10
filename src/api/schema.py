from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class FileAttachment(BaseModel):
    filename: str
    content_type: str
    data: str  # Base64 encoded file content


class ChatRequest(BaseModel):
    message: str
    conversation_id: int
    agent_id: Optional[int] = None  # Optional: Specific agent ID to use
    model: str = "default"  # Deprecated: kept for backward compatibility
    files: Optional[List[FileAttachment]] = None
    client_context: Optional[Dict[str, Any]] = None  # Frontend state (e.g. dynamic panel values)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


class ConversationCreate(BaseModel):
    title: Optional[str] = None


class ProjectCreate(BaseModel):
    project_name: str
    disable_authentication: bool = False
    disable_message_storage: bool = False


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    disable_authentication: Optional[bool] = None
    disable_message_storage: Optional[bool] = None


class ConversationResponse(BaseModel):
    id: int
    title: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    model: Optional[str]
    token_count: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


# Agent schemas

class AgentCreate(BaseModel):
    name: str
    endpoint: str
    connection_type: str  # "http", "websocket", "grpc"
    is_default: bool = False
    extras: Optional[Dict[str, Any]] = None
    auth: Optional[Dict[str, Any]] = None  # {"auth_type": "bearer|basic|api_key", "credentials": str|{username, password}}
    icon: Optional[str] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    endpoint: Optional[str] = None
    connection_type: Optional[str] = None
    is_default: Optional[bool] = None
    extras: Optional[Dict[str, Any]] = None
    auth: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None


class AgentResponse(BaseModel):
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
    endpoint: str
    graph_id: Optional[str] = None
    auth: Optional[Dict[str, Any]] = None


class OpenAIModelsRequest(BaseModel):
    endpoint: str
    auth: Optional[Dict[str, Any]] = None


# AD Group schemas

class ADGroupCreate(BaseModel):
    group_dn: str
    group_name: str
    role: str = "member"  # "member" or "admin"
    agent_ids: Optional[List[int]] = None  # Agents this group can access


class ADGroupUpdate(BaseModel):
    role: Optional[str] = None
    agent_ids: Optional[List[int]] = None  # Agents this group can access


class ADGroupResponse(BaseModel):
    id: int
    project_id: int
    group_dn: str
    group_name: str
    role: str
    added_at: str
    agent_ids: List[int] = []

    class Config:
        from_attributes = True


# Project Member (LAN ID) schemas

class MemberCreate(BaseModel):
    username: str  # LAN ID / username
    role: str = "member"  # "member" or "admin"
    agent_ids: Optional[List[int]] = None  # Agents this member can access


class MemberUpdate(BaseModel):
    role: Optional[str] = None
    agent_ids: Optional[List[int]] = None  # Agents this member can access


class MemberResponse(BaseModel):
    user_id: int
    username: str
    role: str
    is_owner: bool = False
    joined_at: Optional[str] = None
    agent_ids: List[int] = []

    class Config:
        from_attributes = True


# LDAP Search schemas

class LDAPSearchResult(BaseModel):
    dn: str
    name: str
    type: str  # "user" or "group"


class LDAPSearchResponse(BaseModel):
    results: List[LDAPSearchResult]
