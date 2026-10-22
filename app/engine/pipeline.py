import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Set
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

# Strong references to background tasks to prevent garbage collection in Python 3.12+
ACTIVE_TASKS: Set[asyncio.Task] = set()
RUNNING_NOVELS: Set[str] = set()

def track_task(task: asyncio.Task) -> asyncio.Task:
    ACTIVE_TASKS.add(task)
    task.add_done_callback(ACTIVE_TASKS.discard)
    return task

async def update_progress(
    novel_id: str,
    step_name: str,
    step_num: int,
    total_steps: int,
    percentage: int,
    ep_num: int = 1,
    total_eps: int = 1,
    is_active: bool = True,
    err: Optional[str] = None,
    log_line: Optional[str] = None,
    preview_text: Optional[str] = None
):
    prev = store.get_progress(novel_id)
    logs = list(prev.logs) if prev and prev.logs else []
    
    if log_line:
        time_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
        logs.append(f"[{time_str}] {log_line}")
        # Keep recent 30 logs
        if len(logs) > 30:
            logs = logs[-30:]

    preview = preview_text if preview_text is not None else (prev.current_preview if prev else None)

    p = GenerationProgress(
        novel_id=novel_id,
        status=NovelStatus.WRITING.value if is_active else (NovelStatus.COMPLETED.value if percentage >= 100 and ep_num >= total_eps else NovelStatus.READY.value),
        current_step=step_name,
        step_number=step_num,
        total_steps=total_steps,
        current_episode=ep_num,
        total_episodes=total_eps,
        percentage=percentage,
        is_active=is_active,
        last_error=err,
        logs=logs,
        current_preview=preview
    )
    store.save_progress(p)

async def initialize_novel(blueprint: StoryBlueprint):
    """Initializes the world, characters, and story matrix."""
    novel_id = blueprint.novel_id
    try:
        blueprint.status = NovelStatus.DESIGNING.value
        store.save_blueprint(blueprint)
        
        # Step 1: World & Characters
        await update_progress(
            novel_id, "Constructing world & cast", 1, 2, 25, 0, blueprint.total_episodes,
            log_line=f"🌍 Stage 1: Constructing world rules, locations, and psychological dossiers ({blueprint.world.city})..."
        )
        blueprint = await execute_stage1(blueprint)
        store.save_blueprint(blueprint)
        
        cast_names = ", ".join([c.core.name for c in blueprint.cast.characters[:4]])
        await update_progress(
            novel_id, "Cast dossiers forged", 1, 2, 50, 0, blueprint.total_episodes,
            log_line=f"🎭 Character dossiers completed: {cast_names}"
        )

        # Step 2: Story Matrix
        await update_progress(
            novel_id, "Weaving narrative matrix", 2, 2, 75, 0, blueprint.total_episodes,
            log_line=f"📐 Stage 2: Weaving Character x Episode Matrix for {blueprint.total_episodes} episodes..."
        )
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
        
        if blueprint.auto_continue:
            await update_progress(
                novel_id, "World ready. Starting Chapter 1...", 2, 2, 100, 0, blueprint.total_episodes,
                is_active=True,
                log_line="🚀 Matrix ready. Auto-continue enabled — initiating Chapter 1..."
            )
            task = asyncio.create_task(run_novel_episodes(novel_id))
            track_task(task)
        else:
            await update_progress(
                novel_id, "World & story matrix ready", 2, 2, 100, 0, blueprint.total_episodes,
                is_active=False,
                log_line="✨ World and story matrix initialized successfully. Ready to write Chapter 1."
            )

    except Exception as e:
        logger.error(f"Error in initialize_novel: {e}", exc_info=True)
        blueprint.status = NovelStatus.FAILED.value
        store.save_blueprint(blueprint)
        await update_progress(
            novel_id, "Failed during world design", 1, 2, 0, 0, blueprint.total_episodes,
            is_active=False, err=str(e),
            log_line=f"❌ Error during world design: {str(e)}"
        )

