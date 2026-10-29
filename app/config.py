import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Storyteller AI"
    data_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "novels")
    db_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "storyteller.db")
    
    # LLM Settings
    # provider can be: "mock", "gemini", "openai", "ollama", "openrouter"
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")

    # Qloo Cultural AI / Taste Settings
    qloo_api_key: str = os.getenv("QLOO_API_KEY", "")
    qloo_base_url: str = os.getenv("QLOO_BASE_URL", "https://hackathon.api.qloo.com")
    qloo_enabled: bool = os.getenv("QLOO_ENABLED", "true").lower() in ("true", "1")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
