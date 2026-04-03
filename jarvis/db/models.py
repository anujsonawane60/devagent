"""
Data models for Jarvis — the complete personal AI storage layer.

Every model maps 1:1 to a database table. Fields with `_enc` suffix
are stored encrypted (AES-256) and decrypted transparently by repositories.

All user-facing tables include `user_id` for data isolation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────────────────────────
#  IDENTITY — Who is the user?
# ─────────────────────────────────────────────────────────────────


@dataclass
class User:
    """A person using Jarvis. One row per platform identity."""

    id: str                             # platform-specific ID (e.g., Telegram user ID)
    platform: str                       # "telegram", "cli", "discord"
    username: Optional[str] = None
    display_name: Optional[str] = None
    timezone: str = "UTC"               # user's preferred timezone
    language: str = "en"                # preferred language code
    preferences: dict = field(default_factory=dict)  # JSON blob: {"theme": "dark", ...}
    is_authorized: bool = False
    created_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    TABLE = "users"


# ─────────────────────────────────────────────────────────────────
#  PEOPLE — Who does the user know?
# ─────────────────────────────────────────────────────────────────


@dataclass
class Contact:
    """A person in the user's life. Sensitive fields are encrypted."""

    id: Optional[int] = None
    user_id: str = ""

    # Identity (plaintext — LLM needs these for lookup)
    name: str = ""                      # "Satyajit"
    nickname: Optional[str] = None      # "Satya"
    relationship: Optional[str] = None  # "friend", "mom", "colleague", "boss"

    # Sensitive fields (encrypted in DB, LLM never sees raw values)
    phone_enc: Optional[str] = None     # encrypted phone number
    email_enc: Optional[str] = None     # encrypted email
    address_enc: Optional[str] = None   # encrypted address

    # Life events
    birthday: Optional[str] = None      # "2000-05-15" (YYYY-MM-DD)
    anniversary: Optional[str] = None   # "2022-06-20"

    # Free-text context (helps Jarvis understand the relationship)
    # e.g., "College friend, works at Google, lives in Bangalore"
    context: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    TABLE = "contacts"
    ENCRYPTED_FIELDS = ("phone_enc", "email_enc", "address_enc")


# ─────────────────────────────────────────────────────────────────
#  PRODUCTIVITY — What does the user need to do?
# ─────────────────────────────────────────────────────────────────


@dataclass
class Task:
    """A to-do item, reminder, or action the user needs to take."""

    id: Optional[int] = None
    user_id: str = ""

    title: str = ""
    description: Optional[str] = None

    # Priority & organization
    priority: str = "medium"            # "low", "medium", "high", "urgent"
    category: Optional[str] = None      # "work", "personal", "health", etc.

    # Timing
    due_date: Optional[str] = None      # "2026-04-01"
    due_time: Optional[str] = None      # "14:30" (HH:MM)

    # Recurrence
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None  # "daily", "weekly:mon,fri", "monthly:15"

    # Status
    status: str = "pending"             # "pending", "in_progress", "completed", "cancelled"
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    TABLE = "tasks"


# ─────────────────────────────────────────────────────────────────
#  KNOWLEDGE — Structured notes
# ─────────────────────────────────────────────────────────────────


@dataclass
class Note:
    """A structured, titled piece of knowledge the user intentionally saves."""

    id: Optional[int] = None
    user_id: str = ""

    title: str = ""
    content: str = ""
    category: Optional[str] = None      # "work", "personal", "tech", etc.
    is_pinned: bool = False

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    TABLE = "notes"


# ─────────────────────────────────────────────────────────────────
#  THOUGHTS — Quick captures, the brain dump  ★ KEY FEATURE
# ─────────────────────────────────────────────────────────────────


