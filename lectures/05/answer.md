# Lecture 05 Answers

All outputs are saved in [`runs/`](runs/). Each output file starts with the exact command that produced it, so every number below can be checked against its file.

## Exercises

- **Answering model** (`[model]` shown during execution): `gemini-3.5-flash-lite`
- **Comparison question**: `In Lecture 02, what does LoRA freeze and what does it train? What does QLoRA add?`
- **Target materials**:
  - Vector search, Tree and Graph: the 214 pages of the main materials for Lectures 01 to 03 in `data/rag_data/index.sqlite3` (Lecture 01: 73 pages, Lecture 02: 70 pages, Lecture 03: 71 pages).
  - Full context: all 8 documents in `data/rag_data/lectures.json`, 398 pages and 369,491 characters. This also includes the Lecture 05 main materials and the exercise documents for Lectures 01 to 04.
  - I kept the scopes as provided and checked where the difference mattered: in question 1, the full-context answer used two pages of the Lecture 2 exercise document, which the other methods cannot see (see the table).
- **Evidence I checked before running**: `lec02-main-p052` (Lecture 2, Japanese source page 52, translated PDF page 75) contains the whole answer: the original weights W are frozen, only the small matrices A and B are trained, and QLoRA also stores the frozen weights in 4 bits. `lec02-main-p051` (PEFT overview) states the same three points in a shorter form.

### Results by Method

**Question 1** (the comparison question). Output files: `runs/q1_full.txt`, `runs/q1_vector.txt`, `runs/q1_tree.txt`, `runs/q1_graph.txt`.

| Method | Key points and correctness of the answer | Cited pages and evidence | Time (seconds) | Input/output tokens | Model responses | Estimated generation API cost (USD) |
|---|---|---|---|---|---|---|
| Full context | Correct. LoRA freezes the original weights and trains only the small matrices A and B; QLoRA also compresses the frozen weights to 4 bits. It added two details that are not in the main materials ("NF4", and adapters still trained at 16-bit precision) | "Lecture 2 · translated PDF p.75, Japanese source p.52" is correct (`lec02-main-p052`). "Japanese source p.26" is a wrong label: Lecture 2 main page 26 is an unrelated quiz. The added details exist only in the Lecture 2 exercise document (`lec02-exercise-p021` and `lec02-exercise-p026`), which is outside the scope of the other methods | 10.27 | 95,824 / 241 | 1 | 0.029350 |
| Vector search | Correct. Same three points, with the "thin sticky notes" analogy from the page | Lecture 2 pages 51 to 52. Both pages support every point | 36.05 | 2,758 / 189 | 2 | 0.001300 |
| Tree | Correct and the most detailed: under 1% of the parameters are trained, about 4 GB for a 7-billion-parameter model | Lecture 2 Japanese source page 52, whose full text it opened. Correct | 188.93 | 9,442 / 384 | 5 | 0.003793 |
| Graph | Correct. Same three points plus the 4 GB example | `lec02-main-p052` for every point. Correct | 44.88 | 5,188 / 250 | 2 | 0.002181 |

All four answers were correct. For the same correct answer, full context used 34.7 times the input tokens of vector search and 22.6 times its cost. The times mostly reflect load on the API server, not the method (see Observations), so I compare tokens and cost rather than seconds.

**Question 2** (multiple pages): `In the Lecture 03 examples, how does compaction differ from memory across sessions? Do all daily notes go into long-term memory?` Evidence: `lec03-main-p013`, `lec03-main-p039`, `lec03-main-p040`.

