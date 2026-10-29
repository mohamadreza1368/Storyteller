import uuid
from typing import List
from app.models.blueprint import StoryBlueprint, WorldSettings, CastSettings, Location
from app.models.character import (
    Character, PersonaCore, Motivation, BehaviorLayer,
    CharacterArc, CharacterState, Relationship
)
from app.engine.llm_client import llm
from app.engine.prompts import WORLD_CAST_SYSTEM_PROMPT
from app.engine.writing_craft import (
    CHARACTER_HUMAN_DIALOGUE_DIRECTIVES,
    AVOID_AI_VOCABULARY_DIRECTIVES
)
from app.engine.qloo_client import qloo_client

def build_character_system_prompt(char: Character, world: WorldSettings) -> str:
    """Builds a comprehensive, isolated LLM System Prompt for an autonomous character agent."""
    rules_text = "; ".join(world.world_rules) if world.world_rules else "Grounded physical reality."
    values_text = ", ".join(char.core.values) if char.core.values else "Truth and self-preservation"
    mannerisms = ", ".join(char.core.quirks + char.core.habits) if (char.core.quirks or char.core.habits) else "Cautious and observant"

    # Qloo Cultural Taste & Lifestyle Enrichment
    cultural_taste = qloo_client.enrich_character_cultural_dossier(
        char.core.role or "Main",
        char.core.temperament or "Complex",
        world.era
    )
    reading_pref = ", ".join(cultural_taste.get("reading_tastes", []))
    music_pref = cultural_taste.get("musical_temperament", "Quiet ambient contemplation")
    hallmarks = cultural_taste.get("aesthetic_hallmarks", "Distinctive period garments")
    
    return f"""You are {char.core.name}, an autonomous agent roleplaying in a literary fiction narrative.
Setting: {world.city}, {world.country} ({world.era})
World Context & Rules: {rules_text}

CHARACTER DOSSIER & PSYCHOLOGY:
- Role & Occupation: {char.core.role} - {char.core.occupation or 'Resident'} (Age: {char.core.age or 30})
- Temperament Archetype: {char.core.temperament or 'Complex & Guarded'}
- Core Values: {values_text}
- Mannerisms & Habits: {mannerisms}

CULTURAL TASTE & AESTHETIC PALETTE (Qloo Cultural Intelligence):
- Intellectual & Reading Tastes: {reading_pref}
- Musical & Atmospheric Cadence: {music_pref}
- Personal Aesthetic & Artifacts: {hallmarks}

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
When another character addresses you in a scene, respond directly to them in dialogue and physical reaction. Pursue your external want while guarding your secret with believable subtlety.

{CHARACTER_HUMAN_DIALOGUE_DIRECTIVES}
{AVOID_AI_VOCABULARY_DIRECTIVES}"""

