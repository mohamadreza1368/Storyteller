# Storyteller AI Studio

An autonomous, multi-agent novel writing and narrative intelligence platform built with a multi-tier generation architecture and an integrated cultural taste engine.

Unlike simple chatbots that produce unstructured chapters in a single prompt, Storyteller orchestrates an authentic **6-stage literary production line** augmented with **Taste & Cultural Intelligence**:

```
[Story Muse: Taste & Scenarios] ──> [Stage 1: World & Cast] ──> [Stage 2: Story Matrix] ──> [Stage 3: Scene Director]
                                                                                                  │
                                                                                                  ▼
[Stage 6: Memory Keeper] <── [Stage 5: Prose Synthesis] <── [Stage 4: Character Simulation] <─────┘
```

---

## 🌟 Key Architecture & Capabilities

### 1. Story Muse & Cultural Taste Intelligence (Powered by Qloo Basic Insights)
- **Qloo Taste Graph Queries**: Directly queries Qloo's `/search` and `/v2/insights` endpoints (using the documented `take` parameter and deep entity extraction) to discover real cross-domain cultural recommendations across books, films, and places based on user-provided cultural signals.
- **Interactive 3-Scenario Generator**: Translates Qloo cultural affinities into 3 distinct, compelling novel premises (complete with high-concept loglines, dramatic hooks, core conflict, and protagonist archetypes) with instant 1-click loading into the creation wizard.
- **Dynamic Contextual Synthesis**: When offline or unconfigured, dynamically synthesizes tailored creative affinities matching the specific input genres rather than relying on static lists.
- **Author Aesthetic Archetype**: Synthesizes the author's narrative profile and aesthetic archetype (e.g., *Visionary Speculative Architect*, *Gothic & Dark Academia Chronicler*, *Master of Intrigue & Moral Ambiguity*, *Lyrical Humanist*, or *Literary Stylist*).

### 2. The 6-Stage Autonomous Multi-Agent Pipeline
1. **Stage 1: World & Cast Architect**
   - Synthesizes indelible world locations, atmospheric rules, and deep psychological character dossiers.
   - Character Persona Architecture models external **Want**, internal **Need**, tragic **Flaw**, hidden **Secret**, intellectual reading interests, and aesthetic temperament.
2. **Stage 2: Story Matrix Weaver**
   - Constructs a 2D matrix of `Character × Episode`, tracking main arcs, subplots, and escalation beats across every chapter.
3. **Stage 3: Scene Director**
   - Segments each episode into distinct dramatic scenes complete with time of day, location keys, Point of View (POV), central dramatic goal, and escalating tension.
4. **Stage 4: Autonomous Character Actor Simulation**
   - Each character acts as an independent agent possessing **asymmetric knowledge** (preventing omniscient hallucinations).
   - In each turn, the agent records its **Secret Internal Monologue** (`thought`), **Physical Body Language & Staging** (`action`), and spoken dialogue (`dialogue`).
5. **Stage 5: Master Novelist Prose Synthesis**
   - Translates turn-by-turn theatrical interactions into immersive, publication-ready literary prose adhering to the cardinal rule of *"Show, Don't Tell"*.
6. **Stage 6: Story Memory & Continuity Keeper**
   - Maintains an evolving running summary, tracks unresolved narrative threads (`open_threads`), and freezes established world facts to guarantee long-form consistency.

---

### 3. Modular Agent Skills & Literary Quality Gates
The engine's creative pipeline is guided by 4 dedicated, open agent skill definitions located in the root `skills/` directory:
- **`book-writer`** (`skills/book-writer/SKILL.md`): Enforces third-person limited interiority, sensory staging, dynamic sentence cadence, and dramatic scene tension curves.
- **`humanizer`** (`skills/humanizer/SKILL.md`): Eradicates characteristic LLM tells including artificial "Not X, but Y" contrasts, isolated dramatic one-liner closures, pseudo-profound aphorisms, forced triads, and narrator throat-clearing.
- **`avoid-ai-writing`** (`skills/avoid-ai-writing/SKILL.md`): Strict blacklist of overused AI tropes (`delve`, `tapestry`, `palpable`, `beacon`, `labyrinthine`, `dance of shadows`), coupled with automated post-generation regex substitution and punctuation sanitization.
- **`qloo-cultural-intelligence`** (`skills/qloo-cultural-intelligence/SKILL.md`): Interfaces with Qloo's Taste AI graph across books, cinema, music, and places to ground narrative seeds, scenarios, and character tastes in verified cultural data.

