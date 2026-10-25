# Lecture 01 Answers

## Exercises

- Model's answer to the course-specific question (the 3 homework levels; a summary is fine):
  With gemini-3.5-flash-lite, the model said it has no information about the "AIE2026 course" and could not list the levels. It asked for more context instead of guessing.
- What you noticed when comparing it with the correct meaning in the glossary:
  The glossary (`homework-levels`) says the levels are Basic (review lecture content), Implementation (write your own code) and Advanced (research and experimentation), and any one completes the homework. A bare LLM does not know course-specific facts. Here it honestly said "I don't know". For a general term ("What is LoRA?") the answer was broadly correct, but its structure changed between runs. When I typed "LoRa" (small a) by mistake, the model explained LoRa long-range radio for IoT, a different technology, so one letter changed the whole answer.
- Token counts you displayed (input / output):
  "What is LoRA?" with gemini-3.5-flash-lite: input 6 / output 556

## Homework

- Level attempted: Basic
- What you did:
  Asked the same course-specific question ("What are the 3 homework levels in the AIE2026 course?") 3 times each with two models, switching with the `AIE_MODEL` environment variable: `gemini-3.5-flash-lite` (default) and `gemini-3.8-flash`. I did not change temperature, because the course slides say Google deprecated it. Raw outputs are in `lectures/01/runs/flash-lite.txt` and `lectures/01/runs/flash.txt`.
- Results:

  | Model | Successful runs | Answer | Tokens (input / output) |
  |---|---|---|---|
  | gemini-3.5-flash-lite | 3 of 3 | Said it does not know the course every time. Wording and suggestion changed each run (paste the syllabus / which institution / check the LMS) | 18 / 74, 50, 81 |
  | gemini-3.8-flash | 2 of 6 (4 failed with 503 "model is busy") | Both times confidently invented 3 levels ("Baseline/Core", "Advanced" or "Stretch", "Production" or "Hardcore") and linked them to a different course (AI Makerspace's AI Engineering Bootcamp). The 2nd answer added a short note asking which institution | 18 / 396, 360 |

  Correct answer (glossary): Basic / Implementation / Advanced.

- Observations and questions:
  - The stronger model gave longer, more detailed, but wrong answers, while the smaller model admitted it did not know. A bigger model is not automatically more reliable about facts it never saw in training.
  - The same question gave different wording on every run with both models. The 3.8-flash made-up story was similar in both runs, but the level names changed.
  - Input tokens were the same (18) for both models. Output was about 5.5 times longer for gemini-3.8-flash on average (378 vs 68 tokens), so it costs more and uses the free quota faster.
  - gemini-3.8-flash failed with 503 in 4 of 6 attempts, so gemini-3.5-flash-lite is more practical for repeated tests on the free tier.
  - Question: how can we make the model answer from course facts (like the glossary) instead of guessing?
