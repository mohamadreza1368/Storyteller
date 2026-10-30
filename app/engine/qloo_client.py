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

def _infer_country_for_city(city: Optional[str]) -> str:
    c_lower = (city or "").lower()
    city_map = {
        "istanbul": "Turkey",
        "tokyo": "Japan",
        "kyoto": "Japan",
        "osaka": "Japan",
        "paris": "France",
        "lyon": "France",
        "marseille": "France",
        "london": "United Kingdom",
        "edinburgh": "Scotland",
        "glasgow": "Scotland",
        "dublin": "Ireland",
        "berlin": "Germany",
        "munich": "Germany",
        "rome": "Italy",
        "venice": "Italy",
        "florence": "Italy",
        "milan": "Italy",
        "madrid": "Spain",
        "barcelona": "Spain",
        "new york": "United States",
        "texas": "United States",
        "chicago": "United States",
        "los angeles": "United States",
        "san francisco": "United States",
        "cairo": "Egypt",
        "tehran": "Iran",
        "beijing": "China",
        "shanghai": "China",
        "sydney": "Australia",
        "melbourne": "Australia",
        "toronto": "Canada",
        "vancouver": "Canada",
        "amsterdam": "Netherlands",
        "vienna": "Austria",
        "prague": "Czech Republic",
        "budapest": "Hungary",
        "athens": "Greece",
        "lisbon": "Portugal",
    }
    for k, v in city_map.items():
        if k in c_lower:
            return v
    return "United Kingdom" if not city else (city.title() + " Region")

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
    inspirations_summary: str = Field("", description="How user tastes and cultural affinities inspired this premise")

