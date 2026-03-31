# Changelog

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