@dataclass
class Thought:
    """
    An unstructured, zero-friction capture of anything on the user's mind.

    Unlike Notes (structured, titled), Thoughts are quick dumps:
      - "I think I should learn Rust"
      - "Pizza place on MG Road was amazing"
      - "Satyajit said he's moving to Bangalore"
      - "idea: habit tracker app"

    Jarvis auto-classifies the thought_type and can auto-link to contacts,
    suggest tags, or detect if it should go to the Vault instead.
    """

    id: Optional[int] = None
    user_id: str = ""

    content: str = ""                   # the actual thought (the only required field)

    # Auto-classification by Jarvis
    thought_type: str = "random"        # "idea", "opinion", "fact", "random",
                                        # "bookmark", "quote", "snippet", "question"

    mood: Optional[str] = None          # "happy", "frustrated", "curious", "excited" (optional)
    source: str = "telegram"            # which interface captured it

    # Flags
    is_pinned: bool = False
    is_private: bool = False            # extra-sensitive, encrypt content too

    # Linking — if the thought mentions a known contact
    linked_contact_id: Optional[int] = None  # FK to contacts.id

    created_at: Optional[datetime] = None

    TABLE = "thoughts"


# ─────────────────────────────────────────────────────────────────
#  TAGS — Universal tagging system
# ─────────────────────────────────────────────────────────────────


@dataclass
class Tag:
    """A label that can be attached to any entity (thought, note, task, contact)."""

    id: Optional[int] = None
    user_id: str = ""

    name: str = ""                      # "work", "personal", "tech", "food"
    color: Optional[str] = None         # hex color for UI: "#FF5733"

    created_at: Optional[datetime] = None

    TABLE = "tags"


@dataclass
class Taggable:
    """
    Junction table: connects a Tag to any entity.

    entity_type + entity_id = polymorphic FK.
    Example: tag "work" → entity_type="task", entity_id=5
             tag "food" → entity_type="thought", entity_id=12
    """

    id: Optional[int] = None
    tag_id: int = 0
    entity_type: str = ""               # "thought", "note", "task", "contact"
    entity_id: int = 0

    TABLE = "taggables"


# ─────────────────────────────────────────────────────────────────
#  VAULT — Encrypted secrets
# ─────────────────────────────────────────────────────────────────


@dataclass
class VaultEntry:
    """
    Sensitive data the user wants to store securely.

    The value is ALWAYS encrypted. The LLM never sees the raw value.
    When user asks "what's my Netflix password?", the tool reads from
    vault, decrypts, and returns it — the LLM only sees "Retrieved
    credential for Netflix" in the conversation.

    Examples:
      - label="Netflix password", value_enc=encrypt("xyz123")
      - label="Home WiFi", value_enc=encrypt("MyWifi@456")
      - label="Bank PIN", value_enc=encrypt("1234")
    """

    id: Optional[int] = None
    user_id: str = ""

    label: str = ""                     # "Netflix password", "WiFi", "Bank PIN"
    value_enc: str = ""                 # ALWAYS encrypted (AES-256)
    category: str = "general"           # "password", "pin", "key", "secret", "personal"
    notes: Optional[str] = None         # non-sensitive context: "for home router"

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    TABLE = "vault"
    ENCRYPTED_FIELDS = ("value_enc",)


# ─────────────────────────────────────────────────────────────────
#  MEMORY — What Jarvis learns over time (auto-extracted)
# ─────────────────────────────────────────────────────────────────


@dataclass
class Memory:
    """
    A fact Jarvis has learned about the user from conversations.
    These are NOT user-created — Jarvis creates them by observing patterns.

    Examples:
      - fact="User prefers Python over Java" (category=preference)
      - fact="User's mom's name is Sunita" (category=fact)
      - fact="User wakes up at 6 AM" (category=habit)
      - fact="User dislikes long meetings" (category=opinion)

    Confidence increases when the same fact is observed multiple times.
    """

    id: Optional[int] = None
    user_id: str = ""

    fact: str = ""                      # "User prefers dark mode"
    category: str = "fact"              # "preference", "fact", "opinion", "habit", "relationship"
    confidence: float = 0.5             # 0.0 → 1.0, increases with repetition

    # Provenance: where did Jarvis learn this?
    source_conversation_id: Optional[int] = None  # FK to conversations.id

    created_at: Optional[datetime] = None
    last_confirmed: Optional[datetime] = None  # last time this fact was reaffirmed

    TABLE = "memories"


