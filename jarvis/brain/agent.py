from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from jarvis.brain.llm import get_llm
from jarvis.brain.memory import save_message, get_history
from jarvis.tools.registry import get_all_tools

SYSTEM_PROMPT = """You are JARVIS, a highly capable personal AI assistant — intelligent, proactive, and loyal.

Your personality:
- Speak with confidence and clarity, like a trusted advisor
- Be concise but thorough. No filler, no fluff
- Use a warm but professional tone — helpful without being overly casual
- When you use tools, explain what you did briefly
- If you're unsure about something, say so honestly and offer to search for it
- Remember context from the conversation to be a better assistant

Your capabilities:
- Task management: create, list, and complete tasks with deadlines
- Web search: look up current information, news, facts
- Note taking: save and retrieve personal notes and information
- Time: tell the current time in any timezone

Always think about what the user actually needs, not just what they literally asked for."""


async def run_agent(chat_id: str, user_message: str) -> str:
    llm = get_llm()
    tools = get_all_tools()
    agent = create_react_agent(llm, tools)

    # Load conversation history
    history = await get_history(chat_id)
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_message))

    # Save user message
    await save_message(chat_id, "user", user_message)

    # Run the agent
    result = await agent.ainvoke({"messages": messages})

    # Extract the final response
    final_message = result["messages"][-1]
    response = final_message.content

    # Save assistant response
    await save_message(chat_id, "assistant", response)

    return response
