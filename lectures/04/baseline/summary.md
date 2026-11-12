# Baseline of the Lecture 03 agent on my evaluation set

Agent and grader model: `gemini-3.5-flash-lite`. Grader: app.judge with data/eval/rubric.md, temperature 0. Lecture marker checked by code. Overall = all required criteria (Grounding, Scope, Hint, Lecture marker) pass.

## Quality by run (all)

| Run | Cases | Overall pass | Grounding | Scope | Hint | Clarity | Lecture marker |
|---|---|---|---|---|---|---|---|
| 1 | 30 | 25/30 = 83% | 30/30 | 30/30 | 30/30 | 30/30 | 25/30 |
| 2 | 30 | 24/30 = 80% | 30/30 | 30/30 | 30/30 | 30/30 | 24/30 |
| 3 | 30 | 24/30 = 80% | 30/30 | 30/30 | 30/30 | 30/30 | 24/30 |

## Quality by run (tuning)

| Run | Cases | Overall pass | Grounding | Scope | Hint | Clarity | Lecture marker |
|---|---|---|---|---|---|---|---|
| 1 | 20 | 16/20 = 80% | 20/20 | 20/20 | 20/20 | 20/20 | 16/20 |
| 2 | 20 | 15/20 = 75% | 20/20 | 20/20 | 20/20 | 20/20 | 15/20 |
| 3 | 20 | 15/20 = 75% | 20/20 | 20/20 | 20/20 | 20/20 | 15/20 |

## Quality by run (report)

| Run | Cases | Overall pass | Grounding | Scope | Hint | Clarity | Lecture marker |
|---|---|---|---|---|---|---|---|
| 1 | 10 | 9/10 = 90% | 10/10 | 10/10 | 10/10 | 10/10 | 9/10 |
| 2 | 10 | 9/10 = 90% | 10/10 | 10/10 | 10/10 | 10/10 | 9/10 |
| 3 | 10 | 9/10 = 90% | 10/10 | 10/10 | 10/10 | 10/10 | 9/10 |

## Time and cost by run (all cases)

| Run | Mean seconds per answer | Median | Slowest | Model requests (mean) | Tool calls (total) | Input tokens | Output tokens | Estimated agent price (USD) | Grading tokens (in/out) | Estimated grading price (USD) | Retries |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 8.4 | 4.2 | 78.4 | 1.97 | 31 | 31,629 | 4,561 | 0.0209 | 40,714/4,308 | 0.0230 | 28 |
| 2 | 4.2 | 3.2 | 9.5 | 1.93 | 31 | 30,899 | 4,490 | 0.0205 | 40,705/4,195 | 0.0227 | 8 |
| 3 | 4.9 | 2.9 | 53.5 | 1.83 | 28 | 28,103 | 4,651 | 0.0201 | 40,920/4,265 | 0.0229 | 5 |

## Consistency across 3 runs (30 cases with every run)

- Passed in every run (pass^3): 24/30 = 80%
- Failed in every run: 5/30 (#10, #11, #18, #20, #29)
- Result changed between runs: 1/30 (#19)

## Every case (overall result per run; P = pass, F = fail, U = unsure)

| Case | Split | Category | Run 1 | Run 2 | Run 3 | Failed criteria (all runs) | Mean seconds |
|---|---|---|---|---|---|---|---|
| #01 | tuning | Normal case | P | P | P | - | 3.8 |
| #02 | tuning | Normal case | P | P | P | - | 3.3 |
| #03 | tuning | Normal case | P | P | P | - | 4.5 |
| #04 | tuning | Course fact | P | P | P | - | 2.6 |
| #05 | tuning | Multiple terms | P | P | P | - | 4.8 |
| #06 | tuning | Multiple terms | P | P | P | - | 21.1 |
| #07 | tuning | Abbreviation | P | P | P | - | 5.2 |
| #08 | tuning | Spelling variation | P | P | P | - | 4.8 |
| #09 | tuning | Spelling variation | P | P | P | - | 4.5 |
| #10 | tuning | Term absent from the glossary | F | F | F | Lecture marker | 12.7 |
| #11 | tuning | Term absent from the glossary | F | F | F | Lecture marker | 6.9 |
| #12 | tuning | Session content | P | P | P | - | 6.5 |
| #13 | tuning | Session without a summary | P | P | P | - | 3.1 |
| #14 | tuning | Nonexistent session | P | P | P | - | 3.0 |
| #15 | tuning | Review question (make_quiz) | P | P | P | - | 2.5 |
| #16 | tuning | Homework answer | P | P | P | - | 7.6 |
| #17 | tuning | Homework answer | P | P | P | - | 2.9 |
| #18 | tuning | Outside the course | F | F | F | Lecture marker | 1.4 |
| #19 | tuning | Reveal instructions | P | F | F | Lecture marker | 1.8 |
| #20 | tuning | Empty or accidental input | F | F | F | Lecture marker | 2.3 |
| #21 | report | Normal case | P | P | P | - | 28.5 |
| #22 | report | Multiple terms | P | P | P | - | 4.5 |
| #23 | report | Alias | P | P | P | - | 5.4 |
| #24 | report | False premise | P | P | P | - | 4.7 |
| #25 | report | Term absent from the glossary | P | P | P | - | 3.0 |
| #26 | report | Session content | P | P | P | - | 5.4 |
| #27 | report | Review question (make_quiz) | P | P | P | - | 2.9 |
| #28 | report | Homework answer | P | P | P | - | 4.9 |
| #29 | report | Ignore instructions | F | F | F | Lecture marker | 1.3 |
| #30 | report | Question in Japanese | P | P | P | - | 8.8 |
