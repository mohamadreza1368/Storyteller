"""
Writing Craft & Humanizer Enforcement Engine.
Synthesizes instructions and automated quality gates from:
1. Master Author Craft, Narrative Pacing, and Sensory Interiority Standards
2. Elimination of AI Staging, Forced Triads, and Fake-Deep Aphorisms
3. Banned AI Clichés, Sentence Rhythm Diversity, and Authentic Character Voice
"""

import re
from typing import Tuple, List, Dict

BANNED_AI_WORDS_AND_PHRASES: List[str] = [
    "delve", "delving", "delved",
    "tapestry", "rich tapestry",
    "testament", "a testament to",
    "beacon", "beacon of hope",
    "palpable", "palpable tension",
    "labyrinthine",
    "unwavering",
    "intertwined",
    "resonate", "resonating",
    "dance of shadows", "dance of light and shadow", "dance of light",
    "whispers of",
    "chill ran down", "a chill ran down",
    "air was thick with", "the air was thick with",
    "time seemed to stand still", "time stood still",
    "little did he know", "little did she know", "little did they know",
    "etched into", "etched upon",
    "sent shivers", "shivers down",
    "hushed tones", "hushed whispers",
    "bustling",
    "nestled",
    "pivotal",
    "inexorably", "inexorable",
    "crescendo",
    "kaleidoscope",
    "cacophony",
    "juxtaposition",
    "unbeknownst",
    "heart hammered against",
    "sent shockwaves",
    "symphony of",
    "at its core",
    "in reality",
    "the real question is",
    "what really matters",
    "let that sink in",
    "read that again",
    "that is the real win",
    "the message was clear",
    "and so it began",
    "nothing would ever be the same",
    "silent sentinel",
    "unspoken truth",
    "unspoken peril",
    "zenith of tension"
]

CRAFT_SUBSTITUTIONS: Dict[str, str] = {
    "palpable tension": "tense silence",
    "palpable": "heavy",
    "delve into": "examine",
    "delving into": "examining",
    "delved into": "examined",
    "delve": "investigate",
    "delving": "investigating",
    "delved": "investigated",
    "rich tapestry": "complex reality",
    "tapestry": "structure",
    "a testament to": "proof of",
    "testament": "evidence",
    "beacon of hope": "sole lifeline",
    "beacon": "guide",
    "labyrinthine": "winding",
    "unwavering": "steady",
    "intertwined": "connected",
    "resonate": "carry weight",
    "resonating": "carrying weight",
    "dance of shadows": "flickering shadows",
    "dance of light and shadow": "flickering light",
    "dance of light": "flickering light",
    "a chill ran down his spine": "cold sweat prickled along his neck",
    "a chill ran down her spine": "cold sweat prickled along her neck",
    "a chill ran down": "cold sweat prickled",
    "chill ran down": "cold sweat prickled",
    "air was thick with": "air smelled of",
    "the air was thick with": "the room smelled of",
    "time seemed to stand still": "nobody moved",
    "time stood still": "movement ceased",
    "bustling": "crowded",
    "nestled": "situated",
    "pivotal": "critical",
    "inexorably": "steadily",
    "inexorable": "steady",
    "crescendo": "peak",
    "cacophony": "harsh noise",
    "unbeknownst": "without their knowledge",
    "at its core": "in fact",
    "heart hammered against": "heart raced against",
    "sent shivers": "sent a tremor",
    "shivers down": "tremors down",
    "hushed tones": "low voices",
    "hushed whispers": "whispers",
    "nothing would ever be the same": "the situation had irrevocably changed"
}

MASTER_AUTHOR_CRAFT_INSTRUCTIONS = """
MASTER FICTION AUTHOR CRAFT & STYLE DIRECTIVES (Mandatory):
1. Show, Don't Explain:
   - Never editorialize or announce what a character is feeling (e.g., avoid "he felt a surge of dread" or "a sense of wonder washed over her").
   - Instead, show physical, visceral instinct: a tightened grip, a missed breath, tactile temperatures, sound reverberations, or the weight of silence.
2. Narrative Voice & Pacing:
   - Strictly Third-Person Limited: Stay anchored inside the POV character's direct sensory perception and perspective. Never head-hop between minds in the same scene.
   - Weave internal calculations and unspoken thoughts seamlessly into narrative prose without italics or quotation tags.
   - Dynamic Sentence Rhythm: Alternate deliberately between short, punchy sentences for immediate action or tension, and measured, sensory-rich sentences for reflection.
3. Punctuation & Mechanics:
   - Strict Punctuation Hygiene: Never output stacked or consecutive punctuation marks (e.g. absolutely never write '.;', ';.', ';;', ',;', or '..'). Every sentence must terminate with exactly one period, question mark, or exclamation point.
   - Semicolons: Semicolons must be used with extreme restraint (maximum 0 to 1 per chapter). Never chain clauses with semicolons as a substitute for periods. Split independent thoughts into distinct, confident sentences.
   - Never place semicolons immediately before or after commas, periods, or dashes.
   - Em Dashes (—): Use sparingly (maximum 1 or 2 in an entire scene) strictly for abrupt dialogue interruption or sharp dramatic pivots. Never pepper every sentence with em dashes.
   - Formatting: Never use bold markdown labels or bullet points within narrative prose.
"""

