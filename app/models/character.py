from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.enums import Temperament, ArcEvolution, RelationshipType

class PersonaCore(BaseModel):
    name: str = Field(..., description="Character name")
    gender: str = Field("Unspecified", description="Gender: Male, Female, Non-binary, Unspecified")
    age: Optional[int] = Field(None, description="Character age")
    occupation: Optional[str] = Field(None, description="Occupation or social position")
    role: str = Field("Main", description="Main or Supporting")
    temperament: Optional[str] = Field(Temperament.PASSIONATE_IDEALIST.value, description="Character archetype")
    values: List[str] = Field(default_factory=list, description="Core moral values")
    quirks: List[str] = Field(default_factory=list, description="Distinctive quirks and behavioral mannerisms")
    habits: List[str] = Field(default_factory=list, description="Daily routines and habits")

class Motivation(BaseModel):
    want: str = Field("", description="External tangible goal")
    need: str = Field("", description="Internal emotional or moral need")
    flaw: str = Field("", description="Character flaw or fatal blindspot")
    secret: str = Field("", description="Hidden secret or dark past")
    current_goal: str = Field("", description="Current active objective in this section of the story")

class BehaviorLayer(BaseModel):
    voice: str = Field("", description="Speech signature, tone, and pacing")
    dialogue_style: str = Field("", description="Style of spoken interactions (terse, sarcastic, warm, etc.)")
    thought_pattern: str = Field("", description="Internal thought and monologue pattern")
    action_tendency: str = Field("", description="Physical behavior under pressure or crisis")

class CharacterArc(BaseModel):
    evolution: str = Field(ArcEvolution.FEAR_TO_COURAGE.value, description="Internal transformation arc")
    stage: str = Field("Beginning of journey", description="Current stage in character arc")
    arc_progress: int = Field(0, ge=0, le=100, description="Percentage of transformation achieved")
    milestones: List[str] = Field(default_factory=list, description="Key developmental milestones")
    reached_milestones: List[str] = Field(default_factory=list, description="Milestones already passed")

class CharacterState(BaseModel):
    emotion: str = Field("Calm", description="Current emotional state")
    knowledge: List[str] = Field(default_factory=list, description="What the character knows right now (isolated epistemic state)")
    situation: str = Field("Normal", description="Current physical and social situation")

class Relationship(BaseModel):
    from_key: str = Field(..., description="Source character name or key")
    to_key: str = Field(..., description="Target character name or key")
    type: str = Field(RelationshipType.FRIENDSHIP.value, description="Relationship category")
    description: str = Field("", description="Dynamic, backstory, and tension between them")

class Character(BaseModel):
    key: str = Field(..., description="Unique character identifier in the matrix")
    is_main: bool = Field(True, description="True if main character, False if supporting")
    core: PersonaCore
    motivation: Motivation = Field(default_factory=Motivation)
    behavior: BehaviorLayer = Field(default_factory=BehaviorLayer)
    arc: CharacterArc = Field(default_factory=CharacterArc)
    state: CharacterState = Field(default_factory=CharacterState)
    relationships: List[Relationship] = Field(default_factory=list)
    system_prompt: Optional[str] = Field(None, description="Dedicated LLM System Prompt for this character agent")
    notes: Optional[str] = Field(None, description="Author specific notes")

class CharacterSeed(BaseModel):
    name: str
    role: str = "Main"
    gender: Optional[str] = "Male"
    age: Optional[int] = 30
    occupation: Optional[str] = None
    persona: Optional[str] = None
    arc: Optional[str] = None
    notes: Optional[str] = None

class RelationshipSeed(BaseModel):
    from_name: str
    to_name: str
    type: str = RelationshipType.FRIENDSHIP.value
    description: Optional[str] = ""
