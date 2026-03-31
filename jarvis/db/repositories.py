"""
Repository classes for all data models.

Each repo handles CRUD operations scoped by user_id.
Sensitive fields are encrypted/decrypted transparently — callers
never see ciphertext.
"""

import json
from jarvis.db.database import get_db
from jarvis.db.encryption import encrypt, decrypt
from jarvis.db.vector_store import VectorStore


# ─────────────────────────────────────────────────────────────────
#  USERS
# ─────────────────────────────────────────────────────────────────


class UserRepo:
    @staticmethod
    async def upsert(
        user_id: str,
        platform: str,
        username: str | None = None,
        display_name: str | None = None,
    ):
        db = await get_db()
        await db.execute(
            """INSERT INTO users (id, platform, username, display_name)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   last_seen = CURRENT_TIMESTAMP,
                   username = COALESCE(excluded.username, users.username),
                   display_name = COALESCE(excluded.display_name, users.display_name)
            """,
            (user_id, platform, username, display_name),
        )
        await db.commit()

    @staticmethod
    async def get(user_id: str) -> dict | None:
        db = await get_db()
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        result = dict(row)
        result["preferences"] = json.loads(result.get("preferences") or "{}")
        return result

    @staticmethod
    async def update_preferences(user_id: str, preferences: dict):
        db = await get_db()
        await db.execute(
            "UPDATE users SET preferences = ? WHERE id = ?",
            (json.dumps(preferences), user_id),
        )
        await db.commit()

    @staticmethod
    async def update_timezone(user_id: str, timezone: str):
        db = await get_db()
        await db.execute(
            "UPDATE users SET timezone = ? WHERE id = ?", (timezone, user_id)
        )
        await db.commit()


# ─────────────────────────────────────────────────────────────────
#  CONVERSATIONS
# ─────────────────────────────────────────────────────────────────


class ConversationRepo:
    @staticmethod
    async def save_message(
        user_id: str,
        chat_id: str,
        role: str,
        content: str,
        is_redacted: bool = False,
    ):
        db = await get_db()
        await db.execute(
            "INSERT INTO conversations (user_id, chat_id, role, content, is_redacted) VALUES (?, ?, ?, ?, ?)",
            (user_id, chat_id, role, content, int(is_redacted)),
        )
        await db.commit()

    @staticmethod
    async def get_history(chat_id: str, limit: int = 20) -> list[dict]:
        db = await get_db()
        cursor = await db.execute(
            "SELECT role, content FROM conversations WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
            (chat_id, limit),
        )
        rows = await cursor.fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    @staticmethod
    async def clear_history(chat_id: str):
        db = await get_db()
        await db.execute("DELETE FROM conversations WHERE chat_id = ?", (chat_id,))
        await db.commit()


# ─────────────────────────────────────────────────────────────────
#  CONTACTS (encrypted fields)
# ─────────────────────────────────────────────────────────────────


