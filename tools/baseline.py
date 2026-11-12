"""Lecture 04 homework: baseline of the Lecture 03 agent on my own evaluation set (quality, time, cost).

For every run and every case, this script:
  1. asks the agent (app.agent: same model, INSTRUCTIONS and tools as Lecture 03) and measures the time of the
     successful call, the model requests, tool calls, tokens and the estimated price;
  2. grades the answer with the LLM grader of app.judge (same rubric.md, temperature 0) and checks the
     lecture marker with code.
Each result is appended to a JSON Lines file at once, so an interrupted run continues where it stopped.
The estimated price is Pydantic AI's list-price estimate; the free tier is not charged.

Usage (from the repository root):
    uv run python tools/baseline.py --runs 1 --write-answers   # run 1, then copy its answers into my_cases.jsonl for labeling
    uv run python tools/baseline.py --runs 3                   # add runs 2 and 3 (recorded cases are skipped)
    uv run python tools/baseline.py --summary-only             # rebuild the summary from the records
"""

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pydantic_ai.exceptions import ModelAPIError  # noqa: E402
from pydantic_ai.messages import ToolCallPart  # noqa: E402

from app import judge  # noqa: E402
from app.config import MODEL  # noqa: E402
from tools.judge_retry import MAX_TRIES, describe, is_temporary, retry_delay  # noqa: E402

DEFAULT_CASES = ROOT / "data" / "eval" / "my_cases.jsonl"
DEFAULT_OUT = ROOT / "lectures" / "04" / "baseline"
SHORT = {"pass": "P", "fail": "F", "unsure": "U"}


def timed_call(agent, *args, sleep=time.sleep, **kwargs):
    """Run agent.run_sync with retries for temporary errors. Return (result, seconds of the successful try, retries)."""
    for attempt in range(1, MAX_TRIES + 1):
        start = time.perf_counter()
        try:
            result = agent.run_sync(*args, **kwargs)
            return result, time.perf_counter() - start, attempt - 1
        except ModelAPIError as e:
            if not is_temporary(e) or attempt == MAX_TRIES:
                raise
            delay = retry_delay(e, attempt)
            print(f"\n  [retry] {describe(e)}; waiting {delay} seconds (attempt {attempt} of {MAX_TRIES})", flush=True)
            sleep(delay)


def usage_dict(usage) -> dict:
    cost = getattr(usage, "cost", None)
    return {
        "requests": usage.requests,
        "tool_calls": usage.tool_calls,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cost_usd": float(cost) if cost is not None else None,
    }


def tools_called(result) -> list[str]:
    return [p.tool_name for m in result.all_messages() for p in m.parts if isinstance(p, ToolCallPart)]


def run_case(agent, model, grader, case: dict, run: int, settings: dict) -> dict:
    """Answer one case with the agent, grade it, and return one record."""
    result, seconds, retries = timed_call(agent, case["question"], model=model, model_settings=settings)
    answer = str(result.output)
    graded, grade_seconds, grade_retries = timed_call(grader, judge.judge_prompt({**case, "answer": answer}),
                                                      model_settings=settings)
    verdicts = {key: getattr(graded.output, key).model_dump() for key, _ in judge.LLM_CRITERIA}
    verdicts["lecture_mark"] = {"reason": "Code check of the final line", "verdict": judge.check_lecture_mark(answer)}
    return {
        "run": run, "id": case["id"], "split": case.get("split", ""), "category": case.get("category", ""),
        "question": case["question"], "answer": answer,
        "seconds": round(seconds, 2), "retries": retries, "tools": tools_called(result), **usage_dict(result.usage),
        "verdicts": verdicts, "overall": judge.overall({k: verdicts[k]["verdict"] for k in judge.REQUIRED}),
        "grading": {"seconds": round(grade_seconds, 2), "retries": grade_retries, **usage_dict(graded.usage)},
    }


def read_records(path: Path) -> list[dict]:
    return judge.read_jsonl(path) if path.exists() else []


def pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.0f}%" if whole else "n/a"


