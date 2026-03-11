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
            
            # Fetch user details from LDAP (loaded fresh on each login)
            display_name = None
            email = None
            ad_groups = None
            
            user_info = ldap_auth.search_users_and_groups(request.username)
            print(f"user_info: {user_info}")
            if user_info:
                display_name = user_info.get("name")
                email = user_info.get("email")
                ad_groups = user_info.get("member_of")
                # Normalize ad_groups to list
                if ad_groups and isinstance(ad_groups, str):
                    ad_groups = [ad_groups]
            
            # Get or create user in database (only stores username)
            user = db_chat.get_or_create_user(normalized_username)
            
            # Create token with LDAP details embedded
            access_token = create_access_token(
                username=user.username,
                user_id=user.id,
                display_name=display_name,
                email=email,
                ad_groups=ad_groups
            )
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user_id=user.id,
                username=user.username,
                display_name=display_name,
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
    # User details come from JWT token (loaded from LDAP at login time)
    return JSONResponse({
        "user_id": current_user.user_id,
        "username": current_user.username,
        "display_name": current_user.display_name,
        "email": current_user.email,
        "ad_groups": current_user.ad_groups,
    })
