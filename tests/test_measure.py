"""Tests for app/measure.py. They use a fake client, so no API key or network is needed."""

from types import SimpleNamespace

from google.genai import errors

from app.measure import run_experiment, summarize, to_markdown


class FakeModels:
    """Returns the scripted results in order.

    A number is the output token count of a successful answer.
    A string like "503" means "raise that HTTP error".
    """

    def __init__(self, script):
        self.script = list(script)

    def generate_content(self, model, contents):
        item = self.script.pop(0)
        if isinstance(item, str):
            code = int(item)
            raise errors.APIError(code, {"error": {"code": code, "message": "fake", "status": "FAKE"}})
        usage = SimpleNamespace(prompt_token_count=10, candidates_token_count=item,
                                thoughts_token_count=5, total_token_count=15 + item)
        return SimpleNamespace(usage_metadata=usage, text="x" * item, model_version=model)


def fake_client(script):
    return SimpleNamespace(models=FakeModels(script))


def test_records_tokens_and_summarizes():
    client = fake_client([20, 40])
    records = run_experiment(client, ["m"], {"q": "question"}, runs=2, sleep=lambda s: None)
    assert [r.status for r in records] == ["ok", "ok"]
    assert records[0].input_tokens == 10 and records[0].thinking_tokens == 5
    row = summarize(records)[0]
    assert row["ok / attempts"] == "2 / 2"
    assert row["avg output"] == 30
    assert "| m | q |" in to_markdown([row])


def test_retries_busy_model_and_counts_failed_attempts():
    client = fake_client(["503", 25])
    records = run_experiment(client, ["m"], {"q": "question"}, runs=1, sleep=lambda s: None)
    assert [r.status for r in records] == ["error 503", "ok"]
    assert summarize(records)[0]["ok / attempts"] == "1 / 2"


def test_stops_calling_a_model_that_stays_rate_limited():
    client = fake_client(["429", "429"])
    records = run_experiment(client, ["m"], {"a": "q1", "b": "q2"}, runs=2, sleep=lambda s: None)
    assert [r.status for r in records] == ["error 429", "error 429"]
    assert summarize(records)[0]["ok / attempts"] == "0 / 2"
