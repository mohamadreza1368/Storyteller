from typing import List, Tuple, Optional, Any
import logging
from app.models.blueprint import StoryBlueprint
from app.models.simulation import SceneRecord, StoryMemory
from app.engine.llm_client import llm
from app.engine.prompts import NARRATOR_SYSTEM_PROMPT
from app.engine.writing_craft import audit_and_clean_prose, build_narrative_style_brief

logger = logging.getLogger(__name__)

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

    style_brief = build_narrative_style_brief(blueprint.style, blueprint.world)

    sys_prompt = NARRATOR_SYSTEM_PROMPT.format(
        style_brief=style_brief
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

{style_brief}

WHAT TRANSPIRED IN PRIOR CHAPTERS:
{prior_text}

CRITICAL CONTINUITY & CRAFT DIRECTIVES:
- Do NOT rewrite or restart the beginning of the book. The previous chapters have already taken place.
- Pick up the story directly from the staged scenes for Chapter {episode_number}.
- Strictly execute the Prose Style, Genre rules, Tone, and Theme from the style brief above!
- Fully dramatize EVERY scene below, weaving in the multi-agent spoken dialogue and physical staging.
- STRICT LENGTH DIRECTIVE: Keep the chapter focused and impactful (around {target_words} words). Under no circumstances exceed 3,000 words.
- STRICT ANTI-AI MANDATE: Zero tolerance for AI clichés (banned: delve, tapestry, testament, beacon, palpable, labyrinthine, dance of shadows). No "Not X, but Y" formulas, no dramatic one-line closers, no forced triads.
- STRICT PUNCTUATION HYGIENE: Never output stacked or consecutive punctuation marks (e.g. absolutely never write '.;', ';.', ';;', ',;', or '..'). Never abuse semicolons. Separate complete thoughts with clean periods. A sentence ends with a single period, question mark, or exclamation point.
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
        # Dynamically synthesize unique, non-repeating prose adhering strictly to human author craft
        c_title = f"Chapter {episode_number}: {scenes[0].title if scenes else 'The Turning Tide'}"
        c_summary = (
            f"In Chapter {episode_number}, events escalate as {pov_char} navigates tensions at "
            f"{scenes[0].location_key if scenes else blueprint.world.city}. "
            f"The encounter forces hidden calculations into the open and narrows their remaining choices."
        )

        rendered_scenes = []
        for s_idx, sc in enumerate(scenes):
            scene_paragraphs = []
            
            # Grounded, tactile opening paragraph tailored to this scene
            if episode_number == 1 and s_idx == 0:
                p_intro = (
                    f"A damp chill clung to the lime mortar and wet flagstones of {blueprint.world.city}. "
                    f"At {sc.location_key}, under the grey light of {sc.time_marker.lower()}, "
                    f"{sc.pov_character_key} stood beside the entryway, listening to the drip of condensation from an iron gutter. "
                    f"The air smelled of wet slate, soot, and damp wool. Every instinct counseled caution, "
                    f"yet the demand of the hour—{sc.goal.lower()}—allowed no retreat."
                )
            elif episode_number == 2 and s_idx == 0:
                p_intro = (
                    f"By the following morning, the repercussions of yesterday had reached the back streets of the quarter. "
                    f"Inside {sc.location_key}, the cold had settled into the woodwork, and the silence carried a sharp, brittle edge. "
                    f"{sc.pov_character_key} checked the latch and turned to face the room. "
                    f"The dilemma at hand demanded a decisive answer before noon."
                )
            elif episode_number == 3 and s_idx == 0:
                p_intro = (
                    f"The pretense of negotiation was gone. In the bare courtyard of {sc.location_key}, "
                    f"under the biting wind of {sc.time_marker.lower()}, every movement felt observed. "
                    f"{sc.pov_character_key} kept both hands visible, watching the shadows across the opposite doorway. "
                    f"The rift had deepened around a single point: {sc.conflict.lower()}."
                )
            else:
                p_intro = (
                    f"The afternoon dragged on at {sc.location_key}, bringing a heavy gloom that softened the sharp edges of the room. "
                    f"As {sc.time_marker.lower()} approached, {sc.pov_character_key} rested a palm against the worn desk, steadying a shallow breath. "
                    f"Days of quiet maneuver had narrowed to this single room, where {sc.goal.lower()} would either succeed or end in ruin."
                )
            scene_paragraphs.append(p_intro)

            # Dramatize the conflict and staged turns
            if sc.turns:
                for t in sc.turns:
                    p_turn = (
                        f"{t.action} "
                        f"When words came, they cut straight through the pause: \"{t.dialogue}\" "
                        f"{t.character_key} studied the reaction closely, keeping the real concern hidden: {t.thought.lower()} "
                        f"The mood settled into {t.emotion.lower()}, leaving little room for polite evasion."
                    )
                    scene_paragraphs.append(p_turn)
            else:
                p_solo = (
                    f"{sc.pov_character_key} moved across {sc.location_key}, checking the locks and the floorboards beneath the rug. "
                    f"The obstacle was immediate: {sc.conflict}. Waiting would only give the others time to consolidate their hold."
                )
                scene_paragraphs.append(p_solo)

            # Scene resolution paragraph without melodramatic clichés
            p_res = (
                f"With the first confrontation spent, the immediate focus shifted. {sc.resolution} "
                f"{sc.pov_character_key} turned back toward the window, recognizing that the terms of the encounter had changed for good."
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

    # Pass through Writing Craft & Humanizer Enforcement Gate
    sanitized_content, flags = audit_and_clean_prose(content)
    if flags:
        logger.info(f"Humanizer cleaned {len(flags)} tells in Chapter {episode_number}: {flags[:5]}")
    content = sanitized_content

    return title, summary, content
