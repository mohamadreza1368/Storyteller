from typing import List, Optional, Callable, Awaitable
from app.models.blueprint import StoryBlueprint
from app.models.character import Character
from app.models.simulation import SceneRecord, CharacterTurn, StoryMemory
from app.engine.llm_client import llm
from app.engine.prompts import CHARACTER_ACTOR_SYSTEM_PROMPT

async def execute_stage4(
    blueprint: StoryBlueprint,
    scenes: List[SceneRecord],
    memory: StoryMemory,
    log_callback: Optional[Callable[[str], Awaitable[None]]] = None
) -> List[SceneRecord]:
    """
    Stage 4: Autonomous Multi-Agent Character Roleplay & Dialogue.
    Each character runs as an independent LLM instance with their own dedicated
    System Prompt, reacting dynamically to the words and actions of other character agents.
    """
    char_map = {c.core.name: c for c in blueprint.cast.characters}
    for c in blueprint.cast.characters:
        char_map[c.key] = c

    for scene in scenes:
        scene_history: List[CharacterTurn] = []
        present_chars = [char_map[name] for name in scene.character_keys if name in char_map]
        if not present_chars and blueprint.cast.characters:
            present_chars = blueprint.cast.characters[:2]

        # Multi-turn conversational rounds between agents in this scene
        rounds = 2 if len(present_chars) > 1 else 1
        for round_idx in range(rounds):
            for char in present_chars:
                # Use the dedicated system prompt stored on the character if present
                if getattr(char, "system_prompt", None):
                    sys_prompt = char.system_prompt
                else:
                    sys_prompt = CHARACTER_ACTOR_SYSTEM_PROMPT.format(
                        name=char.core.name,
                        occupation=char.core.occupation or "Unknown",
                        age=char.core.age or 30,
                        temperament=char.core.temperament or "Idealist",
                        values=", ".join(char.core.values) if char.core.values else "Truth",
                        want=char.motivation.want,
                        need=char.motivation.need,
                        flaw=char.motivation.flaw,
                        secret=char.motivation.secret,
                        voice=char.behavior.voice or "Measured and natural",
                        knowledge=" | ".join(char.state.knowledge) if char.state.knowledge else "General opening knowledge"
                    )

                history_str = "\n".join([
                    f"- {t.character_key}: [Action: {t.action}] [Dialogue: \"{t.dialogue}\"]"
                    for t in scene_history
                ]) if scene_history else "The scene has just commenced; no dialogue spoken yet."

                last_exchange_directive = ""
                if scene_history:
                    last_turn = scene_history[-1]
                    if last_turn.character_key != char.core.name:
                        last_exchange_directive = (
                            f"\nIMMEDIATE INTERPERSONAL CUE TO ADDRESS:\n"
                            f"{last_turn.character_key} just said: \"{last_turn.dialogue}\"\n"
                            f"{last_turn.character_key}'s physical action: {last_turn.action}\n"
                            f"Directly reply and react to {last_turn.character_key}! Speak naturally in dialogue and describe your bodily reaction.\n"
                        )

                user_prompt = f"""Scene Context: "{scene.title}"
Location: {scene.location_key} | Time: {scene.time_marker}
Scene Dramatic Goal: {scene.goal}
Immediate Conflict: {scene.conflict}

Dialogue & Action History So Far:
{history_str}
{last_exchange_directive}
It is your turn, {char.core.name}. Express your physical action, spoken words, and secret internal thought.
Return strictly a JSON object matching this schema:
{{
  "action": "Physical movement, posture, or tactical body language",
  "dialogue": "Exact spoken words addressing the present characters (or 'Silence')",
  "thought": "Raw internal thoughts and calculations that remain entirely secret to you alone",
  "emotion": "Current emotional state",
  "knowledge_gain": "Any new deduction or fact learned just now (or null)"
}}
"""

                async def fallback_turn(c=char, r=round_idx, sc=scene, hist=scene_history):
                    other_name = [p.core.name for p in present_chars if p.core.name != c.core.name]
                    target_name = other_name[0] if other_name else "the room"
                    if r == 0:
                        return {
                            "action": f"{c.core.name} paused beside the table at {sc.location_key}, assessing the rising tension caused by {sc.conflict.lower()}.",
                            "dialogue": f"We cannot afford missteps now, {target_name}. Look at what is happening with {sc.goal.lower()}.",
                            "thought": f"I must protect my aim ({c.motivation.want or 'the truth'}) before this situation slips entirely beyond my control.",
                            "emotion": "Tense and observant",
                            "knowledge_gain": f"Recognized the immediate danger posed by {sc.conflict}."
                        }
                    else:
                        return {
                            "action": f"{c.core.name} took a decisive step forward in {sc.location_key}, voice dropping to an urgent whisper.",
                            "dialogue": f"Whatever happens next, {target_name}, we have crossed the threshold. We see this through to {sc.resolution.lower()}.",
                            "thought": f"Even if my secret ({c.motivation.secret or 'motives'}) is tested, retreat is no longer an option.",
                            "emotion": "Resolute and determined",
                            "knowledge_gain": f"Committed to seeing through {sc.resolution}."
                        }

                turn_data = await llm.generate_json(
                    sys_prompt,
                    user_prompt,
                    fallback_generator=lambda c=char, r=round_idx, sc=scene, h=scene_history: fallback_turn(c, r, sc, h)
                )

                turn = CharacterTurn(
                    character_key=char.core.name,
                    action=turn_data.get("action", ""),
                    dialogue=turn_data.get("dialogue", ""),
                    thought=turn_data.get("thought", ""),
                    emotion=turn_data.get("emotion", "Engaged"),
                    knowledge_gain=turn_data.get("knowledge_gain")
                )

                if turn.knowledge_gain and turn.knowledge_gain not in char.state.knowledge:
                    char.state.knowledge.append(turn.knowledge_gain)
                char.state.emotion = turn.emotion

                scene_history.append(turn)
                scene.turns.append(turn)

                if log_callback:
                    try:
                        clean_diag = (turn.dialogue or "").strip()
                        if clean_diag and clean_diag.lower() != "silence":
                            snippet = clean_diag if len(clean_diag) <= 75 else clean_diag[:72] + "..."
                            await log_callback(f"🗣️ [Agent: {char.core.name}] Speaks: \"{snippet}\"")
                    except Exception:
                        pass

    return scenes
