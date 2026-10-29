import os
import time
import asyncio
import logging
import requests
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.config import settings
from app.storage.store import store
from app.engine.llm_client import llm, clean_and_parse_json

logger = logging.getLogger(__name__)

class CulturalAffinityItem(BaseModel):
    title: str = Field(..., description="Name of book, film, destination, or artist")
    category: str = Field(..., description="Category: book, movie, place, artist, or tag")
    affinity_reason: str = Field("", description="Why this matches the user's cultural tastes")
    icon: str = Field("book", description="Icon hint: book, film, map-pin, music")

class StoryScenario(BaseModel):
    id: str = Field(..., description="Scenario identifier")
    title: str = Field(..., description="Evocative book title")
    genre: str = Field(..., description="Primary genre")
    tone: str = Field(..., description="Narrative tone")
    prose_style: str = Field("Literary", description="Prose style")
    logline: str = Field(..., description="One-sentence high concept logline")
    premise: str = Field(..., description="Full multi-sentence premise and core conflict")
    hook: str = Field(..., description="Opening dramatic question or inciting incident")
    city: str = Field(..., description="Primary city or world setting")
    country: str = Field(..., description="Country or realm")
    era: str = Field("Contemporary", description="Time period or era")
    protagonist_name: str = Field(..., description="Protagonist name")
    protagonist_role: str = Field(..., description="Protagonist profession or role")
    protagonist_archetype: str = Field(..., description="Character archetype")
    conflict: str = Field(..., description="Core internal and external conflict")
    inspirations_summary: str = Field("", description="How user tastes and Qloo cultural signals inspired this premise")