def summarize(records: list[dict], model_name: str = MODEL) -> str:
    """Markdown summary: quality by run, time and cost by run, consistency across runs, and every case."""
    runs = sorted({r["run"] for r in records})
    out = [f"# Baseline of the Lecture 03 agent on my evaluation set\n",
           f"Agent and grader model: `{model_name}`. Grader: app.judge with data/eval/rubric.md, temperature 0. "
           f"Lecture marker checked by code. Overall = all required criteria (Grounding, Scope, Hint, Lecture marker) pass.\n"]

    for split in ["all", "tuning", "report"]:
        recs = [r for r in records if split == "all" or r["split"] == split]
        if not recs:
            continue
        out.append(f"## Quality by run ({split})\n")
        head = "| Run | Cases | Overall pass | " + " | ".join(n for _, n in judge.ALL_CRITERIA) + " |"
        out += [head, "|" + "---|" * (3 + len(judge.ALL_CRITERIA))]
        for run in runs:
            rr = [r for r in recs if r["run"] == run]
            cells = []
            for key, _ in judge.ALL_CRITERIA:
                c = Counter(r["verdicts"][key]["verdict"] for r in rr)
                extra = f" (+{c['unsure']} unsure)" if c["unsure"] else ""
                cells.append(f"{c['pass']}/{c['pass'] + c['fail']}{extra}")
            passed = sum(r["overall"] == "pass" for r in rr)
            unsure = sum(r["overall"] == "unsure" for r in rr)
            extra = f" (+{unsure} unsure)" if unsure else ""
            out.append(f"| {run} | {len(rr)} | {passed}/{len(rr)} = {pct(passed, len(rr))}{extra} | " + " | ".join(cells) + " |")
        out.append("")

    out.append("## Time and cost by run (all cases)\n")
    out += ["| Run | Mean seconds per answer | Median | Slowest | Model requests (mean) | Tool calls (total) | "
            "Input tokens | Output tokens | Estimated agent price (USD) | Grading tokens (in/out) | Estimated grading price (USD) | Retries |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for run in runs:
        rr = [r for r in records if r["run"] == run]
        secs = [r["seconds"] for r in rr]
        cost = sum(r["cost_usd"] or 0 for r in rr)
        gcost = sum(r["grading"]["cost_usd"] or 0 for r in rr)
        out.append(f"| {run} | {mean(secs):.1f} | {median(secs):.1f} | {max(secs):.1f} | {mean(r['requests'] for r in rr):.2f} | "
                   f"{sum(r['tool_calls'] for r in rr)} | {sum(r['input_tokens'] for r in rr):,} | {sum(r['output_tokens'] for r in rr):,} | "
                   f"{cost:.4f} | {sum(r['grading']['input_tokens'] for r in rr):,}/{sum(r['grading']['output_tokens'] for r in rr):,} | "
                   f"{gcost:.4f} | {sum(r['retries'] + r['grading']['retries'] for r in rr)} |")
    out.append("")

    by_case = defaultdict(dict)
    for r in records:
        by_case[r["id"]][r["run"]] = r
    complete = {cid: rs for cid, rs in by_case.items() if all(run in rs for run in runs)}
    if len(runs) > 1 and complete:
        always = [c for c, rs in complete.items() if all(r["overall"] == "pass" for r in rs.values())]
        never = [c for c, rs in complete.items() if all(r["overall"] == "fail" for r in rs.values())]
        changed = [c for c in complete if c not in always and c not in never]
        out.append(f"## Consistency across {len(runs)} runs ({len(complete)} cases with every run)\n")
        out.append(f"- Passed in every run (pass^{len(runs)}): {len(always)}/{len(complete)} = {pct(len(always), len(complete))}")
        out.append(f"- Failed in every run: {len(never)}/{len(complete)} ({', '.join('#' + c for c in sorted(never)) or 'none'})")
        out.append(f"- Result changed between runs: {len(changed)}/{len(complete)} ({', '.join('#' + c for c in sorted(changed)) or 'none'})\n")

    out.append("## Every case (overall result per run; P = pass, F = fail, U = unsure)\n")
    out += ["| Case | Split | Category | " + " | ".join(f"Run {r}" for r in runs) + " | Failed criteria (all runs) | Mean seconds |",
            "|" + "---|" * (5 + len(runs))]
    for cid in sorted(by_case):
        rs = by_case[cid]
        any_r = next(iter(rs.values()))
        failed = sorted({n for r in rs.values() for k, n in judge.ALL_CRITERIA if r["verdicts"][k]["verdict"] == "fail"})
        cells = " | ".join(SHORT.get(rs[run]["overall"], "-") if run in rs else "-" for run in runs)
        out.append(f"| #{cid} | {any_r['split']} | {any_r['category']} | {cells} | {', '.join(failed) or '-'} | "
                   f"{mean(r['seconds'] for r in rs.values()):.1f} |")
    return "\n".join(out) + "\n"


def write_answers(cases_path: Path, records: list[dict], run: int = 1) -> int:
    """Copy one run's answers into the evaluation set, so that it can be labeled and graded with app.judge."""
    answers = {r["id"]: r["answer"] for r in records if r["run"] == run}
    cases = judge.read_jsonl(cases_path)
    for case in cases:
        if case["id"] in answers:
            case["answer"] = answers[case["id"]]
    judge.write_jsonl(cases_path, cases)
    return len(answers)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Baseline of the Lecture 03 agent on an evaluation set")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--rubric", type=Path, default=judge.DEFAULT_RUBRIC)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--runs", type=int, default=3, help="Total number of runs to have recorded")
    parser.add_argument("--wait", type=float, default=10.0, help="Seconds between cases (3 model calls per case; free tier: 15 per minute)")
    parser.add_argument("--timeout", type=float, default=120.0, help="Seconds allowed per model request")
    parser.add_argument("--write-answers", action="store_true", help="After run 1, copy its answers into --cases")
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args(argv)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    records_path = args.out_dir / "records.jsonl"
    records = read_records(records_path)

    if not args.summary_only:
        from app.agent import agent, build_model

        cases = judge.read_jsonl(args.cases)
        model = build_model()
        grader = judge.build_judge(judge.build_llm_model(MODEL), args.rubric.read_text(encoding="utf-8"))
        settings = {"timeout": args.timeout}
        done = {(r["run"], r["id"]) for r in records}
        for run in range(1, args.runs + 1):
            todo = [c for c in cases if (run, c["id"]) not in done]
            if not todo:
                continue
            print(f"Run {run}: {len(todo)} cases ", end="", flush=True)
            for case in todo:
                record = run_case(agent, model, grader, case, run, settings)
                with open(records_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                records.append(record)
                print(SHORT.get(record["overall"], "?"), end="", flush=True)
                time.sleep(args.wait)
            print()
        if args.write_answers:
            n = write_answers(args.cases, records, run=1)
            print(f"→ Copied {n} answers from run 1 into {judge._rel(args.cases)}")

    summary = summarize(records)
    (args.out_dir / "summary.md").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
