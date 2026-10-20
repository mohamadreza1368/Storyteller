from typing import List
from app.models.blueprint import StoryBlueprint
from app.models.character import Character
from app.models.simulation import SceneRecord, CharacterTurn, StoryMemory
from app.engine.llm_client import llm
from app.engine.prompts import CHARACTER_ACTOR_SYSTEM_PROMPT

async def execute_stage4(
    blueprint: StoryBlueprint,
    scenes: List[SceneRecord],
    memory: StoryMemory
) -> List[SceneRecord]:
    """
    Stage 4: Multi-Agent Character Roleplaying in English.
    Simulates turn-based interactions where each character acts independently
    based strictly on their own persona, goals, secrets, and isolated knowledge.
    """
    char_map = {c.core.name: c for c in blueprint.cast.characters}
    for c in blueprint.cast.characters:
        char_map[c.key] = c

    for scene in scenes:
        scene_history = []
        present_chars = [char_map[name] for name in scene.character_keys if name in char_map]
        if not present_chars and blueprint.cast.characters:
            present_chars = blueprint.cast.characters[:2]

        rounds = 2 if len(present_chars) > 1 else 1
        for round_idx in range(rounds):
            for char in present_chars:
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
                ]) if scene_history else "The scene has just commenced."

                user_prompt = f"""
Scene Context: "{scene.title}"
Setting: {scene.location_key} | Time: {scene.time_marker}
Dramatic Goal: {scene.goal}
Immediate Conflict: {scene.conflict}

Dialogue & Action History So Far:
{history_str}

It is your turn, {char.core.name}. Express your physical action, spoken words, and secret internal thought.
Return strictly a JSON object matching this schema:
{{
  "action": "Physical movement, posture, or facial gesture",
  "dialogue": "Exact spoken words (or 'Silence' if silent)",
  "thought": "Raw internal thoughts and calculations that remain entirely secret",
  "emotion": "Current emotional state",
  "knowledge_gain": "Any new deduction or fact learned just now (or null)"
}}
"""

                async def fallback_turn(c=char, r=round_idx, sc=scene):
                    if r == 0:
                        return {
                            "action": f"{c.core.name} paused beside the table at {sc.location_key}, assessing the rising tension caused by {sc.conflict.lower()}.",
                            "dialogue": f"We cannot afford missteps now. Look at what is happening with {sc.goal.lower()}.",
                            "thought": f"I must protect my aim ({c.motivation.want or 'the truth'}) before this situation slips entirely beyond my control.",
                            "emotion": "Tense and observant",
                            "knowledge_gain": f"Recognized the immediate danger posed by {sc.conflict}."
                        }
                    else:
                        return {
                            "action": f"{c.core.name} took a decisive step forward in {sc.location_key}, voice dropping to an urgent whisper.",
                            "dialogue": f"Whatever happens next, we have crossed the threshold. We see this through to {sc.resolution.lower()}.",
                            "thought": f"Even if my secret ({c.motivation.secret or 'motives'}) is tested, retreat is no longer an option.",
                            "emotion": "Resolute and determined",
                            "knowledge_gain": f"Committed to seeing through {sc.resolution}."
                        }

                turn_data = await llm.generate_json(
                    sys_prompt,
                    user_prompt,
                    fallback_generator=lambda c=char, r=round_idx, sc=scene: fallback_turn(c, r, sc)
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

    return scenes
