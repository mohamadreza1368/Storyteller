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

    target_words = max(blueprint.words_per_episode or 1800, 1800)
    user_prompt = f"""
Novel: "{blueprint.title}"
Episode: {episode_number} of {blueprint.total_episodes}
Primary POV Character: {pov_char}
Target Word Count: around {target_words} words of literary fiction

STAGED SCENES, DRAMATIC CONFLICTS, AND MULTI-AGENT CHARACTER TURNS:
{full_scenes_prompt}

INSTRUCTIONS FOR WRITING:
1. Write a complete, richly detailed, unhurried chapter in English (around {target_words} words).
2. Fully flesh out EVERY staged scene with sensory ambiance, psychological interiority, dialogue, and body language. Do NOT summarize or skip scenes.
3. Separate distinct scenes using the authentic scene divider:
   ✦
4. Format the final output strictly as:
[TITLE]: Evocative Chapter Title
[SUMMARY]: Two-sentence summary of the chapter's key events
[TEXT]:
(Full prose of the chapter begins here)
"""

    async def fallback():
        c_title = f"Chapter {episode_number}: Shadows Along the Water"
        c_summary = f"A tense confrontation in the rain-drenched archives uncovers the first anomalous clue, forcing ancient loyalties into question as old wounds resurface."
        
        # Scene 1: Arrival & Setting the Atmosphere
        s1_p1 = f"A heavy, damp mist crept off the river and settled over the limestone facades of {blueprint.world.city}. Street lamps flickered like tired sentinels through the gloom, amber halos bleeding into the rain that drummed an uneven rhythm against the leaded panes. The air carried the familiar scent of coal soot, wet cobbles, and decaying autumn leaves—the very perfume of a past {pov_char} had spent a decade attempting to outrun. Every breath tasted faintly of iron and damp wool."
        s1_p2 = f"Inside the archives, the silence possessed weight. It was not merely the absence of sound, but an accumulated gravity forged by centuries of parchment, bindings, and official silences. Every oak plank beneath his boots groaned with age, as though thirty years of whispered betrayals remained trapped between the lime-washed walls. He paused before the tall card catalogue, his hand hovering over the brass drawer pulls. The chill of the metal seeped into his fingertips before he had even made contact."
        s1_p3 = f"{pov_char} ran his fingertips across the velvet rim of the desk chair, steadying himself against a sudden wave of vertigo. The texture was rough, worn thin by hands long buried in the municipal cemetery. For twenty years, the official narrative had stood uncontested: a simple clerical error, an archive ledger misfiled during the restructuring. But as he pulled the dossier from beneath the false bottom of the cedar crate, the ink told a vastly different story."
        s1_p4 = f"The documents were bound with crimson ribbon that had faded to the shade of dried brick. On the cover sheet, a signature appeared in bold, angular strokes—a signature he would have recognized anywhere, even in the dim light filtering through the fanlight above. His pulse thudded in his ears, rhythmic and unrelenting. 'So it was never lost,' he murmured to the empty room. 'It was buried.'"
        scene1 = f"{s1_p1}\n\n{s1_p2}\n\n{s1_p3}\n\n{s1_p4}"

        # Scene 2: The Confrontation
        s2_p1 = f"The sound of the outer door latch clicking into place cut through the quiet like a blade through silk. Footsteps approached along the tiled corridor—deliberate, measured, without the hurried haste of an intruder. Whoever had entered knew the building's geometry as intimately as he did. {pov_char} did not turn immediately; instead, he carefully closed the ledger, his thumb lingering on the embossed leather binding."
        s2_p2 = f"When their gazes collided across the half-shadowed reading room, words ceased to function as mere conversation. Every syllable uttered was calculated, not to vindicate the truth, but to buy precious seconds against an inevitable storm. In the tightening knot of mutual suspicion, even breathing felt like a negotiated surrender. Shadows stretched between them across the long oak conference table, dividing the lamplight into hostile territories."
        s2_p3 = f"'You shouldn't have returned to {blueprint.world.city},' the other said quietly, removing leather gloves finger by finger with excruciating patience. 'Some archives are kept closed not out of malice, but out of mercy. You think you're unearthing justice, but you are merely disturbing ghosts that have made peace with their graves.' The voice was steady, carrying the practiced calm of someone accustomed to administering difficult decrees."
        s2_p4 = f"{pov_char} felt the cold sting of betrayal settle into his chest, sharp and familiar. 'Mercy is a luxury reserved for the architects of the silence,' he countered, his voice barely above a whisper yet cutting through the gloom. 'My family didn't receive mercy when the ledger vanished. They received disgrace and exile. If the ghosts are disturbed tonight, they have you to hold accountable.'"
        scene2 = f"{s2_p1}\n\n{s2_p2}\n\n{s2_p3}\n\n{s2_p4}"

        # Scene 3: Aftermath & Cliffhanger
        s3_p1 = f"Outside, the rain intensified, lashing against the high clerestory windows with renewed ferocity. The brass mantle clock behind the librarian's desk began its slow, deliberate chime, striking the midnight hour. Each toll reverberated through the iron rafters, measuring the collapse of whatever fragile peace had remained between them."
        s3_p2 = f"Neither of them moved toward the doorway. The ledger lay between them on the scarred varnish, a wedge driven deep into the heart of the district's foundational order. What had begun as a solitary search for personal vindication had expanded into something far more dangerous: a crack in the veneer of an entire institution."
        s3_p3 = f"As the final chime faded into the drumming downpour, the illusion of neutrality was irrevocably shattered. The city outside lay quiet under the black sky, its gas lamps flickering against the river fog, unaware that the first stone in the wall of silence had just been dislodged."
        scene3 = f"{s3_p1}\n\n{s3_p2}\n\n{s3_p3}"

        full = f"{scene1}\n\n✦\n\n{scene2}\n\n✦\n\n{scene3}"
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
