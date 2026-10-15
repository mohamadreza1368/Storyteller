import sys
import asyncio

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from app.models.blueprint import CreateNovelRequest
from app.storage.store import store
from app.api.novels import create_novel
from app.engine.pipeline import initialize_novel, generate_single_episode
from fastapi import BackgroundTasks

async def test_full_pipeline():
    print("1. Creating novel request...")
    req = CreateNovelRequest(
        title="The Whispering Archives of Blackwood",
        premise="An archivist uncovers a century-old coded ledger in a Victorian library, revealing that the town's founding families made a grim covenant.",
        genre="Gothic & Mystery",
        prose_style="Literary & Rich",
        theme="Truth & Consequences",
        tone="Tense & Suspenseful",
        era="Late Victorian",
        city="Edinburgh",
        total_episodes=2,
        words_per_episode=800,
        start_now=False
    )
    
    bg = BackgroundTasks()
    blueprint = await create_novel(req, bg)
    print(f"Created Blueprint: {blueprint.novel_id} - {blueprint.title}")

    print("\n2. Initializing novel (Stage 1: World/Cast + Stage 2: Story Matrix)...")
    await initialize_novel(blueprint)
    
    saved_bp = store.get_blueprint(blueprint.novel_id)
    print(f"World locations: {[l.name for l in saved_bp.world.locations]}")
    print(f"Cast characters: {[c.core.name for c in saved_bp.cast.characters]}")
    for c in saved_bp.cast.characters:
        print(f"  - {c.core.name}: Want='{c.motivation.want}', Secret='{c.motivation.secret}'")

    print("\n3. Generating Episode 1 (Stage 3: Director, Stage 4: Multi-Agent Actor Sim, Stage 5: Narrator, Stage 6: Memory)...")
    episode = await generate_single_episode(blueprint.novel_id, 1)
    
    print("\n" + "="*50)
    print(f"Episode 1 Title: {episode.title}")
    print(f"POV: {episode.pov_character} | Words: {episode.word_count}")
    print(f"Summary: {episode.summary}")
    print(f"Total Scenes: {len(episode.scenes)}")
    for sc in episode.scenes:
        print(f"\n  Scene {sc.scene_number}: {sc.title} ({sc.location_key})")
        print(f"  Turns recorded: {len(sc.turns)}")
        for t in sc.turns:
            print(f"    * {t.character_key}: [Action: {t.action[:35]}...] [Dialogue: \"{t.dialogue}\"]")
            print(f"      [Secret Thought: \"{t.thought}\"]")

    print("\n4. Verifying Story Memory...")
    memory = store.get_memory(blueprint.novel_id)
    print(f"Running Summary: {memory.running_summary}")
    print(f"Open Threads: {memory.open_threads}")
    print("\nSUCCESS! Complete pipeline verified.")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
