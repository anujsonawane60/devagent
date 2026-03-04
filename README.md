# DevAgent

AI development agent that lives inside your codebase. Manage your entire development workflow from Telegram — build features, fix bugs, deploy, and monitor — all from your phone.

## What It Does

DevAgent is a one-time installation into any project (fresh or existing). Once added, it:

- **Understands your codebase** — tree-sitter AST parsing for Python, JavaScript, TypeScript, TSX. SQLite FTS5 for keyword search. ChromaDB for semantic code search.
- **Builds features** — Tell it what to build (`/add user dashboard`), it creates a feature branch, generates code using Claude Sonnet 4, validates (lint, typecheck, test, build), and commits only if everything passes.
- **Fixes bugs autonomously** — Integrated with Sentry for real-time error monitoring. Fetches stack traces, generates fixes via LLM, validates, and creates PRs.
- **Deploys from your phone** — `/deploy staging` or `/deploy production` via Vercel integration. Rollback with `/undo`.
- **Never breaks things** — Checkpoint system at every step. Refuses to work on main/master. Automatic rollback on validation failure.

## Quick Start

### 1. Install

```bash
git clone <your-repo-url>
cd devagent
pip install -e ".[dev]"
```

### 2. Configure

Create a `.env` file in the project root:

```env
# Required
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_ALLOWED_USERS=123456789,987654321
ANTHROPIC_API_KEY=your-anthropic-api-key

# LLM Provider (default: anthropic)
LLM_PROVIDER=anthropic
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Optional: OpenAI instead of Anthropic
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your-openai-key
# OPENAI_MODEL=gpt-4o

# Optional: GitHub (for PR creation)
GITHUB_TOKEN=your-github-token

# Optional: Sentry (for error monitoring)
SENTRY_AUTH_TOKEN=your-sentry-token
SENTRY_ORG=your-org-slug
SENTRY_PROJECT=your-project-slug

# Optional: Vercel (for deployments)
VERCEL_TOKEN=your-vercel-token
VERCEL_PROJECT_ID=prj_xxx
VERCEL_TEAM_ID=team_xxx

# Optional: Storage
DB_PATH=devagent.db
CHROMADB_PATH=devagent_chroma
DEBUG=false
```

**Getting the tokens:**