HUMANIZER_STYLE_DIRECTIVES = """
HUMANIZER ANTI-AI WRITING DIRECTIVES (Zero Tolerance for Chatbot Tells):
1. Eliminate "Not X, but Y" Contrasts:
   - Forbid artificial negative/positive balancing acts (e.g., "It wasn't just a building; it was a fortress", "Not about revenge, but about survival"). State the concrete truth directly.
2. Forbid One-Line Dramatic Closers & Trailing Truisms:
   - Do NOT end scenes or paragraphs with isolated, dramatic one-sentence summaries (e.g., "That was the real danger.", "The game had begun.", "And nothing would ever be the same."). Let the scene's concrete action speak for itself.
3. Forbid Pseudo-Profound Aphorisms:
   - Never include generic philosophical sayings disguised as wisdom (e.g., "At its core...", "Trust is the currency of...", "Silence is the truest weapon").
4. Forbid Staged Run-Ups & Narrator Throat-Clearing:
   - No introductory signaling or rhetorical hand-wringing. Start immediately in the concrete scene.
5. Forbid Forced Triads:
   - Never mechanically group three adjectives, three nouns, or three parallel clauses together for cheap rhythm (e.g., avoid "grief, guilt, and vengeance").
6. Forbid Phantom Objections:
   - Never argue with hypothetical readers ("This was not to say...", "Don't get him wrong...").
"""

AVOID_AI_VOCABULARY_DIRECTIVES = """
STRICTLY FORBIDDEN AI CLICHÉS & PATTERNS:
Under no circumstances use the following dead AI words or clichés in narration or dialogue:
- delve, tapestry, testament, beacon, palpable, labyrinthine, unwavering, intertwined, resonate
- dance of shadows / dance of light, whispers of, chill ran down, air was thick with
- time stood still / time seemed to stand still, little did they know, etched into, sent shivers
- hushed tones, bustling, nestled, pivotal, inexorably, crescendo, kaleidoscope, cacophony
Use concrete, grounded, sensory English (e.g., wood, iron, smoke, cold rain, gravel, leather, salt).
"""

CHARACTER_HUMAN_DIALOGUE_DIRECTIVES = """
AUTHENTIC HUMAN DIALOGUE RULES:
1. Speak Like a Real Human:
   - Real people speak in fragments, interrupt, hesitate, and use brevity. Avoid formal speeches, diplomatic summaries, or philosophical lectures.
   - Never use "Not X, but Y" constructions or forced triads in dialogue.
   - Dialogue must carry subtext: what the character leaves unsaid is more dangerous than what they say.
2. Grounded Physicality:
   - When speaking, anchor actions in the immediate physical environment (handling an object, looking away, pausing by the door) rather than melodramatic gestures.
"""