---

## 🚀 Quick Start

### 1. Install Dependencies
Ensure Python 3.10+ (tested on Python 3.10, 3.11, 3.12, 3.14) is installed:
```bash
pip install fastapi uvicorn pydantic google-genai openai requests
```

### 2. Launch the Studio
```bash
python run.py
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

### 3. Administrator Setup
The platform initializes with role-based access control (Admin & Author roles). System administrators can access the centralized Admin Console (`#viewAdmin`) to configure global AI engine credentials, oversee story volume metrics, and manage registered authors.

---

## 👥 Multi-User Web Architecture & Author Profiles

Storyteller is built as a collaborative multi-user platform:
- **Authentication & Security**: Secure token-based registration and login with salt-based PBKDF2 password hashing stored in SQLite.
- **Onboarding Taste Calibration**: Authors can optionally provide up to 5 favorite books and 5 films during registration to calibrate their studio persona (or skip directly).
- **Author Profile & Studio Personalization**: Authors can manage their display name, bio, credentials, and review or update their creative aesthetic archetype and cultural inspirations at any time.
- **Library Isolation**: Each author manages their own personal story library.
- **Zero API Friction for Authors**: Regular authors never enter or manage API keys. The platform utilizes centralized global AI configurations managed solely by administrators.

---

## 🛡️ Administration Console & Global AI Engines

Administrators have access to a dedicated **Administration Console** (`#viewAdmin`):
- **Live Platform KPI Analytics**: Real-time tracking of registered authors, total novels created, chapters generated, and cumulative word counts.
- **Author Oversight with Privacy Protection**: Displays each author's account status and story volume (`novels_count`) while keeping private novel text strictly confidential.
- **Account Actions**: Suspend or reactivate authors, reset author passwords, or remove accounts.
- **Centralized Global AI Management**:
  - **Narrative LLM Provider**: Custom API proxy, Google Gemini, OpenAI, OpenRouter, Ollama, Mock with custom endpoint URLs and keys.
  - **Dedicated Chapter Illustration Engine (Image API)**:
    - Provider selection (Custom OpenAI-compatible image endpoint, Official OpenAI DALL-E, Google Gemini Imagen, Smart AI Flux, or Offline Vector Art).
    - Dedicated Image Base URL (e.g., AvalAI, OpenRouter, Local Stable Diffusion / WebUI).
    - Dedicated Image API key and model selection (`dall-e-3`, `flux-1.1-pro`, `imagen-3.0-generate-002`).
    - Quick 1-click gateway presets and live latency diagnostics.
  - **Cultural & Taste Intelligence Provider**:
    - Centralized configuration for cultural taste graph API (Qloo Basic Insights specification).
    - Gateway presets for Hackathon (`hackathon.api.qloo.com`) and Production (`api.qloo.com`).
    - Integrated live connectivity tester and automatic intelligent fallback engine.

| Engine | Supported Models / Providers | Configuration |
| :--- | :--- | :--- |
| **Story LLM (Narrative)** | Custom API (AvalAI, Groq, DeepSeek, vLLM, LM Studio), Gemini, OpenAI, OpenRouter, Ollama | Set `Base URL`, `API Key`, and `Model Name` |
| **Chapter Illustration (Image)** | Custom Image API (AvalAI, OpenRouter, Local SD), OpenAI (`dall-e-3`), Gemini (`imagen-3.0`), Smart AI (Flux) | Set dedicated `Image Base URL`, `Image API Key`, and `Image Model` |
| **Cultural & Taste Intelligence** | Qloo Basic Insights (`/v2/insights`), Custom Cultural Graph, Built-in Fallback | Set `Base URL`, `API Key` (`X-Api-Key`), and toggle |

---

## 🎭 Novel Studio Features

