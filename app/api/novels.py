import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Response, Depends
from pydantic import BaseModel
from app.api.deps import get_current_user_optional, get_current_user
from app.storage.users import User

from app.models.blueprint import (
    CreateNovelRequest, StoryBlueprint, NovelSummary,
    WorldSettings, CastSettings, PlotSettings, StyleSettings,
    Location, LocationSeed
)
from app.models.character import Character, PersonaCore, CharacterSeed
from app.models.episode import EpisodeResponse, EpisodeSummary, GenerationProgress, SetAutoContinueRequest
from app.models.enums import NovelStatus, Genre, ProseStyle, Theme, Tone, Perspective, EndingType
from app.storage.store import store
from app.engine.pipeline import initialize_novel, generate_single_episode, run_novel_episodes, track_task, is_novel_active
from app.engine.image_client import chapter_image_client
from app.engine.qloo_client import qloo_client, generate_scenarios_from_tastes

router = APIRouter(prefix="/api/novels", tags=["Novels"])

class RenameRequest(BaseModel):
    title: str

class MagicIdeaRequest(BaseModel):
    prompt: Optional[str] = ""
    genre: Optional[str] = None

class QlooScenarioRequest(BaseModel):
    books: List[str] = []
    movies: List[str] = []
    locations: List[str] = []

@router.post("/qloo-scenarios")
async def generate_qloo_scenarios_endpoint(req: QlooScenarioRequest):
    """
    Discovers 5 cultural affinity matches via Qloo's taste graph,
    then synthesizes 3 rich, distinct book writing scenarios for the author.
    """
    return await generate_scenarios_from_tastes(
        books=req.books,
        movies=req.movies,
        locations=req.locations
    )