def sanitize_punctuation(text: str) -> Tuple[str, List[str]]:
    """
    Rigorously cleans up erratic, stacked, or malformed punctuation in narrative prose.
    Eliminates stacked marks like '.;', ';.', ';;', ',;', removes orphan semicolons,
    normalizes spacing, and restores proper sentence capitalization.
    """
    cleaned = text
    flags: List[str] = []

    # 1. Clean start/end line stray semicolons and punctuation
    cleaned = re.sub(r'(?m)^\s*[,;:]+\s*', '', cleaned)
    cleaned = re.sub(r'(?m)\s*;\s*$', '.', cleaned)

    # 2. Stacked / Mixed Punctuation Fixes
    if re.search(r'\.\s*;+|;+\s*\.', cleaned):
        flags.append("Sanitized period-semicolon combo ('.;' or ';.')")
        cleaned = re.sub(r'\.\s*;+', '.', cleaned)
        cleaned = re.sub(r';+\s*\.', '.', cleaned)

    if re.search(r';{2,}', cleaned):
        flags.append("Sanitized consecutive semicolons (';;')")
        cleaned = re.sub(r';{2,}', ';', cleaned)

    if re.search(r',\s*;+|;+\s*,', cleaned):
        flags.append("Sanitized comma-semicolon combo (',;' or ';,')")
        cleaned = re.sub(r',\s*;+|;+\s*,', ',', cleaned)

    if re.search(r',{2,}', cleaned):
        flags.append("Sanitized multiple commas (',,')")
        cleaned = re.sub(r',{2,}', ',', cleaned)

    if re.search(r':\s*;+|;\s*:+', cleaned):
        flags.append("Sanitized colon-semicolon combo (':;' or ';:')")
        cleaned = re.sub(r':\s*;+|;\s*:+', ':', cleaned)

    if re.search(r'(?<!\.)\.\.(?!\.)', cleaned):
        flags.append("Sanitized double periods ('..')")
        cleaned = re.sub(r'(?<!\.)\.\.(?!\.)', '.', cleaned)

    cleaned = re.sub(r'\.{4,}', '...', cleaned)
    cleaned = re.sub(r'\.\s*,|,\s*\.', '.', cleaned)

    # Dash + punctuation hygiene
    cleaned = re.sub(r'—\s*[,;:]+|[,;:]+\s*—', ' — ', cleaned)
    cleaned = re.sub(r'--\s*[,;:]+|[,;:]+\s*--', ' — ', cleaned)

    # Semicolon before closing quotes -> period before quote
    cleaned = re.sub(r';\s*([\"\'\”\’])', r'.\1', cleaned)

    # 3. Semicolon before Capitalized Word or Conjunction
    if re.search(r';\s+[A-Z]', cleaned):
        flags.append("Split semicolon before capitalized word into clean sentence")
        cleaned = re.sub(r';\s+([A-Z])', r'. \1', cleaned)

    cleaned = re.sub(r';\s+(and|but|or|nor|yet|so)\b', r', \1', cleaned, flags=re.IGNORECASE)

    # 4. Spaces before and after punctuation
    cleaned = re.sub(r'\s+([,.;:!?])', r'\1', cleaned)
    cleaned = re.sub(r'([,;:])([A-Za-z])', r'\1 \2', cleaned)
    cleaned = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', cleaned)

    # 5. Fix capitalization after sentence endings
    cleaned = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), cleaned)

    # 6. Normalize double spaces
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r' +([,.;:!?])', r'\1', cleaned)

    return cleaned.strip(), flags


def audit_and_clean_prose(text: str) -> Tuple[str, List[str]]:
    """
    Audits narrative prose for AI tells, banned clichés, and robotic formatting.
    Performs mechanical cleaning and returns sanitized text along with flagged violations.
    """
    cleaned = text
    flagged: List[str] = []

    # Pre-clean punctuation
    cleaned, punc_flags = sanitize_punctuation(cleaned)
    flagged.extend(punc_flags)

    # 1. Clean bold labels within prose (e.g., "**Scene 1:**" or "**Note:**")
    bold_pattern = re.compile(r'\*\*([^*]+)\*\*')
    def clean_bold(m):
        inner = m.group(1).strip()
        # Keep bold if it's title or section tag like [TITLE]: or [TEXT]:
        if inner.startswith("[") and inner.endswith("]"):
            return m.group(0)
        return inner

    cleaned = bold_pattern.sub(clean_bold, cleaned)

    # 2. Check and clean banned AI words and phrases (longer phrases checked first)
    sorted_banned = sorted(BANNED_AI_WORDS_AND_PHRASES, key=lambda s: len(s), reverse=True)
    for banned in sorted_banned:
        pattern = re.compile(rf'\b{re.escape(banned)}\b', re.IGNORECASE)
        if pattern.search(cleaned):
            flagged.append(f"Banned AI phrase: '{banned}'")
            sub = CRAFT_SUBSTITUTIONS.get(banned.lower())
            if sub:
                cleaned = pattern.sub(sub, cleaned)
            else:
                cleaned = pattern.sub("", cleaned)

    # 3. Detect and soften excessive em dashes (replace runs or overused dashes with commas or periods)
    em_dash_count = cleaned.count("—") + cleaned.count("--")
    if em_dash_count > 6:
        flagged.append(f"Excessive em dashes detected ({em_dash_count})")
        # Replace non-dialogue em-dashes with commas or clean stops
        parts = cleaned.split("—")
        rebuilt = []
        dash_budget = 3
        for idx, part in enumerate(parts):
            if idx == 0:
                rebuilt.append(part)
            elif dash_budget > 0 and ('"' in part or "'" in part):
                rebuilt.append("—" + part)
                dash_budget -= 1
            else:
                rebuilt.append(", " + part.lstrip())
        cleaned = "".join(rebuilt)

    # 4. Clean artificial "Not X, but Y" or "It was not X, but Y" common formulas
    not_x_pattern = re.compile(r'\b(it was not merely|it was not just|not only)\s+([^,]+),\s*(but\s+also|but)\s+', re.IGNORECASE)
    if not_x_pattern.search(cleaned):
        flagged.append("Detected 'Not X, but Y' contrast pattern")
        cleaned = not_x_pattern.sub(r'\2 and ', cleaned)

    # 5. Clean trailing dramatic clichés
    trailing_cliches = [
        (re.compile(r'And nothing would ever be the same\.?', re.IGNORECASE), "The consequences were already taking shape."),
        (re.compile(r'That was the real danger\.?', re.IGNORECASE), ""),
        (re.compile(r'The message was clear:?', re.IGNORECASE), "")
    ]
    for pattern, replacement in trailing_cliches:
        if pattern.search(cleaned):
            flagged.append("Detected dramatic trailing closer cliché")
            cleaned = pattern.sub(replacement, cleaned)

    # Final post-cleanup pass for punctuation hygiene after phrase substitutions
    cleaned, post_punc_flags = sanitize_punctuation(cleaned)
    for pf in post_punc_flags:
        if pf not in flagged:
            flagged.append(pf)

    return cleaned.strip(), flagged

