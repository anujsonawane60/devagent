# Changelog

## 2026-04-01 — Full Data Layer + Vector Search + 6 Integration Agents

### Complete Data Storage (models.py)
- 12 data models covering the user's full digital life: User, Contact, Task, Note, Thought, Tag, Taggable, VaultEntry, Memory, ScheduledJob, Conversation, AgentLog
- **Thoughts** — zero-friction brain dump system with auto-classification (idea/opinion/fact/random/bookmark/quote/snippet/question)
- **Vault** — AES-256 encrypted secret storage (passwords, PINs, API keys). LLM never sees raw values.
- **Contacts** — phone/email/address encrypted at rest
- **Memories** — Jarvis learns facts about the user with confidence scoring
- **Scheduled Jobs** — future actions with recurrence rules
- **Tags** — universal tagging system (tag any entity type)
- Schema versioned (v1 → v2) with automatic migrations

### AES-256 Encryption (`encryption.py`)
- Fernet encryption for sensitive fields (phone, email, vault values, private thoughts)
- Key stored in `.env`, never in DB. Auto-generates on first run with warning to save it.

### Vector Search / Semantic Memory (`vector_store.py` + `embeddings.py`)
- ChromaDB for semantic search — finds content by **meaning**, not just keywords
- OpenAI `text-embedding-3-small` for embeddings
- Indexed on save: thoughts, notes, memories, contacts
- `smart_search()` / `smart_recall()` — SQL first, vector fallback
- Per-user collections for data isolation
- Toggle with `VECTOR_DB_ENABLED=false` for keyword-only mode

### 5 New Core Agents (8 → 13 total, 30 → 50 tools)
- **contacts_agent** (5 tools) — save, find, update, list, delete contacts (encrypted)
- **thoughts_agent** (5 tools) — save, search (semantic), list, pin, delete thoughts
- **vault_agent** (4 tools) — store, get, list, delete secrets (encrypted)
- **memory_agent** (3 tools) — learn, recall (semantic), forget
- **scheduler_agent** (3 tools) — schedule, list, cancel future actions

### Background Scheduler Runner
- `jarvis/scheduler/runner.py` — polls `scheduled_jobs` every 30s, executes due jobs
- Sends Telegram messages when reminders/scheduled messages are due
- Handles recurring jobs (daily, weekly, monthly, yearly)

### 6 Integration Agents (13 → 14 total... wait, 14)
- **email_agent** (3 tools) — Gmail: read inbox, send email, search mail
- **calendar_agent** (3 tools) — Google Calendar: list events, create event, check availability
- **github_agent** (4 tools) — GitHub: repos, PRs, issues
- **messaging_agent** (2 tools) — SMS + WhatsApp via Twilio
- **notion_agent** (3 tools) — Notion: search, create pages, list databases
- **spotify_agent** (5 tools) — Spotify: now playing, search, play, pause, skip

### Credential System (`core/credentials.py`)
- Graceful "not configured" messages — shown only when user tries to use the feature
- Step-by-step setup instructions per service (Gmail, GitHub, Twilio, Notion, Spotify)
- No crashes, no silent failures

### Voice Note Support
- Telegram voice messages transcribed via OpenAI Whisper API ($0.006/min)
- Transcribed text processed as normal message — voice and text are equivalent

### OAuth Helpers
- `jarvis/auth/google_auth.py` — one-time Google OAuth for Gmail + Calendar
- `jarvis/auth/spotify_auth.py` — one-time Spotify OAuth

### Upgraded Existing Tools
- task_tools: added priority, category, due_time, delete_task
- note_tools: added category, pinning, smart_search (semantic), delete_note

### Dependencies Added
- `chromadb`, `langchain-chroma` — vector search
- `cryptography` — AES-256 encryption
- `google-api-python-client`, `google-auth-oauthlib` — Gmail + Calendar
- `PyGithub` — GitHub
- `twilio` — SMS + WhatsApp
- `notion-client` — Notion
- `spotipy` — Spotify

### Final Count
- **14 agents**, **50 tools**
- **12 data models**, **10 repository classes**
- **SQLite** (structured) + **ChromaDB** (semantic) dual storage

---

## 2026-03-31 — Multi-Agent Architecture (Phase 1 + 2)

Rebuilt the entire system as a multi-agent architecture with Jarvis as supervisor/orchestrator.

### Architecture
- **Supervisor pattern**: Jarvis routes user requests to specialized sub-agents (task_agent, research_agent, notes_agent) via `langgraph-supervisor`
- **Agent registry**: Auto-discovers and registers sub-agents. Adding a new agent = one file.
- **Interface layer**: Decoupled from agent layer. Telegram adapter now, CLI/Discord/web later.
- **Multi-LLM factory**: Supports OpenAI, Anthropic, Google. Per-agent LLM overrides via config.
- **UserContext flow**: Every tool receives user identity via LangGraph's RunnableConfig — proper per-user data isolation.

### Bug Fixes
- Fixed: tasks/notes hardcoded to `chat_id='global'` — now uses actual user_id
- Fixed: DB connection opened/closed per call — now singleton pool
- Fixed: No authentication — added Telegram user allowlist
- Fixed: Agent recreated every message — now singleton supervisor graph

### New Files
- `jarvis/core/` — context.py, llm_factory.py, base_agent.py
- `jarvis/agents/` — registry.py, supervisor.py, task_agent.py, research_agent.py, notes_agent.py
- `jarvis/interfaces/` — base.py, telegram.py (decoupled adapter)
- `jarvis/auth/` — authenticator.py
- `jarvis/db/migrations.py`, `jarvis/db/repositories.py`

### Dependencies Added
- `langgraph-supervisor` — supervisor/orchestrator pattern
- `langchain-anthropic` — Claude support

---

## 2026-03-30 14:30 — Build JARVIS personal AI agent from scratch (Phase 1)

Replaced entire codebase with JARVIS — a LangGraph-powered personal AI agent with Telegram interface, OpenAI GPT-4o brain, SQLite storage, and extensible tool system (tasks, web search, notes, datetime).
