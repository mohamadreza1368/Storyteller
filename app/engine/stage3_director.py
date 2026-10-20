from typing import List, Optional, Any
from app.models.blueprint import StoryBlueprint
from app.models.simulation import SceneRecord, StoryMemory, StoryMatrix
from app.engine.llm_client import llm
from app.engine.prompts import SCENE_DIRECTOR_SYSTEM_PROMPT

async def execute_stage3(
    blueprint: StoryBlueprint,
    episode_number: int,
    memory: StoryMemory,
    matrix: Optional[StoryMatrix] = None,
    prior_episodes: Optional[List[Any]] = None
) -> List[SceneRecord]:
    """
    Stage 3: Scene Directing & Blocking for a specific episode.
    Ensures strict narrative continuity, forward plot advancement, and zero repetition.
    """

    chars = {c.key: c.core.name for c in blueprint.cast.characters}
    char_names = list(chars.values())
    locs = [l.name for l in blueprint.world.locations] or ["The Old Archives", "The Foggy Harbor", "The High Council Chamber"]

    # 1. Extract specific Matrix Event and Character Goals for this episode
    event_title = f"Chapter {episode_number}: Turning Points"
    event_desc = f"Key developments pushing the narrative arc of Chapter {episode_number}."
    char_goals_text = ""

    if matrix:
        for ev in getattr(matrix, "events", []):
            if ev.episode_number == episode_number:
                event_title = ev.title
                event_desc = ev.description
                break

        grid = getattr(matrix, "character_episode_grid", {}) or {}
        goals_lines = []
        for c in blueprint.cast.characters:
            c_goals = grid.get(c.key, []) or grid.get(c.core.name, [])
            if len(c_goals) >= episode_number:
                goals_lines.append(f"  * {c.core.name}: {c_goals[episode_number - 1]}")
        if goals_lines:
            char_goals_text = "\n" + "\n".join(goals_lines)

    # 2. Extract Prior Chapters Summary to enforce progression
    prior_summary_lines = []
    if prior_episodes:
        for ep in sorted(prior_episodes, key=lambda x: getattr(x, "episode_number", 0)):
            ep_num = getattr(ep, "episode_number", 0)
            if ep_num < episode_number:
                ep_t = getattr(ep, "title", f"Chapter {ep_num}")
                ep_s = getattr(ep, "summary", "")
                prior_summary_lines.append(f"- Chapter {ep_num} ('{ep_t}'): {ep_s}")

    prior_summary_block = "\n".join(prior_summary_lines) if prior_summary_lines else "None (This is Chapter 1 - Opening of the Novel)."

    user_prompt = f"""
Novel: "{blueprint.title}"
Current Chapter to Direct: Episode {episode_number} of {blueprint.total_episodes}
Planned Event for this Episode: "{event_title}"
Event Overview: {event_desc}
Character Objectives for Chapter {episode_number}:{char_goals_text or ' Drive their individual arcs forward.'}

NARRATIVE CONTINUITY & WHAT ALREADY HAPPENED:
{prior_summary_block}

Current Story Memory & Open Threads:
- Running Summary: {memory.running_summary or 'Story begins.'}
- Open Threads: {memory.open_threads or 'Initial mystery.'}

CRITICAL DIRECTORIAL MANDATE:
- You are directing CHAPTER {episode_number}. The events of preceding chapters have ALREADY OCCURRED.
- DO NOT REPEAT, restart, or rehash earlier scenes. The characters must be in new locations, facing escalating complications and new dilemmas.
- Block 2 to 3 dynamic, distinct scenes that push the story forward from the end of Chapter {episode_number - 1} into Chapter {episode_number}.

Available Cast: {char_names}
Available Locations: {locs}

Return strictly a JSON object matching this schema:
{{
  "scenes": [
    {{
      "scene_number": 1,
      "title": "Evocative Scene Title",
      "location": "{locs[(episode_number - 1) % len(locs)]}",
      "time_marker": "Atmospheric time marker",
      "pov_character": "{char_names[(episode_number - 1) % len(char_names)] if char_names else 'Julian'}",
      "present_characters": ["{char_names[0]}"],
      "goal": "Specific dramatic scene objective",
      "conflict": "Immediate obstacle or interpersonal friction",
      "resolution": "Scene outcome and psychological shift"
    }}
  ]
}}
"""

    async def fallback():
        c_count = len(char_names)
        c1 = char_names[(episode_number - 1) % c_count] if c_count > 0 else "Julian"
        c2 = char_names[episode_number % c_count] if c_count > 1 else c1
        l_count = len(locs)
        loc1 = locs[(episode_number - 1) % l_count] if l_count > 0 else "The Old Archives"
        loc2 = locs[episode_number % l_count] if l_count > 1 else loc1

        if episode_number == 1:
            return {
                "scenes": [
                    {
                        "scene_number": 1,
                        "title": f"The Shattered Seal at {loc1}",
                        "location": loc1,
                        "time_marker": "Late Twilight, Rain Beginning",
                        "pov_character": c1,
                        "present_characters": [c1],
                        "goal": f"{c1} searches the private repository to recover the anomalous record",
                        "conflict": "A second concealed lock mechanism resists intrusion as footsteps echo nearby",
                        "resolution": f"{c1} springs the lock and secures the document just before the door opens"
                    },
                    {
                        "scene_number": 2,
                        "title": f"Crossroads at {loc2}",
                        "location": loc2,
                        "time_marker": "Midnight, Damp Harbor Fog",
                        "pov_character": c1,
                        "present_characters": [c1, c2],
                        "goal": "Confront the intermediary and verify the ledger's authenticity",
                        "conflict": f"{c2} accuses {c1} of tampering with official records to protect family honor",
                        "resolution": "A tense standoff forces a reluctant pact to decipher the watermark together"
                    }
                ]
            }
        elif episode_number == 2:
            return {
                "scenes": [
                    {
                        "scene_number": 1,
                        "title": f"The Cipher of the Iron Seal at {loc1}",
                        "location": loc1,
                        "time_marker": "Dusk, Flickering Gaslight",
                        "pov_character": c2,
                        "present_characters": [c1, c2],
                        "goal": "Analyze the coded entries and identify the third party named in the margin",
                        "conflict": "The ink has been chemically degraded; deciphering reveals a signature from the high magistracy",
                        "resolution": "Both realize the conspiracy is not historical, but actively operating within the city"
                    },
                    {
                        "scene_number": 2,
                        "title": f"Under Surveillance at {loc2}",
                        "location": loc2,
                        "time_marker": "Past Midnight, Low Tide",
                        "pov_character": c1,
                        "present_characters": [c1, c2],
                        "goal": "Intercept the courier vessel before the contraband evidence is moved overseas",
                        "conflict": "Shadowy figures surround the pier; an unexpected whistle signals an ambush",
                        "resolution": "They barely escape through the sluice gates, but lose the cipher key in the water"
                    }
                ]
            }
        elif episode_number == 3:
            return {
                "scenes": [
                    {
                        "scene_number": 1,
                        "title": f"Fractured Alliances at {loc1}",
                        "location": loc1,
                        "time_marker": "Pre-Dawn Cold",
                        "pov_character": c1,
                        "present_characters": [c1, c2],
                        "goal": "Bandage wounds and confront the shocking revelation that one of them was followed",
                        "conflict": "Accusations of betrayal flare when an official warrant bearing {c2}'s family insignia is found",
                        "resolution": "A bitter confession reveals the depth of coercion exerted by the council"
                    },
                    {
                        "scene_number": 2,
                        "title": f"The Crucible of Reckoning at {loc2}",
                        "location": loc2,
                        "time_marker": "Gloomy Morning, Thunder Rolling",
                        "pov_character": c2,
                        "present_characters": [c1, c2],
                        "goal": "Infiltrate the inner sanctum to confront the primary architect of the silence",
                        "conflict": "The architect calmly burns the remaining ledgers, daring them to present unverified claims",
                        "resolution": "A decisive confrontation forces a moral sacrifice to preserve the surviving testimony"
                    }
                ]
            }
        else: # Chapter 4+ Final Reckoning / Resolution
            return {
                "scenes": [
                    {
                        "scene_number": 1,
                        "title": f"The Final Gathering at {loc1}",
                        "location": loc1,
                        "time_marker": "Overcast Noon",
                        "pov_character": c1,
                        "present_characters": [c1, c2],
                        "goal": "Assemble the fragments of surviving testimony before the public hearing",
                        "conflict": "An ultimatum arrives demanding total silence in exchange for immunity and restoration of titles",
                        "resolution": f"{c1} and {c2} decisively reject the compromise, choosing exposure over safety"
                    },
                    {
                        "scene_number": 2,
                        "title": f"Echoes in the City at {loc2}",
                        "location": loc2,
                        "time_marker": "Evening, Rain Clearing into Stars",
                        "pov_character": c1,
                        "present_characters": [c1, c2],
                        "goal": "Deliver the final testament and assess the transformed reality of their lives",
                        "conflict": "The irreversible weight of what was lost versus the fragile freedom of truth",
                        "resolution": "The silence of twenty years is broken forever; an unwritten chapter begins"
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
