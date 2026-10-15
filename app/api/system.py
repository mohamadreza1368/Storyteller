from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.config import settings
from app.engine.llm_client import llm
from app.storage.store import store

router = APIRouter(prefix="/api/system", tags=["System"])

class SystemConfigRequest(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    image_provider: Optional[str] = None
    image_model: Optional[str] = None

class TestConnectionRequest(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None

@router.get("/info")
async def get_system_info():
    is_demo = (llm.provider == "mock" or (not llm.api_key and llm.provider not in ("ollama", "custom")))
    saved = store.get_system_settings() or {}
    return {
        "app_name": settings.app_name,
        "provider": llm.provider,
        "model": llm.model,
        "base_url": llm.base_url,
        "has_api_key": bool(llm.api_key),
        "demo_mode": is_demo,
        "demo_message": "Creative Offline Simulator Mode: Generating with local narrative engine. Configure an API key or Custom endpoint for live LLM generation." if is_demo else f"AI Engine Connected ({llm.provider}: {llm.model}).",
        "image_provider": saved.get("image_provider", "auto"),
        "image_model": saved.get("image_model", "")
    }

@router.post("/config")
async def update_system_config(req: SystemConfigRequest):
    llm.update_config(
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        base_url=req.base_url,
        image_provider=req.image_provider,
        image_model=req.image_model
    )
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