async def generate_single_episode(novel_id: str, ep_num: int) -> Optional[EpisodeResponse]:
    """Runs stages 3 to 6 for a single episode."""
    blueprint = store.get_blueprint(novel_id)
    if not blueprint:
        return None

    memory = store.get_memory(novel_id) or StoryMemory(novel_id=novel_id)
    matrix = store.get_matrix(novel_id)
    prior_episodes = store.list_episodes(novel_id)

    try:
        blueprint.status = NovelStatus.WRITING.value
        store.save_blueprint(blueprint)

        # Stage 3: Scene Director
        await update_progress(
            novel_id, f"Directing scenes for Chapter {ep_num}", 3, 6, 20, ep_num, blueprint.total_episodes,
            is_active=True,
            log_line=f"🎬 Stage 3 (Scene Director): Deconstructing plot and blocking dramatic beats for Chapter {ep_num}..."
        )
        scenes = await execute_stage3(blueprint, ep_num, memory, matrix=matrix, prior_episodes=prior_episodes)
        locs_summary = ", ".join([s.location_key for s in scenes[:2]])
        await update_progress(
            novel_id, f"Scenes mapped ({len(scenes)} scenes)", 3, 6, 35, ep_num, blueprint.total_episodes,
            is_active=True,
            log_line=f"📍 {len(scenes)} scenes blocked at: {locs_summary} (POV: {scenes[0].pov_character_key if scenes else 'Narrator'})"
        )

        # Stage 4: Character Simulation (Multi-agent actor turns & live dialogue)
        await update_progress(
            novel_id, f"Multi-agent roleplay in Chapter {ep_num}", 4, 6, 50, ep_num, blueprint.total_episodes,
            is_active=True,
            log_line=f"🎭 Stage 4 (Actor Simulation): Characters entered the scene; dialogue and internal thoughts simulating..."
        )

        async def log_dialogue_turn(diag_log: str):
            await update_progress(
                novel_id, f"Multi-agent roleplay in Chapter {ep_num}", 4, 6, 55, ep_num, blueprint.total_episodes,
                is_active=True,
                log_line=diag_log
            )

        scenes = await execute_stage4(blueprint, scenes, memory, log_callback=log_dialogue_turn)

        # Extract a sample secret thought for live monitor
        sample_thought = None
        for sc in scenes:
            for t in sc.turns:
                if t.thought and len(t.thought) > 10:
                    sample_thought = f"{t.character_key} [Secret Thought]: {t.thought}"
                    break
            if sample_thought:
                break

        await update_progress(
            novel_id, f"Character roleplay completed", 4, 6, 65, ep_num, blueprint.total_episodes,
            is_active=True,
            log_line=f"💭 Character turns recorded. Subtext and psychological layers registered.",
            preview_text=sample_thought
        )

        # Stage 5: Novelist / Narrator Prose Synthesis
        await update_progress(
            novel_id, f"Writing prose for Chapter {ep_num}", 5, 6, 80, ep_num, blueprint.total_episodes,
            is_active=True,
            log_line=f"✍️ Stage 5 (Master Novelist): Synthesizing expansive literary prose from staged scenes..."
        )
        title, summary, content = await execute_stage5(blueprint, ep_num, scenes, memory, prior_episodes=prior_episodes)
        word_count = len(content.split())

        preview_excerpt = content[:220].strip() + "..."
        await update_progress(
            novel_id, f"Prose synthesized ({word_count} words)", 5, 6, 90, ep_num, blueprint.total_episodes,
            is_active=True,
            log_line=f"📖 Complete text of Chapter {ep_num} synthesized ({word_count} words). Title: '{title}'",
            preview_text=preview_excerpt
        )

        # Stage 6: Story Memory Registration
        await update_progress(
            novel_id, "Registering story memory", 6, 6, 94, ep_num, blueprint.total_episodes,
            is_active=True,
            log_line=f"🧠 Stage 6 (Story Memory): Updating narrative event chain and canonical world facts..."
        )
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
            await update_progress(
                novel_id, f"Illustrating scene for Chapter {ep_num}", 6, 6, 98, ep_num, blueprint.total_episodes,
                is_active=True,
                log_line=f"🎨 AI Artwork: Synthesizing illustration for key scene in Chapter {ep_num}..."
            )
            img_data, mime_type, prompt_used = await chapter_image_client.generate(blueprint, ep_response)
            store.save_episode_image(novel_id, ep_num, img_data, mime_type)
            ep_response.image_url = f"/api/novels/{novel_id}/episodes/{ep_num}/image"
            ep_response.image_prompt = prompt_used
            await update_progress(
                novel_id, f"Illustration ready", 6, 6, 99, ep_num, blueprint.total_episodes,
                is_active=True,
                log_line=f"🖼️ Chapter {ep_num} artwork generated and saved."
            )
        except Exception as img_err:
            logger.warning(f"Failed to generate chapter artwork for Chapter {ep_num}: {img_err}")
            await update_progress(
                novel_id, f"Artwork fallback ready", 6, 6, 99, ep_num, blueprint.total_episodes,
                is_active=True,
                log_line=f"ℹ️ Artwork replaced with thematic genre cover."
            )

        store.save_episode(ep_response)

        # Check completion
        is_novel_finished = (ep_num >= blueprint.total_episodes)
        if is_novel_finished:
            blueprint.status = NovelStatus.COMPLETED.value
            store.save_blueprint(blueprint)
            await update_progress(
                novel_id, "Novel completed successfully", 6, 6, 100, ep_num, blueprint.total_episodes,
                is_active=False,
                log_line=f"🎉 All {blueprint.total_episodes} chapters completed successfully!"
            )
        else:
            blueprint.status = NovelStatus.READY.value
            store.save_blueprint(blueprint)
            
            # If auto-continue is on, keep is_active=True so frontend progress indicator stays unbroken!
            keep_active = bool(blueprint.auto_continue)
            await update_progress(
                novel_id,
                f"Chapter {ep_num} completed",
                6, 6, 100, ep_num, blueprint.total_episodes,
                is_active=keep_active,
                log_line=f"✅ Chapter {ep_num} completed successfully." + (f" Auto-continuing to Chapter {ep_num + 1}..." if keep_active else "")
            )

        return ep_response

    except Exception as e:
        logger.error(f"Error generating episode {ep_num}: {e}", exc_info=True)
        blueprint.status = NovelStatus.FAILED.value
        store.save_blueprint(blueprint)
        await update_progress(
            novel_id, f"Error generating Chapter {ep_num}", 5, 6, 0, ep_num, blueprint.total_episodes,
            is_active=False, err=str(e),
            log_line=f"❌ Error generating Chapter {ep_num}: {str(e)}"
        )
        return None

