"""
JWT Token utilities for authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from core.config import get_config

_cfg = get_config()
JWT_SECRET_KEY = _cfg.jwt_secret_key
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = _cfg.jwt_expire_minutes

# Security scheme for FastAPI
security = HTTPBearer()


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    sub: str  # username
    user_id: int
    exp: datetime
    display_name: Optional[str] = None
    email: Optional[str] = None
    ad_groups: Optional[List[str]] = None


class CurrentUser(BaseModel):
    """Current authenticated user info."""
    username: str
    user_id: int
    display_name: Optional[str] = None
    email: Optional[str] = None
    ad_groups: Optional[List[str]] = None


def create_access_token(
    username: str,
    user_id: int,
    display_name: Optional[str] = None,
    email: Optional[str] = None,
    ad_groups: Optional[List[str]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        username: The username to encode in the token
        user_id: The user's database ID
        display_name: The user's display name from LDAP
        email: The user's email from LDAP
        ad_groups: List of AD group DNs the user belongs to
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    
    payload = {
        "sub": username,
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    
    # Only include optional fields if they have values
    if display_name:
        payload["display_name"] = display_name
    if email:
        payload["email"] = email
    if ad_groups:
        payload["ad_groups"] = ad_groups
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[TokenPayload]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token string
        
    Returns:
        TokenPayload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return TokenPayload(
            sub=payload["sub"],
            user_id=payload["user_id"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            display_name=payload.get("display_name"),
            email=payload.get("email"),
            ad_groups=payload.get("ad_groups")
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    FastAPI dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        CurrentUser with username, user_id, display_name, and ad_groups
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise credentials_exception
    
    return CurrentUser(
        username=payload.sub,
        user_id=payload.user_id,
        display_name=payload.display_name,
        email=payload.email,
        ad_groups=payload.ad_groups
    )


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[CurrentUser]:
    """
    FastAPI dependency to optionally get the current user.
    Returns None if no valid token is provided instead of raising an exception.
    """
    if credentials is None:
        return None
    
    payload = verify_token(credentials.credentials)
    if payload is None:
        return None
    
    return CurrentUser(
        username=payload.sub,
        user_id=payload.user_id,
        display_name=payload.display_name,
        email=payload.email,
        ad_groups=payload.ad_groups
    )