class ContactRepo:
    @staticmethod
    async def create(
        user_id: str,
        name: str,
        nickname: str | None = None,
        relationship: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        birthday: str | None = None,
        anniversary: str | None = None,
        context: str | None = None,
    ) -> int:
        db = await get_db()
        cursor = await db.execute(
            """INSERT INTO contacts
               (user_id, name, nickname, relationship, phone_enc, email_enc, address_enc,
                birthday, anniversary, context)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id, name, nickname, relationship,
                encrypt(phone) if phone else None,
                encrypt(email) if email else None,
                encrypt(address) if address else None,
                birthday, anniversary, context,
            ),
        )
        await db.commit()
        contact_id = cursor.lastrowid

        # Index in vector store (name + relationship + context for semantic search)
        embed_text = f"{name}"
        if relationship:
            embed_text += f" ({relationship})"
        if context:
            embed_text += f" - {context}"
        await VectorStore.store(user_id, "contact", contact_id, embed_text)

        return contact_id

    @staticmethod
    async def find_by_name(user_id: str, name: str) -> dict | None:
        """Find a contact by name (case-insensitive partial match)."""
        db = await get_db()
        cursor = await db.execute(
            """SELECT * FROM contacts
               WHERE user_id = ? AND (name LIKE ? OR nickname LIKE ?)
               LIMIT 1""",
            (user_id, f"%{name}%", f"%{name}%"),
        )
        row = await cursor.fetchone()
        return _decrypt_contact(dict(row)) if row else None

    @staticmethod
    async def get(user_id: str, contact_id: int) -> dict | None:
        db = await get_db()
        cursor = await db.execute(
            "SELECT * FROM contacts WHERE id = ? AND user_id = ?",
            (contact_id, user_id),
        )
        row = await cursor.fetchone()
        return _decrypt_contact(dict(row)) if row else None

    @staticmethod
    async def list_all(user_id: str, limit: int = 50) -> list[dict]:
        """List contacts (names + relationship only, no sensitive data)."""
        db = await get_db()
        cursor = await db.execute(
            "SELECT id, name, nickname, relationship, birthday FROM contacts WHERE user_id = ? ORDER BY name",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    async def update(user_id: str, contact_id: int, **fields) -> bool:
        """Update contact fields. Pass phone/email/address as plaintext — encrypted here."""
        encrypt_map = {"phone": "phone_enc", "email": "email_enc", "address": "address_enc"}
        updates = []
        values = []
        for key, val in fields.items():
            if key in encrypt_map:
                updates.append(f"{encrypt_map[key]} = ?")
                values.append(encrypt(val) if val else None)
            else:
                updates.append(f"{key} = ?")
                values.append(val)
        if not updates:
            return False
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.extend([contact_id, user_id])
        db = await get_db()
        cursor = await db.execute(
            f"UPDATE contacts SET {', '.join(updates)} WHERE id = ? AND user_id = ?",
            values,
        )
        await db.commit()
        return cursor.rowcount > 0

    @staticmethod
    async def delete(user_id: str, contact_id: int) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "DELETE FROM contacts WHERE id = ? AND user_id = ?",
            (contact_id, user_id),
        )
        await db.commit()
        if cursor.rowcount > 0:
            await VectorStore.delete(user_id, "contact", contact_id)
            return True
        return False


def _decrypt_contact(row: dict) -> dict:
    """Decrypt sensitive fields in a contact row."""
    row["phone"] = decrypt(row.pop("phone_enc", "") or "")
    row["email"] = decrypt(row.pop("email_enc", "") or "")
    row["address"] = decrypt(row.pop("address_enc", "") or "")
    return row


# ─────────────────────────────────────────────────────────────────
#  TASKS (enhanced)
# ─────────────────────────────────────────────────────────────────


class TaskRepo:
    @staticmethod
    async def create(
        user_id: str,
        title: str,
        description: str | None = None,
        priority: str = "medium",
        category: str | None = None,
        due_date: str | None = None,
        due_time: str | None = None,
        is_recurring: bool = False,
        recurrence_rule: str | None = None,
    ) -> int:
        db = await get_db()
        cursor = await db.execute(
            """INSERT INTO tasks
               (user_id, title, description, priority, category, due_date, due_time,
                is_recurring, recurrence_rule)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, title, description, priority, category, due_date, due_time,
             int(is_recurring), recurrence_rule),
        )
        await db.commit()
        return cursor.lastrowid

    @staticmethod
    async def list_tasks(user_id: str, status: str = "pending") -> list[dict]:
        db = await get_db()
        if status == "all":
            cursor = await db.execute(
                "SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM tasks WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                (user_id, status),
            )
        return [dict(row) for row in await cursor.fetchall()]

    @staticmethod
    async def complete(user_id: str, task_id: int) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "UPDATE tasks SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0

    @staticmethod
    async def update(user_id: str, task_id: int, **fields) -> bool:
        updates = [f"{k} = ?" for k in fields]
        if not updates:
            return False
        values = list(fields.values()) + [task_id, user_id]
        db = await get_db()
        cursor = await db.execute(
            f"UPDATE tasks SET {', '.join(updates)} WHERE id = ? AND user_id = ?",
            values,
        )
        await db.commit()
        return cursor.rowcount > 0

    @staticmethod
    async def delete(user_id: str, task_id: int) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


