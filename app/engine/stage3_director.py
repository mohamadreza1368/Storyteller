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

    is_final_chapter = (episode_number >= blueprint.total_episodes)
    final_mandate = (
        f"\n- FINAL CHAPTER MANDATE: This is Chapter {episode_number} of {blueprint.total_episodes} (THE FINAL CHAPTER). "
        "The story MUST conclude in this chapter! Block scenes that drive the ultimate confrontation, "
        "deliver the climax, and bring the narrative to a complete, definitive resolution."
    ) if is_final_chapter else ""

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
- Block 2 to 3 dynamic, distinct scenes that push the story forward from the end of Chapter {episode_number - 1} into Chapter {episode_number}.{final_mandate}

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
        c1 = char_names[(episode_number - 1) % c_count] if c_count > 0 else "Protagonist"
        c2 = char_names[episode_number % c_count] if c_count > 1 else c1
        l_count = len(locs)
        loc1 = locs[(episode_number - 1) % l_count] if l_count > 0 else f"District Center of {blueprint.world.city}"
        loc2 = locs[episode_number % l_count] if l_count > 1 else loc1
        premise_topic = blueprint.premise or f"the unfolding events across {blueprint.world.city}"

        if episode_number == 1:
            return {
                "scenes": [
                    {
                        "scene_number": 1,
                        "title": f"The Threshold at {loc1}",
                        "location": loc1,
                        "time_marker": "Late Twilight, Atmosphere Tense",
                        "pov_character": c1,
                        "present_characters": [c1],
                        "goal": f"{c1} assesses the immediate situation regarding {premise_topic}",
                        "conflict": f"Unexpected complications in {blueprint.world.city} indicate danger is closer than anticipated",
                        "resolution": f"{c1} commits to investigating further before retreat becomes impossible"
                    },
                    {
                        "scene_number": 2,
                        "title": f"Converging Paths at {loc2}",
                        "location": loc2,
                        "time_marker": "Nightfall",
                        "pov_character": c1,
                        "present_characters": [c1, c2],
                        "goal": f"Exchange vital information regarding {premise_topic}",
                        "conflict": f"{c2} expresses skepticism about the risks and questions {c1}'s motives",
                        "resolution": "A fragile alignment is established as the reality of the stakes sinks in"
                    }
                ]
            }
        elif episode_number < blueprint.total_episodes:
            return {
                "scenes": [
                    {
                        "scene_number": 1,
                        "title": f"Escalation at {loc1}",
                        "location": loc1,
                        "time_marker": "Morning, Growing Scrutiny",
                        "pov_character": c2,
                        "present_characters": [c1, c2],
                        "goal": f"Pursue key clues tied to the crisis in {blueprint.world.city}",
                        "conflict": "An opposing force or unexpected obstacle threatens to derail their plans",
                        "resolution": "A narrow breakthrough reveals deeper ramifications affecting both characters"
                    },
                    {
                        "scene_number": 2,
                        "title": f"Under Scrutiny at {loc2}",
                        "location": loc2,
                        "time_marker": "Late Night, Shadowed Streets",
                        "pov_character": c1,
                        "present_characters": [c1, c2],
                        "goal": "Confront the immediate consequences of their earlier discovery",
                        "conflict": "Secrets between the characters threaten to shatter their mutual cooperation",
                        "resolution": "They reach a critical turning point where neither can turn back"
                    }
                ]
            }
        else: # Final Chapter (Climax & Resolution)
            return {
                "scenes": [
                    {
                        "scene_number": 1,
                        "title": f"The Reckoning at {loc1}",
                        "location": loc1,
                        "time_marker": "Daybreak, High Tension",
                        "pov_character": c1,
                        "present_characters": [c1, c2],
                        "goal": f"Confront the central conflict of {premise_topic} head-on",
                        "conflict": "The full weight of the crisis reaches its peak; decisive action is demanded",
                        "resolution": f"The climax forces {c1} and {c2} to make irreversible choices that alter their destinies"
                    },
                    {
                        "scene_number": 2,
                        "title": f"Resolution in {blueprint.world.city} at {loc2}",
                        "location": loc2,
                        "time_marker": "Dusk, Settling Quiet",
                        "pov_character": c1,
                        "present_characters": [c1, c2],
                        "goal": "Face the aftermath and acknowledge what has been forever transformed",
                        "conflict": "Reconciling the sacrifices made with the dawn of a new reality",
                        "resolution": "The central story achieves lasting resolution and narrative closure"
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
