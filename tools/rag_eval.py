"""Lecture 05 homework: compare retrieval methods on questions whose evidence pages are known.

For each question in the question set, every method is run on the same query embedding, and we count how many of
the known evidence pages it returns, how many pages it returns, and how much text it would add to the model input.
No answer is generated, so this costs one embedding call per question (none if the embeddings are already saved).

Usage (from the repository root):
    uv run python tools/rag_eval.py --questions data/eval/lec05_questions.jsonl \
        --embeddings lectures/05/runs/query_embeddings.json --out lectures/05/runs/retrieval_eval.md

The query embeddings are saved so the comparison can be repeated (and new settings tried) without the API.
"""

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import retrieval  # noqa: E402


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def embed_questions(questions: list[dict], cache_path: Path) -> dict[str, list[float]]:
    """Return question text → query vector, calling the API only for questions not yet saved."""
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.is_file() else {}
    real_embed = retrieval.embed_text
    for q in questions:
        text = q["question"].strip()
        if text in cache:
            continue
        for attempt in range(1, 5):
            try:
                cache[text] = real_embed(text, "RETRIEVAL_QUERY")
                break
            except Exception as e:  # rate limits and busy errors: wait and retry
                if attempt == 4:
                    raise
                print(f"  embedding failed ({type(e).__name__}: {str(e)[:80]}); retrying in 30 seconds")
                time.sleep(30)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache), encoding="utf-8")
        time.sleep(2)
    return cache


def use_saved_embeddings(cache: dict[str, list[float]]) -> None:
    """Make retrieval use the saved vectors instead of calling the API."""
    def embed(text: str, task_type: str) -> list[float]:
        if text.strip() not in cache:
            raise KeyError(f"No saved embedding for: {text[:60]}")
        return cache[text.strip()]
    retrieval.embed_text = embed


def graph_pages(query: str) -> list[dict]:
    found = retrieval.search_graph(query)
    return found["seeds"] + found["expanded"]


METHODS = {
    "Vector search, top 5 (provided)": lambda q: retrieval.search(q, top_k=5),
    "Vector search, top 10 (Basic)": lambda q: retrieval.search(q, top_k=10),
    "Vector top 5 + adjacent pages (Implementation)": lambda q: retrieval.add_neighbor_pages(retrieval.search(q, top_k=5)),
    "Graph (provided)": graph_pages,
    "Hybrid (Advanced)": lambda q: retrieval.search_hybrid(q)["results"],
}
ABLATIONS = {
    "Hybrid without the divider-page filter": lambda q: retrieval.search_hybrid(q, min_chars=0)["results"],
    "Hybrid without keeping a page per named lecture": lambda q: retrieval.search_hybrid(q, reserve_lectures=False)["results"],
    "Hybrid without the question-term bonus": lambda q: retrieval.search_hybrid(q, term_bonus=0.0)["results"],
    "Hybrid without the per-section cap": lambda q: retrieval.search_hybrid(q, max_per_section=99)["results"],
    "Vector search, top 7 (same page count as hybrid)": lambda q: retrieval.search(q, top_k=7),
}


def evaluate(questions: list[dict], methods: dict) -> list[dict]:
    rows = []
    for name, run in methods.items():
        for q in questions:
            pages = run(q["question"])
            ids = [p["page_id"] for p in pages]
            evidence = q["evidence"]
            rows.append({
                "method": name, "question": q["id"], "pages": ids,
                "found": [e for e in evidence if e in ids], "evidence": evidence,
                "characters": sum(len(p["content"]) for p in pages),
            })
    return rows


def evidence_ranks(questions: list[dict]) -> list[str]:
    """Where each evidence page sits in the full similarity ranking (1 = most similar of 214 pages)."""
    lines = []
    for q in questions:
        if not q["evidence"]:
            continue
        distance = retrieval.page_distances(q["question"])
        ranked = sorted(distance, key=lambda pid: (distance[pid], pid))
        parts = [f"{e} = rank {ranked.index(e) + 1}" for e in q["evidence"]]
        lines.append(f"- {q['id']}: " + ", ".join(parts))
    return lines


def summary_table(rows: list[dict], questions: list[dict], methods: list[str]) -> list[str]:
    answerable = [q["id"] for q in questions if q["evidence"]]
    total = sum(len(q["evidence"]) for q in questions)
    lines = ["| Method | Evidence pages found (of %d) | Questions with all evidence (of %d) | Average pages returned | Average characters returned |" % (total, len(answerable)),
             "|---|---|---|---|---|"]
    for m in methods:
        mine = [r for r in rows if r["method"] == m]
        found = sum(len(r["found"]) for r in mine)
        complete = sum(1 for r in mine if r["question"] in answerable and len(r["found"]) == len(r["evidence"]))
        pages = sum(len(r["pages"]) for r in mine) / len(mine)
        chars = sum(r["characters"] for r in mine) / len(mine)
        lines.append(f"| {m} | {found} | {complete} | {pages:.1f} | {chars:,.0f} |")
    return lines


def detail_table(rows: list[dict], questions: list[dict], methods: list[str]) -> list[str]:
    lines = ["| Method | " + " | ".join(q["id"] for q in questions) + " |", "|---|" + "---|" * len(questions)]
    for m in methods:
        cells = []
        for q in questions:
            r = next(r for r in rows if r["method"] == m and r["question"] == q["id"])
            got = f"{len(r['found'])}/{len(r['evidence'])}" if r["evidence"] else "n/a"
            cells.append(f"{got} · {len(r['pages'])} p · {r['characters']:,} ch")
        lines.append(f"| {m} | " + " | ".join(cells) + " |")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare retrieval methods on questions with known evidence pages")
    parser.add_argument("--questions", type=Path, default=ROOT / "data/eval/lec05_questions.jsonl")
    parser.add_argument("--embeddings", type=Path, default=ROOT / "lectures/05/runs/query_embeddings.json")
    parser.add_argument("--out", type=Path, default=ROOT / "lectures/05/runs/retrieval_eval.md")
    args = parser.parse_args()

    questions = read_jsonl(args.questions)
    cache = embed_questions(questions, args.embeddings)
    use_saved_embeddings(cache)
    rows = evaluate(questions, {**METHODS, **ABLATIONS})

    out = ["# Retrieval comparison on questions with known evidence pages", "",
           "Same query embedding for every method. No answers are generated here; this measures only what each method returns.",
           "Characters = total page text returned (a rough measure of added input).", "",
           "## Summary", "", *summary_table(rows, questions, list(METHODS)), "",
           "## Per question (evidence found · pages · characters)", "", *detail_table(rows, questions, list(METHODS)), "",
           "## Ablation of the hybrid method", "", *summary_table(rows, questions, ["Hybrid (Advanced)", *ABLATIONS]), "",
           "## Where the evidence pages rank by similarity alone (214 pages)", "", *evidence_ranks(questions), "",
           "## Pages returned", ""]
    for r in rows:
        if r["method"] in METHODS:
            missing = [e for e in r["evidence"] if e not in r["found"]]
            out.append(f"- {r['method']} · {r['question']}: {', '.join(r['pages'])}"
                       + (f" — missing: {', '.join(missing)}" if missing else ""))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(out) + "\n", encoding="utf-8")
    args.out.with_suffix(".json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("\n".join(out[:40]))
    print(f"\nSaved: {args.out}")


if __name__ == "__main__":
    main()
