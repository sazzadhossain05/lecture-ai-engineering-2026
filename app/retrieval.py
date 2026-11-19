"""Lecture 05: page-level vector search."""

import argparse
import json
import math
import re
import sqlite3
from contextlib import contextmanager
from collections import defaultdict, deque
from pathlib import Path

from google import genai
from google.genai import types
from pydantic_ai.exceptions import ModelHTTPError
import sqlite_vec

from app.config import (
    EMBEDDING_DIMENSIONS, EMBEDDING_MAX_TOKENS, EMBEDDING_MODEL,
    RAG_DB, RAG_DOCUMENT_IDS, RAG_SOURCE, RAG_TOP_K, RAG_TREE, get_api_key,
    RAG_GRAPH, GRAPH_START_K, GRAPH_HOPS, GRAPH_MAX_RESULTS, RAG_NEIGHBOR_WINDOW,
    HYBRID_MAX_PAGES, HYBRID_MAX_PER_SECTION, HYBRID_MIN_CHARS, HYBRID_MAX_TERM_PAGES, HYBRID_TERM_BONUS,
)


def get_all_materials() -> str:
    """Combine all materials into one string with lecture, section, and page metadata."""
    documents = json.loads(RAG_SOURCE.read_text(encoding="utf-8"))
    return "\n\n".join(
        f"Document: {document['id']} / {document['title']}\n"
        f"Section: {section['section']}\n"
        f"Page: {page.get('citation') or ('PDF p.' + str(page['page']))} / {page['title']}\n{page['content']}"
        for document in documents
        for section in document["content"]
        for page in section["content"]
    )

def load_pages(source: Path = RAG_SOURCE) -> list[dict]:
    """Convert document → section → page JSON into a page list for the selected materials."""
    documents = json.loads(source.read_text(encoding="utf-8"))
    pages = []
    for document in documents:
        if document["id"] not in RAG_DOCUMENT_IDS:
            continue
        for section in document["content"]:
            for page in section["content"]:
                pages.append({"page_id": page["id"], "document_id": document["id"],
                              "lecture": int(document["id"][3:5]), "document_title": document["title"],
                              "section": section["section"], "title": page["title"],
                              "page": page["page"], "content": page["content"]})
                if page.get("citation"):
                    pages[-1]["citation"] = page["citation"]
    return pages


def browse_tree(node_id: str | None = None) -> dict:
    """Return the first sentence for child pages and the full text for the selected page itself."""
    tree = json.loads(RAG_TREE.read_text(encoding="utf-8"))
    tree["children"] = [node for node in tree["children"] if node["id"] in RAG_DOCUMENT_IDS]
    node_id = node_id or tree["id"]
    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}

    def describe(node, full=False):
        info = {key: node[key] for key in ("id", "kind", "title")}
        if node["kind"] == "page":
            info.update({key: value for key, value in pages[node["id"]].items() if key != "page_id"})
            if not full:
                info["content"] = re.split(r"(?<=[。！？।॥])|(?<=[.!?؟])\s+|\n", info["content"].strip(), maxsplit=1)[0]
        return info

    remaining = [tree]
    while remaining:
        node = remaining.pop()
        if node["id"] == node_id:
            return {
                "node": describe(node, full=True),
                "children": [describe(child) for child in node.get("children", [])],
            }
        remaining.extend(node.get("children", []))
    raise ValueError("The requested table-of-contents node was not found.")


def read_page(page_id: str) -> dict:
    """Return text and citation metadata for one specified page from the main materials for Lectures 01–03."""
    for page in load_pages(RAG_SOURCE):
        if page["page_id"] == page_id:
            return page
    raise ValueError("The requested page was not found.")


def normalized_vector(values: list[float]) -> list[float]:
    """Normalize the vector to unit length."""
    norm = math.hypot(*values)
    if norm == 0:
        raise ValueError("The embedding is a zero vector.")
    return [value / norm for value in values]


def embed_text(text: str, task_type: str) -> list[float]:
    """Embed text with Gemini. Stop instead of truncating if the input limit is exceeded."""
    with genai.Client(api_key=get_api_key()) as client:
        count = client.models.count_tokens(model=EMBEDDING_MODEL, contents=text).total_tokens
        if count is None or count > EMBEDDING_MAX_TOKENS:
            raise ValueError(f"Embedding input exceeds the limit or could not be measured: {count} tokens.")
        response = client.models.embed_content(
            model=EMBEDDING_MODEL, contents=text,
            config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=EMBEDDING_DIMENSIONS),
        )
    embedding = response.embeddings[0]
    if embedding.statistics and embedding.statistics.truncated:
        raise ValueError("The embedding API truncated the text.")
    return normalized_vector(embedding.values)


