# DevAgent — Demo Task List

Test every agent with these examples. Run the bot (`python -m jarvis.main`), open Telegram, and try each one.

---

## 1. Task Agent

| # | User Input | Expected Action | Expected Response |
|---|-----------|-----------------|-------------------|
| 1.1 | "Add a task: buy groceries" | `create_task(title="buy groceries")` → saves to `tasks` table | "Task created: buy groceries" |
| 1.2 | "Create a high priority task: finish report by 2026-04-05" | `create_task(title="finish report", priority="high", due_date="2026-04-05")` | "Task created: finish report \| priority: high \| due: 2026-04-05" |
| 1.3 | "Add a work task: review PR, due tomorrow at 3pm" | `create_task(title="review PR", category="work", due_date="2026-04-01", due_time="15:00")` | "Task created: review PR \| due: 2026-04-01 15:00 \| category: work" |
| 1.4 | "Show my tasks" | `list_tasks(status="pending")` → reads from DB | Lists all pending tasks with IDs, priorities, due dates |
| 1.5 | "Show all tasks including completed" | `list_tasks(status="all")` | Lists all tasks with [x] for completed ones |
| 1.6 | "Mark task #1 as done" | `complete_task(task_id=1)` → updates status in DB | "Task #1 marked as completed." |
| 1.7 | "Delete task #2" | `delete_task(task_id=2)` → removes from DB | "Task #2 deleted." |

---

## 2. Research Agent

| # | User Input | Expected Action | Expected Response |
|---|-----------|-----------------|-------------------|
| 2.1 | "Search for latest AI news" | `web_search(query="latest AI news")` → DuckDuckGo API | Summarized search results with titles, snippets, and links |
| 2.2 | "What time is it in Tokyo?" | `get_current_time(timezone_name="Asia/Tokyo")` | "Current time (Asia/Tokyo): 2026-03-31 18:15:00 JST" |
| 2.3 | "Who is the CEO of Tesla?" | `web_search(query="CEO of Tesla")` | Summarized answer from search results |
| 2.4 | "Search for Python FastAPI tutorial" | `web_search(query="Python FastAPI tutorial")` | List of tutorial links with descriptions |

---

## 3. Notes Agent

| # | User Input | Expected Action | Expected Response |
|---|-----------|-----------------|-------------------|
| 3.1 | "Save a note titled 'Meeting Notes' with content: discussed Q2 roadmap, budget approved" | `save_note(title="Meeting Notes", content="discussed Q2 roadmap, budget approved")` → saves to `notes` table + vector index | "Note saved: Meeting Notes" |
| 3.2 | "Save a pinned work note: Sprint Review — shipped 3 features, 2 bugs fixed" | `save_note(title="Sprint Review", content="shipped 3 features, 2 bugs fixed", category="work", is_pinned=true)` | "Note saved (pinned) [work]: Sprint Review" |
| 3.3 | "Find my notes about roadmap" | `search_notes(query="roadmap")` → SQL LIKE + vector semantic search | Shows "Meeting Notes" even if searching "quarterly planning" (semantic match) |
| 3.4 | "Show all my notes" | `list_notes()` | List of note titles with IDs, categories, dates |
| 3.5 | "Delete note #1" | `delete_note(note_id=1)` → removes from DB + vector store | "Note #1 deleted." |

---

## 4. Contacts Agent

| # | User Input | Expected Action | Expected Response |
|---|-----------|-----------------|-------------------|
| 4.1 | "Satyajit's number is 9876543210" | `save_contact(name="Satyajit", phone="9876543210")` → phone **encrypted** in DB + vector index | "Contact saved: Satyajit" (does NOT repeat the phone number) |
| 4.2 | "Save my friend Raj, email raj@gmail.com, birthday 1999-05-15" | `save_contact(name="Raj", relationship="friend", email="raj@gmail.com", birthday="1999-05-15")` → email **encrypted** | "Contact saved: Raj (friend)" |
| 4.3 | "He works at Google in Bangalore" | `update_contact(name="Raj", context="works at Google in Bangalore")` | "Updated Raj's info." |
| 4.4 | "What's Satyajit's phone number?" | `find_contact(name="Satyajit")` → **decrypts** phone from DB | Shows name, phone (decrypted), relationship, birthday |
| 4.5 | "Show all my contacts" | `list_contacts()` → names + relationships only (no sensitive data) | List of contacts with relationships and birthdays |
| 4.6 | "Update Satyajit's email to satya@gmail.com" | `update_contact(name="Satyajit", email="satya@gmail.com")` → **encrypted** | "Updated Satyajit's info." |
| 4.7 | "Delete Raj's contact" | `delete_contact(name="Raj")` → hard delete from DB + vector store | "Deleted contact: Raj" |

**Security check:** Open `data/jarvis.db` with any SQLite viewer → `contacts` table → `phone_enc` column should show encrypted gibberish, NOT the actual phone number.

---

## 5. Thoughts Agent

