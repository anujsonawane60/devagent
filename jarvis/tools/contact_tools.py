from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.db.repositories import ContactRepo
from jarvis.tools import get_user_context


@tool
async def save_contact(
    name: str,
    relationship: str = "",
    phone: str = "",
    email: str = "",
    birthday: str = "",
    context: str = "",
    *,
    config: RunnableConfig,
) -> str:
    """Save a new contact. Phone/email are stored encrypted. Birthday format: YYYY-MM-DD.
    Context is free text about the person (e.g., 'college friend, works at Google')."""
    ctx = get_user_context(config)

    # Check if contact already exists
    existing = await ContactRepo.find_by_name(ctx.user_id, name)
    if existing:
        # Update existing contact with new info
        updates = {}
        if phone:
            updates["phone"] = phone
        if email:
            updates["email"] = email
        if birthday:
            updates["birthday"] = birthday
        if relationship:
            updates["relationship"] = relationship
        if context:
            updates["context"] = context
        if updates:
            await ContactRepo.update(ctx.user_id, existing["id"], **updates)
            return f"Updated {name}'s contact info."
        return f"{name} is already saved."

    await ContactRepo.create(
        user_id=ctx.user_id,
        name=name,
        relationship=relationship or None,
        phone=phone or None,
        email=email or None,
        birthday=birthday or None,
        context=context or None,
    )
    return f"Contact saved: {name}" + (f" ({relationship})" if relationship else "")


@tool
async def find_contact(name: str, *, config: RunnableConfig) -> str:
    """Find a contact by name. Returns their info (phone, email, birthday, etc.)."""
    ctx = get_user_context(config)
    contact = await ContactRepo.find_by_name(ctx.user_id, name)
    if not contact:
        return f"No contact found matching '{name}'."

    lines = [f"**{contact['name']}**"]
    if contact.get("relationship"):
        lines.append(f"Relationship: {contact['relationship']}")
    if contact.get("phone"):
        lines.append(f"Phone: {contact['phone']}")
    if contact.get("email"):
        lines.append(f"Email: {contact['email']}")
    if contact.get("birthday"):
        lines.append(f"Birthday: {contact['birthday']}")
    if contact.get("context"):
        lines.append(f"Context: {contact['context']}")
    return "\n".join(lines)


@tool
async def update_contact(
    name: str,
    phone: str = "",
    email: str = "",
    birthday: str = "",
    relationship: str = "",
    context: str = "",
    *,
    config: RunnableConfig,
) -> str:
    """Update an existing contact's info. Only provided fields are updated."""
    ctx = get_user_context(config)
    contact = await ContactRepo.find_by_name(ctx.user_id, name)
    if not contact:
        return f"No contact found matching '{name}'."

    updates = {}
    if phone:
        updates["phone"] = phone
    if email:
        updates["email"] = email
    if birthday:
        updates["birthday"] = birthday
    if relationship:
        updates["relationship"] = relationship
    if context:
        updates["context"] = context

    if not updates:
        return "No fields to update."

    await ContactRepo.update(ctx.user_id, contact["id"], **updates)
    return f"Updated {contact['name']}'s info."


@tool
async def list_contacts(*, config: RunnableConfig) -> str:
    """List all saved contacts (names and relationships)."""
    ctx = get_user_context(config)
    contacts = await ContactRepo.list_all(ctx.user_id)
    if not contacts:
        return "No contacts saved yet."
    lines = []
    for c in contacts:
        line = f"- {c['name']}"
        if c.get("relationship"):
            line += f" ({c['relationship']})"
        if c.get("birthday"):
            line += f" | Birthday: {c['birthday']}"
        lines.append(line)
    return "\n".join(lines)


@tool
async def delete_contact(name: str, *, config: RunnableConfig) -> str:
    """Delete a contact by name. This permanently removes all their info."""
    ctx = get_user_context(config)
    contact = await ContactRepo.find_by_name(ctx.user_id, name)
    if not contact:
        return f"No contact found matching '{name}'."
    await ContactRepo.delete(ctx.user_id, contact["id"])
    return f"Deleted contact: {contact['name']}"
