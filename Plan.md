# DevAgent — Multi-Agent Architecture Plan

## Vision

Build a personal multi-agent AI system where **Jarvis** (name may change) acts as a manager/orchestrator. The user talks only to Jarvis — Jarvis understands intent, delegates tasks to specialized sub-agents, and returns results seamlessly. The user never interacts with sub-agents directly.

Think of it like a company: Jarvis is the CEO who talks to you, and behind the scenes there are specialists (task manager, researcher, note-taker, coder, scheduler...) doing the actual work.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Telegram / CLI)                 │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│              INTERFACE LAYER (Adapters)                  │
│  telegram.py  │  cli.py (future)  │  discord.py (future)│
│  - Extract UserContext from platform                    │
│  - Auth check (allowlist)                               │
│  - Invoke supervisor graph with config                  │
└──────────────────────────┬──────────────────────────────┘
                           │  UserContext + messages
┌──────────────────────────▼──────────────────────────────┐
│               SUPERVISOR (Jarvis)                       │
│  - Understands user intent                              │
│  - Routes to sub-agents via handoff tools               │
│  - Responds directly for simple queries                 │
│  - Aggregates multi-agent results                       │
│  Built with: langgraph-supervisor                       │
└────┬──────────────┬──────────────┬──────────────────────┘
     │              │              │
┌────▼────┐  ┌──────▼─────┐  ┌────▼──────┐  ┌───────────┐
│ Task    │  │ Research   │  │ Notes    │  │ Future    │
│ Agent   │  │ Agent      │  │ Agent    │  │ Agents... │
│         │  │            │  │          │  │           │
│ Tools:  │  │ Tools:     │  │ Tools:   │  │ Coder,    │
│ create  │  │ web_search │  │ save     │  │ Scheduler │
│ list    │  │ get_time   │  │ search   │  │ Email,    │
│ complete│  │            │  │ list     │  │ etc.      │
└────┬────┘  └──────┬─────┘  └────┬─────┘  └───────────┘
     │              │              │
┌────▼──────────────▼──────────────▼──────────────────────┐
│                    CORE LAYER                           │
│  UserContext  │  LLM Factory  │  DB Pool  │  Agent Reg  │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    STORAGE (SQLite → Postgres later)     │
│  users │ conversations │ tasks │ notes │ agent_logs     │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
jarvis/
├── main.py                       # Entry point
├── config.py                     # Settings (multi-LLM, auth, DB, etc.)
│
├── core/                         # Foundation layer
│   ├── context.py                # UserContext — identity that flows everywhere
│   ├── llm_factory.py            # Multi-provider LLM creation (OpenAI/Anthropic/Google)
│   └── base_agent.py             # AgentDefinition — blueprint for sub-agents
│
├── agents/                       # All agents live here
│   ├── registry.py               # AgentRegistry — auto-discovers sub-agents
│   ├── supervisor.py             # Jarvis orchestrator graph
│   ├── task_agent.py             # Task management specialist
│   ├── research_agent.py         # Web search/research specialist
│   ├── notes_agent.py            # Notes/knowledge specialist
│   └── (future agents...)        # coder_agent.py, scheduler_agent.py, etc.
│
├── tools/                        # Tools grouped by domain
│   ├── __init__.py               # get_user_context() helper
│   ├── task_tools.py             # create_task, list_tasks, complete_task
│   ├── search_tools.py           # web_search
│   ├── note_tools.py             # save_note, search_notes, list_notes
│   └── datetime_tools.py         # get_current_time
│
├── db/                           # Storage layer
│   ├── database.py               # Singleton async DB connection
│   ├── migrations.py             # Schema versioning & migrations
│   └── repositories.py           # TaskRepo, NoteRepo, ConversationRepo, UserRepo
│
├── interfaces/                   # Platform adapters (decoupled from agents)
│   ├── base.py                   # InterfaceAdapter ABC
│   ├── telegram.py               # Telegram adapter
│   └── (future...)               # cli.py, discord.py, web.py
│
└── auth/
    └── authenticator.py          # User allowlist per platform