| Method | Key points and correctness of the answer | Cited pages and evidence | Time (seconds) | Input/output tokens | Model responses | Estimated generation API cost (USD) |
|---|---|---|---|---|---|---|
| Full context | Correct on both parts: compaction replaces old history with a summary inside the same session; memory stores records outside and loads them in a new session. Not all daily notes are kept: a nightly review moves only what passes a threshold into `MEMORY.md` | Lecture 3 pages 13, 38, 39, 40. Correct | 24.18 | 95,828 / 254 | 1 | 0.029383 |
| Vector search | Part 1 correct. Part 2 was given only as a hint ("check the nightly review steps on page 40"), not as an answer | Lecture 3 pages 13, 39, 40, 65. All three evidence pages were retrieved | 97.47 | 2,293 / 281 | 2 | 0.001390 |
| Tree | Both parts given only as hints that point to pages 39 to 40 | Opened the full text of pages 39 and 40. Did not open page 13 | 98.20 | 8,278 / 319 | 6 | 0.003281 |
| Graph | Correct on both parts | Lecture 3 pages 38, 39, 40. Page 13 was not retrieved, but page 39 alone explains the difference between within-session and across-session memory | 76.03 | 4,876 / 266 | 2 | 0.002128 |

**Question 6** (absent from the materials): `What are the measured average response time and accuracy of the RAG system we just built?`

| Method | Key points and correctness of the answer | Cited pages and evidence | Time (seconds) | Input/output tokens | Model responses | Estimated generation API cost (USD) |
|---|---|---|---|---|---|---|
| Full context | Not run for this question, to limit requests while the API was returning "high demand" errors | | | | | |
| Vector search | Correct. It said the materials report no such measurements and did not invent numbers. It added that one try does not show accuracy | Lecture 2 page 13, which does say this. Correct | 38.01 | 2,710 / 186 | 2 | 0.001278 |
| Tree | Not run for this question (same reason) | | | | | |
| Graph | Not run for this question (same reason) | | | | | |

The Advanced homework method also answered question 6 correctly without inventing numbers (see Homework).

- **Pages found by running search alone, and what their text confirmed**: `uv run python -m app.retrieval "LoRA QLoRA difference"` (`runs/step2_retrieval.txt`) returned 5 pages in this order: `lec02-main-p052`, `lec02-main-p051`, `lec02-main-p060`, `lec02-main-p047`, `lec02-main-p061`.
  - Page 52 is the evidence: "Freeze the original weights and train only a small change, or delta, with LoRA. QLoRA also compresses the original weights to 4 bits."
  - Page 51 (PEFT overview) also states that LoRA freezes the base model and that QLoRA compresses it to 4 bits.
  - Pages 60 and 61 are the Lecture 2 exercise steps. They contain the word QLoRA ("Train with QLoRA") but do not explain what is frozen or trained: similar terms, not evidence.
  - Page 47 (RAG compared with fine-tuning for adding knowledge) matched only on the fine-tuning words.
- **Tool calls shown by `--trace`**:
  - Full context: no tool call; 1 model response with all 369,491 characters as input.
  - Vector search: 1 call, `search_materials("LoRA freeze train QLoRA")`, which returned Lecture 2 pages 52, 51, 60, 47, 61.
  - Tree: 4 calls of `browse_tree`: no ID (list of lectures) → `lec02-main` → section `lec02-main-s045` "When and how to adapt the selected model" → page `lec02-main-p052` (1,238 characters). It chose the right section from the titles at the first try. Its cost comes from 5 model responses, each sending the growing conversation again. For question 2 it made 5 calls: lecture list → `lec03-main` → section `lec03-main-s037` "Part 6 Memory" → pages 39 and 40.
  - Graph: 1 call, `search_graph("LoRA freeze train QLoRA Lecture 02")`. Seeds: Lecture 2 pages 52, 60, 51. Expanded: pages 53, 59, 61, 50, 62, 49, 47 (all from Lecture 2, Part 4 and the exercise slides).
- **Examples where retrieved information was insufficient, or was retrieved but not used in the answer**:
  1. Retrieved but not stated (question 2, vector search and Tree): the pages with the answer (39 and 40) were retrieved, but part 2 was answered only as a hint. This comes from the instruction "Guide learners with hints on how to think, rather than writing homework answers for them", not from retrieval. Other runs of the same question answered directly, so this changes from run to run.
  2. Not retrieved (question 2, Graph): page 13 was missing from all 10 pages. The graph started from pages 65, 39 and 38 and expanded only into nearby pages of "Part 6 Memory" and the appendix. The answer was still correct because page 39 covers the point.
  3. Retrieved from outside the scope, with a wrong page label (question 1, full context): see the first table.
  4. Retrieved but used wrongly (homework question t2, vector search): Lecture 3 page 19 was in the results of all 3 searches and states the trend ("Task length AI can handle (METR) ... doubles about every 4 months"), but the answer did not name it and guessed a trend that the materials do not support. Details are in the Advanced section.
