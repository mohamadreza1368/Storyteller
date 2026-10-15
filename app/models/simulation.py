from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class CharacterTurn(BaseModel):
    character_key: str = Field(..., description="Character name or key")
    action: str = Field("", description="Physical action, body language, or movement")
    dialogue: str = Field("", description="Spoken dialogue in the scene")
    thought: str = Field("", description="Secret internal thoughts and subtext known only to this character")
    emotion: str = Field("", description="Emotional state at this exact moment")
    knowledge_gain: Optional[str] = Field(None, description="New information or realization acquired in this turn")

class SceneRecord(BaseModel):
    scene_number: int
    title: str = Field("Scene", description="Scene title")
    location_key: str = Field(..., description="Location of the scene")
    time_marker: str = Field("", description="Time setting: Dusk, Midnight, Rainy Afternoon, etc.")
    pov_character_key: str = Field(..., description="POV character key")
    character_keys: List[str] = Field(default_factory=list, description="Characters present in the scene")
    goal: str = Field("", description="Dramatic scene goal")
    conflict: str = Field("", description="Primary tension or obstacle in the scene")
    resolution: str = Field("", description="Scene climax, outcome, and narrative consequence")
    turns: List[CharacterTurn] = Field(default_factory=list, description="Turn-based multi-agent character actions and thoughts")

class MatrixEvent(BaseModel):
    event_key: str
    episode_number: int
    title: str
    description: str
    character_keys: List[str] = Field(default_factory=list)
    impact: str = ""

class StoryMatrix(BaseModel):
    character_episode_grid: Dict[str, List[str]] = Field(default_factory=dict)
    events: List[MatrixEvent] = Field(default_factory=list)
    timeline: List[str] = Field(default_factory=list)

class StoryMemory(BaseModel):
    novel_id: str
    running_summary: str = Field("", description="Continuous summary of all events up to this point")
    open_threads: List[str] = Field(default_factory=list, description="Active narrative questions and unresolved mysteries")
    world_facts: List[str] = Field(default_factory=list, description="Established canonical world rules and revelations")
    character_states: Dict[str, Dict] = Field(default_factory=dict, description="Last recorded emotional and epistemic state for each character")