class QlooClient:
    def __init__(self):
        self._refresh_config()

    def _refresh_config(self):
        saved = store.get_system_settings() or {}
        self.api_key = (saved.get("qloo_api_key") or settings.qloo_api_key or "").strip()
        self.base_url = (saved.get("qloo_base_url") or settings.qloo_base_url or "https://hackathon.api.qloo.com").rstrip("/")
        self.enabled = saved.get("qloo_enabled", settings.qloo_enabled)

    @property
    def is_available(self) -> bool:
        self._refresh_config()
        return bool(self.enabled and self.api_key)

    def _headers(self, key_override: Optional[str] = None) -> Dict[str, str]:
        key = key_override if key_override is not None else self.api_key
        return {
            "X-Api-Key": key,
            "Accept": "application/json"
        }

    def search_entities(self, query: str, entity_type: Optional[str] = None, timeout: int = 8) -> List[Dict[str, Any]]:
        """Searches Qloo entity catalog for books, movies, artists, or locations."""
        self._refresh_config()
        if not self.is_available or not query.strip():
            return []

        url = f"{self.base_url}/search"
        params: Dict[str, Any] = {"query": query.strip()}
        if entity_type:
            params["types"] = entity_type

        try:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("results", []) or data.get("entities", [])
            else:
                logger.warning(f"Qloo /search returned HTTP {resp.status_code}: {resp.text[:200]}")
                return []
        except Exception as e:
            logger.warning(f"Qloo /search exception: {e}")
            return []

    def get_insights(self, filter_type: str, signal_entities: Optional[List[str]] = None, signal_tags: Optional[List[str]] = None, timeout: int = 10) -> List[Dict[str, Any]]:
        """Queries Qloo /v2/insights for cultural recommendations and affinity graphs."""
        self._refresh_config()
        if not self.is_available:
            return []

        url = f"{self.base_url}/v2/insights"
        params: Dict[str, Any] = {"filter.type": filter_type}
        if signal_entities:
            params["signal.interests.entities"] = ",".join(signal_entities)
        if signal_tags:
            params["signal.interests.tags"] = ",".join(signal_tags)

        try:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("entities", []) or data.get("results", [])
            else:
                logger.warning(f"Qloo /v2/insights returned HTTP {resp.status_code}: {resp.text[:200]}")
                return []
        except Exception as e:
            logger.warning(f"Qloo /v2/insights exception: {e}")
            return []

    def test_connection(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> Dict[str, Any]:
        """Validates API credentials against Qloo hackathon base URL."""
        test_key = (api_key if api_key is not None else self.api_key).strip()
        test_url = (base_url or self.base_url or "https://hackathon.api.qloo.com").rstrip("/")

        if not test_key:
            return {
                "success": False,
                "message": "Missing API Key. Please provide your Qloo hackathon API key.",
                "latency_ms": 0
            }

        start = time.time()
        url = f"{test_url}/search"
        headers = {"X-Api-Key": test_key, "Accept": "application/json"}
        params = {"query": "Dune", "types": "urn:entity:book"}

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=12)
            latency = int((time.time() - start) * 1000)

            if resp.status_code == 200:
                return {
                    "success": True,
                    "message": "Connected successfully to Qloo Hackathon Taste API!",
                    "endpoint": test_url,
                    "latency_ms": latency
                }
            elif resp.status_code == 401:
                return {
                    "success": False,
                    "message": "Authentication failed (HTTP 401). Verify that your key is valid and base URL is set to https://hackathon.api.qloo.com",
                    "latency_ms": latency,
                    "status_code": 401
                }
            elif resp.status_code == 403:
                return {
                    "success": False,
                    "message": f"Access forbidden (HTTP 403): {resp.text[:150]}",
                    "latency_ms": latency,
                    "status_code": 403
                }
            else:
                return {
                    "success": False,
                    "message": f"Server returned HTTP {resp.status_code}: {resp.text[:150]}",
                    "latency_ms": latency,
                    "status_code": resp.status_code
                }
        except requests.exceptions.RequestException as e:
            latency = int((time.time() - start) * 1000)
            return {
                "success": False,
                "message": f"Network connection error: {str(e)}",
                "latency_ms": latency
            }

    def discover_cultural_affinities(
        self,
        books: List[str],
        movies: List[str],
        locations: List[str],
        target_count: int = 5
    ) -> List[CulturalAffinityItem]:
        """
        Discovers 5 high-affinity cultural recommendations across books, films, and locations
        based on user interests using Qloo's taste graph or intelligent curated fallbacks.
        """
        self._refresh_config()
        clean_books = [b.strip() for b in books if b and b.strip()]
        clean_movies = [m.strip() for m in movies if m and m.strip()]
        clean_locations = [loc.strip() for loc in locations if loc and loc.strip()]

        discovered: List[CulturalAffinityItem] = []

        # If live Qloo is available, query real entity search & insights
        if self.is_available and (clean_books or clean_movies or clean_locations):
            entity_ids = []
            # 1. Search for book entity IDs
            for b in clean_books[:2]:
                res = self.search_entities(b, "urn:entity:book")
                if res and isinstance(res, list) and len(res) > 0:
                    eid = res[0].get("id") or res[0].get("entity_id")
                    if eid:
                        entity_ids.append(str(eid))

            # 2. Search for movie entity IDs
            for m in clean_movies[:2]:
                res = self.search_entities(m, "urn:entity:movie")
                if res and isinstance(res, list) and len(res) > 0:
                    eid = res[0].get("id") or res[0].get("entity_id")
                    if eid:
                        entity_ids.append(str(eid))

            # 3. Query insights across books and movies
            if entity_ids:
                book_recs = self.get_insights("urn:entity:book", signal_entities=entity_ids[:3])
                for item in book_recs[:3]:
                    name = item.get("name") or item.get("title")
                    if name and name.lower() not in [b.lower() for b in clean_books]:
                        desc = item.get("description") or "Shared atmospheric, thematic, and stylistic resonance"
                        discovered.append(CulturalAffinityItem(
                            title=name,
                            category="book",
                            affinity_reason=desc,
                            icon="book"
                        ))

                movie_recs = self.get_insights("urn:entity:movie", signal_entities=entity_ids[:3])
                for item in movie_recs[:3]:
                    name = item.get("name") or item.get("title")
                    if name and name.lower() not in [m.lower() for m in clean_movies]:
                        desc = item.get("description") or "Shared visual tension, pacing, and mood palette"
                        discovered.append(CulturalAffinityItem(
                            title=name,
                            category="movie",
                            affinity_reason=desc,
                            icon="film"
                        ))

        # If discovered items are fewer than target_count, supplement with intelligent literary & cinematic affinities
        if len(discovered) < target_count:
            fallbacks = self._generate_intelligent_affinities(clean_books, clean_movies, clean_locations)
            for fb in fallbacks:
                if not any(d.title.lower() == fb.title.lower() for d in discovered):
                    discovered.append(fb)
                if len(discovered) >= target_count:
                    break

        return discovered[:target_count]

    def _generate_intelligent_affinities(
        self,
        books: List[str],
        movies: List[str],
        locations: List[str]
    ) -> List[CulturalAffinityItem]:
        """Provides rich contextual cultural affinities synthesized for literary fiction."""
        all_inputs = " ".join(books + movies + locations).lower()

        pool = [
            CulturalAffinityItem(
                title="The Shadow of the Wind (Carlos Ruiz Zafon)",
                category="book",
                affinity_reason="Labyrinthine gothic mystery, rare manuscripts, and haunting forgotten cities",
                icon="book"
            ),
            CulturalAffinityItem(
                title="Blade Runner 2049 (Denis Villeneuve)",
                category="movie",
                affinity_reason="Atmospheric neon-noir existentialism, identity inquiry, and sweeping visual stillness",
                icon="film"
            ),
            CulturalAffinityItem(
                title="Old Town & Underground Vaults, Edinburgh",
                category="place",
                affinity_reason="Cobblestone mist, historical intrigue, hidden architectural strata, and brooding tension",
                icon="map-pin"
            ),
            CulturalAffinityItem(
                title="Tinker Tailor Soldier Spy (John le Carre)",
                category="book",
                affinity_reason="Layered psychological chess, quiet betrayal, bureaucratic coldness, and guarded secrets",
                icon="book"
            ),
            CulturalAffinityItem(
                title="In the Mood for Love (Wong Kar-wai)",
                category="movie",
                affinity_reason="Hypnotic longing, unspoken emotional currents, opulent textures, and lingering melancholy",
                icon="film"
            ),
            CulturalAffinityItem(
                title="The Secret History (Donna Tartt)",
                category="book",
                affinity_reason="Dark academia aesthetics, moral degradation, cloistered intellectual obsession, and tragic guilt",
                icon="book"
            ),
            CulturalAffinityItem(
                title="Chinatown (Roman Polanski)",
                category="movie",
                affinity_reason="Intricate systemic corruption, deception, sun-bleached tragedy, and fatalistic pursuit of truth",
                icon="film"
            ),
            CulturalAffinityItem(
                title="Montmartre & Canal Saint-Martin, Paris",
                category="place",
                affinity_reason="Bohemian artistic reverie, melancholic rain-swept alleys, and intimate rendezvous",
                icon="map-pin"
            )
        ]

        # Prioritize items sharing thematic tone
        if any(w in all_inputs for w in ["future", "cyber", "sci-fi", "space", "robot", "tech", "dune"]):
            pool.insert(0, CulturalAffinityItem(
                title="Neuromancer (William Gibson)",
                category="book",
                affinity_reason="Groundbreaking cyberpunk pulse, high-tech desperation, and sensory grit",
                icon="book"
            ))
        if any(w in all_inputs for w in ["detective", "murder", "crime", "investigate", "sherlock"]):
            pool.insert(0, CulturalAffinityItem(
                title="The Girl with the Dragon Tattoo (Stieg Larsson)",
                category="book",
                affinity_reason="Relentless forensic investigation, Nordic frost, and buried corporate atrocities",
                icon="book"
            ))

        return pool

    def enrich_character_cultural_dossier(self, role: str, archetype: str, era: str) -> Dict[str, Any]:
        """Provides character cultural taste markers (music, literature, aesthetic habits) based on persona."""
        self._refresh_config()
        role_lower = (role or "").lower()
        arch_lower = (archetype or "").lower()

        if "scholar" in role_lower or "intellectual" in arch_lower:
            return {
                "reading_tastes": ["Classical political philosophy", "Rare archival periodicals", "Gothic antiquities"],
                "musical_temperament": "Baroque cello suites, melancholic solo piano",
                "aesthetic_hallmarks": "Iron gall ink stains, tweed lapels, vintage brass pocket watch"
            }
        elif "detective" in role_lower or "investigator" in role_lower:
            return {
                "reading_tastes": ["Forensic case law", "Local municipal maps", "Hardboiled crime fiction"],
                "musical_temperament": "Cool midnight jazz, muted trumpet, slow rain ambiance",
                "aesthetic_hallmarks": "Heavy woolen trench coat, dog-eared field notebook, cold black coffee"
            }
        elif "operative" in role_lower or "rebel" in arch_lower:
            return {
                "reading_tastes": ["Cryptographic treatises", "Underground pamphlets", "Urban architecture blueprints"],
                "musical_temperament": "Industrial synth-wave, low-frequency atmospheric drones",
                "aesthetic_hallmarks": "Tactical matte-black hardware, unbranded waterproof garments, silent footsteps"
            }
        else:
            return {
                "reading_tastes": ["Modern literary memoirs", "Psychological drama", "Historical diaries"],
                "musical_temperament": "Acoustic folk, ambient chamber orchestrations",
                "aesthetic_hallmarks": "Handmade leather journals, tailored linen coats, quiet observational pauses"
            }

    def enrich_location_cultural_texture(self, city: str, country: str, era: str) -> Dict[str, str]:
        """Generates authentic sensory and cultural cues for world locations."""
        c = (city or "").lower()
        if "edinburgh" in c or "scotland" in (country or "").lower():
            return {
                "sensory_textures": "Smell of damp sandstone, coal hearth smoke, peat-stained rain, and yellow streetlamps cutting through dense haar mist.",
                "cultural_milieu": "Steep wynds, hidden vaults beneath Georgian crescents, theological debates in wood-paneled taverns."
            }
        elif "paris" in c or "france" in (country or "").lower():
            return {
                "sensory_textures": "Aroma of roasted espresso, wet zinc rooftops, damp boxwood in Luxembourg Gardens, and faint Gauloises tobacco.",
                "cultural_milieu": "Intimate bistro corners, boulevard cafe terraces, secondhand bookstalls along the Seine, whispered artistic alliances."
            }
        elif "tokyo" in c or "japan" in (country or "").lower() or "kyoto" in c:
            return {
                "sensory_textures": "Scent of hinoki cypress wood, damp asphalt after torrential monsoon rain, ozone from elevated subway lines, and cold green tea.",
                "cultural_milieu": "Narrow alleys illuminated by paper red lanterns, neon reflections on wet crosswalks, quiet bamboo shrines tucked between steel skyscrapers."
            }
        else:
            return {
                "sensory_textures": f"Distinctive sensory rhythm of {city}: weathered limestone, rain-slicked pavement, distant harbor horns, and evening shadows.",
                "cultural_milieu": f"Local cafes, historic civic architecture, and tucked-away courtyards shaped by generations of {era} culture."
            }

    def analyze_author_taste_profile(self, books: List[str], movies: List[str]) -> Dict[str, Any]:
        """
        Analyzes an author's favorite books and films to build a personal cultural identity,
        recommending matching novel genres, aesthetic archetypes, and cultural affinities via Qloo.
        """
        clean_books = [b.strip() for b in books if b and b.strip()][:5]
        clean_movies = [m.strip() for m in movies if m and m.strip()][:5]

        if not clean_books and not clean_movies:
            return {
                "archetype": "Eclectic Story Architect",
                "aesthetic_archetype": "Eclectic Story Architect",
                "recommended_genres": ["Literary Fiction", "Mystery & Crime", "Speculative Drama"],
                "recommended_tones": ["Atmospheric", "Tense", "Reflective"],
                "cultural_affinities": [],
                "suggested_world_settings": ["Edinburgh", "Paris", "Kyoto"],
                "summary": "Open creative canvas ready to explore diverse genres and character-driven narratives."
            }

        affinities = self.discover_cultural_affinities(clean_books, clean_movies, [], target_count=5)
        combined_text = " ".join(clean_books + clean_movies).lower()

        # Determine author aesthetic archetype based on tastes
        if any(w in combined_text for w in ["blade runner", "cyber", "future", "dune", "sci-fi", "matrix", "solaris", "1984"]):
            archetype = "Visionary Speculative Architect"
            genres = ["Sci-Fi & Speculative", "Cyberpunk / Tech Noir", "Dystopian Mystery"]
            tones = ["Brooding & Atmospheric", "Philosophical", "Tense"]
            settings = ["Neo-Tokyo", "London 2045", "Isolated Research Station"]
            summary = "Drawn to high-stakes existential questions, technological frontiers, and atmospheric neo-noir worldbuilding."
        elif any(w in combined_text for w in ["shadow of the wind", "gothic", "frankenstein", "dracula", "poe", "secret history", "dark academia"]):
            archetype = "Gothic & Dark Academia Chronicler"
            genres = ["Gothic Mystery", "Literary Drama", "Historical Thriller"]
            tones = ["Eerie & Haunting", "Introspective", "Melancholic"]
            settings = ["Edinburgh Old Town", "Oxford College Quads", "Victorian Prague"]
            summary = "Fascinated by forgotten archives, intellectual obsessions, hidden guilt, and atmospheric historical settings."
        elif any(w in combined_text for w in ["chinatown", "detective", "sherlock", "noir", "crime", "investigation", "godfather", "tinker tailor"]):
            archetype = "Master of Intrigue & Moral Ambiguity"
            genres = ["Mystery & Crime", "Political Espionage", "Noir Thriller"]
            tones = ["Tense & Calculated", "Cynical yet Searching", "Suspenseful"]
            settings = ["Cold War Berlin", "1940s Los Angeles", "Misty Maritime Wharfs"]
            summary = "Excels at intricate chess-game plots, buried systemic corruption, and morally complex protagonists."
        elif any(w in combined_text for w in ["mood for love", "gatsby", "romance", "pride", "normal people", "call me by your name", "interstellar"]):
            archetype = "Lyrical Humanist & Emotional Realist"
            genres = ["Literary Romance", "Character Drama", "Contemporary Odyssey"]
            tones = ["Poignant & Bittersweet", "Lyrical", "Tender"]
            settings = ["Autumn in Saint-Germain", "Coastal Mediterranean", "Rainy Lisbon"]
            summary = "Focused on deep emotional undercurrents, the fragility of memory, and unforgettable interpersonal connections."
        else:
            archetype = "Literary Stylist & Atmospheric Realist"
            genres = ["Literary Fiction", "Psychological Suspense", "Mystery & Crime"]
            tones = ["Measured & Evocative", "Richly Textured", "Observant"]
            settings = ["Edinburgh", "Paris", "New York Harbor"]
            summary = "Grounded in sensory textures, strong character psychologies, and resonant narrative prose."

        return {
            "archetype": archetype,
            "aesthetic_archetype": archetype,
            "recommended_genres": genres,
            "recommended_tones": tones,
            "cultural_affinities": [a.model_dump() for a in affinities],
            "suggested_world_settings": settings,
            "summary": summary
        }

