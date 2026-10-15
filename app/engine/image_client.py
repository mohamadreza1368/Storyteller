import os
import re
import json
import base64
import logging
import urllib.request
from typing import Tuple, Optional
from app.models.blueprint import StoryBlueprint
from app.models.episode import EpisodeResponse
from app.storage.store import store

logger = logging.getLogger("storyteller.image")

class ChapterImageClient:
    """Handles visual illustration generation for novel chapters."""

    def build_chapter_prompt(self, blueprint: StoryBlueprint, episode: EpisodeResponse) -> str:
        """Constructs an evocative cinematic art prompt based on the chapter's atmosphere."""
        primary_scene = episode.scenes[0] if episode.scenes else None
        location_name = primary_scene.location_key if primary_scene else blueprint.world.city
        time_marker = primary_scene.time_marker if primary_scene else "Night"
        conflict = primary_scene.conflict if primary_scene else episode.summary
        goal = primary_scene.goal if primary_scene else ""

        # Find matching location description from blueprint
        loc_desc = ""
        for loc in blueprint.world.locations:
            if loc.name.lower() in location_name.lower():
                loc_desc = loc.description
                break

        # Genre-specific aesthetic styles
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

        prompt = (
            f"Cinematic wide 16:9 novel illustration for a {blueprint.style.genre} story. "
            f"Setting: {location_name} in {blueprint.world.city}, {blueprint.world.era}. {loc_desc} "
            f"Atmosphere: {time_marker}, {blueprint.style.tone} mood. "
            f"Dramatic moment: {conflict}. "
            f"Style: {style_hint}. Masterpiece digital concept art, epic composition, photorealistic textures, no text, no captions, no watermarks."
        )
        return prompt.strip()

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

    async def generate(self, blueprint: StoryBlueprint, episode: EpisodeResponse) -> Tuple[bytes, str, str]:
        """
        Synthesizes an illustration for the chapter.
        Returns: (image_bytes, mime_type, prompt_used)
        """
        prompt = self.build_chapter_prompt(blueprint, episode)
        cfg = store.get_system_settings()
        prov = cfg.get("provider", "mock")
        key = cfg.get("api_key", "")
        base_url = cfg.get("base_url", "")

        # Try Live Image Provider if configured
        if prov in ("openai", "custom") and key:
            try:
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=key, base_url=base_url or None, timeout=40.0)
                logger.info(f"Generating chapter illustration with OpenAI/Custom API: {prompt[:80]}...")
                response = await client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                if response.data and response.data[0].url:
                    img_url = response.data[0].url
                    req = urllib.request.Request(img_url, headers={"User-Agent": "Storyteller/1.0"})
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        image_bytes = resp.read()
                        return image_bytes, "image/jpeg", prompt
            except Exception as e:
                logger.warning(f"Live image generation error ({prov}): {e}. Falling back to thematic artwork.")

        # Fallback to high-fidelity thematic vector artwork
        svg_bytes = self.generate_thematic_svg(blueprint, episode)
        return svg_bytes, "image/svg+xml", prompt

chapter_image_client = ChapterImageClient()