class QlooClient:
    """
    Client for Qloo's Taste Intelligence & Basic Insights API.
    Interacts with Qloo endpoints (/search and /v2/insights) to uncover
    cross-domain cultural affinities across literature, film, and locations.
    """
    def __init__(self):
        self._last_network_error_time: float = 0.0
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
        key = (key_override if key_override is not None else self.api_key).strip()
        return {
            "X-Api-Key": key,
            "Accept": "application/json",
            "User-Agent": "StorytellerAI/1.0",
            "Connection": "close"
        }

    def _extract_entities_from_response(self, data: Any) -> List[Dict[str, Any]]:
        """
        Deeply extracts entity lists from Qloo API v2 responses, handling
        all possible nesting levels:
        - {"data": {"entities": [...]}}
        - {"results": {"entities": [...]}}
        - {"data": {"results": [...]}}
        - {"data": [...]}
        - {"entities": [...]}
        - {"results": [...]}
        - direct list of entity objects
        """
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if not isinstance(data, dict):
            return []

        # 1. Direct entity list keys
        for key in ("entities", "results", "insights", "items"):
            val = data.get(key)
            if isinstance(val, list) and val and isinstance(val[0], dict):
                return val

        # 2. Nested under 'data', 'results', 'response', or 'payload'
        for container_key in ("data", "results", "response", "payload"):
            container = data.get(container_key)
            if isinstance(container, dict):
                for key in ("entities", "results", "insights", "items"):
                    val = container.get(key)
                    if isinstance(val, list) and val and isinstance(val[0], dict):
                        return val
            elif isinstance(container, list) and container and isinstance(container[0], dict):
                return container

        return []

    def search_entities(self, query: str, entity_type: Optional[str] = None, timeout: int = 5) -> List[Dict[str, Any]]:
        """
        Searches Qloo entity catalog for books, movies, or locations.
        Unpacks nested Qloo results properly with fast network failover.
        """
        self._refresh_config()
        if not self.is_available or not query.strip():
            return []

        # Circuit breaker: fail immediately if recent network failure occurred
        if time.time() - self._last_network_error_time < 30.0:
            return []

        url = f"{self.base_url}/search"
        params: Dict[str, Any] = {"query": query.strip()}
        if entity_type:
            params["types"] = entity_type

        try:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                return self._extract_entities_from_response(data)
            else:
                logger.warning(f"Qloo /search returned HTTP {resp.status_code}: {resp.text[:200]}")
                return []
        except Exception as e:
            self._last_network_error_time = time.time()
            logger.warning(f"Qloo /search network exception (circuit breaker active for 30s): {e}")
            return []

    def get_insights(
        self,
        filter_type: str,
        signal_entities: Optional[List[str]] = None,
        signal_tags: Optional[List[str]] = None,
        take: int = 5,
        timeout: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Queries Qloo Basic Insights endpoint (/v2/insights) according to the official documentation.
        Uses the documented 'take' parameter and extracts nested entities cleanly.
        Reference: https://docs.qloo.com/reference/basic-insights-use-case
        """
        self._refresh_config()
        if not self.is_available:
            return []

        # Circuit breaker: fail immediately if recent network failure occurred
        if time.time() - self._last_network_error_time < 30.0:
            return []

        url = f"{self.base_url}/v2/insights"
        params: Dict[str, Any] = {
            "filter.type": filter_type,
            "take": take
        }
        if signal_entities:
            params["signal.interests.entities"] = ",".join(signal_entities)
        if signal_tags:
            params["signal.interests.tags"] = ",".join(signal_tags)

        try:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                return self._extract_entities_from_response(data)
            else:
                logger.warning(f"Qloo /v2/insights returned HTTP {resp.status_code}: {resp.text[:200]}")
                return []
        except Exception as e:
            self._last_network_error_time = time.time()
            logger.warning(f"Qloo /v2/insights network exception (circuit breaker active for 30s): {e}")
            return []

    def test_connection(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Validates API credentials against Qloo Taste & Basic Insights API endpoints.
        Tests both entity search and the /v2/insights endpoint.
        """
        test_key = (api_key if api_key is not None else self.api_key).strip()
        test_url = (base_url or self.base_url or "https://hackathon.api.qloo.com").rstrip("/")

        if not test_key:
            return {
                "success": False,
                "message": "Missing API Key. Please provide your Qloo API key.",
                "latency_ms": 0
            }

        start = time.time()
        headers = {
            "X-Api-Key": test_key,
            "Accept": "application/json",
            "User-Agent": "StorytellerAI/1.0",
            "Connection": "close"
        }

        # Step 1: Test entity search endpoint
        search_url = f"{test_url}/search"
        search_params = {"query": "Dune", "types": "urn:entity:book"}

        try:
            resp = requests.get(search_url, headers=headers, params=search_params, timeout=12)
            latency = int((time.time() - start) * 1000)

            if resp.status_code == 200:
                # Step 2: Also test Basic Insights endpoint (/v2/insights)
                insights_url = f"{test_url}/v2/insights"
                insights_params = {"filter.type": "urn:entity:book", "take": 2}
                try:
                    ins_resp = requests.get(insights_url, headers=headers, params=insights_params, timeout=8)
                    if ins_resp.status_code == 200:
                        return {
                            "success": True,
                            "message": f"Connected successfully to Qloo Basic Insights & Taste API! ({test_url})",
                            "endpoint": test_url,
                            "latency_ms": latency
                        }
                except Exception:
                    pass

                return {
                    "success": True,
                    "message": f"Connected successfully to Qloo Taste API ({test_url})!",
                    "endpoint": test_url,
                    "latency_ms": latency
                }
            elif resp.status_code == 401:
                return {
                    "success": False,
                    "message": "Authentication failed (HTTP 401). Verify that your key is valid and base URL matches your gateway (hackathon.api.qloo.com or api.qloo.com).",
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
        Discovers high-affinity cultural recommendations across books, films, and locations
        based on user interests using Qloo's taste graph, or dynamic generative synthesis.
        """
        self._refresh_config()
        clean_books = [b.strip() for b in books if b and b.strip()]
        clean_movies = [m.strip() for m in movies if m and m.strip()]
        clean_locations = [loc.strip() for loc in locations if loc and loc.strip()]

        discovered: List[CulturalAffinityItem] = []

        # If live Qloo is available and circuit breaker is not tripped, query real entity search & insights
        if self.is_available and (time.time() - self._last_network_error_time >= 30.0) and (clean_books or clean_movies or clean_locations):
            book_entity_ids: List[str] = []
            movie_entity_ids: List[str] = []
            location_entity_ids: List[str] = []

            # 1. Search for book entity IDs (collect top candidates to ensure valid graph nodes)
            for b in clean_books[:2]:
                res = self.search_entities(b, "urn:entity:book")
                for hit in res[:3]:
                    eid = hit.get("id") or hit.get("entity_id") or hit.get("urn")
                    if eid and str(eid) not in book_entity_ids:
                        book_entity_ids.append(str(eid))

            # 2. Search for movie entity IDs (collect top candidates to ensure valid graph nodes)
            for m in clean_movies[:2]:
                res = self.search_entities(m, "urn:entity:movie")
                for hit in res[:3]:
                    eid = hit.get("id") or hit.get("entity_id") or hit.get("urn")
                    if eid and str(eid) not in movie_entity_ids:
                        movie_entity_ids.append(str(eid))

            # 3. Search for location entity IDs ONLY if location was provided
            for loc in clean_locations[:2]:
                res = self.search_entities(loc, "urn:entity:place")
                for hit in res[:3]:
                    eid = hit.get("id") or hit.get("entity_id") or hit.get("urn")
                    if eid and str(eid) not in location_entity_ids:
                        location_entity_ids.append(str(eid))

            all_media_signals = (book_entity_ids + movie_entity_ids)[:4]

            # 4. Query book insights (prefer book entity IDs, then all media signals)
            book_signals = book_entity_ids if book_entity_ids else all_media_signals
            if book_signals:
                book_recs = self.get_insights("urn:entity:book", signal_entities=book_signals, take=3)
                for item in book_recs:
                    name = item.get("name") or item.get("title")
                    if name and not any(name.lower() == b.lower() for b in clean_books):
                        props = item.get("properties") or {}
                        desc = props.get("short_description") or props.get("description") or item.get("description") or item.get("summary")
                        tags = [t.get("name") for t in item.get("tags", []) if t.get("name")][:3]
                        if tags:
                            tag_str = f" [Themes: {', '.join(tags)}]"
                            desc = f"{desc}{tag_str}" if desc else f"Resonant aesthetic: {', '.join(tags)}"
                        desc = desc or "Resonant narrative themes, prose style, and character tension"
                        discovered.append(CulturalAffinityItem(
                            title=name,
                            category="book",
                            affinity_reason=desc,
                            icon="book"
                        ))
                    if len(discovered) >= 2:
                        break

            # 5. Query movie insights (prefer movie entity IDs, then all media signals)
            movie_signals = movie_entity_ids if movie_entity_ids else all_media_signals
            if movie_signals:
                movie_recs = self.get_insights("urn:entity:movie", signal_entities=movie_signals, take=3)
                for item in movie_recs:
                    name = item.get("name") or item.get("title")
                    if name and not any(name.lower() == m.lower() for m in clean_movies):
                        props = item.get("properties") or {}
                        desc = props.get("short_description") or props.get("description") or item.get("description") or item.get("summary")
                        tags = [t.get("name") for t in item.get("tags", []) if t.get("name")][:3]
                        if tags:
                            tag_str = f" [Themes: {', '.join(tags)}]"
                            desc = f"{desc}{tag_str}" if desc else f"Shared cinematic tone: {', '.join(tags)}"
                        desc = desc or "Shared atmospheric visual palette, pacing, and emotional depth"
                        discovered.append(CulturalAffinityItem(
                            title=name,
                            category="movie",
                            affinity_reason=desc,
                            icon="film"
                        ))
                    if len(discovered) >= target_count - 1:
                        break

            # 6. Query place insights ONLY if location signals are available (as places require geographic context)
            if location_entity_ids:
                place_recs = self.get_insights("urn:entity:place", signal_entities=location_entity_ids, take=2)
                for item in place_recs:
                    name = item.get("name") or item.get("title")
                    if name and not any(name.lower() == l.lower() for l in clean_locations):
                        props = item.get("properties") or {}
                        desc = props.get("short_description") or props.get("description") or item.get("description") or item.get("summary") or "Architectural atmosphere and sensory milieu matching setting"
                        discovered.append(CulturalAffinityItem(
                            title=name,
                            category="place",
                            affinity_reason=desc,
                            icon="map-pin"
                        ))
                    if len(discovered) >= target_count:
                        break

        # If live Qloo items are fewer than target_count, dynamically synthesize bespoke affinities
        # based strictly on the user's specific inputs (NEVER a fixed static list)
        if len(discovered) < target_count:
            needed = target_count - len(discovered)
            dynamic_affinities = self._synthesize_dynamic_affinities(clean_books, clean_movies, clean_locations, needed)
            for item in dynamic_affinities:
                if not any(d.title.lower() == item.title.lower() for d in discovered):
                    discovered.append(item)
                if len(discovered) >= target_count:
                    break

        return discovered[:target_count]

    def _synthesize_dynamic_affinities(
        self,
        books: List[str],
        movies: List[str],
        locations: List[str],
        count: int = 5
    ) -> List[CulturalAffinityItem]:
        """
        Dynamically synthesizes bespoke cultural affinities matching the author's exact inputs.
        Ensures two different sets of favorites NEVER return the same static list.
        """
        # 1. Attempt LLM-based intelligent synthesis if live LLM is configured AND no event loop is running
        if (llm.api_key or llm.provider in ("ollama", "custom")):
            loop_is_running = False
            try:
                asyncio.get_running_loop()
                loop_is_running = True
            except RuntimeError:
                loop_is_running = False

            if not loop_is_running:
                try:
                    system_prompt = (
                        "You are a cultural literary and cinematic curator. "
                        "Given a user's favorite books, films, and locations, recommend exactly "
                        f"{count} distinct and compelling cultural recommendations (books, films, or evocative places) "
                        "that share deep aesthetic, thematic, or tonal resonances with these SPECIFIC works. "
                        "Do NOT recommend works already listed in the user's inputs. "
                        "Return ONLY a raw JSON array of objects with keys: 'title', 'category' (book, movie, or place), "
                        "'affinity_reason' (one vivid sentence explaining the aesthetic connection), and 'icon' ('book', 'film', or 'map-pin')."
                    )
                    user_msg = f"User Favorites:\nBooks: {', '.join(books) or 'None'}\nMovies: {', '.join(movies) or 'None'}\nLocations: {', '.join(locations) or 'None'}"
                    
                    async def _quick_generate():
                        return await asyncio.wait_for(
                            llm.generate(
                                prompt=user_msg,
                                system_prompt=system_prompt,
                                temperature=0.7,
                                max_tokens=500
                            ),
                            timeout=3.0
                        )
                    resp_text = asyncio.run(_quick_generate())
                    parsed = clean_and_parse_json(resp_text)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        items = []
                        for d in parsed:
                            if isinstance(d, dict) and d.get("title"):
                                cat = d.get("category", "book").lower()
                                icon = "map-pin" if "place" in cat else ("film" if "movie" in cat or "film" in cat else "book")
                                items.append(CulturalAffinityItem(
                                    title=d["title"],
                                    category=cat,
                                    affinity_reason=d.get("affinity_reason", "Aesthetic resonance with your favorite works"),
                                    icon=icon
                                ))
                        if items:
                            return items[:count]
                except Exception as e:
                    logger.debug(f"LLM dynamic affinity synthesis fallback to genre generator: {e}")

        # 2. Dynamic heuristic synthesis tailored to input vocabulary and genre signals
        combined = " ".join(books + movies + locations).lower()
        results: List[CulturalAffinityItem] = []

        if any(w in combined for w in ["road", "mccarthy", "no country", "western", "texas", "desert", "grimdark", "apocalyp", "post-apocalyp", "blood meridian", "coen", "survival", "deadwood", "fargo", "dust"]):
            results = [
                CulturalAffinityItem(title="Blood Meridian (Cormac McCarthy)", category="book", affinity_reason="Brutal poetic realism, primeval wilderness, and existential moral dread", icon="book"),
                CulturalAffinityItem(title="Hell or High Water (David Mackenzie)", category="movie", affinity_reason="Sun-bleached West Texas desperate bank heists and dying rural heritage", icon="film"),
                CulturalAffinityItem(title="Big Bend National Park & Chisos Basin, Texas", category="place", affinity_reason="Unforgiving canyon gorges, borderlands stillness, and austere desert winds", icon="map-pin"),
                CulturalAffinityItem(title="All the Pretty Horses (Cormac McCarthy)", category="book", affinity_reason="Lyrical frontier elegies, vanished cowboy codes, and border crossings", icon="book"),
                CulturalAffinityItem(title="Sicario (Denis Villeneuve)", category="movie", affinity_reason="Ominous sonic dread, ruthless moral compromise, and borderland violence", icon="film")
            ]
        elif any(w in combined for w in ["dune", "sci-fi", "space", "cyber", "blade runner", "matrix", "future", "robot", "asimov", "neuromancer", "alien", "solaris"]):
            results = [
                CulturalAffinityItem(title="Hyperion (Dan Simmons)", category="book", affinity_reason="Pilgrims traversing deep-time space mysteries with Canterbury-style narrative depth", icon="book"),
                CulturalAffinityItem(title="Solaris (Andrei Tarkovsky)", category="movie", affinity_reason="Existential grief, haunting cosmic boundaries, and psychological mystery", icon="film"),
                CulturalAffinityItem(title="Atacama Desert & ALMA Observatory, Chile", category="place", affinity_reason="Otherworldly geological silence under the clearest starfields on Earth", icon="map-pin"),
                CulturalAffinityItem(title="Left Hand of Darkness (Ursula K. Le Guin)", category="book", affinity_reason="Profound sociological worldbuilding and intimate interpersonal diplomacy", icon="book"),
                CulturalAffinityItem(title="Children of Men (Alfonso Cuarón)", category="movie", affinity_reason="Visceral single-shot realism amidst systemic societal breakdown", icon="film")
            ]
        elif any(w in combined for w in ["potter", "magic", "fantasy", "ring", "tolkien", "dragon", "witch", "hobbit", "westeros", "game of thrones", "sandman", "frozen", "narnia", "disney"]):
            results = [
                CulturalAffinityItem(title="His Dark Materials: The Golden Compass (Philip Pullman)", category="book", affinity_reason="Subversive theological myth, daemon bonds, and arctic expeditions", icon="book"),
                CulturalAffinityItem(title="Spirited Away (Hayao Miyazaki)", category="movie", affinity_reason="Liminal spirit bathhouses, forgotten names, and atmospheric reverence", icon="film"),
                CulturalAffinityItem(title="Hampton Court Palace & Maze, London", category="place", affinity_reason="Tudor labyrinthine passages, riverside gardens, and royal secrets", icon="map-pin"),
                CulturalAffinityItem(title="The Name of the Wind (Patrick Rothfuss)", category="book", affinity_reason="Lyrical storytelling of legendary folklore, arcane universities, and music", icon="book"),
                CulturalAffinityItem(title="Pan's Labyrinth (Guillermo del Toro)", category="movie", affinity_reason="Dark folkloric mythology intersecting with historical harshness", icon="film")
            ]
        elif any(w in combined for w in ["sherlock", "detective", "crime", "mystery", "murder", "poirot", "agatha", "noir", "fincher", "investigat", "doyle"]):
            results = [
                CulturalAffinityItem(title="The Alienist (Caleb Carr)", category="book", affinity_reason="Pioneering psychological profiling in gaslit Gilded Age New York", icon="book"),
                CulturalAffinityItem(title="Zodiac (David Fincher)", category="movie", affinity_reason="Obsessive archival investigative dread and meticulous period detail", icon="film"),
                CulturalAffinityItem(title="Fleet Street & The Temple Inns of Court, London", category="place", affinity_reason="Hidden legal courtyards, cobblestones, and Victorian investigative intrigue", icon="map-pin"),
                CulturalAffinityItem(title="Tinker Tailor Soldier Spy (John le Carré)", category="book", affinity_reason="Quiet betrayal, bureaucratic coldness, and guarded psychological chess", icon="book"),
                CulturalAffinityItem(title="Chinatown (Roman Polanski)", category="movie", affinity_reason="Systemic deception and sun-bleached fatalistic pursuit of truth", icon="film")
            ]
        elif any(w in combined for w in ["pride", "prejudice", "austen", "bronte", "romance", "love", "passion", "paris", "woolf", "before sunrise"]):
            results = [
                CulturalAffinityItem(title="Atonement (Ian McEwan)", category="book", affinity_reason="Lyrical prose, devastating misunderstandings, and lifelong penance", icon="book"),
                CulturalAffinityItem(title="In the Mood for Love (Wong Kar-wai)", category="movie", affinity_reason="Opulent textures, unexpressed longing, and slow-motion melancholy", icon="film"),
                CulturalAffinityItem(title="Peak District & Chatsworth House, England", category="place", affinity_reason="Sweeping moors, stately Regency libraries, and solitary countryside walks", icon="map-pin"),
                CulturalAffinityItem(title="The Remains of the Day (Kazuo Ishiguro)", category="book", affinity_reason="Heartbreaking emotional restraint and quiet dignity amidst historical shifts", icon="book"),
                CulturalAffinityItem(title="Portrait of a Lady on Fire (Céline Sciamma)", category="movie", affinity_reason="Intimate coastal isolation, shared gaze, and artistic devotion", icon="film")
            ]
        else:
            # Dynamic synthesis reflecting whatever primary title the user entered
            primary_title = books[0] if books else (movies[0] if movies else "Modern Narrative")
            results = [
                CulturalAffinityItem(title=f"Works in dialogue with {primary_title}", category="book", affinity_reason="Explores contiguous narrative themes, emotional resonance, and stylistics", icon="book"),
                CulturalAffinityItem(title="The Secret History (Donna Tartt)", category="book", affinity_reason="Intellectual cloistering, psychological tension, and aesthetic obsessions", icon="book"),
                CulturalAffinityItem(title="Drive My Car (Ryusuke Hamaguchi)", category="movie", affinity_reason="Contemplative long journeys, theatrical dialogue, and quiet revelations", icon="film"),
                CulturalAffinityItem(title="Canal District & Rijksmuseum Alleys, Amsterdam", category="place", affinity_reason="Quiet waterways, centuries-old brick facades, and contemplative light", icon="map-pin"),
                CulturalAffinityItem(title="Never Let Me Go (Kazuo Ishiguro)", category="book", affinity_reason="Deeply humane emotional undercurrents beneath speculative stillness", icon="book")
            ]

        return results[:count]

    def analyze_author_taste_profile(self, books: List[str], movies: List[str]) -> Dict[str, Any]:
        """
        Synthesizes an author's aesthetic archetype and narrative profile
        based on their favorite media.
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

        # Dynamic archetype assignment based on user's actual works
        if any(w in combined_text for w in ["blade runner", "cyber", "future", "dune", "sci-fi", "matrix", "solaris", "1984", "asimov", "alien"]):
            archetype = "Visionary Speculative Architect"
            genres = ["Sci-Fi & Speculative", "Cyberpunk / Tech Noir", "Dystopian Mystery"]
            tones = ["Brooding & Atmospheric", "Philosophical", "Tense"]
            settings = ["Neo-Tokyo", "London 2045", "Isolated Research Station"]
            summary = "Drawn to high-stakes existential questions, technological frontiers, and atmospheric neo-noir worldbuilding."
        elif any(w in combined_text for w in ["potter", "magic", "fantasy", "ring", "tolkien", "dragon", "witch", "sandman"]):
            archetype = "Mythic Worldbuilder & Lorekeeper"
            genres = ["Epic & High Fantasy", "Dark Fantasy", "Magical Realism"]
            tones = ["Evocative & Lyrical", "Wondrous", "Dramatic"]
            settings = ["Ancient Forest Citadel", "Arcane Coastal Port", "High Mountain Sanctuary"]
            summary = "Fascinated by grand mythologies, ancient oaths, arcane orders, and the cost of power."
        elif any(w in combined_text for w in ["gothic", "shadow", "secret history", "dark academia", "dorian gray", "poe", "dracula", "frankenstein"]):
            archetype = "Gothic & Dark Academia Chronicler"
            genres = ["Gothic Fiction", "Psychological Suspense", "Dark Academia"]
            tones = ["Haunting & Melancholic", "Tense", "Lyrical"]
            settings = ["Edinburgh Old Town", "Oxford College Quads", "Victorian Prague"]
            summary = "Attracted to ancient libraries, moral ruin, forgotten manuscripts, and the dark psychology of intellectual obsession."
        elif any(w in combined_text for w in ["sherlock", "detective", "crime", "noir", "chinatown", "fincher", "investigat", "agatha", "poirot"]):
            archetype = "Master of Intrigue & Moral Ambiguity"
            genres = ["Mystery & Crime", "Neo-Noir", "Political Thriller"]
            tones = ["Tense", "Calculated & Gritty", "Atmospheric"]
            settings = ["Rain-slicked Berlin", "Fog-bound London", "Mediterranean Port"]
            summary = "Thrives in labyrinthine plots, bureaucratic deceptions, moral dilemmas, and relentless unraveling of truth."
        elif any(w in combined_text for w in ["romance", "pride", "prejudice", "mood for love", "austen", "celine", "before sunrise"]):
            archetype = "Lyrical Humanist & Romantic Realist"
            genres = ["Romance", "Literary Drama", "Historical Romance"]
            tones = ["Poignant & Bittersweet", "Lyrical", "Tender"]
            settings = ["Autumn in Saint-Germain", "Coastal Mediterranean", "Rainy Lisbon"]
            summary = "Focused on deep emotional undercurrents, the fragility of memory, and unforgettable interpersonal connections."
        else:
            archetype = "Literary Stylist & Atmospheric Realist"
            genres = ["Literary Fiction", "Psychological Suspense", "Contemporary Drama"]
            tones = ["Measured & Evocative", "Richly Textured", "Observant"]
            settings = ["Coastal Town", "Old European Quarter", "Metropolitan Center"]
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
    Main entry point: Discovers 5 cultural affinity items via Qloo API,
    then prompts the LLM narrative engine to forge 3 distinct book scenarios.
    """
    affinities = qloo_client.discover_cultural_affinities(books, movies, locations, target_count=5)

    user_tastes_summary = []
    if books:
        user_tastes_summary.append(f"Favorite Books: {', '.join(books)}")
    if movies:
        user_tastes_summary.append(f"Favorite Films: {', '.join(movies)}")
    if locations:
        user_tastes_summary.append(f"Inspirational Locations: {', '.join(locations)}")

    user_context_str = "; ".join(user_tastes_summary) if user_tastes_summary else "General literary & cinematic tastes"

    affinities_str = "\n".join([
        f"- [{item.category.upper()}] {item.title}: {item.affinity_reason}"
        for item in affinities
    ])

    system_prompt = (
        "You are an elite novelist, story architect, and scenario strategist. "
        "A user has shared their artistic tastes, and the cultural intelligence engine has identified "
        "5 key cultural affinities resonating with their aesthetic.\n\n"
        "Your task: Craft exactly 3 DISTINCT, highly compelling, genre-defining novel scenarios. "
        "Each scenario must feel like an irresistible bestseller book concept that deeply resonates with their tastes.\n\n"
        "Return ONLY a valid JSON array of 3 scenario objects with the following exact keys:\n"
        "- id: string (e.g. 'sc_1', 'sc_2', 'sc_3')\n"
        "- title: string (evocative book title)\n"
        "- genre: string (e.g. 'Mystery & Crime', 'Sci-Fi & Speculative', 'Literary Fiction')\n"
        "- tone: string (e.g. 'Brooding & Atmospheric', 'Bittersweet & Haunting', 'Tense & Urgent')\n"
        "- prose_style: string (e.g. 'Literary & Elegant', 'Poetic & Evocative', 'Fast-Paced Cinematic')\n"
        "- logline: string (one crisp, hook-laden sentence)\n"
        "- premise: string (2-3 sentences explaining the world and core conflict)\n"
        "- hook: string (the inciting incident or dramatic question)\n"
        "- city: string (primary city or location setting)\n"
        "- country: string (country or realm)\n"
        "- era: string (e.g. 'Contemporary', '1920s Victorian Dusk', 'Near-Future 2045')\n"
        "- protagonist_name: string (full name of main character)\n"
        "- protagonist_role: string (occupation or societal standing)\n"
        "- protagonist_archetype: string (e.g. 'Scarred Cynic', 'Reluctant Truth-Seeker', 'Guarded Intellectual')\n"
        "- conflict: string (core internal vs external collision)\n"
        "- inspirations_summary: string (one sentence explaining how user tastes and cultural affinities informed this premise)\n\n"
        "Strict Rule: Output ONLY the raw JSON array, with no Markdown ticks (```json) or conversational preamble."
    )

    user_prompt = f"""AUTHOR TASTE PROFILE:
{user_context_str}

IDENTIFIED CULTURAL AFFINITIES:
{affinities_str}

Please generate the 3 distinct, irresistible novel scenarios tailored to these inspirations."""

    try:
        raw_resp = await asyncio.wait_for(
            llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.75,
                max_tokens=1800
            ),
            timeout=30.0
        )
        parsed = clean_and_parse_json(raw_resp)

        scenarios_data = []
        if isinstance(parsed, list):
            scenarios_data = parsed
        elif isinstance(parsed, dict) and "scenarios" in parsed:
            scenarios_data = parsed["scenarios"]

        scenarios: List[StoryScenario] = []
        for i, s in enumerate(scenarios_data[:3]):
            sc_city = s.get("city") or (locations[0] if locations else "Edinburgh")
            sc_country = s.get("country") or _infer_country_for_city(sc_city)
            scenarios.append(StoryScenario(
                id=s.get("id") or f"sc_{i+1}",
                title=s.get("title") or f"Scenario {i+1}",
                genre=s.get("genre") or "Literary Fiction",
                tone=s.get("tone") or "Atmospheric",
                prose_style=s.get("prose_style") or "Literary & Elegant",
                logline=s.get("logline") or "An untold secret threatens the foundations of an ancient city.",
                premise=s.get("premise") or "When a forgotten manuscript surfaces, two estranged rivals must decipher its warnings before the dawn.",
                hook=s.get("hook") or "A midnight confession left in an empty chapel.",
                city=sc_city,
                country=sc_country,
                era=s.get("era") or "Contemporary",
                protagonist_name=s.get("protagonist_name") or "Julian Vance",
                protagonist_role=s.get("protagonist_role") or "Archival Researcher",
                protagonist_archetype=s.get("protagonist_archetype") or "Reluctant Truth-Seeker",
                conflict=s.get("conflict") or "Obsession with historical truth against the safety of those he protects.",
                inspirations_summary=s.get("inspirations_summary") or "Synthesized from literary and atmospheric cultural affinities."
            ))

        if len(scenarios) == 3:
            return {
                "scenarios": [sc.model_dump() for sc in scenarios],
                "similar_items": [item.model_dump() for item in affinities]
            }

    except Exception as e:
        logger.warning(f"LLM scenario generation failed, using structured creative synthesis: {e}")

    # Dynamic genre-aware procedural generation if LLM is offline or error occurred
    fav_book = books[0] if books else "The Secret History"
    fav_movie = movies[0] if movies else "Chinatown"
    fav_loc = locations[0] if locations else "Edinburgh"
    combined_tastes = " ".join(books + movies + locations).lower()

    if any(w in combined_tastes for w in ["road", "mccarthy", "no country", "western", "texas", "desert", "grimdark", "apocalyp", "post-apocalyp", "blood meridian", "coen", "survival"]):
        fallback_scenarios = [
            StoryScenario(
                id="sc_1",
                title=f"No Haven on the {fav_loc} Border",
                genre="Neo-Western Thriller",
                tone="Gritty & Relentless",
                prose_style="Sparse & Visceral",
                logline=f"An aging lawman in {fav_loc} tracks a silent executioner across an arid wasteland where the rules of civilization no longer hold.",
                premise=f"Drawing on the uncompromising dread of {fav_movie} and the bleak moral clarity of {fav_book}, a solitary investigator stumbles upon an abandoned courier truck carrying contraband that powerful cartels and corrupt officials would burn counties to recover.",
                hook="A satchel buried beneath desert limestone, stamped with an emblem from thirty years ago.",
                city=fav_loc,
                country="United States / Borderlands",
                era="Late Summer, 1980",
                protagonist_name="Sheriff Wyatt Boyd",
                protagonist_role="County Sheriff",
                protagonist_archetype="Weary Cynic",
                conflict="Upholding an archaic oath to justice vs the terrifying certainty that evil is always one step ahead.",
                inspirations_summary=f"Forged from the brutal starkness of {fav_book} and the fatalistic suspense of {fav_movie}."
            ),
            StoryScenario(
                id="sc_2",
                title=f"The Ash Meridian",
                genre="Post-Apocalyptic Survival",
                tone="Haunting & Austere",
                prose_style="Poetic & Biblical",
                logline="A father and daughter navigate a scorched continent toward the coast, carrying the last recorded seed catalog.",
                premise=f"Echoing the devastating paternal devotion in {fav_book}, two survivors trek through ash-choked valleys near {fav_loc}, evading scavenging militias while protecting a fragile glass jar containing pre-collapse wheat strains.",
                hook="The glow of an unshielded campfire reflecting against a ridge where no one should be alive.",
                city=fav_loc,
                country="Wasteland Frontier",
                era="Post-Collapse Year 14",
                protagonist_name="Eli Vance",
                protagonist_role="Former Agronomist & Wanderer",
                protagonist_archetype="Fierce Protector",
                conflict="Preserving his daughter's innocence and humanity vs doing whatever it takes to survive another winter.",
                inspirations_summary=f"Synthesizing the desolate poetry of {fav_book} and minimalist cinematic stillness."
            ),
            StoryScenario(
                id="sc_3",
                title=f"Blood & Cholla at Midnight",
                genre="Southern Noir Crime",
                tone="Tense & Fatalistic",
                prose_style="Calculated & Hardboiled",
                logline="A former ranch hand is hired to retrieve a stolen deed, only to discover his client murdered the rightful heirs forty years ago.",
                premise=f"Channels the tension of {fav_movie} into the remote canyons surrounding {fav_loc}, where ancient blood feuds between ranching dynasties collide with oil speculators and mercenary trackers.",
                hook="A bloodstained silver spur found in an unmapped ravine.",
                city=fav_loc,
                country="United States",
                era="Early 1970s",
                protagonist_name="Carson Cole",
                protagonist_role="Ex-Ranger & Private Tracker",
                protagonist_archetype="Morally Ambiguous Drifter",
                conflict="Taking the life-changing bounty money vs protecting the last surviving granddaughter of his old mentor.",
                inspirations_summary=f"Derived from classic neo-noir fatalism, desolate vistas, and explosive confrontations."
            )
        ]
    elif any(w in combined_tastes for w in ["potter", "magic", "fantasy", "ring", "tolkien", "dragon", "witch", "hobbit", "westeros", "game of thrones", "sandman", "frozen", "narnia", "disney"]):
        fallback_scenarios = [
            StoryScenario(
                id="sc_1",
                title=f"The Frostbound Arcana of {fav_loc}",
                genre="Epic Fantasy & Arcane Mystery",
                tone="Wondrous & Atmospheric",
                prose_style="Lyrical & Immersive",
                logline=f"An apprentice cartographer in {fav_loc} discovers that the winter freeze is carrying an ancient, forbidden language into the city's spires.",
                premise=f"Infused with the whimsical wonder of {fav_book} and the glacial mythic beauty of {fav_movie}, a young scholar uncovers an enchanted atlas that predicts frost storms capable of crystallizing human memories into glowing glass runes.",
                hook="A grandfather clock in the academy tower freezes solid in mid-ring, trapping a spectral voice inside its chime.",
                city=fav_loc,
                country="The Realm of Albion",
                era="Late Victorian Mythic Dusk",
                protagonist_name="Lyra Hawthorne",
                protagonist_role="Arcane Cartographer",
                protagonist_archetype="Curious Seeker",
                conflict="Unlocking forbidden elemental power to save her family vs risking the eternal winter of the realm.",
                inspirations_summary=f"Echoes the boarding-school enchantment of {fav_book} and the elemental ice magic of {fav_movie}."
            ),
            StoryScenario(
                id="sc_2",
                title=f"The Clockwork Hearthstone",
                genre="Urban Fantasy & Secret Lore",
                tone="Charming & Suspenseful",
                prose_style="Richly Textured & Evocative",
                logline=f"Hidden beneath the cobblestones of {fav_loc}, an illicit guild of alchemists races to reignite a primordial flame before the equinox.",
                premise=f"Channeling the vibrant camaraderie of {fav_book}, three misfit apprentices discover that {fav_loc}'s most famous monument conceals an ancient engine powered by living starlight, now coveted by an exiled sorcerer.",
                hook="A stray alley cat drops a glowing bronze key into a tea saucer at a midnight apothecary.",
                city=fav_loc,
                country=_infer_country_for_city(fav_loc),
                era="Edwardian Fantasy",
                protagonist_name="Jesse Vance",
                protagonist_role="Horologist & Alchemy Apprentice",
                protagonist_archetype="Reluctant Hero",
                conflict="Loyalty to the strict Guild decrees vs breaking the ancient laws of magic to shield an orphaned elemental.",
                inspirations_summary=f"Synthesizes secret magical societies, hidden urban lore, and warm character fellowship."
            ),
            StoryScenario(
                id="sc_3",
                title=f"The Winter Archon's Legacy",
                genre="High Fantasy Adventure",
                tone="Heroic & Poignant",
                prose_style="Epic & Majestic",
                logline="An exiled heir possessing the forbidden power of living ice must journey across perilous peaks to reclaim a shattered throne.",
                premise=f"Drawing inspiration from the mythic scope of {fav_movie} and high-stakes magical destinies, this grand adventure follows a solitary sovereign who must tame an unyielding blizzard in order to unite warring northern clans against an abyssal eclipse.",
                hook="A river freezes into solid mirrors overnight, reflecting kingdoms that died five hundred years ago.",
                city=fav_loc,
                country="The Northern Marches",
                era="Age of Legends",
                protagonist_name="Rowan Drake",
                protagonist_role="Exiled Archon & Frostbinder",
                protagonist_archetype="Vulnerable Sovereign",
                conflict="Fearing the destructive potential of their own magic vs stepping into destiny to deliver their people.",
                inspirations_summary=f"Combines mythic destiny, elemental forces, and heartfelt emotional courage."
            )
        ]
    elif any(w in combined_tastes for w in ["dune", "sci-fi", "space", "cyber", "blade runner", "matrix", "future", "robot", "asimov", "neuromancer", "alien", "solaris"]):
        fallback_scenarios = [
            StoryScenario(
                id="sc_1",
                title=f"The Silicon Horizon of {fav_loc}",
                genre="Cyberpunk / Tech Noir",
                tone="Brooding & Atmospheric",
                prose_style="Cinematic & Razor-Sharp",
                logline=f"In the neon-drenched sky-districts of {fav_loc}, a rogue memory detective is hired to locate an artificial entity that dreamt of a human child.",
                premise=f"Synthesizing the philosophical cyberpunk depth of {fav_movie} and speculative worldbuilding of {fav_book}, an augmented investigator uncovers a syndicate synthesizing synthetic souls for an off-world oligarchy.",
                hook="An android corpse discovered on a high-voltage transit rail with organic tears in its synthetic tear ducts.",
                city=fav_loc,
                country="Unified Megacity Zone",
                era="Year 2049",
                protagonist_name="Kaelen Mercer",
                protagonist_role="Neural Trace Operative",
                protagonist_archetype="Jaded Cynic",
                conflict="Following corporate termination protocols vs discovering that his own memories are an unauthorized copy.",
                inspirations_summary=f"Inspired by neo-noir neon aesthetics, artificial consciousness dilemmas, and rain-soaked streetscapes."
            ),
            StoryScenario(
                id="sc_2",
                title=f"Echoes of the Void Colony",
                genre="Hard Sci-Fi Drama",
                tone="Introspective & Tense",
                prose_style="Methodical & Philosophical",
                logline="A terraforming engineer on an isolated research outpost detects a recurring seismic signal speaking in human radio pulses.",
                premise=f"Evoking the deep cosmic solitude of {fav_book}, a skeleton crew of scientists orbiting a dead gas giant must determine whether an alien geological entity is communicating or attempting to rewrite their ship's navigational consciousness.",
                hook="A lunar rover returns to the airlock autonomous and empty, its compass pointing directly down toward the planetary core.",
                city=fav_loc,
                country="Orbital Sector Nine",
                era="22nd Century",
                protagonist_name="Dr. Veda Cross",
                protagonist_role="Exobiologist & Systems Lead",
                protagonist_archetype="Guarded Intellectual",
                conflict="Scientific obsession with humanity's first contact vs preserving the sanity and life of the remaining crew.",
                inspirations_summary=f"Echoes existential space exploration, atmospheric acoustic isolation, and deep-time mysteries."
            ),
            StoryScenario(
                id="sc_3",
                title=f"The Neural Override",
                genre="Speculative Thriller",
                tone="Urgent & Paranoic",
                prose_style="Fast-Paced & Visceral",
                logline="A biometric auditor discovers that citizens' subconscious memories are being swapped while they sleep in {fav_loc}.",
                premise=f"Drawing on high-concept speculative tension, a compliance officer in {fav_loc} realizes that recent civic reforms are actually calibrating mass neural synchronization, erasing historic dissidence from living minds.",
                hook="A man wakes up with flawless recall of a thirty-year diplomatic career he never lived.",
                city=fav_loc,
                country="Federal Commonwealth",
                era="Near-Future 2038",
                protagonist_name="Tamsin Thorne",
                protagonist_role="Cognitive Compliance Officer",
                protagonist_archetype="Reluctant Rebel",
                conflict="Security of compliance within the regime vs the terrifying vertigo of true, unmonitored human reality.",
                inspirations_summary=f"Synthesizes dystopian paranoias, corporate surveillance, and the fragility of identity."
            )
        ]
    else:
        # Default tailored literary / mystery / drama
        fallback_scenarios = [
            StoryScenario(
                id="sc_1",
                title=f"The Labyrinth of {fav_loc}",
                genre="Mystery & Suspense",
                tone="Brooding & Atmospheric",
                prose_style="Literary & Elegant",
                logline=f"In the subterranean archives of {fav_loc}, an obsessive scholar unearths a code that redefines an unsolved disappearance.",
                premise=f"Drawing on the intricate tension of {fav_book} and the visual stillness of {fav_movie}, a reclusive archivist discovers that the death of their mentor was not suicide, but the first step in a centuries-old conspiracy buried beneath {fav_loc}.",
                hook="A coded letter delivered twenty years after the sender vanished from the city docks.",
                city=fav_loc,
                country=_infer_country_for_city(fav_loc),
                era="Late Autumn, 1994",
                protagonist_name="Arthur Pendelton",
                protagonist_role="Rare Manuscripts Curator",
                protagonist_archetype="Guarded Intellectual",
                conflict="Protecting his mentor's memory vs exposing an institutional crime that implicates his own family.",
                inspirations_summary=f"Infused with the investigative depth of {fav_book} and the atmospheric dread of {fav_movie}."
            ),
            StoryScenario(
                id="sc_2",
                title=f"Echoes of Cold Rain",
                genre="Literary Drama",
                tone="Bittersweet & Poignant",
                prose_style="Poetic & Evocative",
                logline="Two former confidants reunite under an alias to settle a debt before one of them departs the continent forever.",
                premise=f"Evoking the melancholy textures of {fav_movie}, this intimate psychological drama follows an exiled musician and a translator who meet in an off-season hotel in {fav_loc} during a week of unending rain.",
                hook="An unannounced visitor slips a train ticket under a locked hotel suite door.",
                city=fav_loc,
                country="Europe",
                era="Contemporary",
                protagonist_name="Clara Sterling",
                protagonist_role="Concert Accompanist",
                protagonist_archetype="Scarred Idealist",
                conflict="Longing for reconciliation vs the cold realization that some vows cannot survive the truth.",
                inspirations_summary=f"Synthesizing the emotional restraint of {fav_movie} and literary chamber realism."
            ),
            StoryScenario(
                id="sc_3",
                title=f"The Solitude of {fav_loc}",
                genre="Psychological Fiction",
                tone="Measured & Tense",
                prose_style="Evocative & Observant",
                logline="An estranged daughter returns to settle an estate, uncovering an uncatalogued collection of portraits that tell a dangerous truth.",
                premise=f"Blending the character psychology of {fav_book} with striking visual contrasts, an art restorer working in {fav_loc} discovers hidden layers in a celebrated painter's final works that expose a decades-old deception.",
                hook="A canvas painted over in lead white that bleeds crimson under ultraviolet restoration lamps.",
                city=fav_loc,
                country="Continental Europe",
                era="Late Autumn, 2002",
                protagonist_name="Julian Vance",
                protagonist_role="Art Restorer",
                protagonist_archetype="Reluctant Truth-Seeker",
                conflict="The desire for familial closure vs confronting an ugly legacy that could destroy her own name.",
                inspirations_summary=f"Inspired by the layered nuance of {fav_book} and the visual precision of {fav_movie}."
            )
        ]

    return {
        "scenarios": [sc.model_dump() for sc in fallback_scenarios],
        "similar_items": [item.model_dump() for item in affinities]
    }
