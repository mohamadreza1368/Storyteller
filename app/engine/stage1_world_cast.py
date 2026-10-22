import uuid
from typing import List
from app.models.blueprint import StoryBlueprint, WorldSettings, CastSettings, Location
from app.models.character import (
    Character, PersonaCore, Motivation, BehaviorLayer,
    CharacterArc, CharacterState, Relationship
)
from app.engine.llm_client import llm
from app.engine.prompts import WORLD_CAST_SYSTEM_PROMPT

def build_character_system_prompt(char: Character, world: WorldSettings) -> str:
    """Builds a comprehensive, isolated LLM System Prompt for an autonomous character agent."""
    rules_text = "; ".join(world.world_rules) if world.world_rules else "Grounded physical reality."
    values_text = ", ".join(char.core.values) if char.core.values else "Truth and self-preservation"
    mannerisms = ", ".join(char.core.quirks + char.core.habits) if (char.core.quirks or char.core.habits) else "Cautious and observant"
    
    return f"""You are {char.core.name}, an autonomous agent roleplaying in a literary fiction narrative.
Setting: {world.city}, {world.country} ({world.era})
World Context & Rules: {rules_text}

CHARACTER DOSSIER & PSYCHOLOGY:
- Role & Occupation: {char.core.role} - {char.core.occupation or 'Resident'} (Age: {char.core.age or 30})
- Temperament Archetype: {char.core.temperament or 'Complex & Guarded'}
- Core Values: {values_text}
- Mannerisms & Habits: {mannerisms}

MOTIVATION ENGINE:
- External Want (Tangible Objective): {char.motivation.want}
- Internal Need (Emotional Void): {char.motivation.need}
- Fatal Flaw & Blindspot: {char.motivation.flaw}
- Buried Secret (Must Guard at all costs): {char.motivation.secret}

VOICE & BEHAVIOR:
- Speaking Style & Cadence: {char.behavior.voice or 'Distinct, measured, and authentic'}
- Behavior Under Pressure: {char.behavior.action_tendency or 'Careful, observing every movement'}

MULTI-AGENT INTERACTIVE ROLEPLAY DIRECTIVE:
You act, think, and speak STRICTLY from {char.core.name}'s isolated perspective. You have ZERO omniscient or telepathic knowledge of other characters' private thoughts or hidden secrets unless explicitly revealed in spoken dialogue or observable action.
When another character addresses you in a scene, respond directly to them in dialogue and physical reaction. Pursue your external want while guarding your secret with believable subtlety."""

