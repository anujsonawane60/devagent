# Project Plan: AI Dev Agent via Telegram

## 📋 Executive Summary

**What we're building:** A Telegram-controlled AI agent that lives in your codebase, helps build features, fixes bugs, and manages deployments - all from your phone.

**Target:** Next.js/React projects initially (easiest to validate, largest market)

**Timeline:** 12 weeks to production-ready MVP

**Differentiation:** Not another chat-with-codebase tool. This one actually **writes, tests, and deploys** code autonomously.

---

## 🎯 Phase 1: Foundation (Weeks 1-4)

### Week 1: Setup & Architecture

**Goal:** Get basic Telegram bot talking to codebase

**Tasks:**
1. Project structure setup
   ```
   /agent-core          # Main orchestration logic
   /telegram-interface  # Bot handlers
   /code-engine         # Code generation & parsing
   /integrations        # Git, Vercel, testing
   /storage             # SQLite for state, ChromaDB for vectors
   ```

2. Telegram bot scaffolding
   - Bot registration with BotFather
   - Webhook setup
   - Command routing (`/help`, `/status`, `/analyze`)
   - Authentication (whitelist Telegram user IDs)

3. Project detection
   - Auto-detect framework (Next.js, Vite, etc.)
   - Find package.json, tsconfig, entry points
   - Generate project manifest

**Deliverable:** Bot that can receive commands and read project structure

**Testing:** Deploy to a test Next.js project, send `/analyze` command, get project summary back

---

### Week 2: Code Indexing

**Goal:** Agent understands your codebase

**Tasks:**
1. AST parsing
   ```python
   # Use tree-sitter for accurate parsing
   def parse_project():
       - Extract all components, functions, routes
       - Build dependency graph
       - Identify patterns (data fetching, state management)
   ```

2. Vector embedding
   - Embed each file's purpose/functionality
   - Store in ChromaDB
   - Build semantic search: "find auth logic" → returns relevant files

3. Context retrieval
   ```python
   def get_context_for_task(task: str) -> List[File]:
       # Hybrid search:
       # 1. Vector similarity (semantic)
       # 2. Dependency graph (structural)
       # 3. Git history (recency)
       # Return top 15 files that fit in context window
   ```

**Deliverable:** Agent can answer "Where is the authentication logic?" or "Show me all API routes"

**Testing:** Ask it to find specific functionality, verify it returns correct files

---

### Week 3: Basic Code Generation

**Goal:** Agent can add simple features

**Tasks:**
1. Prompt engineering for code generation
   ```python
   SYSTEM_PROMPT = """
   You are a senior Next.js developer.
   
   Project context:
   {project_structure}
   
   Coding standards:
   - TypeScript strict mode
   - Tailwind for styling
   - Server components by default
   - Error boundaries for client components
   
   Current task: {task}
   
   Relevant files:
   {context_files}
   
   Generate code that:
   1. Follows existing patterns
   2. Includes TypeScript types
   3. Has error handling
   4. Matches project style
   """
   ```

2. File operations
   - Create new files
   - Modify existing files (using AST manipulation, not regex)
   - Update imports automatically

3. Git integration
   - Create feature branch
   - Commit with descriptive message
   - Push to remote

**Deliverable:** Command like `/add feature: contact form on homepage` → creates component, adds route, commits to git

**Testing:** 
- Add 5 different simple features
- Verify they build without errors
- Check code quality manually

---

### Week 4: Testing & Validation

**Goal:** Never deploy broken code

**Tasks:**
1. Pre-commit validation
   ```python
   def validate_changes():
       return {
           'typescript': run_tsc(),
           'build': run_build(),
           'tests': run_unit_tests(),
           'lint': run_eslint()
       }
   ```

2. Automated test generation
   - For new components, generate basic tests
   - Use Claude to write Jest/Vitest tests
   - Run before committing

3. Safety mechanisms
   - Always create new branch (never commit to main)
   - Checkpoint system (save state before changes)
   - Rollback command: `/undo`

**Deliverable:** Agent won't commit code that fails TypeScript or build checks

**Testing:**
- Intentionally request broken code
- Verify it catches errors
- Test rollback mechanism

---

## 🚀 Phase 2: Bug Fixing (Weeks 5-8)

### Week 5: Error Monitoring Integration

**Goal:** Agent knows when things break

**Tasks:**
1. Sentry integration
   - Webhook listener for new errors
   - Parse stacktraces
   - Extract error context