@contextmanager
def open_index(path: Path):
    """Open an existing search database read-only and close it on exit."""
    if not path.is_file():
        raise FileNotFoundError("Search database not found.")
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        db.row_factory = sqlite3.Row
        db.enable_load_extension(True)
        sqlite_vec.load(db)
        db.enable_load_extension(False)
        yield db
    finally:
        db.close()


def search(query: str, top_k: int | None = None) -> list[dict]:
    """Embed the query and return up to top_k (default RAG_TOP_K) similar pages."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("The search query is empty.")
    top_k = RAG_TOP_K if top_k is None else top_k
    if top_k < 1:
        raise ValueError("The number of search results must be at least 1.")
    with open_index(RAG_DB) as db:
        vector = embed_text(query.strip(), "RETRIEVAL_QUERY")
        columns = {column["name"] for column in db.execute("PRAGMA table_info(chunks)")}
        citation = "citation," if "citation" in columns else ""
        rows = db.execute(f"""
            SELECT page_id, document_id, lecture, document_title, section, title, page, content,
                   {citation}
                   vec_distance_cosine(embedding, ?) AS distance
            FROM chunks ORDER BY distance, page_id LIMIT ?
        """, (sqlite_vec.serialize_float32(vector), top_k))
        return [dict(row) for row in rows]


# --- Homework (Implementation): add the pages just before and after each search hit ---------------

def add_neighbor_pages(hits: list[dict], window: int = RAG_NEIGHBOR_WINDOW) -> list[dict]:
    """Return the hits plus up to `window` pages before and after each one, in reading order.

    Neighbors never cross into another document, and each page appears only once. A page that is a hit
    itself keeps role "hit" even if it is also next to another hit. Neighbors carry the same citation
    metadata as hits, plus `neighbor_of` (the hit's page ID) and `offset` (-1 = page before, +1 = page after).
    """
    pages = load_pages(RAG_SOURCE)
    position = {page["page_id"]: i for i, page in enumerate(pages)}
    hit_ids = {hit["page_id"] for hit in hits}
    results, seen = [], set()
    for rank, hit in enumerate(hits, 1):
        i = position.get(hit["page_id"])
        if i is None:  # not in the selected materials: keep the hit as it is
            if hit["page_id"] not in seen:
                seen.add(hit["page_id"])
                results.append({**hit, "role": "hit", "rank": rank})
            continue
        for j in range(i - window, i + window + 1):
            if not 0 <= j < len(pages) or pages[j]["document_id"] != hit["document_id"]:
                continue
            page_id = pages[j]["page_id"]
            if page_id in seen:
                continue
            if j == i:
                seen.add(page_id)
                results.append({**hit, "role": "hit", "rank": rank})
            elif page_id not in hit_ids:  # a hit is added later with its own rank and distance
                seen.add(page_id)
                results.append({**pages[j], "role": "neighbor", "neighbor_of": hit["page_id"], "offset": j - i})
    return results


def search_with_neighbors(query: str) -> list[dict]:
    """Vector search (RAG_TOP_K hits), then add the pages before and after each hit."""
    return add_neighbor_pages(search(query))


# --- Homework (Advanced): hybrid retrieval ---------------------------------------------------------

def page_distances(query: str) -> dict[str, float]:
    """Cosine distance between the query and every page in the search database (one embedding call)."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("The search query is empty.")
    with open_index(RAG_DB) as db:
        vector = embed_text(query.strip(), "RETRIEVAL_QUERY")
        rows = db.execute("SELECT page_id, vec_distance_cosine(embedding, ?) AS distance FROM chunks",
                          (sqlite_vec.serialize_float32(vector),))
        return {row["page_id"]: row["distance"] for row in rows}


def load_terms(page_ids: set[str]) -> tuple[dict[str, dict], dict[str, set[str]]]:
    """From graph.json: term nodes (id → node) and term → the selected pages that mention it."""
    graph = json.loads(RAG_GRAPH.read_text(encoding="utf-8"))
    terms = {node["id"]: node for node in graph["nodes"] if node["kind"] == "term"}
    term_pages = defaultdict(set)
    for edge in graph["edges"]:
        if edge["relation"] != "mentions":
            continue
        a, b = edge["source"], edge["target"]
        page, term = (a, b) if b in terms else (b, a)
        if page in page_ids and term in terms:
            term_pages[term].add(page)
    return terms, term_pages


def named_lectures(question: str) -> set[int]:
    """Lecture numbers written in the question, for example "Lecture 02" or "Lectures 1 and 3" → {2} or {1, 3}."""
    numbers = set()
    for match in re.finditer(r"\bLectures?\s+(\d{1,2}(?:\s*(?:,|and|&|to|–|-)\s*\d{1,2})*)", question, re.IGNORECASE):
        values = [int(n) for n in re.findall(r"\d{1,2}", match.group(1))]
        if re.search(r"to|–|-", match.group(1)) and len(values) == 2:
            values = list(range(values[0], values[1] + 1))
        numbers.update(values)
    return numbers


def question_terms(question: str, terms: dict[str, dict]) -> set[str]:
    """Course terms whose name or alias appears in the question (short aliases such as "FT" must match case)."""
    found = set()
    for term_id, node in terms.items():
        for alias in {node["title"], *node.get("aliases", [])}:
            flags = 0 if len(alias) <= 3 else re.IGNORECASE
            if re.search(r"(?<![\w-])" + re.escape(alias) + r"(?![\w-])", question, flags):
                found.add(term_id)
                break
    return found


def search_hybrid(query: str, *, max_pages: int = HYBRID_MAX_PAGES, max_per_section: int = HYBRID_MAX_PER_SECTION,
                  min_chars: int = HYBRID_MIN_CHARS, max_term_pages: int = HYBRID_MAX_TERM_PAGES,
                  term_bonus: float = HYBRID_TERM_BONUS, reserve_lectures: bool = True) -> dict:
    """Question-aware hybrid retrieval: vector search + lecture/section structure + the course-term graph.

    1. One query embedding gives the distance to every page (page vectors are already in the database).
    2. Section-divider pages (shorter than min_chars) are skipped: they hold only a title.
    3. Course terms in the question are found in the term graph (aliases from graph.json). A page that
       mentions one gets a small bonus (term_bonus each, at most 2). Very common terms are ignored.
    4. For each lecture the question names, its best page is kept, so a question that spans
       lectures gets evidence from each of them (Tree-like use of the lecture structure).
    5. The remaining places go to the highest scores (similarity + term bonus), at most
       max_per_section pages per section, up to max_pages pages. `why` explains each choice.
    The keyword arguments let tools/rag_eval.py switch single steps off for comparison.
    """
    pages = load_pages(RAG_SOURCE)
    by_id = {page["page_id"]: page for page in pages}
    distance = {pid: d for pid, d in page_distances(query).items() if pid in by_id}
    ranked = sorted(distance, key=lambda pid: (distance[pid], pid))
    vector_rank = {pid: rank for rank, pid in enumerate(ranked, 1)}
    content = [pid for pid in ranked if len(by_id[pid]["content"].strip()) >= min_chars]
    skipped = [pid for pid in ranked[:10] if pid not in content]

    terms, term_pages = load_terms(set(by_id))
    asked_terms = {t for t in question_terms(query, terms) if 0 < len(term_pages[t]) <= max_term_pages}
    matched = {pid: sorted(terms[t]["title"] for t in asked_terms if pid in term_pages[t]) for pid in content}
    score = {pid: 1 - distance[pid] + term_bonus * min(len(matched[pid]), 2) for pid in content}
    order = sorted(content, key=lambda pid: (-score[pid], pid))

    def why(pid: str) -> list[str]:
        reasons = [f"similarity rank {vector_rank[pid]} of {len(ranked)}"]
        if matched[pid]:
            reasons.append("mentions the question's terms: " + ", ".join(matched[pid]))
        return reasons

    chosen, per_section = {}, defaultdict(int)

    def take(pid: str, extra: str | None = None) -> None:
        section = (by_id[pid]["document_id"], by_id[pid]["section"])
        per_section[section] += 1
        chosen[pid] = why(pid) + ([extra] if extra else [])

    lectures = sorted(named_lectures(query) & {page["lecture"] for page in pages}) if reserve_lectures else []
    for lecture in lectures:
        best = next((pid for pid in order if by_id[pid]["lecture"] == lecture), None)
        if best and best not in chosen and len(chosen) < max_pages:
            take(best, f"best page of Lecture {lecture:02d}, which the question names")
    for pid in order:
        if len(chosen) >= max_pages:
            break
        section = (by_id[pid]["document_id"], by_id[pid]["section"])
        if pid not in chosen and per_section[section] < max_per_section:
            take(pid)

    results = [{**by_id[pid], "distance": round(distance[pid], 4), "score": round(score[pid], 4),
                "vector_rank": vector_rank[pid], "why": chosen[pid]}
               for pid in sorted(chosen, key=lambda p: (-score[p], p))]
    return {"results": results, "named_lectures": lectures,
            "question_terms": sorted(terms[t]["title"] for t in asked_terms),
            "skipped_divider_pages": skipped}


def search_graph(query: str) -> dict:
    """Start with vector search, then expand candidates through adjacent pages and shared terms."""
    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}
    graph = json.loads(RAG_GRAPH.read_text(encoding="utf-8"))
    nodes = {node["id"]: node for node in graph["nodes"]
             if node["kind"] == "term" or node["id"] in pages}
    adjacent = defaultdict(set)
    for edge in graph["edges"]:
        a, b = edge["source"], edge["target"]
        if edge["relation"] in ("next_page", "mentions") and a in nodes and b in nodes:
            adjacent[a].add(b)
            adjacent[b].add(a)

    seeds = [hit for hit in search(query) if hit["page_id"] in pages][:min(GRAPH_START_K, GRAPH_MAX_RESULTS)]
    seed_ids = {seed["page_id"] for seed in seeds}
    results, candidates = [], {}
    for rank, seed in enumerate(seeds):
        root = seed["page_id"]
        results.append({**pages[root], "distance": seed["distance"], "hops": 0,
                        "path": [{"id": root, "title": pages[root]["title"]}]})
        queue = deque([(root, [root])])
        visited = {root}
        while queue:
            current, path = queue.popleft()
            if len(path) - 1 >= GRAPH_HOPS:
                continue
            # At the same depth, follow terms with fewer connections first.
            neighbors = sorted(adjacent[current], key=lambda n: (len(adjacent[n]), n))
            for neighbor in neighbors:
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                route = path + [neighbor]
                queue.append((neighbor, route))
                if neighbor not in pages or neighbor in seed_ids:
                    continue
                frequency = max((len(adjacent[n]) for n in route if nodes[n]["kind"] == "term"), default=0)
                priority = (len(route) - 1, frequency, rank, neighbor)
                candidate = {**pages[neighbor], "hops": len(route) - 1,
                             "path": [{"id": n, "title": nodes[n]["title"]} for n in route]}
                if neighbor not in candidates or priority < candidates[neighbor][0]:
                    candidates[neighbor] = (priority, candidate)
    expanded = [candidate for _, candidate in sorted(candidates.values())]
    return {"seeds": results, "expanded": expanded[:max(0, GRAPH_MAX_RESULTS - len(results))],
            "max_hops": GRAPH_HOPS}



