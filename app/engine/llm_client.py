import os
import json
import time
import logging
from typing import Optional, Dict, Any, List
from app.config import settings
from app.storage.store import store

logger = logging.getLogger(__name__)

def clean_and_parse_json(raw_text: str) -> Dict[str, Any]:
    """Robustly extracts and parses JSON from LLM output, handling markdown fences and formatting anomalies."""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Locate outermost JSON object if surrounded by preamble/postscript
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        text = text[first_brace:last_brace + 1]

    # Clean trailing commas before closing braces/brackets
    import re
    cleaned = re.sub(r",\s*([\]\}])", r"\1", text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try raw text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback: attempt simple repair of unclosed JSON structures
            stack = []
            in_string = False
            escape = False
            for ch in text:
                if escape:
                    escape = False
                    continue
                if ch == "\\":
                    escape = True
                    continue
                if ch == '"':
                    in_string = not in_string
                    continue
                if not in_string:
                    if ch in ("{", "["):
                        stack.append(ch)
                    elif ch == "}" and stack and stack[-1] == "{":
                        stack.pop()
                    elif ch == "]" and stack and stack[-1] == "[":
                        stack.pop()

            repaired = text
            if in_string:
                repaired += '"'
            while stack:
                opener = stack.pop()
                repaired += "}" if opener == "{" else "]"

            repaired = re.sub(r",\s*([\]\}])", r"\1", repaired)
            return json.loads(repaired)

class LLMClient:
    def __init__(self):
        # Load saved settings if any
        saved = store.get_system_settings()
        self.provider = (saved.get("provider") or settings.llm_provider).lower()
        self.api_key = saved.get("api_key") or settings.llm_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = saved.get("model") or settings.llm_model
        self.base_url = saved.get("base_url") or settings.llm_base_url

        if not self.api_key and self.provider not in ("mock", "ollama"):
            self.provider = "mock"

    def update_config(self, provider: str = None, api_key: str = None, model: str = None, base_url: str = None,
                      image_provider: str = None, image_api_key: str = None, image_base_url: str = None, image_model: str = None):
        saved = store.get_system_settings() or {}
        if provider:
            self.provider = provider.lower()
            saved["provider"] = self.provider
        if api_key is not None:
            self.api_key = api_key
            saved["api_key"] = self.api_key
        if model:
            self.model = model
            saved["model"] = self.model
        if base_url is not None:
            self.base_url = base_url
            saved["base_url"] = self.base_url
        if image_provider is not None:
            saved["image_provider"] = image_provider
        if image_api_key is not None:
            saved["image_api_key"] = image_api_key
        if image_base_url is not None:
            saved["image_base_url"] = image_base_url
        if image_model is not None:
            saved["image_model"] = image_model

        # Save to persistent storage
        store.save_system_settings(saved)

    async def test_connection(self, provider: str = None, api_key: str = None, model: str = None, base_url: str = None) -> Dict[str, Any]:
        """Tests live connectivity to the LLM endpoint and measures response latency."""
        prov = (provider or self.provider).lower()
        key = api_key if api_key is not None else self.api_key
        mod = model or self.model
        url = base_url if base_url is not None else self.base_url

        if prov == "mock":
            return {
                "success": True,
                "latency_ms": 15,
                "message": "Offline Creative Simulator active (no API key or internet required).",
                "model": "local-creative-simulator"
            }

        start_time = time.time()
        test_prompt = "In one short sentence, say hello and that you are ready to craft a novel."

        try:
            if prov == "gemini":
                from google import genai
                client = genai.Client(api_key=key)
                res = client.models.generate_content(
                    model=mod or "gemini-2.5-flash",
                    contents=test_prompt
                )
                latency = int((time.time() - start_time) * 1000)
                return {
                    "success": True,
                    "latency_ms": latency,
                    "message": res.text.strip(),
                    "model": mod or "gemini-2.5-flash"
                }

            elif prov in ("custom", "openai", "openrouter", "ollama"):
                from openai import AsyncOpenAI
                target_base_url = url or (
                    "https://openrouter.ai/api/v1" if prov == "openrouter" else (
                        "http://localhost:11434/v1" if prov == "ollama" else None
                    )
                )
                client = AsyncOpenAI(
                    api_key=key or "dummy",
                    base_url=target_base_url,
                    timeout=15.0
                )
                res = await client.chat.completions.create(
                    model=mod or "gpt-4o-mini",
                    messages=[
                        {"role": "user", "content": test_prompt}
                    ],
                    max_tokens=60
                )
                latency = int((time.time() - start_time) * 1000)
                return {
                    "success": True,
                    "latency_ms": latency,
                    "message": res.choices[0].message.content.strip(),
                    "model": mod or "gpt-4o-mini"
                }
            else:
                return {
                    "success": False,
                    "latency_ms": 0,
                    "error": f"Unknown provider: {prov}"
                }

        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            logger.error(f"Test connection error: {e}")
            return {
                "success": False,
                "latency_ms": latency,
                "error": str(e)
            }

    async def generate_json(self, system_prompt: str, user_prompt: str, fallback_generator=None) -> Dict[str, Any]:
        """Calls the configured LLM and expects structured JSON output."""
        if self.provider == "mock" or (not self.api_key and self.provider not in ("ollama", "custom")):
            if fallback_generator:
                return await fallback_generator()
            return {}

        prompt_with_format = f"{user_prompt}\n\nIMPORTANT: Return ONLY valid JSON matching the requested schema. Do NOT enclose in markdown backticks."
        
        try:
            if self.provider == "gemini":
                from google import genai
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model=self.model or "gemini-2.5-flash",
                    contents=f"{system_prompt}\n\n{prompt_with_format}"
                )
                return clean_and_parse_json(response.text)

            elif self.provider in ("custom", "openai", "openrouter", "ollama"):
                from openai import AsyncOpenAI
                target_base_url = self.base_url or (
                    "https://openrouter.ai/api/v1" if self.provider == "openrouter" else (
                        "http://localhost:11434/v1" if self.provider == "ollama" else None
                    )
                )
                client = AsyncOpenAI(
                    api_key=self.api_key or "dummy",
                    base_url=target_base_url,
                    timeout=25.0
                )
                res = await client.chat.completions.create(
                    model=self.model or "gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt_with_format}
                    ],
                    max_tokens=4096,
                    response_format={"type": "json_object"} if self.provider not in ("ollama", "custom") else None
                )
                content = res.choices[0].message.content or ""
                return clean_and_parse_json(content)

        except Exception as e:
            logger.error(f"LLM Error ({self.provider}): {e}")
            if fallback_generator:
                return await fallback_generator()
            raise e

    async def generate_text(self, system_prompt: str, user_prompt: str, fallback_generator=None) -> str:
        """Generates continuous prose or dialogue text."""
        if self.provider == "mock" or (not self.api_key and self.provider not in ("ollama", "custom")):
            if fallback_generator:
                return await fallback_generator()
            return ""

        try:
            if self.provider == "gemini":
                from google import genai
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model=self.model or "gemini-2.5-flash",
                    contents=f"{system_prompt}\n\n{user_prompt}"
                )
                return response.text.strip()

            elif self.provider in ("custom", "openai", "openrouter", "ollama"):
                from openai import AsyncOpenAI
                target_base_url = self.base_url or (
                    "https://openrouter.ai/api/v1" if self.provider == "openrouter" else (
                        "http://localhost:11434/v1" if self.provider == "ollama" else None
                    )
                )
                client = AsyncOpenAI(
                    api_key=self.api_key or "dummy",
                    base_url=target_base_url,
                    timeout=25.0
                )
                res = await client.chat.completions.create(
                    model=self.model or "gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=4096
                )
                return res.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"LLM Error ({self.provider}): {e}")
            if fallback_generator:
                return await fallback_generator()
            raise e

llm = LLMClient()
