from typing import List, Tuple, Optional, Any
from app.models.blueprint import StoryBlueprint
from app.models.simulation import SceneRecord, StoryMemory
from app.engine.llm_client import llm
from app.engine.prompts import NARRATOR_SYSTEM_PROMPT

async def execute_stage5(
    blueprint: StoryBlueprint,
    episode_number: int,
    scenes: List[SceneRecord],
    memory: StoryMemory,
    prior_episodes: Optional[List[Any]] = None
) -> Tuple[str, str, str]:
    """
    Stage 5: Master Narrator / Novelist Prose Synthesis.
    Converts simulated scenes and multi-agent character turns into expansive literary fiction.
    Guarantees progressive, non-repeating chapters across the novel arc.
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
            f"Goal: {sc.goal}\n"
            f"Conflict & Obstacle: {sc.conflict}\n"
            f"Staged Actor Turns:\n{turns_text}\n"
            f"Resolution: {sc.resolution}\n"
        )

    full_scenes_prompt = "\n\n".join(scenes_description)

    # Prior episodes continuity
    prior_summary_lines = []
    if prior_episodes:
        for ep in sorted(prior_episodes, key=lambda x: getattr(x, "episode_number", 0)):
            ep_n = getattr(ep, "episode_number", 0)
            if ep_n < episode_number:
                t = getattr(ep, "title", f"Chapter {ep_n}")
                s = getattr(ep, "summary", "")
                prior_summary_lines.append(f"- Chapter {ep_n} ('{t}'): {s}")

    prior_text = "\n".join(prior_summary_lines) if prior_summary_lines else "None (Opening Chapter of the Novel)."

    sys_prompt = NARRATOR_SYSTEM_PROMPT.format(
        prose_style=blueprint.style.prose_style,
        tone=blueprint.style.tone,
        perspective=blueprint.style.perspective
    )

    target_words = min(max(blueprint.words_per_episode or 1800, 1200), 2800)
    is_final_chapter = (episode_number >= blueprint.total_episodes)
    final_closure_directive = (
        f"\nCRITICAL FINAL CHAPTER DIRECTIVE:\n"
        f"- This is Chapter {episode_number} of {blueprint.total_episodes} (THE FINAL CHAPTER of the novel).\n"
        f"- Bring the central premise and overarching conflict to a definitive climax and resolution.\n"
        f"- Tie up open mysteries and provide deep, memorable closure for the characters.\n"
        f"- End the book conclusively with a powerful, resonant final passage.\n"
    ) if is_final_chapter else ""

    user_prompt = f"""
Novel: "{blueprint.title}"
Episode to Write: Chapter {episode_number} of {blueprint.total_episodes}
Primary POV Character: {pov_char}
Target Word Count: around {target_words} words of literary prose (STRICT MAX: 3,000 words)

WHAT TRANSPIRED IN PRIOR CHAPTERS:
{prior_text}

CRITICAL CONTINUITY DIRECTIVE:
- Do NOT rewrite or restart the beginning of the book. The previous chapters have already taken place.
- Pick up the story directly from the staged scenes for Chapter {episode_number}.
- Fully dramatize EVERY scene below, weaving in the multi-agent spoken dialogue and physical staging.
- STRICT LENGTH DIRECTIVE: Keep the chapter focused and impactful (around {target_words} words). Under no circumstances exceed 3,000 words.
- Separate distinct scenes using the authentic scene divider:
  ✦
{final_closure_directive}
STAGED SCENES AND ACTOR TURNS FOR CHAPTER {episode_number}:
{full_scenes_prompt}