@router.post("/magic-blueprint", response_model=CreateNovelRequest)
async def generate_magic_blueprint(req: MagicIdeaRequest):
    """Generates a complete creative blueprint setup from a single short prompt or template."""
    presets = [
        {
            "prompt": "mystery",
            "title": "The Whispering Archives of Blackwood",
            "premise": "An archival conservator returns to his fog-drenched home city after twenty years to uncover the secret of a missing ledger that shattered his family's name.",
            "genre": Genre.MYSTERY_CRIME.value,
            "theme": Theme.TRUTH_LIES.value,
            "tone": Tone.TENSE.value,
            "prose_style": ProseStyle.LITERARY.value,
            "city": "Edinburgh",
            "era": "Contemporary",
            "rules": ["No secret buried in the district survives beyond a single generation."],
            "locations": [
                {"name": "The Vaulted Archives", "description": "Smell of aged paper, iron gall ink, and cold amber gas lamps"},
                {"name": "The Lantern Wharf", "description": "Weather-beaten moorings veiled in dense river fog"}
            ],
            "characters": [
                {"name": "Julian Vance", "role": "Main", "gender": "Male", "occupation": "Archival Conservator", "persona": "Scarred Cynic"},
                {"name": "Clara Sterling", "role": "Main", "gender": "Female", "occupation": "Investigative Journalist", "persona": "Passionate Idealist"},
                {"name": "Arthur Pendelton", "role": "Supporting", "gender": "Male", "occupation": "Elder Antiquarian", "persona": "Strict Traditionalist"}
            ]
        },
        {
            "prompt": "romance",
            "title": "Autumn Echoes at Cafe Saint-Germain",
            "premise": "Two strangers with conflicting pasts cross paths during an October downpour in the historic center, finding an unexpected bond while concealing wounds they dare not speak aloud.",
            "genre": Genre.ROMANCE.value,
            "theme": Theme.LONELINESS_CONNECTION.value,
            "tone": Tone.BITTERSWEET.value,
            "prose_style": ProseStyle.POETIC_IMAGERY.value,
            "city": "Paris",
            "era": "Contemporary",
            "rules": ["People never disclose the complete truth of the fractures they carry."],
            "locations": [
                {"name": "Cafe Saint-Germain", "description": "Dark mahogany tables, aroma of espresso and damp coats by the hearth"},
                {"name": "The Pont des Arts at Midnight", "description": "The river Seine shimmering beneath autumn lamplight"}
            ],
            "characters": [
                {"name": "David Laurent", "role": "Main", "gender": "Male", "occupation": "Restoration Architect", "persona": "Isolated Scholar"},
                {"name": "Elena Vane", "role": "Main", "gender": "Female", "occupation": "Literary Translator", "persona": "Secretive Wit"}
            ]
        },
        {
            "prompt": "sci-fi",
            "title": "Protocol Zero: London 2045",
            "premise": "When a catastrophic blackout severs the city's neural neural network, a disgraced data archaeologist discovers that citizens' digital memories have been systematically rewritten.",
            "genre": Genre.SCI_FI.value,
            "theme": Theme.IDENTITY_BELONGING.value,
            "tone": Tone.DARK.value,
            "prose_style": ProseStyle.COLD_REPORT.value,
            "city": "London",
            "era": "Near-Future 2045",
            "rules": ["Digital data can be fabricated; only biological memory carries authentic weight."],
            "locations": [
                {"name": "Shard Central Server Spire", "description": "Frigid neon corridors vibrating with cooling fans"},
                {"name": "The Analog Undermarket", "description": "Moist underground vaults dealing in salvaged magnetic tape and physical paper"}
            ],
            "characters": [
                {"name": "Marcus Kane", "role": "Main", "gender": "Male", "occupation": "Data Retrieval Specialist", "persona": "Restless Rebel"},
                {"name": "Dr. Sarah Chen", "role": "Main", "gender": "Female", "occupation": "Chief Neural Architect", "persona": "Calculating Strategist"}
            ]
        }
    ]

    p_lower = (req.prompt or "").lower()
    selected = None
    for p in presets:
        if p["prompt"].lower() in p_lower or (req.genre and p["genre"] == req.genre):
            selected = p
            break
    if not selected:
        selected = presets[0] if not p_lower else {
            "title": f"Story of {req.prompt[:30]}",
            "premise": req.prompt,
            "genre": req.genre or Genre.DRAMA.value,
            "theme": Theme.IDENTITY_BELONGING.value,
            "tone": Tone.TENSE.value,
            "prose_style": ProseStyle.LITERARY.value,
            "city": "London",
            "era": "Contemporary",
            "rules": ["Silence in the face of truth inevitably invites catastrophe."],
            "locations": [
                {"name": "Central Setting", "description": "Rain-streaked streets filled with forgotten echoes"}
            ],
            "characters": [
                {"name": "Protagonist", "role": "Main", "gender": "Male", "occupation": "Central Figure", "persona": "Passionate Idealist"},
                {"name": "Companion", "role": "Main", "gender": "Female", "occupation": "Unexpected Ally", "persona": "Scarred Cynic"}
            ]
        }

    return CreateNovelRequest(
        title=selected["title"],
        premise=selected["premise"],
        genre=selected["genre"],
        theme=selected["theme"],
        tone=selected["tone"],
        prose_style=selected["prose_style"],
        city=selected["city"],
        era=selected["era"],
        world_rules=selected["rules"],
        locations=[LocationSeed(**l) for l in selected["locations"]],
        characters=[CharacterSeed(**c) for c in selected["characters"]],
        total_episodes=4,
        words_per_episode=1200,
        start_now=False
    )

