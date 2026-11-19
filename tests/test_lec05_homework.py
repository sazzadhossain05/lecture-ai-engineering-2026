"""Lecture 05 homework tests: result count setting, adjacent pages, hybrid retrieval (no API key needed).

Instead of calling the embedding API, the query vector is replaced with the stored vector of one page,
so that page should come back first. This checks the retrieval logic, not answer quality.
"""

import json
import os
import sqlite3
import struct
import subprocess
import sys

import pytest

from app import retrieval, tools
from app.agent import returned_pages
from app.config import HYBRID_MAX_PAGES, HYBRID_MAX_PER_SECTION, HYBRID_MIN_CHARS, RAG_DB


def stored_vector(page_id: str) -> list[float]:
    with sqlite3.connect(RAG_DB) as db:
        (blob,) = db.execute("SELECT embedding FROM chunks WHERE page_id = ?", (page_id,)).fetchone()
    return list(struct.unpack(f"{len(blob) // 4}f", blob))


@pytest.fixture
def query_like(monkeypatch):
    """Make every query embed to the stored vector of the given page."""
    def use(page_id: str) -> None:
        vector = stored_vector(page_id)
        monkeypatch.setattr(retrieval, "embed_text", lambda text, task_type: vector)
    return use


def test_top_k_can_be_set_with_an_environment_variable():
    code = "from app.config import RAG_TOP_K; print(RAG_TOP_K)"
    default = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                             env={k: v for k, v in os.environ.items() if k != "AIE_RAG_TOP_K"}, check=True)
    changed = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                             env={**os.environ, "AIE_RAG_TOP_K": "10"}, check=True)
    assert default.stdout.strip() == "5"
    assert changed.stdout.strip() == "10"


def test_search_returns_the_requested_number_of_pages(query_like):
    query_like("lec02-main-p052")
    hits = retrieval.search("LoRA", top_k=3)
    assert len(hits) == 3
    assert hits[0]["page_id"] == "lec02-main-p052"
    with pytest.raises(ValueError):
        retrieval.search("LoRA", top_k=0)


def test_neighbors_add_the_pages_before_and_after_without_duplicates(query_like):
    query_like("lec03-main-p039")
    results = retrieval.search_with_neighbors("memory")
    ids = [r["page_id"] for r in results]
    assert len(ids) == len(set(ids))
    hits = [r for r in results if r["role"] == "hit"]
    assert [r["rank"] for r in hits] == list(range(1, len(hits) + 1))
    assert hits[0]["page_id"] == "lec03-main-p039"
    for page in results:
        if page["role"] == "neighbor":
            hit = next(r for r in hits if r["page_id"] == page["neighbor_of"])
            assert page["document_id"] == hit["document_id"]
            assert page["offset"] in (-1, 1)
            assert page["content"] and page["citation"]


def test_neighbors_stay_inside_the_document():
    first = retrieval.read_page("lec02-main-p001")
    results = retrieval.add_neighbor_pages([{**first, "distance": 0.1}])
    assert [r["page_id"] for r in results] == ["lec02-main-p001", "lec02-main-p002"]
    last = retrieval.read_page("lec01-main-p073")
    results = retrieval.add_neighbor_pages([{**last, "distance": 0.1}])
    assert [r["page_id"] for r in results] == ["lec01-main-p072", "lec01-main-p073"]


def test_a_page_that_is_a_hit_is_not_repeated_as_a_neighbor():
    hits = [{**retrieval.read_page(pid), "distance": d} for pid, d in (("lec03-main-p039", 0.1), ("lec03-main-p040", 0.2))]
    results = retrieval.add_neighbor_pages(hits)
    roles = {r["page_id"]: r["role"] for r in results}
    assert list(roles) == ["lec03-main-p038", "lec03-main-p039", "lec03-main-p040", "lec03-main-p041"]
    assert roles["lec03-main-p040"] == "hit"


