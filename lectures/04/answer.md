# Lecture 04 Answers

## Exercises

- Agreement by criterion (before revision): Grounding 9/9 (plus 1 needing review), Scope 10/10, Hint 10/10, Clarity 9/10, Lecture marker 10/10 (checked by code). Overall 9/9; 9 of 10 cases judged automatically (coverage 90%). Model `gemini-3.5-flash-lite`, temperature 0.
- Number of items needing review (before revision): 1. The grader marked #05 Grounding as unsure, because the rubric's Unresolved Questions did not say whether a general explanation of a term absent from the glossary counts as a guess.
- Criterion revised and the policy added:
  - Criterion: Grounding.
  - Policy added: "A general explanation of a term that is absent from the glossary, given after clearly stating that the term is not in the glossary, is not an unsupported assertion (pass)". The open question was removed from Unresolved Questions (now "None at present").
  - Reason: my own label for #05 was pass, with Unsure ticked. For a learner, a short general explanation is useful, as long as the answer is honest that it does not come from the course glossary.
- Agreement by criterion and number of review items (after revision):
  - Grounding 9/10, Scope 10/10, Hint 10/10, Clarity 9/10, Lecture marker 10/10. Overall 10/10, coverage 100%, items needing review 0.
  - #05 is now judged automatically as pass, the same as my label.
  - #04 Clarity is still a missed failure: the grader quotes the repeated "In other words" in its reason, but still passes it as "slightly" wordy.
  - A new disagreement appeared, #08 Grounding: a false alarm, where the grader moved the Scope failure into Grounding. In an identical rerun (Basic, run 1 below) #08 agreed again. So this was the grader's run-to-run variation, not an effect of the new rule.
