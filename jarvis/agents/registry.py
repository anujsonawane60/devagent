import importlib
import logging

from jarvis.core.base_agent import AgentDefinition

logger = logging.getLogger(__name__)

# Modules that export get_agent_definition(). Add new agents here.
AGENT_MODULES = [
    "jarvis.agents.task_agent",
    "jarvis.agents.research_agent",
    "jarvis.agents.notes_agent",
    "jarvis.agents.contacts_agent",
    "jarvis.agents.thoughts_agent",
    "jarvis.agents.vault_agent",
    "jarvis.agents.memory_agent",
    "jarvis.agents.scheduler_agent",
]


class AgentRegistry:
    """Discovers and manages sub-agent definitions."""

    def __init__(self):
        self._agents: dict[str, AgentDefinition] = {}

    def register(self, defn: AgentDefinition):
        self._agents[defn.name] = defn
        logger.info(f"Registered agent: {defn.name}")

    def get(self, name: str) -> AgentDefinition:
        return self._agents[name]

    def get_all(self) -> list[AgentDefinition]:
        return list(self._agents.values())

    def auto_discover(self):
        """Import all agent modules and collect their definitions."""
        for module_path in AGENT_MODULES:
            try:
                mod = importlib.import_module(module_path)
                defn = mod.get_agent_definition()
                self.register(defn)
            except Exception as e:
                logger.error(f"Failed to load agent from {module_path}: {e}")