- **Method you would adopt for this use case, your reasons, and limitations of the comparison conditions**:
  - I would adopt vector search for a course question-answering chatbot, with the result count raised from 5 to 6 or 7 (see the Basic homework). It answered questions 1 to 5 correctly with 2,127 to 2,758 input tokens and 0.0013 to 0.0018 USD per answer.
  - Full context was also correct, but cost 22.6 times more on question 1 and 21.1 times more on question 2. Its input grows with every page added to the materials, while the input of vector search stays about the same.
  - Tree was correct but needed 5 to 6 model responses and 3.4 to 3.6 times the input tokens. I would use it when the user names a section.
  - Graph needed about 2 times the input tokens and missed one evidence page on question 2.
  - Limitations: one run per method and question; times are not comparable because of server load; full context had a larger scope than the other methods; I chose the evidence pages myself by reading the materials; only 6 questions here (plus 3 more in the homework).
- **Observations and questions**:
  - Time was driven by load on the API server, not by the method. Runs took from 4.71 to 188.93 seconds. In the first batch of 25 runs, 7 runs failed 4 times in a row with HTTP 503 "This model is currently experiencing high demand"; I ran them again later with longer waits. None of the failures was an input-limit error: full context was accepted every time (95,824 input tokens).
  - Environment problem: in my Codespace the default Python was 3.14, and its `sqlite3` module had no `enable_load_extension`, so sqlite-vec could not be loaded. 8 tests failed with `AttributeError: 'sqlite3.Connection' object has no attribute 'enable_load_extension'`, including the course's own `test_built_index_can_be_searched`. Switching to Python 3.12 with uv (`echo 3.12 > .python-version`, `uv python install 3.12`, `uv sync --frozen`) fixed it, and all 29 tests passed. Question: should the repository fix the Python version so that new Codespaces do not hit this?
  - Question: when the instructions ask for hints, how should answer correctness be judged in a comparison like this? A hint that points to the right page helps learning, but it is not a direct answer.

## Homework

- **Level attempted**: Advanced. I also completed Basic and Implementation on the same questions, so the three levels can be compared with each other.

### Common conditions for all three levels

- Model `gemini-3.5-flash-lite`, the same 214-page search database (no rebuild, no change to text or embedding settings), the same question text, and `--trace` on every run. Only the retrieval changed.
- Two kinds of measurement:
  1. **Retrieval only** (`tools/rag_eval.py`): every method receives the same saved embedding of the question text. I count how many known evidence pages it returns, how many pages it returns, and how many characters it would add to the model input. No answer is generated, so model randomness and the model's choice of search words do not affect this test. The query embeddings are saved (`runs/query_embeddings.json`, `runs/target_query_embeddings.json`), so the test can be repeated without the API. Results: `runs/retrieval_eval.md` and `runs/target_eval.md`.
  2. **Agent runs**: the full agent with `--trace`, one run per question and method. I checked each answer and its cited pages against the materials.
- Tests: `tests/test_lec05_homework.py` has 12 tests that need no API key (the query embedding is replaced by the stored vector of one page, so that page must come first). All 29 tests in the repository pass.
- Questions and the evidence pages I identified in the materials before running (`data/eval/lec05_questions.jsonl`, `data/eval/lec05_target_questions.jsonl`):

