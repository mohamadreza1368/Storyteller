import os
import json
import shutil
import logging
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from app.config import settings
from app.models.blueprint import StoryBlueprint, NovelSummary
from app.models.simulation import StoryMatrix, StoryMemory, SceneRecord
from app.models.episode import EpisodeResponse, GenerationProgress, EpisodeSummary
from app.models.enums import NovelStatus
from app.storage.database import db

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self, base_dir: str = settings.data_dir):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self._migrate_legacy_json_novels()

    def _migrate_legacy_json_novels(self):
        """Automatically imports existing legacy JSON files into SQLite tables on startup."""
        if not os.path.exists(self.base_dir):
            return

        try:
            with db.get_connection() as conn:
                for entry in os.scandir(self.base_dir):
                    if not entry.is_dir():
                        continue
                    novel_id = entry.name
                    bp_path = os.path.join(entry.path, "blueprint.json")
                    if not os.path.exists(bp_path):
                        continue

                    # Check if novel already in database
                    cur = conn.execute("SELECT id FROM novels WHERE id = ?", (novel_id,))
                    if cur.fetchone():
                        continue

                    # 1. Migrate Blueprint
                    try:
                        with open(bp_path, "r", encoding="utf-8") as f:
                            raw_bp = f.read()
                            bp = StoryBlueprint.model_validate_json(raw_bp)

                        conn.execute("""
                            INSERT INTO novels (
                                id, title, working_title, premise, logline, synopsis, hook,
                                genre, theme, tone, prose_style, perspective, ending_style,
                                city, country, era, story_time_span, total_episodes, words_per_episode,
                                auto_continue, status, created_at_utc, updated_at_utc, owner_id, owner_name, blueprint_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(id) DO UPDATE SET
                                title = excluded.title,
                                working_title = excluded.working_title,
                                premise = excluded.premise,
                                logline = excluded.logline,
                                synopsis = excluded.synopsis,
                                hook = excluded.hook,
                                genre = excluded.genre,
                                theme = excluded.theme,
                                tone = excluded.tone,
                                prose_style = excluded.prose_style,
                                perspective = excluded.perspective,
                                ending_style = excluded.ending_style,
                                city = excluded.city,
                                country = excluded.country,
                                era = excluded.era,
                                story_time_span = excluded.story_time_span,
                                total_episodes = excluded.total_episodes,
                                words_per_episode = excluded.words_per_episode,
                                auto_continue = excluded.auto_continue,
                                status = excluded.status,
                                updated_at_utc = excluded.updated_at_utc,
                                owner_id = excluded.owner_id,
                                owner_name = excluded.owner_name,
                                blueprint_json = excluded.blueprint_json
                        """, (
                            bp.novel_id, bp.title, bp.working_title, bp.premise, bp.logline, bp.synopsis, bp.hook,
                            bp.style.genre, bp.style.theme, bp.style.tone, bp.style.prose_style, bp.style.perspective,
                            bp.plot.resolution, bp.world.city, bp.world.country, bp.world.era, bp.world.story_time_span,
                            bp.total_episodes, bp.words_per_episode, 1 if bp.auto_continue else 0, bp.status,
                            bp.created_at_utc or datetime.now(timezone.utc).isoformat(),
                            bp.updated_at_utc or datetime.now(timezone.utc).isoformat(),
                            bp.owner_id, bp.owner_name, raw_bp
                        ))
                    except Exception as e:
                        logger.warning(f"Error migrating blueprint for {novel_id}: {e}")
                        continue

                    # 2. Migrate Matrix
                    matrix_path = os.path.join(entry.path, "matrix.json")
                    if os.path.exists(matrix_path):
                        try:
                            with open(matrix_path, "r", encoding="utf-8") as f:
                                m_json = f.read()
                            conn.execute("""
                                INSERT OR REPLACE INTO story_matrix (novel_id, matrix_json, updated_at_utc)
                                VALUES (?, ?, ?)
                            """, (novel_id, m_json, datetime.now(timezone.utc).isoformat()))
                        except Exception:
                            pass

                    # 3. Migrate Memory
                    memory_path = os.path.join(entry.path, "memory.json")
                    if os.path.exists(memory_path):
                        try:
                            with open(memory_path, "r", encoding="utf-8") as f:
                                mem_json = f.read()
                            conn.execute("""
                                INSERT OR REPLACE INTO story_memory (novel_id, memory_json, updated_at_utc)
                                VALUES (?, ?, ?)
                            """, (novel_id, mem_json, datetime.now(timezone.utc).isoformat()))
                        except Exception:
                            pass

                    # 4. Migrate Episodes
                    eps_dir = os.path.join(entry.path, "episodes")
                    if os.path.exists(eps_dir):
                        for ep_file in os.scandir(eps_dir):
                            if ep_file.name.endswith(".json"):
                                try:
                                    with open(ep_file.path, "r", encoding="utf-8") as f:
                                        ep = EpisodeResponse.model_validate_json(f.read())
                                    conn.execute("""
                                        INSERT OR REPLACE INTO episodes 
                                        (novel_id, episode_number, title, summary, content, word_count, pov_character, image_url, created_at_utc)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        ep.novel_id, ep.episode_number, ep.title, ep.summary, ep.content,
                                        ep.word_count, ep.pov_character, ep.image_url,
                                        ep.created_at_utc or datetime.now(timezone.utc).isoformat()
                                    ))
                                except Exception:
                                    pass

                    # 5. Migrate Progress
                    prog_path = os.path.join(entry.path, "progress.json")
                    if os.path.exists(prog_path):
                        try:
                            with open(prog_path, "r", encoding="utf-8") as f:
                                p_raw = f.read()
                                p = GenerationProgress.model_validate_json(p_raw)
                            conn.execute("""
                                INSERT OR REPLACE INTO generation_progress
                                (novel_id, status, current_step, step_number, total_steps, percentage, current_episode, total_episodes, is_active, last_error, progress_json)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                p.novel_id, p.status, p.current_step, p.step_number, p.total_steps,
                                p.percentage, p.current_episode, p.total_episodes, 1 if p.is_active else 0,
                                p.last_error, p_raw
                            ))
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"Legacy novel migration error: {e}")

    def save_blueprint(self, bp: StoryBlueprint):
        now = datetime.now(timezone.utc).isoformat()
        bp.updated_at_utc = now
        bp_json = bp.model_dump_json(indent=2)

        with db.get_connection() as conn:
            conn.execute("""
                INSERT INTO novels (
                    id, title, working_title, premise, logline, synopsis, hook,
                    genre, theme, tone, prose_style, perspective, ending_style,
                    city, country, era, story_time_span, total_episodes, words_per_episode,
                    auto_continue, status, created_at_utc, updated_at_utc, owner_id, owner_name, blueprint_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    working_title = excluded.working_title,
                    premise = excluded.premise,
                    logline = excluded.logline,
                    synopsis = excluded.synopsis,
                    hook = excluded.hook,
                    genre = excluded.genre,
                    theme = excluded.theme,
                    tone = excluded.tone,
                    prose_style = excluded.prose_style,
                    perspective = excluded.perspective,
                    ending_style = excluded.ending_style,
                    city = excluded.city,
                    country = excluded.country,
                    era = excluded.era,
                    story_time_span = excluded.story_time_span,
                    total_episodes = excluded.total_episodes,
                    words_per_episode = excluded.words_per_episode,
                    auto_continue = excluded.auto_continue,
                    status = excluded.status,
                    updated_at_utc = excluded.updated_at_utc,
                    owner_id = excluded.owner_id,
                    owner_name = excluded.owner_name,
                    blueprint_json = excluded.blueprint_json
            """, (
                bp.novel_id, bp.title, bp.working_title, bp.premise, bp.logline, bp.synopsis, bp.hook,
                bp.style.genre, bp.style.theme, bp.style.tone, bp.style.prose_style, bp.style.perspective,
                bp.plot.resolution, bp.world.city, bp.world.country, bp.world.era, bp.world.story_time_span,
                bp.total_episodes, bp.words_per_episode, 1 if bp.auto_continue else 0, bp.status,
                bp.created_at_utc or now, now, bp.owner_id, bp.owner_name, bp_json
            ))

    def get_blueprint(self, novel_id: str) -> Optional[StoryBlueprint]:
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT blueprint_json FROM novels WHERE id = ?", (novel_id,))
            row = cursor.fetchone()
            if row:
                return StoryBlueprint.model_validate_json(row["blueprint_json"])
        return None

    def list_novels(self, user_id: Optional[str] = None) -> List[NovelSummary]:
        with db.get_connection() as conn:
            query = """
                SELECT n.id, n.title, n.premise, n.genre, n.status, n.total_episodes,
                       COUNT(e.episode_number) as written_episodes,
                       COALESCE(SUM(e.word_count), 0) as total_words,
                       n.created_at_utc, n.updated_at_utc, n.owner_id, n.owner_name
                FROM novels n
                LEFT JOIN episodes e ON n.id = e.novel_id
                WHERE (? IS NULL OR n.owner_id = ?)
                GROUP BY n.id
                ORDER BY n.updated_at_utc DESC
            """
            cursor = conn.execute(query, (user_id, user_id))
            summaries = []
            for r in cursor.fetchall():
                summaries.append(NovelSummary(
                    novel_id=r["id"],
                    title=r["title"] or "Untitled Novel",
                    premise=r["premise"] or "",
                    genre=r["genre"] or "Drama",
                    status=r["status"] or "Draft",
                    total_episodes=r["total_episodes"] or 4,
                    written_episodes=r["written_episodes"] or 0,
                    total_words=r["total_words"] or 0,
                    created_at_utc=r["created_at_utc"],
                    updated_at_utc=r["updated_at_utc"],
                    owner_id=r["owner_id"],
                    owner_name=r["owner_name"]
                ))
            return summaries

    def get_user_novels_count(self, user_id: str) -> int:
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM novels WHERE owner_id = ?", (user_id,))
            return cursor.fetchone()[0]

    def get_platform_stats(self) -> dict:
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT n.id) as total_novels,
                       COUNT(e.episode_number) as total_episodes,
                       COALESCE(SUM(e.word_count), 0) as total_words
                FROM novels n
                LEFT JOIN episodes e ON n.id = e.novel_id
            """)
            r = cursor.fetchone()
            return {
                "total_novels": r["total_novels"] if r else 0,
                "total_episodes": r["total_episodes"] if r else 0,
                "total_words": r["total_words"] if r else 0
            }

    def delete_novel(self, novel_id: str) -> bool:
        with db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM novels WHERE id = ?", (novel_id,))
            affected = cursor.rowcount > 0

        # Also cleanup any leftover legacy folder on disk
        legacy_dir = os.path.join(self.base_dir, novel_id)
        if os.path.exists(legacy_dir):
            try:
                shutil.rmtree(legacy_dir)
            except Exception:
                pass

        return affected

    def rename_novel(self, novel_id: str, new_title: str) -> Optional[StoryBlueprint]:
        bp = self.get_blueprint(novel_id)
        if bp:
            bp.title = new_title
            self.save_blueprint(bp)
            return bp
        return None

    def save_matrix(self, novel_id: str, matrix: StoryMatrix):
        m_json = matrix.model_dump_json(indent=2)
        now = datetime.now(timezone.utc).isoformat()
        with db.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO story_matrix (novel_id, matrix_json, updated_at_utc)
                VALUES (?, ?, ?)
            """, (novel_id, m_json, now))

    def get_matrix(self, novel_id: str) -> Optional[StoryMatrix]:
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT matrix_json FROM story_matrix WHERE novel_id = ?", (novel_id,))
            row = cursor.fetchone()
            if row:
                return StoryMatrix.model_validate_json(row["matrix_json"])
        return None

    def save_memory(self, novel_id: str, memory: StoryMemory):
        mem_json = memory.model_dump_json(indent=2)
        now = datetime.now(timezone.utc).isoformat()
        with db.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO story_memory (novel_id, memory_json, updated_at_utc)
                VALUES (?, ?, ?)
            """, (novel_id, mem_json, now))

    def get_memory(self, novel_id: str) -> Optional[StoryMemory]:
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT memory_json FROM story_memory WHERE novel_id = ?", (novel_id,))
            row = cursor.fetchone()
            if row:
                return StoryMemory.model_validate_json(row["memory_json"])
        return None

    def save_episode(self, ep: EpisodeResponse):
        now = datetime.now(timezone.utc).isoformat()
        ep.created_at_utc = now
        scenes_json_str = json.dumps([s.model_dump() for s in (ep.scenes or [])])
        with db.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO episodes 
                (novel_id, episode_number, title, summary, content, word_count, pov_character, image_url, created_at_utc, scenes_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ep.novel_id, ep.episode_number, ep.title, ep.summary, ep.content,
                ep.word_count, ep.pov_character, ep.image_url, now, scenes_json_str
            ))

    def get_episode(self, novel_id: str, episode_number: int) -> Optional[EpisodeResponse]:
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM episodes WHERE novel_id = ? AND episode_number = ?
            """, (novel_id, episode_number))
            row = cursor.fetchone()
            if row:
                scenes_list = []
                if "scenes_json" in row.keys() and row["scenes_json"]:
                    try:
                        raw_s = json.loads(row["scenes_json"])
                        scenes_list = [SceneRecord(**s) for s in raw_s]
                    except Exception as e:
                        logger.warning(f"Failed to parse scenes_json: {e}")

                return EpisodeResponse(
                    novel_id=row["novel_id"],
                    episode_number=row["episode_number"],
                    title=row["title"],
                    summary=row["summary"] or "",
                    content=row["content"],
                    word_count=row["word_count"],
                    pov_character=row["pov_character"] or "Narrator",
                    image_url=row["image_url"],
                    created_at_utc=row["created_at_utc"],
                    scenes=scenes_list
                )
        return None

    def save_episode_image(self, novel_id: str, episode_number: int, data: bytes, mime_type: str = "image/jpeg"):
        now = datetime.now(timezone.utc).isoformat()
        with db.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO episode_images (novel_id, episode_number, image_data, mime_type, created_at_utc)
                VALUES (?, ?, ?, ?, ?)
            """, (novel_id, episode_number, data, mime_type, now))

    def get_episode_image(self, novel_id: str, episode_number: int) -> Optional[Tuple[bytes, str]]:
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT image_data, mime_type FROM episode_images 
                WHERE novel_id = ? AND episode_number = ?
            """, (novel_id, episode_number))
            row = cursor.fetchone()
            if row:
                return bytes(row["image_data"]), row["mime_type"]

        # Fallback to legacy disk file if image was saved before migration
        img_dir = os.path.join(self.base_dir, novel_id, "episodes", "images")
        if os.path.exists(img_dir):
            for ext in ("jpg", "png", "svg", "jpeg"):
                p = os.path.join(img_dir, f"{episode_number}.{ext}")
                if os.path.exists(p):
                    meta_path = os.path.join(img_dir, f"{episode_number}.meta")
                    mime_type = "image/svg+xml" if ext == "svg" else "image/jpeg"
                    if os.path.exists(meta_path):
                        try:
                            with open(meta_path, "r", encoding="utf-8") as mf:
                                mime_type = mf.read().strip()
                        except Exception:
                            pass
                    with open(p, "rb") as f:
                        data = f.read()
                    # Cache into SQLite for future fast retrieval
                    self.save_episode_image(novel_id, episode_number, data, mime_type)
                    return data, mime_type
        return None

    def list_episodes(self, novel_id: str) -> List[EpisodeSummary]:
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT episode_number, title, summary, word_count, pov_character, image_url 
                FROM episodes 
                WHERE novel_id = ? 
                ORDER BY episode_number ASC
            """, (novel_id,))
            return [
                EpisodeSummary(
                    episode_number=r["episode_number"],
                    title=r["title"],
                    summary=r["summary"] or "",
                    word_count=r["word_count"],
                    pov_character=r["pov_character"],
                    image_url=r["image_url"]
                )
                for r in cursor.fetchall()
            ]

    def save_progress(self, progress: GenerationProgress):
        p_json = progress.model_dump_json(indent=2)
        with db.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO generation_progress
                (novel_id, status, current_step, step_number, total_steps, percentage, current_episode, total_episodes, is_active, last_error, progress_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                progress.novel_id, progress.status, progress.current_step, progress.step_number, progress.total_steps,
                progress.percentage, progress.current_episode, progress.total_episodes,
                1 if progress.is_active else 0, progress.last_error, p_json
            ))

    def get_progress(self, novel_id: str) -> GenerationProgress:
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT progress_json FROM generation_progress WHERE novel_id = ?", (novel_id,))
            row = cursor.fetchone()
            if row:
                return GenerationProgress.model_validate_json(row["progress_json"])
        return GenerationProgress(
            novel_id=novel_id,
            status=NovelStatus.READY.value,
            current_step="Ready",
            step_number=0,
            percentage=0,
            is_active=False
        )

    def save_system_settings(self, cfg: dict):
        val = json.dumps(cfg, ensure_ascii=False, indent=2)
        with db.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO system_settings (key, value_json)
                VALUES ('system_config', ?)
            """, (val,))

    def get_system_settings(self) -> dict:
        with db.get_connection() as conn:
            cursor = conn.execute("SELECT value_json FROM system_settings WHERE key = 'system_config'")
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row["value_json"])
                except Exception:
                    return {}

        # Legacy fallback if settings.json exists
        legacy_path = os.path.join(os.path.dirname(self.base_dir), "settings.json")
        if os.path.exists(legacy_path):
            try:
                with open(legacy_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.save_system_settings(cfg)
                    return cfg
            except Exception:
                return {}
        return {}

store = StorageManager()
