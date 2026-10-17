import os
import json
from typing import List, Optional
from datetime import datetime, timezone
from app.config import settings
from app.models.blueprint import StoryBlueprint, NovelSummary
from app.models.simulation import StoryMatrix, StoryMemory
from app.models.episode import EpisodeResponse, GenerationProgress, EpisodeSummary
from app.models.enums import NovelStatus

class StorageManager:
    def __init__(self, base_dir: str = settings.data_dir):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _novel_dir(self, novel_id: str) -> str:
        d = os.path.join(self.base_dir, novel_id)
        os.makedirs(d, exist_ok=True)
        os.makedirs(os.path.join(d, "episodes"), exist_ok=True)
        return d

    def save_blueprint(self, bp: StoryBlueprint):
        d = self._novel_dir(bp.novel_id)
        bp.updated_at_utc = datetime.now(timezone.utc).isoformat()
        with open(os.path.join(d, "blueprint.json"), "w", encoding="utf-8") as f:
            f.write(bp.model_dump_json(indent=2))

    def get_blueprint(self, novel_id: str) -> Optional[StoryBlueprint]:
        path = os.path.join(self._novel_dir(novel_id), "blueprint.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return StoryBlueprint.model_validate_json(f.read())

    def list_novels(self, user_id: Optional[str] = None) -> List[NovelSummary]:
        summaries = []
        if not os.path.exists(self.base_dir):
            return summaries
        for entry in os.scandir(self.base_dir):
            if entry.is_dir():
                bp = self.get_blueprint(entry.name)
                if bp:
                    if user_id and bp.owner_id and bp.owner_id != user_id:
                        continue
                    episodes = self.list_episodes(entry.name)
                    total_words = sum(ep.word_count for ep in episodes)
                    summaries.append(NovelSummary(
                        novel_id=bp.novel_id,
                        title=bp.title,
                        premise=bp.premise,
                        genre=bp.style.genre,
                        status=bp.status,
                        total_episodes=bp.total_episodes,
                        written_episodes=len(episodes),
                        total_words=total_words,
                        created_at_utc=bp.created_at_utc,
                        updated_at_utc=bp.updated_at_utc,
                        owner_id=bp.owner_id,
                        owner_name=bp.owner_name
                    ))
        summaries.sort(key=lambda s: s.updated_at_utc, reverse=True)
        return summaries

    def get_user_novels_count(self, user_id: str) -> int:
        count = 0
        if not os.path.exists(self.base_dir):
            return count
        for entry in os.scandir(self.base_dir):
            if entry.is_dir():
                bp = self.get_blueprint(entry.name)
                if bp and bp.owner_id == user_id:
                    count += 1
        return count

    def get_platform_stats(self) -> dict:
        total_novels = 0
        total_episodes = 0
        total_words = 0
        if os.path.exists(self.base_dir):
            for entry in os.scandir(self.base_dir):
                if entry.is_dir():
                    bp = self.get_blueprint(entry.name)
                    if bp:
                        total_novels += 1
                        eps = self.list_episodes(entry.name)
                        total_episodes += len(eps)
                        total_words += sum(e.word_count for e in eps)
        return {
            "total_novels": total_novels,
            "total_episodes": total_episodes,
            "total_words": total_words
        }

    def delete_novel(self, novel_id: str) -> bool:
        import shutil
        d = os.path.join(self.base_dir, novel_id)
        if os.path.exists(d):
            shutil.rmtree(d)
            return True
        return False

    def rename_novel(self, novel_id: str, new_title: str) -> Optional[StoryBlueprint]:
        bp = self.get_blueprint(novel_id)
        if bp:
            bp.title = new_title
            self.save_blueprint(bp)
            return bp
        return None

    def save_matrix(self, novel_id: str, matrix: StoryMatrix):
        d = self._novel_dir(novel_id)
        with open(os.path.join(d, "matrix.json"), "w", encoding="utf-8") as f:
            f.write(matrix.model_dump_json(indent=2))

    def get_matrix(self, novel_id: str) -> Optional[StoryMatrix]:
        path = os.path.join(self._novel_dir(novel_id), "matrix.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return StoryMatrix.model_validate_json(f.read())

    def save_memory(self, novel_id: str, memory: StoryMemory):
        d = self._novel_dir(novel_id)
        with open(os.path.join(d, "memory.json"), "w", encoding="utf-8") as f:
            f.write(memory.model_dump_json(indent=2))

    def get_memory(self, novel_id: str) -> Optional[StoryMemory]:
        path = os.path.join(self._novel_dir(novel_id), "memory.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return StoryMemory.model_validate_json(f.read())

    def save_episode(self, ep: EpisodeResponse):
        d = self._novel_dir(ep.novel_id)
        ep.created_at_utc = datetime.now(timezone.utc).isoformat()
        path = os.path.join(d, "episodes", f"{ep.episode_number}.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(ep.model_dump_json(indent=2))

    def get_episode(self, novel_id: str, episode_number: int) -> Optional[EpisodeResponse]:
        path = os.path.join(self._novel_dir(novel_id), "episodes", f"{episode_number}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return EpisodeResponse.model_validate_json(f.read())

    def save_episode_image(self, novel_id: str, episode_number: int, data: bytes, mime_type: str = "image/jpeg"):
        d = self._novel_dir(novel_id)
        img_dir = os.path.join(d, "episodes", "images")
        os.makedirs(img_dir, exist_ok=True)
        ext = "svg" if "svg" in mime_type else "jpg"
        file_path = os.path.join(img_dir, f"{episode_number}.{ext}")
        with open(file_path, "wb") as f:
            f.write(data)
        meta_path = os.path.join(img_dir, f"{episode_number}.meta")
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(mime_type)

    def get_episode_image(self, novel_id: str, episode_number: int) -> Optional[Tuple[bytes, str]]:
        d = self._novel_dir(novel_id)
        img_dir = os.path.join(d, "episodes", "images")
        if not os.path.exists(img_dir):
            return None
        for ext in ("jpg", "png", "svg", "jpeg"):
            path = os.path.join(img_dir, f"{episode_number}.{ext}")
            if os.path.exists(path):
                meta_path = os.path.join(img_dir, f"{episode_number}.meta")
                mime_type = "image/svg+xml" if ext == "svg" else "image/jpeg"
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r", encoding="utf-8") as mf:
                            mime_type = mf.read().strip()
                    except Exception:
                        pass
                with open(path, "rb") as f:
                    return f.read(), mime_type
        return None

    def list_episodes(self, novel_id: str) -> List[EpisodeSummary]:
        episodes_dir = os.path.join(self._novel_dir(novel_id), "episodes")
        summaries = []
        if not os.path.exists(episodes_dir):
            return summaries
        for entry in os.scandir(episodes_dir):
            if entry.name.endswith(".json"):
                with open(entry.path, "r", encoding="utf-8") as f:
                    ep = EpisodeResponse.model_validate_json(f.read())
                    summaries.append(EpisodeSummary(
                        episode_number=ep.episode_number,
                        title=ep.title,
                        summary=ep.summary,
                        word_count=ep.word_count,
                        pov_character=ep.pov_character,
                        image_url=ep.image_url
                    ))
        summaries.sort(key=lambda x: x.episode_number)
        return summaries

    def save_progress(self, progress: GenerationProgress):
        d = self._novel_dir(progress.novel_id)
        with open(os.path.join(d, "progress.json"), "w", encoding="utf-8") as f:
            f.write(progress.model_dump_json(indent=2))

    def get_progress(self, novel_id: str) -> GenerationProgress:
        path = os.path.join(self._novel_dir(novel_id), "progress.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return GenerationProgress.model_validate_json(f.read())
        return GenerationProgress(
            novel_id=novel_id,
            status=NovelStatus.READY.value,
            current_step="Ready",
            step_number=0,
            percentage=0,
            is_active=False
        )

    def save_system_settings(self, cfg: dict):
        path = os.path.join(os.path.dirname(self.base_dir), "settings.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)

    def get_system_settings(self) -> dict:
        path = os.path.join(os.path.dirname(self.base_dir), "settings.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

store = StorageManager()
