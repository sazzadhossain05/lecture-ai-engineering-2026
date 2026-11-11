"""Lecture 04 homework: agreement between two graders (Cohen's kappa), the LLM grader's miss rate, and code checks.

Agreement alone can look high when almost every item passes, so Cohen's kappa corrects for the agreement
expected by chance: kappa = (observed agreement - chance agreement) / (1 - chance agreement).
1 means perfect agreement, 0 means no better than chance. It is undefined when both graders give one
single class to every item (chance agreement is 1).

Usage (from the repository root):
    # Two humans: my labels versus the instructor's labels (exercise set, no API key needed)
    uv run python tools/eval_stats.py --labels lectures/04/labels.jsonl --other lectures/04/reference/labels_instructor.jsonl
    # My labels versus the LLM grader on my own set, for all cases and for each split
    uv run python tools/eval_stats.py --labels lectures/04/my_labels.jsonl --judge lectures/04/my_judge_result.json --cases data/eval/my_cases.jsonl
"""

import argparse
import json
import re
import sys
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.judge import ALL_CRITERIA, REQUIRED, load_labels, overall, read_jsonl  # noqa: E402

PASS, FAIL = "pass", "fail"


def cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    """Cohen's kappa for pass/fail pairs (reference, other). Returns None when it is undefined."""
    n = len(pairs)
    if n == 0:
        return None
    observed = sum(a == b for a, b in pairs) / n
    a_pass = sum(a == PASS for a, _ in pairs) / n
    b_pass = sum(b == PASS for _, b in pairs) / n
    chance = a_pass * b_pass + (1 - a_pass) * (1 - b_pass)
    if chance >= 1:
        return None
    return (observed - chance) / (1 - chance)


def compare(reference: dict[str, dict], other: dict[str, dict], ids: list[str], keys: list[str]) -> dict:
    """Compare two graders criterion by criterion. `reference` is the human; `other` is the second grader.

    Items where either side is not pass/fail (for example the LLM's unsure) are excluded and counted.
    missed = other passes what the reference fails; false_alarm = other fails what the reference passes.
    """
    stats = {}
    for key in keys:
        pairs, excluded = [], 0
        for cid in ids:
            a, b = reference[cid].get(key), other[cid].get(key)
            if a in (PASS, FAIL) and b in (PASS, FAIL):
                pairs.append((a, b))
            else:
                excluded += 1
        ref_fails = sum(a == FAIL for a, _ in pairs)
        missed = sum(a == FAIL and b == PASS for a, b in pairs)
        stats[key] = {
            "n": len(pairs),
            "agree": sum(a == b for a, b in pairs),
            "kappa": cohen_kappa(pairs),
            "missed": missed,
            "false_alarm": sum(a == PASS and b == FAIL for a, b in pairs),
            "excluded": excluded,
            "reference_fails": ref_fails,
            "miss_rate": (missed / ref_fails) if ref_fails else None,
        }
    return stats


def with_overall(grades: dict[str, dict]) -> dict[str, dict]:
    """Add an "overall" entry computed like app.judge: all required criteria must pass."""
    out = {}
    for cid, g in grades.items():
        verdicts = {k: g.get(k, "unsure") if g.get(k) in (PASS, FAIL, "unsure") else "unsure" for k in REQUIRED}
        out[cid] = {**g, "overall": overall(verdicts)}
    return out


def load_judge(path: Path) -> dict[str, dict]:
    """Read the verdicts saved by app.judge (judge_result.json) as id → {criterion: verdict}."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {cid: {k: v["verdict"] for k, v in crit.items()} for cid, crit in data["verdicts"].items()}


def fmt_kappa(k: float | None) -> str:
    return "undefined (one class only)" if k is None else f"{k:.2f}"


def table(stats: dict, names: dict[str, str]) -> str:
    rows = ["| Criterion | Compared | Agreement | Cohen's kappa | Missed failures | False alarms | Excluded (unsure) | Miss rate |",
            "|---|---|---|---|---|---|---|---|"]
    for key, s in stats.items():
        miss = "no failures" if s["miss_rate"] is None else f"{s['missed']}/{s['reference_fails']} = {100 * s['miss_rate']:.0f}%"
        rows.append(f"| {names.get(key, key)} | {s['n']} | {s['agree']}/{s['n']} | {fmt_kappa(s['kappa'])} | "
                    f"{s['missed']} | {s['false_alarm']} | {s['excluded']} | {miss} |")
    return "\n".join(rows)


def word_count(text: str) -> int:
    return len(re.sub(r"```.*?```", " ", text, flags=re.S).split())


def code_signals(cases: list[dict], labels: dict[str, dict]) -> str:
    """Simple checks code can do, compared with my labels: answer length versus Clarity, code blocks versus Hint."""
    lines = []
    clar = {v: [word_count(c["answer"]) for c in cases if labels.get(c["id"], {}).get("clarity") == v] for v in (PASS, FAIL)}
    for v in (PASS, FAIL):
        if clar[v]:
            lines.append(f"- Clarity {v}: {len(clar[v])} answer(s), words (code excluded) mean {mean(clar[v]):.0f}, "
                         f"median {median(clar[v]):.0f}, range {min(clar[v])} to {max(clar[v])}")
    with_code = [c["id"] for c in cases if "```" in c["answer"]]
    hint_fail = [c["id"] for c in cases if labels.get(c["id"], {}).get("hint") == FAIL]
    lines.append(f"- Answers containing a code block: {', '.join('#' + i for i in with_code) or 'none'}; "
                 f"Hint failures in my labels: {', '.join('#' + i for i in hint_fail) or 'none'}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Agreement statistics between two graders")
    parser.add_argument("--labels", type=Path, required=True, help="Reference labels (my labels, jsonl)")
    parser.add_argument("--other", type=Path, help="A second human label file (jsonl)")
    parser.add_argument("--judge", type=Path, help="LLM grading result saved by app.judge (json)")
    parser.add_argument("--cases", type=Path, help="Evaluation set; enables per-split results and code checks")
    args = parser.parse_args(argv)
    if bool(args.other) == bool(args.judge):
        parser.error("Give exactly one of --other or --judge")

    names = {**dict(ALL_CRITERIA), "overall": "Overall (required criteria)"}
    reference = with_overall(load_labels(args.labels))
    other = with_overall(load_labels(args.other)) if args.other else load_judge(args.judge)
    if args.judge:
        other = {cid: {**g, "overall": overall({k: g[k] for k in REQUIRED})} for cid, g in other.items()}
    other_name = args.other.name if args.other else f"LLM grader ({args.judge.name})"

    cases = read_jsonl(args.cases) if args.cases else []
    groups = {"all": [cid for cid in reference if cid in other]}
    for split in sorted({c.get("split") for c in cases if c.get("split")}):
        groups[split] = [c["id"] for c in cases if c.get("split") == split and c["id"] in reference and c["id"] in other]

    keys = [k for k, _ in ALL_CRITERIA] + ["overall"]
    print(f"# Agreement: my labels ({args.labels.name}) versus {other_name}\n")
    for group, ids in groups.items():
        print(f"## {group} ({len(ids)} cases)\n")
        print(table(compare(reference, other, ids, keys), names))
        print()
    if cases:
        print("## Code signals compared with my labels\n")
        print(code_signals(cases, reference))


if __name__ == "__main__":
    main()
