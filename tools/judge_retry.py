"""Run app.judge with automatic retries when Gemini is busy (503), rate-limited (429) or times out.

app.judge stops at the first server error and loses the cases already graded.
This wrapper keeps app/judge.py unchanged: it wraps the grading agent and the answer agent
so that each call is retried after a pause. It accepts the same options as app.judge, plus
--timeout (seconds per model request) for slow models.

Usage (from the repository root):
    uv run python tools/judge_retry.py --wait 3
    uv run python tools/judge_retry.py --wait 13 --model gemini-3.5-flash --timeout 300
"""

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError  # noqa: E402

RETRY_STATUS = {429, 500, 502, 503, 504}  # Temporary errors: busy server or rate limit
MAX_TRIES = 6


def is_temporary(error: ModelAPIError) -> bool:
    """Busy server, rate limit, or a connection problem such as a timeout (no status code)."""
    if isinstance(error, ModelHTTPError):
        return error.status_code in RETRY_STATUS
    return True


def retry_delay(error: ModelAPIError, attempt: int) -> int:
    """Seconds to wait before the next try: one minute after a rate limit, otherwise 10, 20, 30, 40 seconds."""
    if isinstance(error, ModelHTTPError) and error.status_code == 429:
        return 60
    return min(10 * attempt, 40)


def describe(error: ModelAPIError) -> str:
    return f"error {error.status_code}" if isinstance(error, ModelHTTPError) else f"{type(error).__name__} ({str(error)[:40]})"


def run_with_retry(agent, *args, max_tries: int = MAX_TRIES, sleep=time.sleep, **kwargs):
    """Call agent.run_sync and retry temporary errors. Other errors are raised at once."""
    for attempt in range(1, max_tries + 1):
        try:
            return agent.run_sync(*args, **kwargs)
        except ModelAPIError as e:
            if not is_temporary(e) or attempt == max_tries:
                raise
            delay = retry_delay(e, attempt)
            print(f"\n  [retry] {describe(e)}; waiting {delay} seconds (attempt {attempt} of {max_tries})", flush=True)
            sleep(delay)


class RetryingAgent:
    """Wraps a Pydantic AI agent so that run_sync retries temporary errors. Other attributes pass through."""

    def __init__(self, agent, sleep=time.sleep, timeout: float | None = None):
        self._agent = agent
        self._sleep = sleep
        self._timeout = timeout

    def run_sync(self, *args, **kwargs):
        if self._timeout:
            kwargs["model_settings"] = {**(kwargs.get("model_settings") or {}), "timeout": self._timeout}
        return run_with_retry(self._agent, *args, sleep=self._sleep, **kwargs)

    def __getattr__(self, name):
        return getattr(self._agent, name)


def main(argv: list[str] | None = None) -> None:
    from app import agent as agent_module
    from app import judge

    extra = argparse.ArgumentParser(add_help=False)
    extra.add_argument("--timeout", type=float, default=None, help="Seconds allowed per model request")
    ours, rest = extra.parse_known_args(argv)

    original_build_judge = judge.build_judge
    judge.build_judge = lambda model, rubric: RetryingAgent(original_build_judge(model, rubric), timeout=ours.timeout)
    agent_module.agent = RetryingAgent(agent_module.agent, timeout=ours.timeout)  # Used by --generate
    judge.main(rest)


if __name__ == "__main__":
    main(sys.argv[1:])