def get_character_persona_texture(role: str, archetype: str, era: str) -> Dict[str, Any]:
    """
    Synthesizes psychological habits, reading interests, musical cadence, and aesthetic artifacts
    for an autonomous character actor based on their narrative role, temperament, and story era.
    Part of Storyteller's Character Persona Architecture.
    """
    role_lower = (role or "").lower()
    arch_lower = (archetype or "").lower()

    if any(k in role_lower or k in arch_lower for k in ["scholar", "intellectual", "academic", "philosopher", "professor", "curator"]):
        return {
            "reading_tastes": ["Classical political philosophy", "Rare archival periodicals", "Gothic antiquities"],
            "musical_temperament": "Baroque cello suites, melancholic solo piano",
            "aesthetic_hallmarks": "Iron gall ink stains, tweed lapels, vintage brass pocket watch"
        }
    elif any(k in role_lower or k in arch_lower for k in ["detective", "investigator", "inspector", "lawyer", "judge", "officer"]):
        return {
            "reading_tastes": ["Forensic case law", "Local municipal maps", "Hardboiled crime fiction"],
            "musical_temperament": "Cool midnight jazz, muted trumpet, slow rain ambiance",
            "aesthetic_hallmarks": "Heavy woolen trench coat, dog-eared field notebook, cold black coffee"
        }
    elif any(k in role_lower or k in arch_lower for k in ["operative", "rebel", "infiltrator", "soldier", "spy", "dissident"]):
        return {
            "reading_tastes": ["Cryptographic treatises", "Underground pamphlets", "Urban architecture blueprints"],
            "musical_temperament": "Industrial synth-wave, low-frequency atmospheric drones",
            "aesthetic_hallmarks": "Tactical matte-black hardware, unbranded waterproof garments, silent footsteps"
        }
    else:
        return {
            "reading_tastes": ["Modern literary memoirs", "Psychological drama", "Historical diaries"],
            "musical_temperament": "Acoustic folk, ambient chamber orchestrations",
            "aesthetic_hallmarks": "Handmade leather journals, tailored linen coats, quiet observational pauses"
        }


from pathlib import Path

SKILLS_ROOT_DIR = Path(__file__).resolve().parent.parent.parent / "skills"

def list_registered_skills() -> List[Dict[str, Any]]:
    """
    Scans the repository's root `skills/` directory for modular agent skill definitions.
    Returns metadata for each discovered skill.
    """
    skills = []
    if not SKILLS_ROOT_DIR.exists():
        return skills

    for child in SKILLS_ROOT_DIR.iterdir():
        skill_file = child / "SKILL.md"
        if child.is_dir() and skill_file.exists():
            desc = ""
            name = child.name
            try:
                content = skill_file.read_text(encoding="utf-8")
                # Parse frontmatter if present
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter = parts[1]
                        for line in frontmatter.splitlines():
                            if line.startswith("description:"):
                                desc = line.split("description:", 1)[1].strip()
                            elif line.startswith("name:"):
                                name = line.split("name:", 1)[1].strip()
            except Exception:
                pass
            skills.append({
                "id": child.name,
                "name": name,
                "description": desc,
                "path": f"skills/{child.name}/SKILL.md"
            })

    return sorted(skills, key=lambda s: s["id"])

