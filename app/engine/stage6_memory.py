from app.models.blueprint import StoryBlueprint
from app.models.simulation import StoryMemory, SceneRecord
from app.engine.llm_client import llm
from app.engine.prompts import MEMORY_SYSTEM_PROMPT

async def execute_stage6(
    blueprint: StoryBlueprint,
    episode_number: int,
    episode_summary: str,
    scenes: list[SceneRecord],
    memory: StoryMemory
) -> StoryMemory:
    """
    Stage 6: Story Memory Registration in English.
    Updates the continuous summary, active open threads, and established world facts.
    """

    user_prompt = f"""
Novel: "{blueprint.title}"
Completed Episode: {episode_number}
Current Episode Summary: {episode_summary}
Prior Running Summary: {memory.running_summary}
Prior Open Threads: {memory.open_threads}
Established World Facts: {memory.world_facts}

Tasks:
1. Synthesize an updated, cohesive Running Summary incorporating the dramatic developments of this chapter.
2. Extract remaining Open Threads — unresolved mysteries, ticking clocks, or unanswered dilemmas.
3. Record any newly confirmed World Facts established in this chapter.

Return strictly a JSON object matching this schema:
{{
  "running_summary": "Updated continuous narrative summary so far",
  "open_threads": ["Unresolved mystery 1", "Active dramatic question 2"],
  "world_facts": ["Established fact 1", "Established law 2"]
}}
"""

    async def fallback():
        new_summary = f"{memory.running_summary} In Chapter {episode_number}, a dramatic confrontation unfolded, revealing critical new leads while fracturing fragile alliances." if memory.running_summary else episode_summary
        return {
            "running_summary": new_summary,
            "open_threads": [
                "Who was inside the archives prior to the break-in?",
                "Will the tenuous alliance between the protagonists survive the coming confrontation?"
            ],
            "world_facts": [
                "Classified registry files cannot be expunged without executive authorization.",
                "The watermarked ledger holds the definitive proof of culpability."
            ]
        }

    data = await llm.generate_json(MEMORY_SYSTEM_PROMPT, user_prompt, fallback_generator=fallback)

    memory.running_summary = data.get("running_summary", memory.running_summary or episode_summary)
    memory.open_threads = data.get("open_threads", memory.open_threads)
    memory.world_facts = data.get("world_facts", memory.world_facts)

    for char in blueprint.cast.characters:
        inc = int(100 / max(1, blueprint.total_episodes))
        char.arc.arc_progress = min(100, char.arc.arc_progress + inc)

    return memory
