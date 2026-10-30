# Storyteller AI Studio

An autonomous, multi-agent novel writing studio and narrative intelligence platform built with a 6-stage literary production line, integrated **Qloo Taste AI™** cultural intelligence, and battle-tested **AI creative writing frameworks**.

Unlike single-prompt chatbots that produce flat, predictable summaries, Storyteller operates like a collaborative writer's room and cinematic director suite, transforming core premises into multi-chapter literary fiction with deep psychological interiority, genuine subtext, and multi-sensory environmental immersion.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Story Muse & Cultural Taste AI                       │
│    (Qloo Insights Graph: Cross-Domain Literary & Cinematic Affinities)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│       Stage 1:       │    │       Stage 2:       │    │       Stage 3:       │
│     World & Cast     ├───►│     Story Matrix     ├───►│    Scene Director    │
│  Psychology Architect│    │    Pacing & Beats    │    │& Sensory Atmosphere  │
└──────────────────────┘    └──────────────────────┘    └──────────┬───────────┘
                                                                   │
                                                                   ▼
┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│       Stage 6:       │    │       Stage 5:       │    │       Stage 4:       │
│  Memory & Continuity │◄───┤    Master Novelist   │◄───┤  Multi-Agent Actor   │
│   Event Chain Keeper │    │ Prose Synthesis Engine│   │Roleplay & Subtext Sim│
└──────────────────────┘    └──────────────────────┘    └──────────────────────┘
```

---

## 🌟 Key Architecture & Capabilities

### 1. Cultural Taste Intelligence (Powered by Qloo Taste AI™)
- **Cross-Domain Taste Graph**: Directly queries Qloo's `/search` and `/v2/insights` endpoints to discover high-affinity cultural connections across literature, cinema, and geographical settings based on user-provided cultural signals.
- **Interactive 3-Scenario Generator**: Synthesizes 3 distinct, compelling novel scenarios (high-concept logline, premise, dramatic hook, protagonist archetypes, and cultural aesthetic touchstones) with instant 1-click loading into the Creation Wizard.
- **Persistent Cultural DNA**: Selected cultural affinities and aesthetic motifs are preserved directly in the novel's blueprint and fed into every stage of worldbuilding and prose generation.
- **Author Aesthetic Archetype**: Calibrates the author's creative identity (e.g., *Visionary Speculative Architect*, *Gothic & Dark Academia Chronicler*, *Master of Intrigue & Moral Ambiguity*, *Lyrical Humanist*, or *Literary Stylist*).

---

### 2. The 6-Stage Autonomous Multi-Agent Production Pipeline

1. **Stage 1: World & Cast Psychology Architect**
   - Implements the *Character Internal Landscape Builder* and *Social Dynamics Architecture*.
   - Models external **Want**, internal **Need**, tragic **Fatal Flaw**, buried **Dark Secret**, latent behavioral contradictions, and speech cadences.
   - Maps dyadic relationships, information asymmetries (what Character A knows that Character B conceals), and interpersonal powder kegs.
   - Enforces anthropological worldbuilding: material realities, cultural taboos, architecture, and sensory textures.

2. **Stage 2: Story Matrix & Plot Structure Weaver**
   - Integrates the **12-Stage Hero's Journey** and the **Save the Cat! 15-Beat** pacing framework.
   - Constructs a 2D matrix of `Character × Episode`, ensuring tight causal momentum and distinct chapter arcs.
   - Implements *Foreshadowed Plot Twists* with retroactive inevitability: plants early narrative seeds so climaxes feel shocking yet completely justified in retrospect.

3. **Stage 3: Cinematic Scene Director & Environmental Designer**
   - Breaks each episode into 2 to 3 dramatic, dynamic scenes with rising tension arcs (Beginning Complication -> Rising Friction -> Critical Turn).
   - Injects the **Multi-Sensory Scene Atmosphere Framework**:
     - *Acoustic Palette*: low-frequency background hum, reverberation, and sharp auditory interruptions.
     - *Olfactory & Ambient Notes*: smoke, damp slate, old paper, rain, or chemical scents.
     - *Tactile Feedback*: ambient temperature, barometric pressure, moisture, and surface textures.
     - *Lighting Dynamics*: direction, color temperature, and what remains obscured in shadows.

4. **Stage 4: Autonomous Multi-Agent Character Simulation**
   - Characters act as independent agents possessing **isolated epistemic horizons** (zero telepathic or omniscient leakage).
   - Implements the **Subtext-Driven Dialogue Framework**: characters never speak their core desires directly; they deflect, use metaphor, employ tactical silence, and maneuver for psychological control.
   - Records each turn's **Physical Staging** (`action`), **Spoken Dialogue** (`dialogue`), and **Unspoken Internal Calculations** (`thought`).

5. **Stage 5: Master Novelist Prose Synthesis**
   - Converts theatrical scene logs into publication-ready literary fiction adhering to the **Show-Don’t-Tell Prose Stylistic Converter**.
   - Banned abstract emotional announcements (e.g., "he felt dread" or "a wave of sorrow washed over her"). Internal states are converted into visceral somatic sensations, physical friction, and involuntary body language.
   - Strictly enforces negative anti-AI constraints: zero artificial "Not X, but Y" formulas, no dramatic one-line trailing truisms, no forced triads, and strict punctuation hygiene.

6. **Stage 6: Story Memory & Continuity Keeper**
   - Maintains an evolving running summary, tracks unresolved narrative threads (`open_threads`), and records newly revealed world facts to prevent contradictions across expansive multi-chapter arcs.

---

### 3. Dynamic Narrative Style & Craft Directives
Storyteller actively adapts its prose, scene blocking, and character voice based on user selections:

- **Primary Genre Guidance**: Detailed craft rules for *Mystery & Crime*, *Gothic & Horror*, *Romance*, *Historical Fiction*, *Sci-Fi & Speculative*, *Drama*, *Adventure*, and *Magical Realism*.
- **Prose Style Directives**: Concrete syntactical rules for *Literary & Elegant*, *Crisp & Minimalist* (Hemingway/Cormac McCarthy discipline), *Poetic & Vivid*, *Clear & Fluent*, *Witty & Satirical*, *Cold & Journalistic*, and *Epic & Grand*.
- **Narrative Tone**: Atmosphere directives for *Dark & Gritty*, *Bittersweet*, *Tense & Suspenseful*, *Hopeful & Inspiring*, *Humorous & Witty*, and *Nostalgic & Melancholic*.
- **Central Theme**: Infuses moral friction and dilemma based on *Love & Sacrifice*, *Power & Corruption*, *Identity & Belonging*, *Revenge & Justice*, *Freedom & Autonomy*, *Truth & Deceit*, and *War & Humanity*.

---

### 4. Behind the Scenes Exploration & Persistent Drawer
- Every episode stores its complete theatrical breakdown in SQLite (`scenes_json`).
- In the reader, click **"🎭 Behind the Scenes"** to slide open the interactive drawer and inspect:
  - Exact scene dramatic goals and conflicts.
  - Character physical staging and body language.
  - Authentic spoken dialogue.
  - **Secret Unspoken Thoughts** and psychological calculations.

---

### 5. Integrity & Story Generation Queue
- **No Mock / Fallback Text in Production**: When an LLM endpoint is offline, rate-limited, or pending capacity, the studio safely sets the status to `"In Story Generation Queue"` with a clear notification. The system never fabricates repetitive canned text.

---

## 🚀 Quick Start

### 1. Requirements & Installation
Ensure Python 3.10+ is installed:
```bash
git clone https://github.com/mohamadreza1368/Storyteller.git
cd Storyteller
pip install fastapi uvicorn pydantic google-genai openai requests
```

### 2. Launch the Application
```bash
python run.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

