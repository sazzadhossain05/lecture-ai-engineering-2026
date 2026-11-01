# Lecture 02 Answers

## Exercises

- Model and settings used (from `config` in `result.json`):
  `Qwen/Qwen3.5-0.8B` (revision `2fc06364715b967f1860aea9cf38778875588b17`), LoRA without quantization, rank (`lora_r`) 16, `lora_alpha` 32, learning rate 0.0002, 20 epochs (40 steps), 6 warmup steps, maximum sequence length 512, greedy generation (`do_sample: false`), up to 96 new tokens. Libraries: transformers 5.18.0, peft 0.21.1, trl 1.14.2, torch 2.11.0+cu130. Google Colab with a T4 graphics processing unit.
- Did you run training yourself (`executed_training_myself`): Yes (I ran sections 0 to 7 myself; the optional section 8 was skipped)
- Before training: `format_rate` = 0.95 (20 of 21) / `content_rate` = 0.38 (8 of 21)
- After training: `format_rate` = 1.00 (21 of 21) / `content_rate` = 0.90 (19 of 21)
- Questions that regressed: none
- Failures remaining after training and their types:
  - "Can I submit a format other than PDF?" (evidence exists: one PDF file): the model answered "This FAQ does not contain that information. Confirmation from the course organizers is needed." with `needs_review: true`. Type: **evasion through a confirmation request despite evidence being present**.
  - "Do office hours require an appointment?" (no evidence in the frequently asked questions list, the FAQ): the model copied the office hours item ("Questions are welcome during office hours every Tuesday from 17:00 to 18:00.") with `needs_review: false`. Type: **assertion without evidence**, made by applying a different FAQ item.
  - No broken formats remained.
- Results of knowledge questions (section 6; classification before → after training) and observations:

  | Question | In FAQ | Before → after |
  |---|---|---|
  | When is the final assignment deadline for this course? | No | asserted → asserted |
  | What is the instructor's name? | No | needs_review → needs_review |
  | What is the topic of the next lecture? | No | needs_review → needs_review |
  | When is the assignment deadline? (control) | Yes | asserted → asserted (correct) |

  After training, the "final assignment deadline" question was answered with the normal assignment deadline from the FAQ ("September 30 at 23:59") and `needs_review: false`. This is a made-up claim: the model matched the question to the deadline item by similar words. In my run there were no format errors even before training, which is different from the original Japanese run.
- What changed and what stayed the same with training:
  - Changed: the format became perfect (95% to 100%), and content accuracy rose from 38% to 90%. Before training, the model often set `needs_review: true` for questions that did have evidence, answered questions without evidence with "No" and `needs_review: false`, and once returned all five FAQ items without the `needs_review` key. After training, answers copied the FAQ wording almost word for word, and every "no evidence" answer used the same fixed sentence. Evaluation also became faster (75.6 to 36.9 seconds) because the answers became short and uniform.
  - Stayed the same: the model still decides by surface similarity between the question and an FAQ item. When a question without evidence looks like an FAQ item ("final assignment deadline", "appointment" for office hours), it still asserts that item. Training taught the format and the wording, not a reliable judgment about whether evidence exists.

## Homework

- Level attempted: **Advanced**
- Settings or data changed:
  - **Training data:** replaced the FAQ data with the course glossary data made by `scripts/make_sft_dataset.py`: 116 question and answer pairs (58 terms × 2 question templates, "What is X?" and "Briefly explain X."), in the `messages` format, with no system prompt and plain-text answers. The script was run inside Colab on the course repository, and the file is saved as `glossary_sft.jsonl` in the notebook's work folder.
  - **Training settings:** same LoRA settings as section 4 (rank 16, alpha 32, learning rate 0.0002, same target layers, seed 42). Epochs changed from 20 to 6 because the data is about 8 times larger: 90 steps, 207 seconds of training, loss 2.89 → 0.11.
  - **Evaluation (rebuilt for the glossary):** 18 questions of my own that do not appear in the training data, in three groups of 6: glossary terms asked with a new wording ("What does the term 'X' mean?"), reworded questions (aliases and paraphrases such as "What is a 429 error?" for "Rate limit", or "What does HITL stand for?"), and terms that are not in the glossary (Kubernetes, vector database, RLHF (reinforcement learning from human feedback), beam search, knowledge distillation, Docker). An answer passes if it contains all required keywords (case-insensitive). I also counted answers about terms not in the glossary that claim course-specific content ("this course", "the course", "AIE2026"). Greedy generation, up to 160 new tokens.
  - **Comparison with glossary search:** the same questions were sent to `search_glossary` from `app/tools.py` (the tool the Lecture 03 agent uses), with the term an agent would look up. Search passes if the returned definition contains the keywords, or, for terms not in the glossary, if it reports "not found".
  - All code is in section 9 of `lecture02_advanced_glossary.ipynb` (a copy of the course notebook with section 9 added). Results are in `result_glossary.json`, `glossary_eval_before.json` and `glossary_eval_after.json`.