def run_full_context(agent, question: str, model, instructions: str, prompt_template: str):
    """Pass all materials at once and answer without retrieval tools."""
    prompt = prompt_template.format(materials=get_all_materials(), question=question)
    print(f"[full-context] Input: {len(prompt):,} characters")
    try:
        with agent.override(tools=[], instructions=instructions):
            return agent.run_sync(prompt, model=model)
    except ModelHTTPError as e:
        print(f"[full-context] API error HTTP {e.status_code}: {e.body}")
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search the lecture materials without using an agent")
    parser.add_argument("query", help="What to look up")
    method = parser.add_mutually_exclusive_group()
    method.add_argument("--neighbors", action="store_true", help="Homework: also return the pages before and after each hit")
    method.add_argument("--hybrid", action="store_true", help="Homework: vector search + graph links, re-ranked")
    parser.add_argument("--top-k", type=int, default=None, help="Number of vector search results (default: RAG_TOP_K)")
    args = parser.parse_args()
    if args.hybrid:
        found = search_hybrid(args.query)
        results = found["results"]
    elif args.neighbors:
        results = add_neighbor_pages(search(args.query, args.top_k))
    else:
        results = search(args.query, args.top_k)
    for i, result in enumerate(results, 1):
        print(f"\n{'=' * 60}\nSearch result {i} · {result['page_id']}\n{'=' * 60}")
        print(f"Lecture: {result['document_title']}")
        print(f"Section: {result['section']}")
        print(f"Title: {result['title']}")
        print(f"Page: {result.get('citation') or result['page']}")
        if result.get("role") == "neighbor":
            print(f"Added as the page {'before' if result['offset'] < 0 else 'after'} {result['neighbor_of']}")
        if result.get("why"):
            print(f"Why: {'; '.join(result['why'])}")
        print(f"\n{result['content']}")
