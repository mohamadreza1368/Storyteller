from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from app.storage.users import User, UserPublic, user_manager
from app.storage.store import store
from app.engine.llm_client import llm
from app.config import settings
from app.api.deps import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])

class UpdateUserStatusRequest(BaseModel):
    status: str  # "active" or "suspended"

class ResetPasswordRequest(BaseModel):
    new_password: str

class AdminAIConfigRequest(BaseModel):
    # Global LLM settings
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    # Dedicated Image Generation API settings
    image_provider: Optional[str] = None
    image_api_key: Optional[str] = None
    image_base_url: Optional[str] = None
    image_model: Optional[str] = None

class AdminDashboardStats(BaseModel):
    total_users: int
    active_users: int
    suspended_users: int
    total_novels: int
    total_episodes: int
    total_words: int
    current_ai_provider: str
    current_ai_model: str
    image_engine: str

@router.get("/dashboard", response_model=AdminDashboardStats)
async def get_dashboard_stats(admin: User = Depends(get_current_admin)):
    users = user_manager.list_users()
    active_cnt = sum(1 for u in users if u.status == "active")
    suspended_cnt = sum(1 for u in users if u.status == "suspended")
    
    p_stats = store.get_platform_stats()
    saved = store.get_system_settings() or {}

    return AdminDashboardStats(
        total_users=len(users),
        active_users=active_cnt,
        suspended_users=suspended_cnt,
        total_novels=p_stats["total_novels"],
        total_episodes=p_stats["total_episodes"],
        total_words=p_stats["total_words"],
        current_ai_provider=llm.provider,
        current_ai_model=llm.model or "default",
        image_engine=saved.get("image_provider", "auto")
    )

@router.get("/users", response_model=List[UserPublic])
async def list_all_users(admin: User = Depends(get_current_admin)):
    """List all registered users with their authored novels count (content not exposed)."""
    users = user_manager.list_users()
    user_list = []
    for u in users:
        n_count = store.get_user_novels_count(u.id)
        user_list.append(UserPublic(
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
            novels_count=n_count
        ))
    user_list.sort(key=lambda x: x.created_at, reverse=True)
    return user_list

@router.patch("/users/{user_id}/status")
async def update_user_status(user_id: str, req: UpdateUserStatusRequest, admin: User = Depends(get_current_admin)):
    if req.status not in ("active", "suspended"):
        raise HTTPException(status_code=400, detail="Invalid status. Must be 'active' or 'suspended'.")
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Administrators cannot suspend their own account.")
    
    updated = user_manager.update_status(user_id, req.status)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"message": f"User status successfully updated to {req.status}."}

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(user_id: str, req: ResetPasswordRequest, admin: User = Depends(get_current_admin)):
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")
    updated = user_manager.reset_password(user_id, req.new_password)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"message": "Password successfully reset for user."}

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: User = Depends(get_current_admin)):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Administrators cannot delete their own account.")
    try:
        success = user_manager.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found.")
        return {"message": "User deleted successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/ai-config")
async def get_ai_config(admin: User = Depends(get_current_admin)):
    """Retrieve global AI configuration for the platform."""
    saved = store.get_system_settings() or {}
    img_key = saved.get("image_api_key", "")
    return {
        "provider": llm.provider,
        "model": llm.model,
        "base_url": llm.base_url,
        "has_api_key": bool(llm.api_key),
        "api_key_masked": f"••••••••{llm.api_key[-4:]}" if llm.api_key and len(llm.api_key) > 4 else ("••••" if llm.api_key else ""),
        "image_provider": saved.get("image_provider", "auto"),
        "image_base_url": saved.get("image_base_url", ""),
        "image_model": saved.get("image_model", ""),
        "has_image_api_key": bool(img_key),
        "image_api_key_masked": f"••••••••{img_key[-4:]}" if img_key and len(img_key) > 4 else ("••••" if img_key else "")
    }

@router.post("/ai-config")
async def update_ai_config(req: AdminAIConfigRequest, admin: User = Depends(get_current_admin)):
    """Update global AI credentials, models, and endpoints for all platform users."""
    llm.update_config(
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        base_url=req.base_url,
        image_provider=req.image_provider,
        image_api_key=req.image_api_key,
        image_base_url=req.image_base_url,
        image_model=req.image_model
    )
    return await get_ai_config(admin)

@router.post("/test-connection")
async def test_admin_api_connection(req: AdminAIConfigRequest, admin: User = Depends(get_current_admin)):
    """Test live connectivity of global AI credentials."""
    result = await llm.test_connection(
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        base_url=req.base_url
    )
    return result

@router.post("/test-image-connection")
async def test_admin_image_connection(req: AdminAIConfigRequest, admin: User = Depends(get_current_admin)):
    """Test live connectivity of global Image Generation API credentials."""
    from app.engine.image_client import chapter_image_client
    result = await chapter_image_client.test_connection(
        provider=req.image_provider,
        api_key=req.image_api_key,
        model=req.image_model,
        base_url=req.image_base_url
    )
    return result