| ID | Question | Evidence pages | Type |
|---|---|---|---|
| q1_lora | In Lecture 02, what does LoRA freeze and what does it train? What does QLoRA add? | Lecture 2 page 52 | One page |
| q2_memory | In the Lecture 03 examples, how does compaction differ from memory across sessions? Do all daily notes go into long-term memory? | Lecture 3 pages 13, 39, 40 | Multiple pages |
| q3_properties | Which model properties from Lecture 02 become design assumptions for agents in Lecture 03, and which part of the agent design handles each one? | Lecture 3 page 3, Lecture 2 page 62 | Across lectures |
| q4_rag_vs_ft | To add new knowledge to a chatbot, why does the course recommend RAG before fine-tuning, and how does the example chatbot in Lecture 01 use RAG? | Lecture 2 pages 46, 47; Lecture 1 page 49 | Across lectures |
| q5_stop | What are the three ways to stop an agent loop, and who should decide whether the task is done? | Lecture 3 pages 43, 44 | Multiple pages |
| q6_absent | What are the measured average response time and accuracy of the RAG system we just built? | None | Absent from the materials |
| t1_rsi | How does Lecture 03 revisit the recursive self-improvement (RSI) idea that Lecture 01 introduced? | Lecture 1 page 10, Lecture 3 page 55 | Advanced target |
| t2_errors | Lecture 03 warns about compounding errors in agents. Which trend from Lecture 01 does it build on, and how likely is an agent to succeed over 20 steps at 95% per step? | Lecture 3 page 19, Lecture 1 page 9 | Advanced target |
| t3_schedule | Why does Lecture 02 say a model cannot answer questions about this year's course schedule, and which chatbot example in Lecture 01 solves this? | Lecture 2 page 22, Lecture 1 page 49 | Advanced target |

### Basic: search result count from 5 to 10

- **What I did**: `RAG_TOP_K` in `app/config.py` now reads the environment variable `AIE_RAG_TOP_K` (default 5). Only the number of results changes, and I can run before and after without editing the file between runs: `AIE_RAG_TOP_K=10 uv run python -m app.agent --trace "$AIE_QUESTION"`. The agent prints `[search] RAG_TOP_K=10`, so each saved output shows its own setting. `search()` also accepts a `top_k` argument and rejects values below 1.
- **Comparison questions and conditions held fixed**: q1_lora and q2_memory; same model, materials, instructions and tools.
- **Results**:

| Question | Result count | Answer | Pages returned and cited | Time (seconds) | Input/output tokens | Model responses | Cost (USD) |
|---|---|---|---|---|---|---|---|
| q1 | 5 | Correct | Returned Lecture 2 pages 52, 51, 60, 47, 61; cited 51 to 52 | 36.05 | 2,758 / 189 | 2 | 0.001300 |
| q1 | 10 | Correct, same content | The same 5 plus pages 48, 58, 54, 46, 23; cited 51 to 52 | 39.99 | 4,649 / 146 | 2 | 0.001760 |
| q2 | 5 | Part 1 correct; part 2 only a hint | Lecture 3 pages 65, 38, 39, 40, 13 | 97.47 | 2,293 / 281 | 2 | 0.001390 |
| q2 | 10 | Both parts correct and direct | The same 5 plus Lecture 3 pages 41, 37, 64 and Lecture 2 pages 46, 15 | 51.33 | 4,000 / 296 | 2 | 0.001940 |

  - Tool calls did not change: one search per question, with almost the same search words ("LoRA freeze train QLoRA" and "LoRA freeze train QLoRA add").
  - Retrieval only, questions 1 to 5: evidence pages found went from 10 to 11 of 11, questions with all evidence from 4 to 5 of 5, and average characters from 4,777 to 9,057 (+90%). The only page gained was Lecture 2 page 46 for q4, which is at similarity rank 6.
  - Target questions t1 to t3: no gain (4 of 6 evidence pages with both settings), because the missing pages are at ranks 14 and 51.
- **Improvements and limitations**:
  - Input tokens rose 68.6% (q1) and 74.4% (q2), and cost rose 35.4% and 39.6%. The q1 answer did not change.
  - The q2 answer became direct, but the run with 5 results already had pages 39 and 40, so the extra pages did not cause this. It is run-to-run variation together with the hint instruction.
  - 10 is more than needed. The lowest-ranked evidence page in questions 1 to 5 is at rank 6, so 6 results already find all 11 pages. 7 results also find all 11, with 29% fewer characters than 10 (6,457 compared with 9,057).
