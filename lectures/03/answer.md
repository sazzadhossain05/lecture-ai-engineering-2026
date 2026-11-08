# Lecture 03 Answers

## Exercises

- Differences between the Lecture 01 (bare LLM) and agent answers:
  - Question: "What are the 3 homework levels in the AIE2026 course?" (model `gemini-3.5-flash-lite` in both lectures).
  - Lecture 01 (`app.ask`, the model alone): it said it has no information about the AIE2026 course and asked for more context. The stronger `gemini-3.8-flash` was worse: it confidently invented three levels and attributed them to a different course.
  - Lecture 03 (agent): it first searched the glossary, then gave the correct answer from the `homework-levels` entry: Basic (review the lecture content), Implementation (write your own code) and Advanced (research and experimentation). It also said that completing any one level completes the homework and that the homework is not graded, and it ended with "(Lecture 01)" as `INSTRUCTIONS` requires.
  - The model is the same, so the difference comes only from the tool: the agent can look up course facts that the model never saw in training.
- Tool calls shown by `--trace` (tool names and arguments):
  - "What are the 3 homework levels…": `search_glossary({'query': 'homework'})` (it returned 3 entries: 3 homework levels, ADK, answer.md).
  - "What is the difference between LoRA and QLoRA?": `search_glossary({'query': 'LoRA'})` and `search_glossary({'query': 'QLoRA'})`. The model looked up one term per call, as the `search_glossary` docstring says ("Put only one term to look up in query"), and it asked for both searches in the same model response.
  - "Give me one review question from Lecture 02": `make_quiz({'lecture': 2})`.
  - Raw output: `lectures/03/runs/pydantic_ai.txt`.
- Number of LLM calls for one question (`requests`):
  - 2 for every question (`requests=2`; `tool_calls` = 1, 2 and 1). The first model call decides which tools to call and with which arguments. The program runs the tools and sends the results back, and the second model call writes the answer.
  - Two tool calls do not mean three model calls: in the LoRA question both searches were requested in one response.
  - Tokens (input / output): 1,128 / 105, 1,343 / 266 and 895 / 65.
- Tool added and the description in its docstring:
  - `make_quiz(lecture: int) -> str` in `app/tools.py`, registered with `agent.tool_plain(tools.make_quiz)` in `app/agent.py`.
  - Docstring: "Create one review question from the glossary terms of the specified session (an integer starting at 1). Use when the learner asks for a review question or quiz about a session, such as "Give me one review question from Lecture 02". Pose the returned question to the learner and keep the answer hidden until the learner has tried to answer."
  - It picks one Lecture N term with `random.choice` and returns JSON with `question`, `answer` and `lecture`. For a session without terms (for example `lecture=0`), it returns "No glossary terms for Lecture 00" and lists the sessions that have terms, instead of raising an error.
  - Checks:
    - `--list-tools` shows 3 tools including `make_quiz` and its docstring (`lectures/03/runs/list_tools.txt`).
    - In the trace, the model called it with `lecture=2` and kept the answer hidden.
    - I added `tests/test_make_quiz.py` (2 tests: the question comes from the requested session, and session 0 gives the clear message). `uv run pytest -q`: 17 passed.

## Homework

- Level attempted: **Advanced, option (a): rebuild the agent with Google's Agent Development Kit (ADK) and compare**
- What you did:
  - Created `adk_agent/glossary_agent/agent.py` and `__init__.py` (`from . import agent`). The agent reuses `INSTRUCTIONS` from `app/agent.py` and the three tools from `app/tools.py` without changes (`search_glossary`, `get_lecture_summary` and my `make_quiz`). Only the assembly is new:
    ```python
    root_agent = Agent(
        model=MODEL,  # same model as app.agent: gemini-3.5-flash-lite
        name="glossary_agent",
        instruction=INSTRUCTIONS,
        tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz],
    )
    ```
  - Ran it with `PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent`. Output: `lectures/03/runs/adk_run.txt`. ADK version 2.14.0 (installed temporarily by `uv run --with`); Pydantic AI 2.57.0 (from `uv.lock`).
  - `adk run` shows only the final answer, not the tool calls. To compare the two frameworks fairly, I wrote `adk_agent/compare_trace.py`. It runs the same `root_agent` through ADK's `InMemoryRunner` and reads every event. It prints the tool calls and tool results in the same format as `app.agent --trace`, and it counts the model calls and tokens from each event's `usage_metadata`.
  - Asked both agents the same three exercise questions, once each, on 8 November 2026. Raw outputs: `lectures/03/runs/pydantic_ai.txt` and `lectures/03/runs/adk.txt`.
  - To see exactly what each framework sends to Gemini, I also ran the ADK agent with a fake model (a small class that records the request instead of calling Gemini). I also read how Pydantic AI converts tool results for Gemini (`model_response_object` in `pydantic_ai/messages.py`).