# ─────────────────────────────────────────────────────────────────
#  SCHEDULE — Future actions
# ─────────────────────────────────────────────────────────────────


@dataclass
class ScheduledJob:
    """
    An action to be executed at a future time.

    Examples:
      - Send birthday wishes to Satyajit at 2026-04-01 00:00
      - Remind user to take medicine every day at 08:00
      - Send weekly report every Monday at 09:00
    """

    id: Optional[int] = None
    user_id: str = ""

    action_type: str = ""               # "send_message", "reminder", "recurring_task"
    description: str = ""               # human-readable: "Birthday wishes to Satyajit"

    # What to do (JSON blob with action-specific data)
    # e.g., {"contact_id": 5, "message": "Happy Birthday!"}
    payload: dict = field(default_factory=dict)

    # Who it targets (if applicable)
    target_contact_id: Optional[int] = None  # FK to contacts.id

    # When
    scheduled_at: Optional[str] = None  # ISO datetime: "2026-04-01T00:00:00"
    recurrence_rule: Optional[str] = None  # "daily", "weekly:mon", "yearly:04-01"

    # Status
    status: str = "pending"             # "pending", "completed", "failed", "cancelled"

    created_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None

    TABLE = "scheduled_jobs"


# ─────────────────────────────────────────────────────────────────
#  CONVERSATIONS — Chat history
# ─────────────────────────────────────────────────────────────────


@dataclass
class Conversation:
    """A single message in a conversation thread."""

    id: Optional[int] = None
    user_id: str = ""
    chat_id: str = ""                   # thread identifier
    role: str = ""                      # "user", "assistant"
    content: str = ""
    is_redacted: bool = False           # True if sensitive data was stripped

    created_at: Optional[datetime] = None

    TABLE = "conversations"


# ─────────────────────────────────────────────────────────────────
#  SOCIAL MEDIA — Content management (SSM Agent)
# ─────────────────────────────────────────────────────────────────


@dataclass
class SocialPost:
    """
    A social media post generated by the SSM agent.

    Stores generated content per platform with full edit history.
    The user reviews, edits, and manually posts — Jarvis generates.
    """

    id: Optional[int] = None
    user_id: str = ""

    # Content
    platform: str = ""                  # "linkedin", "instagram", "facebook", "twitter"
    content: str = ""                   # the generated post text
    hashtags: Optional[str] = None      # comma-separated: "#AI,#Tech,#Startup"
    media_suggestion: Optional[str] = None  # AI-suggested image/visual description
    call_to_action: Optional[str] = None    # suggested CTA text

    # Context
    topic: Optional[str] = None         # original topic/prompt from user
    tone: str = "professional"          # "professional", "casual", "inspirational", "humorous"
    target_audience: Optional[str] = None  # "developers", "founders", "general"

    # Status
    status: str = "draft"               # "draft", "approved", "posted", "archived"
    is_pinned: bool = False

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None

    TABLE = "ssm_posts"


# ─────────────────────────────────────────────────────────────────
#  SYSTEM — Logs & analytics
# ─────────────────────────────────────────────────────────────────


@dataclass
class AgentLog:
    """Execution log for agent runs — debugging and performance tracking."""

    id: Optional[int] = None
    user_id: str = ""
    agent_name: str = ""
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    tools_used: Optional[str] = None    # comma-separated tool names
    duration_ms: Optional[int] = None

    created_at: Optional[datetime] = None

    TABLE = "agent_logs"


# ─────────────────────────────────────────────────────────────────
#  MODEL REGISTRY — for programmatic access
# ─────────────────────────────────────────────────────────────────

ALL_MODELS = [
    User,
    Contact,
    Task,
    Note,
    Thought,
    Tag,
    Taggable,
    VaultEntry,
    Memory,
    ScheduledJob,
    Conversation,
    AgentLog,
    SocialPost,
]
