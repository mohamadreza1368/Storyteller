from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.config import settings
from app.engine.llm_client import llm
from app.engine.qloo_client import qloo_client
from app.storage.store import store

router = APIRouter(prefix="/api/system", tags=["System"])

class SystemConfigRequest(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    image_provider: Optional[str] = None
    image_model: Optional[str] = None
    image_api_key: Optional[str] = None
    image_base_url: Optional[str] = None
    qloo_api_key: Optional[str] = None
    qloo_base_url: Optional[str] = None
    qloo_enabled: Optional[bool] = None

class TestConnectionRequest(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None

class TestQlooRequest(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None

@router.get("/info")
async def get_system_info():
    is_demo = (llm.provider == "mock" or (not llm.api_key and llm.provider not in ("ollama", "custom")))
    saved = store.get_system_settings() or {}
    q_key = saved.get("qloo_api_key") or settings.qloo_api_key or ""
    q_url = saved.get("qloo_base_url") or settings.qloo_base_url or "https://hackathon.api.qloo.com"
    q_en = saved.get("qloo_enabled", settings.qloo_enabled)

    return {
        "app_name": settings.app_name,
        "provider": llm.provider,
        "model": llm.model,
        "base_url": llm.base_url,
        "has_api_key": bool(llm.api_key),
        "demo_mode": is_demo,
        "demo_message": "Creative Offline Simulator Mode: Generating with local narrative engine. Configure an API key or Custom endpoint for live LLM generation." if is_demo else f"AI Engine Connected ({llm.provider}: {llm.model}).",
        "image_provider": saved.get("image_provider", "auto"),
        "image_model": saved.get("image_model", ""),
        "has_image_api_key": bool(saved.get("image_api_key")),
        "image_base_url": saved.get("image_base_url", ""),
        "has_qloo_api_key": bool(q_key),
        "qloo_base_url": q_url,
        "qloo_enabled": bool(q_en)
    }

@router.post("/config")
async def update_system_config(req: SystemConfigRequest):
    llm.update_config(
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        base_url=req.base_url,
        image_provider=req.image_provider,
        image_model=req.image_model,
        image_api_key=req.image_api_key,
        image_base_url=req.image_base_url
    )
    
    # Save Qloo settings to persistent storage
    saved = store.get_system_settings() or {}
    if req.qloo_api_key is not None:
        saved["qloo_api_key"] = req.qloo_api_key
    if req.qloo_base_url is not None:
        saved["qloo_base_url"] = req.qloo_base_url.rstrip("/")
    if req.qloo_enabled is not None:
        saved["qloo_enabled"] = req.qloo_enabled
    store.save_system_settings(saved)

    return await get_system_info()

@router.post("/test-connection")
async def test_api_connection(req: TestConnectionRequest):
    """Live test of LLM connectivity with latency and response."""
    result = await llm.test_connection(
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        base_url=req.base_url
    )
    return result

@router.post("/test-qloo-connection")
async def test_qloo_connection(req: TestQlooRequest):
    """Live test of Qloo Taste API credentials and connectivity."""
    saved = store.get_system_settings() or {}
    key = req.api_key if req.api_key is not None else saved.get("qloo_api_key") or settings.qloo_api_key
    url = req.base_url if req.base_url is not None else saved.get("qloo_base_url") or settings.qloo_base_url
    return qloo_client.test_connection(api_key=key, base_url=url)
