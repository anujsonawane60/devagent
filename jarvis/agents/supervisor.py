import logging
import time

from langgraph_supervisor import create_supervisor
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from jarvis.agents.registry import AgentRegistry
from jarvis.core.context import UserContext
from jarvis.core.llm_factory import create_llm, create_llm_for_agent
from jarvis.db.repositories import ConversationRepo
from jarvis.config import settings

logger = logging.getLogger(__name__)

SUPERVISOR_PROMPT = """You are JARVIS, a highly capable personal AI assistant — intelligent, proactive, and loyal.

Your personality:
- Speak with confidence and clarity, like a trusted advisor
- Be concise but thorough. No filler, no fluff
- Use a warm but professional tone — helpful without being overly casual
- If you're unsure about something, say so honestly

You coordinate specialized agents to help the user. Delegate tasks to the right agent — the user should never be aware of internal delegation.

Rules:
- For simple greetings, small talk, or general questions you can answer yourself — respond directly. Do NOT delegate these.
- For capability-specific requests, delegate to the appropriate agent.
- If a request spans multiple agents, delegate to them sequentially.
- Always present the final response naturally, as if YOU did the work.
- Never mention agent names or delegation mechanics to the user."""


_supervisor_graph = None


def build_supervisor():
    """Build the supervisor graph with all registered sub-agents."""
    global _supervisor_graph

    registry = AgentRegistry()
    registry.auto_discover()

    # Build each sub-agent with its own (or default) LLM
    sub_agents = []
    for defn in registry.get_all():
        llm = create_llm_for_agent(defn.name)
        agent = defn.build(llm)
        sub_agents.append(agent)
        logger.info(f"Built sub-agent: {defn.name}")

    # Build supervisor
    supervisor_llm = create_llm()
    workflow = create_supervisor(
        agents=sub_agents,
        model=supervisor_llm,
        prompt=SUPERVISOR_PROMPT,
        supervisor_name="jarvis",
        output_mode="full_history",
    )
    _supervisor_graph = workflow.compile()
    logger.info(f"Supervisor built with {len(sub_agents)} sub-agents")
    return _supervisor_graph


def get_supervisor():
    """Get or build the supervisor graph (singleton)."""
    global _supervisor_graph
    if _supervisor_graph is None:
        build_supervisor()
    return _supervisor_graph


async def run_supervisor(ctx: UserContext, user_message: str) -> str:
    """Run the supervisor graph for a user message."""
    graph = get_supervisor()

    # Load conversation history
    history = await ConversationRepo.get_history(ctx.chat_id, settings.MEMORY_WINDOW)
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_message))

    # Save user message
    await ConversationRepo.save_message(ctx.user_id, ctx.chat_id, "user", user_message)

    # Run with user context
    config = {
        "configurable": {
            "user_context": ctx.to_dict(),
            "thread_id": ctx.chat_id,
        }
    }

    start_time = time.time()
    result = await graph.ainvoke({"messages": messages}, config=config)
    duration_ms = int((time.time() - start_time) * 1000)

    # Extract the final AI response
    response = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            response = msg.content
            break

    if not response:
        response = "I'm sorry, I couldn't process that request. Could you try rephrasing?"

    # Save assistant response
    await ConversationRepo.save_message(ctx.user_id, ctx.chat_id, "assistant", response)

    logger.info(f"[{ctx.user_id}] Supervisor completed in {duration_ms}ms")
    return response