Format the final output strictly as:
[TITLE]: Chapter Title
[SUMMARY]: Two-sentence summary of the chapter's key events
[TEXT]:
(Complete chapter prose begins here)
"""

    async def fallback():
        # Dynamically synthesize unique, non-repeating prose from the actual staged scenes
        c_title = f"Chapter {episode_number}: {scenes[0].title if scenes else 'The Turning Tide'}"
        c_summary = (
            f"In Chapter {episode_number}, events escalate as {pov_char} navigates tensions at "
            f"{scenes[0].location_key if scenes else blueprint.world.city}. "
            f"The encounter deepens existing fractures and propels the narrative toward irreversible change."
        )

        rendered_scenes = []
        for s_idx, sc in enumerate(scenes):
            scene_paragraphs = []
            
            # Atmospheric opening paragraph tailored to this scene
            if episode_number == 1 and s_idx == 0:
                p_intro = (
                    f"A damp, persistent chill clung to the stone facades of {blueprint.world.city}. "
                    f"At {sc.location_key}, beneath the heavy shadows of {sc.time_marker.lower()}, "
                    f"{sc.pov_character_key} stood motionless for a lingering heartbeat, taking measure of the silence. "
                    f"The air smelled of wet asphalt, extinguished coal, and aged lime—the distinct scent of secrets "
                    f"that had spent years waiting to be unearthed. Every instinct urged caution, yet the objective "
                    f"({sc.goal.lower()}) left no room for hesitation."
                )
            elif episode_number == 2 and s_idx == 0:
                p_intro = (
                    f"By the time the events of yesterday had settled into the collective memory of the district, "
                    f"the quiet at {sc.location_key} had taken on a razor-sharp edge. The sky was an unforgiving slate grey, "
                    f"and {sc.time_marker.lower()} brought with it a sudden gust that rattled the high clerestory panes. "
                    f"{sc.pov_character_key} surveyed the room with narrowed eyes, acutely aware that the trail was growing colder. "
                    f"The immediate challenge—{sc.conflict.lower()}—loomed larger with every passing second."
                )
            elif episode_number == 3 and s_idx == 0:
                p_intro = (
                    f"The fragile pretense of neutrality had completely unraveled. In the grim expanse of {sc.location_key}, "
                    f"amidst the biting cold of {sc.time_marker.lower()}, the stakes were no longer speculative. "
                    f"{sc.pov_character_key} could feel the tightening net of scrutiny closing in from every avenue of {blueprint.world.city}. "
                    f"There was a palpable weight in the room, born of the mounting friction: {sc.conflict.lower()}."
                )
            else:
                p_intro = (
                    f"The atmosphere at {sc.location_key} carried the unmistakable stillness that precedes a reckoning. "
                    f"As {sc.time_marker.lower()} approached, shadows lengthened across the scarred woodwork and weathered stone. "
                    f"{sc.pov_character_key} took a slow breath, steadying a heartbeat that had raced through hours of pursuit. "
                    f"Every thread of the investigation had led inexorably to this location, where {sc.goal.lower()} would finally be tested."
                )
            scene_paragraphs.append(p_intro)

            # Dramatize the conflict and staged turns
            if sc.turns:
                for t in sc.turns:
                    p_turn = (
                        f"{t.action} "
                        f"When words finally came, they carried the quiet force of an indictment: \"{t.dialogue}\" "
                        f"Beneath the surface, however, thoughts remained tightly guarded. "
                        f"{t.character_key} turned the matter over in secret, reflecting that {t.thought.lower()} "
                        f"The emotional current in the room shifted to {t.emotion.lower()}, charging the silence between them with unspoken peril."
                    )
                    scene_paragraphs.append(p_turn)
            else:
                p_solo = (
                    f"{sc.pov_character_key} moved with deliberate care across {sc.location_key}, conscious of every creaking board and sudden whisper. "
                    f"The obstacle was immediate and relentless: {sc.conflict}. Every passing minute without progress risked exposing the entire undertaking "
                    f"to those who guarded the status quo with unyielding vigilance."
                )
                scene_paragraphs.append(p_solo)

            # Scene resolution paragraph
            p_res = (
                f"As the tension reached its zenith, the immediate outcome shifted decisively. {sc.resolution} "
                f"Looking back across the space of {sc.location_key}, it was clear that the balance of power had irrevocably altered. "
                f"Neither of them would face the coming hours unchanged by what had just transpired."
            )
            scene_paragraphs.append(p_res)

            rendered_scenes.append("\n\n".join(scene_paragraphs))

        full_prose = "\n\n✦\n\n".join(rendered_scenes)
        return f"[TITLE]: {c_title}\n[SUMMARY]: {c_summary}\n[TEXT]:\n{full_prose}"

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