| # | User Input | Expected Action | Expected Response |
|---|-----------|-----------------|-------------------|
| 5.1 | "Save this: I think React is better than Angular" | `save_thought(content="I think React is better than Angular", thought_type="opinion")` → saves to DB + vector index | "Saved opinion: I think React is better than Angular" |
| 5.2 | "Idea: build a habit tracker app with gamification" | `save_thought(content="build a habit tracker app with gamification", thought_type="idea")` | "Saved idea: build a habit tracker app..." |
| 5.3 | "That pizza place on MG Road was amazing" | `save_thought(content="That pizza place on MG Road was amazing", thought_type="random")` | "Saved thought: That pizza place on MG Road..." |
| 5.4 | "Save privately: my interview is at XYZ company" | `save_thought(content="my interview is at XYZ company", is_private=true)` → content **encrypted** in DB | "Saved thought (private): my interview..." |
| 5.5 | "What were those food places I mentioned?" | `search_thoughts(query="food places")` → vector semantic search finds "pizza place on MG Road" even without keyword match | Shows matching thoughts with relevance scores |
| 5.6 | "Show my ideas" | `list_thoughts(thought_type="idea")` | Lists only thoughts typed as "idea" |
| 5.7 | "Show all my thoughts" | `list_thoughts()` | Lists all thoughts with type tags |
| 5.8 | "Pin thought #3" | `pin_thought(thought_id=3)` | "Thought #3 pinned." |
| 5.9 | "Delete thought #1" | `delete_thought(thought_id=1)` → removes from DB + vector store | "Thought #1 deleted." |

**Semantic search test:** Save "Satya recommended Cafe Paashh near Koregaon Park" then search "food places friends told me about" → should find it even though no keywords match.

---

## 6. Vault Agent

| # | User Input | Expected Action | Expected Response |
|---|-----------|-----------------|-------------------|
| 6.1 | "My Netflix password is xyz123" | `store_secret(label="Netflix password", value="xyz123", category="password")` → value **encrypted** | "Securely saved: Netflix password (password)" (does NOT show xyz123) |
| 6.2 | "Save my WiFi password: HomeNet456" | `store_secret(label="WiFi password", value="HomeNet456", category="password")` | "Securely saved: WiFi password (password)" |
| 6.3 | "My bank PIN is 1234" | `store_secret(label="Bank PIN", value="1234", category="pin")` | "Securely saved: Bank PIN (pin)" |
| 6.4 | "What's my Netflix password?" | `get_secret(label="Netflix")` → **decrypts** from vault | Shows the decrypted value: "xyz123" |
| 6.5 | "Show all my saved passwords" | `list_secrets()` → labels and categories ONLY | "Netflix password (password), WiFi password (password), Bank PIN (pin)" — NO values shown |
| 6.6 | "Delete my old WiFi password" | `delete_secret(label="WiFi")` → hard delete | "Deleted secret: WiFi password" |

**Security check:** Open `data/jarvis.db` → `vault` table → `value_enc` column should show encrypted gibberish, NOT "xyz123".

---

## 7. Memory Agent

| # | User Input | Expected Action | Expected Response |
|---|-----------|-----------------|-------------------|
| 7.1 | "I prefer Python over Java" | `learn_fact(fact="User prefers Python over Java", category="preference")` → saves to DB + vector index, confidence=0.5 | "Remembered: User prefers Python over Java" |
| 7.2 | "My mom's name is Sunita" | `learn_fact(fact="User's mother is Sunita", category="relationship")` | "Remembered: User's mother is Sunita" |
| 7.3 | "I wake up at 6 AM every day" | `learn_fact(fact="User wakes up at 6 AM daily", category="habit")` | "Remembered: User wakes up at 6 AM daily" |
| 7.4 | "I really love Python" | `learn_fact(fact="User prefers Python over Java")` → same fact, confidence boosts 0.5 → 0.6 | "Remembered: ..." (confidence increased internally) |
| 7.5 | "What do you know about my preferences?" | `recall(query="preferences")` → SQL + vector search | Lists learned facts sorted by confidence |
| 7.6 | "What programming languages do I like?" | `recall(query="programming languages")` → vector finds "User prefers Python over Java" semantically | Shows matched memory with confidence score |
| 7.7 | "Forget that I like Java" | `forget(memory_id=...)` → deletes from DB + vector store | "Memory #X forgotten." |

**Confidence test:** Say "I prefer Python" 3 more times → recall → confidence should be 0.9 or higher.

---

## 8. Scheduler Agent

