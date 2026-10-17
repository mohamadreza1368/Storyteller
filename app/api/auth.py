from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from pydantic import BaseModel, EmailStr
from app.storage.users import User, UserPublic, user_manager
from app.storage.store import store
from app.api.deps import get_current_user, get_token_from_request

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: Optional[str] = ""

class LoginRequest(BaseModel):
    login: Optional[str] = None
    identifier: Optional[str] = None
    password: str

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

class AuthResponse(BaseModel):
    token: str
    user: UserPublic

@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, response: Response):
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")
    if len(req.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters long.")
    
    try:
        user = user_manager.create_user(
            email=req.email,
            username=req.username,
            password=req.password,
            full_name=req.full_name or req.username
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Log them in automatically
    auth_res = user_manager.authenticate(user.email, req.password)
    if not auth_res:
        raise HTTPException(status_code=500, detail="Registration succeeded but login failed.")
    user_obj, token = auth_res

    response.set_cookie(key="st_token", value=token, httponly=True, samesite="lax", max_age=86400 * 30)
    
    return AuthResponse(
        token=token,
        user=UserPublic(
            id=user_obj.id,
            username=user_obj.username,
            email=user_obj.email,
            full_name=user_obj.full_name,
            role=user_obj.role,
            status=user_obj.status,
            avatar_url=user_obj.avatar_url,
            bio=user_obj.bio,
            created_at=user_obj.created_at,
            last_login=user_obj.last_login,
            novels_count=0
        )
    )

@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, response: Response):
    login_id = (req.login or req.identifier or "").strip()
    if not login_id:
        raise HTTPException(status_code=400, detail="Username or email is required.")
    try:
        auth_res = user_manager.authenticate(login_id, req.password)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not auth_res:
        raise HTTPException(status_code=401, detail="Invalid email/username or password.")

    user_obj, token = auth_res
    response.set_cookie(key="st_token", value=token, httponly=True, samesite="lax", max_age=86400 * 30)

    novels_cnt = store.get_user_novels_count(user_obj.id)
    return AuthResponse(
        token=token,
        user=UserPublic(
            id=user_obj.id,
            username=user_obj.username,
            email=user_obj.email,
            full_name=user_obj.full_name,
            role=user_obj.role,
            status=user_obj.status,
            avatar_url=user_obj.avatar_url,
            bio=user_obj.bio,
            created_at=user_obj.created_at,
            last_login=user_obj.last_login,
            novels_count=novels_cnt
        )
    )

@router.post("/logout")
async def logout(request: Request, response: Response):
    token = get_token_from_request(request)
    if token:
        user_manager.revoke_token(token)
    response.delete_cookie(key="st_token")
    return {"message": "Logged out successfully."}

@router.get("/me", response_model=UserPublic)
async def get_current_user_profile(user: User = Depends(get_current_user)):
    novels_cnt = store.get_user_novels_count(user.id)
    return UserPublic(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        status=user.status,
        avatar_url=user.avatar_url,
        bio=user.bio,
        created_at=user.created_at,
        last_login=user.last_login,
        novels_count=novels_cnt
    )

@router.patch("/profile", response_model=UserPublic)
async def update_profile(req: ProfileUpdateRequest, user: User = Depends(get_current_user)):
    new_pwd = None
    if req.new_password:
        if not req.current_password:
            raise HTTPException(status_code=400, detail="Current password is required to change password.")
        # Verify current password
        auth_check = user_manager.authenticate(user.email, req.current_password)
        if not auth_check:
            raise HTTPException(status_code=400, detail="Current password is incorrect.")
        if len(req.new_password) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")
        new_pwd = req.new_password

    updated = user_manager.update_profile(
        user_id=user.id,
        full_name=req.full_name,
        bio=req.bio,
        new_password=new_pwd
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    novels_cnt = store.get_user_novels_count(updated.id)
    return UserPublic(
        id=updated.id,
        username=updated.username,
        email=updated.email,
        full_name=updated.full_name,
        role=updated.role,
        status=updated.status,
        avatar_url=updated.avatar_url,
        bio=updated.bio,
        created_at=updated.created_at,
        last_login=updated.last_login,
        novels_count=novels_cnt
    )