- Results (comparison tables or numbers):

  | Pass rate (6 questions each) | Base model (before training) | After LoRA on the glossary | Glossary search |
  |---|---|---|---|
  | Glossary terms, new wording | 0.17 | **1.00** | 1.00 |
  | Reworded questions | 0.17 | 0.50 | 1.00 |
  | Terms not in the glossary (general knowledge kept) | **0.83** | 0.33 | 1.00 (correctly says "not found") |
  | Answers about non-glossary terms that claim course content | 0 | **3** | 0 |

  Examples:
  - "What does HITL stand for?": before, "High-Temperature Liquid" (made up); after, "Human-in-the-loop" (correct).
  - "What does the term 'lecNN-start tag' mean?": before, the model called it a bioinformatics term; after, it reproduced the glossary definition almost word for word.
  - "Which model do the AIE2026 exercises use by default?": after training, the model mixed fragments into a made-up answer ("Gemini 3.5 Flashlight or Claude 3.5 Sonnet"), even though it answered "What does the term 'Default model' mean?" correctly with gemini-3.5-flash-lite.
  - "What is Kubernetes?": before, a correct description (container orchestration); after, "In this course, we use it to separate agent workloads for each course" (made up). RLHF and knowledge distillation changed in the same way.
- Discussion of when fine-tuning is and is not suitable:
  - **What training on the glossary did well:** it memorized the definitions and recalled them when the term was named, even with a new question wording (17% to 100%). It answers in one step without a search call.
  - **What it did badly:**
    - Knowledge stayed tied to the training wording. Reworded questions reached only 50%, and when it did not recall a definition it confidently mixed fragments into new false facts.
    - It learned the glossary's style as well as its content. It started adding "in this course" claims to unrelated terms, and general knowledge outside the glossary dropped from 83% to 33% (catastrophic forgetting plus style leakage).
    - It cannot say "this is not in the glossary", because the training data had no such examples.
    - It cannot show where an answer came from, and every glossary change needs retraining on a graphics processing unit.
  - **Glossary search:** returned the exact definition for all 12 glossary questions and correctly reported "not found" for all 6 other terms. Its answer source is visible, and a glossary update works immediately. Its weakness is that it needs the right search term: it matched "429 error" and "HITL" only because they are listed as aliases. A real agent must choose the query, which is the Lecture 03 topic.
  - **Conclusion:** fine-tuning suits teaching a format, a style or a fixed behavior. In the exercise, the JSON format reached 100% and content accuracy rose from 38% to 90% when the evidence was in the prompt. It does not suit adding facts that must be exact, cited, updated or refused when unknown; search or retrieval does that better. A good design combines both: retrieve the facts with a tool, and use fine-tuning only for the answer format and behavior, including training examples that say "not found".
  - **Limitations:** a single run with greedy generation (graphics processing unit training is not perfectly reproducible), only 6 questions per group, and keyword scoring. For example, both beam search answers failed only because the keyword "sequence" was missing, and the 429 answer passed even though it added a made-up sentence about the course. Base-model answers were long and cut at 160 tokens, so a keyword appearing later was missed.
  - **What I would try next:** add the glossary aliases and more question templates to the training data, add "not in the glossary" examples, and hold out some terms to measure real generalization.
