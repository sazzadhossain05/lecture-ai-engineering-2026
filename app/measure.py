"""Lecture 01 Advanced homework: measure response time and token counts.

Asks every (model, question) pair several times. For every call it records the
response time, the token counts and any error, saves everything to CSV, and
prints a summary table that compares the models and questions.

Usage:
    uv run python -m app.measure
    uv run python -m app.measure --runs 5
    uv run python -m app.measure --models gemini-3.5-flash-lite gemini-3.1-flash-lite

The free tier limits requests per minute and per day, so the script waits
between calls, retries "model is busy" (503) errors a few times, and stops
calling a model that keeps hitting its rate limit (429).
"""

from __future__ import annotations

import argparse
import csv
import statistics
import time
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from pathlib import Path

from google import genai
from google.genai import errors

from app.config import get_api_key

DEFAULT_MODELS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]

# Three questions with different expected answer lengths:
# a course-specific fact the model cannot know, a short answer and a long answer.
QUESTIONS = {
    "course": "What are the 3 homework levels in the AIE2026 course?",
    "short": "What is LoRA in machine learning? Answer in two sentences.",
    "long": "Explain LoRA in machine learning in detail.",
}

# Seconds between calls to one model, to stay under the free-tier requests-per-minute limit.
# Course measurements: flash-lite 15 per minute (at least 4 s apart), 3.8-flash 5 per minute (12 s).
GAP_SECONDS = {"gemini-3.5-flash-lite": 5.0, "gemini-3.8-flash": 13.0}
DEFAULT_GAP = 13.0

BUSY_RETRIES = 2  # extra tries after a 503 "model is busy" error
BUSY_WAIT = 20.0  # seconds to wait before retrying a 503
RATE_LIMIT_WAIT = 60.0  # seconds to wait once after a 429 before giving up on that model

OUT_DIR = Path("lectures/01/results")


@dataclass
class Record:
    """One API call (one attempt). Failed attempts are recorded too."""

    timestamp: str
    model: str
    question_id: str
    run: int
    attempt: int
    status: str  # "ok", "error 503", "error 429", ...
    seconds: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    thinking_tokens: int | None = None
    total_tokens: int | None = None
    answer_chars: int | None = None
    model_version: str | None = None
    answer: str = ""


def call_once(client, model: str, question_id: str, question: str, run: int, attempt: int) -> Record:
    """Call the model once and measure the wall-clock time until the full answer arrives."""
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    start = time.perf_counter()
    try:
        response = client.models.generate_content(model=model, contents=question)
    except errors.APIError as e:
        return Record(stamp, model, question_id, run, attempt, f"error {e.code}", round(time.perf_counter() - start, 2))
    seconds = round(time.perf_counter() - start, 2)

    usage = response.usage_metadata
    text = response.text or ""
    return Record(
        timestamp=stamp,
        model=model,
        question_id=question_id,
        run=run,
        attempt=attempt,
        status="ok",
        seconds=seconds,
        input_tokens=getattr(usage, "prompt_token_count", None),
        output_tokens=getattr(usage, "candidates_token_count", None),
        thinking_tokens=getattr(usage, "thoughts_token_count", None),
        total_tokens=getattr(usage, "total_token_count", None),
        answer_chars=len(text),
        model_version=getattr(response, "model_version", None),
        answer=text,
    )


def run_experiment(client, models: list[str], questions: dict[str, str], runs: int, sleep=time.sleep) -> list[Record]:
    """Ask each question `runs` times per model, with pauses and retries. Returns every attempt."""
    records: list[Record] = []
    for model in models:
        gap = GAP_SECONDS.get(model, DEFAULT_GAP)
        rate_limited = False
        for run in range(1, runs + 1):
            for qid, question in questions.items():
                if rate_limited:
                    break
                attempt = 0
                while True:
                    attempt += 1
                    rec = call_once(client, model, qid, question, run, attempt)
                    records.append(rec)
                    print(f"{model:24} {qid:7} run {run} try {attempt}: {rec.status:9} {rec.seconds:6.2f} s  output tokens: {rec.output_tokens}")
                    sleep(gap)
                    if rec.status == "error 503" and attempt <= BUSY_RETRIES:
                        sleep(BUSY_WAIT)
                        continue
                    if rec.status == "error 429":
                        if attempt == 1:
                            sleep(RATE_LIMIT_WAIT)
                            continue
                        rate_limited = True
                        print(f"{model}: still rate-limited (429), skipping its remaining calls")
                    break
    return records


def _mean(values: list[float]) -> float | None:
    return round(statistics.mean(values), 2) if values else None


def summarize(records: list[Record]) -> list[dict]:
    """One summary row per (model, question): success rate, time and token averages."""
    keys = list(dict.fromkeys((r.model, r.question_id) for r in records))
    rows = []
    for model, qid in keys:
        group = [r for r in records if r.model == model and r.question_id == qid]
        ok = [r for r in group if r.status == "ok"]
        secs = [r.seconds for r in ok]
        out = [r.output_tokens or 0 for r in ok]
        think = [r.thinking_tokens or 0 for r in ok]
        speed = [((r.output_tokens or 0) + (r.thinking_tokens or 0)) / r.seconds for r in ok if r.seconds > 0]
        rows.append({
            "model": model,
            "question": qid,
            "ok / attempts": f"{len(ok)} / {len(group)}",
            "errors": ", ".join(sorted({r.status for r in group if r.status != "ok"})) or "-",
            "avg seconds": _mean(secs),
            "min-max seconds": f"{min(secs):.2f}-{max(secs):.2f}" if secs else "-",
            "avg input": _mean([r.input_tokens or 0 for r in ok]),
            "avg output": _mean(out),
            "avg thinking": _mean(think),
            "tokens per second": _mean(speed),
        })
    return rows


def to_markdown(rows: list[dict]) -> str:
    if not rows:
        return "(no results)\n"
    headers = list(rows[0])
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for row in rows:
        lines.append("| " + " | ".join("-" if row[h] is None else str(row[h]) for h in headers) + " |")
    return "\n".join(lines) + "\n"


def save(records: list[Record], rows: list[dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    columns = [f.name for f in fields(Record) if f.name != "answer"]
    with open(out_dir / "measurements.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(asdict(r) for r in records)
    with open(out_dir / "answers.md", "w", encoding="utf-8") as f:
        for r in records:
            if r.status == "ok":
                f.write(f"## {r.model} / {r.question_id} / run {r.run}\n\n{r.answer.strip()}\n\n")
    (out_dir / "summary.md").write_text(to_markdown(rows), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure response time and token counts")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--questions", nargs="+", choices=list(QUESTIONS), default=list(QUESTIONS))
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be at least 1")

    client = genai.Client(api_key=get_api_key())
    questions = {q: QUESTIONS[q] for q in args.questions}
    records = run_experiment(client, args.models, questions, args.runs)
    rows = summarize(records)
    save(records, rows, OUT_DIR)
    print("\n" + to_markdown(rows))
    print(f"Saved: {OUT_DIR}/measurements.csv, answers.md, summary.md")


if __name__ == "__main__":
    main()