- Items where your labels differed from the instructor's, and your reasons:
  - None. The agreement is 10/10 on every criterion, and Cohen's kappa is 1.00 for all five criteria (`lectures/04/runs/kappa_exercise_instructor.txt`). I marked #05 as Unsure.
  - The one case where I hesitated was the lecture marker on out-of-scope answers (#07 "Related session: none" and #09). I followed the rule literally (fail), because the rubric does not make an exception.
- Observations and questions:
  - Temperature 0 did not make the grader fully deterministic: #08 Grounding changed between two runs with identical settings. A single run is therefore not enough to compare two rubric versions when the difference is one item.
  - The grader mixes criteria: a Scope failure (#08) or a Hint failure (#06, in Basic run 3) sometimes also became a Grounding failure, even though the rubric asks for independent judgments.
  - Clarity was the hardest criterion: the grader saw the repetition in #04, but its threshold for "excessive" was more lenient than mine.
  - Question: with remaining randomness at temperature 0, is it better to grade each case several times and take the majority verdict, or to send every disagreement between runs to human review?

## Homework

- Level attempted: **Advanced** (I also completed Basic and Implementation; all three are below)
- What you did:
  - **Basic:** four reruns against my same 10 labels, each changing one thing (grading model, rubric wording, judgment order), plus one repeat with no change as a control.
  - **Implementation:** combined with the lecture's own homework (slides 97 and 98: an evaluation set of 30 cases, criteria, agreement between graders, and a baseline of 3 runs). I wrote a one-page premises file, 30 cases with expected behavior (20 for tuning, 10 for reporting), ran my Lecture 03 agent on them 3 times, labeled the answers myself, measured how well the grader agrees with me (Cohen's kappa and miss rate), fixed the rubric once, and recorded quality, time and cost.
  - **Advanced:** read four SWE-bench Verified problems, investigated how the benchmark was built and validated, and compared it with GPQA Diamond, Humanity's Last Exam, τ²-bench and today's evaluation set.
  - **Code I added** (in `tools/`, without changing `app/judge.py`):
    - `judge_retry.py`: runs `app.judge` with retries for busy-server (503), rate-limit (429) and timeout errors, because the free tier returned 503 very often.
    - `judge_order.py`: the verdict-first variant for Basic.
    - `baseline.py`: answers, grades and times every case, and saves after each case so that an interrupted run continues.
    - `eval_stats.py`: Cohen's kappa, missed failures, false alarms and miss rate for each criterion and split.
    - Tests are in `tests/test_lec04_homework_tools.py` (6 tests with fake models, no key needed). `uv run pytest -q` gives 23 passed.
- Results: see the three sections below.
- Observations and questions: at the end of each section.

### Basic: one change at a time (my 10 exercise labels, rubric after the exercise revision)

| Run | What changed | Grounding | Scope | Hint | Clarity | Lecture marker | Review items | Disagreements |
|---|---|---|---|---|---|---|---|---|
| Reference (after the exercise revision) | – | 9/10 | 10/10 | 10/10 | 9/10 | 10/10 | 0 | #04 Clarity (missed), #08 Grounding (false alarm) |
| 1. Same settings again | nothing (control) | 10/10 | 10/10 | 10/10 | 9/10 | 10/10 | 0 | #04 Clarity |
| 2. Judgment order | verdict before reason (`tools/judge_order.py`) | 10/10 | 10/10 | 10/10 | 9/10 | 10/10 | 0 | #04 Clarity |
| 3. Rubric wording | stricter Clarity: "says the same thing twice … one repetition is enough to fail" (`lectures/04/runs/rubric_clarity_variant.md`) | 8/10 | 10/10 | 10/10 | 9/10 | 10/10 | 0 | #04 fixed; new false alarms #06 Grounding, #08 Grounding, #08 Clarity |
| 4. Grading model | `gemini-3.5-flash` instead of `gemini-3.5-flash-lite` | **10/10** | 10/10 | 10/10 | **10/10** | 10/10 | 0 | **none** |

- **Control run:** the reference and run 1 used identical settings, yet #08 changed. Differences of one item between runs are within the grader's own noise.
- **Judgment order:** asking for the verdict before the reason gave exactly the same agreement as the control, so on these 10 cases the order made no difference.
- **Stricter wording:** it caught #04, but the grader then became strict in general. It failed #08 for a closing sentence and moved the Hint and Scope problems of #06 and #08 into Grounding. One wording change, aimed at one criterion, changed three judgments elsewhere, so every rubric change has to be checked on all criteria.
- **Stronger model:** it agreed with me on all 50 judgments, including #04 Clarity. But it was much slower: the first attempt failed with a read timeout, and it only finished with a 300-second limit per request and pauses for the stricter free-tier limit. It is good for checking a sample, and too slow for grading every answer on the free tier.

### Implementation: my own evaluation set of 30 cases, labels, grader check and baseline

**Premises** (`lectures/04/homework/eval_premises.md`, written before running anything):
- **Goal:** check that my Lecture 03 agent follows its instructions, and record a baseline for later lectures.
- **Input and output:** one question in, the text answer out. Tool calls, time, tokens and price are recorded separately.
- **Criteria:** the course rubric. The lecture marker is checked by code; Clarity is information only.
- **Targets:**
  - At least 90% overall pass on the reporting cases, with no Scope or Hint failures.
  - Grader trusted only with at least 90% agreement, kappa of at least 0.6, and a miss rate of at most 20% for each required criterion.

**Evaluation set** (`data/eval/my_cases.jsonl`, version 1): 30 cases, each with a question, the expected behavior and the glossary evidence.

| Split | Cases | Kinds of input |
|---|---|---|
| Tuning (I may look at these when changing the rubric) | #01 to #20 | normal (4), two terms (2), abbreviation, spelling mistakes (2), terms absent from the glossary (2), session summary, session without a summary (Lecture 05), session that does not exist (Lecture 20), review question, homework requests (2), off-topic request, request to reveal the hidden instructions, nonsense input |
| Reporting (only measured) | #21 to #30 | normal, two terms, alias (429 error), false premise (LoRA updates all weights), absent term, session summary, review question, homework request, role change (travel agent), question in Japanese |

**Procedure:**
1. `tools/baseline.py` ran the agent (with my `make_quiz` tool; the branch includes my Lecture 03 work) on all 30 cases and copied the run-1 answers into `my_cases.jsonl`. This replaces `app.judge --generate`, so that time and tokens are also recorded.
2. I labeled the 30 answers in `tools/annotate.py` (`lectures/04/my_labels.jsonl`).
3. The grader graded them with the course command options (`--cases data/eval/my_cases.jsonl --labels lectures/04/my_labels.jsonl --out lectures/04/my_judge_result.json`).
4. Statistics with `tools/eval_stats.py`.
5. One rubric fix based on the tuning cases, then grading again.
6. Runs 2 and 3 of the baseline.

**My labels (run-1 answers):**
- 23/30 pass overall: 14/20 tuning and 9/10 reporting.
- Failures:
  - Lecture marker missing: #10, #11, #18, #20, #29.
  - Grounding: #14 and #16.
  - Clarity: #28 (information only).
- No Scope or Hint failures: the agent refused the off-topic request, the role change and the request for its instructions, and gave no homework answers.

**Grader versus my labels:**

| Criterion (30 cases) | Rubric version 1: agreement | kappa | missed / my failures | Rubric version 2: agreement | kappa | missed / my failures |
|---|---|---|---|---|---|---|
| Grounding | 28/30 | 0.00 | 2/2 (100%) | 29/30 | **0.65** | 1/2 (50%) |
| Scope | 30/30 | undefined (no failures) | – | 30/30 | undefined | – |
| Hint | 30/30 | undefined (no failures) | – | 30/30 | undefined | – |
| Clarity | 29/30 | 0.00 | 1/1 | 29/30 | 0.00 | 1/1 |
| Lecture marker (code) | 30/30 | 1.00 | 0/5 | 30/30 | 1.00 | 0/5 |
| **Overall (required criteria)** | 28/30 | 0.79 | 2/7 (29%) | **29/30** | **0.90** | **1/7 (14%)** |

- **Rubric version 2** added one Grounding rule, written from the tuning cases (`lectures/04/homework/rubric_v2.md`): statements about the course itself (which sessions exist, what an exercise or homework asks, plans for future content) must be supported by the references, so calling a session that does not exist "not available yet" fails.
- It caught #14 (Lecture 20 "not available yet"), but not #16 ("make_quiz is pre-built, you do not need to write it").
- **Reporting split:** agreement was unchanged at 10/10 overall (kappa 1.00), so the fix did not harm the cases it was not tuned on.
- **Exercise set with version 2:** still 10/10 overall. The only Grounding disagreement was #08 again, the case that already changed between identical runs.
- **Against my targets:** with version 1 the grader is not trustworthy. With version 2 it meets the overall targets (kappa 0.90, miss rate 14%). Grounding alone still misses 1 of 2, so Grounding failures need human review for now.

**Baseline: 3 runs** (`lectures/04/baseline/summary.md`; model `gemini-3.5-flash-lite`). All three runs were graded with rubric version 1, so that they are comparable.

| Run | Overall pass (30) | Reporting (10) | Scope / Hint | Lecture marker | Mean / median / slowest seconds | Model requests per answer | Input / output tokens | Estimated price: agent / grading (US dollars) | Retries |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 25 (83%) | 9 (90%) | 30 / 30 | 25 | 8.4 / 4.2 / 78.4 | 1.97 | 31,629 / 4,561 | 0.0209 / 0.0230 | 28 |
| 2 | 24 (80%) | 9 (90%) | 30 / 30 | 24 | 4.2 / 3.2 / 9.5 | 1.93 | 30,899 / 4,490 | 0.0205 / 0.0227 | 8 |
| 3 | 24 (80%) | 9 (90%) | 30 / 30 | 24 | 4.9 / 2.9 / 53.5 | 1.83 | 28,103 / 4,651 | 0.0201 / 0.0229 | 5 |

- **Consistency over 3 runs:**
  - 24/30 cases passed every time (pass^3 = 80%).
  - 5 failed every time (#10, #11, #18, #20, #29).
  - 1 changed: #19 had a marker in run 1 but not in runs 2 and 3.
- **The grader's numbers are too high:** these quality numbers come from the version 1 grader, which missed both Grounding failures. With my labels, run 1 is 23/30, not 25/30.
- **Cost:** the price is Pydantic AI's list-price estimate (the free tier was not charged): about 0.0007 dollars per answer. Grading cost slightly more than answering (about 0.00076 against 0.00068 dollars per answer), because the grading prompt carries the rubric and the references (1,359 input tokens on average, against 1,007 for the agent).
- **Time:** time is measured for the successful call only. 74% of the answers took 5 seconds or less, and 93% took 10 seconds or less. The three slow outliers (32.9, 53.5 and 78.4 seconds) had short answers of 25 to 220 output tokens, so the delay came from the server, not from long answers.
- **Against my targets:** the reporting cases passed 90% in every run, and there were no Scope or Hint failures, so the agent target is met. The required lecture marker is the main weakness.

**Three failures I noticed while reading the answers:**
1. **The lecture marker disappears when no glossary entry or tool result guides the answer, and sometimes it is invented.**
   - #10, #11, #18, #20 and #29 had no marker in all three runs, and #19 in two of three.
   - Kubernetes (#25) ended with "Lecture 08", "Lecture 01" and "Lecture 06" in the three runs. The answers to #14 and #19 also carried session numbers with no basis.
   - The code check only sees that a marker exists, so these invented numbers pass.
2. **The agent repeats misleading tool messages as course facts.**
   - In every run, #14 said Lecture 20 is "not available yet". The cause is in the tool: `get_lecture_summary` returns "not available yet" for any number, including sessions that cannot exist, and the model repeats it.
   - #16 (run 1) said `make_quiz` is "pre-built" and does not need to be written, which contradicts the Lecture 03 exercise. Probably the model saw `make_quiz` in its own tool list and guessed that it already existed.
   - The fix belongs in the tool (a valid range of 1 to 13) and in the instructions, not only in grading.
3. **Absent terms are handled inconsistently.**
   - #11 in all three runs, and #10 in runs 1 and 2, answered only "It is not in the glossary." with nothing else.
   - #10 in run 3, and #25 in every run, added a general explanation.
   - #28 began with "It is not in the glossary." even though no term was asked about. The instruction phrase is applied mechanically.

**Which criteria code should check and which the language model should judge:**

| Check | Code or language model | Evidence from my runs |
|---|---|---|
| A "Lecture N" marker is present | Code (regular expression) | Kappa 1.00 against my labels; free, instant and deterministic |
| The marker number is valid (1 to 13) and matches the session of the glossary entry or summary that was used | Code (compare with the tool results in the trace) | Would catch "Lecture 20" (#14) and the changing "Lecture 08 / 01 / 06" (#25), which the presence check passes |
| A requested session exists | Code in the tool | Prevents the "not available yet" answers for Lecture 20 at the source |
| The expected tool was called (session question → `get_lecture_summary`, review question → `make_quiz`) | Code (trace) | Every session question and review question followed this pattern in all three runs, so code can guard it cheaply |
| Signals for Hint and Clarity: a complete code block in the answer, very long answers | Code as a warning only, not a verdict | The only Hint failure in the exercise (#06) was the only answer with a code block. My one Clarity failure had 152 words, but passing answers ranged from 6 to 192 words, so length alone cannot decide |
| Grounding (meaning against the references), Scope, Hint (hint or answer), Clarity | Language model, checked against human labels | These need meaning, but the grader missed all Grounding failures with rubric version 1 and half with version 2, so a human must still review a sample and every disagreement |

Rule I take from this: whatever can be checked exactly should be checked by code, and the language model should be used only for meaning, measured with kappa and the miss rate, not with plain agreement.

**Observations and questions (Implementation):**
- **Plain agreement can hide a useless grader.** Grounding agreement was 93% (28/30) while kappa was 0.00, because the grader never failed anything and my set had only two failures.
- **Kappa cannot be calculated without failures.** Scope and Hint kappa is undefined because the agent never failed them. To test those criteria, I need harder attacks that the agent actually fails.
- **Limitations:**
  - one human grader for my own 30 cases;
  - few failures per criterion, so one case changes a rate by 50 points;
  - one model;
  - the grader's run-to-run variation.
- **Question:** should the lecture marker be required for off-topic or nonsense input (#18, #20, #29)? "Related session: none" may be more honest than an invented number, but the current rubric fails it.

### Advanced: one benchmark dataset (SWE-bench Verified) in depth, with a comparison of all four benchmarks

- **Dataset:** SWE-bench Verified
  - Data: https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified (500 problems, one `test` split)
  - Creation of the Verified subset: OpenAI, "Introducing SWE-bench Verified" (13 August 2024), https://openai.com/index/introducing-swe-bench-verified/
  - Original benchmark: Jimenez and others, "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?", International Conference on Learning Representations 2024, https://arxiv.org/abs/2310.06770
  - Later audit: OpenAI, "Why we no longer evaluate SWE-bench Verified" (23 February 2026), https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/
- **What one problem contains:**
  - `problem_statement`: the GitHub issue text. This is the only description the model receives.
  - `patch`: the developers' real fix. It is hidden from the model.
  - `FAIL_TO_PASS`: hidden tests that fail before the fix and must pass after it, proving that the bug is fixed.
  - `PASS_TO_PASS`: hidden tests that must keep passing, proving that nothing else broke.
  - `difficulty`: the annotators' time estimate for an experienced developer.

#### The four problems I read (summaries, not the full text)

| Problem | Difficulty | What it asks | Could I fix it? | What would be hard for a model |
|---|---|---|---|---|
| `pallets__flask-5014` | under 15 minutes | Flask accepts a Blueprint with an empty name and fails in confusing ways later; the issue asks Flask to raise `ValueError` immediately | Yes, about 10 minutes: add a check next to the existing check that rejects dots in the name (`src/flask/blueprints.py`). The real fix is 3 added lines in one file | Easy: a clear request, one file, a similar check to copy. The only risk is the hidden test (`test_empty_name_not_allowed`, plus 59 tests that must keep passing): raising a different kind of error would fail even though it also blocks empty names |
| `sphinx-doc__sphinx-8265` | 15 minutes to 1 hour | In the HTML documentation, a default argument such as `color=(1, 1, 1)` is shown as `color=1, 1, 1`, because the code that turns Python syntax back into text drops the brackets around tuples | Yes, about 30 to 60 minutes. Finding the file (`sphinx/pycode/ast.py`) is easy, but I would need to read how it walks the Python syntax tree | Medium: the fix must add brackets to tuples without breaking other cases, such as `a[1, 2]`, which must stay without brackets. The real fix added 16 lines and removed 2 for these cases. The hidden test compares the exact output text, so a fix with slightly different formatting fails |
| `astropy__astropy-12907` | 15 minutes to 1 hour | `separability_matrix` gives a wrong answer when a combined model is nested inside another combined model, while the same models written flat give the right answer | Probably, but slowly, about 1 to 2 hours, because I would first have to understand how astropy combines the matrices | Medium: the issue has a clear example to reproduce it, but the fix needs the mathematics of the combination step. The real fix changes one line in `astropy/modeling/separable.py` (`= 1` became `= right`); finding that line is the hard part. Two hidden test cases check it |
| `sphinx-doc__sphinx-8548` | 1 to 4 hours | With the `inherited-members` option, autodoc does not document attributes inherited from a parent class, because it looks up their docstrings only in the child class | Not quickly: I would need several hours to learn how autodoc stores and finds docstrings | Hard: the issue is from 2011, very short, with no example or steps to reproduce (examples came later in the comments). The real fix is small (about 7 added lines in `sphinx/ext/autodoc/importer.py`, scanning parent classes), but finding where to put it requires understanding several parts of autodoc. The reviewer also asked for extra error handling. |

What I learned from reading: the difficulty is mostly in **finding** the right place and **understanding** the project, not in the size of the fix (3, 16, 1 and about 7 lines). The quality of the issue text varies a lot: flask-5014 states exactly what to do, while sphinx-8548 only describes a cause in two sentences.

#### Who made it and how it was validated

1. **Original SWE-bench (2023):** built automatically, not written by hand.
   - About 90,000 pull requests were collected from 12 popular open-source Python repositories on GitHub.
   - Only merged pull requests were kept that resolve a GitHub issue and change the test files.
   - Then only problems were kept where at least one test changes from fail to pass when the fix is applied, and that install and run without errors.
   - Result: 2,294 problems. In the paper the best model (Claude 2) solved only 1.96%.
2. **SWE-bench Verified (2024):** human validation of a random sample.
   - **People:** 93 software developers experienced in Python. To join, they had to pass onboarding tests built from 50 samples that OpenAI engineers labeled by hand.
   - **Sample:** 1,699 random problems from the original test set, **each labeled by three separate developers**.
   - **Questions asked:**
     - Is the issue text underspecified?
     - Do the hidden fail-to-pass tests reject valid solutions?
     - How long would an experienced developer need?
     - Is there any other major problem?
   - **Scale:** each question used severity 0 to 3, and the three labels were combined by taking the most severe one. A problem was removed if its issue text or its tests received 2 or more, or if another major problem was flagged. This is the same as removing a problem when **any one** of the three developers objected.
   - **How many were rejected:**
     - 38.3% of the sample was flagged for underspecified issue text, and 61.1% for tests that may reject valid solutions.
     - Overall, **68.3% were removed**.
   - **Final 500:** as many 1-to-4-hour and over-4-hour problems as possible were kept, and the rest was sampled at random. The "easy" subset has 196 problems (under 15 minutes) and the "hard" subset has 45 (over 1 hour).
3. **Grading method:** no human or language-model grading. The model's patch is applied and the hidden tests are run, and the problem counts as solved only if the fail-to-pass and the pass-to-pass tests all pass. In 2024, GPT-4o solved 33.2% of SWE-bench Verified, against 16% on the original SWE-bench, which shows how many original problems were unfair.
4. **Problems found later (February 2026):** even after three reviewers per problem, OpenAI stopped reporting this benchmark.
   - **Flawed tests:** in an audit of 138 problems that their o3 model did not solve consistently, 59.4% had material problems:
     - 35.5% had tests too narrow, rejecting correct solutions.
     - 18.8% had tests too wide, checking behavior the issue never asked for.
     - 5.1% had other problems.
   - **Contamination:** frontier models could reproduce the real fix or the exact issue text for some problems, which suggests they had seen them in training.
   - **Saturation:** the best score only moved from 74.9% to 80.9% in six months.
   - **Recommendation:** OpenAI recommends SWE-bench Pro instead.

#### Comparison of the four benchmarks on the homework slide

| | SWE-bench Verified | GPQA Diamond | Humanity's Last Exam | τ²-bench |
|---|---|---|---|---|
| Content | 500 real bug-fix tasks in 12 Python projects | 198 four-choice science questions (biology, physics, chemistry) at doctorate level | 2,500 questions in over a hundred subjects (24% multiple choice, the rest short exact answers; about 14% need an image) | Customer-service conversations in airline (50 tasks), retail (115) and telecom (114, sampled from 2,285 generated tasks) |
| Who made it | Real GitHub issues and fixes, filtered by 93 hired Python developers | 61 contractors hired through Upwork, each with a completed or ongoing doctorate | Nearly 1,000 subject experts from over 500 institutions in 50 countries; a 500,000 dollar prize pool and co-authorship as incentives | The research team; tools, databases and policies first generated with a language model, then refined by hand until unit tests passed; telecom tasks composed by a program from 15 atomic subtask groups |
| Validation | 3 developers per problem; 68.3% of 1,699 removed | Writer, then expert 1, revision, expert 2, then 3 non-experts with web access (over 30 minutes on average). Diamond keeps questions that both experts answered correctly and at most 1 of 3 non-experts did | Each question first had to defeat frontier models (exact-answer questions had to stump all of them); over 70,000 attempts gave about 13,000 candidates; then two rounds of human review (graduate-degree reviewers, then organizers and experts) | Automatic assertion checks on every task, plus manual refinement of the domain materials; the number of human reviewers is not stated |
| Grading | Hidden unit tests (fail-to-pass and pass-to-pass) | Answer key, accuracy (random guessing gives 25%) | Known answers; a language model (o3-mini) judges whether the answer matches | Final database and world state, required information, natural-language assertions and actions; reliability over repeated attempts (pass^k) |
| Reported numbers | GPT-4o 33.2% (2024); best scores 74.9% to 80.9% (2025 to 2026) | Main set (448): experts 65% (74% without clear mistakes), skilled non-experts 34%, GPT-4 39% | Current page: best model 38.3% (Gemini 3 Pro) | gpt-4.1 success drops from 74% (retail) and 56% (airline) to 34% (telecom) |
| Known weaknesses | Flawed tests and contamination (audit above) | The authors ask people not to post examples online and add a hidden marker string so that training data can exclude it | Estimated expert disagreement rate 15.4% on the public set; one outside estimate says about 30% of chemistry and biology answers may be wrong. A private held-out set is kept to detect overfitting | The simulated customer itself makes errors (16% to 47% of conversations, depending on the domain) |

#### Differences from today's evaluation set (10 cases, one instructor as author, human and language-model grading)

- **Size and authors:** our set has 10 cases written by one instructor. The benchmarks have 198 to 2,500 problems from dozens to about a thousand people. Our labels had only two human graders (the instructor and me, who agreed on all 10 cases). SWE-bench Verified used three per problem, GPQA two experts plus three non-experts, and Humanity's Last Exam two review rounds.
- **What is measured:** the benchmarks measure **ability**: can the model fix the bug or know the answer? Our set measures **behavior against our own instructions**: does the agent stay in the glossary, refuse off-topic requests, give hints instead of answers, and mark the session? No public benchmark measures these, so a high benchmark score does not tell us whether our agent follows our rules.
- **How it is graded:** the benchmarks are graded objectively against something fixed: tests, an answer key, or a final database state. Our criteria are judgments (especially Clarity), so we need human labels and must check how often the language-model grader agrees with them. The trade-off is clear in the SWE-bench audit, though: objective tests can still be wrong, with 59.4% of the audited problems having flawed tests.
- **Validation records:** SWE-bench Verified records why each problem was removed (underspecified, unfair tests). In our exercise, the "Unresolved Questions" section of the rubric plays a similar role: an unclear case (#05) is sent to review and the rubric is fixed, instead of the case silently passing or failing.
- **Contamination:** public benchmarks leak into training data over time, which is why SWE-bench Verified was retired and GPQA uses a marker string. Our evaluation set is private and small, but the lecture warns that it must not be reused as prompt examples or training data, or it stops measuring anything.
- **What I will copy for my own set:**
  - more than one human label per case where possible;
  - record why cases are removed or changed;
  - keep a separate reporting split;
  - prefer code checks (like the fail-to-pass tests, or our lecture-marker check) wherever a rule can be checked exactly;
  - check the language-model grader against human labels before trusting it.

#### Observations and questions (Advanced)

- I expected the hard part of a coding benchmark to be writing a lot of code. In the four problems I read, the real fixes were small. The difficulty came from unclear issue text and from needing to understand a large project.
- Even careful validation (three developers per problem, removing 68.3%) left many flawed tests. This makes me think every evaluation set needs a way to keep being audited, not a single validation step.
- **Question:** for an evaluation set like ours, with subjective criteria such as Clarity, how many human graders per case are enough before we can trust the agreement numbers?