qloo_client = QlooClient()

async def generate_scenarios_from_tastes(
    books: List[str],
    movies: List[str],
    locations: List[str]
) -> Dict[str, Any]:
    """
    Main entry point: Discovers 5 high-affinity cultural items from Qloo,
    then prompts LLM (or mock simulator) to generate 3 rich, distinct book scenarios.
    """
    affinities = qloo_client.discover_cultural_affinities(books, movies, locations, target_count=5)

    user_tastes_summary = []
    if books:
        user_tastes_summary.append(f"Favorite Books: {', '.join(books)}")
    if movies:
        user_tastes_summary.append(f"Favorite Movies: {', '.join(movies)}")
    if locations:
        user_tastes_summary.append(f"Favorite Locations: {', '.join(locations)}")
    user_tastes_str = " | ".join(user_tastes_summary) if user_tastes_summary else "General Literary & Mystery"

    qloo_affinity_str = "\n".join([
        f"- [{item.category.upper()}] {item.title}: {item.affinity_reason}"
        for item in affinities
    ])

    system_prompt = """You are an elite literary scout and master story architect.
Your task is to analyze an author's cultural tastes and Qloo's cultural affinity graph to synthesize EXACTLY THREE (3) distinct, highly captivating, mature book scenarios.

EACH SCENARIO MUST EXPLORE A UNIQUE ANGLE:
- Scenario 1 (Intrigue & Mystery / Noir): Focus on secrets, high stakes investigation, psychological deception, or hidden truths.
- Scenario 2 (Atmospheric & Suspense / Speculative): Focus on brooding environmental tension, aesthetic worldbuilding, moral ambiguity, or unexpected crossroads.
- Scenario 3 (Literary Drama & Deep Odyssey): Focus on profound emotional currents, interpersonal friction, character transformation, and unforgettable relationships.

Return STRICTLY valid JSON conforming to the requested schema. No prose outside the JSON."""

    user_prompt = f"""AUTHOR'S CULTURAL TASTE PROFILE:
{user_tastes_str}

QLOO CULTURAL TASTE AFFINITIES (DISCOVERED MATCHES):
{qloo_affinity_str}

Generate 3 complete novel writing scenarios based on these cultural intersections.
Return JSON in this exact structure:
{{
  "scenarios": [
    {{
      "id": "scenario_1",
      "title": "Evocative Title",
      "genre": "Mystery & Crime",
      "tone": "Tense & Suspenseful",
      "prose_style": "Literary",
      "logline": "One compelling sentence hook summarizing protagonist, stakes, and catalyst.",
      "premise": "Full three-to-four sentence narrative premise outlining the setup, primary conflict, and what is at stake.",
      "hook": "Opening dramatic scene or shocking inciting discovery.",
      "city": "Specific City or Region",
      "country": "Country",
      "era": "Contemporary or Historic Era",
      "protagonist_name": "Full Name",
      "protagonist_role": "Profession or Position",
      "protagonist_archetype": "Psychological Archetype",
      "conflict": "Central internal moral struggle versus external antagonist force.",
      "inspirations_summary": "How specific cultural elements from Qloo (e.g. books/films/cities) were fused into this premise."
    }},
    ...
  ]
}}"""

    if llm.provider == "mock" or (not llm.api_key and llm.provider not in ("ollama", "custom")):
        scenarios = _generate_mock_scenarios(books, movies, locations, affinities)
    else:
        async def fallback():
            return {"scenarios": [s.model_dump() for s in _generate_mock_scenarios(books, movies, locations, affinities)]}

        try:
            data = await asyncio.wait_for(
                llm.generate_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    fallback_generator=fallback
                ),
                timeout=15.0
            )
            scenarios_raw = data.get("scenarios", []) if isinstance(data, dict) else []
            scenarios = []
            for idx, sc in enumerate(scenarios_raw[:3], 1):
                if isinstance(sc, dict):
                    sc["id"] = sc.get("id") or f"scenario_{idx}"
                    scenarios.append(StoryScenario(**sc))

            if len(scenarios) < 3:
                scenarios = _generate_mock_scenarios(books, movies, locations, affinities)
        except Exception as e:
            logger.warning(f"Notice: generating scenarios fallback engaged: {e}")
            scenarios = _generate_mock_scenarios(books, movies, locations, affinities)

    return {
        "user_tastes": {
            "books": books,
            "movies": movies,
            "locations": locations
        },
        "similar_items": [item.model_dump() for item in affinities],
        "scenarios": [s.model_dump() for s in scenarios]
    }