- Results:

  **Code comparison (how instructions and tools are passed)**

  | | Pydantic AI (`app/agent.py`) | ADK (`adk_agent/glossary_agent/agent.py`) |
  |---|---|---|
  | Instructions | `Agent(instructions=INSTRUCTIONS)` | `Agent(instruction=INSTRUCTIONS)` (singular). ADK adds one sentence of its own after my text: "You are an agent. Your internal name is "glossary_agent"." |
  | Special characters in instructions | Text is sent as written | Text in curly braces, such as `{name}`, is read as a session state variable and replaced. `INSTRUCTIONS` has no braces, so it is sent unchanged (checked with the fake model) |
  | Tools | Registered one at a time after creating the agent: `agent.tool_plain(tools.search_glossary)` | Passed as a list of plain functions: `tools=[...]`. ADK wraps each function automatically |
  | Tool description seen by the model | Name, docstring and type hints. Schema: `{"query": {"type": "string"}}` | Same names and docstrings. The schema has extra title fields (`'title': 'Query'`, `'search_glossaryParams'`) |
  | Model | Given at run time (`run_sync(question, model=build_model())`), so tests can use `TestModel` without a Gemini key | Fixed when the agent is created (`model=MODEL`). The key is read from the environment (the Codespaces secret). For my fake-model check I had to create a second agent |
  | Name | Not needed | `name` is required. `adk run` and the event author use it |
  | Running | `agent.run_sync(question)` is one synchronous call. It returns `.output`, `.all_messages()` and `.usage` (requests, tool calls, tokens, estimated cost) | `adk run` is an interactive terminal. In code: create a runner and a session, then read an asynchronous stream of events. Usage is reported per event, so I added it up myself |
  | Tool result sent to Gemini | A string result is wrapped as `{'return_value': ...}`. The trace prints the content before wrapping, so the wrapping is not visible | A string result is wrapped as `{'result': ...}`, and the trace shows the wrapped form |

  **Same questions, same model (`gemini-3.5-flash-lite`), one run each**

  | Question | Agent | Tool calls (arguments) | Model calls | Input / output tokens | Answer |
  |---|---|---|---|---|---|
  | 3 homework levels | Pydantic AI | `search_glossary('homework')`: 3 entries returned | 2 | 1,128 / 105 | Correct levels, any one completes, not graded, "(Lecture 01)" |
  | 3 homework levels | ADK | `search_glossary('homework levels')`: 1 entry (exact alias match) | 2 | 1,083 / 125 | Same facts, plus advice to pick the level that fits your goals, "(Lecture 01)" |
  | 3 homework levels | ADK, `adk run` | not shown | not shown | not shown | Same facts, "(Lecture 01)" |
  | LoRA versus QLoRA | Pydantic AI | `search_glossary('LoRA')`, `search_glossary('QLoRA')` | 2 | 1,343 / 266 | Correct. Added a detail that was not in the returned definitions (LoRA keeps the base weights in about 16-bit precision). Ended with a question to think about, "Lecture 02" |
  | LoRA versus QLoRA | ADK | the same two calls | 2 | 1,467 / 216 | Correct. Began "Based on the course glossary", stayed close to the definitions, ended with a hint and "(Lecture 02)" |
  | Review question, Lecture 02 | Pydantic AI | `make_quiz(lecture=2)`: Learning rate | 2 | 895 / 65 | Asked the question, kept the answer hidden, gave a hint about parameter updates, "(Lecture 02)" |
  | Review question, Lecture 02 | ADK | `make_quiz(lecture=2)`: LoRA | 2 | 1,048 / 67 | Asked the question, kept the answer hidden, offered a hint on request, "Lecture 02" |
  | **Total** | Pydantic AI / ADK | 4 / 4 tool calls | 6 / 6 | 3,366 / 436 versus 3,598 / 408 | All answers correct in both |

- Observations and questions:
  - **The framework changed the code, not the agent.** With the same model, instructions and tools, both versions followed the same loop: search first, one term per search, the answer in the second model call, and the session named at the end. Every question took exactly 2 model calls in both. An agent really is "model + loop + tools". The framework only decides how I write the assembly and how much of the loop I can see.
  - **The model chooses the search words, and that changes the cost.** For the same question, one run searched "homework" and the other "homework levels". "homework" also matched two unrelated entries (ADK and answer.md) through their definitions, so that run sent about 690 more characters to the model. This is why the Pydantic AI run used more input tokens on this question, even though ADK adds a sentence to the instructions. Clear tool descriptions and good search matching matter for both accuracy and cost.
  - **Small hidden differences in the request.** ADK adds its own identity sentence to the instructions and sends a slightly longer tool schema. On the LoRA question, both agents received the same tool results, but ADK used 124 more input tokens. I believe the added sentence and schema explain part of this, but I could not confirm the full breakdown, because the frameworks do not show the final request in Gemini's own format.
  - **Answers differed in style, not in facts.** The ADK answers stayed closer to the glossary wording. Once, the Pydantic AI answer added a correct general fact that the tool had not returned (16-bit base weights), and in the quiz its hint came close to the hidden answer. With one run per question and no fixed temperature, I cannot say whether these differences come from the framework or from normal randomness. The quiz questions were different terms because `make_quiz` uses `random.choice`, so the quiz answers cannot be compared directly.
  - **Visibility of the loop.** Pydantic AI returns one result object with all messages and usage, which made `--trace` easy. With ADK, `adk run` hides the tool calls. I had to read the asynchronous event stream myself to see them, and the trace shows the `{'result': ...}` wrapping, which Pydantic AI also does but does not show.
  - **Testing.** Pydantic AI's design of passing the model at run time lets the course tests run without a key. In ADK the model is part of the agent, so testing without a key needs a separate agent with a fake model.
  - **Limitations:** one run per question, three questions, a single model, and no control of randomness.
  - **Questions:**
    - Is there a recommended way in ADK to swap the model at run time for tests, as Pydantic AI does with `TestModel`?
    - Does ADK's identity sentence ("Your internal name is…") have any purpose in a single-agent setup, or is it only for passing work between several agents?
