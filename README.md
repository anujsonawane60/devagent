# DevAgent — Personal Multi-Agent AI Assistant

A multi-agent AI system where **Jarvis** (supervisor) manages 8 specialized agents that handle your tasks, contacts, notes, thoughts, secrets, memory, scheduling, and web research — all through a single Telegram chat.

```
You ── Telegram ── Jarvis (supervisor)
                      ├── Task Agent         (to-dos, reminders)
                      ├── Research Agent     (web search, time)
                      ├── Notes Agent        (structured notes)
                      ├── Contacts Agent     (people, encrypted)
                      ├── Thoughts Agent     (quick brain dumps)
                      ├── Vault Agent        (passwords, encrypted)
                      ├── Memory Agent       (learns about you)
                      └── Scheduler Agent    (future actions)
```

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- Telegram Bot Token ([create via @BotFather](https://t.me/BotFather))

### 1. Clone the repo

```bash
git clone https://github.com/anujsonawane60/devagent.git
cd devagent
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set the **required** values:

```env
OPENAI_API_KEY=sk-your-openai-api-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

Generate an encryption key (important — save this!):

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste the output into `.env`:

```env
ENCRYPTION_KEY=your-generated-key-here
```

### 5. Run

```bash
python -m jarvis.main
```

You should see:

```
INFO - Initializing database...
INFO - Database migrated to v2.
INFO - Building supervisor and sub-agents...
INFO - Registered agent: task_agent
INFO - Registered agent: research_agent
INFO - Registered agent: notes_agent
INFO - Registered agent: contacts_agent
INFO - Registered agent: thoughts_agent
INFO - Registered agent: vault_agent
INFO - Registered agent: memory_agent
INFO - Registered agent: scheduler_agent
INFO - Supervisor built with 8 sub-agents
INFO - Starting in polling mode (local dev)...
INFO - JARVIS is online!
```

Open your Telegram bot and start chatting.

---

## Configuration Reference

All config is in `.env`. Here's every option:

### Required

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from @BotFather |

### Recommended

| Variable | Default | Description |
|----------|---------|-------------|
| `ENCRYPTION_KEY` | auto-generated | AES-256 key for encrypting contacts, vault. **Save this — losing it means losing encrypted data.** |

### LLM Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_LLM_PROVIDER` | `openai` | LLM provider: `openai`, `anthropic`, or `google` |
| `DEFAULT_LLM_MODEL` | `gpt-4o` | Model name |
| `DEFAULT_LLM_TEMPERATURE` | `0.7` | Response creativity (0.0-1.0) |
| `ANTHROPIC_API_KEY` | | Required if using Anthropic |
| `GOOGLE_API_KEY` | | Required if using Google/Gemini |
| `AGENT_LLM_OVERRIDES` | `{}` | Per-agent model config (JSON). Example below. |

**Per-agent LLM overrides** — use different models for different agents:

```env
AGENT_LLM_OVERRIDES={"research_agent": {"provider": "anthropic", "model": "claude-sonnet-4-20250514"}, "task_agent": {"provider": "openai", "model": "gpt-4o-mini"}}
```

### Vector Search (Semantic Memory)

| Variable | Default | Description |
|----------|---------|-------------|
| `VECTOR_DB_ENABLED` | `true` | Enable/disable semantic search. Set `false` to use keyword-only search. |
| `VECTOR_DB_PATH` | `data/vectors` | Where ChromaDB stores embeddings |
| `EMBEDDING_PROVIDER` | `openai` | `openai` (paid, best) or `ollama` (free, local) |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model. Use `nomic-embed-text` with Ollama. |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_ALLOWED_USERS` | `[]` | JSON list of allowed Telegram user IDs. Empty = allow everyone (dev mode). |

To find your Telegram user ID, message [@userinfobot](https://t.me/userinfobot).

```env
TELEGRAM_ALLOWED_USERS=["123456789", "987654321"]
```

### Database & Deployment

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `data/jarvis.db` | SQLite database path |
| `MEMORY_WINDOW` | `20` | Number of recent messages loaded as context |
| `WEBHOOK_URL` | | Leave empty for polling (local dev). Set for webhook (production). |
| `LOG_LEVEL` | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |

---

## What You Can Do

Talk to Jarvis naturally. Here are some examples:

### Tasks
```
"Add a task: buy groceries"
"Remind me to call mom tomorrow"
"Create a high priority work task: finish report by Friday"
"Show my tasks"
"Mark task #3 as done"
```

### Notes
```
"Save a note about today's meeting"
"Find my notes about Python"
"Show all my notes"
```

### Thoughts (quick brain dumps)
```
"Save this: I think React is better than Angular"
"Idea: build a habit tracker app"
"Pizza place on MG Road was amazing"
"Show my ideas"
"Search my thoughts about food"
```

### Contacts
```
"Satyajit's number is 9876543210"
"Save my friend Raj's email: raj@gmail.com"
"What's Satyajit's phone number?"
"Show all my contacts"
```

### Vault (passwords & secrets)
```
"My Netflix password is xyz123"
"What's my WiFi password?"
"Show my saved passwords"
```

### Memory (Jarvis learns about you)
```
"I prefer Python over Java"
"My mom's name is Sunita"
"What do you know about me?"
"Forget that I like Java"
```

### Scheduler
```
"Send birthday wishes to Satyajit at 12 AM tomorrow"
"Remind me to take medicine every day at 8 AM"
"Show my upcoming schedules"
"Cancel schedule #5"
```

### Research
```
"Search for latest AI news"
"What time is it in Tokyo?"
"Who is the president of France?"
```

---

## Project Structure

```
jarvis/
├── main.py                        Entry point
├── config.py                      All settings (from .env)
│
├── core/                          Foundation
│   ├── context.py                 UserContext (identity that flows everywhere)
│   ├── llm_factory.py             Multi-provider LLM creation
│   └── base_agent.py              AgentDefinition blueprint
│
├── agents/                        All 8 agents + supervisor
│   ├── supervisor.py              Jarvis orchestrator
│   ├── registry.py                Auto-discovers agents
│   ├── task_agent.py              Tasks & reminders
│   ├── research_agent.py          Web search & time
│   ├── notes_agent.py             Structured notes
│   ├── contacts_agent.py          People (encrypted)
│   ├── thoughts_agent.py          Quick brain dumps
│   ├── vault_agent.py             Secrets (encrypted)
│   ├── memory_agent.py            Long-term memory
│   └── scheduler_agent.py         Future actions
│
├── tools/                         30 tools across 9 modules
│   ├── task_tools.py              create, list, complete, delete
│   ├── search_tools.py            web_search
│   ├── datetime_tools.py          get_current_time
│   ├── note_tools.py              save, search, list, delete
│   ├── contact_tools.py           save, find, update, list, delete
│   ├── thought_tools.py           save, search, list, pin, delete
│   ├── vault_tools.py             store, get, list, delete
│   ├── memory_tools.py            learn, recall, forget
│   └── scheduler_tools.py         schedule, list, cancel
│
├── db/                            Storage layer
│   ├── database.py                Singleton SQLite connection
│   ├── models.py                  12 data model definitions
│   ├── migrations.py              Versioned schema (v1 → v2)
│   ├── repositories.py            CRUD for all models
│   ├── encryption.py              AES-256 (Fernet) for sensitive data
│   ├── embeddings.py              Text-to-vector (OpenAI/Ollama)
│   └── vector_store.py            ChromaDB semantic search
│
├── interfaces/                    Platform adapters
│   ├── base.py                    InterfaceAdapter ABC
│   └── telegram.py                Telegram bot adapter
│
└── auth/
    └── authenticator.py           User allowlist
```

---

## Security

- **Encryption at rest**: Phone numbers, emails, addresses, vault secrets are encrypted with AES-256 (Fernet) before writing to SQLite. The key lives in `.env`, never in the database.
- **LLM data minimization**: Encrypted values are handled by tools directly — the LLM sees "Saved contact info" not "Saved 9876543210".
- **Per-user isolation**: Every DB query is scoped by `user_id`. User A cannot access User B's data.
- **Telegram allowlist**: Set `TELEGRAM_ALLOWED_USERS` to restrict access to specific Telegram user IDs.
- **Private thoughts**: Thoughts marked `is_private=true` are encrypted in the database.
- **Conversation redaction**: Sensitive data in chat history can be flagged as redacted.

---

## Adding a New Agent

1. Create `jarvis/tools/my_tools.py` with `@tool` functions
2. Create `jarvis/agents/my_agent.py` with `get_agent_definition()`
3. Add `"jarvis.agents.my_agent"` to `AGENT_MODULES` in `jarvis/agents/registry.py`
4. Restart — supervisor auto-discovers it

See [Agents.md](Agents.md) for the full agent reference.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent framework | LangGraph + langgraph-supervisor |
| LLM providers | OpenAI, Anthropic (Claude), Google (Gemini) |
| Tool framework | LangChain `@tool` decorator |
| Database | SQLite (aiosqlite) |
| Vector search | ChromaDB + OpenAI embeddings |
| Encryption | cryptography (Fernet/AES-256) |
| Bot interface | python-telegram-bot |
| Web search | DuckDuckGo (duckduckgo-search) |
| Config | Pydantic Settings + .env |

---

## Docs

- [Plan.md](Plan.md) — Architecture plan and implementation phases
- [Agents.md](Agents.md) — Full agent reference with all tools and examples
- [Changes.md](Changes.md) — Changelog