- **Observations**: a larger result count cannot reach a page that similarity ranks very low, such as Lecture 1 page 9 at rank 51 of 214 for t2. That needs a different kind of retrieval.

### Implementation: add the pages before and after each hit

- **What I did** (`app/retrieval.py`, `app/tools.py`, `app/agent.py`):
  1. `add_neighbor_pages(hits, window=1)` uses the page metadata from `load_pages()` and adds the page immediately before and after each hit, only inside the same `document_id`.
  2. No duplicates: a page that is already a hit stays a hit and is not repeated as a neighbor, and every page appears once.
  3. Every page keeps its text and citation metadata. Added pages are marked `role: "neighbor"`, with `neighbor_of` (the hit) and `offset` (-1 or +1), so the model and I can see why each page is there. The trace prints a "Pages returned:" line that shows this.
  4. New tool `search_materials_with_neighbors(query)` and flag `--neighbors`. Its instructions are the default instructions plus one line: pages with role "neighbor" were added only because they sit next to a hit; use them only when their text supports the answer.
  5. Tests: the first page of a document gets only its next page, the last page gets only its previous page, and a hit is never repeated as a neighbor.
- **Comparison questions and conditions held fixed**: q1_lora, q2_memory and q5_stop, normal search compared with the neighbor version.
- **Results**:

| Question | Method | Answer | Pages returned | Time (seconds) | Input/output tokens | Model responses | Cost (USD) |
|---|---|---|---|---|---|---|---|
| q1 | Normal search | Correct | 5 | 36.05 | 2,758 / 189 | 2 | 0.001300 |
| q1 | With neighbors | Correct, same content | 11 (6 neighbors: Lecture 2 pages 53, 50, 46, 48, 59, 62) | 46.90 | 5,067 / 226 | 2 | 0.002085 |
| q2 | Normal search | Part 1 correct; part 2 only a hint | 5 | 97.47 | 2,293 / 281 | 2 | 0.001390 |
| q2 | With neighbors | Both parts only as hints | 11 (6 neighbors: Lecture 3 pages 64, 66, 37, 41, 12, 14) | 32.69 | 4,464 / 248 | 2 | 0.001959 |
| q5 | Normal search | Correct: the model, the harness, or a human or monitor stops the loop; someone other than the working model decides "done" | 5 | 27.93 | 2,127 / 411 | 2 | 0.001666 |
| q5 | With neighbors | Correct, same content | 11 (6 neighbors: Lecture 3 pages 45, 41, 25, 27, 47, 49) | 42.41 | 4,142 / 304 | 2 | 0.002003 |

  - Retrieval only, questions 1 to 5: evidence pages found went from 10 to 11 of 11, but each question returned 12.7 pages and 10,717 characters on average (2.2 times normal search).
- **Example where necessary evidence was added**: q4. Lecture 2 page 46 ("Small-scale FT changes behavior well but is weaker at adding knowledge", similarity rank 6) is not in the top 5, but it was added as the neighbor of page 47 (rank 3).
- **Examples where unnecessary information increased**: q1, all 6 neighbors were unnecessary because page 52 alone answers it. q2, the neighbors included page 37, a section divider ("Part 6 Memory", 45 characters). q5, none of the 6 neighbors was used in the answer. Over the three questions, input tokens rose 84% to 95% and cost rose 20% to 60%, with no better answer.
- **Remaining failures**: neighbors help only when the evidence sits next to a hit. In the target questions the missing evidence is in another lecture (for example, Lecture 1 page 9 for a Lecture 3 question), so neighbors found 4 of 6 evidence pages, the same as normal search, while returning 13.7 pages and 10,570 characters on average.
- **Observations**: I would not use plain neighbors on both sides as the default. A narrower rule (for example, add a neighbor only when it continues the same page title, and never add divider pages) might keep the q4 gain with fewer pages. I have not tested this yet.

### Advanced: question-aware hybrid retrieval

