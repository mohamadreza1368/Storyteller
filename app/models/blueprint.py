from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.enums import (
    Genre, ProseStyle, Theme, Tone, Perspective, EndingType,
    PlotStructure, NovelStatus
)
from app.models.character import Character, CharacterSeed, Relationship, RelationshipSeed

class Location(BaseModel):
    key: str
    name: str
    kind: str = Field("Location", description="Type: Estate, Manor, Street, Cafe, Harbor, Forest, etc.")
    description: str = Field("", description="Visual details, sensory cues, and atmospheric setting")
    atmosphere: str = Field("", description="Prevailing psychological mood of this environment")
    notes: Optional[str] = None

class LocationSeed(BaseModel):
    name: str
    kind: Optional[str] = "Location"
    description: Optional[str] = ""

class WorldSettings(BaseModel):
    era: str = Field("Contemporary", description="Time period: Victorian, 1970s, Contemporary, Near-Future, etc.")
    country: str = Field("United Kingdom", description="Country")
    city: str = Field("London", description="City / Region")
    atmosphere: str = Field("Realistic", description="Prevailing world atmosphere")
    reality_mode: str = Field("Realistic", description="Realism level, Sci-Fi, or Supernatural/Fantasy")
    story_time_span: str = Field("One Season", description="Duration of the narrative: One night, One week, A few years, etc.")
    world_rules: List[str] = Field(default_factory=list, description="Immutable rules and physical/social laws of this world")
    world_facts: List[str] = Field(default_factory=list, description="Established canonical facts about this world")
    locations: List[Location] = Field(default_factory=list)

class CastSettings(BaseModel):
    main_count: int = Field(2, ge=1, le=10)
    supporting_count: int = Field(3, ge=0, le=15)
    characters: List[Character] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)

class ArcBeat(BaseModel):
    beat: str = Field(..., description="Description of the narrative beat or turning point")
    consequence: str = Field("", description="Impact on characters and story trajectory")
    milestone: str = Field("", description="Hero's journey stage or character development milestone")

class PlotLine(BaseModel):
    key: str = Field(..., description="Plotline identifier")
    title: str = Field(..., description="Plotline title")
    is_main: bool = Field(True, description="True if primary plot, False if subplot")
    character_keys: List[str] = Field(default_factory=list, description="Characters involved in this thread")
    synopsis: str = Field("", description="Summary of this plotline arc")
    beats: List[ArcBeat] = Field(default_factory=list)

class PlotSettings(BaseModel):
    structure: str = Field(PlotStructure.MULTI_LINE.value, description="Single plotline or multi-line")
    plot_line_count: int = Field(2, ge=1, le=6)
    plot_lines: List[PlotLine] = Field(default_factory=list)
    resolution: str = Field(EndingType.SURPRISING.value, description="Ending style")

class StyleSettings(BaseModel):
    prose_style: str = Field(ProseStyle.LITERARY.value, description="Prose style and diction")
    tone: str = Field(Tone.BITTERSWEET.value, description="Overall narrative tone")
    perspective: str = Field(Perspective.THIRD_PERSON_LIMITED.value, description="Narrative point of view")
    theme: str = Field(Theme.IDENTITY_BELONGING.value, description="Core thematic question")
    genre: str = Field(Genre.DRAMA.value, description="Novel genre")
    cultural_influences: List[str] = Field(default_factory=list, description="Qloo cultural touchstones, reference works, films, and books")
    thematic_dna: List[str] = Field(default_factory=list, description="Aesthetic and thematic motifs discovered via taste intelligence")

class StoryBlueprint(BaseModel):
    novel_id: str
    title: str = Field("Untitled Novel", description="Novel title")
    working_title: Optional[str] = None
    premise: str = Field("", description="One or two sentence core premise")
    logline: str = Field("", description="High-concept narrative hook and stakes")
    synopsis: str = Field("", description="Full narrative synopsis")
    hook: str = Field("", description="Dramatic opening hook or question")
    
    total_episodes: int = Field(5, ge=1, le=50, description="Total planned episodes / chapters")
    words_per_episode: int = Field(1800, ge=500, le=3000, description="Target word count per episode (max 3000 words)")
    auto_continue: bool = Field(False, description="Whether to generate subsequent episodes automatically")
    
    world: WorldSettings = Field(default_factory=WorldSettings)
    cast: CastSettings = Field(default_factory=CastSettings)
    plot: PlotSettings = Field(default_factory=PlotSettings)
    style: StyleSettings = Field(default_factory=StyleSettings)
    
    status: str = Field(NovelStatus.DRAFT.value)
    created_at_utc: str = Field("")
    updated_at_utc: str = Field("")
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None

class CreateNovelRequest(BaseModel):
    title: Optional[str] = None
    premise: Optional[str] = None
    genre: Optional[str] = Genre.DRAMA.value
    prose_style: Optional[str] = ProseStyle.LITERARY.value
    theme: Optional[str] = Theme.IDENTITY_BELONGING.value
    tone: Optional[str] = Tone.BITTERSWEET.value
    era: Optional[str] = "Contemporary"
    country: Optional[str] = "United Kingdom"
    city: Optional[str] = "London"
    story_time_span: Optional[str] = "One Season"
    world_rules: Optional[List[str]] = None
    locations: Optional[List[LocationSeed]] = None
    characters: Optional[List[CharacterSeed]] = None
    relationships: Optional[List[RelationshipSeed]] = None
    total_episodes: Optional[int] = 4
    words_per_episode: Optional[int] = Field(1800, ge=500, le=3000)
    perspective: Optional[str] = Perspective.THIRD_PERSON_LIMITED.value
    ending: Optional[str] = EndingType.SURPRISING.value
    auto_continue: Optional[bool] = False
    cultural_influences: Optional[List[str]] = None
    thematic_dna: Optional[List[str]] = None
    start_now: Optional[bool] = True
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None

class NovelSummary(BaseModel):
    novel_id: str
    title: str
    premise: str
    genre: str
    status: str
    total_episodes: int
    written_episodes: int
    total_words: int
    created_at_utc: str
    updated_at_utc: str
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None