| Token | Where to get it |
|-------|----------------|
| `TELEGRAM_BOT_TOKEN` | Message [@BotFather](https://t.me/BotFather) on Telegram, create a new bot |
| `TELEGRAM_ALLOWED_USERS` | Your Telegram user ID (message [@userinfobot](https://t.me/userinfobot)) |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) |
| `GITHUB_TOKEN` | GitHub Settings > Developer settings > Personal access tokens |
| `SENTRY_AUTH_TOKEN` | Sentry Settings > API Keys > Auth Tokens |
| `VERCEL_TOKEN` | Vercel Settings > Tokens |

### 3. Run

```bash
devagent
```

Or directly:

```bash
python -m agent.core
```

### 4. Initialize Your Project

Open Telegram, find your bot, and run:

```
/setup /path/to/your/project
```

This analyzes the project, indexes the codebase, detects validation checks, and reports git status.

## Commands

### Core

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/status` | Show bot status and active integrations |
| `/setup <path>` | Initialize DevAgent for a project |

### Code Understanding

| Command | Description |
|---------|-------------|
| `/analyze <path>` | Detect language, framework, dependencies |
| `/index <path>` | Index codebase for search (tree-sitter + FTS5) |
| `/search <query>` | Full-text search across indexed code |
| `/find <name>` | Find a function/class definition by exact name |

### Code Generation

| Command | Description |
|---------|-------------|
| `/generate <task>` | Generate code changes using LLM |
| `/add <feature>` | Full workflow: branch, generate, validate, commit |
| `/diff <path>` | Show current git diff |

### Safety & Validation

| Command | Description |
|---------|-------------|
| `/validate <path>` | Run lint, typecheck, build, test |
| `/undo <path>` | Rollback to last checkpoint |

### Bug Fixing

| Command | Description |
|---------|-------------|
| `/errors` | Show recent unresolved Sentry errors |
| `/fix [issue_id]` | Auto-fix a Sentry error (fetch, generate, validate, commit) |

### Deployment & PRs

| Command | Description |
|---------|-------------|
| `/deploy <staging\|production>` | Deploy via Vercel |
| `/pr <title>` | Create a GitHub pull request |

## How It Works

### Feature Building (`/add`)

```
You: /add user authentication with JWT
```

1. Creates feature branch `feature/user-authentication-with-jwt`
2. Uses context builder to find relevant existing code
3. Generates code changes via Claude Sonnet 4
4. Applies changes to files
5. Runs validation (lint, typecheck, tests, build)
6. If validation passes: commits to feature branch
7. If validation fails: rolls back automatically
8. You run `/pr "Add JWT authentication"` to create a PR

### Bug Fixing (`/fix`)

```
You: /fix
```

1. Fetches latest unresolved error from Sentry
2. Parses stack trace and error context
3. Searches codebase for relevant files
4. Generates minimal fix via LLM
5. Creates fix branch `fix/sentry-{issue_id}`
6. Applies and validates
7. Commits if all checks pass

### Deployment (`/deploy`)

```
You: /deploy staging
```

1. Pushes current branch to remote
2. Triggers Vercel deployment (preview or production)
3. Returns deployment URL and status

## Project Structure

```
devagent/
├── agent/
│   ├── core.py              # Entry point, bot orchestration
│   ├── commands.py           # All 16 command handlers
│   ├── context.py            # LLM context retrieval (FTS5 + dependency graph)
│   └── safety.py             # Validation runner, checkpoints, rollback
│
├── code_engine/
│   ├── analyzer.py           # Project detection (language, framework, deps)
│   ├── parser.py             # Tree-sitter AST parsing (Python, JS, TS, TSX)
│   ├── generator.py          # LLM code generation + file operations
│   ├── search.py             # SQLite FTS5 code search
│   └── embeddings.py         # ChromaDB semantic search
│
├── integrations/
│   ├── git.py                # Git operations (branch, commit, push, diff)
│   ├── github.py             # GitHub PRs and comments
│   ├── sentry.py             # Sentry error monitoring
│   └── vercel.py             # Vercel deployments
│
├── tg_bot/
│   ├── bot.py                # Telegram app builder with all integrations
│   ├── handlers.py           # Telegram command routing (16 handlers)
│   └── auth.py               # User whitelist authentication
│
├── storage/
│   ├── db.py                 # SQLite (FTS5, entities, manifests, logs)
│   └── cache.py              # In-memory TTL cache
│
├── config/
│   ├── settings.py           # Environment-based configuration
│   └── llm.py                # LLM provider abstraction (Anthropic, OpenAI)
│
└── tests/                    # 222 tests, 82% coverage
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Telegram | `python-telegram-bot` |
| LLM | Claude Sonnet 4 via `anthropic` SDK (or GPT-4o via `openai`) |
| Code Parsing | `tree-sitter` (Python, JS, TS, TSX) |
| Keyword Search | SQLite FTS5 via `aiosqlite` |
| Semantic Search | ChromaDB |
| Git | `gitpython` |
| HTTP | `httpx` (GitHub, Sentry, Vercel APIs) |
| Testing | `pytest` + `pytest-asyncio` + `pytest-cov` |

## Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=agent --cov=tg_bot --cov=code_engine --cov=config --cov=storage --cov=integrations

# Specific module
pytest tests/test_safety.py -v
pytest tests/test_github_integration.py -v
```

## Safety Guarantees

- **Branch protection** — refuses to work directly on `main` or `master`
- **Checkpoints** — saves git state before every change
- **Automatic rollback** — reverts if validation fails
- **Validation pipeline** — auto-detects lint, typecheck, build, test from project config
- **Auth whitelist** — only allowed Telegram user IDs can interact

## License

MIT
