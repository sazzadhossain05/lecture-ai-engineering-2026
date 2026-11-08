"""Run the ADK agent on one question and print its tool calls, like `app.agent --trace`.

`adk run` only shows the final answer, so this script uses ADK's Runner to read every event
(tool calls, tool results, answer text) and to count model calls and tokens.

Run from the repository root:
    PYTHONPATH=. uv run --with google-adk python -m adk_agent.compare_trace "What is the difference between LoRA and QLoRA?"
"""

import argparse
import asyncio

from google.adk.runners import InMemoryRunner
from google.genai import types

APP_NAME = "glossary_agent"
USER_ID = "student"


async def run_question(agent, question: str) -> dict:
    """Ask one question in a new session and collect tool calls, answer text and usage."""
    runner = InMemoryRunner(agent=agent, app_name=APP_NAME)
    session = await runner.session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    message = types.Content(role="user", parts=[types.Part(text=question)])
    trace, answer = [], []
    usage = {"model_calls": 0, "input_tokens": 0, "output_tokens": 0}
    async for event in runner.run_async(user_id=USER_ID, session_id=session.id, new_message=message):
        meta = event.usage_metadata
        if meta is not None:
            usage["model_calls"] += 1
            usage["input_tokens"] += meta.prompt_token_count or 0
            usage["output_tokens"] += meta.candidates_token_count or 0
        parts = event.content.parts if event.content and event.content.parts else []
        for part in parts:
            if part.function_call:
                trace.append(f"[tool call]   {part.function_call.name}({dict(part.function_call.args or {})})")
            elif part.function_response:
                trace.append(f"[tool return] {part.function_response.name} -> {str(part.function_response.response)[:120]}…")
            elif part.text and not part.thought and event.author == agent.name:
                answer.append(part.text)
    return {"answer": "".join(answer).strip(), "trace": trace, "usage": usage}


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the ADK agent a question and show its tool calls")
    parser.add_argument("question")
    args = parser.parse_args()

    from adk_agent.glossary_agent.agent import root_agent

    print(f"[model] {root_agent.model}")
    result = asyncio.run(run_question(root_agent, args.question))
    print(result["answer"])
    print("\n--- trace ---")
    print("\n".join(result["trace"]))
    print(f"[usage] {result['usage']}")


if __name__ == "__main__":
    main()
