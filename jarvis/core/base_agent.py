from dataclasses import dataclass, field
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent


@dataclass
class AgentDefinition:
    """Blueprint for a sub-agent. Each agent module exports one via get_agent_definition()."""

    name: str  # e.g., "task_agent"
    description: str  # Used by supervisor prompt for routing decisions
    system_prompt: str
    tools: list[BaseTool]
    llm_config: dict = field(default_factory=dict)  # Per-agent LLM override

    def build(self, llm) -> "CompiledGraph":
        """Build a compiled LangGraph agent from this definition."""
        agent = create_react_agent(llm, self.tools, prompt=self.system_prompt)
        agent.name = self.name
        return agent
