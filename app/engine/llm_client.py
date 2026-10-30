import os
import json
import time
import inspect
import logging
from typing import Optional, Dict, Any, List, Union
from app.config import settings
from app.storage.store import store

logger = logging.getLogger(__name__)

async def _invoke_fallback(fallback_generator):
    """Safely calls a fallback generator whether it is an async coroutine, regular function, or value."""
    if fallback_generator is None:
        return None
    try:
        if callable(fallback_generator):
            res = fallback_generator()
            if inspect.isawaitable(res):
                return await res
            return res
        elif inspect.isawaitable(fallback_generator):
            return await fallback_generator
        return fallback_generator
    except Exception as e:
        logger.error(f"Fallback generator invocation error: {e}", exc_info=True)
        return None

import re

def clean_and_parse_json(raw_text: str) -> Union[Dict[str, Any], List[Any]]:
    """Robustly extracts and parses JSON objects and arrays from LLM output, handling reasoning tags and markdown fences."""
    if not raw_text or not raw_text.strip():
        raise ValueError("LLM returned an empty response.")

    text = raw_text.strip()

    # 1. Strip thinking / reasoning tags (<think>...</think>, <thought>...</thought>)
    text = re.sub(r"<(think|thought)>.*?</\1>", "", text, flags=re.DOTALL)
    # If unclosed thinking tag remaining, strip from tag to end
    text = re.sub(r"<(think|thought)>.*$", "", text, flags=re.DOTALL).strip()

    # 2. Extract from markdown code fences if present (supports both {...} and [...])
    fence_match = re.search(r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```", text, flags=re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    else:
        # Strip standalone code fence markers
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # Check whether the JSON is an array ([...]) or an object ({...})
        first_bracket = text.find("[")
        first_obj = text.find("{")
        if first_bracket != -1 and (first_obj == -1 or first_bracket < first_obj):
            last_bracket = text.rfind("]")
            if last_bracket != -1 and last_bracket > first_bracket:
                text = text[first_bracket:last_bracket + 1]
            else:
                text = text[first_bracket:]
        elif first_obj != -1:
            last_brace = text.rfind("}")
            if last_brace != -1 and last_brace > first_obj:
                text = text[first_obj:last_brace + 1]
            else:
                text = text[first_obj:]
        else:
            raise ValueError(f"No JSON object or array found in LLM response: {raw_text[:200]}")

    # 3. Clean trailing commas before closing braces/brackets
    cleaned = re.sub(r",\s*([\]\}])", r"\1", text)

    # 4. Attempt direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 5. Attempt parse on raw extracted slice
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 6. Attempt repair of unclosed strings, trailing commas, and unclosed brackets/braces
    stack = []
    in_string = False
    escape = False
    repaired_chars = []
    for ch in text:
        if escape:
            escape = False
            repaired_chars.append(ch)
            continue
        if ch == "\\":
            escape = True
            repaired_chars.append(ch)
            continue
        if ch == '"':
            in_string = not in_string
            repaired_chars.append(ch)
            continue
        if in_string:
            # Replace literal newlines/tabs inside unescaped strings
            if ch == "\n":
                repaired_chars.append("\\n")
                continue
            if ch == "\r":
                continue
            if ch == "\t":
                repaired_chars.append("\\t")
                continue
            repaired_chars.append(ch)
            continue

        if ch in ("{", "["):
            stack.append(ch)
        elif ch == "}" and stack and stack[-1] == "{":
            stack.pop()
        elif ch == "]" and stack and stack[-1] == "[":
            stack.pop()
        repaired_chars.append(ch)

    repaired = "".join(repaired_chars)
    if in_string:
        repaired += '"'
    while stack:
        opener = stack.pop()
        repaired += "}" if opener == "{" else "]"

    repaired = re.sub(r",\s*([\]\}])", r"\1", repaired)

    try:
        return json.loads(repaired)
    except json.JSONDecodeError as err:
        raise ValueError(f"Failed to parse LLM JSON: {err}. Snippet: {repaired[:300]}") from err

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
                    timeout=15.0,
                    max_retries=0
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
                res = await _invoke_fallback(fallback_generator)
                return res if isinstance(res, dict) else {}
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
                    timeout=120.0,
                    max_retries=1
                )
                res = await client.chat.completions.create(
                    model=self.model or "gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt_with_format}
                    ],
                    max_tokens=16384,
                    response_format={"type": "json_object"} if self.provider not in ("ollama", "custom") else None
                )
                choice = res.choices[0]
                content = choice.message.content or ""
                if not content and hasattr(choice.message, "reasoning_content") and choice.message.reasoning_content:
                    content = choice.message.reasoning_content
                return clean_and_parse_json(content)

        except Exception as e:
            logger.error(f"LLM Error ({self.provider}): {e}")
            if fallback_generator:
                logger.warning(f"Using stage fallback generator due to LLM response error: {e}")
                res = await _invoke_fallback(fallback_generator)
                if isinstance(res, dict):
                    return res
            raise e

    async def generate_text(self, system_prompt: str, user_prompt: str, fallback_generator=None) -> str:
        """Generates continuous prose or dialogue text."""
        if self.provider == "mock" or (not self.api_key and self.provider not in ("ollama", "custom")):
            if fallback_generator:
                res = await _invoke_fallback(fallback_generator)
                return str(res) if res is not None else ""
            return ""

        try:
            if self.provider == "gemini":
                from google import genai
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model=self.model or "gemini-2.5-flash",
                    contents=f"{system_prompt}\n\n{user_prompt}"
                )
                text = (response.text or "").strip()
                text = re.sub(r"<(think|thought)>.*?</\1>", "", text, flags=re.DOTALL)
                text = re.sub(r"<(think|thought)>.*$", "", text, flags=re.DOTALL).strip()
                return text

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
                    timeout=120.0,
                    max_retries=1
                )
                res = await client.chat.completions.create(
                    model=self.model or "gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=16384
                )
                choice = res.choices[0]
                content = choice.message.content or ""
                if not content and hasattr(choice.message, "reasoning_content") and choice.message.reasoning_content:
                    content = choice.message.reasoning_content
                content = re.sub(r"<(think|thought)>.*?</\1>", "", content, flags=re.DOTALL)
                content = re.sub(r"<(think|thought)>.*$", "", content, flags=re.DOTALL).strip()
                if not content and fallback_generator:
                    res_fb = await _invoke_fallback(fallback_generator)
                    return str(res_fb) if res_fb is not None else ""
                return content

        except Exception as e:
            logger.error(f"LLM Error ({self.provider}): {e}")
            if fallback_generator:
                logger.warning(f"Using fallback text generator due to LLM error: {e}")
                res = await _invoke_fallback(fallback_generator)
                if res is not None:
                    return str(res)
            raise e

    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: int = 1500) -> str:
        """Convenience alias for text generation across providers."""
        return await self.generate_text(system_prompt=system_prompt, user_prompt=prompt)

llm = LLMClient()