async def execute_stage1(blueprint: StoryBlueprint) -> StoryBlueprint:
    """Stage 1: Expands world rules, locations, characters, motivations, and relationships in English."""
    
    user_prompt = f"""
Proposed Title: {blueprint.title}
Core Premise: {blueprint.premise}
Genre: {blueprint.style.genre}
Theme: {blueprint.style.theme}
Tone: {blueprint.style.tone}
Setting: {blueprint.world.city}, {blueprint.world.country} ({blueprint.world.era})

Initial seed characters:
{[c.core.name for c in blueprint.cast.characters]}

Initial seed locations:
{[l.name for l in blueprint.world.locations]}

Initial world rules:
{blueprint.world.world_rules}

Construct a comprehensive world dossier with:
1. Compelling title, logline, synopsis, and opening hook.
2. 2-3 immutable world rules.
3. 2-4 atmospheric locations with sensory details.
4. Deep psychological profiles for at least 2 main characters (and supporting cast if needed), including their Want, Need, Flaw, Secret, Voice, and Arc Evolution.
5. High-tension interpersonal relationships between them.

Return ONLY a valid JSON object matching this schema:
{{
  "title": "Compelling Final Title",
  "logline": "Gripping one-sentence hook featuring the protagonist, conflict, and stakes",
  "synopsis": "Full narrative synopsis in a cohesive paragraph",
  "hook": "Shocking or evocative opening sentence",
  "world_rules": ["Rule 1", "Rule 2"],
  "locations": [
    {{"name": "Location Name", "kind": "Type", "description": "Atmospheric sensory description", "atmosphere": "Mood"}}
  ],
  "characters": [
    {{
      "name": "Character Name",
      "gender": "Male/Female/Non-binary",
      "age": 34,
      "occupation": "Occupation",
      "role": "Main/Supporting",
      "temperament": "Archetype",
      "values": ["Value 1", "Value 2"],
      "quirks": ["Distinctive quirk"],
      "habits": ["Daily habit"],
      "want": "Tangible external goal",
      "need": "Internal emotional/spiritual need",
      "flaw": "Fatal flaw or blindspot",
      "secret": "Hidden secret",
      "voice": "Speech pattern and cadence",
      "evolution": "Transformation trajectory (e.g. From Distrust to Vulnerability)",
      "initial_knowledge": ["What they know at the start"]
    }}
  ],
  "relationships": [
    {{"from_name": "Name 1", "to_name": "Name 2", "type": "Friendship/Rivalry/etc.", "description": "Dynamic and tension"}}
  ]
}}
"""

    async def fallback():
        p_name = blueprint.cast.characters[0].core.name if blueprint.cast.characters else "Julian"
        s_name = blueprint.cast.characters[1].core.name if len(blueprint.cast.characters) > 1 else "Clara"
        return {
            "title": blueprint.title if blueprint.title != "Untitled Novel" else "The Winter That Never Returned",
            "logline": f"When a long-buried secret resurfaces in {blueprint.world.city}, {p_name} must choose between protecting a family legacy and uncovering a devastating truth.",
            "synopsis": f"Set against the mist and stone of {blueprint.world.city} in the {blueprint.world.era} era, {p_name} is drawn into an intricate labyrinth of deceit where loyalty becomes a liability.",
            "hook": "The mantle clock struck quarter to three; the precise second the library window shattered into rain-streaked shards.",
            "world_rules": [
                "Silence in the face of injustice is treated as complicity.",
                "No pact sealed in the district holds without a verified witness."
            ],
            "locations": [
                {"name": "The Old Blackwood Archives", "kind": "Estate", "description": "Towering oak shelves smelling of oxidized paper, wax, and damp stone.", "atmosphere": "Claustrophobic and mysterious"},
                {"name": "The Lantern Wharf", "kind": "Harbor", "description": "Creaking wooden moorings veiled in river fog, illuminated by amber gas lamps.", "atmosphere": "Tense and melancholic"}
            ],
            "characters": [
                {
                    "name": p_name,
                    "gender": "Male",
                    "age": 36,
                    "occupation": "Archival Conservator",
                    "role": "Main",
                    "temperament": "Scarred Cynic",
                    "values": ["Uncovering Truth", "Quiet Loyalty"],
                    "quirks": ["Repeatedly turns an antique brass key between his fingers"],
                    "habits": ["Drinking black coffee alone before daybreak"],
                    "want": "To recover the missing ledger that proves his predecessor was innocent",
                    "need": "To accept that the past cannot be rewritten and allow himself to trust again",
                    "flaw": "Inability to accept help, assuming everyone harbors ulterior motives",
                    "secret": "He was the one who inadvertently leaked the vault combination that night",
                    "voice": "Measured, low, laced with subtle dry irony",
                    "evolution": "From Distrust to Vulnerability",
                    "initial_knowledge": ["The ledger was removed hours before the fire broke out"]
                },
                {
                    "name": s_name,
                    "gender": "Female",
                    "age": 32,
                    "occupation": "Investigative Journalist",
                    "role": "Main",
                    "temperament": "Passionate Idealist",
                    "values": ["Justice", "Audacity"],
                    "quirks": ["Taps her leather-bound notebook against her palm when agitated"],
                    "habits": ["Pacing rapidly while formulating arguments"],
                    "want": "To expose the institutional cover-up before the archives are shuttered",
                    "need": "To realize that morality is rarely black and white",
                    "flaw": "Reckless impulsiveness and hasty condemnation of suspects",
                    "secret": "Her closest benefactor is the key stakeholder behind the redevelopment",
                    "voice": "Direct, sharp, fiercely articulate",
                    "evolution": "From Denial to Acceptance",
                    "initial_knowledge": ["Several classified casualty records were purged from the registry"]
                }
            ],
            "relationships": [
                {"from_name": p_name, "to_name": s_name, "type": "Rivalry", "description": "An uneasy alliance forged under mutual suspicion and shared peril"}
            ]
        }

    data = await llm.generate_json(WORLD_CAST_SYSTEM_PROMPT, user_prompt, fallback_generator=fallback)

    blueprint.title = data.get("title", blueprint.title)
    blueprint.logline = data.get("logline", "")
    blueprint.synopsis = data.get("synopsis", "")
    blueprint.hook = data.get("hook", "")
    
    # World rules & locations
    blueprint.world.world_rules = data.get("world_rules", blueprint.world.world_rules)
    new_locations = []
    for loc in data.get("locations", []):
        new_locations.append(Location(
            key=f"loc_{uuid.uuid4().hex[:6]}",
            name=loc.get("name", "Location"),
            kind=loc.get("kind", "Location"),
            description=loc.get("description", ""),
            atmosphere=loc.get("atmosphere", "")
        ))
    if new_locations:
        blueprint.world.locations = new_locations

    # Cast & Characters
    new_characters = []
    char_key_map = {}
    for c_data in data.get("characters", []):
        c_name = c_data.get("name", "Character")
        c_key = f"char_{uuid.uuid4().hex[:6]}"
        char_key_map[c_name] = c_key
        
        char = Character(
            key=c_key,
            is_main=(c_data.get("role") == "Main"),
            core=PersonaCore(
                name=c_name,
                gender=c_data.get("gender", "Unspecified"),
                age=c_data.get("age", 30),
                occupation=c_data.get("occupation", ""),
                role=c_data.get("role", "Main"),
                temperament=c_data.get("temperament", ""),
                values=c_data.get("values", []),
                quirks=c_data.get("quirks", []),
                habits=c_data.get("habits", [])
            ),
            motivation=Motivation(
                want=c_data.get("want", ""),
                need=c_data.get("need", ""),
                flaw=c_data.get("flaw", ""),
                secret=c_data.get("secret", ""),
                current_goal=c_data.get("want", "")
            ),
            behavior=BehaviorLayer(
                voice=c_data.get("voice", ""),
                dialogue_style=c_data.get("voice", ""),
                thought_pattern="Analytical and guarded",
                action_tendency="Deliberate and cautious"
            ),
            arc=CharacterArc(
                evolution=c_data.get("evolution", ""),
                stage="Beginning of journey",
                arc_progress=5
            ),
            state=CharacterState(
                emotion="Anxious and guarded",
                knowledge=c_data.get("initial_knowledge", []),
                situation="On the precipice of discovery"
            )
        )
        char.system_prompt = build_character_system_prompt(char, blueprint.world)
        new_characters.append(char)

    if new_characters:
        blueprint.cast.characters = new_characters

    # Relationships
    new_rels = []
    for rel_data in data.get("relationships", []):
        fn = rel_data.get("from_name", "")
        tn = rel_data.get("to_name", "")
        fk = char_key_map.get(fn, fn)
        tk = char_key_map.get(tn, tn)
        new_rels.append(Relationship(
            from_key=fk,
            to_key=tk,
            type=rel_data.get("type", "Friendship"),
            description=rel_data.get("description", "")
        ))
    blueprint.cast.relationships = new_rels

    return blueprint