# ─────────────────────────────────────────────────────────────────
#  NOTES
# ─────────────────────────────────────────────────────────────────


class NoteRepo:
    @staticmethod
    async def save(
        user_id: str,
        title: str,
        content: str,
        category: str | None = None,
        is_pinned: bool = False,
    ) -> int:
        db = await get_db()
        cursor = await db.execute(
            "INSERT INTO notes (user_id, title, content, category, is_pinned) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, content, category, int(is_pinned)),
        )
        await db.commit()
        note_id = cursor.lastrowid

        # Index in vector store
        embed_text = f"{title}: {content}" if title else content
        await VectorStore.store(user_id, "note", note_id, embed_text,
                                metadata={"category": category or ""})
        return note_id

    @staticmethod
    async def search(user_id: str, query: str, limit: int = 10) -> list[dict]:
        db = await get_db()
        cursor = await db.execute(
            """SELECT id, title, content, category, is_pinned, created_at
               FROM notes WHERE user_id = ? AND (title LIKE ? OR content LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (user_id, f"%{query}%", f"%{query}%", limit),
        )
        return [dict(row) for row in await cursor.fetchall()]

    @staticmethod
    async def list_all(user_id: str, limit: int = 20) -> list[dict]:
        db = await get_db()
        cursor = await db.execute(
            "SELECT id, title, category, is_pinned, created_at FROM notes WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(row) for row in await cursor.fetchall()]

    @staticmethod
    async def update(user_id: str, note_id: int, **fields) -> bool:
        updates = [f"{k} = ?" for k in fields]
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values = list(fields.values()) + [note_id, user_id]
        db = await get_db()
        cursor = await db.execute(
            f"UPDATE notes SET {', '.join(updates)} WHERE id = ? AND user_id = ?",
            values,
        )
        await db.commit()
        return cursor.rowcount > 0

    @staticmethod
    async def delete(user_id: str, note_id: int) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id)
        )
        await db.commit()
        if cursor.rowcount > 0:
            await VectorStore.delete(user_id, "note", note_id)
            return True
        return False

    @staticmethod
    async def smart_search(user_id: str, query: str, limit: int = 10) -> list[dict]:
        """SQL keyword search + vector semantic search, merged and deduplicated."""
        # Step 1: SQL exact search
        sql_results = await NoteRepo.search(user_id, query, limit)
        seen_ids = {r["id"] for r in sql_results}

        # Step 2: Vector semantic search (fills the gap)
        if len(sql_results) < limit:
            vector_hits = await VectorStore.search(user_id, query, entity_type="note", limit=limit)
            for hit in vector_hits:
                eid = hit["entity_id"]
                if eid not in seen_ids:
                    db = await get_db()
                    cursor = await db.execute(
                        "SELECT id, title, content, category, is_pinned, created_at FROM notes WHERE id = ? AND user_id = ?",
                        (eid, user_id),
                    )
                    row = await cursor.fetchone()
                    if row:
                        result = dict(row)
                        result["_relevance"] = hit["score"]
                        sql_results.append(result)
                        seen_ids.add(eid)

        return sql_results[:limit]


# ─────────────────────────────────────────────────────────────────
#  THOUGHTS ★
# ─────────────────────────────────────────────────────────────────


class ThoughtRepo:
    @staticmethod
    async def save(
        user_id: str,
        content: str,
        thought_type: str = "random",
        mood: str | None = None,
        source: str = "telegram",
        is_pinned: bool = False,
        is_private: bool = False,
        linked_contact_id: int | None = None,
    ) -> int:
        # If private, encrypt the content too
        stored_content = encrypt(content) if is_private else content
        db = await get_db()
        cursor = await db.execute(
            """INSERT INTO thoughts
               (user_id, content, thought_type, mood, source, is_pinned, is_private, linked_contact_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, stored_content, thought_type, mood, source,
             int(is_pinned), int(is_private), linked_contact_id),
        )
        await db.commit()
        thought_id = cursor.lastrowid

        # Index in vector store (use original plaintext, not encrypted)
        # Private thoughts still get indexed (vectors don't expose raw text)
        await VectorStore.store(user_id, "thought", thought_id, content,
                                metadata={"thought_type": thought_type})

        return thought_id

    @staticmethod
    async def search(user_id: str, query: str, limit: int = 20) -> list[dict]:
        """Search non-private thoughts by content."""
        db = await get_db()
        cursor = await db.execute(
            """SELECT * FROM thoughts
               WHERE user_id = ? AND is_private = 0 AND content LIKE ?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, f"%{query}%", limit),
        )
        return [dict(row) for row in await cursor.fetchall()]

    @staticmethod
    async def list_by_type(
        user_id: str, thought_type: str | None = None, limit: int = 20
    ) -> list[dict]:
        db = await get_db()
        if thought_type:
            cursor = await db.execute(
                "SELECT * FROM thoughts WHERE user_id = ? AND thought_type = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, thought_type, limit),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM thoughts WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
            )
        rows = [dict(row) for row in await cursor.fetchall()]
        # Decrypt private thoughts
        for row in rows:
            if row.get("is_private"):
                row["content"] = decrypt(row["content"])
        return rows

    @staticmethod
    async def get(user_id: str, thought_id: int) -> dict | None:
        db = await get_db()
        cursor = await db.execute(
            "SELECT * FROM thoughts WHERE id = ? AND user_id = ?",
            (thought_id, user_id),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        result = dict(row)
        if result.get("is_private"):
            result["content"] = decrypt(result["content"])
        return result

    @staticmethod
    async def pin(user_id: str, thought_id: int, pinned: bool = True) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "UPDATE thoughts SET is_pinned = ? WHERE id = ? AND user_id = ?",
            (int(pinned), thought_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0

    @staticmethod
    async def delete(user_id: str, thought_id: int) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "DELETE FROM thoughts WHERE id = ? AND user_id = ?",
            (thought_id, user_id),
        )
        await db.commit()
        if cursor.rowcount > 0:
            await VectorStore.delete(user_id, "thought", thought_id)
            return True
        return False

    @staticmethod
    async def smart_search(user_id: str, query: str, limit: int = 20) -> list[dict]:
        """SQL keyword search + vector semantic search, merged and deduplicated."""
        # Step 1: SQL exact search
        sql_results = await ThoughtRepo.search(user_id, query, limit)
        seen_ids = {r["id"] for r in sql_results}

        # Step 2: Vector semantic search
        if len(sql_results) < limit:
            vector_hits = await VectorStore.search(user_id, query, entity_type="thought", limit=limit)
            for hit in vector_hits:
                eid = hit["entity_id"]
                if eid not in seen_ids:
                    thought = await ThoughtRepo.get(user_id, eid)
                    if thought:
                        thought["_relevance"] = hit["score"]
                        sql_results.append(thought)
                        seen_ids.add(eid)

        return sql_results[:limit]


# ─────────────────────────────────────────────────────────────────
#  TAGS (universal tagging)
# ─────────────────────────────────────────────────────────────────


class TagRepo:
    @staticmethod
    async def get_or_create(user_id: str, name: str, color: str | None = None) -> int:
        """Get existing tag or create new one. Returns tag_id."""
        db = await get_db()
        cursor = await db.execute(
            "SELECT id FROM tags WHERE user_id = ? AND name = ?",
            (user_id, name.lower()),
        )
        row = await cursor.fetchone()
        if row:
            return row["id"]
        cursor = await db.execute(
            "INSERT INTO tags (user_id, name, color) VALUES (?, ?, ?)",
            (user_id, name.lower(), color),
        )
        await db.commit()
        return cursor.lastrowid

    @staticmethod
    async def tag_entity(tag_id: int, entity_type: str, entity_id: int):
        """Attach a tag to an entity."""
        db = await get_db()
        await db.execute(
            """INSERT OR IGNORE INTO taggables (tag_id, entity_type, entity_id)
               VALUES (?, ?, ?)""",
            (tag_id, entity_type, entity_id),
        )
        await db.commit()

    @staticmethod
    async def untag_entity(tag_id: int, entity_type: str, entity_id: int):
        db = await get_db()
        await db.execute(
            "DELETE FROM taggables WHERE tag_id = ? AND entity_type = ? AND entity_id = ?",
            (tag_id, entity_type, entity_id),
        )
        await db.commit()

    @staticmethod
    async def get_tags_for(user_id: str, entity_type: str, entity_id: int) -> list[dict]:
        """Get all tags attached to an entity."""
        db = await get_db()
        cursor = await db.execute(
            """SELECT t.id, t.name, t.color FROM tags t
               JOIN taggables tg ON t.id = tg.tag_id
               WHERE t.user_id = ? AND tg.entity_type = ? AND tg.entity_id = ?""",
            (user_id, entity_type, entity_id),
        )
        return [dict(row) for row in await cursor.fetchall()]

    @staticmethod
    async def find_by_tag(user_id: str, tag_name: str, entity_type: str | None = None) -> list[dict]:
        """Find all entities with a given tag."""
        db = await get_db()
        if entity_type:
            cursor = await db.execute(
                """SELECT tg.entity_type, tg.entity_id FROM taggables tg
                   JOIN tags t ON t.id = tg.tag_id
                   WHERE t.user_id = ? AND t.name = ? AND tg.entity_type = ?""",
                (user_id, tag_name.lower(), entity_type),
            )
        else:
            cursor = await db.execute(
                """SELECT tg.entity_type, tg.entity_id FROM taggables tg
                   JOIN tags t ON t.id = tg.tag_id
                   WHERE t.user_id = ? AND t.name = ?""",
                (user_id, tag_name.lower()),
            )
        return [dict(row) for row in await cursor.fetchall()]

    @staticmethod
    async def list_user_tags(user_id: str) -> list[dict]:
        db = await get_db()
        cursor = await db.execute(
            "SELECT id, name, color FROM tags WHERE user_id = ? ORDER BY name",
            (user_id,),
        )
        return [dict(row) for row in await cursor.fetchall()]


# ─────────────────────────────────────────────────────────────────
#  VAULT (encrypted secrets)
# ─────────────────────────────────────────────────────────────────


class VaultRepo:
    @staticmethod
    async def store(
        user_id: str,
        label: str,
        value: str,
        category: str = "general",
        notes: str | None = None,
    ) -> int:
        """Store a secret. Value is encrypted before writing."""
        db = await get_db()
        cursor = await db.execute(
            "INSERT INTO vault (user_id, label, value_enc, category, notes) VALUES (?, ?, ?, ?, ?)",
            (user_id, label, encrypt(value), category, notes),
        )
        await db.commit()
        return cursor.lastrowid

    @staticmethod
    async def retrieve(user_id: str, label: str) -> dict | None:
        """Retrieve and decrypt a secret by label."""
        db = await get_db()
        cursor = await db.execute(
            "SELECT * FROM vault WHERE user_id = ? AND label LIKE ? LIMIT 1",
            (user_id, f"%{label}%"),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        result = dict(row)
        result["value"] = decrypt(result.pop("value_enc"))
        return result

    @staticmethod
    async def list_labels(user_id: str) -> list[dict]:
        """List vault entries (labels + category only, NO values)."""
        db = await get_db()
        cursor = await db.execute(
            "SELECT id, label, category, notes, created_at FROM vault WHERE user_id = ? ORDER BY label",
            (user_id,),
        )
        return [dict(row) for row in await cursor.fetchall()]

    @staticmethod
    async def update(user_id: str, vault_id: int, value: str | None = None, **fields) -> bool:
        updates = []
        values = []
        if value is not None:
            updates.append("value_enc = ?")
            values.append(encrypt(value))
        for key, val in fields.items():
            updates.append(f"{key} = ?")
            values.append(val)
        if not updates:
            return False
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.extend([vault_id, user_id])
        db = await get_db()
        cursor = await db.execute(
            f"UPDATE vault SET {', '.join(updates)} WHERE id = ? AND user_id = ?",
            values,
        )
        await db.commit()
        return cursor.rowcount > 0

    @staticmethod
    async def delete(user_id: str, vault_id: int) -> bool:
        """Hard delete — gone forever."""
        db = await get_db()
        cursor = await db.execute(
            "DELETE FROM vault WHERE id = ? AND user_id = ?", (vault_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


# ─────────────────────────────────────────────────────────────────
#  MEMORIES (Jarvis's learned knowledge)
# ─────────────────────────────────────────────────────────────────


class MemoryRepo:
    @staticmethod
    async def learn(
        user_id: str,
        fact: str,
        category: str = "fact",
        confidence: float = 0.5,
        source_conversation_id: int | None = None,
    ) -> int:
        """Save a learned fact. If similar fact exists, boost confidence instead."""
        db = await get_db()
        # Check if we already know something similar
        cursor = await db.execute(
            "SELECT id, confidence FROM memories WHERE user_id = ? AND fact = ?",
            (user_id, fact),
        )
        existing = await cursor.fetchone()
        if existing:
            # Boost confidence (cap at 1.0)
            new_confidence = min(1.0, existing["confidence"] + 0.1)
            await db.execute(
                "UPDATE memories SET confidence = ?, last_confirmed = CURRENT_TIMESTAMP WHERE id = ?",
                (new_confidence, existing["id"]),
            )
            await db.commit()
            return existing["id"]

        cursor = await db.execute(
            """INSERT INTO memories (user_id, fact, category, confidence, source_conversation_id)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, fact, category, confidence, source_conversation_id),
        )
        await db.commit()
        memory_id = cursor.lastrowid

        # Index in vector store for semantic recall
        await VectorStore.store(user_id, "memory", memory_id, fact,
                                metadata={"category": category})

        return memory_id

    @staticmethod
    async def recall(user_id: str, query: str | None = None, category: str | None = None, limit: int = 20) -> list[dict]:
        """Recall learned facts, optionally filtered."""
        db = await get_db()
        conditions = ["user_id = ?"]
        params: list = [user_id]
        if query:
            conditions.append("fact LIKE ?")
            params.append(f"%{query}%")
        if category:
            conditions.append("category = ?")
            params.append(category)
        params.append(limit)
        cursor = await db.execute(
            f"SELECT * FROM memories WHERE {' AND '.join(conditions)} ORDER BY confidence DESC, last_confirmed DESC LIMIT ?",
            params,
        )
        return [dict(row) for row in await cursor.fetchall()]

    @staticmethod
    async def forget(user_id: str, memory_id: int) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "DELETE FROM memories WHERE id = ? AND user_id = ?",
            (memory_id, user_id),
        )
        await db.commit()
        if cursor.rowcount > 0:
            await VectorStore.delete(user_id, "memory", memory_id)
            return True
        return False

    @staticmethod
    async def smart_recall(user_id: str, query: str, limit: int = 10) -> list[dict]:
        """Recall memories using semantic search — finds by meaning, not just keywords."""
        # SQL first
        sql_results = await MemoryRepo.recall(user_id, query=query, limit=limit)
        seen_ids = {r["id"] for r in sql_results}

        # Vector search for semantic matches
        if len(sql_results) < limit:
            vector_hits = await VectorStore.search(user_id, query, entity_type="memory", limit=limit)
            for hit in vector_hits:
                eid = hit["entity_id"]
                if eid not in seen_ids:
                    db = await get_db()
                    cursor = await db.execute(
                        "SELECT * FROM memories WHERE id = ? AND user_id = ?", (eid, user_id)
                    )
                    row = await cursor.fetchone()
                    if row:
                        result = dict(row)
                        result["_relevance"] = hit["score"]
                        sql_results.append(result)
                        seen_ids.add(eid)

        return sql_results[:limit]