- **Question I chose to solve**: questions that span two lectures and name them. With normal search, the most similar pages often come from only one of the lectures. For t3, all top 5 pages are from Lecture 2 and the Lecture 1 evidence is at rank 14; for t2, the Lecture 1 evidence is at rank 51 of 214. I wrote three target questions (t1 to t3) and identified their evidence pages before running (table above). q3 and q4 are also cross-lecture questions.
- **Design: data structure, storage, retrieval method, and reasons**:
  - **Storage**: no new database or index. The method reuses the bundled `index.sqlite3` (one 768-dimension vector per page), the page metadata in `lectures.json` (lecture → section → page), and the term nodes in `graph.json` (course terms with aliases, linked by `mentions` edges to the pages that mention them). Reason: no rebuild is needed, and it uses the same page vectors as normal search, so the comparison is fair.
  - **Step 1, similarity to every page**: one query embedding, then `vec_distance_cosine` against all 214 pages in SQLite. Reason: the same single embedding call as normal search; with 214 pages, scoring all of them is cheap, and the later steps can choose from the full ranking.
  - **Step 2, skip section-divider pages**: pages shorter than 150 characters are not returned. Reason: divider pages hold only a title (for example Lecture 3 page 37, "Part 6 Memory", 45 characters), yet they ranked in the top 10 for 5 of the 9 questions (Lecture 3 pages 37, 5, 42, 54 and 18). For t2, 2 of the 5 basic RAG results were divider pages (page 18, "Part 3 Loop Compounding Errors", 30 characters, and page 54).
  - **Step 3, course-term bonus**: course terms written in the question are found through the aliases in `graph.json`, and a page that mentions one gets +0.01 per term (at most 2). Terms that appear on more than 30 pages are ignored as too common (for example "AI agent", 54 pages). Aliases of 3 characters or fewer, such as "FT", must match with the same capital letters and as a whole word. Reason: an exact course term is a strong sign of the topic.
  - **Step 4, keep each named lecture**: for every lecture the question names ("Lecture 01", "Lectures 1 and 3"), the best page of that lecture is kept. Reason: a cross-lecture question then gets at least one page from each lecture, using the lecture structure in the same way as Tree.
  - **Step 5, fill up to 7 pages by score, at most 4 per section**. Reason: spread the results over sections, and keep the size between 5 and 10 results.
  - **Explanations**: every returned page has a `why` list (similarity rank, matched terms, or "best page of Lecture 01, which the question names"), and the result also lists the named lectures, matched terms and skipped divider pages. Reason: I can check from the trace why each page was chosen.
  - Tool `search_hybrid(query)` and flag `--hybrid`. The instructions are the default instructions plus one line: "search_hybrid returns pages from several sections; `why` shows how each page was found. Being linked does not mean a page contains the answer."
  - Each step can be switched off by an argument; `tools/rag_eval.py` uses this for the ablation below.
- **Comparison with basic RAG (same questions, model and target materials)**:

Retrieval only, questions 1 to 5 (11 evidence pages; pages and characters are averaged over all 6 questions, including q6):

| Method | Evidence pages found (of 11) | Questions with all evidence (of 5) | Average pages returned | Average characters returned |
|---|---|---|---|---|
| Vector search, top 5 (basic RAG) | 10 | 4 | 5.0 | 4,777 |
| Vector search, top 10 (Basic level) | 11 | 5 | 10.0 | 9,057 |
| Top 5 + adjacent pages (Implementation level) | 11 | 5 | 12.7 | 10,717 |
| Graph (provided) | 10 | 4 | 10.0 | 8,899 |
| **Hybrid (Advanced level)** | **11** | **5** | **7.0** | **6,539** |
| Vector search, top 7 (same page count as hybrid) | 11 | 5 | 7.0 | 6,457 |

Retrieval only, target questions t1 to t3 (6 evidence pages):

| Method | Evidence pages found (of 6) | Questions with all evidence (of 3) | Average pages returned | Average characters returned |
|---|---|---|---|---|
| Vector search, top 5 (basic RAG) | 4 | 1 | 5.0 | 3,522 |
| Vector search, top 10 | 4 | 1 | 10.0 | 8,094 |
| Top 5 + adjacent pages | 4 | 1 | 13.7 | 10,570 |
| Graph (provided) | 3 | 0 | 10.0 | 7,547 |
| **Hybrid (Advanced level)** | **4** | **1** | **7.0** | **6,212** |
| Vector search, top 7 | 4 | 1 | 7.0 | 5,085 |