2. Error notification flow
   ```
   Error occurs → Sentry webhook → Agent receives
   → Fetch relevant code → Analyze with LLM
   → Send TG message: "🔴 New error in /api/users"
   → Admin replies: "fix it" or "ignore"
   ```

3. Error database
   - Store all errors
   - Track resolution status
   - Learn from past fixes

**Deliverable:** Real-time error notifications in Telegram with code context

---

### Week 6: Automated Bug Fixing

**Goal:** Agent can fix common bugs autonomously

**Tasks:**
1. Fix generation
   ```python
   def generate_fix(error: Error, context: CodeContext):
       prompt = f"""
       Error: {error.message}
       Stacktrace: {error.stack}
       
       Relevant code:
       {context.files}
       
       Previous similar fixes:
       {vector_db.search_similar_errors(error)}
       
       Generate a fix that:
       1. Addresses root cause
       2. Adds error handling
       3. Includes test to prevent regression
       """
       
       return claude_api.generate(prompt)
   ```

2. Fix validation
   - Apply fix to codebase
   - Run full test suite
   - If tests pass → create PR
   - If tests fail → try alternative approach

3. PR creation
   - GitHub/GitLab API integration
   - Descriptive PR title and body
   - Link to Sentry error
   - Request admin review

**Deliverable:** `/fix` command that attempts to resolve reported errors

**Testing:**
- Introduce known bugs
- Verify agent can fix them
- Measure success rate

---

### Week 7: Learning from Fixes

**Goal:** Agent gets better over time

**Tasks:**
1. Fix similarity matching
   - When new error occurs, search for similar past errors
   - If similar fix exists, apply with minimal modification

2. Pattern recognition
   - Identify common bug types in your codebase
   - Suggest preventive measures
   - "You often forget null checks in API routes - should I add validation middleware?"

3. Feedback loop
   ```python
   # After admin reviews PR
   if pr_merged:
       vector_db.store_successful_fix(error, fix, outcome="success")
   else:
       vector_db.store_failed_fix(error, fix, outcome="rejected")
       # Use this to improve future attempts
   ```

**Deliverable:** Agent suggests fixes based on historical patterns

---

### Week 8: Deployment Automation

**Goal:** Agent can deploy approved changes

**Tasks:**
1. Vercel/Netlify integration
   - API token setup
   - Trigger deployments
   - Monitor build status

2. Deployment flow
   ```
   Admin: "/deploy staging"
   Agent: Runs validation → Creates preview → Sends URL
   Admin: Tests preview → "/deploy production"
   Agent: Merges to main → Triggers prod deploy → Monitors for errors
   ```

3. Rollback capability
   - If new errors spike after deploy
   - Auto-notify: "⚠️ Error rate increased 300% after deploy"
   - Quick rollback: `/rollback production`

**Deliverable:** Full CI/CD controlled via Telegram

**Testing:**
- Deploy to staging
- Introduce breaking change
- Verify rollback works
- Test error monitoring post-deploy

---

## 🔧 Phase 3: Polish & Scale (Weeks 9-12)

### Week 9: Multi-Project Support

**Goal:** Manage multiple projects from one bot

**Tasks:**
1. Project switching
   ```
   Admin: "/projects"
   Agent: "1. my-saas-app (Next.js)
           2. api-backend (FastAPI)
           3. mobile-app (React Native)"
   
   Admin: "/switch 1"
   Agent: "Now working on my-saas-app"
   ```

2. Project-specific context
   - Separate vector DB per project
   - Separate git repos
   - Separate deployment configs

3. Unified dashboard
   - Health status of all projects
   - Recent errors across projects
   - Deploy history

**Deliverable:** Single bot managing 3+ projects

---

### Week 10: Advanced Features

**Goal:** Power user capabilities

**Tasks:**
1. Code review agent
   - `/review` command before merging PR
   - Check for security issues, performance problems
   - Suggest improvements

2. Performance monitoring
   - Integrate with Vercel Analytics
   - Alert on slow endpoints
   - Suggest optimizations (code splitting, caching)

3. Dependency management
   - Auto-detect outdated packages
   - Generate upgrade PRs
   - Test compatibility before suggesting

**Deliverable:** Proactive agent that maintains codebase health

---

### Week 11: Security & Permissions

**Goal:** Production-grade security