- **Story Muse & 3-Scenario Synthesis**: Explore connected cultural affinities and generate 3 rich, genre-defining novel scenarios with instant 1-click creation wizard loading.
- **1-Click Literary Presets**: Instantly seed your novel with classic and modern concepts (Gothic Victorian, Parisian Romance, Cyberpunk Noir).
- **AI Magic Co-pilot**: Type a one-line idea or title, and the AI will auto-populate genre, tone, era, city, and premise in seconds.
- **Behind the Scenes Drawer**: In the reading view, click **"🎭 Behind the Scenes"** to slide open the actor simulation drawer and inspect characters' secret thoughts, raw body language, and dramatic turns behind every paragraph.
- **Kindle-Style Reader**: Customize your reading experience with Day, Sepia, and Night color palettes, adjustable typography, and one-click copy / markdown export.
- **Full Continuity & State Recovery**: Novels and generated episodes are stored automatically as JSON blueprints and memory banks under `data/novels/`.

---

## 📁 Repository Structure

```
storyteller/
├── skills/                       # Open agent skills & literary quality specifications
│   ├── book-writer/SKILL.md      # Pacing, tension mapping, and third-person limited craft
│   ├── humanizer/SKILL.md        # Elimination of AI staging, aphorisms, and forced triads
│   ├── avoid-ai-writing/SKILL.md # AI vocabulary blacklist and sensory substitutions
│   └── qloo-cultural-intelligence/SKILL.md # Cultural taste graph integration spec
├── app/
│   ├── config.py                 # Application settings and environment variables
│   ├── main.py                   # FastAPI server entry point and static routing
│   ├── models/                   # Pydantic data schemas
│   │   ├── enums.py              # Genre, ProseStyle, Theme, Tone, Temperament enums
│   │   ├── character.py          # Character persona, motivations, arcs, and relationships
│   │   ├── blueprint.py          # Master novel blueprint, world locations, and cast settings
│   │   ├── simulation.py         # Actor turns, scene records, and story memory models
│   │   └── episode.py            # Episode models and pipeline progress trackers
│   ├── engine/                   # Multi-agent literary production line & intelligence
│   │   ├── llm_client.py         # Multi-provider LLM client (Custom, Gemini, OpenAI, Ollama, Mock)
│   │   ├── qloo_client.py        # Cultural Taste & Basic Insights client (affinities, archetypes, scenarios)
│   │   ├── prompts.py            # Systematic literary prompts for all 6 stages
│   │   ├── stage1_world_cast.py  # Stage 1: World and character generation
│   │   ├── stage2_matrix.py      # Stage 2: Story matrix and chapter arcs
│   │   ├── stage3_director.py    # Stage 3: Scene directorship and POV planning
│   │   ├── stage4_character_sim.py# Stage 4: Multi-agent turn-by-turn roleplay simulation
│   │   ├── stage5_narrator.py    # Stage 5: Literary prose synthesis
│   │   ├── stage6_memory.py      # Stage 6: Running memory and open plot thread tracking
│   │   └── pipeline.py           # Background pipeline coordinator
│   ├── storage/                  # SQLite and JSON file persistence
│   │   ├── database.py           # SQLite connection pool and automated migrations
│   │   ├── users.py              # User management, token handling, and password hashing
│   │   └── store.py              # Disk persistence for blueprints, episodes, and settings
│   ├── api/                      # REST API endpoints
│   │   ├── auth.py               # Registration, login, logout, and profile management
│   │   ├── admin.py              # Platform KPI analytics, user administration, and global AI config
│   │   ├── novels.py             # Novel CRUD, generation triggers, scenarios, and presets
│   │   └── system.py             # System diagnostics and connection test endpoints
│   └── static/                   # Studio frontend single-page application
│       ├── index.html            # Studio SPA layout (Wizard, Library, Reader, Settings, Admin)
│       ├── app.css               # Clean typography, dark mode, and responsive layout
│       └── app.js                # Studio UI controller and live polling
├── data/novels/                  # Saved novel blueprints and episode records
├── test_pipeline.py              # End-to-end verification script
├── run.py                        # Fast server launcher
└── README.md
```

---

## 📄 License
MIT License.