def _generate_mock_scenarios(
    books: List[str],
    movies: List[str],
    locations: List[str],
    affinities: List[CulturalAffinityItem]
) -> List[StoryScenario]:
    """Fallback generator that synthesizes 3 tailored scenarios even when offline."""
    fav_loc = locations[0] if locations else "Edinburgh"
    fav_book = books[0] if books else "The Shadow of the Wind"
    fav_movie = movies[0] if movies else "Blade Runner"

    return [
        StoryScenario(
            id="scenario_1",
            title=f"The Cartographer of {fav_loc}",
            genre="Mystery & Crime",
            tone="Tense & Atmospheric",
            prose_style="Literary",
            logline=f"An archival restorer discovers a hand-drawn map of {fav_loc} annotated with unsolved disappearances spanning three decades.",
            premise=f"When rare book conservator Julian Vance receives an anonymous bequest containing an uncatalogued eighteenth-century atlas of {fav_loc}, he assumes it is an eccentric collector's prank. But each folded vellum plate marks the exact coordinates of prominent citizens who vanished without a trace. As cold rain sweeps the streets, Julian realizes whoever drew the missing routes is now mapping his own daily movements.",
            hook="A wax-sealed parchment arrives at midnight, still smelling of damp river mud and sulfur.",
            city=fav_loc,
            country="United Kingdom",
            era="Late Autumn, Contemporary",
            protagonist_name="Julian Vance",
            protagonist_role="Archival Conservator",
            protagonist_archetype="Recluse Scholar & Reluctant Investigator",
            conflict="Must expose a generation-old institutional conspiracy while confronting his own complicity in burying his family's records.",
            inspirations_summary=f"Synthesizes the antiquarian manuscript obsession of {fav_book} with the brooding urban tension of {fav_loc}."
        ),
        StoryScenario(
            id="scenario_2",
            title="The Obsidian Echoes",
            genre="Sci-Fi & Speculative",
            tone="Brooding & Melancholic",
            prose_style="Lyrical & Cinematic",
            logline="In a neon-glazed coastal metropolis, a memory extractor begins recovering forbidden recollections belonging to an architect who never existed.",
            premise=f"Deep in the fog-drenched districts of {fav_loc}, memory archivist Vesper Cole extracts sensory memories for dying clients seeking digital absolution. When an unidentified terminal patient dies in her clinic, Vesper intercepts an encrypted synaptic imprint showing architectural monuments of a city identical to {fav_loc}—except this version burned down a century ago. Hunted by city enforcement, she must reconstruct the ghost architect's final blueprint.",
            hook="A client's pulse flatlines on the sensory recliner, leaving an unsanctioned holographic memory burning behind Vesper's retina.",
            city=fav_loc,
            country="Autonomous Maritime Basin",
            era="Near-Future 2048",
            protagonist_name="Vesper Cole",
            protagonist_role="Neural Memory Archivist",
            protagonist_archetype="Cautious Cynic with Buried Empathy",
            conflict="Protecting a dangerous metaphysical truth that could tear apart the city's synthetic peace versus erasing the memories to save herself.",
            inspirations_summary=f"Draws from the visual existentialism of {fav_movie} and Qloo's noir-affinity signals."
        ),
        StoryScenario(
            id="scenario_3",
            title="A Winter in Saint-Germain",
            genre="Literary Drama",
            tone="Poignant & Bittersweet",
            prose_style="Poetic & Measured",
            logline="Two estranged translators reunite across the rainy bridges of Europe to decipher the unsent letters of a poet whose silence broke their youth.",
            premise=f"Ten years after an artistic betrayal scattered their tight-knit translation circle, Clara Sterling and Gabriel Moreau find themselves stranded in the winter avenues of {fav_loc}. Tasked with editing the posthumous papers of their late mentor, each discovered letter challenges their memory of the tragic night everything fell apart. Between long silences and rain-slicked cobblestones, they must decide whether forgiveness is worth unraveling their carefully rebuilt lives.",
            hook="An unopened telegram postmarked November 1994 falls from the spine of a water-damaged poetry anthology.",
            city=fav_loc,
            country="France",
            era="Winter 1999",
            protagonist_name="Clara Sterling",
            protagonist_role="Literary Translator",
            protagonist_archetype="Guarded Perfectionist",
            conflict="Facing the unresolved emotional truth of her first love versus clinging to the safety of self-imposed exile.",
            inspirations_summary=f"Inspired by the melancholic intimacy of European arthouse cinema and lyrical character-driven prose."
        )
    ]
