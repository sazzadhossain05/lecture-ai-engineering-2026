"""Basic homework: grade with the verdict requested BEFORE the reason (app/judge.py asks for the reason first).

Only the field order of the structured output changes (verdict, then reason), as suggested in problem.md.
app/judge.py stays unchanged; retries come from tools/judge_retry.py. Same options as app.judge.

Usage:
    uv run python tools/judge_order.py --wait 3 --out lectures/04/runs/basic_order.json
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pydantic import BaseModel, Field, create_model  # noqa: E402

from app import judge  # noqa: E402
from tools import judge_retry  # noqa: E402


class VerdictFirst(BaseModel):
    """Judgment for one criterion, with the verdict first (verdict → reason)."""

    verdict: judge.Verdict = Field(description="One of pass / fail / unsure")
    reason: str = Field(description="Reason for the judgment, in one or two English sentences")


def verdict_first_result():
    """Build a JudgeResult with the same criteria and descriptions, but VerdictFirst fields."""
    fields = {
        key: (VerdictFirst, Field(description=judge.JudgeResult.model_fields[key].description))
        for key, _ in judge.LLM_CRITERIA
    }
    return create_model("JudgeResult", **fields)


if __name__ == "__main__":
    judge.JudgeResult = verdict_first_result()
    print("[order] verdict before reason")
    judge_retry.main(sys.argv[1:])