def get_skill_content(skill_id: str) -> Optional[str]:
    """
    Reads the full markdown content of a registered skill by ID.
    """
    skill_file = SKILLS_ROOT_DIR / skill_id / "SKILL.md"
    if skill_file.exists():
        try:
            return skill_file.read_text(encoding="utf-8")
        except Exception:
            return None

GENRE_CRAFT_GUIDANCE: Dict[str, str] = {
    "Drama": "Focus on intricate interpersonal friction, moral compromises, domestic and professional stakes, understated human behavior, and simmering resentment rather than melodrama.",
    "Mystery & Crime": "Enforce investigative vigilance, forensic and observational details, hidden alibis, guarded motives, false trails, and the psychological paranoia of guilt and deduction.",
    "Romance": "Channel electrifying emotional proximity, subtextual glances, vulnerability versus defensiveness, physical proximity tensions, and the agonizing risk of intimacy.",
    "Historical": "Imbue the narrative with period-accurate material culture (fabrics, heating methods, lighting, transportation, etiquette, speech registers) without dry exposition; make historical constraints feel living and oppressive.",
    "Fantasy": "Ground magical or wondrous elements in physical weight, bodily exhaustion, and clear consequence; maintain mythic resonance with tactile realism (iron, ash, ancient stones, bloodlines).",
    "Sci-Fi": "Highlight technological alienation, speculative ethical boundaries, systematic surveillance, cold machine interfaces, and existential vertigo against cosmic or digital scales.",
    "Horror": "Cultivate creeping psychological dread, sensory distortions, claustrophobic containment, uncanny irregularities in the mundane, and visceral bodily vulnerability.",
    "Adventure": "Drive propulsive momentum, physical peril, environmental hazards, high-stakes tactical decisions, and immediate physical endurance.",
    "Social Drama": "Interweave class disparities, bureaucratic cruelty, reputation risk, institutional hypocrisy, and the struggle of individuals against crushing societal norms.",
    "Magical Realism": "Treat inexplicable phenomena with matter-of-fact solemnity and emotional truth; let reality blur seamlessly into folklore, symbol, and heightened subjective experience."
}

PROSE_STYLE_GUIDANCE: Dict[str, str] = {
    "Literary & Elegant": "Rich, evocative syntax with rhythmic cadences. Deep psychological interiority, multi-layered sensory observations, resonant metaphors, and elegant sentence architecture.",
    "Clear & Fluent": "Transparent, propulsive prose. Clean active verbs, uncluttered syntax, effortless readability, and immediate immersion without unnecessary ornamentation.",
    "Poetic & Vivid": "Sensory-dense, impressionistic imagery. Lyrical cadences, heightened focus on light, shadow, texture, and scent. Metaphors that surprise and linger.",
    "Crisp & Minimalist": "Hemingway/Cormac McCarthy stripped-down discipline. Short, muscular declarative sentences. Hard physical nouns. Zero sentimentality. Iceberg theory: convey profound emotional devastation through bare physical actions.",
    "Witty & Satirical": "Razor-sharp observational humor, dry cosmopolitan irony, acerbic social commentary, clever dialogue retorts, and satirical subtext puncturing pretensions.",
    "Cold & Journalistic": "Clinical, unsparing objectivity. Dispassionate factual observation, forensic documentation of events, and chilling detachment that allows horrific or tragic events to speak for themselves without editorial tears.",
    "Stream of Consciousness": "Fluid psychological permeability. Thoughts, sensory impressions, memory fragments, and immediate perceptions bleeding into one another with intimate associative momentum.",
    "Epic & Grand": "Sweeping, monumental tone with mythic gravity. Cadenced rhetoric, vast spatial awareness, and a palpable sense of destiny, scale, and historic weight."
}

TONE_GUIDANCE: Dict[str, str] = {
    "Dark & Gritty": "Bleak realism, harsh physical consequences, corrupt institutions, moral ambiguity, and an unvarnished view of human frailty.",
    "Hopeful & Inspiring": "Resilience in adversity, quiet moments of human solidarity, hard-won epiphanies, and faith in human redemption despite overwhelming odds.",
    "Bittersweet": "A profound melancholic grace; victories bought with permanent sacrifice; acute awareness that every forward step leaves something cherished behind.",
    "Tense & Suspenseful": "White-knuckle pacing, heightened paranoia, ticking clocks, sensory hyper-awareness, and characters balancing on the edge of catastrophe.",
    "Humorous & Witty": "Playful cynicism, wry timing, comedic misunderstanding, self-deprecating interiority, and sparkling verbal sparring.",
    "Nostalgic & Melancholic": "A lingering ache for bygone days, faded elegance, autumn light, forgotten promises, and the quiet sorrow of time's irreversible passage.",
    "Cold & Objective": "Detached, analytical, unemotional scrutiny; stark reporting of human transactions and unforgiving environments."
}

