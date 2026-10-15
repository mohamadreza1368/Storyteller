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

---

## ⚙️ AI Models & Custom API Integration

The studio features an **Offline Creative Simulator** by default, allowing you to test, experiment, and generate stories instantly without internet or API keys.

To connect external LLM providers, click **"⚙️ Model Settings"** in the top navigation bar:

| Provider | Supported Models / Notes | Configuration |
| :--- | :--- | :--- |
| **Custom API (OpenAI-compatible)** | Any proxy, AvalAI, Groq, DeepSeek, vLLM, LM Studio, etc. | Set `Base URL`, `API Key`, and `Model Name` |
| **Google Gemini** | `gemini-2.5-flash`, `gemini-1.5-pro` | Official `google-genai` SDK |
| **OpenAI** | `gpt-4o`, `gpt-4o-mini`, `o3-mini` | Direct OpenAI API |
| **OpenRouter** | `anthropic/claude-3.5-sonnet`, `deepseek/deepseek-r1`, etc. | Routes via `https://openrouter.ai/api/v1` |
| **Ollama (Local)** | `llama3`, `qwen2.5`, `mistral` | Local endpoint: `http://localhost:11434/v1` |
| **Mock Simulator** | High-fidelity offline literary simulator | Zero setup required |

> **Live Test Connection**: The settings modal includes a "Test Connection" button with real-time latency measurement and diagnostic feedback.

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
