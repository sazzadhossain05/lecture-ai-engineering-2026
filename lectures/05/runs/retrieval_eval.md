# Retrieval comparison on questions with known evidence pages

Same query embedding for every method. No answers are generated here; this measures only what each method returns.
Characters = total page text returned (a rough measure of added input).

## Summary

| Method | Evidence pages found (of 11) | Questions with all evidence (of 5) | Average pages returned | Average characters returned |
|---|---|---|---|---|
| Vector search, top 5 (provided) | 10 | 4 | 5.0 | 4,777 |
| Vector search, top 10 (Basic) | 11 | 5 | 10.0 | 9,057 |
| Vector top 5 + adjacent pages (Implementation) | 11 | 5 | 12.7 | 10,717 |
| Graph (provided) | 10 | 4 | 10.0 | 8,899 |
| Hybrid (Advanced) | 11 | 5 | 7.0 | 6,539 |

## Per question (evidence found · pages · characters)

| Method | q1_lora | q2_memory | q3_properties | q4_rag_vs_ft | q5_stop | q6_absent |
|---|---|---|---|---|---|---|
| Vector search, top 5 (provided) | 1/1 · 5 p · 5,844 ch | 3/3 · 5 p · 3,929 ch | 2/2 · 5 p · 3,977 ch | 2/3 · 5 p · 5,666 ch | 2/2 · 5 p · 3,488 ch | n/a · 5 p · 5,757 ch |
| Vector search, top 10 (Basic) | 1/1 · 10 p · 11,428 ch | 3/3 · 10 p · 6,948 ch | 2/2 · 10 p · 7,586 ch | 3/3 · 10 p · 10,048 ch | 2/2 · 10 p · 7,362 ch | n/a · 10 p · 10,971 ch |
| Vector top 5 + adjacent pages (Implementation) | 1/1 · 11 p · 11,464 ch | 3/3 · 11 p · 8,084 ch | 2/2 · 13 p · 7,686 ch | 3/3 · 15 p · 14,230 ch | 2/2 · 11 p · 8,152 ch | n/a · 15 p · 14,688 ch |
| Graph (provided) | 1/1 · 10 p · 11,019 ch | 2/3 · 10 p · 9,364 ch | 2/2 · 10 p · 5,993 ch | 3/3 · 10 p · 8,766 ch | 2/2 · 10 p · 7,318 ch | n/a · 10 p · 10,933 ch |
| Hybrid (Advanced) | 1/1 · 7 p · 7,931 ch | 3/3 · 7 p · 5,096 ch | 2/2 · 7 p · 5,203 ch | 3/3 · 7 p · 7,603 ch | 2/2 · 7 p · 5,626 ch | n/a · 7 p · 7,774 ch |

## Ablation of the hybrid method

| Method | Evidence pages found (of 11) | Questions with all evidence (of 5) | Average pages returned | Average characters returned |
|---|---|---|---|---|
| Hybrid (Advanced) | 11 | 5 | 7.0 | 6,539 |
| Hybrid without the divider-page filter | 11 | 5 | 7.0 | 6,468 |
| Hybrid without keeping a page per named lecture | 11 | 5 | 7.0 | 6,539 |
| Hybrid without the question-term bonus | 11 | 5 | 7.0 | 6,643 |
| Hybrid without the per-section cap | 11 | 5 | 7.0 | 6,636 |
| Vector search, top 7 (same page count as hybrid) | 11 | 5 | 7.0 | 6,457 |

## Where the evidence pages rank by similarity alone (214 pages)

- q1_lora: lec02-main-p052 = rank 1
- q2_memory: lec03-main-p013 = rank 5, lec03-main-p039 = rank 2, lec03-main-p040 = rank 4
- q3_properties: lec03-main-p003 = rank 1, lec02-main-p062 = rank 2
- q4_rag_vs_ft: lec02-main-p046 = rank 6, lec02-main-p047 = rank 3, lec01-main-p049 = rank 1
- q5_stop: lec03-main-p043 = rank 1, lec03-main-p044 = rank 2