| # | User Input | Expected Action | Expected Response |
|---|-----------|-----------------|-------------------|
| 8.1 | "Remind me in 2 minutes: time to go" | `schedule_action(action_type="reminder", description="time to go", scheduled_at="2026-03-31T13:54:00")` → saves to `scheduled_jobs` | "Scheduled #1: time to go at 2026-03-31T13:54:00" |
| 8.2 | *(wait 2 min)* | Background runner finds due job → `bot.send_message()` → marks completed | User receives: "[Reminder] time to go" in Telegram |
| 8.3 | "Send birthday wishes to Satyajit at 12 AM on April 1st" | `schedule_action(action_type="send_message", contact_name="Satyajit", scheduled_at="2026-04-01T00:00:00", message="Happy Birthday Satyajit!")` | "Scheduled #2: Birthday wishes to Satyajit at 2026-04-01T00:00:00" |
| 8.4 | "Remind me to take medicine every day at 8 AM" | `schedule_action(action_type="recurring_task", scheduled_at="2026-04-01T08:00:00", recurrence_rule="daily")` | "Scheduled #3: ... (recurring: daily)" |
| 8.5 | "Show my upcoming schedules" | `list_schedules(status="pending")` | Lists all pending jobs with IDs, times, recurrence info |
| 8.6 | "Cancel schedule #3" | `cancel_schedule(job_id=3)` | "Schedule #3 cancelled." |

**Background runner test:** After 8.1, watch the terminal logs. Within 30 seconds of the due time you should see:
```
INFO - Executed job #1: time to go
```

---

## Multi-Agent Scenarios (Complex)

These test Jarvis routing to multiple agents in sequence.

| # | User Input | Expected Flow | What Happens |
|---|-----------|---------------|-------------|
| M1 | "My friend Satyajit's birthday is tomorrow, his number is 9876543210, send him wishes at 12 AM" | contacts_agent → scheduler_agent | 1. Saves contact with phone (encrypted). 2. Schedules birthday message for 12 AM. 3. At 12 AM, runner sends the message. |
| M2 | "Search for the best Python frameworks and save a note about it" | research_agent → notes_agent | 1. Searches web for Python frameworks. 2. Saves results as a structured note. |
| M3 | "I prefer dark mode, remember that. Also add a task to update my app settings" | memory_agent → task_agent | 1. Learns "User prefers dark mode". 2. Creates task "update app settings". |
| M4 | "Save this thought: I should learn Rust. Also what time is it in Berlin?" | thoughts_agent → research_agent | 1. Saves thought (type: idea). 2. Returns Berlin time. |

---

## Supervisor Direct Responses (No Delegation)

| # | User Input | Expected Result |
|---|-----------|-----------------|
| S1 | "Hello!" | Jarvis greets directly — no agent called |
| S2 | "Who are you?" | Jarvis describes itself — no agent called |
| S3 | "Thank you!" | Jarvis responds politely — no agent called |
| S4 | "What can you do?" | Jarvis lists capabilities — no agent called |

---

## Checklist

```
[ ] 1.1  Create basic task
[ ] 1.2  Create task with priority
[ ] 1.3  Create task with category + time
[ ] 1.4  List pending tasks
[ ] 1.5  List all tasks
[ ] 1.6  Complete a task
[ ] 1.7  Delete a task

[ ] 2.1  Web search
[ ] 2.2  Timezone query
[ ] 2.3  Factual question
[ ] 2.4  Tutorial search

[ ] 3.1  Save note
[ ] 3.2  Save pinned note with category
[ ] 3.3  Search notes (semantic)
[ ] 3.4  List notes
[ ] 3.5  Delete note

[ ] 4.1  Save contact with phone (check encryption)
[ ] 4.2  Save contact with email + birthday
[ ] 4.3  Update contact context
[ ] 4.4  Find contact (check decryption)
[ ] 4.5  List contacts
[ ] 4.6  Update contact email
[ ] 4.7  Delete contact

[ ] 5.1  Save opinion thought
[ ] 5.2  Save idea thought
[ ] 5.3  Save random thought
[ ] 5.4  Save private thought (check encryption)
[ ] 5.5  Search thoughts (semantic)
[ ] 5.6  List by type
[ ] 5.7  List all thoughts
[ ] 5.8  Pin thought
[ ] 5.9  Delete thought

[ ] 6.1  Store password (check: response doesn't show value)
[ ] 6.2  Store WiFi password
[ ] 6.3  Store PIN
[ ] 6.4  Retrieve password
[ ] 6.5  List secrets (check: no values shown)
[ ] 6.6  Delete secret

[ ] 7.1  Learn preference
[ ] 7.2  Learn relationship fact
[ ] 7.3  Learn habit
[ ] 7.4  Confidence boost (repeat fact)
[ ] 7.5  Recall by category
[ ] 7.6  Recall semantic search
[ ] 7.7  Forget a memory

[ ] 8.1  Schedule a reminder
[ ] 8.2  Verify reminder fires (check Telegram)
[ ] 8.3  Schedule birthday message
[ ] 8.4  Schedule recurring task
[ ] 8.5  List schedules
[ ] 8.6  Cancel schedule

[ ] M1   Multi-agent: contact + schedule
[ ] M2   Multi-agent: research + notes
[ ] M3   Multi-agent: memory + task
[ ] M4   Multi-agent: thoughts + research

[ ] S1   Direct greeting
[ ] S2   Identity question
[ ] S3   Thank you
[ ] S4   Capabilities question

[ ] SEC  Verify phone_enc is encrypted in DB
[ ] SEC  Verify value_enc is encrypted in vault
[ ] SEC  Verify private thought content is encrypted
[ ] SEC  Verify Jarvis doesn't repeat passwords in responses
```
