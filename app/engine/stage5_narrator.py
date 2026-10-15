from typing import List, Tuple
from app.models.blueprint import StoryBlueprint
from app.models.simulation import SceneRecord, StoryMemory
from app.engine.llm_client import llm
from app.engine.prompts import NARRATOR_SYSTEM_PROMPT

async def execute_stage5(
    blueprint: StoryBlueprint,
    episode_number: int,
    scenes: List[SceneRecord],
    memory: StoryMemory
) -> Tuple[str, str, str]:
    """
    Stage 5: Master Narrator / Novelist Prose Synthesis in English.
    Converts simulated scenes and multi-agent character turns into refined literary fiction.
    Returns: (title, summary, full_content)
    """

    pov_char = scenes[0].pov_character_key if scenes else "Narrator"
    
    scenes_description = []
    for sc in scenes:
        turns_text = "\n".join([
            f"  - {t.character_key}:\n    Action: {t.action}\n    Dialogue: \"{t.dialogue}\"\n    Emotion: {t.emotion}\n    Secret Thought: {t.thought}"
            for t in sc.turns
        ])
        scenes_description.append(
            f"### Scene {sc.scene_number}: {sc.title}\n"
            f"Setting: {sc.location_key} | Time: {sc.time_marker}\n"
            f"POV: {sc.pov_character_key}\n"
            f"Goal & Conflict: {sc.goal} | Obstacle: {sc.conflict}\n"
            f"Actors & Staged Turns:\n{turns_text}\n"
            f"Resolution: {sc.resolution}\n"
        )

    full_scenes_prompt = "\n\n".join(scenes_description)

    sys_prompt = NARRATOR_SYSTEM_PROMPT.format(
        prose_style=blueprint.style.prose_style,
        tone=blueprint.style.tone,
        perspective=blueprint.style.perspective
    )

    user_prompt = f"""
Novel: "{blueprint.title}"
Episode: {episode_number} of {blueprint.total_episodes}
Primary POV Character: {pov_char}
Approximate Target Word Count: around {blueprint.words_per_episode} words

Staged scenes, actions, and multi-agent character dialogue:
{full_scenes_prompt}

Write a complete, gripping, beautifully paced chapter in English.
Include an evocative chapter title and a brief two-sentence summary formatted exactly as:
[TITLE]: Chapter Title
[SUMMARY]: Two-sentence summary of the chapter's key events
[TEXT]:
(Complete chapter prose begins here)
"""

    async def fallback():
        c_title = f"Chapter {episode_number}: Whispers in the Fog"
        c_summary = f"A tense confrontation in the rain-drenched archives uncovers the first anomalous clue, forcing ancient loyalties into question."
        
        p1 = f"A heavy, damp mist crept off the river and settled over the limestone facades of {blueprint.world.city}. Street lamps flickered like tired sentinels through the gloom, amber halos bleeding into the rain. The air carried the familiar scent of soot, wet cobbles, and decaying autumn leaves—the very perfume of a past {pov_char} had spent a decade attempting to outrun."
        p2 = f"Inside the archives, the silence possessed weight. Every plank beneath his boots groaned with age, as though thirty years of whispered betrayals remained trapped between the lime-washed walls. {pov_char} ran his fingertips across the velvet rim of the desk chair, steadying himself. The texture was rough, worn thin by hands long buried."
        p3 = f"When their gazes collided across the half-shadowed reading room, words ceased to function as mere conversation. Every syllable uttered was calculated, not to vindicate the truth, but to buy precious seconds against an inevitable storm. In the tightening knot of mutual suspicion, even breathing felt like a negotiated surrender."
        p4 = f"As the brass mantle clock tolled the midnight hour, the illusion of neutrality shattered. Neither of them would leave this room untouched by what had been unearthed. The game had shifted, and the city itself seemed to hold its breath for dawn."
        
        full = f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}"
        return f"[TITLE]: {c_title}\n[SUMMARY]: {c_summary}\n[TEXT]:\n{full}"

    raw_output = await llm.generate_text(sys_prompt, user_prompt, fallback_generator=fallback)

    title = f"Chapter {episode_number}"
    summary = ""
    content = raw_output

    if "[TITLE]:" in raw_output and "[TEXT]:" in raw_output:
        parts = raw_output.split("[TEXT]:")
        header = parts[0]
        content = parts[1].strip() if len(parts) > 1 else raw_output

        for line in header.split("\n"):
            line = line.strip()
            if line.startswith("[TITLE]:"):
                title = line.replace("[TITLE]:", "").strip()
            elif line.startswith("[SUMMARY]:"):
                summary = line.replace("[SUMMARY]:", "").strip()

    return title, summary, content