THEME_GUIDANCE: Dict[str, str] = {
    "Love & Sacrifice": "Force characters to choose between personal survival and the welfare of another; examine the devastating price of devotion.",
    "Power & Corruption": "Trace how authority, leverage, and desperation erode ethical convictions and reshape human relationships into transactional warfare.",
    "Identity & Belonging": "Confront characters with displacement, cultural or social alienation, masks worn for survival, and the agonizing question of who they truly are.",
    "Forgiveness & Redemption": "Explore the heavy baggage of past guilt, the impossibility of clean slates, and the agonizing moral labor required to earn forgiveness.",
    "Revenge & Justice": "Contrast the hollow appetite for vengeance against the demanding pursuit of moral justice, measuring the collateral damage of retribution.",
    "Freedom & Autonomy": "Pit characters against suffocating institutional, social, or familial cages, testing what they are willing to forfeit to achieve true self-determination.",
    "Loneliness & Connection": "Dramatize the acute pain of emotional isolation and the fragile, terrifying vulnerability required to build genuine human bridges.",
    "Truth & Deceit": "Showcase how convenient lies rot relationships from within, and how unvarnished truth detonates established lives.",
    "Death & Legacy": "Examine the shadow of mortality, what remains behind after one is gone, and the struggle to leave a meaningful imprint.",
    "War & Humanity": "Illuminate the brutal dehumanization of systemic conflict and the quiet, miraculous acts of decency that preserve the human soul."
}

def build_narrative_style_brief(style: Any, world: Any) -> str:
    """
    Synthesizes an exhaustive, unambiguous Narrative Style & Craft Brief from the blueprint's
    genre, prose_style, tone, theme, and Qloo cultural influences.
    Injected directly into LLM stages to ensure stories possess unmistakable voice, atmospheric depth,
    and distinct personality.
    """
    genre_val = getattr(style, "genre", "Drama")
    prose_val = getattr(style, "prose_style", "Literary & Elegant")
    tone_val = getattr(style, "tone", "Bittersweet")
    theme_val = getattr(style, "theme", "Identity & Belonging")
    perspective_val = getattr(style, "perspective", "Third-Person Limited")
    influences = getattr(style, "cultural_influences", []) or []
    thematic_dna = getattr(style, "thematic_dna", []) or []

    genre_rule = "Root conflicts in realistic human friction and high personal stakes."
    for k, v in GENRE_CRAFT_GUIDANCE.items():
        if k.lower() in genre_val.lower() or genre_val.lower() in k.lower():
            genre_rule = v
            break

    prose_rule = "Maintain elegant, engaging sentence structure and sensory depth."
    for k, v in PROSE_STYLE_GUIDANCE.items():
        if k.lower() in prose_val.lower() or prose_val.lower() in k.lower():
            prose_rule = v
            break

    tone_rule = "Infuse every passage with subtle emotional atmosphere."
    for k, v in TONE_GUIDANCE.items():
        if k.lower() in tone_val.lower() or tone_val.lower() in k.lower():
            tone_rule = v
            break

    theme_rule = "Test the characters' deepest convictions through difficult choices."
    for k, v in THEME_GUIDANCE.items():
        if k.lower() in theme_val.lower() or theme_val.lower() in k.lower():
            theme_rule = v
            break

    qloo_section = ""
    if influences or thematic_dna:
        aff_lines = []
        if influences:
            aff_lines.append(f"- Aesthetic Reference Works & Cultural Affinities: {', '.join(influences)}")
        if thematic_dna:
            aff_lines.append(f"- Taste DNA & Thematic Motifs: {', '.join(thematic_dna)}")
        qloo_section = (
            f"\nQLOO CULTURAL & TASTE INTELLIGENCE:\n"
            + "\n".join(aff_lines)
            + "\nInfuse the narrative atmosphere, character tastes, and aesthetic palette with the distinctive mood and sensibilities of these cultural touchstones."
        )

    brief = f"""==================================================
NARRATIVE STYLE & AESTHETIC DIRECTIVES:
- PRIMARY GENRE: "{genre_val}"
  Craft Directive: {genre_rule}

- PROSE STYLE & SYNTAX: "{prose_val}"
  Diction Directive: {prose_rule}

- NARRATIVE TONE & MOOD: "{tone_val}"
  Atmospheric Directive: {tone_rule}

- CENTRAL THEME: "{theme_val}"
  Thematic Tension: {theme_rule}

- NARRATIVE PERSPECTIVE: "{perspective_val}"
  Psychic Distance: Stay strictly grounded inside the viewpoint of the POV character. Never head-hop or judge from an omniscient outside narrator.
{qloo_section}
=================================================="""
    return brief
    return None

