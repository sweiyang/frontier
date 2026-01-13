import mimetypes
import asyncio
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from conduit.core.frontend.frontend import Frontend
from conduit.core.auth.auth import LDAPAuthService
from conduit.core.auth.jwt import create_access_token, get_current_user, CurrentUser
from conduit.core.db import db_chat, db_project
from conduit.api.schema import (
    ChatRequest,
    LoginRequest,
    ConversationCreate,
    ConversationResponse,
    MessageResponse,
    ProjectCreate,
    TokenResponse,
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    ADGroupCreate,
    ADGroupUpdate,
    ADGroupResponse,
    LDAPSearchResult,
    LDAPSearchResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize resources on startup."""
    # Startup: Initialize database and create tables
    db_chat.get_db()
    print("Database initialized")
    yield
    # Shutdown: cleanup if needed
    print("Shutting down")


app = FastAPI(lifespan=lifespan)

# LDAP Configuration - override with environment variables
LDAP_SERVER = os.getenv("LDAP_SERVER", "ldap://localhost:1389")
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "dc=example,dc=com")
LDAP_USE_SSL = os.getenv("LDAP_USE_SSL", "false").lower() == "true"

ldap_auth = LDAPAuthService(LDAP_SERVER, LDAP_BASE_DN, LDAP_USE_SSL)


def get_project_from_header(x_project: Optional[str] = Header(None)) -> Optional[str]:
    """Extract project name from X-Project header."""
    return x_project


# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user via LDAP and return JWT token."""
    try:
        success = ldap_auth.login(request.username, request.password)
        if success:
            # Create or get user in database
            user = db_chat.get_or_create_user(request.username)
            # Generate JWT token
            access_token = create_access_token(username=user.username, user_id=user.id)
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user_id=user.id,
                username=user.username
            )
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/logout")
async def logout(current_user: CurrentUser = Depends(get_current_user)):
    """Logout the current user."""
    ldap_auth.logout()
    return JSONResponse({"success": True, "message": "Logged out"})


@app.get("/me")
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    """Get current authenticated user info. Used to verify token and restore session."""
    return JSONResponse({
        "user_id": current_user.user_id,
        "username": current_user.username
    })


@app.get("/conversations")
async def list_conversations_endpoint(
    current_user: CurrentUser = Depends(get_current_user),
    project: Optional[str] = Depends(get_project_from_header)
):
    """List all conversations for the authenticated user, optionally filtered by project."""
    conversations = db_chat.list_conversations(current_user.username, project=project)
    return JSONResponse({"conversations": conversations, "project": project})


@app.post("/conversations")
async def create_conversation_endpoint(
    request: ConversationCreate,
    current_user: CurrentUser = Depends(get_current_user),
    project: Optional[str] = Depends(get_project_from_header)
):
    """Create a new conversation for the authenticated user within a project."""
    conversation = db_chat.create_conversation(current_user.username, request.title, project=project)
    return JSONResponse(conversation)


