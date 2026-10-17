from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from app.storage.users import User, user_manager

def get_token_from_request(request: Request) -> Optional[str]:
    # 1. Check Authorization: Bearer <token>
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    
    # 2. Check X-Auth-Token header
    token = request.headers.get("X-Auth-Token")
    if token:
        return token.strip()

    # 3. Check Cookie
    token = request.cookies.get("st_token")
    if token:
        return token.strip()
    
    return None

async def get_current_user_optional(request: Request) -> Optional[User]:
    token = get_token_from_request(request)
    if not token:
        return None
    user = user_manager.get_user_by_token(token)
    if not user or user.status == "suspended":
        return None
    return user

async def get_current_user(request: Request) -> User:
    user = await get_current_user_optional(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to your account."
        )
    return user

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to access this resource."
        )
    return current_user
