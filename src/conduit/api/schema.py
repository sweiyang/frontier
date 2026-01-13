from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: int
    model: str = "default"


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


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    endpoint: Optional[str] = None
    connection_type: Optional[str] = None
    is_default: Optional[bool] = None
    extras: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    id: int
    project_id: int
    name: str
    endpoint: str
    connection_type: str
    is_default: bool
    extras: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# AD Group schemas

class ADGroupCreate(BaseModel):
    group_dn: str
    group_name: str
    role: str = "member"  # "member" or "admin"


class ADGroupUpdate(BaseModel):
    role: str


class ADGroupResponse(BaseModel):
    id: int
    project_id: int
    group_dn: str
    group_name: str
    role: str
    added_at: str

    class Config:
        from_attributes = True


# LDAP Search schemas

class LDAPSearchResult(BaseModel):
    dn: str
    name: str
    type: str  # "user" or "group"


class LDAPSearchResponse(BaseModel):
    results: List[LDAPSearchResult]