# ─────────────────────────────────────────────────────────────────
#  SCHEDULED JOBS
# ─────────────────────────────────────────────────────────────────


class ScheduledJobRepo:
    @staticmethod
    async def create(
        user_id: str,
        action_type: str,
        description: str = "",
        payload: dict | None = None,
        target_contact_id: int | None = None,
        scheduled_at: str | None = None,
        recurrence_rule: str | None = None,
    ) -> int:
        db = await get_db()
        cursor = await db.execute(
            """INSERT INTO scheduled_jobs
               (user_id, action_type, description, payload, target_contact_id,
                scheduled_at, recurrence_rule)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, action_type, description, json.dumps(payload or {}),
             target_contact_id, scheduled_at, recurrence_rule),
        )
        await db.commit()
        return cursor.lastrowid

    @staticmethod
    async def get_pending(user_id: str | None = None) -> list[dict]:
        """Get pending jobs. If user_id is None, returns all users' pending jobs (for scheduler daemon)."""
        db = await get_db()
        if user_id:
            cursor = await db.execute(
                "SELECT * FROM scheduled_jobs WHERE user_id = ? AND status = 'pending' ORDER BY scheduled_at",
                (user_id,),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM scheduled_jobs WHERE status = 'pending' ORDER BY scheduled_at"
            )
        rows = [dict(row) for row in await cursor.fetchall()]
        for row in rows:
            row["payload"] = json.loads(row.get("payload") or "{}")
        return rows

    @staticmethod
    async def get_due_jobs(before_datetime: str) -> list[dict]:
        """Get jobs that are due (scheduled_at <= given datetime). For the background scheduler."""
        db = await get_db()
        cursor = await db.execute(
            "SELECT * FROM scheduled_jobs WHERE status = 'pending' AND scheduled_at <= ? ORDER BY scheduled_at",
            (before_datetime,),
        )
        rows = [dict(row) for row in await cursor.fetchall()]
        for row in rows:
            row["payload"] = json.loads(row.get("payload") or "{}")
        return rows

    @staticmethod
    async def mark_completed(job_id: int) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "UPDATE scheduled_jobs SET status = 'completed', executed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (job_id,),
        )
        await db.commit()
        return cursor.rowcount > 0

    @staticmethod
    async def mark_failed(job_id: int) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "UPDATE scheduled_jobs SET status = 'failed', executed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (job_id,),
        )
        await db.commit()
        return cursor.rowcount > 0

    @staticmethod
    async def cancel(user_id: str, job_id: int) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "UPDATE scheduled_jobs SET status = 'cancelled' WHERE id = ? AND user_id = ?",
            (job_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0

    @staticmethod
    async def list_jobs(user_id: str, status: str | None = None) -> list[dict]:
        db = await get_db()
        if status:
            cursor = await db.execute(
                "SELECT * FROM scheduled_jobs WHERE user_id = ? AND status = ? ORDER BY scheduled_at",
                (user_id, status),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM scheduled_jobs WHERE user_id = ? ORDER BY scheduled_at DESC",
                (user_id,),
            )
        rows = [dict(row) for row in await cursor.fetchall()]
        for row in rows:
            row["payload"] = json.loads(row.get("payload") or "{}")
        return rows
