# Changelog

## [Week 5] Runtime Fixes & Multi-LLM Support — 2026-03-05

### Bug Fixes
- `agent/core.py` — Fixed "event loop already running" crash on startup; replaced `app.run_polling()` with lower-level async API (`app.updater.start_polling()` + `app.start()`) for proper Windows compatibility
- `agent/commands.py` — Added `project_path` persistence; `/setup` now stores the path and all subsequent commands (`/analyze`, `/index`, `/generate`, `/add`, `/validate`, `/diff`, `/undo`, `/deploy`, `/pr`, `/fix`) use it automatically without requiring a path argument each time
- `agent/commands.py` — Added `_resolve_path()` helper for consistent path resolution (absolute, relative to project, or stored default)
- `code_engine/analyzer.py` — Fixed "Could not detect project" for monorepo layouts; added `_analyze_monorepo()` that scans immediate subdirectories (e.g. `frontend/`, `backend/`) and combines results when root-level detection fails
- `tg_bot/bot.py` — Added global `error_handler` so LLM/API errors are sent back to the user in Telegram instead of crashing silently

### New Features
- `config/llm.py` — Added **Gemini** provider (`GeminiProvider` using `google-genai` SDK) and **DeepSeek** provider (via OpenAI-compatible API with custom `base_url`); total supported providers: Anthropic, OpenAI, Gemini, DeepSeek
- `config/settings.py` — Added `gemini_api_key`, `gemini_model`, `deepseek_api_key`, `deepseek_model` settings; added `get_llm_api_key()` and `get_llm_model()` helpers; validation now supports all 4 providers
- `tg_bot/handlers.py` — Added `/start` command (shows user ID and auth status), added plain text handler (directs users to use `/help`)
- `tg_bot/bot.py` — Simplified LLM provider creation using new `Settings` helper methods

### Modified Files
- `agent/core.py` — Rewrote `main()` with proper async lifecycle and graceful shutdown (Ctrl+C)
- `agent/commands.py` — All path-dependent commands now default to stored `project_path`; updated `/help` with categorized command listing and active project display; `/status` shows current project path
- `config/llm.py` — `OpenAIProvider` now accepts `base_url` and `provider_label` for OpenAI-compatible APIs; `create_llm_provider()` factory supports `gemini` and `deepseek`
- `config/settings.py` — Added `SUPPORTED_PROVIDERS` constant; `validate()` uses dynamic key name lookup
- `tg_bot/handlers.py` — Removed hardcoded `project_path=""` from handler calls; handlers now rely on `CommandHandler`'s stored path
- `code_engine/analyzer.py` — `analyze()` falls back to monorepo scanning; TypeScript detection checks subdirectories
- `setup.py` — Added `google-genai>=1.0.0` dependency
- `.env.example` — Updated with all 4 LLM provider configurations

---

## [Week 4+] Full Integration Suite — 2026-03-04

### New Files
- `code_engine/embeddings.py` — `SemanticSearch` class using ChromaDB for code embedding, similarity search, batch upsert, per-project clear
- `integrations/github.py` — `GitHubManager` with `PullRequest`/`PRComment` dataclasses; create, list, get, merge PRs; add comments; auto-detect owner/repo from SSH/HTTPS remotes
- `integrations/sentry.py` — `SentryClient` with `SentryError`/`SentryFrame` dataclasses; fetch unresolved issues, parse stack traces from events, generate LLM-ready fix context, resolve issues via API
- `integrations/vercel.py` — `VercelClient` with `Deployment` dataclass; create, list, cancel deployments; promote preview to production; rollback to previous successful deploy; team/project scoping
- `tests/test_embeddings.py` — 10 tests for ChromaDB semantic search
- `tests/test_github_integration.py` — 13 tests for GitHub PR lifecycle and repo detection
- `tests/test_sentry_integration.py` — 10 tests for Sentry issue fetching, stack trace parsing, resolve
- `tests/test_vercel_integration.py` — 13 tests for Vercel deployment operations

### Modified Files
- `config/settings.py` — added `github_token`, `sentry_auth_token`, `sentry_org`, `sentry_project`, `vercel_token`, `vercel_project_id`, `vercel_team_id`, `chromadb_path` settings with env var loading
- `agent/commands.py` — `CommandHandler` now accepts `github`, `sentry`, `vercel` params; added 6 new command methods: `add_feature`, `fix_error`, `deploy`, `errors`, `create_pr`, `setup_project`; `/status` shows active integrations; `/help` lists all 16 commands
- `tg_bot/handlers.py` — wired 6 new Telegram handlers (add, fix, deploy, errors, pr, setup); total handlers: 16
- `tg_bot/bot.py` — `create_bot()` now initializes all integrations (LLM, GitHub, Sentry, Vercel) from settings and passes DB to CommandHandler
- `agent/core.py` — passes `db` instance to `create_bot()` for full integration wiring
- `pyproject.toml` — added full dependency list with version pins (`chromadb>=0.5.0`, `httpx>=0.27.0`, etc.); added `devagent` console entry point; updated coverage source list
- `setup.py` — mirrors pyproject.toml dependencies with `install_requires` and `extras_require`
- `tests/conftest.py` — added `github_manager`, `sentry_client`, `vercel_client`, `semantic_search` fixtures
- `tests/test_commands.py` — extended from 17 to 31 tests (14 new tests for add/fix/deploy/errors/pr/setup commands)
- `tests/test_telegram_bot.py` — extended from 8 to 11 tests (3 new handler tests); handler count updated to 16
- `tests/test_config.py` — extended from 8 to 10 tests (2 new tests for integration settings)

