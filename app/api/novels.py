import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Response, Depends
from pydantic import BaseModel
from app.api.deps import get_current_user_optional
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
from app.engine.pipeline import initialize_novel, generate_single_episode, run_novel_episodes
from app.engine.image_client import chapter_image_client

router = APIRouter(prefix="/api/novels", tags=["Novels"])

class RenameRequest(BaseModel):
    title: str

class MagicIdeaRequest(BaseModel):
    prompt: Optional[str] = ""
    genre: Optional[str] = None

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

@router.get("", response_model=List[NovelSummary])
async def list_novels(user: Optional[User] = Depends(get_current_user_optional)):
    """List novels in the library for the current user (or all if admin)."""
    if user and user.role != "admin":
        return store.list_novels(user_id=user.id)
    return store.list_novels()

@router.post("", response_model=StoryBlueprint)
async def create_novel(req: CreateNovelRequest, background_tasks: BackgroundTasks, user: Optional[User] = Depends(get_current_user_optional)):
    """Creates a new novel and initiates world/matrix building in the background."""
    novel_id = f"novel_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    owner_id = user.id if user else req.owner_id
    owner_name = (user.full_name or user.username) if user else req.owner_name

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
        background_tasks.add_task(initialize_novel, blueprint)

    return blueprint

@router.get("/{novel_id}", response_model=StoryBlueprint)
async def get_novel(novel_id: str):
    """Retrieve full novel blueprint, cast, world, and settings."""
    bp = store.get_blueprint(novel_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Novel not found")
    return bp

@router.delete("/{novel_id}")
async def delete_novel(novel_id: str):
    """Delete a novel permanently."""
    success = store.delete_novel(novel_id)
    if not success:
        raise HTTPException(status_code=404, detail="Novel not found")
    return {"message": "Novel deleted successfully"}

@router.patch("/{novel_id}/rename", response_model=StoryBlueprint)
async def rename_novel(novel_id: str, req: RenameRequest):
    """Rename a novel."""
    bp = store.rename_novel(novel_id, req.title)
    if not bp:
        raise HTTPException(status_code=404, detail="Novel not found")
    return bp

@router.get("/{novel_id}/progress", response_model=GenerationProgress)
async def get_progress(novel_id: str):
    """Get live generation step progress."""
    return store.get_progress(novel_id)

@router.post("/{novel_id}/auto-continue")
async def toggle_auto_continue(novel_id: str, req: SetAutoContinueRequest, background_tasks: BackgroundTasks):
    """Toggle auto-continue mode."""
    bp = store.get_blueprint(novel_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Novel not found")
    bp.auto_continue = req.auto_continue
    store.save_blueprint(bp)

    if bp.auto_continue:
        background_tasks.add_task(run_novel_episodes, novel_id)

    return {"auto_continue": bp.auto_continue}

@router.post("/{novel_id}/write-next")
async def write_next_episode(novel_id: str, background_tasks: BackgroundTasks):
    """Manually trigger generation of the next episode."""
    bp = store.get_blueprint(novel_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    written = len(store.list_episodes(novel_id))
    next_ep = written + 1
    if next_ep > bp.total_episodes:
        raise HTTPException(status_code=400, detail="All episodes for this novel have already been generated")

    background_tasks.add_task(generate_single_episode, novel_id, next_ep)
    return {"message": f"Writing of Chapter {next_ep} initiated in background"}

@router.get("/{novel_id}/episodes", response_model=List[EpisodeSummary])
async def list_episodes(novel_id: str):
    """List written episodes for a novel."""
    return store.list_episodes(novel_id)

@router.get("/{novel_id}/episodes/{episode_number}", response_model=EpisodeResponse)
async def get_episode(novel_id: str, episode_number: int):
    """Retrieve full text and behind-the-scenes actor data of a specific episode."""
    ep = store.get_episode(novel_id, episode_number)
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    return ep

@router.get("/{novel_id}/episodes/{episode_number}/image")
async def get_episode_image(novel_id: str, episode_number: int):
    """Serve the chapter illustration or dynamically generate it on demand."""
    img_data = store.get_episode_image(novel_id, episode_number)
    if img_data:
        data, mime_type = img_data
        return Response(content=data, media_type=mime_type, headers={"Cache-Control": "public, max-age=86400"})

    # Auto-generate if missing and episode exists
    bp = store.get_blueprint(novel_id)
    ep = store.get_episode(novel_id, episode_number)
    if not bp or not ep:
        raise HTTPException(status_code=404, detail="Episode or novel not found")

    data, mime_type, prompt = await chapter_image_client.generate(bp, ep)
    store.save_episode_image(novel_id, episode_number, data, mime_type)
    ep.image_url = f"/api/novels/{novel_id}/episodes/{episode_number}/image"
    ep.image_prompt = prompt
    store.save_episode(ep)

    return Response(content=data, media_type=mime_type, headers={"Cache-Control": "public, max-age=86400"})

@router.post("/{novel_id}/episodes/{episode_number}/generate-image")
async def generate_episode_image(novel_id: str, episode_number: int):
    """Regenerate the chapter artwork based on current settings and episode content."""
    bp = store.get_blueprint(novel_id)
    ep = store.get_episode(novel_id, episode_number)
    if not bp or not ep:
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