def test_hybrid_returns_unique_content_pages_across_sections(query_like):
    query_like("lec03-main-p039")
    found = retrieval.search_hybrid("compaction and memory")
    results = found["results"]
    ids = [r["page_id"] for r in results]
    assert ids[0] == "lec03-main-p039"
    assert 1 <= len(ids) <= HYBRID_MAX_PAGES and len(ids) == len(set(ids))
    assert all(len(r["content"].strip()) >= HYBRID_MIN_CHARS for r in results)
    sections = [(r["document_id"], r["section"]) for r in results]
    assert max(sections.count(s) for s in sections) <= HYBRID_MAX_PER_SECTION
    assert all(r["why"] and r["citation"] for r in results)
    assert found["skipped_divider_pages"] == [] or all(len(retrieval.read_page(p)["content"].strip()) < HYBRID_MIN_CHARS for p in found["skipped_divider_pages"])
    assert [r["score"] for r in results] == sorted((r["score"] for r in results), reverse=True)


def test_hybrid_skips_section_divider_pages(query_like):
    query_like("lec03-main-p037")  # "Part 6 Memory": a divider page with only a title
    found = retrieval.search_hybrid("memory")
    assert "lec03-main-p037" not in [r["page_id"] for r in found["results"]]
    assert "lec03-main-p037" in found["skipped_divider_pages"]


def test_lecture_names_and_course_terms_are_read_from_the_question():
    assert retrieval.named_lectures("In Lecture 02, what does LoRA freeze?") == {2}
    assert retrieval.named_lectures("from Lecture 02 ... in Lecture 03") == {2, 3}
    assert retrieval.named_lectures("Lectures 1 and 3") == {1, 3}
    assert retrieval.named_lectures("What is RAG?") == set()
    terms, _ = retrieval.load_terms({p["page_id"] for p in retrieval.load_pages()})
    assert {"term:lora", "term:qlora"} <= retrieval.question_terms("What does QLoRA add to LoRA?", terms)
    assert "term:fine-tuning" in retrieval.question_terms("Why RAG before FT?", terms)
    assert "term:fine-tuning" not in retrieval.question_terms("a soft decision", terms)  # "ft" inside a word


def test_hybrid_keeps_a_page_from_each_named_lecture(query_like):
    query_like("lec03-main-p003")  # a Lecture 03 page: without help, Lecture 01 pages rank low
    question = "How do Lecture 01 and Lecture 03 describe agents?"
    found = retrieval.search_hybrid(question)
    lectures = [r["lecture"] for r in found["results"]]
    assert found["named_lectures"] == [1, 3] and 1 in lectures and 3 in lectures
    reserved = [r for r in found["results"] if any("which the question names" in w for w in r["why"])]
    assert {r["lecture"] for r in reserved} == {1, 3}
    plain = retrieval.search_hybrid(question, reserve_lectures=False)
    assert len(plain["results"]) == len(found["results"])


def test_hybrid_term_bonus_marks_pages_that_mention_question_terms(query_like):
    query_like("lec02-main-p052")
    found = retrieval.search_hybrid("What does QLoRA add to LoRA?")
    assert set(found["question_terms"]) == {"LoRA", "QLoRA"}
    top = found["results"][0]
    assert top["page_id"] == "lec02-main-p052"
    assert any("mentions the question's terms" in w for w in top["why"])


def test_tool_wrappers_return_json(query_like):
    query_like("lec02-main-p052")
    with_neighbors = json.loads(tools.search_materials_with_neighbors("LoRA"))
    hybrid = json.loads(tools.search_hybrid("LoRA"))
    assert with_neighbors["results"][0]["page_id"] == "lec02-main-p052"
    assert hybrid["results"][0]["page_id"] == "lec02-main-p052"
    assert json.loads(tools.search_hybrid("  "))["error"]


def test_trace_lists_returned_pages():
    content = json.dumps({"results": [{"page_id": "a"}, {"page_id": "b", "role": "neighbor", "neighbor_of": "a"}]})
    assert returned_pages(content) == "results: a, b (neighbor of a)"
    graph = json.dumps({"seeds": [{"page_id": "s"}], "expanded": [{"page_id": "e"}]})
    assert returned_pages(graph) == "seeds: s | expanded: e"
    assert returned_pages("not json") is None
