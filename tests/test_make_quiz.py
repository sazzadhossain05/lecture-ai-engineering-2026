"""Tests for the make_quiz tool added in the Lecture 03 exercise (no LLM or API key used)."""

import json

from app import tools


def test_make_quiz_returns_question_and_answer_from_the_requested_lecture():
    quiz = json.loads(tools.make_quiz(2))
    assert quiz["lecture"] == 2
    assert quiz["question"].startswith("What does ")
    lecture2_definitions = {t["definition"] for t in tools.load_glossary() if t["lecture"] == 2}
    assert quiz["answer"] in lecture2_definitions


def test_make_quiz_reports_a_lecture_without_terms():
    assert "No glossary terms for Lecture 00" in tools.make_quiz(0)