### Test Results
- **222 passed, 0 skipped**
- **82% code coverage**

---

## [Week 4] Testing & Validation — 2026-03-04

### New Files
- `agent/safety.py` — `ValidationRunner` (runs lint/typecheck/build/test via `asyncio.create_subprocess_exec`), `SafetyManager` (checkpoint/rollback via git, branch protection, `safe_apply` orchestration), `ValidationCheck`/`ValidationResult`/`Checkpoint` dataclasses
- `tests/test_validation.py` — 13 tests for ValidationRunner
- `tests/test_safety.py` — 12 tests for SafetyManager

### Modified Files
- `agent/commands.py` — added `/validate` and `/undo` commands
- `tg_bot/handlers.py` — wired 2 new Telegram handlers (validate, undo); total handlers: 10
- `tests/conftest.py` — added `safety_manager` and `validation_runner` fixtures
- `tests/test_telegram_bot.py` — handler count updated to 10

### Test Results
- **157 passed, 0 skipped**
- **89% code coverage**

---

## [Week 3] Basic Code Generation — 2026-03-04

### New Files
- `integrations/git.py` — `GitManager` class with `GitStatus`/`CommitResult` dataclasses; supports branch, commit, stage, diff, push operations via GitPython
- `code_engine/generator.py` — `CodeGenerator` class with `FileChange`/`GenerationPlan`/`GenerationResult` dataclasses; LLM-powered code generation with JSON response parsing and file create/modify/delete

### Modified Files
- `agent/commands.py` — added `/generate` and `/diff` commands; `CommandHandler` now accepts optional `llm` param
- `tg_bot/handlers.py` — wired 2 new Telegram handlers (generate, diff); total handlers: 8
- `tests/conftest.py` — added `git_repo` and `mock_llm` fixtures
- `tests/test_git_integration.py` — replaced skip stub with 12 tests (status, branching, staging, commit, diff, remote, dirty tree)
- `tests/test_code_generator.py` — replaced skip stub with 15 tests (dataclasses, prompt building, JSON parsing, file operations, end-to-end)
- `tests/test_commands.py` — extended from 11 to 17 tests (added generate/diff command tests)
- `tests/test_telegram_bot.py` — extended from 6 to 8 tests (added generate/diff handler tests); handler count updated to 8

### Test Results
- **132 passed, 2 skipped** (stubs for Week 4)
- **91% code coverage**

---

## [Week 2] Code Indexing & Search — 2026-03-04

### New Files
- `code_engine/search.py` — SQLite FTS5 search engine (`CodeSearchEngine`) with `index_project`, `search`, `find_definition`, `get_file_context`
- `tests/test_parser.py` — 16 tests for tree-sitter AST parsing
- `tests/test_context.py` — 6 tests for context retrieval
- `tests/dummy_data/sample_python_project/app/models.py` — classes with methods (User, Project)
- `tests/dummy_data/sample_python_project/app/utils.py` — utility functions and FileProcessor class
- `tests/dummy_data/sample_nextjs_project/src/app/layout.tsx` — React components (RootLayout, Header, Footer)
- `tests/dummy_data/sample_nextjs_project/src/lib/api.ts` — async API helpers and arrow functions

### Modified Files
- `requirements.txt` — added `tree-sitter>=0.23.0`, `tree-sitter-python>=0.23.0`, `tree-sitter-javascript>=0.23.0`, `tree-sitter-typescript>=0.23.0`
- `code_engine/parser.py` — replaced stub with full tree-sitter parser (Python, JS, TS/TSX); extracts functions, classes, methods, components, imports, exports
- `storage/db.py` — added `code_entities`, `code_search` (FTS5), `file_dependencies` tables; added `save_entities`, `search_code`, `save_dependencies`, `get_dependencies`, `clear_project_index` methods
- `agent/context.py` — replaced stub with `ContextBuilder` class (FTS5 search, dependency expansion, relevance ranking, token budget trimming)
- `agent/commands.py` — added `/index`, `/search`, `/find` command handlers; `CommandHandler` now accepts optional `db` param
- `tg_bot/handlers.py` — wired 3 new Telegram handlers (index, search, find); total handlers: 6
- `tests/conftest.py` — added `parser`, `db`, `search_engine`, `context_builder` fixtures
- `tests/test_file_search.py` — replaced skip stub with 10 search engine tests
- `tests/test_commands.py` — extended from 5 to 11 tests (added async command tests)
- `tests/test_telegram_bot.py` — extended from 5 to 6 tests (added search handler test)
- `tests/test_db.py` — extended from 4 to 8 tests (added code_entities and dependencies tests)

### Test Results
- **97 passed, 4 skipped** (stubs for Week 3–4)
- **90% code coverage**