Ablation, removing one step at a time: without the divider filter, without keeping named lectures, without the term bonus, or without the section cap, every version still finds 11 of 11 on questions 1 to 5 and 4 of 6 on t1 to t3. Removing a step changes only which non-evidence pages are returned.

Agent runs, questions 1 to 6 (one run each):

| Question | Basic RAG: answer | Basic RAG: input/output tokens, cost (USD) | Hybrid: answer | Hybrid: input/output tokens, cost (USD) |
|---|---|---|---|---|
| q1 | Correct | 2,758 / 189, 0.001300 | Correct | 3,885 / 199, 0.001663 |
| q2 | Part 1 correct; part 2 only a hint | 2,293 / 281, 0.001390 | Both parts correct and direct, citing Lecture 3 pages 13, 39, 40, 65 | 3,471 / 260, 0.001691 |
| q3 | Correct: all six properties and the part that handles each, from Lecture 3 page 3 | 2,191 / 472, 0.001837 | Correct, same content | 3,276 / 461, 0.002135 |
| q4 | Correct, citing Lecture 2 page 53 and Lecture 1 pages 19, 49 | 2,599 / 364, 0.001690 | Correct, and adds the research findings on Lecture 2 page 47 | 3,789 / 571, 0.002564 |
| q5 | Correct | 2,127 / 411, 0.001666 | Correct | 3,488 / 341, 0.001899 |
| q6 | Correct: no such measurements in the materials | 2,710 / 186, 0.001278 | Correct: no such measurements in the materials | 3,964 / 112, 0.001469 |

Graph was also run on q3 and q4 and was correct on both (3,971 / 422 tokens, 0.002246 USD; 4,471 / 533 tokens, 0.002674 USD).

Agent runs, target questions (one run each):

| Question | Method | Answer | Evidence retrieved and cited | Searches | Time (seconds) | Input/output tokens | Model responses | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| t1 | Basic RAG | Correct: Lecture 1 introduces RSI as an upward spiral; Lecture 3 revisits it as a cycle (page 55), as an agent improving its own harness (page 58), and with risks (pages 57 to 58) | Both evidence pages in the first search; cites Lecture 1 page 10 and Lecture 3 pages 54 to 58 | 2 | 7.54 | 5,381 / 368 | 3 | 0.002534 |
| t1 | Hybrid | Correct: same points, plus the reality check that full automation is not reached yet (pages 57, 69) | Both evidence pages in one search; cites Lecture 1 page 10 and Lecture 3 pages 55, 57, 58, 69 | 1 | 4.71 | 3,428 / 346 | 2 | 0.001893 |
| t2 | Basic RAG | Incomplete: "about 36%" is correct, but the Lecture 1 trend is not named. It only says "same as Lecture 1, page 9" and guesses a trend that the materials do not support | Lecture 3 page 19 in all 3 searches (it states the trend); Lecture 1 page 9 never retrieved | 3 | 10.74 | 10,431 / 224 | 4 | 0.003689 |
| t2 | Hybrid | Correct: the METR trend that the length of tasks AI completes doubles about every four months, and about 36% | Lecture 3 page 19, and Lecture 1 page 9 in the second search; cites both | 2 | 8.28 | 10,330 / 197 | 3 | 0.003592 |
| t3 | Basic RAG | Partly correct: gives the knowledge cutoff and hallucination, and the RAG chatbot of Lecture 1 page 49, but misses the page that answers the first part | Lecture 1 page 49 retrieved; Lecture 2 page 22 never retrieved; cites Lecture 2 pages 14 and 27 instead | 3 | 9.48 | 9,031 / 370 | 4 | 0.003634 |
| t3 | Hybrid | Correct: the model only knows facts up to its training data, so it does not know this year's syllabus (page 22); the Lecture 1 chatbot uses RAG (pages 19, 49) | Both evidence pages retrieved and cited | 3 | 7.44 | 16,429 / 277 | 4 | 0.004525 |

