import asyncio
import logging
from typing import Optional
from app.models.blueprint import StoryBlueprint
from app.models.episode import EpisodeResponse, GenerationProgress
from app.models.simulation import StoryMemory
from app.models.enums import NovelStatus
from app.storage.store import store
from app.engine.stage1_world_cast import execute_stage1
from app.engine.stage2_matrix import execute_stage2
from app.engine.stage3_director import execute_stage3
from app.engine.stage4_character_sim import execute_stage4
from app.engine.stage5_narrator import execute_stage5
from app.engine.stage6_memory import execute_stage6
from app.engine.image_client import chapter_image_client

logger = logging.getLogger(__name__)

async def update_progress(novel_id: str, step_name: str, step_num: int, total_steps: int, percentage: int, ep_num: int = 1, total_eps: int = 1, is_active: bool = True, err: Optional[str] = None):
    p = GenerationProgress(
        novel_id=novel_id,
        status=NovelStatus.WRITING.value if is_active else NovelStatus.READY.value,
        current_step=step_name,
        step_number=step_num,
        total_steps=total_steps,
        current_episode=ep_num,
        total_episodes=total_eps,
        percentage=percentage,
        is_active=is_active,
        last_error=err
    )
    store.save_progress(p)

async def initialize_novel(blueprint: StoryBlueprint):
    """Initializes the world, characters, and story matrix in English."""
    novel_id = blueprint.novel_id
    try:
        blueprint.status = NovelStatus.DESIGNING.value
        store.save_blueprint(blueprint)
        
        # Step 1: World & Characters
        await update_progress(novel_id, "Constructing world & cast", 1, 2, 25, 0, blueprint.total_episodes)
        blueprint = await execute_stage1(blueprint)
        store.save_blueprint(blueprint)

        # Step 2: Story Matrix
        await update_progress(novel_id, "Weaving narrative matrix", 2, 2, 75, 0, blueprint.total_episodes)
        blueprint, matrix = await execute_stage2(blueprint)
        store.save_blueprint(blueprint)
        store.save_matrix(novel_id, matrix)

        # Initialize Story Memory
        memory = StoryMemory(
            novel_id=novel_id,
            running_summary=blueprint.synopsis,
            open_threads=[f"Opening Hook: {blueprint.hook}"],
            world_facts=blueprint.world.world_rules
        )
        store.save_memory(novel_id, memory)

        blueprint.status = NovelStatus.READY.value
        store.save_blueprint(blueprint)
        await update_progress(novel_id, "World & story matrix ready", 2, 2, 100, 0, blueprint.total_episodes, is_active=False)

        if blueprint.auto_continue:
            asyncio.create_task(run_novel_episodes(novel_id))

    except Exception as e:
        logger.error(f"Error in initialize_novel: {e}", exc_info=True)
        blueprint.status = NovelStatus.FAILED.value
        store.save_blueprint(blueprint)
        await update_progress(novel_id, "Failed during world design", 1, 2, 0, 0, blueprint.total_episodes, is_active=False, err=str(e))

async def generate_single_episode(novel_id: str, ep_num: int) -> Optional[EpisodeResponse]:
    """Runs stages 3 to 6 for a single episode."""
    blueprint = store.get_blueprint(novel_id)
    if not blueprint:
        return None

    memory = store.get_memory(novel_id) or StoryMemory(novel_id=novel_id)

    try:
        blueprint.status = NovelStatus.WRITING.value
        store.save_blueprint(blueprint)

        # Stage 3: Scene Director
        await update_progress(novel_id, f"Directing scenes for Chapter {ep_num}", 3, 6, 20, ep_num, blueprint.total_episodes)
        scenes = await execute_stage3(blueprint, ep_num, memory)

        # Stage 4: Character Simulation (Multi-agent actor turns)
        await update_progress(novel_id, f"Multi-agent roleplay in Chapter {ep_num}", 4, 6, 50, ep_num, blueprint.total_episodes)
        scenes = await execute_stage4(blueprint, scenes, memory)

        # Stage 5: Novelist / Narrator Prose Synthesis
        await update_progress(novel_id, f"Writing prose for Chapter {ep_num}", 5, 6, 80, ep_num, blueprint.total_episodes)
        title, summary, content = await execute_stage5(blueprint, ep_num, scenes, memory)
        word_count = len(content.split())

        # Stage 6: Story Memory Registration
        await update_progress(novel_id, "Registering story memory", 6, 6, 95, ep_num, blueprint.total_episodes)
        memory = await execute_stage6(blueprint, ep_num, summary, scenes, memory)
        store.save_memory(novel_id, memory)
        store.save_blueprint(blueprint)

        # Save Episode
        ep_response = EpisodeResponse(
            novel_id=novel_id,
            episode_number=ep_num,
            title=title,
            pov_character=scenes[0].pov_character_key if scenes else "Narrator",
            summary=summary,
            content=content,
            word_count=word_count,
            scenes=scenes
        )

        # Illustrate Chapter Scene Artwork
        try:
            await update_progress(novel_id, f"Illustrating scene for Chapter {ep_num}", 6, 6, 98, ep_num, blueprint.total_episodes)
            img_data, mime_type, prompt_used = await chapter_image_client.generate(blueprint, ep_response)
            store.save_episode_image(novel_id, ep_num, img_data, mime_type)
            ep_response.image_url = f"/api/novels/{novel_id}/episodes/{ep_num}/image"
            ep_response.image_prompt = prompt_used
        except Exception as img_err:
            logger.warning(f"Failed to generate chapter artwork for Chapter {ep_num}: {img_err}")

        store.save_episode(ep_response)

        # Check completion
        if ep_num >= blueprint.total_episodes:
            blueprint.status = NovelStatus.COMPLETED.value
            store.save_blueprint(blueprint)
            await update_progress(novel_id, "Novel completed successfully", 6, 6, 100, ep_num, blueprint.total_episodes, is_active=False)
        else:
            blueprint.status = NovelStatus.READY.value
            store.save_blueprint(blueprint)
            await update_progress(novel_id, f"Chapter {ep_num} completed", 6, 6, 100, ep_num, blueprint.total_episodes, is_active=False)

        return ep_response

    except Exception as e:
        logger.error(f"Error generating episode {ep_num}: {e}", exc_info=True)
        blueprint.status = NovelStatus.FAILED.value
        store.save_blueprint(blueprint)
        await update_progress(novel_id, f"Error generating Chapter {ep_num}", 5, 6, 0, ep_num, blueprint.total_episodes, is_active=False, err=str(e))
        return None

async def run_novel_episodes(novel_id: str):
    """Continuously writes episodes until end or stopped."""
    blueprint = store.get_blueprint(novel_id)
    if not blueprint:
        return

    while True:
        blueprint = store.get_blueprint(novel_id)
        if not blueprint or not blueprint.auto_continue:
            break

        written = len(store.list_episodes(novel_id))
        next_ep = written + 1
        if next_ep > blueprint.total_episodes:
            blueprint.status = NovelStatus.COMPLETED.value
            store.save_blueprint(blueprint)
            break

        await generate_single_episode(novel_id, next_ep)
        await asyncio.sleep(1)
