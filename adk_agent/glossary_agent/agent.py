"""Lecture 03 Advanced homework (a): the same learning support agent, rebuilt with Google ADK.

The instructions (INSTRUCTIONS) and the tool functions are reused from app/ unchanged;
only the agent assembly differs from the Pydantic AI version in app/agent.py.

Run from the repository root:
    PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent
"""

from google.adk.agents import Agent

from app import tools
from app.agent import INSTRUCTIONS
from app.config import MODEL

root_agent = Agent(
    model=MODEL,  # Same model as app.agent (gemini-3.5-flash-lite unless AIE_MODEL is set)
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz],
)
