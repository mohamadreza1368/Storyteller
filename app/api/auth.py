from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from pydantic import BaseModel, EmailStr
from app.storage.users import User, UserPublic, user_manager
from app.storage.store import store
from app.engine.qloo_client import qloo_client
from app.api.deps import get_current_user, get_token_from_request

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: Optional[str] = ""
    favorite_books: Optional[List[str]] = None
    favorite_movies: Optional[List[str]] = None

class LoginRequest(BaseModel):
    login: Optional[str] = None
    identifier: Optional[str] = None
    password: str

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None
    favorite_books: Optional[List[str]] = None
    favorite_movies: Optional[List[str]] = None

class AuthResponse(BaseModel):
    token: str
    user: UserPublic

def user_to_public(u: User, novels_cnt: int = 0) -> UserPublic:
    return UserPublic(
        id=u.id,
        username=u.username,
        email=u.email,
        full_name=u.full_name,
        role=u.role,
        status=u.status,
        avatar_url=u.avatar_url,
        bio=u.bio,
        created_at=u.created_at,
        last_login=u.last_login,
        novels_count=novels_cnt,
        favorite_books=u.favorite_books,
        favorite_movies=u.favorite_movies,
        cultural_taste=u.cultural_taste
    )

@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, response: Response):
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")
    if len(req.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters long.")
    
    clean_books = [b.strip() for b in (req.favorite_books or []) if b and b.strip()][:5]
    clean_movies = [m.strip() for m in (req.favorite_movies or []) if m and m.strip()][:5]

    taste_profile = {}
    if clean_books or clean_movies:
        try:
            taste_profile = qloo_client.analyze_author_taste_profile(clean_books, clean_movies)
        except Exception:
            taste_profile = {}

    try:
        user = user_manager.create_user(
            email=req.email,
            username=req.username,
            password=req.password,
            full_name=req.full_name or req.username,
            favorite_books=clean_books,
            favorite_movies=clean_movies,
            cultural_taste=taste_profile
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
        user=user_to_public(user_obj, 0)
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
        user=user_to_public(user_obj, novels_cnt)
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
    return user_to_public(user, novels_cnt)

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

    taste_update = None
    if req.favorite_books is not None or req.favorite_movies is not None:
        b_list = req.favorite_books if req.favorite_books is not None else user.favorite_books
        m_list = req.favorite_movies if req.favorite_movies is not None else user.favorite_movies
        taste_update = qloo_client.analyze_author_taste_profile(b_list, m_list)

    updated = user_manager.update_profile(
        user_id=user.id,
        full_name=req.full_name,
        bio=req.bio,
        new_password=new_pwd,
        favorite_books=req.favorite_books,
        favorite_movies=req.favorite_movies,
        cultural_taste=taste_update
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    novels_cnt = store.get_user_novels_count(updated.id)
    return user_to_public(updated, novels_cnt)