**Tasks:**
1. Multi-user support
   ```python
   ROLES = {
       'admin': ['deploy', 'rollback', 'delete'],
       'developer': ['create', 'fix', 'review'],
       'viewer': ['status', 'logs']
   }
   ```

2. Action approval workflow
   - Critical actions require confirmation
   - 2FA via Telegram for production deploys
   - Audit log of all actions

3. Secrets management
   - Never expose API keys in messages
   - Encrypted storage for credentials
   - Rotate tokens regularly

**Deliverable:** Enterprise-ready security model

---

### Week 12: Documentation & Launch

**Goal:** Ship it

**Tasks:**
1. Documentation
   - README with setup instructions
   - Command reference
   - Architecture diagrams
   - Best practices guide

2. Onboarding flow
   ```
   npm install -g devagent
   devagent init
   # Walks through:
   # - Telegram bot token
   # - Project detection
   # - Git setup
   # - Deploy provider
   # - First test command
   ```

3. Demo video & landing page
   - 2-minute demo showing key workflows
   - Pricing page (if monetizing)
   - GitHub repo with examples

**Deliverable:** Public launch

---

## 📊 Success Metrics

Track these from day 1:

| Metric | Target (3 months) |
|--------|-------------------|
| Successful code generations | 80%+ build without errors |
| Bug fix success rate | 50%+ auto-fixes accepted |
| Average fix time | <5 minutes from error to PR |
| User satisfaction | 4+ stars on feedback |
| False positive rate | <10% (wrong fixes suggested) |

---

## 🛠️ Tech Stack (Final)

**Core:**
- Python 3.11+ (main agent logic)
- `python-telegram-bot` (Telegram interface)
- `anthropic` SDK (Claude Sonnet 4)
- `tree-sitter` (code parsing)
- `gitpython` (Git operations)

**Storage:**
- SQLite (state, audit logs, checkpoints)
- ChromaDB (vector embeddings for code search)
- Redis (task queue, rate limiting)

**Integrations:**
- Sentry SDK (error monitoring)
- Vercel/Netlify API (deployments)
- GitHub/GitLab API (PRs, code review)

**Testing:**
- pytest (unit tests)
- playwright (e2e tests)
- Mock Telegram bot for testing flows

---

## 💰 Cost Estimation

**LLM API costs (per project/month):**
- Code generation: ~100 requests/month @ $0.10 = $10
- Bug fixes: ~50 requests/month @ $0.15 = $7.50
- Code review: ~30 requests/month @ $0.05 = $1.50
- **Total: ~$20/month per active project**

**Infrastructure:**
- VPS (4GB RAM): $20/month
- Vector DB hosting: $0 (self-hosted ChromaDB)
- **Total: $20/month**

**Grand total for 5 projects: ~$120/month**

---

## 🚨 Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Agent writes buggy code | Multi-layer validation, human approval for critical changes |
| Security breach via TG | 2FA, IP whitelist, audit logs, encrypted secrets |
| LLM hallucinations | Automated testing, rollback capability, human-in-loop |
| Context window limits | Smart context retrieval, chunking strategies |
| Cost explosion | Rate limiting, caching, budget alerts |

---

## 📦 Repository Structure

```
devagent/
├── README.md
├── setup.py
├── requirements.txt
├── .env.example
│
├── agent/
│   ├── __init__.py
│   ├── core.py              # Main orchestration
│   ├── commands.py          # Command handlers
│   ├── context.py           # Context retrieval
│   └── safety.py            # Validation & rollback
│
├── telegram/
│   ├── bot.py               # Telegram bot setup
│   ├── handlers.py          # Message/command handlers
│   └── auth.py              # User authentication
│
├── code_engine/
│   ├── parser.py            # AST parsing
│   ├── generator.py         # Code generation
│   ├── analyzer.py          # Code analysis
│   └── embeddings.py        # Vector embeddings
│
├── integrations/
│   ├── git.py               # Git operations
│   ├── sentry.py            # Error monitoring
│   ├── vercel.py            # Deployments
│   └── github.py            # PR creation
│
├── storage/
│   ├── db.py                # SQLite operations
│   ├── vector.py            # ChromaDB wrapper
│   └── cache.py             # Redis cache
│
├── tests/
│   ├── test_parser.py
│   ├── test_generator.py
│   └── test_e2e.py
│
└── examples/
    ├── nextjs-project/      # Sample project
    └── commands.md          # Command examples
```


