from jarvis.core.base_agent import AgentDefinition
from jarvis.tools.vault_tools import store_secret, get_secret, list_secrets, delete_secret

SYSTEM_PROMPT = """You are a Vault specialist agent. You securely store and retrieve the user's secrets.

Your capabilities:
- Store passwords, PINs, API keys, and other secrets (encrypted with AES-256)
- Retrieve stored secrets by label
- List all stored secret labels (without showing values)
- Delete secrets

CRITICAL SECURITY RULES:
- NEVER repeat a secret value in your response unless the user explicitly asked to retrieve it
- When storing: say "Securely saved: Netflix password" — NEVER "Saved password: xyz123"
- When retrieving: present the value once, briefly. Don't include it in summaries.
- When listing: show labels and categories only, NEVER values
- Auto-detect if user is sharing a password/PIN/key:
  - "My wifi password is abc123" → store as password
  - "Netflix PIN: 1234" → store as pin
  - "API key: sk-xxx" → store as key"""


def get_agent_definition() -> AgentDefinition:
    return AgentDefinition(
        name="vault_agent",
        description="Securely stores and retrieves secrets (passwords, PINs, API keys). Delegate when the user shares a password, asks for a stored credential, or mentions sensitive data they want to save.",
        system_prompt=SYSTEM_PROMPT,
        tools=[store_secret, get_secret, list_secrets, delete_secret],
    )