Totals for t1 to t3: basic RAG 24,843 input tokens and 0.009857 USD; hybrid 30,187 input tokens and 0.010010 USD.

- **Examples of improvements**:
  1. Same evidence with fewer pages than the provided options: all 11 of 11 evidence pages on questions 1 to 5 with 7 pages, where Graph found 10 of 11 with 10 pages and top 10 needed 10 pages. It returned 28% fewer characters than top 10 and 27% fewer than Graph.
  2. Divider pages never take a place: 6 were skipped across 5 questions, where basic RAG spent up to 2 of its 5 places on them (t2).
  3. In the agent runs, the hybrid answered all 3 target questions completely with the right pages; basic RAG did this for 1 of 3. On t1 the hybrid found the pages of both lectures in one search, with 36% fewer input tokens.
  4. On q2, the hybrid answer was direct and complete, citing pages 13, 39 and 40.
- **Remaining failures and limitations**:
  1. **No gain over plain vector search at the same page count.** Vector search with 7 results finds the same evidence (11 of 11 and 4 of 6) with slightly fewer characters (6,457 compared with 6,539 on questions 1 to 6; 5,085 compared with 6,212 on t1 to t3). The ablation shows that no single step changed the evidence count on these 9 questions.
  2. **Keeping a page per named lecture did not keep the right page.** It keeps the most similar page of that lecture, which for t2 was Lecture 1 page 41 (rank 21, not the evidence page 9 at rank 51) and for t3 was Lecture 1 page 19 (rank 9, not the evidence page 49 at rank 14).
  3. The term bonus applied on q1, q2, q4, q5 and q6 (LoRA, QLoRA, Memory, RAG, Agent loop) but changed no evidence count, and it never applied to the target questions: they contain no course term, or only "AI agent", which is on too many pages.
  4. **The agent-run gains on t2 and t3 cannot be credited to the method alone.** The model chose different search words in each run. In the hybrid t2 run, its second search included "METR time horizon", and that search returned Lecture 1 page 9; in the basic RAG run it searched "Lecture 1 page 9" and never got that page. With one run per question I cannot separate the method from this variation.
  5. Cost: with 7 pages instead of 5, input tokens rose 41% to 64% on questions 1 to 6 (cost +14% to +52%). On t3 the hybrid made 3 searches and used 82% more input tokens than basic RAG.
  6. My evidence lists are not complete. While checking the answers I found that q4 is also supported by Lecture 2 page 53 ("FT does not fix the knowledge problem ... Retrieve and provide the materials with RAG"), and the Lecture 1 part of t3 by page 19 (the same lab chatbot, which "searches lecture materials to answer and cites evidence"). I kept the lists as written before the runs. If page 19 is accepted for t3, the hybrid covers it within 7 pages because of step 4, while vector search with 7 results does not (page 19 is 9th).
- **Would I adopt it for my use case?** Not as a whole yet.
  - Adopt: vector search with 7 results, the divider-page filter, and the `why` field, which made checking the evidence much faster.
  - Not yet: keeping named lectures and the term bonus, until a larger test shows a gain.
  - Next steps: (1) choose the kept page of a named lecture by the question's words, not only by similarity; (2) Lecture 3 page 19 says "Same as Lecture 1, page 9", and following such explicit references would have found page 9 directly, but it is the only such reference in the 214 pages, so I did not build it for one case; (3) run each agent question 5 times and compare averages instead of single runs.
- **Observations and questions**:
  - The two measurements disagreed: the retrieval-only test says hybrid equals vector search with 7 results, while the agent runs favored the hybrid. The agent writes its own search words, so a fixed-query test alone does not predict answer quality. Question: is there a recommended way to compare retrieval methods for an agent that searches several times, for example many repeated runs graded with the Lecture 04 method?
  - Distance is not evidence: Lecture 1 page 9 is the right evidence for t2 but ranks 51 of 214 by similarity, because the question talks about "compounding errors" while the page talks about "task length".
