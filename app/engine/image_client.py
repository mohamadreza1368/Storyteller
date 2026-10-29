import os
import re
import json
import base64
import logging
import urllib.request
import asyncio
from typing import Tuple, Optional
from app.models.blueprint import StoryBlueprint
from app.models.episode import EpisodeResponse
from app.storage.store import store
from app.engine.llm_client import llm

logger = logging.getLogger("storyteller.image")

class ChapterImageClient:
    """Handles visual illustration generation for novel chapters with AI art direction."""

    async def craft_vivid_chapter_prompt(self, blueprint: StoryBlueprint, episode: EpisodeResponse) -> str:
        """
        Dynamically crafts an ultra-detailed, evocative 16:9 cinematic visual prompt
        capturing the central dramatic scene and unique atmosphere of this specific chapter.
        Uses intelligent LLM Art Direction when available, with a rich narrative heuristic fallback.
        """
        primary_scene = episode.scenes[0] if episode.scenes else None
        location_name = primary_scene.location_key if primary_scene else blueprint.world.city
        time_marker = primary_scene.time_marker if primary_scene else "Night"
        conflict = primary_scene.conflict if primary_scene else episode.summary

        # Match location description & atmosphere from world definition
        loc_desc = ""
        for loc in blueprint.world.locations:
            if loc.name.lower() in location_name.lower() or location_name.lower() in loc.name.lower():
                loc_desc = loc.description
                break
        if not loc_desc:
            loc_desc = f"the architectural interior and surrounding atmosphere of {location_name}"

        # Match character details present in this chapter / scene
        char_names = primary_scene.character_keys if (primary_scene and primary_scene.character_keys) else [episode.pov_character]
        char_details = []
        for name in char_names:
            c_match = None
            for c in blueprint.cast.characters:
                c_name = getattr(c, "key", "")
                core = getattr(c, "core", None)
                if core:
                    c_name = getattr(core, "name", c_name) or c_name
                if c_name and (c_name.lower() == name.lower() or name.lower() in c_name.lower()):
                    c_match = c
                    break

            if c_match:
                core = getattr(c_match, "core", None)
                archetype = getattr(core, "temperament", None) or getattr(core, "occupation", None) or getattr(core, "role", "protagonist")
                display_name = getattr(core, "name", getattr(c_match, "key", name))
                char_details.append(f"{display_name} ({archetype})")
            else:
                char_details.append(name)
        char_str = ", ".join(char_details) if char_details else episode.pov_character

        # Extract dramatic physical action from character turns if available
        action_detail = ""
        if primary_scene and primary_scene.turns:
            for turn in primary_scene.turns:
                if turn.action and len(turn.action.strip()) > 10:
                    action_detail = turn.action.strip()
                    break
        if not action_detail:
            action_detail = f"confronting the pivotal conflict: {conflict}"

        # Genre-specific artistic lighting & aesthetics
        genre_styles = {
            "Mystery & Crime": "cinematic chiaroscuro lighting, deep noir shadows, warm amber gaslight cutting through thick London sea fog, wet cobblestones, film-still realism",
            "Romance": "soft golden hour illumination, warm ambient candlelight, painterly impressionism, emotional depth, gentle reflections on rain-washed window glass",
            "Sci-Fi": "neon cyberpunk chiaroscuro, volumetric cyan and magenta holographic glow, sleek rain-slicked asphalt, architectural retro-futurism",
            "Fantasy": "ethereal celestial twilight, ancient carved masonry, glowing arcane runic symbols, misty mountain horizon under starry night sky",
            "Historical": "19th century oil painting masterpiece, rich umber and gold earth tones, authentic period architectural textures, soft directional daylight",
            "Horror": "dark gothic suspense, chilling pale moonlight filtering through decrepit ruins, ominous silhouette framing, haunting atmospheric fog",
            "Adventure": "grand panoramic wide-angle vista, dynamic scudding clouds, dramatic low-angle sunlight, rugged untamed terrain"
        }
        style_hint = genre_styles.get(blueprint.style.genre, "cinematic lighting, dramatic composition, master novel concept art")

        # Rich heuristic fallback prompt if LLM is offline or in mock mode
        heuristic_prompt = (
            f"Cinematic wide 16:9 novel illustration for Chapter {episode.episode_number}: '{episode.title}'. "
            f"Scene in {location_name}, {blueprint.world.city} ({blueprint.world.era}). {loc_desc}. "
            f"Focal scene: {char_str} {action_detail}. "
            f"Atmosphere: {time_marker}, {blueprint.style.tone} mood. {style_hint}. "
            f"Masterpiece digital concept art, volumetric lighting, photorealistic textures, 8k resolution, no text, no watermark, no split frame."
        ).strip()

        # Attempt AI Art Director LLM prompt generation if active
        if getattr(llm, "provider", "mock") != "mock":
            try:
                sys_prompt = (
                    "You are an award-winning visual art director and cinematic concept artist for film and literature. "
                    "Your task is to craft a single, highly evocative, atmospheric image generation prompt "
                    "for an ultra-detailed 16:9 cinematic illustration capturing the central, iconic moment of a novel chapter.\n"
                    "Requirements:\n"
                    "1. Focus on concrete visual subjects: character pose, physical action, era-appropriate attire, facial tension.\n"
                    "2. Focus on specific physical environment, lighting, weather, and color palette (e.g. amber gaslight in foggy cobblestone street, or cyan neon reflections on wet asphalt).\n"
                    "3. Include tangible props or focal objects relevant to the chapter.\n"
                    "4. Art style: Masterpiece novel concept art, cinematic wide 16:9 composition, rich textures, volumetric lighting, photorealistic details.\n"
                    "5. Strictly forbid: text, words, titles, captions, watermarks, comic panels, split screens.\n"
                    "6. Length: 60 to 90 words. Output ONLY the raw descriptive prompt string with no prefix or explanations."
                )

                user_prompt = (
                    f"Chapter {episode.episode_number}: \"{episode.title}\"\n"
                    f"Setting: {location_name} in {blueprint.world.city}, {blueprint.world.era}. {loc_desc}\n"
                    f"Genre & Tone: {blueprint.style.genre}, {blueprint.style.tone}\n"
                    f"Characters Present: {char_str}\n"
                    f"Key Action / Climax: {action_detail}\n"
                    f"Chapter Summary: {episode.summary}\n"
                    f"Prose Excerpt: {episode.content[:600] if episode.content else ''}\n\n"
                    f"Write the 16:9 cinematic image generation prompt:"
                )

                ai_prompt = await asyncio.wait_for(
                    llm.generate_text(sys_prompt, user_prompt, fallback_generator=lambda: heuristic_prompt),
                    timeout=8.0
                )
                if ai_prompt and len(ai_prompt.strip()) > 30 and "[TITLE]:" not in ai_prompt:
                    clean_ai_prompt = re.sub(r'^(prompt|image prompt):?\s*', '', ai_prompt.strip(), flags=re.IGNORECASE)
                    clean_ai_prompt = clean_ai_prompt.replace('"', '').replace('\n', ' ').strip()
                    if "no text" not in clean_ai_prompt.lower():
                        clean_ai_prompt += ", wide 16:9 cinematic framing, photorealistic textures, no text, no watermark"
                    logger.info(f"AI Art Director crafted chapter prompt for Chapter {episode.episode_number}: {clean_ai_prompt[:80]}...")
                    return clean_ai_prompt
            except Exception as e:
                logger.debug(f"LLM visual prompt generation skipped: {e}. Using rich heuristic prompt.")

        return heuristic_prompt

    def build_chapter_prompt(self, blueprint: StoryBlueprint, episode: EpisodeResponse) -> str:
        """Constructs an evocative cinematic art prompt based on the chapter's atmosphere."""
        primary_scene = episode.scenes[0] if episode.scenes else None
        location_name = primary_scene.location_key if primary_scene else blueprint.world.city
        time_marker = primary_scene.time_marker if primary_scene else "Night"
        conflict = primary_scene.conflict if primary_scene else episode.summary

        loc_desc = ""
        for loc in blueprint.world.locations:
            if loc.name.lower() in location_name.lower():
                loc_desc = loc.description
                break

        genre_styles = {
            "Mystery & Crime": "cinematic chiaroscuro, moody atmospheric fog, warm gas lamp or amber light cutting through deep shadows, highly detailed Victorian/film-noir realism",
            "Romance": "soft romantic golden hour or rainy twilight lighting, painterly impressionism, emotional depth, gentle reflections on wet cobblestones or vintage interior",
            "Sci-Fi": "futuristic neon lighting, cyan and magenta holographic highlights, sleek reflections on wet surfaces, cinematic cyberpunk aesthetic",
            "Fantasy": "ethereal celestial lighting, ancient stone architecture, glowing arcane runes, misty mountain landscape under starry night sky",
            "Historical": "19th century oil painting style, rich warm earth tones, authentic architectural period details, soft natural window light",
            "Horror": "dark gothic suspense, ominous shadows, cold moonlight filtering through decrepit ruins, chilling chiaroscuro atmosphere",
            "Adventure": "dramatic grand scale panoramic vista, sweeping dynamic clouds, golden hour sunlight, majestic exploration mood"
        }
        style_hint = genre_styles.get(blueprint.style.genre, "cinematic lighting, dramatic composition, award-winning book illustration, 8k resolution")

        return (
            f"Cinematic wide 16:9 novel illustration for Chapter {episode.episode_number}: '{episode.title}'. "
            f"Setting: {location_name} in {blueprint.world.city}, {blueprint.world.era}. {loc_desc} "
            f"Atmosphere: {time_marker}, {blueprint.style.tone} mood. "
            f"Dramatic moment: {conflict}. "
            f"Style: {style_hint}. Masterpiece digital concept art, epic composition, photorealistic textures, no text, no captions, no watermarks."
        ).strip()

    def generate_thematic_svg(self, blueprint: StoryBlueprint, episode: EpisodeResponse) -> bytes:
        """Generates an atmospheric vector illustration tailored to the chapter's setting."""
        primary_scene = episode.scenes[0] if episode.scenes else None
        location = primary_scene.location_key if primary_scene else blueprint.world.city
        time_marker = primary_scene.time_marker if primary_scene else "Night"
        genre = blueprint.style.genre

        # Color schemes based on genre
        palettes = {
            "Mystery & Crime": {
                "sky1": "#0B132B", "sky2": "#1C2541", "accent": "#F59E0B",
                "fog": "rgba(100, 116, 139, 0.25)", "silhouette": "#070C18"
            },
            "Romance": {
                "sky1": "#2B1020", "sky2": "#542138", "accent": "#F472B6",
                "fog": "rgba(244, 114, 182, 0.15)", "silhouette": "#180812"
            },
            "Sci-Fi": {
                "sky1": "#050814", "sky2": "#0F172A", "accent": "#06B6D4",
                "fog": "rgba(6, 182, 212, 0.2)", "silhouette": "#03060C"
            },
            "Fantasy": {
                "sky1": "#0A0E2A", "sky2": "#1E1B4B", "accent": "#A855F7",
                "fog": "rgba(168, 85, 247, 0.2)", "silhouette": "#060919"
            },
            "Historical": {
                "sky1": "#1C1917", "sky2": "#44403C", "accent": "#D97706",
                "fog": "rgba(217, 119, 6, 0.12)", "silhouette": "#0C0A09"
            },
            "Horror": {
                "sky1": "#090514", "sky2": "#1A0B2E", "accent": "#DC2626",
                "fog": "rgba(220, 38, 38, 0.15)", "silhouette": "#05020A"
            }
        }

        pal = palettes.get(genre, palettes["Mystery & Crime"])

        # Clean strings for SVG display
        safe_title = re.sub(r'[<>&"]', '', episode.title)
        safe_location = re.sub(r'[<>&"]', '', location)
        safe_era = re.sub(r'[<>&"]', '', f"{blueprint.world.city} · {time_marker}")

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 500" width="100%" height="100%">
  <defs>
    <linearGradient id="skyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{pal['sky1']}"/>
      <stop offset="100%" stop-color="{pal['sky2']}"/>
    </linearGradient>
    <linearGradient id="accentGlow" x1="50%" y1="0%" x2="50%" y2="100%">
      <stop offset="0%" stop-color="{pal['accent']}" stop-opacity="0.6"/>
      <stop offset="100%" stop-color="{pal['accent']}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="vignette" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#000000" stop-opacity="0.2"/>
      <stop offset="70%" stop-color="#000000" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.9"/>
    </linearGradient>
    <filter id="blurFilter">
      <feGaussianBlur stdDeviation="40"/>
    </filter>
  </defs>

  <!-- Sky & Atmosphere -->
  <rect width="1200" height="500" fill="url(#skyGrad)"/>
  <circle cx="600" cy="180" r="220" fill="url(#accentGlow)" filter="url(#blurFilter)"/>
  
  <!-- Architectural Silhouette & Landscape Layers -->
  <path d="M0,500 L0,320 L120,310 L160,260 L200,310 L280,310 L340,240 L380,310 L520,310 L580,220 L640,310 L750,300 L820,250 L870,300 L1020,300 L1080,230 L1140,300 L1200,300 L1200,500 Z" fill="{pal['silhouette']}" opacity="0.6"/>
  <path d="M0,500 L0,380 L80,370 L140,340 L220,370 L380,360 L440,320 L500,360 L680,350 L760,310 L840,350 L980,340 L1060,300 L1120,350 L1200,350 L1200,500 Z" fill="{pal['silhouette']}" opacity="0.9"/>

  <!-- Atmospheric Fog Band -->
  <rect x="0" y="300" width="1200" height="120" fill="{pal['fog']}" filter="url(#blurFilter)"/>

  <!-- Dramatic Light Beam -->
  <polygon points="560,0 640,0 750,500 450,500" fill="url(#accentGlow)" opacity="0.25"/>

  <!-- Dark Vignette Overlay -->
  <rect width="1200" height="500" fill="url(#vignette)"/>

  <!-- Cinematic Chapter Badge & Location Marker -->
  <g transform="translate(60, 360)">
    <rect x="0" y="0" width="140" height="28" rx="14" fill="{pal['accent']}" opacity="0.25"/>
    <text x="70" y="19" fill="#FFFFFF" font-family="'Plus Jakarta Sans', sans-serif" font-size="12" font-weight="700" text-anchor="middle" letter-spacing="1">CHAPTER {episode.episode_number}</text>
  </g>

  <text x="60" y="425" fill="#FFFFFF" font-family="'Lora', Georgia, serif" font-size="34" font-weight="700" letter-spacing="-0.5">{safe_title}</text>
  
  <g transform="translate(60, 460)">
    <circle cx="6" cy="6" r="3" fill="{pal['accent']}"/>
    <text x="18" y="10" fill="#94A3B8" font-family="'Plus Jakarta Sans', sans-serif" font-size="13" font-weight="600">{safe_location} · {safe_era}</text>
  </g>
