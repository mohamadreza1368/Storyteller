from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.simulation import SceneRecord

class EpisodeOutline(BaseModel):
    episode_number: int
    title: str = Field(..., description="Episode title")
    summary: str = Field(..., description="High-level narrative summary of this chapter")
    pov_character: str = Field(..., description="Primary POV character for this episode")
    scenes: List[SceneRecord] = Field(default_factory=list)

class EpisodeResponse(BaseModel):
    novel_id: str
    episode_number: int
    title: str
    pov_character: str
    summary: str
    content: str = Field(..., description="Full prose narrative text of the chapter")
    word_count: int
    scenes: List[SceneRecord] = Field(default_factory=list, description="Breakdown of scenes and actor turns")
    created_at_utc: str = ""

class EpisodeSummary(BaseModel):
    episode_number: int
    title: str
    summary: str
    word_count: int
    pov_character: str

class GenerationProgress(BaseModel):
    novel_id: str
    status: str
    current_step: str
    step_number: int
    total_steps: int = 6
    current_episode: int = 1
    total_episodes: int = 1
    percentage: int = 0
    last_error: Optional[str] = None
    is_active: bool = False

class SetAutoContinueRequest(BaseModel):
    auto_continue: bool
