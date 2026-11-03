# Lecture 01 Answers

## Exercises

- Model's answer to the course-specific question (the 3 homework levels; a summary is fine):
  With gemini-3.5-flash-lite, the model said it has no information about the "AIE2026 course" and could not list the levels. It asked for more context instead of guessing.
- What you noticed when comparing it with the correct meaning in the glossary:
  The glossary (`homework-levels`) says the levels are Basic (review lecture content), Implementation (write your own code) and Advanced (research and experimentation), and any one completes the homework. A large language model without extra context does not know course-specific facts. Here it honestly said "I don't know". For a general term ("What is LoRA?") the answer was broadly correct, but its structure changed between runs. When I typed "LoRa" (small a) by mistake, the model explained LoRa long-range radio for Internet of Things devices, a different technology, so one letter changed the whole answer.
- Token counts you displayed (input / output):
  "What is LoRA?" with gemini-3.5-flash-lite: input 6 / output 556

## Homework

- Level attempted: **Advanced** (I also completed Basic earlier; those results are kept at the end)
- What you did:
  - Wrote `app/measure.py`, which asks every model and question pair several times and records the response time, input tokens, output tokens, hidden thinking tokens and any errors for every attempt. It waits between calls to stay under the per-minute limit, retries "model is busy" errors (503) up to two times, and stops calling a model that keeps returning "rate limit reached" (429). Results are saved to `lectures/01/results/` (`measurements.csv` for every attempt, `summary.md`, and `answers.md` with all answers).
  - Added `tests/test_measure.py` (3 tests with a fake model, so they need no Gemini key or internet access): token recording and summary, retry after a busy error, and stopping on repeated rate-limit errors. `uv run pytest -q` passes (14 tests).
  - Models: `gemini-3.5-flash-lite` and `gemini-3.8-flash`. Questions: a course-specific fact the model cannot know ("What are the 3 homework levels in the AIE2026 course?"), a short answer ("What is LoRA in machine learning? Answer in two sentences.") and a long answer ("Explain LoRA in machine learning in detail."). Each pair 3 times. Run on 2026-11-01.
- Results:

  | Model | Question | Successful / attempts | Average seconds (min to max) | Output tokens | Thinking tokens | Output + thinking |
  |---|---|---|---|---|---|---|
  | gemini-3.5-flash-lite | course fact | 3 / 3 | 1.0 (0.9 to 1.1) | 57 | 0 | 57 |
  | gemini-3.5-flash-lite | short answer | 3 / 3 | 0.9 (0.8 to 1.1) | 55 | 0 | 55 |
  | gemini-3.5-flash-lite | long answer | 3 / 3 | 5.6 (5.5 to 5.8) | 1,485 | 0 | 1,485 |
  | gemini-3.8-flash | course fact | 3 / 4 (one 503) | 64.3 (21.3 to 107.7) | 388 | 1,252 | 1,640 |
  | gemini-3.8-flash | short answer | 3 / 4 (one 503) | 119.7 (6.8 to 242.7) | 66 | 448 | 514 |
  | gemini-3.8-flash | long answer | 3 / 3 | 122.9 (82.5 to 143.3) | 1,916 | 1,393 | 3,308 |

  Input tokens were the same for both models (18, 14 and 10 for the three questions).

  Answer quality: gemini-3.5-flash-lite said it did not know the course in all 3 runs. gemini-3.8-flash confidently invented three levels ("Baseline / Core", "Advanced" or "Stretch", "Production") and attributed them to a different course (AI Makerspace) in all 3 runs, the same as in my Basic runs. Both models answered the general LoRA questions correctly.

- Observations and discussion:
  - **Time:** gemini-3.5-flash-lite answered short questions in about 1 second, and its time grew with answer length (about 5.6 seconds for about 1,500 tokens). gemini-3.8-flash took 1 to 2 minutes on average, and the time for almost the same 66-token answer ranged from 6.8 to 242.7 seconds, so most of its time was waiting and thinking, not writing the visible answer.
  - **Hidden thinking tokens:** gemini-3.8-flash generated 448 to 1,393 thinking tokens per answer that are not shown in the text. Google's token documentation says that with thinking turned on, "response pricing is the sum of output tokens and thinking tokens". So the short answer really cost about 9 times as many tokens as gemini-3.5-flash-lite (514 versus 55), and the course-fact question about 29 times as many (1,640 versus 57).
  - **More thinking did not fix missing knowledge:** the stronger model spent about 1,250 thinking tokens on the course question and still gave a wrong answer with confidence. The small model was honest. Facts the model never saw need to come from outside, for example a glossary search tool (Lecture 03).
  - **Relationship to the free-tier rate limits** (course measurements on slide 16: gemini-3.5-flash-lite 15 requests per minute and 500 per day; gemini-3.8-flash 5 per minute and about 10 to 20 per day):
    - Limits count requests, not answer length. A 55-token answer and a 1,500-token answer each use one request.
    - gemini-3.5-flash-lite answers in about 1 second, so a loop without pauses could send about 60 requests per minute and hit the 15-per-minute limit (error 429). The per-minute limit is the real constraint, so my script waits 5 seconds between calls. This experiment used only 9 of the 500 daily requests.
    - gemini-3.8-flash takes 1 to 2 minutes per answer, so a single script cannot even reach 5 requests per minute. The daily limit is the real constraint: this experiment alone used 11 attempts, about the whole estimated daily allowance.
    - The errors I saw were 503 ("model is busy"), which come from Google's servers and are not caused by my usage, so waiting and retrying works. Error 429 would mean my own limit is used up, so retrying immediately does not help; the right action is to wait for the minute or day to reset. Pacing my calls meant I never got a 429.
    - For agents in Lecture 03, one question needs several model calls. With gemini-3.8-flash, 3 calls could take several minutes and only a few questions per day would fit in the limit. With gemini-3.5-flash-lite, one question takes a few seconds and well over 100 questions per day would fit.
  - **Conclusion:** on the free tier, gemini-3.5-flash-lite is the practical choice for repeated experiments and agents. gemini-3.8-flash is worth using only for a few questions that need deeper reasoning, and its hidden thinking tokens must be counted when estimating time and cost. Always record which model was used.
  - Question: does a 503 error count toward the daily request limit? I could not confirm this from the documentation.

### Earlier Basic-level results (2026-10-25)

- What I did: asked "What are the 3 homework levels in the AIE2026 course?" 3 times each with `gemini-3.5-flash-lite` and `gemini-3.8-flash`, switching with the `AIE_MODEL` environment variable. Raw outputs are in `lectures/01/runs/`.

  | Model | Successful runs | Answer | Tokens (input / output) |
  |---|---|---|---|
  | gemini-3.5-flash-lite | 3 of 3 | Said it does not know the course every time; the wording and suggestion changed each run (paste the syllabus / which institution / check the learning management system) | 18 / 74, 50, 81 |
  | gemini-3.8-flash | 2 of 6 (4 failed with 503 "model is busy") | Both times confidently invented 3 levels and linked them to a different course (AI Makerspace) | 18 / 396, 360 |
