# Storyteller AI Studio

An autonomous, multi-agent novel writing platform built by reverse-engineering the multi-tier generation architecture of `novel.imedata.ir` and upgraded into a modern, streamlined literary writing suite.

Unlike simple chatbots that generate an entire chapter in a single, unstructured prompt, Storyteller AI orchestrates an authentic **6-stage literary production line**:

```
[Stage 1: World & Cast] ──> [Stage 2: Story Matrix] ──> [Stage 3: Scene Director]
                                                                  │
                                                                  ▼
[Stage 6: Memory Keeper] <── [Stage 5: Prose Synthesis] <── [Stage 4: Character Simulation]
```

---

## 🌟 Key Architecture & Capabilities

### 1. The 6-Stage Autonomous Multi-Agent Pipeline
1. **Stage 1: World & Cast Architect**
   - Synthesizes indelible world locations, atmospheric rules, and deep psychological character dossiers.
   - Distinctly isolates external **Want**, internal **Need**, tragic **Flaw**, hidden **Secret**, and Jungian / classical archetypes (`Temperament`).
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

## 🚀 Quick Start

### 1. Launch the Server
Ensure Python 3.10+ (or 3.14) is installed with dependencies:
```bash
pip install fastapi uvicorn pydantic google-genai openai requests
```

Launch the studio:
```bash
python run.py
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:8000`**

### Default Administrator Account
The platform automatically provisions an initial admin account for platform management:
- **Email**: `admin@storyteller.ai`
- **Password**: `admin123`
*(Admins can change this password at any time via Author Profile or Admin Console)*

---

## 👥 Multi-User Web Architecture & Profile Management

Storyteller is built as a multi-user web application:
- **User Authentication**: Secure token-based registration and login with salt-based PBKDF2 password hashing.
- **Author Profile**: Users can update their display name, bio, credentials, and track their authored stories.
- **Library Isolation**: Each author manages their own personal story library.
- **Zero API Friction for Authors**: Regular authors never enter or manage API keys. The entire platform utilizes centralized global AI configurations managed solely by administrators.

---

## 🛡️ Administration Console & Global AI Engine

Administrators have access to a dedicated **Administration Console** (`#viewAdmin`):
- **Live Platform KPI Analytics**: Real-time tracking of registered authors, total novels created, chapters generated, and cumulative word counts.
- **Author Oversight with Privacy Protection**: Displays each author's account status and story volume (`novels_count`) while keeping private novel text strictly confidential.
- **Account Actions**: Suspend or reactivate authors, reset author passwords, or remove accounts.
- **Centralized Global AI Management**:
  - Global LLM provider selection (Custom API proxy, Google Gemini, OpenAI, OpenRouter, Ollama, Mock) with custom endpoint URLs and keys.
  - **Dedicated Chapter Illustration Engine (Image API)**:
    - Independent provider selection (Custom OpenAI-compatible image endpoint, Official OpenAI DALL-E, Google Gemini Imagen, Smart AI Flux, or Offline Vector Art).
    - Dedicated Image Server Base URL (e.g. `https://api.avalai.ir/v1` or custom proxy).
    - Dedicated Image API key (or optionally inherits the global LLM key if identical).
    - Dedicated image model selection (e.g. `dall-e-3`, `flux-1.1-pro`, `imagen-3.0-generate-002`).
    - Quick 1-click gateway presets (AvalAI, OpenAI, OpenRouter Flux, Local SD / WebUI).
    - Dedicated live Image API connectivity test tool with latency and response diagnostics.

| Engine | Supported Models / Providers | Configuration |
| :--- | :--- | :--- |
| **Story LLM (Narrative)** | Custom API (AvalAI, Groq, DeepSeek, vLLM, LM Studio), Gemini, OpenAI, OpenRouter, Ollama | Set `Base URL`, `API Key`, and `Model Name` |
| **Chapter Illustration (Image)** | Custom Image API (AvalAI, OpenRouter, Local SD), OpenAI (`dall-e-3`), Gemini (`imagen-3.0`), Smart AI (Flux) | Set dedicated `Image Base URL`, `Image API Key`, and `Image Model` |

---

## 🎭 Novel Studio Features

- **1-Click Literary Presets**: Instantly seed your novel with genre-defining concepts (Gothic Victorian, Parisian Romance, Cyberpunk Noir).
- **AI Magic Co-pilot**: Type a one-line idea or title, and the AI will auto-populate genre, tone, era, city, and premise in seconds.
- **Behind the Scenes Drawer**: In the reading view, click **"🎭 Behind the Scenes"** to slide open the actor simulation drawer and inspect characters' secret thoughts, raw body language, and dramatic turns behind every paragraph.
- **Kindle-Style Reader**: Customize your reading experience with Day, Sepia, and Night color palettes, adjustable typography, and one-click copy / markdown export.
- **Full Continuity & State Recovery**: Novels and generated episodes are stored automatically as JSON blueprints and memory banks under `data/novels/`.

---

## 📁 Repository Structure

```
storyteller/
├── app/
│   ├── config.py                 # Application settings and default LLM configuration
│   ├── main.py                   # FastAPI server entry point and static routing
│   ├── models/                   # Pydantic data schemas
│   │   ├── enums.py              # Genre, ProseStyle, Theme, Tone, Temperament enums
│   │   ├── character.py          # Character persona, motivations, arcs, and relationships
│   │   ├── blueprint.py          # Master novel blueprint, world locations, and cast settings
│   │   ├── simulation.py         # Actor turns, scene records, and story memory models
│   │   └── episode.py            # Episode models and pipeline progress trackers
│   ├── engine/                   # The 6-stage literary production line
│   │   ├── llm_client.py         # Multi-provider client (Custom, Gemini, OpenAI, Ollama, Mock)
│   │   ├── prompts.py            # Systematic literary prompts for all 6 stages
│   │   ├── stage1_world_cast.py  # Stage 1: World and character generation
│   │   ├── stage2_matrix.py      # Stage 2: Story matrix and chapter arcs
│   │   ├── stage3_director.py    # Stage 3: Scene directorship and POV planning
│   │   ├── stage4_character_sim.py# Stage 4: Multi-agent turn-by-turn roleplay simulation
│   │   ├── stage5_narrator.py    # Stage 5: Literary prose synthesis
│   │   ├── stage6_memory.py      # Stage 6: Running memory and open plot thread tracking
│   │   └── pipeline.py           # Background pipeline coordinator
│   ├── storage/
│   │   └── store.py              # Disk persistence for blueprints, episodes, and settings
│   ├── api/
│   │   ├── novels.py             # Novel CRUD, generation triggers, and preset endpoints
│   │   └── system.py             # System diagnostics and connection test endpoints
│   └── static/                   # Studio frontend
│       ├── index.html            # Studio SPA layout (Wizard, Library, Reader, Settings)
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
