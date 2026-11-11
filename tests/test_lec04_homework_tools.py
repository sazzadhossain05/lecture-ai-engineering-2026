"""Tests for the Lecture 04 homework tools (no API key or network needed: fake models only)."""

import json
import sys
from pathlib import Path

import pytest
from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError
from pydantic_ai.models.test import TestModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import judge  # noqa: E402
from tools import baseline, eval_stats  # noqa: E402
from tools.judge_retry import RetryingAgent  # noqa: E402


# ---------------------------------------------------------------- eval_stats
def test_cohen_kappa_known_value():
    # observed 3/4; chance = 0.5*0.25 + 0.5*0.75 = 0.5; kappa = (0.75 - 0.5) / 0.5 = 0.5
    pairs = [("pass", "pass"), ("pass", "fail"), ("fail", "fail"), ("fail", "fail")]
    assert eval_stats.cohen_kappa(pairs) == pytest.approx(0.5)
    assert eval_stats.cohen_kappa([("pass", "pass"), ("fail", "fail")]) == pytest.approx(1.0)


def test_cohen_kappa_undefined_when_both_use_one_class():
    assert eval_stats.cohen_kappa([("pass", "pass")] * 5) is None
    assert eval_stats.cohen_kappa([]) is None


def test_compare_counts_missed_false_alarms_and_excludes_unsure():
    human = {"1": {"hint": "fail"}, "2": {"hint": "pass"}, "3": {"hint": "fail"}, "4": {"hint": "pass"}}
    grader = {"1": {"hint": "pass"}, "2": {"hint": "fail"}, "3": {"hint": "unsure"}, "4": {"hint": "pass"}}
    s = eval_stats.compare(human, grader, ["1", "2", "3", "4"], ["hint"])["hint"]
    assert (s["n"], s["agree"], s["missed"], s["false_alarm"], s["excluded"]) == (3, 1, 1, 1, 1)
    assert s["miss_rate"] == pytest.approx(1.0)  # the only compared human failure was passed by the grader


# ---------------------------------------------------------------- judge_retry
class Flaky:
    def __init__(self, errors):
        self.errors, self.calls = list(errors), 0

    def run_sync(self, prompt, **kwargs):
        self.calls += 1
        if self.errors:
            raise self.errors.pop(0)
        return f"ok:{prompt}"


def test_retrying_agent_retries_busy_and_timeout_errors():
    waits = []
    flaky = Flaky([ModelHTTPError(503, "m", "busy"), ModelAPIError("m", "ReadTimeout")])
    assert RetryingAgent(flaky, sleep=waits.append).run_sync("q") == "ok:q"
    assert waits == [10, 20] and flaky.calls == 3


def test_retrying_agent_raises_other_errors_at_once():
    with pytest.raises(ModelHTTPError):
        RetryingAgent(Flaky([ModelHTTPError(400, "m", "bad request")]), sleep=lambda s: None).run_sync("q")


# ---------------------------------------------------------------- baseline
def test_baseline_records_resume_and_summary(tmp_path, monkeypatch):
    import app.agent as agent_module

    cases = [
        {"id": "01", "category": "Normal case", "split": "tuning", "question": "What is LoRA?", "answer": "",
         "reference": {"glossary": ["lora"], "expected": "Explain LoRA"}},
        {"id": "02", "category": "Outside the course", "split": "report", "question": "Weather?", "answer": "",
         "reference": {"glossary": [], "expected": "Refuse"}},
    ]
    cases_path = tmp_path / "cases.jsonl"
    judge.write_jsonl(cases_path, cases)
    monkeypatch.setattr(agent_module, "build_model", lambda: TestModel(custom_output_text="An answer.\n\nLecture 02"))
    monkeypatch.setattr(judge, "build_llm_model", lambda name: judge.build_test_model())
    args = ["--cases", str(cases_path), "--out-dir", str(tmp_path / "out"), "--wait", "0"]

    baseline.main(args + ["--runs", "1", "--write-answers"])
    assert [c["answer"] for c in judge.read_jsonl(cases_path)] == ["An answer.\n\nLecture 02"] * 2

    baseline.main(args + ["--runs", "2"])  # run 1 is already recorded, so only run 2 is added
    records = judge.read_jsonl(tmp_path / "out" / "records.jsonl")
    assert sorted((r["run"], r["id"]) for r in records) == [(1, "01"), (1, "02"), (2, "01"), (2, "02")]
    assert all(r["verdicts"]["lecture_mark"]["verdict"] == "pass" and r["requests"] >= 1 for r in records)

    summary = (tmp_path / "out" / "summary.md").read_text(encoding="utf-8")
    assert "Passed in every run (pass^2)" in summary and "Quality by run (report)" in summary
    assert json.loads(json.dumps(records))  # records stay plain JSON
