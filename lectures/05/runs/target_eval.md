# Retrieval comparison on questions with known evidence pages

Same query embedding for every method. No answers are generated here; this measures only what each method returns.
Characters = total page text returned (a rough measure of added input).

## Summary

| Method | Evidence pages found (of 6) | Questions with all evidence (of 3) | Average pages returned | Average characters returned |
|---|---|---|---|---|
| Vector search, top 5 (provided) | 4 | 1 | 5.0 | 3,522 |
| Vector search, top 10 (Basic) | 4 | 1 | 10.0 | 8,094 |
| Vector top 5 + adjacent pages (Implementation) | 4 | 1 | 13.7 | 10,570 |
| Graph (provided) | 3 | 0 | 10.0 | 7,547 |
| Hybrid (Advanced) | 4 | 1 | 7.0 | 6,212 |

## Per question (evidence found · pages · characters)

| Method | t1_rsi | t2_errors | t3_schedule |
|---|---|---|---|
| Vector search, top 5 (provided) | 2/2 · 5 p · 2,820 ch | 1/2 · 5 p · 3,212 ch | 1/2 · 5 p · 4,535 ch |
| Vector search, top 10 (Basic) | 2/2 · 10 p · 7,393 ch | 1/2 · 10 p · 7,360 ch | 1/2 · 10 p · 9,529 ch |
| Vector top 5 + adjacent pages (Implementation) | 2/2 · 13 p · 8,512 ch | 1/2 · 13 p · 8,129 ch | 1/2 · 15 p · 15,068 ch |
| Graph (provided) | 1/2 · 10 p · 6,076 ch | 1/2 · 10 p · 7,296 ch | 1/2 · 10 p · 9,268 ch |
| Hybrid (Advanced) | 2/2 · 7 p · 5,758 ch | 1/2 · 7 p · 6,134 ch | 1/2 · 7 p · 6,745 ch |

## Ablation of the hybrid method

| Method | Evidence pages found (of 6) | Questions with all evidence (of 3) | Average pages returned | Average characters returned |
|---|---|---|---|---|
| Hybrid (Advanced) | 4 | 1 | 7.0 | 6,212 |
| Hybrid without the divider-page filter | 4 | 1 | 7.0 | 5,518 |
| Hybrid without keeping a page per named lecture | 4 | 1 | 7.0 | 5,835 |
| Hybrid without the question-term bonus | 4 | 1 | 7.0 | 6,212 |
| Hybrid without the per-section cap | 4 | 1 | 7.0 | 6,212 |
| Vector search, top 7 (same page count as hybrid) | 4 | 1 | 7.0 | 5,085 |

## Where the evidence pages rank by similarity alone (214 pages)

- t1_rsi: lec01-main-p010 = rank 4, lec03-main-p055 = rank 1
- t2_errors: lec03-main-p019 = rank 1, lec01-main-p009 = rank 51
- t3_schedule: lec02-main-p022 = rank 2, lec01-main-p049 = rank 14

## Pages returned

- Vector search, top 5 (provided) · t1_rsi: lec03-main-p055, lec03-main-p058, lec03-main-p054, lec01-main-p010, lec03-main-p021
- Vector search, top 5 (provided) · t2_errors: lec03-main-p019, lec03-main-p018, lec03-main-p046, lec03-main-p003, lec03-main-p054 — missing: lec01-main-p009
- Vector search, top 5 (provided) · t3_schedule: lec02-main-p003, lec02-main-p022, lec02-main-p014, lec02-main-p027, lec02-main-p053 — missing: lec01-main-p049
- Vector search, top 10 (Basic) · t1_rsi: lec03-main-p055, lec03-main-p058, lec03-main-p054, lec01-main-p010, lec03-main-p021, lec03-main-p057, lec03-main-p069, lec03-main-p020, lec02-main-p029, lec03-main-p004
- Vector search, top 10 (Basic) · t2_errors: lec03-main-p019, lec03-main-p018, lec03-main-p046, lec03-main-p003, lec03-main-p054, lec03-main-p020, lec03-main-p045, lec02-main-p017, lec03-main-p004, lec02-main-p062 — missing: lec01-main-p009
- Vector search, top 10 (Basic) · t3_schedule: lec02-main-p003, lec02-main-p022, lec02-main-p014, lec02-main-p027, lec02-main-p053, lec02-main-p019, lec02-main-p005, lec02-main-p015, lec01-main-p019, lec02-main-p026 — missing: lec01-main-p049
- Vector top 5 + adjacent pages (Implementation) · t1_rsi: lec03-main-p055, lec03-main-p056, lec03-main-p057, lec03-main-p058, lec03-main-p059, lec03-main-p053, lec03-main-p054, lec01-main-p009, lec01-main-p010, lec01-main-p011, lec03-main-p020, lec03-main-p021, lec03-main-p022
- Vector top 5 + adjacent pages (Implementation) · t2_errors: lec03-main-p019, lec03-main-p020, lec03-main-p017, lec03-main-p018, lec03-main-p045, lec03-main-p046, lec03-main-p047, lec03-main-p002, lec03-main-p003, lec03-main-p004, lec03-main-p053, lec03-main-p054, lec03-main-p055 — missing: lec01-main-p009
- Vector top 5 + adjacent pages (Implementation) · t3_schedule: lec02-main-p002, lec02-main-p003, lec02-main-p004, lec02-main-p021, lec02-main-p022, lec02-main-p023, lec02-main-p013, lec02-main-p014, lec02-main-p015, lec02-main-p026, lec02-main-p027, lec02-main-p028, lec02-main-p052, lec02-main-p053, lec02-main-p054 — missing: lec01-main-p049
- Graph (provided) · t1_rsi: lec03-main-p055, lec03-main-p058, lec03-main-p054, lec03-main-p056, lec03-main-p057, lec03-main-p059, lec03-main-p053, lec03-main-p060, lec03-main-p052, lec01-main-p046 — missing: lec01-main-p010
- Graph (provided) · t2_errors: lec03-main-p019, lec03-main-p018, lec03-main-p046, lec03-main-p020, lec03-main-p017, lec03-main-p045, lec03-main-p047, lec03-main-p021, lec03-main-p016, lec03-main-p044 — missing: lec01-main-p009
- Graph (provided) · t3_schedule: lec02-main-p003, lec02-main-p022, lec02-main-p014, lec02-main-p002, lec02-main-p004, lec02-main-p021, lec02-main-p023, lec02-main-p013, lec02-main-p015, lec02-main-p001 — missing: lec01-main-p049
- Hybrid (Advanced) · t1_rsi: lec03-main-p055, lec03-main-p058, lec01-main-p010, lec03-main-p021, lec03-main-p057, lec03-main-p069, lec03-main-p020
- Hybrid (Advanced) · t2_errors: lec03-main-p019, lec03-main-p046, lec03-main-p003, lec03-main-p020, lec03-main-p045, lec02-main-p017, lec01-main-p041 — missing: lec01-main-p009
- Hybrid (Advanced) · t3_schedule: lec02-main-p003, lec02-main-p022, lec02-main-p014, lec02-main-p027, lec02-main-p053, lec02-main-p019, lec01-main-p019 — missing: lec01-main-p049
