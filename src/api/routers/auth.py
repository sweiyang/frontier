"""Auth routes: /login, /logout, /me."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from api.app_config import ldap_auth
from api.deps.auth import CurrentUser, get_current_user
from api.schema import LoginRequest, TokenResponse
from core.auth.jwt import create_access_token
from core.db import db_chat

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user via LDAP and return JWT token."""
    try:
        success = ldap_auth.login(request.username, request.password)
        if success:
            normalized_username = request.username.lower()
            user = db_chat.get_or_create_user(normalized_username)
            access_token = create_access_token(username=user.username, user_id=user.id)
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user_id=user.id,
                username=user.username,
            )
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(current_user: CurrentUser = Depends(get_current_user)):
    """Logout the current user."""
    ldap_auth.logout()
    return JSONResponse({"success": True, "message": "Logged out"})


@router.get("/me")
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    """Get current authenticated user info. Used to verify token and restore session."""
    return JSONResponse({
        "user_id": current_user.user_id,
        "username": current_user.username,
    })
