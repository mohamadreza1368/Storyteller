from enum import Enum

class Genre(str, Enum):
    DRAMA = "Drama"
    MYSTERY_CRIME = "Mystery & Crime"
    ROMANCE = "Romance"
    HISTORICAL = "Historical"
    FANTASY = "Fantasy"
    SCI_FI = "Sci-Fi"
    HORROR = "Horror"
    ADVENTURE = "Adventure"
    SOCIAL = "Social Drama"
    MAGICAL_REALISM = "Magical Realism"

class ProseStyle(str, Enum):
    LITERARY = "Literary & Elegant"
    FLUENT_SIMPLE = "Clear & Fluent"
    POETIC_IMAGERY = "Poetic & Vivid"
    MINIMALIST = "Crisp & Minimalist"
    SATIRICAL_BITING = "Witty & Satirical"
    COLD_REPORT = "Cold & Journalistic"
    STREAM_OF_CONSCIOUSNESS = "Stream of Consciousness"
    EPIC = "Epic & Grand"

class Theme(str, Enum):
    LOVE_SACRIFICE = "Love & Sacrifice"
    POWER_CORRUPTION = "Power & Corruption"
    IDENTITY_BELONGING = "Identity & Belonging"
    FORGIVENESS_REDEMPTION = "Forgiveness & Redemption"
    REVENGE_JUSTICE = "Revenge & Justice"
    FREEDOM = "Freedom & Autonomy"
    LONELINESS_CONNECTION = "Loneliness & Connection"
    TRUTH_LIES = "Truth & Deceit"
    DEATH_LEGACY = "Death & Legacy"
    WAR_HUMANITY = "War & Humanity"

class Tone(str, Enum):
    DARK = "Dark & Gritty"
    HOPEFUL = "Hopeful & Inspiring"
    BITTERSWEET = "Bittersweet"
    TENSE = "Tense & Suspenseful"
    HUMOROUS = "Humorous & Witty"
    NOSTALGIC = "Nostalgic & Melancholic"
    COLD_NEUTRAL = "Cold & Objective"

class Temperament(str, Enum):
    PASSIONATE_IDEALIST = "Passionate Idealist"
    SCARRED_PESSIMIST = "Scarred Cynic"
    DEVOTED_SUPPORTER = "Devoted Protector"
    CALCULATING_AMBITIOUS = "Calculating Strategist"
    SECRETIVE_JESTER = "Secretive Wit"
    STRICT_TRADITIONALIST = "Strict Traditionalist"
    RESTLESS_REBEL = "Restless Rebel"
    ISOLATED_SAGE = "Isolated Scholar"
    CURIOUS_INNOCENT = "Curious Innocent"
    CHARMING_DECEIVER = "Charming Trickster"

class ArcEvolution(str, Enum):
    FEAR_TO_COURAGE = "From Fear to Courage"
    SELFISH_TO_SACRIFICE = "From Selfishness to Sacrifice"
    DISTRUST_TO_TRUST = "From Distrust to Vulnerability"
    DENIAL_TO_ACCEPTANCE = "From Denial to Acceptance"
    LONELINESS_TO_CONNECTION = "From Isolation to Connection"
    IDEALISM_TO_CORRUPTION = "From Idealism to Moral Corruption"
    LOVE_TO_OBSESSION = "From Affection to Obsession"
    HOPE_TO_DISILLUSION = "From Hope to Disillusionment"
    STEADFAST = "Steadfast Conviction (Transforming Others)"

class RelationshipType(str, Enum):
    FAMILY = "Family"
    SPOUSE = "Spouses / Partners"
    UNREQUITED_LOVE = "Unrequited Love"
    FRIENDSHIP = "Friendship"
    RIVALRY = "Rivalry"
    ENMITY = "Enmity"
    MENTOR_STUDENT = "Mentor & Protégé"
    COLLEAGUE = "Colleagues"
    CONFIDANT = "Confidants"
    DEBTOR_CREDITOR = "Debtor & Creditor"

class Perspective(str, Enum):
    FIRST_PERSON = "First-Person"
    THIRD_PERSON_LIMITED = "Third-Person Limited"
    OMNISCIENT = "Omniscient"

class EndingType(str, Enum):
    SURPRISING = "Surprising Twist"
    HAPPY = "Triumphant & Uplifting"
    BITTER = "Tragic & Somber"
    OPEN = "Open-Ended & Thought-Provoking"

class PlotStructure(str, Enum):
    SINGLE_LINE = "Single Plotline"
    MULTI_LINE = "Multiple Interwoven Plotlines"

class NovelStatus(str, Enum):
    DRAFT = "Draft"
    DESIGNING = "Designing World"
    READY = "Ready"
    WRITING = "Writing Episode"
    COMPLETED = "Completed"
    STOPPED = "Paused"
    FAILED = "Failed"