@app.get("/conversations/{conversation_id}/messages")
async def get_messages_endpoint(
    conversation_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get all messages for a conversation."""
    messages = db_chat.get_messages(conversation_id)
    return JSONResponse({"messages": messages})


@app.get("/projects/owned")
async def list_owned_projects_endpoint(
    current_user: CurrentUser = Depends(get_current_user)
):
    """List all projects owned by the authenticated user."""
    projects = db_project.list_projects_for_user(current_user.user_id)
    owned_projects = [p for p in projects if p.get("is_owner", False)]
    return JSONResponse({"projects": owned_projects})


@app.post("/projects")
async def create_project_endpoint(
    request: ProjectCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create a new project for the authenticated user."""
    project = db_project.create_project(current_user.user_id, request.project_name)
    return JSONResponse(project)


async def fake_stream_processor(message: str, conversation_id: int, model: str, project: Optional[str] = None):
    """Simulate a streaming response when no agent is configured."""
    project_info = f" [Project: {project}]" if project else ""
    response_text = f"No agent configured.{project_info} Please add an agent in project settings to enable AI chat. "
    
    full_response = ""
    for char in response_text:
        full_response += char
        yield char
        await asyncio.sleep(0.01)
    
    # Save the complete assistant response
    db_chat.save_message(conversation_id, "assistant", full_response, model, len(full_response.split()))


async def agent_stream_processor(
    message: str, 
    conversation_id: int, 
    agent: dict,
    messages_history: list
):
    """Stream response from the actual agent endpoint."""
    import httpx
    
    endpoint = agent["endpoint"]
    agent_name = agent["name"]
    extras = agent.get("extras") or {}
    
    # Build the request payload for the agent
    # Standard format: messages array with role/content
    payload = {
        "messages": messages_history + [{"role": "user", "content": message}],
        **extras  # Include any extra config from the agent
    }
    
    full_response = ""
    
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", endpoint, json=payload) as response:
                if response.status_code != 200:
                    error_msg = f"Agent error: {response.status_code}"
                    yield error_msg
                    db_chat.save_message(conversation_id, "assistant", error_msg, agent_name)
                    return
                
                async for chunk in response.aiter_text():
                    # Handle different streaming formats
                    if chunk:
                        # Check for SSE format (data: ...)
                        if chunk.startswith("data: "):
                            data = chunk[6:].strip()
                            if data and data != "[DONE]":
                                full_response += data
                                yield data
                        else:
                            # Raw text streaming
                            full_response += chunk
                            yield chunk
        
        # Save the complete assistant response
        if full_response:
            db_chat.save_message(
                conversation_id, 
                "assistant", 
                full_response, 
                agent_name, 
                len(full_response.split())
            )
    except httpx.ConnectError:
        error_msg = f"Could not connect to agent '{agent_name}' at {endpoint}"
        yield error_msg
        db_chat.save_message(conversation_id, "assistant", error_msg, agent_name)
    except Exception as e:
        error_msg = f"Error communicating with agent: {str(e)}"
        yield error_msg
        db_chat.save_message(conversation_id, "assistant", error_msg, agent_name)


@app.post("/chat")
async def stream_chat(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    project: Optional[str] = Depends(get_project_from_header)
):
    """Stream chat response for the authenticated user within a project context."""
    # Save user message first
    db_chat.save_message(request.conversation_id, "user", request.message, request.model)
    
    # Get the agent to use
    agent = None
    if project:
        project_data = db_project.get_project_by_name(project)
        if project_data:
            # Try to find the specific agent by model name
            if request.model and request.model != "default":
                agent = db_project.get_agent_by_name(project_data["id"], request.model)
            
            # Fall back to default agent if no specific agent found
            if not agent:
                agent = db_project.get_default_agent_for_project(project_data["id"])
    
    if agent:
        # Get conversation history for context
        messages_history = db_chat.get_messages(request.conversation_id)
        # Convert to simple format for agent
        history = [{"role": m["role"], "content": m["content"]} for m in messages_history[:-1]]  # Exclude the message we just saved
        
        return StreamingResponse(
            agent_stream_processor(request.message, request.conversation_id, agent, history),
            media_type="text/plain"
        )
    else:
        # No agent configured - use fallback
        return StreamingResponse(
            fake_stream_processor(request.message, request.conversation_id, request.model, project),
            media_type="text/plain"
        )


# =============================================================================
# Project Settings API - Agents
# =============================================================================

def get_project_or_404(project_name: str) -> dict:
    """Helper to get project by name or raise 404."""
    project = db_project.get_project_by_name(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def verify_project_owner(project: dict, user_id: int):
    """Verify the user is the project owner."""
    if project["owner_id"] != user_id:
        raise HTTPException(status_code=403, detail="Only project owner can modify settings")


@app.get("/projects/{project_name}/agents")
async def list_agents_endpoint(
    project_name: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """List all agents for a project."""
    project = get_project_or_404(project_name)
    agents = db_project.list_agents_for_project(project["id"])
    return JSONResponse({"agents": agents})


@app.post("/projects/{project_name}/agents")
async def create_agent_endpoint(
    project_name: str,
    request: AgentCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Create a new agent for a project."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)
    
    agent = db_project.create_agent(
        project_id=project["id"],
        name=request.name,
        endpoint=request.endpoint,
        connection_type=request.connection_type,
        is_default=request.is_default,
        extras=request.extras
    )
    return JSONResponse(agent)


@app.put("/projects/{project_name}/agents/{agent_id}")
async def update_agent_endpoint(
    project_name: str,
    agent_id: int,
    request: AgentUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update an agent."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)
    
    # Verify agent belongs to this project
    agent = db_project.get_agent_by_id(agent_id)
    if not agent or agent["project_id"] != project["id"]:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    updated_agent = db_project.update_agent(
        agent_id=agent_id,
        name=request.name,
        endpoint=request.endpoint,
        connection_type=request.connection_type,
        is_default=request.is_default,
        extras=request.extras
    )
    return JSONResponse(updated_agent)


@app.delete("/projects/{project_name}/agents/{agent_id}")
async def delete_agent_endpoint(
    project_name: str,
    agent_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Delete an agent."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)
    
    # Verify agent belongs to this project
    agent = db_project.get_agent_by_id(agent_id)
    if not agent or agent["project_id"] != project["id"]:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db_project.delete_agent(agent_id)
    return JSONResponse({"success": True})


# =============================================================================
# Project Settings API - AD Groups (RBAC)
# =============================================================================

@app.get("/projects/{project_name}/groups")
async def list_ad_groups_endpoint(
    project_name: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """List all AD groups for a project."""
    project = get_project_or_404(project_name)
    groups = db_project.list_ad_groups_for_project(project["id"])
    return JSONResponse({"groups": groups})


@app.post("/projects/{project_name}/groups")
async def add_ad_group_endpoint(
    project_name: str,
    request: ADGroupCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Add an AD group to a project."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)
    
    group = db_project.add_ad_group_to_project(
        project_id=project["id"],
        group_dn=request.group_dn,
        group_name=request.group_name,
        role=request.role
    )
    return JSONResponse(group)


@app.put("/projects/{project_name}/groups/{group_id}")
async def update_ad_group_endpoint(
    project_name: str,
    group_id: int,
    request: ADGroupUpdate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Update an AD group's role."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)
    
    updated_group = db_project.update_ad_group_role(group_id, request.role)
    if not updated_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return JSONResponse(updated_group)


@app.delete("/projects/{project_name}/groups/{group_id}")
async def remove_ad_group_endpoint(
    project_name: str,
    group_id: int,
    current_user: CurrentUser = Depends(get_current_user)
):
    """Remove an AD group from a project."""
    project = get_project_or_404(project_name)
    verify_project_owner(project, current_user.user_id)
    
    success = db_project.remove_ad_group_from_project(group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return JSONResponse({"success": True})


# =============================================================================
# LDAP Search API
# =============================================================================

@app.get("/ldap/search")
async def ldap_search_endpoint(
    q: str,
    type: str = "all",
    current_user: CurrentUser = Depends(get_current_user)
):
    """Search LDAP for users and groups."""
    if len(q) < 2:
        return JSONResponse({"results": []})
    
    results = ldap_auth.search_users_and_groups(q, search_type=type)
    return JSONResponse({"results": results})


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except Exception:
            return await super().get_response("index.html", scope)

frontend = Frontend()
FRONTEND_BUILD_DIR = frontend.get_build_dir()

mimetypes.add_type("text/javascript", ".js")
app.mount(
    "/",
    SPAStaticFiles(directory=frontend.get_build_dir(), html=True),
    name="spa-static-files",
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
