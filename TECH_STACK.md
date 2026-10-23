# Storyteller AI — Technical Stack & System Architecture Specifications

> **System Overview:** Storyteller AI is an autonomous multi-agent novel writing studio that simulates independent character intelligences, stages cinematic scenes with physical blocking, and synthesizes publication-grade literary prose adhering to anti-AI humanizer standards.

---

## 1. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------+
|                                CLIENT LAYER                                 |
|  Vanilla ES6+ SPA · Responsive CSS3 Design System · Web Speech API Audio    |
|  Hash Router (#library, #wizard, #novel, #reader, #guide, #admin)           |
+-------------------------------------+---------------------------------------+
                                      | HTTP REST / JSON
                                      v
+-----------------------------------------------------------------------------+
|                             API & ROUTING LAYER                             |
|  FastAPI (Python 3.10+) · ASGI Uvicorn · CORS Middleware · Dependency Inj.  |
|  Routers: /api/auth · /api/novels · /api/system · /api/admin                |
+-------------------------------------+---------------------------------------+
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
+----------------------------------+     +------------------------------------+
|     AUTONOMOUS STORY ENGINE      |     |      SECURE PERSISTENCE LAYER      |
|                                  |     |                                    |
| 1. Stage 1: World & Cast Anchor  |     |  SQLite 3 (WAL mode, Foreign Keys) |
| 2. Stage 2: Matrix & Pacing Grid |     |  PBKDF2-HMAC-SHA256 Password Hash  |
| 3. Stage 3: Scene Director       |     |  Cryptographic Bearer Auth Tokens  |
| 4. Stage 4: Multi-Agent Sim      |     |  Row-Level Ownership Isolation     |
| 5. Stage 5: Master Narrator      |     |  Parameterized SQL Security        |
| 6. Stage 6: Episodic Memory      |     +------------------------------------+
+-----------------+----------------+
                  |
                  v
+-----------------------------------------------------------------------------+
|                         ANTI-AI QUALITY GATE & CRAFT                        |
|  Integrated Skills: book-writer-skill · humanizer · avoid-ai-writing        |
|  - Banned Cliché Purge (delve, tapestry, beacon, testament, etc.)           |
|  - Structural Pattern Removal ("Not X, but Y", trailing one-liners, triads) |
|  - Punctuation & Sensory Rhythm Discipline (Show, Don't Tell)               |
+-----------------+-----------------------------------------------------------+
                  |
                  v
+-----------------------------------------------------------------------------+
|                           AI & MODEL PROVIDERS                              |
|  - LLM: Google Gemini (2.5 Flash/Pro), OpenAI (GPT-4o), Anthropic Claude,   |
|         OpenRouter, Local LLMs (Ollama / LM Studio)                         |
|  - Image Generation: Imagen 3, Recraft.ai, Pollinations fallback            |
+-----------------------------------------------------------------------------+
```

---

## 2. Core Technology Stack

### 2.1 Backend & Application Runtime
- **Runtime Environment:** Python 3.10+ / Python 3.14 compatible.
- **Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (v0.110.0+)
  - Asynchronous request handling with `asyncio`.
  - Automatic OpenAPI / Swagger UI interactive documentation at `/docs`.
  - Dependency injection pattern for authentication and state guards (`app/api/deps.py`).
- **ASGI Web Server:** [Uvicorn](https://www.uvicorn.org/) (v0.28.0+) with hot-reload capability.
- **Data Validation & Schemas:** [Pydantic v2](https://docs.pydantic.dev/) (`BaseModel`, `Field`, strict typing).
- **HTTP Client:** `httpx` & `requests` with timeout management and retry handlers.

### 2.2 Persistence & Database Layer
- **Engine:** **SQLite 3** (`data/storyteller.db`)
- **Concurrency & Reliability:**
  - WAL (Write-Ahead Logging) mode enabled (`PRAGMA journal_mode = WAL;`) for concurrent read/write transactions.
  - Foreign key constraints enforced (`PRAGMA foreign_keys = ON;`).
  - Thread-safe connection pooling and context management.
- **Data Model Schema:**
  - `users`: User identity, password hashes, salts, role (`admin` vs `author`), created timestamps.
  - `auth_sessions`: Session tokens with expiration timestamps.
  - `novels`: Title, genre, era, location, word count, current status, user ownership foreign key.
  - `blueprints`: Narrative anchors, premise, perspective, theme, tone, serialized JSON metadata.
  - `characters`: Character rosters, wants, needs, flaws, secrets, avatar URLs, POV flags.
  - `episodes`: Chapter numbers, titles, narrative prose, word counts, scene director plans, audio synthesis.
  - `simulation_turns`: Detailed dialogue rounds, actions, and internal thoughts for every scene.
  - `story_matrices`: Chapter-by-character goal planning and tension curves.
  - `character_memories`: Episodic knowledge state, discovered secrets, and evolving relationships.
- **Security & Hardening:**
  - 100% Parameterized queries (`?` placeholders) — Zero raw string formatting or SQL injection vectors.
  - Passwords hashed using standard `PBKDF2-HMAC-SHA256` with 100,000 rounds and unique 16-byte random salts.
  - Cryptographically secure 256-bit session tokens (`secrets.token_urlsafe(32)`).
  - Row-level access control: Regular authors can only read/mutate their own novels; platform administrators have system-wide oversight.

### 2.3 Frontend & User Experience
- **Framework:** Vanilla JavaScript (Modern ES6+ Modules & Async/Await) — **0 heavy dependencies**, **0ms build step**.
- **Styling:** Custom CSS3 Design System using CSS custom properties (variables):
  - Dynamic Dark / Light theme toggle (`data-theme="dark"` / `data-theme="light"`).
  - Four customizable reading modes: *Classic Dark*, *Paper Sepia*, *Daylight White*, and *Midnight Blue*.
  - Fluid typography with Google Fonts (*Plus Jakarta Sans* for UI, *Lora* for literary reading).
- **Client Routing:** Hash-based SPA router (`#library`, `#wizard`, `#novel`, `#reader`, `#guide`, `#admin`) with fallback guards and browser history synchronization.
- **Audio & Accessibility:** Native Web Speech API integration (`speechSynthesis`) enabling instant audiobook narration with adjustable speed, pitch, and voice selection.

---

## 3. Autonomous Multi-Agent Engine Architecture

The generation engine runs through an autonomous **6-Stage Pipeline** (`app/engine/pipeline.py`):

| Stage | Module | Functionality & Constraints |
|---|---|---|
| **Stage 1** | `stage1_world_cast.py` | **World & Cast Anchor:** Locks down premise, historical year, geography, tone, and character dossier. Guarantees preservation of supporting characters. |
| **Stage 2** | `stage2_matrix.py` | **Narrative Matrix:** Builds a chapter-by-chapter goal matrix. Budgets total chapters (target: 3 to 5 chapters) and caps word counts (< 3,000 words per chapter). |
| **Stage 3** | `stage3_director.py` | **Scene Director:** Deconstructs each chapter into 2–3 cinematic scenes. Specifies physical setting, mood, weather, entrance/exit blocking, and dramatic conflict. |
| **Stage 4** | `stage4_character_sim.py` | **Multi-Agent Simulation (No Telepathy):** Each character runs on an isolated LLM instance. Agents respond strictly to audible words and visible body language. Generates physical actions, spoken lines, and private thoughts. |
| **Stage 5** | `stage5_narrator.py` | **Master Prose Synthesis:** Weaves the directorial blocking and dialogue turns into immersive third-person limited prose. |
| **Stage 6** | `stage6_memory.py` | **Episodic Memory Ledger:** Extracts relationship shifts, discoveries, injuries, and unresolved stakes into persistent memory for the next chapter. |

---

## 4. Integrated Writing Craft & Anti-AI Humanizer Engine

The studio embeds literary principles from three industry benchmarks:
- **`book-writer-skill`** (Pacing, scene framing, chapter arcs, third-person limited POV)
- **`humanizer`** (Authentic voice, cadence variation, emotional depth, eliminating machine tone)
- **`avoid-ai-writing`** (Lexical filters, pattern prohibitions, sentence rhythm diversity)

### Enforced Writing Quality Rules (`app/engine/writing_craft.py`):
1. **Forbidden Lexicon:**
   Filters out 100+ AI cliché terms and metaphors, including: `delve`, `tapestry`, `testament`, `beacon`, `palpable`, `labyrinthine`, `dance of shadows`, `whispers of`, `air was thick with`, `inexorably`, `crescendo`. Replaces them with concrete, sensory descriptions.
2. **Elimination of AI Structural Habits:**
   - Strict ban on the *"Not X, but Y"* formulation (e.g., *"It was not just cold, but freezing"*).
   - Strict ban on trailing dramatic one-liners (e.g., *"And nothing would ever be the same again."*).
   - Strict ban on artificial adjective triads (groups of three adjectives).
3. **Punctuation & Tone Discipline:**
   - Em dashes (`—`) strictly limited to a maximum of 1–2 per scene, used exclusively for genuine speech interruptions.
   - Semicolons minimized in narrative prose.
   - Thoughts woven directly into narrative prose without decorative italics or quotes.
4. **Pacing & Word Limits:**
   - Chapter word cap: Strictly below 3,000 words (optimal target: 1,500–2,500 words) to prevent filler drift.

---

## 5. External Integrations & Model Ecosystem

| Capability | Supported Providers | Integration Details |
|---|---|---|
| **Text Generation (LLM)** | Google Gemini (2.5 Flash, 2.5 Pro, 1.5 Pro)<br>OpenAI (GPT-4o, GPT-4o-mini)<br>Anthropic (Claude 3.7 / 3.5 Sonnet)<br>OpenRouter / Ollama / LM Studio | Multi-provider abstraction (`app/engine/llm_client.py`). Unified prompt format, configurable temperature, structured JSON output, and mock fallback mode for offline testing. |
| **Cover Art & Scene Illustrations** | Google Imagen 3<br>Recraft.ai<br>HuggingFace / Pollinations AI | Visual prompt engineering (`app/engine/image_client.py`). Style presets (Victorian Gothic, Cyberpunk Neon, Autumn Impressionism, Graphic Novel). |
| **Audiobook Speech** | Web Speech API (Client-side)<br>FastAPI Audio Synthesis Ready | Dual architecture: immediate client-side zero-latency playback + server-side TTS streaming capability. |

---

## 6. Directory Structure & Key Files

```
storyteller/
├── app/
│   ├── api/                    # REST API endpoints & route handlers
│   │   ├── admin.py            # User management, KPI metrics, global AI config
│   │   ├── auth.py             # Login, register, profile, and session management
│   │   ├── deps.py             # Auth dependencies & role verification
│   │   ├── novels.py           # CRUD operations, chapter generation, export
│   │   └── system.py           # Health checks & platform diagnostics
│   ├── engine/                 # Autonomous multi-agent pipeline
│   │   ├── image_client.py     # Multi-provider image generation client
│   │   ├── llm_client.py       # Multi-provider LLM connector
│   │   ├── pipeline.py         # 6-Stage orchestrator
│   │   ├── prompts.py          # Isolated agent system & user prompts
│   │   ├── stage1_world_cast.py# World builder & character casting
│   │   ├── stage2_matrix.py    # Narrative matrix & chapter budget
│   │   ├── stage3_director.py  # Scene director & blocking
│   │   ├── stage4_character_sim.py # Multi-agent dialogue simulation
│   │   ├── stage5_narrator.py  # Master prose synthesizer
│   │   ├── stage6_memory.py    # Episodic continuity ledger
│   │   └── writing_craft.py    # Anti-AI humanizer quality gate & filter
│   ├── models/                 # Pydantic data schemas
│   │   ├── blueprint.py        # World & premise models
│   │   ├── character.py        # Character attributes, wants, secrets
│   │   ├── enums.py            # Genres, styles, tones, perspectives
│   │   ├── episode.py          # Chapter & novel schemas
│   │   └── simulation.py       # Turn, scene, and stage schemas
│   ├── static/                 # Frontend assets (Single Page Application)
│   │   ├── assets/             # Covers, avatars, and illustration library
│   │   ├── app.css             # Design system, themes, and responsive layouts
│   │   ├── app.js              # State manager, SPA router, and audio player
│   │   └── index.html          # Semantic HTML5 app container
│   ├── storage/                # Database & secure data persistence
│   │   ├── database.py         # SQLite schema definitions & connection pool
│   │   ├── store.py            # Novels & chapters data access object (DAO)
│   │   └── users.py            # User credentials, PBKDF2 hashing, and tokens
│   ├── config.py               # Pydantic settings & environment configuration
│   └── main.py                 # FastAPI application factory & static mounting
├── data/                       # Local SQLite database & novel file storage
├── requirements.txt            # Python dependencies
├── run.py                      # Application bootstrap & development server
└── TECH_STACK.md               # Technical specifications (this document)
```

---

## 7. Security & Compliance Measures

1. **Authentication & Session Management:**
   - Bearer token-based authorization.
   - Salted `PBKDF2-HMAC-SHA256` password hashing with random per-user salt.
   - Timing-safe comparisons where applicable.
2. **Access Control:**
   - Role-Based Access Control (RBAC): `Author` role strictly isolated to own projects; `Admin` role granted diagnostic and management capabilities.
3. **Data Protection:**
   - 100% Parameterized SQLite statements eliminating SQL injection vulnerabilities.
   - No sensitive API keys leaked to client; server-side proxying for all LLM and image calls.
4. **Codebase Quality & Documentation Integrity:**
   - Strict 100% English codebase standard (clean zero-tolerance policy against stray non-English characters in source files).
   - Fully typed Python codebase using Pydantic models and type hints throughout.
