# DevAgent — Agent Reference

> **8 agents, 32 tools** — all managed by the Jarvis supervisor.
> User talks to Jarvis, Jarvis delegates to the right agent.

---

## Supervisor — Jarvis

The orchestrator. Understands user intent and routes to the right sub-agent.

- Responds directly to greetings, small talk, general questions
- Delegates domain-specific tasks to sub-agents
- Can chain multiple agents for complex requests
- User never sees internal delegation

**File:** `jarvis/agents/supervisor.py`

---

## 1. Task Agent

Manages tasks, to-do lists, and reminders.

| Tool | What It Does |
|------|-------------|
| `create_task` | Create task with title, due_date, due_time, priority (low/medium/high/urgent), category |
| `list_tasks` | List tasks by status (pending/completed/all) |
| `complete_task` | Mark a task as completed by ID |
| `delete_task` | Delete a task by ID |

**Example triggers:**
- "Add a task to buy groceries"
- "Remind me to call mom tomorrow"
- "Show my tasks"
- "Mark task #3 as done"
- "Create a high priority work task: finish report by Friday"

**File:** `jarvis/agents/task_agent.py` | **Tools:** `jarvis/tools/task_tools.py`

---

## 2. Research Agent

Searches the web and gathers information.

| Tool | What It Does |
|------|-------------|
| `web_search` | Search the web via DuckDuckGo (returns title, summary, URL) |
| `get_current_time` | Get current time in any timezone |

**Example triggers:**
- "Search for latest AI news"
- "What time is it in Tokyo?"
- "Who won the cricket match yesterday?"
- "Look up Python FastAPI best practices"

**File:** `jarvis/agents/research_agent.py` | **Tools:** `jarvis/tools/search_tools.py`, `jarvis/tools/datetime_tools.py`

---

## 3. Notes Agent

Manages structured notes with titles and content.

| Tool | What It Does |
|------|-------------|
| `save_note` | Save a note with title, content, category, pin option |
| `search_notes` | Smart search (keyword + semantic via vector DB) |
| `list_notes` | List all notes (titles, categories) |
| `delete_note` | Delete a note by ID |

**Example triggers:**
- "Save a note about today's meeting"
- "Save a note titled 'Project Ideas' with content ..."
- "Find my notes about Python"
- "Show all my notes"

**File:** `jarvis/agents/notes_agent.py` | **Tools:** `jarvis/tools/note_tools.py`

---

## 4. Contacts Agent

Manages the user's personal contacts with encrypted sensitive fields.

| Tool | What It Does |
|------|-------------|
| `save_contact` | Save contact (name, relationship, phone, email, birthday, context). Auto-updates if exists. |
| `find_contact` | Find contact by name, shows all their info |
| `update_contact` | Update specific fields of an existing contact |
| `list_contacts` | List all contacts (names + relationships, no sensitive data) |
| `delete_contact` | Permanently delete a contact |

**Security:** Phone, email, and address are **AES-256 encrypted** in the database. The LLM never sees raw values in conversation summaries.

**Example triggers:**
- "Satyajit's number is 9876543210"
- "Save my friend Raj's email: raj@gmail.com"
- "What's Satyajit's phone number?"
- "Show all my contacts"
- "My mom's birthday is May 15th" (saves as contact)

**File:** `jarvis/agents/contacts_agent.py` | **Tools:** `jarvis/tools/contact_tools.py`

---

## 5. Thoughts Agent

Captures quick, unstructured brain dumps — the zero-friction note-taking.

| Tool | What It Does |
|------|-------------|
| `save_thought` | Save a thought with auto-classification (idea/opinion/fact/random/bookmark/quote/snippet/question) |
| `search_thoughts` | Smart search (keyword + semantic via vector DB) |
| `list_thoughts` | List thoughts, optionally filtered by type |
| `pin_thought` | Pin an important thought |
| `delete_thought` | Delete a thought by ID |

**Auto-classification:**
- "I think React is better" → `opinion`
- "Idea: habit tracker app" → `idea`
- "Satyajit is moving to BLR" → `fact`
- "check out this link" → `bookmark`
- Code block → `snippet`
- "Why does X happen?" → `question`
- Everything else → `random`

**Private thoughts** (`is_private=true`) are encrypted in the database.

**Example triggers:**
- "Save this: pizza place on MG Road was amazing"
- "I think I should learn Rust"
- "Idea: build a habit tracker app"
- "Show my ideas"
- "Search my thoughts about food"

**File:** `jarvis/agents/thoughts_agent.py` | **Tools:** `jarvis/tools/thought_tools.py`

---

## 6. Vault Agent

Securely stores and retrieves passwords, PINs, API keys, and other secrets.

