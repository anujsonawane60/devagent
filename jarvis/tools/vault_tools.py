from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.db.repositories import VaultRepo
from jarvis.tools import get_user_context


@tool
async def store_secret(
    label: str,
    value: str,
    category: str = "general",
    notes: str = "",
    *,
    config: RunnableConfig,
) -> str:
    """Store a secret securely (password, PIN, API key, etc.). The value is encrypted with AES-256.
    Category can be: password, pin, key, secret, personal, general.
    IMPORTANT: Never include the actual secret value in your response to the user."""
    ctx = get_user_context(config)
    await VaultRepo.store(ctx.user_id, label, value, category, notes or None)
    return f"Securely saved: {label} ({category})"


@tool
async def get_secret(label: str, *, config: RunnableConfig) -> str:
    """Retrieve a stored secret by label. The value is decrypted from the vault.
    IMPORTANT: When returning the value to the user, present it carefully — do not repeat it
    unnecessarily or include it in summaries."""
    ctx = get_user_context(config)
    entry = await VaultRepo.retrieve(ctx.user_id, label)
    if not entry:
        return f"No secret found matching '{label}'."
    result = f"**{entry['label']}** ({entry['category']})\nValue: {entry['value']}"
    if entry.get("notes"):
        result += f"\nNotes: {entry['notes']}"
    return result


@tool
async def list_secrets(*, config: RunnableConfig) -> str:
    """List all stored secrets (labels and categories only — values are NOT shown)."""
    ctx = get_user_context(config)
    entries = await VaultRepo.list_labels(ctx.user_id)
    if not entries:
        return "No secrets stored in the vault."
    lines = []
    for e in entries:
        line = f"- {e['label']} ({e['category']})"
        if e.get("notes"):
            line += f" — {e['notes']}"
        lines.append(line)
    return "\n".join(lines)


@tool
async def delete_secret(label: str, *, config: RunnableConfig) -> str:
    """Permanently delete a stored secret by label. This cannot be undone."""
    ctx = get_user_context(config)
    entry = await VaultRepo.retrieve(ctx.user_id, label)
    if not entry:
        return f"No secret found matching '{label}'."
    await VaultRepo.delete(ctx.user_id, entry["id"])
    return f"Deleted secret: {entry['label']}"