```

---

## Key Design Decisions

### 1. Supervisor Pattern — How Jarvis Delegates

Jarvis is built with `langgraph-supervisor`. It gets **handoff tools** auto-generated for each sub-agent (e.g., `transfer_to_task_agent`, `transfer_to_research_agent`). The supervisor LLM reads the user's message, decides which agent should handle it, and calls the appropriate handoff tool.

- "Add a task to buy groceries" → `transfer_to_task_agent` → TaskAgent creates the task → response flows back
- "What's happening in tech?" → `transfer_to_research_agent` → ResearchAgent searches the web → response flows back
- "Hello!" → Jarvis responds directly, no delegation

### 2. UserContext — Per-User Data Isolation

Every request carries a `UserContext` (user_id, chat_id, platform, username). Interface adapters create it from platform data. It flows through the supervisor → sub-agents → tools via LangGraph's `RunnableConfig`. Tools extract it to scope DB queries to the correct user. No more shared global data.

### 3. Agent Registry — Adding Agents is Trivial

Each agent module exports `get_agent_definition() -> AgentDefinition`. The registry auto-discovers them on startup. To add a new agent:
1. Create `jarvis/agents/new_agent.py`
2. Define tools, prompt, and `get_agent_definition()`
3. Add module path to `AGENT_MODULES` list in registry.py
4. Done. Supervisor automatically gets a handoff tool for the new agent.

### 4. Multi-LLM — Different Models Per Agent

`LLMFactory` supports OpenAI, Anthropic, and Google. Config allows per-agent overrides:
- Supervisor: GPT-4o-mini (cheap, fast routing)
- Research: Claude (good at synthesis)
- Tasks: GPT-4o (reliable tool calling)

### 5. Interface Decoupling — One Agent System, Many Frontends

Interface adapters translate platform events → graph invocations → platform responses. The agent system never knows which platform it's running on. Adding a new frontend (CLI, Discord, web API) = one new adapter file.

---

## Database Schema

```sql
users           (id, platform, username, display_name, is_authorized, created_at, last_seen)
conversations   (id, user_id, chat_id, role, content, created_at)
tasks           (id, user_id, title, due_date, status, created_at, completed_at)
notes           (id, user_id, title, content, created_at, updated_at)
agent_logs      (id, user_id, agent_name, input_summary, output_summary, tools_used, duration_ms, created_at)
```

All tables use `user_id` for data isolation. Schema is versioned via `migrations.py`.

---

## Implementation Phases

### Phase 1: Foundation Refactor ✅ DONE
**Goal**: Fix all bugs, build clean internals.

- [x] `core/context.py` — UserContext dataclass
- [x] `core/llm_factory.py` — Multi-provider LLM factory
- [x] `db/database.py` — Singleton DB pool
- [x] `db/migrations.py` — Schema versioning with user_id columns
- [x] `db/repositories.py` — TaskRepo, NoteRepo, ConversationRepo, UserRepo
- [x] Refactored all tools with `RunnableConfig` for user context
- [x] `config.py` — Multi-LLM settings, auth settings
- [x] `interfaces/telegram.py` — Decoupled adapter with auth
- [x] `auth/authenticator.py` — Telegram user allowlist

### Phase 2: Supervisor + Sub-Agents ✅ DONE
**Goal**: Multi-agent routing with supervisor pattern.

- [x] `core/base_agent.py` — AgentDefinition
- [x] `agents/registry.py` — AgentRegistry with auto-discover
- [x] `agents/task_agent.py` — Task management sub-agent
- [x] `agents/research_agent.py` — Web search sub-agent
- [x] `agents/notes_agent.py` — Notes management sub-agent
- [x] `agents/supervisor.py` — Jarvis orchestrator graph
- [x] Wired supervisor into main.py and Telegram adapter

**Verified**: Supervisor compiles with nodes: `jarvis`, `task_agent`, `research_agent`, `notes_agent`

### Phase 3: LangGraph Checkpointing ⬜ TODO
**Goal**: Replace manual conversation history with LangGraph's built-in persistence.

- [ ] Add `langgraph-checkpoint-sqlite` dependency
- [ ] Configure checkpointer on supervisor graph (thread_id = chat_id)
- [ ] Remove manual save_message/get_history — LangGraph handles it
- [ ] Keep conversations table for audit/export only

**Why**: Eliminates manual history management, enables conversation resumption after restart.

### Phase 4: Multi-LLM Per Agent + CLI ⬜ TODO
**Goal**: Different LLM models per agent, second interface.

- [ ] Wire `AGENT_LLM_OVERRIDES` config into agent builds
- [ ] Test: supervisor on GPT-4o-mini, research on Claude
- [ ] Create `jarvis/interfaces/cli.py` for terminal testing without Telegram
- [ ] Add fallback logic if a provider fails

**Why**: Cost optimization (cheap routing, expensive reasoning) and provider redundancy.

### Phase 5: CoderAgent ⬜ TODO
**Goal**: Agent that can generate, explain, and debug code.

- [ ] Create `jarvis/agents/coder_agent.py`
- [ ] Tools: `generate_code`, `explain_code`, `run_python` (sandboxed)
- [ ] Register in agent registry
- [ ] Test: "write a Python function to sort a list" → routes to CoderAgent

**Why**: Core capability for a dev-focused AI assistant.

### Phase 6: SchedulerAgent ⬜ TODO
**Goal**: Agent that manages calendar, scheduling, and time-based reminders.

- [ ] Create `jarvis/agents/scheduler_agent.py`
- [ ] Tools: Google Calendar integration, recurring reminders, timezone-aware scheduling
- [ ] DB: Add `schedules` table for recurring events
- [ ] Background job runner for time-triggered reminders

**Why**: Personal assistant needs proactive scheduling, not just reactive responses.

### Phase 7: EmailAgent ⬜ TODO
**Goal**: Agent that can read, draft, and send emails.

- [ ] Create `jarvis/agents/email_agent.py`
- [ ] Tools: Gmail API integration (read inbox, draft, send)
- [ ] Auth: OAuth2 flow for Gmail
- [ ] Safety: Always confirm before sending

**Why**: Email is a high-value automation target for a personal assistant.

### Phase 8: Advanced Memory ⬜ TODO
**Goal**: Long-term memory beyond conversation history.

- [ ] Vector store for semantic memory (ChromaDB or similar)
- [ ] User preference learning (tone, common tasks, shortcuts)
- [ ] Cross-conversation context ("last time you asked about X...")
- [ ] Memory agent or memory layer accessible to all agents

**Why**: Makes the assistant genuinely personal — it remembers and learns.

### Phase 9: Web Dashboard ⬜ TODO
**Goal**: Web UI for managing agents, viewing logs, and configuration.

- [ ] FastAPI backend serving the supervisor graph
- [ ] React/Next.js frontend
- [ ] Real-time chat interface
- [ ] Agent activity dashboard (logs, performance, routing decisions)
- [ ] Settings page for LLM config, agent toggles, user management

**Why**: Better UX than Telegram for power users and administration.

### Phase 10: Deployment & Scaling ⬜ TODO
**Goal**: Production-ready deployment.

- [ ] Docker containerization
- [ ] PostgreSQL migration (replace SQLite)
- [ ] Redis for caching and rate limiting
- [ ] CI/CD pipeline
- [ ] Monitoring and alerting (Grafana/Prometheus)
- [ ] Multi-user support with proper auth (JWT, OAuth)

**Why**: Move from personal dev tool to reliable service.

---

## How to Add a New Agent (Recipe)

```
1. Create jarvis/agents/my_agent.py
2. Define tools in jarvis/tools/my_tools.py
3. Implement get_agent_definition() returning AgentDefinition(
       name="my_agent",
       description="What this agent does (used by supervisor for routing)",
       system_prompt="Agent personality and instructions",
       tools=[tool1, tool2, ...],
   )