| Tool | What It Does |
|------|-------------|
| `store_secret` | Store a secret (value encrypted with AES-256). Categories: password/pin/key/secret/personal |
| `get_secret` | Retrieve and decrypt a secret by label |
| `list_secrets` | List all labels and categories (values NEVER shown) |
| `delete_secret` | Permanently delete a secret |

**Security:**
- Values are **always encrypted** at rest
- LLM **never sees** raw secret values in conversation history
- When listing, only labels are shown — never values
- Auto-detects password/PIN patterns in user messages

**Example triggers:**
- "My Netflix password is xyz123"
- "Save my WiFi password: HomeNet456"
- "What's my Netflix password?"
- "Show all my saved passwords"
- "Delete my old WiFi password"

**File:** `jarvis/agents/vault_agent.py` | **Tools:** `jarvis/tools/vault_tools.py`

---

## 7. Memory Agent

Jarvis's long-term memory — learns and recalls facts about the user.

| Tool | What It Does |
|------|-------------|
| `learn_fact` | Learn a fact about the user. Confidence increases with repetition. Categories: preference/fact/opinion/habit/relationship |
| `recall` | Smart recall (keyword + semantic search) |
| `forget` | Remove a learned fact by ID |

**How confidence works:**
- First time learning a fact: confidence = 50%
- Each time the same fact is confirmed: confidence += 10%
- Higher confidence facts are returned first in recall

**Example triggers:**
- "I prefer dark mode in everything"
- "My mom's name is Sunita"
- "I wake up at 6 AM every day"
- "Do you remember what languages I like?"
- "What do you know about me?"
- "Forget that I like Java — I don't anymore"

**File:** `jarvis/agents/memory_agent.py` | **Tools:** `jarvis/tools/memory_tools.py`

---

## 8. Scheduler Agent

Schedules future actions — messages, reminders, and recurring events.

| Tool | What It Does |
|------|-------------|
| `schedule_action` | Schedule a future action (send_message/reminder/recurring_task) with datetime and optional recurrence |
| `list_schedules` | List scheduled actions by status (pending/completed/failed/cancelled) |
| `cancel_schedule` | Cancel a scheduled action by ID |

**Recurrence rules:**
- `daily` — every day
- `weekly:mon` — every Monday
- `weekly:mon,fri` — every Monday and Friday
- `monthly:15` — 15th of every month
- `yearly:04-01` — every April 1st (birthdays!)

**Example triggers:**
- "Send birthday wishes to Satyajit at 12 AM tomorrow"
- "Remind me to take medicine every day at 8 AM"
- "Schedule a weekly report every Monday at 9 AM"
- "Show my upcoming schedules"
- "Cancel schedule #5"

**File:** `jarvis/agents/scheduler_agent.py` | **Tools:** `jarvis/tools/scheduler_tools.py`

---

## Routing — What Goes Where

| User Says | Agent | Why |
|-----------|-------|-----|
| "Add a task" | task_agent | Task management |
| "Search for news" | research_agent | Web search |
| "Save a note about..." | notes_agent | Structured note |
| "Save this: I think..." | thoughts_agent | Quick brain dump |
| "Satyajit's number is..." | contacts_agent | Contact info |
| "My password is..." | vault_agent | Secret data |
| "I prefer Python" | memory_agent | Learning about user |
| "Remind me at 6 PM" | scheduler_agent | Future action |
| "Hello!" | jarvis (direct) | Simple greeting |
| "Who are you?" | jarvis (direct) | General question |

---

## How to Add a New Agent

```
1. Create jarvis/tools/my_tools.py     — define @tool functions
2. Create jarvis/agents/my_agent.py    — define AgentDefinition + system prompt
3. Add "jarvis.agents.my_agent" to AGENT_MODULES in jarvis/agents/registry.py
4. Restart — supervisor auto-discovers and routes to it
```

No changes to supervisor code. No changes to interface layer.

---

## File Map

```
jarvis/agents/
├── supervisor.py          Jarvis orchestrator
├── registry.py            Auto-discovers all agents
├── task_agent.py          Tasks & reminders
├── research_agent.py      Web search & time
├── notes_agent.py         Structured notes
├── contacts_agent.py      People & contacts
├── thoughts_agent.py      Quick brain dumps
├── vault_agent.py         Encrypted secrets
├── memory_agent.py        Long-term memory
└── scheduler_agent.py     Future actions

jarvis/tools/
├── task_tools.py          4 tools
├── search_tools.py        1 tool
├── datetime_tools.py      1 tool
├── note_tools.py          4 tools
├── contact_tools.py       5 tools
├── thought_tools.py       5 tools
├── vault_tools.py         4 tools
├── memory_tools.py        3 tools
└── scheduler_tools.py     3 tools
                           ─────────
                           30 tools total
```