async def execute_stage1(blueprint: StoryBlueprint) -> StoryBlueprint:
    """
    Stage 1: Constructs and enriches world rules, locations, character dossiers,
    and dedicated LLM System Prompts. Strictly preserves user-specified characters
    (including supporting characters), custom locations, and historical era/year.
    """
    # Format user-provided characters with complete fidelity
    chars_seed_desc = []
    for c in blueprint.cast.characters:
        r_type = "Main protagonist" if c.is_main else "Supporting character"
        chars_seed_desc.append(
            f"- Name: {c.core.name} | Role: {c.core.role} ({r_type}) | "
            f"Gender: {c.core.gender} | Occupation: {c.core.occupation or 'Unspecified'} | Archetype: {c.core.temperament or 'Complex'}"
        )
    chars_text = "\n".join(chars_seed_desc) if chars_seed_desc else "None provided (synthesize 2 to 3 compelling characters)."

    # Format user-provided locations with complete fidelity
    locs_seed_desc = []
    for l in blueprint.world.locations:
        locs_seed_desc.append(
            f"- Name: {l.name} | Type: {l.kind} | Description: {l.description or 'Atmospheric setting'}"
        )
    locs_text = "\n".join(locs_seed_desc) if locs_seed_desc else "None provided (synthesize 2 to 4 atmospheric locations)."

    user_prompt = f"""
Novel Title: {blueprint.title}
Core Premise: {blueprint.premise or 'An unfolding dramatic narrative in ' + blueprint.world.city}
Genre: {blueprint.style.genre}
Theme: {blueprint.style.theme}
Tone: {blueprint.style.tone}
World Setting: {blueprint.world.city}, {blueprint.world.country} (Year / Era: {blueprint.world.era})

SPECIFIED CHARACTERS:
{chars_text}

SPECIFIED LOCATIONS:
{locs_text}

MANDATORY SPECIFICATION DIRECTIVES:
1. YOU MUST PRESERVE AND ELABORATE UPON EVERY SINGLE CHARACTER LISTED ABOVE (both Main and Supporting!). Do NOT omit any character, do NOT rename them, and preserve their exact role (Main or Supporting).
2. YOU MUST PRESERVE AND ELABORATE UPON EVERY LOCATION LISTED ABOVE.
3. The narrative, logline, synopsis, and opening hook MUST be deeply rooted in {blueprint.world.city} during the {blueprint.world.era} era.
4. Qloo Cultural Intelligence: enrich characters with distinctive intellectual and artistic tastes, and imbue locations with visceral sensory textures (scents, architectural acoustics, lighting).

Return ONLY a valid JSON object matching this schema:
{{
  "title": "{blueprint.title if (blueprint.title and blueprint.title != 'New Novel') else 'Compelling Final Title'}",
  "logline": "Gripping one-sentence logline featuring the protagonist, central conflict, and stakes in {blueprint.world.city}",
  "synopsis": "Full narrative synopsis set in {blueprint.world.city} ({blueprint.world.era})",
  "hook": "Evocative opening sentence establishing the world and stakes",
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
        # Truly dynamic fallback that respects ALL user inputs
        fallback_chars = []
        if blueprint.cast.characters:
            for c in blueprint.cast.characters:
                c_role = c.core.role or ("Main" if c.is_main else "Supporting")
                fallback_chars.append({
                    "name": c.core.name,
                    "gender": c.core.gender or "Unspecified",
                    "age": c.core.age or 32,
                    "occupation": c.core.occupation or ("Key Figure" if c.is_main else "Local Contact"),
                    "role": c_role,
                    "temperament": c.core.temperament or "Observant Realist",
                    "values": ["Truth", "Self-Determination"],
                    "quirks": ["Observes peripheral movement before speaking"],
                    "habits": ["Paces when deliberating high-stakes decisions"],
                    "want": f"Pursue their personal objective regarding {blueprint.premise or 'the central dilemma'}",
                    "need": "To confront the unvarnished reality of their circumstances",
                    "flaw": "Guarded skepticism toward unfamiliar alliances",
                    "secret": f"Holds undisclosed knowledge directly connected to the crisis in {blueprint.world.city}",
                    "voice": "Measured, calm, and acutely perceptive",
                    "evolution": "From Caution to Decisive Conviction",
                    "initial_knowledge": [f"Aware of the undercurrents shifting across {blueprint.world.city}"]
                })
        else:
            fallback_chars = [
                {
                    "name": "Protagonist",
                    "gender": "Male",
                    "age": 34,
                    "occupation": "Investigator",
                    "role": "Main",
                    "temperament": "Methodical Seeker",
                    "values": ["Justice", "Truth"],
                    "quirks": ["Keeps detailed chronological records"],
                    "habits": ["Listens intently before offering an assessment"],
                    "want": f"Uncover the truth behind events in {blueprint.world.city}",
                    "need": "To accept that answers often demand personal sacrifice",
                    "flaw": "Reluctance to ask for assistance",
                    "secret": "Personally involved in past events tied to this conflict",
                    "voice": "Thoughtful, resonant, and controlled",
                    "evolution": "From Solitude to Purpose",
                    "initial_knowledge": [f"Familiar with the layout of {blueprint.world.city}"]
                },
                {
                    "name": "Companion",
                    "gender": "Female",
                    "age": 30,
                    "occupation": "Key Ally",
                    "role": "Main",
                    "temperament": "Pragmatic Strategist",
                    "values": ["Loyalty", "Pragmatism"],
                    "quirks": ["Regularly verifies safety and exits"],
                    "habits": ["Quick to identify anomalies in behavior"],
                    "want": "Safeguard those vulnerable to the looming fallout",
                    "need": "To build authentic trust without reservations",
                    "flaw": "Prone to expect betrayal",
                    "secret": "Possesses evidence capable of exposing the instigators",
                    "voice": "Sharp, articulate, and direct",
                    "evolution": "From Self-Defense to Trust",
                    "initial_knowledge": ["Knows the immediate vulnerabilities of the opposing faction"]
                }
            ]

        fallback_locs = []
        if blueprint.world.locations:
            for l in blueprint.world.locations:
                fallback_locs.append({
                    "name": l.name,
                    "kind": l.kind or "District",
                    "description": l.description or f"An atmospheric location in {blueprint.world.city} bearing the distinct character of the {blueprint.world.era} era.",
                    "atmosphere": "Tense and evocative"
                })
        else:
            fallback_locs = [
                {"name": f"The Historic Quarter of {blueprint.world.city}", "kind": "District", "description": f"The atmospheric heart of {blueprint.world.city} in the {blueprint.world.era} era.", "atmosphere": "Vibrant yet watchful"},
                {"name": f"The Vaulted Sanctuary", "kind": "Interior", "description": f"A secure enclave within {blueprint.world.city} where clandestine conferences take place.", "atmosphere": "Shadowed and quiet"}
            ]

        lead_name = fallback_chars[0]["name"]
        final_title = blueprint.title if (blueprint.title and blueprint.title != "New Novel") else f"Echoes of {blueprint.world.city}"
        
        return {
            "title": final_title,
            "logline": f"Against the shifting currents of {blueprint.world.city} ({blueprint.world.era}), {lead_name} must navigate escalating friction to confront {blueprint.premise or 'an irreversible reckoning'}.",
            "synopsis": f"Set in {blueprint.world.city} during the {blueprint.world.era} era, the story follows {lead_name} as a deepening dilemma disrupts the delicate balance of the environment. Every action reverberates through loyalties and long-held secrets.",
            "hook": f"The morning stillness across {blueprint.world.city} was broken not by an alarm, but by an unexpected revelation that made retreat impossible.",
            "world_rules": blueprint.world.world_rules or [
                "Actions taken in contested spaces inevitably attract watchful opposition.",
                "Historical debts and buried pacts always demand their due."
            ],
            "locations": fallback_locs,
            "characters": fallback_chars,
            "relationships": [
                {
                    "from_name": fallback_chars[0]["name"],
                    "to_name": fallback_chars[1]["name"] if len(fallback_chars) > 1 else fallback_chars[0]["name"],
                    "type": "Uneasy Alliance",
                    "description": "Bound by shared stakes, yet separated by private calculations."
                }
            ]
        }

    data = await llm.generate_json(WORLD_CAST_SYSTEM_PROMPT, user_prompt, fallback_generator=fallback)

    if data.get("title") and (not blueprint.title or blueprint.title == "New Novel"):
        blueprint.title = data["title"]
    blueprint.logline = data.get("logline", blueprint.logline)
    blueprint.synopsis = data.get("synopsis", blueprint.synopsis)
    blueprint.hook = data.get("hook", blueprint.hook)
    
    if data.get("world_rules"):
        blueprint.world.world_rules = data["world_rules"]

    # 1. Process and Merge Locations (Preserve all user-specified locations)
    returned_locs = {l.get("name", "").strip().lower(): l for l in data.get("locations", [])}
    merged_locations: List[Location] = []

    # First, retain and enrich all user-provided locations
    existing_user_loc_names = set()
    for u_loc in blueprint.world.locations:
        norm_name = u_loc.name.strip().lower()
        existing_user_loc_names.add(norm_name)
        matched_loc_data = returned_locs.get(norm_name)
        if matched_loc_data:
            u_loc.description = matched_loc_data.get("description") or u_loc.description
            u_loc.atmosphere = matched_loc_data.get("atmosphere") or u_loc.atmosphere
            u_loc.kind = matched_loc_data.get("kind") or u_loc.kind
        merged_locations.append(u_loc)

    # Second, add any complementary locations generated by LLM
    for l_data in data.get("locations", []):
        l_name = l_data.get("name", "").strip()
        if l_name and l_name.lower() not in existing_user_loc_names:
            merged_locations.append(Location(
                key=f"loc_{uuid.uuid4().hex[:6]}",
                name=l_name,
                kind=l_data.get("kind", "Location"),
                description=l_data.get("description", ""),
                atmosphere=l_data.get("atmosphere", "")
            ))

    if merged_locations:
        blueprint.world.locations = merged_locations

    # 2. Process and Merge Cast (Preserve all user-specified characters including Supporting)
    returned_chars = {c.get("name", "").strip().lower(): c for c in data.get("characters", [])}
    merged_characters: List[Character] = []
    char_key_map = {}

    # First, retain and enrich every user-provided character
    existing_user_char_names = set()
    for u_char in blueprint.cast.characters:
        norm_name = u_char.core.name.strip().lower()
        existing_user_char_names.add(norm_name)
        char_key_map[u_char.core.name] = u_char.key
        
        c_match = returned_chars.get(norm_name)
        if c_match:
            u_char.motivation = Motivation(
                want=c_match.get("want", u_char.motivation.want or f"Pursue objective in {blueprint.world.city}"),
                need=c_match.get("need", u_char.motivation.need or "To reconcile with the truth"),
                flaw=c_match.get("flaw", u_char.motivation.flaw or "Guarded vigilance"),
                secret=c_match.get("secret", u_char.motivation.secret or "Guards undisclosed information"),
                current_goal=c_match.get("want", "")
            )
            u_char.behavior = BehaviorLayer(
                voice=c_match.get("voice", u_char.behavior.voice or "Measured and perceptive"),
                dialogue_style=c_match.get("voice", ""),
                thought_pattern="Tactical and focused",
                action_tendency="Calculated reactions"
            )
            u_char.arc = CharacterArc(
                evolution=c_match.get("evolution", "From Caution to Conviction"),
                stage="Beginning of journey",
                arc_progress=5
            )
            u_char.state = CharacterState(
                emotion="Alert and guarded",
                knowledge=c_match.get("initial_knowledge", [f"Aware of the situation in {blueprint.world.city}"]),
                situation="Poised at the opening threshold"
            )
            if c_match.get("temperament") and not u_char.core.temperament:
                u_char.core.temperament = c_match.get("temperament")
            if c_match.get("values"):
                u_char.core.values = c_match.get("values")
            if c_match.get("quirks"):
                u_char.core.quirks = c_match.get("quirks")
            if c_match.get("habits"):
                u_char.core.habits = c_match.get("habits")
        else:
            # User character not directly in LLM response: populate resilient defaults without dropping them!
            u_char.motivation = Motivation(
                want=f"Fulfill their role as {u_char.core.occupation or 'active participant'} in {blueprint.world.city}",
                need="To stand their ground amidst the shifting crisis",
                flaw="Guarded reticence",
                secret=f"Keeps a private stake in the outcome of {blueprint.world.city}",
                current_goal="Assess the immediate landscape"
            )
            u_char.behavior = BehaviorLayer(voice="Direct and measured")
            u_char.state = CharacterState(
                emotion="Composed",
                knowledge=[f"Present in {blueprint.world.city}"]
            )

        u_char.system_prompt = build_character_system_prompt(u_char, blueprint.world)
        merged_characters.append(u_char)

    # Second, if user did not provide characters, add characters synthesized by LLM
    if not blueprint.cast.characters:
        for c_data in data.get("characters", []):
            c_name = c_data.get("name", "Character")
            c_key = f"char_{uuid.uuid4().hex[:6]}"
            char_key_map[c_name] = c_key
            
            c_role = c_data.get("role", "Main")
            char = Character(
                key=c_key,
                is_main=(c_role.lower() == "main"),
                core=PersonaCore(
                    name=c_name,
                    gender=c_data.get("gender", "Unspecified"),
                    age=c_data.get("age", 30),
                    occupation=c_data.get("occupation", ""),
                    role=c_role,
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
            merged_characters.append(char)

    if merged_characters:
        blueprint.cast.characters = merged_characters

    # 3. Relationships
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