4. Add "jarvis.agents.my_agent" to AGENT_MODULES in registry.py
5. Restart — supervisor auto-discovers and routes to the new agent
```

No changes to supervisor code. No changes to interface layer. Just the agent file and its tools.

---

## Tech Stack

| Layer          | Technology                                      |
|----------------|------------------------------------------------|
| Agent Framework| LangGraph + langgraph-supervisor               |
| LLM Providers  | OpenAI, Anthropic (Claude), Google (Gemini)    |
| Tool Framework | LangChain @tool decorator                      |
| Database       | SQLite (aiosqlite) → PostgreSQL later          |
| Bot Interface  | python-telegram-bot                            |
| Web Search     | DuckDuckGo (duckduckgo-search)                 |
| Config         | Pydantic Settings + .env                       |
| Auth           | Allowlist (now) → OAuth/JWT (later)            |

---

## Dependencies

```
# Core
langchain>=0.3.0
langchain-openai>=0.3.0
langgraph>=0.2.0
langgraph-supervisor>=0.0.30

# Multi-LLM
langchain-anthropic>=0.3.0
# langchain-google-genai>=2.0       # Uncomment for Gemini

# Interfaces
python-telegram-bot>=21.0

# Storage
aiosqlite>=0.20.0
# langgraph-checkpoint-sqlite       # Phase 3

# Config
pydantic-settings>=2.0
python-dotenv>=1.0

# Tools
duckduckgo-search>=7.0
```