def check_novel_access(novel_id: str, user: Optional[User]) -> StoryBlueprint:
    """Enforces multi-tenant authorization: only the author or an admin can access this novel."""
    bp = store.get_blueprint(novel_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Novel not found")
    owner_id = getattr(bp, "owner_id", None) or getattr(bp, "user_id", None)
    if owner_id:
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required to access this novel.")
        if user.id != owner_id and user.role != "admin":
            raise HTTPException(status_code=403, detail="Access denied. You do not have permission to view or modify this novel.")
    elif not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied. This novel is private.")
    return bp

@router.get("", response_model=List[NovelSummary])
async def list_novels(user: Optional[User] = Depends(get_current_user_optional)):
    """List novels in the library for the current user (or all if admin). Unauthenticated visitors see an empty list."""
    if not user:
        return []
    if user.role != "admin":
        return store.list_novels(user_id=user.id)
    return store.list_novels()

@router.post("", response_model=StoryBlueprint)
async def create_novel(req: CreateNovelRequest, background_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    """Creates a new novel tied to the authenticated user and initiates world/matrix building in the background."""
    novel_id = f"novel_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    owner_id = user.id
    owner_name = user.full_name or user.username

    chars = []
    if req.characters:
        for c_seed in req.characters:
            chars.append(Character(
                key=f"char_{uuid.uuid4().hex[:6]}",
                is_main=(c_seed.role.lower() == "main"),
                core=PersonaCore(
                    name=c_seed.name,
                    gender=c_seed.gender or "Unspecified",
                    age=c_seed.age or 30,
                    occupation=c_seed.occupation or "",
                    role=c_seed.role
                )
            ))
    
    locs = []
    if req.locations:
        for l_seed in req.locations:
            locs.append(Location(
                key=f"loc_{uuid.uuid4().hex[:6]}",
                name=l_seed.name,
                kind=l_seed.kind or "Location",
                description=l_seed.description or ""
            ))

    blueprint = StoryBlueprint(
        novel_id=novel_id,
        title=req.title or "New Novel",
        premise=req.premise or "",
        total_episodes=req.total_episodes or 5,
        words_per_episode=req.words_per_episode or 1500,
        auto_continue=bool(req.auto_continue),
        status=NovelStatus.DRAFT.value,
        created_at_utc=now,
        updated_at_utc=now,
        owner_id=owner_id,
        owner_name=owner_name,
        world=WorldSettings(
            era=req.era or "Contemporary",
            country=req.country or "United Kingdom",
            city=req.city or "London",
            story_time_span=req.story_time_span or "One Season",
            world_rules=req.world_rules or [],
            locations=locs
        ),
        cast=CastSettings(
            characters=chars
        ),
        plot=PlotSettings(
            resolution=req.ending or EndingType.SURPRISING.value
        ),
        style=StyleSettings(
            genre=req.genre or Genre.DRAMA.value,
            prose_style=req.prose_style or ProseStyle.LITERARY.value,
            theme=req.theme or Theme.IDENTITY_BELONGING.value,
            tone=req.tone or Tone.BITTERSWEET.value,
            perspective=req.perspective or Perspective.THIRD_PERSON_LIMITED.value
        )
    )

    store.save_blueprint(blueprint)

    if req.start_now:
        task = asyncio.create_task(initialize_novel(blueprint))
        track_task(task)

    return blueprint

@router.get("/{novel_id}", response_model=StoryBlueprint)
async def get_novel(novel_id: str, user: Optional[User] = Depends(get_current_user_optional)):
    """Retrieve full novel blueprint, cast, world, and settings (author or admin only)."""
    return check_novel_access(novel_id, user)

@router.get("/{novel_id}/matrix")
async def get_novel_matrix(novel_id: str, user: Optional[User] = Depends(get_current_user_optional)):
    """Retrieve the Character x Episode Story Matrix (author or admin only)."""
    check_novel_access(novel_id, user)
    m = store.get_matrix(novel_id)
    if not m:
        return Response(content="{}", media_type="application/json")
    return m

@router.get("/{novel_id}/memory")
async def get_novel_memory(novel_id: str, user: Optional[User] = Depends(get_current_user_optional)):
    """Retrieve the continuous Story Memory (author or admin only)."""
    check_novel_access(novel_id, user)
    mem = store.get_memory(novel_id)
    if not mem:
        return Response(content="{}", media_type="application/json")
    return mem

@router.delete("/{novel_id}")
async def delete_novel(novel_id: str, current_user: User = Depends(get_current_user)):
    """Delete a novel permanently (author or admin only)."""
    check_novel_access(novel_id, current_user)
    success = store.delete_novel(novel_id)
    if not success:
        raise HTTPException(status_code=404, detail="Novel not found")
    return {"message": "Novel deleted successfully"}

@router.patch("/{novel_id}/rename", response_model=StoryBlueprint)
async def rename_novel(novel_id: str, req: RenameRequest, current_user: User = Depends(get_current_user)):
    """Rename a novel (author or admin only)."""
    check_novel_access(novel_id, current_user)
    updated = store.rename_novel(novel_id, req.title)
    if not updated:
        raise HTTPException(status_code=404, detail="Novel not found")
    return updated

@router.get("/{novel_id}/progress", response_model=GenerationProgress)
async def get_progress(novel_id: str, user: Optional[User] = Depends(get_current_user_optional)):
    """Get live generation step progress (author or admin only)."""
    check_novel_access(novel_id, user)
    p = store.get_progress(novel_id)
    if p and p.is_active and not is_novel_active(novel_id):
        # Auto-heal ghost active states if server restarted or task terminated
        p.is_active = False
        store.save_progress(p)
    return p

@router.post("/{novel_id}/auto-continue")
async def toggle_auto_continue(novel_id: str, req: SetAutoContinueRequest, user: User = Depends(get_current_user)):
    """Toggle auto-continue mode (author or admin only)."""
    bp = check_novel_access(novel_id, user)
    bp.auto_continue = req.auto_continue
    store.save_blueprint(bp)

    if bp.auto_continue and not is_novel_active(novel_id):
        task = asyncio.create_task(run_novel_episodes(novel_id))
        track_task(task)

    return {"auto_continue": bp.auto_continue}

@router.post("/{novel_id}/write-next")
async def write_next_episode(novel_id: str, user: User = Depends(get_current_user)):
    """Manually trigger generation of the next episode (author or admin only)."""
    bp = check_novel_access(novel_id, user)
    
    if is_novel_active(novel_id):
        raise HTTPException(status_code=409, detail="A chapter generation is currently in progress for this novel")

    written = len(store.list_episodes(novel_id))
    next_ep = written + 1
    if next_ep > bp.total_episodes:
        raise HTTPException(status_code=400, detail="All episodes for this novel have already been generated")

    task = asyncio.create_task(generate_single_episode(novel_id, next_ep))
    track_task(task)
    return {"message": f"Writing of Chapter {next_ep} initiated in background"}

@router.post("/{novel_id}/reset-generation")
async def reset_generation(novel_id: str, user: User = Depends(get_current_user)):
    """Reset stuck or interrupted generation state for a novel."""
    bp = check_novel_access(novel_id, user)
    bp.auto_continue = False
    if bp.status == NovelStatus.WRITING.value:
        bp.status = NovelStatus.READY.value
    store.save_blueprint(bp)

    p = store.get_progress(novel_id)
    if p:
        p.is_active = False
        p.percentage = 0
        p.current_step = "Generation state reset"
        store.save_progress(p)

    return {"message": "Generation state reset successfully"}

@router.get("/{novel_id}/episodes", response_model=List[EpisodeSummary])
async def list_episodes(novel_id: str, user: Optional[User] = Depends(get_current_user_optional)):
    """List written episodes for a novel (author or admin only)."""
    check_novel_access(novel_id, user)
    return store.list_episodes(novel_id)

@router.get("/{novel_id}/episodes/{episode_number}", response_model=EpisodeResponse)
async def get_episode(novel_id: str, episode_number: int, user: Optional[User] = Depends(get_current_user_optional)):
    """Retrieve full text and behind-the-scenes actor data of a specific episode (author or admin only)."""
    check_novel_access(novel_id, user)
    ep = store.get_episode(novel_id, episode_number)
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    return ep

@router.get("/{novel_id}/episodes/{episode_number}/image")
async def get_episode_image(novel_id: str, episode_number: int, user: Optional[User] = Depends(get_current_user_optional)):
    """Serve the chapter illustration or dynamically generate it on demand (author or admin only)."""
    bp = check_novel_access(novel_id, user)
    img_data = store.get_episode_image(novel_id, episode_number)
    if img_data:
        data, mime_type = img_data
        return Response(content=data, media_type=mime_type, headers={"Cache-Control": "public, max-age=86400"})

    # Auto-generate if missing and episode exists
    ep = store.get_episode(novel_id, episode_number)
    if not ep:
        raise HTTPException(status_code=404, detail="Episode or novel not found")

    data, mime_type, prompt = await chapter_image_client.generate(bp, ep)
    store.save_episode_image(novel_id, episode_number, data, mime_type)
    ep.image_url = f"/api/novels/{novel_id}/episodes/{episode_number}/image"
    ep.image_prompt = prompt
    store.save_episode(ep)

    return Response(content=data, media_type=mime_type, headers={"Cache-Control": "public, max-age=86400"})

@router.post("/{novel_id}/episodes/{episode_number}/generate-image")
async def generate_episode_image(novel_id: str, episode_number: int, user: User = Depends(get_current_user)):
    """Regenerate the chapter artwork based on current settings and episode content (author or admin only)."""
    bp = check_novel_access(novel_id, user)
    ep = store.get_episode(novel_id, episode_number)
    if not ep:
        raise HTTPException(status_code=404, detail="Episode or novel not found")

    data, mime_type, prompt = await chapter_image_client.generate(bp, ep)
    store.save_episode_image(novel_id, episode_number, data, mime_type)
    ep.image_url = f"/api/novels/{novel_id}/episodes/{episode_number}/image"
    ep.image_prompt = prompt
    store.save_episode(ep)

    return {
        "success": True,
        "image_url": ep.image_url,
        "image_prompt": prompt,
        "mime_type": mime_type
    }

