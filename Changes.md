# Changelog

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