</svg>"""
        return svg.encode("utf-8")

    def build_concise_prompt(self, blueprint: StoryBlueprint, episode: EpisodeResponse) -> str:
        """Constructs a high-impact, fast-rendering cinematic visual prompt."""
        primary_scene = episode.scenes[0] if episode.scenes else None
        location_name = primary_scene.location_key if primary_scene else blueprint.world.city
        time_marker = primary_scene.time_marker if primary_scene else "Night"
        
        genre_vibes = {
            "Mystery & Crime": "cinematic chiaroscuro, warm gas lamps, foggy cobblestone street, moody shadows, realistic novel art",
            "Romance": "warm golden hour lighting, rainy cafe window, romantic atmospheric reflections, painterly realism",
            "Sci-Fi": "neon cyberpunk lighting, holographic glow, futuristic architecture, rain reflections, cinematic 8k",
            "Fantasy": "mystical twilight landscape, glowing arcane castle, starry sky, epic cinematic fantasy art",
            "Historical": "19th century oil painting style, warm candle light, vintage architectural interior, rich textures",
            "Horror": "gothic dark thriller, chilling moonlight, ancient misty mansion, dark silhouette, suspenseful chiaroscuro",
            "Adventure": "sweeping mountain vista, dramatic golden sunlight, majestic wild landscape, epic concept art"
        }
        vibe = genre_vibes.get(blueprint.style.genre, "cinematic lighting, dramatic composition, master novel illustration")
        return f"cinematic 16:9 illustration of {location_name} in {blueprint.world.city}, {time_marker}, {vibe}, highly detailed, wide angle, no text".strip()

    async def generate_ai_free(self, prompt: str) -> Optional[Tuple[bytes, str]]:
        """Generates authentic AI photorealistic/concept art via Pollinations Flux without requiring any API key."""
        try:
            import urllib.parse
            clean_prompt = re.sub(r'[\r\n\t]+', ' ', prompt).strip()
            # 16:9 cinematic aspect ratio: 1024x576, generous 750 char budget for rich scene details
            encoded = urllib.parse.quote(clean_prompt[:750])
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=576&model=flux&nologo=true"
            req = urllib.request.Request(url, headers={"User-Agent": "Storyteller/1.0 (Mozilla/5.0)"})
            loop = asyncio.get_event_loop()

            def _fetch():
                with urllib.request.urlopen(req, timeout=12) as resp:
                    return resp.read(), resp.headers.get("content-type", "image/jpeg")

            data, content_type = await loop.run_in_executor(None, _fetch)
            if data and len(data) > 1000:
                mime = "image/jpeg" if ("jpeg" in content_type or "jpg" in content_type) else ("image/png" if "png" in content_type else "image/jpeg")
                return data, mime
        except Exception as e:
            logger.warning(f"Smart AI image generation note: {e}")
        return None

    async def test_connection(self, provider: str = None, api_key: str = None, model: str = None, base_url: str = None) -> dict:
        """Tests live connectivity to the Image Generation API endpoint."""
        import time
        cfg = store.get_system_settings() or {}
        prov = (provider or cfg.get("image_provider") or "auto").lower()
        key = api_key if api_key is not None else (cfg.get("image_api_key") or cfg.get("api_key") or "")
        mod = model or cfg.get("image_model") or ""
        url = base_url if base_url is not None else (cfg.get("image_base_url") or cfg.get("base_url") or "")

        if prov == "thematic":
            return {
                "success": True,
                "latency_ms": 5,
                "message": "Offline Thematic Vector Art Engine active (zero external API or internet required).",
                "model": "svg-vector-engine"
            }

        if prov == "auto":
            start = time.time()
            test_prompt = "cinematic wide atmospheric library at dusk, warm lighting"
            ai_res = await self.generate_ai_free(test_prompt)
            latency = int((time.time() - start) * 1000)
            if ai_res:
                return {
                    "success": True,
                    "latency_ms": latency,
                    "message": "Smart AI (Flux / Free Online Concept Art) connected successfully.",
                    "model": "flux-pollinations"
                }
            return {
                "success": False,
                "latency_ms": latency,
                "error": "Smart AI service could not be reached. Local vector art fallback will be used."
            }

        if prov == "gemini":
            start = time.time()
            target_model = mod or "imagen-3.0-generate-002"
            try:
                from google import genai
                client = genai.Client(api_key=key)
                res = client.models.generate_images(
                    model=target_model,
                    prompt="A vintage leather journal on an antique desk, warm lighting, cinematic 16:9",
                    config=dict(number_of_images=1, aspect_ratio="16:9")
                )
                latency = int((time.time() - start) * 1000)
                if res.generated_images:
                    return {
                        "success": True,
                        "latency_ms": latency,
                        "message": f"Gemini Imagen connected successfully! Generated sample with {target_model}.",
                        "model": target_model
                    }
                return {
                    "success": False,
                    "latency_ms": latency,
                    "error": "No image returned by Gemini Imagen."
                }
            except Exception as e:
                latency = int((time.time() - start) * 1000)
                return {
                    "success": False,
                    "latency_ms": latency,
                    "error": str(e)
                }

        # Custom API or OpenAI
        start = time.time()
        target_model = mod or ("dall-e-3" if prov == "openai" else "dall-e-3")
        target_url = url or ("https://api.openai.com/v1" if prov == "openai" else None)
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=key or "dummy", base_url=target_url, timeout=30.0)
            response = await client.images.generate(
                model=target_model,
                prompt="A vintage leather-bound book on a wooden desk, warm golden hour light, cinematic illustration",
                size="1024x1024",
                quality="standard",
                n=1
            )
            latency = int((time.time() - start) * 1000)
            if response.data and (getattr(response.data[0], "url", None) or getattr(response.data[0], "b64_json", None)):
                return {
                    "success": True,
                    "latency_ms": latency,
                    "message": f"Image API connected successfully! Generated image via {target_model}.",
                    "model": target_model
                }
            return {
                "success": False,
                "latency_ms": latency,
                "error": "No image data received in API response."
            }
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return {
                "success": False,
                "latency_ms": latency,
                "error": str(e)
            }

    async def generate(self, blueprint: StoryBlueprint, episode: EpisodeResponse) -> Tuple[bytes, str, str]:
        """
        Synthesizes an authentic chapter-specific illustration capturing the pivotal dramatic scene.
        Returns: (image_bytes, mime_type, prompt_used)
        """
        vivid_prompt = await self.craft_vivid_chapter_prompt(blueprint, episode)
        cfg = store.get_system_settings() or {}
        img_provider = (cfg.get("image_provider") or "auto").lower()
        img_key = cfg.get("image_api_key") or cfg.get("api_key") or ""
        img_base_url = cfg.get("image_base_url") or cfg.get("base_url") or ""
        img_model = cfg.get("image_model") or ""

        # 1. Custom or OpenAI Dedicated API (only if specifically configured with an image model)
        is_dedicated_image_endpoint = bool(img_provider in ("openai", "custom") and img_model and any(k in img_model.lower() for k in ("dall", "image", "flux", "diffusion", "sdxl")))
        if is_dedicated_image_endpoint and img_key:
            target_model = img_model or "dall-e-3"
            target_base_url = img_base_url or ("https://api.openai.com/v1" if img_provider == "openai" else None)
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=img_key, base_url=target_base_url, timeout=20.0, max_retries=0)
                logger.info(f"Generating chapter illustration with {target_model} via {target_base_url or 'default endpoint'}...")
                response = await client.images.generate(
                    model=target_model,
                    prompt=vivid_prompt[:1000],
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                if response.data:
                    first = response.data[0]
                    if getattr(first, "b64_json", None):
                        image_bytes = base64.b64decode(first.b64_json)
                        return image_bytes, "image/png", vivid_prompt
                    elif getattr(first, "url", None):
                        img_url = first.url
                        loop = asyncio.get_event_loop()

                        def _fetch():
                            req = urllib.request.Request(img_url, headers={"User-Agent": "Storyteller/1.0"})
                            with urllib.request.urlopen(req, timeout=25) as resp:
                                return resp.read()

                        image_bytes = await loop.run_in_executor(None, _fetch)
                        return image_bytes, "image/jpeg", vivid_prompt
            except Exception as e:
                logger.warning(f"Image API error ({img_provider} - {target_model}): {e}. Seamlessly falling back.")

        # 2. Google Gemini Imagen
        if img_provider == "gemini" and img_key:
            target_model = img_model or "imagen-3.0-generate-002"
            try:
                from google import genai
                client = genai.Client(api_key=img_key)
                logger.info(f"Generating chapter illustration with Google Gemini Imagen ({target_model})...")
                res = client.models.generate_images(
                    model=target_model,
                    prompt=vivid_prompt,
                    config=dict(number_of_images=1, aspect_ratio="16:9")
                )
                if res.generated_images:
                    return res.generated_images[0].image.image_bytes, "image/jpeg", vivid_prompt
            except Exception as e:
                logger.warning(f"Gemini Imagen error ({target_model}): {e}. Seamlessly falling back.")

        # 3. Smart AI Generator (Pollinations Flux: Free, fast, realistic AI concept art, 0 keys needed)
        if img_provider != "thematic":
            ai_res = await self.generate_ai_free(vivid_prompt)
            if ai_res:
                data, mime = ai_res
                return data, mime, vivid_prompt

        # 4. Fallback to local high-fidelity thematic vector artwork
        svg_bytes = self.generate_thematic_svg(blueprint, episode)
        return svg_bytes, "image/svg+xml", vivid_prompt

chapter_image_client = ChapterImageClient()