## Pages returned

- Vector search, top 5 (provided) · q1_lora: lec02-main-p052, lec02-main-p051, lec02-main-p060, lec02-main-p061, lec02-main-p047
- Vector search, top 5 (provided) · q2_memory: lec03-main-p065, lec03-main-p039, lec03-main-p038, lec03-main-p040, lec03-main-p013
- Vector search, top 5 (provided) · q3_properties: lec03-main-p003, lec02-main-p062, lec03-main-p013, lec03-main-p004, lec03-main-p008
- Vector search, top 5 (provided) · q4_rag_vs_ft: lec01-main-p049, lec01-main-p019, lec02-main-p047, lec02-main-p053, lec02-main-p027 — missing: lec02-main-p046
- Vector search, top 5 (provided) · q5_stop: lec03-main-p043, lec03-main-p044, lec03-main-p026, lec03-main-p020, lec03-main-p042
- Vector search, top 5 (provided) · q6_absent: lec02-main-p013, lec02-main-p024, lec01-main-p049, lec01-main-p019, lec02-main-p003
- Vector search, top 10 (Basic) · q1_lora: lec02-main-p052, lec02-main-p051, lec02-main-p060, lec02-main-p061, lec02-main-p047, lec02-main-p024, lec02-main-p006, lec02-main-p054, lec02-main-p023, lec02-main-p053
- Vector search, top 10 (Basic) · q2_memory: lec03-main-p065, lec03-main-p039, lec03-main-p038, lec03-main-p040, lec03-main-p013, lec03-main-p041, lec03-main-p037, lec03-main-p008, lec02-main-p015, lec02-main-p046
- Vector search, top 10 (Basic) · q3_properties: lec03-main-p003, lec02-main-p062, lec03-main-p013, lec03-main-p004, lec03-main-p008, lec03-main-p048, lec03-main-p006, lec02-main-p029, lec03-main-p005, lec03-main-p068
- Vector search, top 10 (Basic) · q4_rag_vs_ft: lec01-main-p049, lec01-main-p019, lec02-main-p047, lec02-main-p053, lec02-main-p027, lec02-main-p046, lec02-main-p024, lec02-main-p003, lec02-main-p057, lec02-main-p013
- Vector search, top 10 (Basic) · q5_stop: lec03-main-p043, lec03-main-p044, lec03-main-p026, lec03-main-p020, lec03-main-p042, lec03-main-p048, lec03-main-p045, lec03-main-p046, lec03-main-p025, lec03-main-p047
- Vector search, top 10 (Basic) · q6_absent: lec02-main-p013, lec02-main-p024, lec01-main-p049, lec01-main-p019, lec02-main-p003, lec03-main-p064, lec02-main-p047, lec02-main-p027, lec03-main-p019, lec02-main-p057
- Vector top 5 + adjacent pages (Implementation) · q1_lora: lec02-main-p052, lec02-main-p053, lec02-main-p050, lec02-main-p051, lec02-main-p059, lec02-main-p060, lec02-main-p061, lec02-main-p062, lec02-main-p046, lec02-main-p047, lec02-main-p048
- Vector top 5 + adjacent pages (Implementation) · q2_memory: lec03-main-p064, lec03-main-p065, lec03-main-p066, lec03-main-p039, lec03-main-p037, lec03-main-p038, lec03-main-p040, lec03-main-p041, lec03-main-p012, lec03-main-p013, lec03-main-p014
- Vector top 5 + adjacent pages (Implementation) · q3_properties: lec03-main-p002, lec03-main-p003, lec02-main-p061, lec02-main-p062, lec02-main-p063, lec03-main-p012, lec03-main-p013, lec03-main-p014, lec03-main-p004, lec03-main-p005, lec03-main-p007, lec03-main-p008, lec03-main-p009
- Vector top 5 + adjacent pages (Implementation) · q4_rag_vs_ft: lec01-main-p048, lec01-main-p049, lec01-main-p050, lec01-main-p018, lec01-main-p019, lec01-main-p020, lec02-main-p046, lec02-main-p047, lec02-main-p048, lec02-main-p052, lec02-main-p053, lec02-main-p054, lec02-main-p026, lec02-main-p027, lec02-main-p028
- Vector top 5 + adjacent pages (Implementation) · q5_stop: lec03-main-p043, lec03-main-p044, lec03-main-p045, lec03-main-p025, lec03-main-p026, lec03-main-p027, lec03-main-p019, lec03-main-p020, lec03-main-p021, lec03-main-p041, lec03-main-p042
- Vector top 5 + adjacent pages (Implementation) · q6_absent: lec02-main-p012, lec02-main-p013, lec02-main-p014, lec02-main-p023, lec02-main-p024, lec02-main-p025, lec01-main-p048, lec01-main-p049, lec01-main-p050, lec01-main-p018, lec01-main-p019, lec01-main-p020, lec02-main-p002, lec02-main-p003, lec02-main-p004
- Graph (provided) · q1_lora: lec02-main-p052, lec02-main-p051, lec02-main-p060, lec02-main-p053, lec02-main-p050, lec02-main-p059, lec02-main-p061, lec02-main-p049, lec02-main-p062, lec02-main-p047
- Graph (provided) · q2_memory: lec03-main-p065, lec03-main-p039, lec03-main-p038, lec03-main-p064, lec03-main-p066, lec03-main-p040, lec03-main-p037, lec03-main-p063, lec03-main-p067, lec03-main-p041 — missing: lec03-main-p013
- Graph (provided) · q3_properties: lec03-main-p003, lec02-main-p062, lec03-main-p013, lec03-main-p002, lec03-main-p004, lec02-main-p061, lec02-main-p063, lec03-main-p012, lec03-main-p014, lec03-main-p001
- Graph (provided) · q4_rag_vs_ft: lec01-main-p049, lec01-main-p019, lec02-main-p047, lec01-main-p048, lec01-main-p050, lec01-main-p018, lec01-main-p020, lec02-main-p046, lec02-main-p048, lec01-main-p047
- Graph (provided) · q5_stop: lec03-main-p043, lec03-main-p044, lec03-main-p026, lec03-main-p042, lec03-main-p045, lec03-main-p025, lec03-main-p027, lec03-main-p041, lec03-main-p046, lec03-main-p024
- Graph (provided) · q6_absent: lec02-main-p013, lec02-main-p024, lec01-main-p049, lec02-main-p012, lec02-main-p014, lec02-main-p023, lec02-main-p025, lec01-main-p048, lec01-main-p050, lec02-main-p011
- Hybrid (Advanced) · q1_lora: lec02-main-p052, lec02-main-p051, lec02-main-p060, lec02-main-p061, lec02-main-p024, lec02-main-p006, lec02-main-p023
- Hybrid (Advanced) · q2_memory: lec03-main-p065, lec03-main-p039, lec03-main-p038, lec03-main-p040, lec03-main-p013, lec03-main-p041, lec03-main-p008
- Hybrid (Advanced) · q3_properties: lec03-main-p003, lec02-main-p062, lec03-main-p013, lec03-main-p004, lec03-main-p008, lec03-main-p048, lec03-main-p006
- Hybrid (Advanced) · q4_rag_vs_ft: lec01-main-p049, lec01-main-p019, lec02-main-p047, lec02-main-p053, lec02-main-p027, lec02-main-p046, lec02-main-p024
- Hybrid (Advanced) · q5_stop: lec03-main-p043, lec03-main-p044, lec03-main-p026, lec03-main-p020, lec03-main-p048, lec03-main-p045, lec03-main-p025
- Hybrid (Advanced) · q6_absent: lec02-main-p013, lec02-main-p024, lec01-main-p049, lec01-main-p019, lec02-main-p003, lec02-main-p047, lec02-main-p027