async def run_novel_episodes(novel_id: str):
    """Continuously writes episodes until novel is completed or auto-continue is stopped."""
    if novel_id in RUNNING_NOVELS:
        logger.info(f"run_novel_episodes already running for {novel_id}")
        return

    RUNNING_NOVELS.add(novel_id)
    try:
        while True:
            blueprint = store.get_blueprint(novel_id)
            if not blueprint or not blueprint.auto_continue:
                logger.info(f"Auto-continue stopped or blueprint missing for {novel_id}")
                break

            written = len(store.list_episodes(novel_id))
            next_ep = written + 1
            if next_ep > blueprint.total_episodes:
                blueprint.status = NovelStatus.COMPLETED.value
                store.save_blueprint(blueprint)
                await update_progress(
                    novel_id, "Novel completed successfully", 6, 6, 100, blueprint.total_episodes, blueprint.total_episodes,
                    is_active=False,
                    log_line=f"🎉 All {blueprint.total_episodes} chapters of the novel have been completed."
                )
                break

            # Signal transition to next episode
            await update_progress(
                novel_id, f"Starting Chapter {next_ep} of {blueprint.total_episodes}", 1, 6, 5, next_ep, blueprint.total_episodes,
                is_active=True,
                log_line=f"⏳ Initiating generation pipeline for Chapter {next_ep} of {blueprint.total_episodes}..."
            )

            # Generate episode with retry
            retries = 2
            success = False
            for attempt in range(retries):
                res = await generate_single_episode(novel_id, next_ep)
                if res is not None:
                    success = True
                    break
                logger.warning(f"Episode {next_ep} generation failed (attempt {attempt + 1}/{retries}). Retrying...")
                await asyncio.sleep(2)

            if not success:
                logger.error(f"Failed to generate episode {next_ep} after {retries} attempts.")
                break

            # Pause briefly between chapters
            await asyncio.sleep(1.5)

    finally:
        RUNNING_NOVELS.discard(novel_id)