### 3. Run the End-to-End Verification Test
Verify the complete 6-stage pipeline and storage engine offline:
```bash
python test_pipeline.py
```

---

## 🛠️ Global AI Engine Configuration

Administrators can configure centralized AI gateways in the **Admin Console** (`#viewAdmin`):

| Engine Component | Supported Gateways | Configuration Details |
| :--- | :--- | :--- |
| **Story LLM (Narrator)** | OpenRouter, OpenAI, Google Gemini, Ollama, Custom OpenAI-Compatible | Set `Provider`, `Base URL`, `API Key`, and `Model Name` (e.g. `anthropic/claude-3.5-sonnet`, `gemini-2.5-flash`, `gpt-4o-mini`) |
| **Chapter Illustration (Image)** | OpenRouter, OpenAI DALL-E 3, Google Gemini Imagen 3, Custom Image Gateway | Set `Image Provider`, `Image Base URL`, `Image API Key`, and `Image Model` |
| **Cultural & Taste Intelligence** | Qloo Basic Insights (`/v2/insights`), Qloo Hackathon Gateway | Set `Qloo Base URL` (`https://hackathon.api.qloo.com`), `Qloo API Key`, and toggle on |

---

## 📁 Repository Structure

```
storyteller/
├── skills/                             # Modular agent skills & open craft specifications
│   ├── book-writer/SKILL.md            # Pacing, tension mapping, and third-person limited craft
│   ├── humanizer/SKILL.md              # Elimination of AI staging, aphorisms, and forced triads
│   ├── avoid-ai-writing/SKILL.md       # AI vocabulary blacklist and sensory substitutions
│   └── qloo-cultural-intelligence/SKILL.md # Cultural taste graph integration spec
├── app/
│   ├── config.py                       # Application settings and environment variables
│   ├── main.py                         # FastAPI server entry point and static routing
│   ├── models/                         # Pydantic data schemas
│   │   ├── enums.py                    # Genre, ProseStyle, Theme, Tone, Temperament enums
│   │   ├── character.py                # Character persona, motivations, arcs, and relationships
│   │   ├── blueprint.py                # Master novel blueprint, world locations, and cast settings
│   │   ├── simulation.py               # Actor turns, scene records, and story memory models
│   │   └── episode.py                  # Episode models and pipeline progress trackers
│   ├── engine/                         # Multi-agent literary production line
│   │   ├── llm_client.py               # Resilient multi-provider LLM client with timeout & error handling
│   │   ├── image_client.py             # Dedicated chapter illustration and cover generator
│   │   ├── qloo_client.py              # Cultural Taste AI client (affinities, archetypes, scenarios)
│   │   ├── writing_craft.py            # Style briefs, genre guidance, humanizer gates, and punctuation hygiene
│   │   ├── prompts.py                  # Battle-tested creative writing system prompts for all 6 stages
│   │   ├── stage1_world_cast.py        # Stage 1: World and character generation
│   │   ├── stage2_matrix.py            # Stage 2: Story matrix and chapter arcs
│   │   ├── stage3_director.py          # Stage 3: Scene directorship and sensory atmosphere
│   │   ├── stage4_character_sim.py     # Stage 4: Multi-agent turn-by-turn roleplay simulation
│   │   ├── stage5_narrator.py          # Stage 5: Master novelist literary prose synthesis
│   │   ├── stage6_memory.py            # Stage 6: Running memory and open plot thread tracking
│   │   └── pipeline.py                 # Background pipeline coordinator & progress tracker
│   ├── storage/                        # SQLite persistence & database migrations
│   │   ├── database.py                 # SQLite connection pool, schema definitions, and column migrations
│   │   ├── users.py                    # User authentication, token handling, and PBKDF2 hashing
│   │   └── store.py                    # Persistence for blueprints, episodes, scenes, and settings
│   ├── api/                            # REST API endpoints
│   │   ├── auth.py                     # Registration, login, logout, and profile management
│   │   ├── admin.py                    # Platform analytics, user administration, and global AI config
│   │   ├── novels.py                   # Novel CRUD, generation triggers, scenarios, and presets
│   │   └── system.py                   # System diagnostics and connection test endpoints
│   └── static/                         # Studio single-page application (SPA)
│       ├── index.html                  # Responsive studio interface (Wizard, Library, Reader, Admin)
│       ├── app.css                     # Premium typography, color palettes, and responsive layouts
│       └── app.js                      # Frontend application controller and live progress polling
├── test_pipeline.py                    # End-to-end verification test suite
├── run.py                              # Server launcher
└── README.md                           # Documentation
```

---

## 📄 License
MIT License.