GENRE_CRAFT_GUIDANCE: Dict[str, str] = {
    "Drama": "Focus on intricate interpersonal friction, moral compromises, domestic and professional stakes, understated human behavior, and simmering resentment rather than melodrama.",
    "Mystery & Crime": "Enforce investigative vigilance, forensic and observational details, hidden alibis, guarded motives, false trails, and the psychological paranoia of guilt and deduction.",
    "Romance": "Channel electrifying emotional proximity, subtextual glances, vulnerability versus defensiveness, physical proximity tensions, and the agonizing risk of intimacy.",
    "Historical": "Imbue the narrative with period-accurate material culture (fabrics, heating methods, lighting, transportation, etiquette, speech registers) without dry exposition; make historical constraints feel living and oppressive.",
    "Fantasy": "Ground magical or wondrous elements in physical weight, bodily exhaustion, and clear consequence; maintain mythic resonance with tactile realism (iron, ash, ancient stones, bloodlines).",
    "Sci-Fi": "Highlight technological alienation, speculative ethical boundaries, systematic surveillance, cold machine interfaces, and existential vertigo against cosmic or digital scales.",
    "Horror": "Cultivate creeping psychological dread, sensory distortions, claustrophobic containment, uncanny irregularities in the mundane, and visceral bodily vulnerability.",
    "Adventure": "Drive propulsive momentum, physical peril, environmental hazards, high-stakes tactical decisions, and immediate physical endurance.",
    "Social Drama": "Interweave class disparities, bureaucratic cruelty, reputation risk, institutional hypocrisy, and the struggle of individuals against crushing societal norms.",
    "Magical Realism": "Treat inexplicable phenomena with matter-of-fact solemnity and emotional truth; let reality blur seamlessly into folklore, symbol, and heightened subjective experience."
}

PROSE_STYLE_GUIDANCE: Dict[str, str] = {
    "Literary & Elegant": "Rich, evocative syntax with rhythmic cadences. Deep psychological interiority, multi-layered sensory observations, resonant metaphors, and elegant sentence architecture.",
    "Clear & Fluent": "Transparent, propulsive prose. Clean active verbs, uncluttered syntax, effortless readability, and immediate immersion without unnecessary ornamentation.",
    "Poetic & Vivid": "Sensory-dense, impressionistic imagery. Lyrical cadences, heightened focus on light, shadow, texture, and scent. Metaphors that surprise and linger.",
    "Crisp & Minimalist": "Hemingway/Cormac McCarthy stripped-down discipline. Short, muscular declarative sentences. Hard physical nouns. Zero sentimentality. Iceberg theory: convey profound emotional devastation through bare physical actions.",
    "Witty & Satirical": "Razor-sharp observational humor, dry cosmopolitan irony, acerbic social commentary, clever dialogue retorts, and satirical subtext puncturing pretensions.",
    "Cold & Journalistic": "Clinical, unsparing objectivity. Dispassionate factual observation, forensic documentation of events, and chilling detachment that allows horrific or tragic events to speak for themselves without editorial tears.",
    "Stream of Consciousness": "Fluid psychological permeability. Thoughts, sensory impressions, memory fragments, and immediate perceptions bleeding into one another with intimate associative momentum.",
    "Epic & Grand": "Sweeping, monumental tone with mythic gravity. Cadenced rhetoric, vast spatial awareness, and a palpable sense of destiny, scale, and historic weight."
}

TONE_GUIDANCE: Dict[str, str] = {
    "Dark & Gritty": "Bleak realism, harsh physical consequences, corrupt institutions, moral ambiguity, and an unvarnished view of human frailty.",
    "Hopeful & Inspiring": "Resilience in adversity, quiet moments of human solidarity, hard-won epiphanies, and faith in human redemption despite overwhelming odds.",
    "Bittersweet": "A profound melancholic grace; victories bought with permanent sacrifice; acute awareness that every forward step leaves something cherished behind.",
    "Tense & Suspenseful": "White-knuckle pacing, heightened paranoia, ticking clocks, sensory hyper-awareness, and characters balancing on the edge of catastrophe.",
    "Humorous & Witty": "Playful cynicism, wry timing, comedic misunderstanding, self-deprecating interiority, and sparkling verbal sparring.",
    "Nostalgic & Melancholic": "A lingering ache for bygone days, faded elegance, autumn light, forgotten promises, and the quiet sorrow of time's irreversible passage.",
    "Cold & Objective": "Detached, analytical, unemotional scrutiny; stark reporting of human transactions and unforgiving environments."
}

