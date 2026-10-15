from typing import List
from app.models.blueprint import StoryBlueprint
from app.models.simulation import SceneRecord, StoryMemory
from app.engine.llm_client import llm
from app.engine.prompts import SCENE_DIRECTOR_SYSTEM_PROMPT

async def execute_stage3(
    blueprint: StoryBlueprint,
    episode_number: int,
    memory: StoryMemory
) -> List[SceneRecord]:
    """Stage 3: Scene Directing & Blocking for a specific episode in English."""

    chars = {c.key: c.core.name for c in blueprint.cast.characters}
    locs = [l.name for l in blueprint.world.locations] or ["The Old Archives", "The Foggy Harbor"]
    char_names = list(chars.values())

    user_prompt = f"""
Novel: "{blueprint.title}"
Episode Number: {episode_number} of {blueprint.total_episodes}
Running Narrative Summary so far: {memory.running_summary or 'Beginning of the novel'}
Active Open Threads: {memory.open_threads}
Cast: {char_names}
Available Locations: {locs}

Your Directorial Mission: Block and deconstruct this episode into 2 to 3 dramatic, vibrant scenes.
For each scene specify:
1. Exact location and atmospheric time marker.
2. POV Character.
3. Present characters.
4. Dramatic scene goal.
5. Conflict / Obstacle.
6. Scene outcome / Resolution.

Return ONLY a JSON object matching this schema:
{{
  "scenes": [
    {{
      "scene_number": 1,
      "title": "Evocative Scene Title",
      "location": "{locs[0]}",
      "time_marker": "Late Twilight",
      "pov_character": "{char_names[0]}",
      "present_characters": ["{char_names[0]}"],
      "goal": "Scene objective",
      "conflict": "Immediate obstacle or friction",
      "resolution": "Outcome and psychological shift"
    }}
  ]
}}
"""

    async def fallback():
        c1 = char_names[0] if char_names else "Julian"
        c2 = char_names[1] if len(char_names) > 1 else c1
        l1 = locs[0] if locs else "The Old Archives"
        l2 = locs[1] if len(locs) > 1 else l1
        return {
            "scenes": [
                {
                    "scene_number": 1,
                    "title": "Shadows in the Stacks",
                    "location": l1,
                    "time_marker": "Late Dusk, Rain Falling",
                    "pov_character": c1,
                    "present_characters": [c1, c2],
                    "goal": f"{c1} seeks to inspect the watermarked records without raising suspicion",
                    "conflict": f"{c2} arrives unannounced, demanding answers regarding the missing ledger",
                    "resolution": "An evasive verbal duel peaks when a handwritten note slips to the floor"
                },
                {
                    "scene_number": 2,
                    "title": "Behind Closed Doors",
                    "location": l2,
                    "time_marker": "Midnight, Harbor Fog",
                    "pov_character": c2,
                    "present_characters": [c2],
                    "goal": f"Verify the handwriting on the newly discovered document against known records",
                    "conflict": "Gnawing doubt and the realization that a trusted mentor is implicated",
                    "resolution": "A firm decision is reached to confront the syndicate at dawn"
                }
            ]
        }

    data = await llm.generate_json(SCENE_DIRECTOR_SYSTEM_PROMPT, user_prompt, fallback_generator=fallback)

    name_to_key = {c.core.name: c.key for c in blueprint.cast.characters}
    loc_name_to_key = {l.name: l.key for l in blueprint.world.locations}

    scenes = []
    for s_idx, s in enumerate(data.get("scenes", [])):
        pov_name = s.get("pov_character", "")
        pov_key = name_to_key.get(pov_name, pov_name)
        
        present_keys = [name_to_key.get(name, name) for name in s.get("present_characters", [])]
        if pov_key not in present_keys:
            present_keys.insert(0, pov_key)

        loc_name = s.get("location", "")
        loc_key = loc_name_to_key.get(loc_name, loc_name)

        scenes.append(SceneRecord(
            scene_number=s_idx + 1,
            title=s.get("title", f"Scene {s_idx + 1}"),
            location_key=loc_name,
            time_marker=s.get("time_marker", "Day"),
            pov_character_key=pov_name,
            character_keys=s.get("present_characters", [pov_name]),
            goal=s.get("goal", ""),
            conflict=s.get("conflict", ""),
            resolution=s.get("resolution", ""),
            turns=[]
        ))

    return scenes