THEME_GUIDANCE: Dict[str, str] = {
    "Love & Sacrifice": "Force characters to choose between personal survival and the welfare of another; examine the devastating price of devotion.",
    "Power & Corruption": "Trace how authority, leverage, and desperation erode ethical convictions and reshape human relationships into transactional warfare.",
    "Identity & Belonging": "Confront characters with displacement, cultural or social alienation, masks worn for survival, and the agonizing question of who they truly are.",
    "Forgiveness & Redemption": "Explore the heavy baggage of past guilt, the impossibility of clean slates, and the agonizing moral labor required to earn forgiveness.",
    "Revenge & Justice": "Contrast the hollow appetite for vengeance against the demanding pursuit of moral justice, measuring the collateral damage of retribution.",
    "Freedom & Autonomy": "Pit characters against suffocating institutional, social, or familial cages, testing what they are willing to forfeit to achieve true self-determination.",
    "Loneliness & Connection": "Dramatize the acute pain of emotional isolation and the fragile, terrifying vulnerability required to build genuine human bridges.",
    "Truth & Deceit": "Showcase how convenient lies rot relationships from within, and how unvarnished truth detonates established lives.",
    "Death & Legacy": "Examine the shadow of mortality, what remains behind after one is gone, and the struggle to leave a meaningful imprint.",
    "War & Humanity": "Illuminate the brutal dehumanization of systemic conflict and the quiet, miraculous acts of decency that preserve the human soul."
}

def build_narrative_style_brief(style: Any, world: Any) -> str:
    """
    Synthesizes an exhaustive, unambiguous Narrative Style & Craft Brief from the blueprint's
    genre, prose_style, tone, theme, and Qloo cultural influences.
    Injected directly into LLM stages to ensure stories possess unmistakable voice, atmospheric depth,
    and distinct personality.
    """
    genre_val = getattr(style, "genre", "Drama")
    prose_val = getattr(style, "prose_style", "Literary & Elegant")
    tone_val = getattr(style, "tone", "Bittersweet")
    theme_val = getattr(style, "theme", "Identity & Belonging")
    perspective_val = getattr(style, "perspective", "Third-Person Limited")
    influences = getattr(style, "cultural_influences", []) or []
    thematic_dna = getattr(style, "thematic_dna", []) or []

    genre_rule = "Root conflicts in realistic human friction and high personal stakes."
    for k, v in GENRE_CRAFT_GUIDANCE.items():
        if k.lower() in genre_val.lower() or genre_val.lower() in k.lower():
            genre_rule = v
            break

    prose_rule = "Maintain elegant, engaging sentence structure and sensory depth."
    for k, v in PROSE_STYLE_GUIDANCE.items():
        if k.lower() in prose_val.lower() or prose_val.lower() in k.lower():
            prose_rule = v
            break

    tone_rule = "Infuse every passage with subtle emotional atmosphere."
    for k, v in TONE_GUIDANCE.items():
        if k.lower() in tone_val.lower() or tone_val.lower() in k.lower():
            tone_rule = v
            break

    theme_rule = "Test the characters' deepest convictions through difficult choices."
    for k, v in THEME_GUIDANCE.items():
        if k.lower() in theme_val.lower() or theme_val.lower() in k.lower():
            theme_rule = v
            break

    qloo_section = ""
    if influences or thematic_dna:
        aff_lines = []
        if influences:
            aff_lines.append(f"- Aesthetic Reference Works & Cultural Affinities: {', '.join(influences)}")
        if thematic_dna:
            aff_lines.append(f"- Taste DNA & Thematic Motifs: {', '.join(thematic_dna)}")
        qloo_section = (
            f"\nQLOO CULTURAL & TASTE INTELLIGENCE:\n"
            + "\n".join(aff_lines)
            + "\nInfuse the narrative atmosphere, character tastes, and aesthetic palette with the distinctive mood and sensibilities of these cultural touchstones."
        )

    brief = f"""==================================================
NARRATIVE STYLE & AESTHETIC DIRECTIVES:
- PRIMARY GENRE: "{genre_val}"
  Craft Directive: {genre_rule}

- PROSE STYLE & SYNTAX: "{prose_val}"
  Diction Directive: {prose_rule}

- NARRATIVE TONE & MOOD: "{tone_val}"
  Atmospheric Directive: {tone_rule}

- CENTRAL THEME: "{theme_val}"
  Thematic Tension: {theme_rule}

- NARRATIVE PERSPECTIVE: "{perspective_val}"
  Psychic Distance: Stay strictly grounded inside the viewpoint of the POV character. Never head-hop or judge from an omniscient outside narrator.
{qloo_section}
=================================================="""
    return brief

