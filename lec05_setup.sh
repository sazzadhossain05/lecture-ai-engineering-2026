#!/usr/bin/env bash
# Lecture 05 setup: create the lec05 branch with the Lecture 05 materials and the homework code.
# Run from the repository root in Codespaces:  bash lec05_setup.sh
# Safe to run again: steps that are already done are skipped.
set -e
cd "$(git rev-parse --show-toplevel)"
COURSE_COMMIT=2e201d17a794d801d2d692e4b8a3670589f31cda   # Lecture 05 version of the English course repository

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "You have uncommitted changes on branch $(git branch --show-current). Commit them first, then run this again."
  exit 1
fi

echo "== 1. Get the Lecture 05 course materials"
git remote get-url en >/dev/null 2>&1 || git remote add en https://github.com/matsuolab/lecture-ai-engineering-2026-en.git
git fetch -q en main
git cat-file -e "$COURSE_COMMIT^{commit}" || { echo "Could not download the course materials. Check the internet connection and try again."; exit 1; }

echo "== 2. Create the lec05 branch from main"
if git show-ref --verify --quiet refs/heads/lec05; then
  git switch -q lec05
else
  git switch -q main
  git switch -q -c lec05
fi

if [ ! -f data/rag_data/index.sqlite3 ]; then
  git checkout "$COURSE_COMMIT" -- .
  git add -A
  git commit -q -m "Update course materials for Lecture 05 from the English course repository"
  echo "   Course materials updated."
else
  echo "   Course materials already present."
fi

echo "== 3. Add the homework code"
if [ ! -f tools/rag_eval.py ]; then
  git apply --whitespace=nowarn <<'LEC05_PATCH_END'
diff --git a/app/agent.py b/app/agent.py
index d292cb4..802e20e 100644
--- a/app/agent.py
+++ b/app/agent.py
@@ -6,6 +6,9 @@ Usage:
     uv run python -m app.agent --graph --trace "What is the difference between LoRA and QLoRA?"  # Follow the graph from search results to answer
     uv run python -m app.agent --tree --trace "What is the difference between LoRA and QLoRA?"  # Follow the table of contents to answer
     uv run python -m app.agent --full-context --trace "What is the difference between LoRA and QLoRA?"  # Pass all materials at once
+    uv run python -m app.agent --neighbors --trace "What is the difference between LoRA and QLoRA?"  # Homework: also read adjacent pages
+    uv run python -m app.agent --hybrid --trace "What is the difference between LoRA and QLoRA?"  # Homework: vector + graph, re-ranked
+    AIE_RAG_TOP_K=10 uv run python -m app.agent --trace "What is the difference between LoRA and QLoRA?"  # Homework: 10 search results
     uv run python -m app.agent --mcp --trace "What is LoRA?"        # Lecture 05: receive tools from MCP servers
     uv run python -m app.agent --mcp --list-tools               # Lecture 05: list tools visible to the model (no API key needed)
 
@@ -32,7 +35,7 @@ from pydantic_ai.providers.google import GoogleProvider
 
 from app import tools
 from app.retrieval import run_full_context
-from app.config import MODEL, api_error_message, get_api_key
+from app.config import MODEL, RAG_TOP_K, api_error_message, get_api_key
 
 INSTRUCTIONS = """\
 You are a learning support agent for the AI Engineering Pilot Course (AIE2026).
@@ -66,6 +69,16 @@ You are a learning support agent for the AI Engineering Pilot Course (AIE2026).
 - Guide learners with hints on how to think, rather than writing homework answers for them.
 """
 
+# Homework (Implementation): same policy as INSTRUCTIONS, using the tool that also returns adjacent pages
+NEIGHBOR_INSTRUCTIONS = INSTRUCTIONS.replace("search_materials", "search_materials_with_neighbors") + (
+    "- Pages with role \"neighbor\" were added only because they sit next to a hit. Use them only when their text supports the answer.\n"
+)
+
+# Homework (Advanced): same policy as INSTRUCTIONS, using hybrid retrieval
+HYBRID_INSTRUCTIONS = INSTRUCTIONS.replace("search_materials", "search_hybrid") + (
+    "- search_hybrid returns pages from several sections; `why` shows how each page was found. Being linked does not mean a page contains the answer.\n"
+)
+
 FULL_CONTEXT_INSTRUCTIONS = """\
 You are a learning support agent for an AI engineering course.
 - Answer using the provided materials and cite each page using its supplied citation label.
@@ -137,6 +150,30 @@ def print_tools(target: Agent) -> None:
         print(f"  Arguments: {json.dumps(params, ensure_ascii=False)}")
 
 
+def returned_pages(content) -> str | None:
+    """Homework: list the page IDs a search tool returned, so runs can be compared page by page."""
+    try:
+        data = json.loads(content)
+    except (TypeError, ValueError):
+        return None
+    if not isinstance(data, dict):
+        return None
+    groups = []
+    for key in ("results", "seeds", "expanded"):
+        items = data.get(key)
+        if isinstance(items, list) and items:
+            ids = []
+            for item in items:
+                label = item.get("page_id", "?")
+                if item.get("role") == "neighbor":
+                    label += f" (neighbor of {item.get('neighbor_of')})"
+                ids.append(label)
+            groups.append(f"{key}: " + ", ".join(ids))
+    if not groups:
+        return "no pages" + (f" ({data['error']})" if data.get("error") else "")
+    return " | ".join(groups)
+
+
 def print_trace(result, elapsed_seconds: float | None = None) -> None:
     """Display which tools were called with which arguments and what they returned."""
     print("\n--- trace ---")
@@ -169,6 +206,9 @@ def print_trace(result, elapsed_seconds: float | None = None) -> None:
                             print(f"    (Leaf page: retrieved {len(node.get('content', ''))} characters of text)")
                 else:
                     print(f"[tool return] {part.tool_name} -> {str(part.content)[:120]}…")
+                    listed = returned_pages(part.content)
+                    if listed:
+                        print(f"  Pages returned: {listed}")
     usage = result.usage
     if elapsed_seconds is not None:
         print(f"[time] Answer completed in {elapsed_seconds:.2f} seconds (including retrieval and embedding)")
@@ -186,6 +226,8 @@ def main() -> None:
     modes.add_argument("--graph", action="store_true", help="Follow the graph from search results and read candidate pages to answer")
     modes.add_argument("--tree", action="store_true", help="Follow the table of contents and read the necessary pages to answer")
     modes.add_argument("--full-context", action="store_true", help="Pass all materials in lectures.json at once, without searching")
+    modes.add_argument("--neighbors", action="store_true", help="Homework: search, and also read the pages before and after each hit")
+    modes.add_argument("--hybrid", action="store_true", help="Homework: vector search + graph links, re-ranked by similarity")
     parser.add_argument("--list-tools", action="store_true", help="List tools visible to the model and exit (no API key needed)")
     args = parser.parse_args()
 
@@ -195,6 +237,10 @@ def main() -> None:
         mode = target.override(instructions=TREE_INSTRUCTIONS, tools=[tools.browse_tree])
     elif args.graph:
         mode = target.override(instructions=GRAPH_INSTRUCTIONS, tools=[tools.search_graph])
+    elif args.neighbors:
+        mode = target.override(instructions=NEIGHBOR_INSTRUCTIONS, tools=[tools.search_materials_with_neighbors])
+    elif args.hybrid:
+        mode = target.override(instructions=HYBRID_INSTRUCTIONS, tools=[tools.search_hybrid])
     with mode:
         if args.list_tools:
             if args.full_context:
@@ -207,6 +253,8 @@ def main() -> None:
             parser.error("Please provide a question")
 
         print(f"[model] {MODEL}")
+        if not (args.tree or args.full_context or args.mcp):
+            print(f"[search] RAG_TOP_K={RAG_TOP_K}")
         if args.mcp:
             print("[tools] MCP servers (app/mcp_servers.json)")
 
diff --git a/app/config.py b/app/config.py
index e14709d..6cfc3ac 100644
--- a/app/config.py
+++ b/app/config.py
@@ -19,7 +19,17 @@ RAG_TREE = ROOT / "data/rag_data/tree.json"
 RAG_GRAPH = ROOT / "data/rag_data/graph.json"
 RAG_DB = Path(os.getenv("AIE_RAG_DB", str(ROOT / "data/rag_data/index.sqlite3")))
 RAG_DOCUMENT_IDS = ("lec01-main", "lec02-main", "lec03-main")
-RAG_TOP_K = 5
+# Homework (Basic): the number of pages returned by vector search. The default stays 5; set
+# AIE_RAG_TOP_K (for example, AIE_RAG_TOP_K=10) to compare result counts without editing this file.
+RAG_TOP_K = int(os.getenv("AIE_RAG_TOP_K", "5"))
+# Homework (Implementation): also return this many pages before and after each search hit (same document only).
+RAG_NEIGHBOR_WINDOW = 1
+# Homework (Advanced): question-aware hybrid retrieval = vector search + lecture/section structure + course-term graph.
+HYBRID_MAX_PAGES = 7         # pages returned to the model
+HYBRID_MAX_PER_SECTION = 4   # keep at least 3 places for evidence from other sections and lectures
+HYBRID_MIN_CHARS = 150       # shorter pages are section dividers that hold only a title
+HYBRID_MAX_TERM_PAGES = 30   # ignore very common terms (for example "AI agent", 54 pages): they match almost everything
+HYBRID_TERM_BONUS = 0.01     # score bonus per course term from the question that a page mentions (at most 2 count)
 GRAPH_START_K = 3
 GRAPH_HOPS = 2
 GRAPH_MAX_RESULTS = 10
diff --git a/app/retrieval.py b/app/retrieval.py
index a66c6c6..d8a7ce2 100644
--- a/app/retrieval.py
+++ b/app/retrieval.py
@@ -17,7 +17,8 @@ import sqlite_vec
 from app.config import (
     EMBEDDING_DIMENSIONS, EMBEDDING_MAX_TOKENS, EMBEDDING_MODEL,
     RAG_DB, RAG_DOCUMENT_IDS, RAG_SOURCE, RAG_TOP_K, RAG_TREE, get_api_key,
-    RAG_GRAPH, GRAPH_START_K, GRAPH_HOPS, GRAPH_MAX_RESULTS,
+    RAG_GRAPH, GRAPH_START_K, GRAPH_HOPS, GRAPH_MAX_RESULTS, RAG_NEIGHBOR_WINDOW,
+    HYBRID_MAX_PAGES, HYBRID_MAX_PER_SECTION, HYBRID_MIN_CHARS, HYBRID_MAX_TERM_PAGES, HYBRID_TERM_BONUS,
 )
 
 
@@ -126,10 +127,13 @@ def open_index(path: Path):
         db.close()
 
 
-def search(query: str) -> list[dict]:
-    """Embed the query and return up to RAG_TOP_K similar pages."""
+def search(query: str, top_k: int | None = None) -> list[dict]:
+    """Embed the query and return up to top_k (default RAG_TOP_K) similar pages."""
     if not isinstance(query, str) or not query.strip():
         raise ValueError("The search query is empty.")
+    top_k = RAG_TOP_K if top_k is None else top_k
+    if top_k < 1:
+        raise ValueError("The number of search results must be at least 1.")
     with open_index(RAG_DB) as db:
         vector = embed_text(query.strip(), "RETRIEVAL_QUERY")
         columns = {column["name"] for column in db.execute("PRAGMA table_info(chunks)")}
@@ -139,10 +143,163 @@ def search(query: str) -> list[dict]:
                    {citation}
                    vec_distance_cosine(embedding, ?) AS distance
             FROM chunks ORDER BY distance, page_id LIMIT ?
-        """, (sqlite_vec.serialize_float32(vector), RAG_TOP_K))
+        """, (sqlite_vec.serialize_float32(vector), top_k))
         return [dict(row) for row in rows]
 
 
+# --- Homework (Implementation): add the pages just before and after each search hit ---------------
+
+def add_neighbor_pages(hits: list[dict], window: int = RAG_NEIGHBOR_WINDOW) -> list[dict]:
+    """Return the hits plus up to `window` pages before and after each one, in reading order.
+
+    Neighbors never cross into another document, and each page appears only once. A page that is a hit
+    itself keeps role "hit" even if it is also next to another hit. Neighbors carry the same citation
+    metadata as hits, plus `neighbor_of` (the hit's page ID) and `offset` (-1 = page before, +1 = page after).
+    """
+    pages = load_pages(RAG_SOURCE)
+    position = {page["page_id"]: i for i, page in enumerate(pages)}
+    hit_ids = {hit["page_id"] for hit in hits}
+    results, seen = [], set()
+    for rank, hit in enumerate(hits, 1):
+        i = position.get(hit["page_id"])
+        if i is None:  # not in the selected materials: keep the hit as it is
+            if hit["page_id"] not in seen:
+                seen.add(hit["page_id"])
+                results.append({**hit, "role": "hit", "rank": rank})
+            continue
+        for j in range(i - window, i + window + 1):
+            if not 0 <= j < len(pages) or pages[j]["document_id"] != hit["document_id"]:
+                continue
+            page_id = pages[j]["page_id"]
+            if page_id in seen:
+                continue
+            if j == i:
+                seen.add(page_id)
+                results.append({**hit, "role": "hit", "rank": rank})
+            elif page_id not in hit_ids:  # a hit is added later with its own rank and distance
+                seen.add(page_id)
+                results.append({**pages[j], "role": "neighbor", "neighbor_of": hit["page_id"], "offset": j - i})
+    return results
+
+
+def search_with_neighbors(query: str) -> list[dict]:
+    """Vector search (RAG_TOP_K hits), then add the pages before and after each hit."""
+    return add_neighbor_pages(search(query))
+
+
+# --- Homework (Advanced): hybrid retrieval ---------------------------------------------------------
+
+def page_distances(query: str) -> dict[str, float]:
+    """Cosine distance between the query and every page in the search database (one embedding call)."""
+    if not isinstance(query, str) or not query.strip():
+        raise ValueError("The search query is empty.")
+    with open_index(RAG_DB) as db:
+        vector = embed_text(query.strip(), "RETRIEVAL_QUERY")
+        rows = db.execute("SELECT page_id, vec_distance_cosine(embedding, ?) AS distance FROM chunks",
+                          (sqlite_vec.serialize_float32(vector),))
+        return {row["page_id"]: row["distance"] for row in rows}
+
+
+def load_terms(page_ids: set[str]) -> tuple[dict[str, dict], dict[str, set[str]]]:
+    """From graph.json: term nodes (id → node) and term → the selected pages that mention it."""
+    graph = json.loads(RAG_GRAPH.read_text(encoding="utf-8"))
+    terms = {node["id"]: node for node in graph["nodes"] if node["kind"] == "term"}
+    term_pages = defaultdict(set)
+    for edge in graph["edges"]:
+        if edge["relation"] != "mentions":
+            continue
+        a, b = edge["source"], edge["target"]
+        page, term = (a, b) if b in terms else (b, a)
+        if page in page_ids and term in terms:
+            term_pages[term].add(page)
+    return terms, term_pages
+
+
+def named_lectures(question: str) -> set[int]:
+    """Lecture numbers written in the question, for example "Lecture 02" or "Lectures 1 and 3" → {2} or {1, 3}."""
+    numbers = set()
+    for match in re.finditer(r"\bLectures?\s+(\d{1,2}(?:\s*(?:,|and|&|to|–|-)\s*\d{1,2})*)", question, re.IGNORECASE):
+        values = [int(n) for n in re.findall(r"\d{1,2}", match.group(1))]
+        if re.search(r"to|–|-", match.group(1)) and len(values) == 2:
+            values = list(range(values[0], values[1] + 1))
+        numbers.update(values)
+    return numbers
+
+
+def question_terms(question: str, terms: dict[str, dict]) -> set[str]:
+    """Course terms whose name or alias appears in the question (short aliases such as "FT" must match case)."""
+    found = set()
+    for term_id, node in terms.items():
+        for alias in {node["title"], *node.get("aliases", [])}:
+            flags = 0 if len(alias) <= 3 else re.IGNORECASE
+            if re.search(r"(?<![\w-])" + re.escape(alias) + r"(?![\w-])", question, flags):
+                found.add(term_id)
+                break
+    return found
+
+
+def search_hybrid(query: str, *, max_pages: int = HYBRID_MAX_PAGES, max_per_section: int = HYBRID_MAX_PER_SECTION,
+                  min_chars: int = HYBRID_MIN_CHARS, max_term_pages: int = HYBRID_MAX_TERM_PAGES,
+                  term_bonus: float = HYBRID_TERM_BONUS, reserve_lectures: bool = True) -> dict:
+    """Question-aware hybrid retrieval: vector search + lecture/section structure + the course-term graph.
+
+    1. One query embedding gives the distance to every page (page vectors are already in the database).
+    2. Section-divider pages (shorter than min_chars) are skipped: they hold only a title.
+    3. Course terms in the question are found in the term graph (aliases from graph.json). A page that
+       mentions one gets a small bonus (term_bonus each, at most 2). Very common terms are ignored.
+    4. For each lecture the question names, its best page is kept, so a question that spans
+       lectures gets evidence from each of them (Tree-like use of the lecture structure).
+    5. The remaining places go to the highest scores (similarity + term bonus), at most
+       max_per_section pages per section, up to max_pages pages. `why` explains each choice.
+    The keyword arguments let tools/rag_eval.py switch single steps off for comparison.
+    """
+    pages = load_pages(RAG_SOURCE)
+    by_id = {page["page_id"]: page for page in pages}
+    distance = {pid: d for pid, d in page_distances(query).items() if pid in by_id}
+    ranked = sorted(distance, key=lambda pid: (distance[pid], pid))
+    vector_rank = {pid: rank for rank, pid in enumerate(ranked, 1)}
+    content = [pid for pid in ranked if len(by_id[pid]["content"].strip()) >= min_chars]
+    skipped = [pid for pid in ranked[:10] if pid not in content]
+
+    terms, term_pages = load_terms(set(by_id))
+    asked_terms = {t for t in question_terms(query, terms) if 0 < len(term_pages[t]) <= max_term_pages}
+    matched = {pid: sorted(terms[t]["title"] for t in asked_terms if pid in term_pages[t]) for pid in content}
+    score = {pid: 1 - distance[pid] + term_bonus * min(len(matched[pid]), 2) for pid in content}
+    order = sorted(content, key=lambda pid: (-score[pid], pid))
+
+    def why(pid: str) -> list[str]:
+        reasons = [f"similarity rank {vector_rank[pid]} of {len(ranked)}"]
+        if matched[pid]:
+            reasons.append("mentions the question's terms: " + ", ".join(matched[pid]))
+        return reasons
+
+    chosen, per_section = {}, defaultdict(int)
+
+    def take(pid: str, extra: str | None = None) -> None:
+        section = (by_id[pid]["document_id"], by_id[pid]["section"])
+        per_section[section] += 1
+        chosen[pid] = why(pid) + ([extra] if extra else [])
+
+    lectures = sorted(named_lectures(query) & {page["lecture"] for page in pages}) if reserve_lectures else []
+    for lecture in lectures:
+        best = next((pid for pid in order if by_id[pid]["lecture"] == lecture), None)
+        if best and best not in chosen and len(chosen) < max_pages:
+            take(best, f"best page of Lecture {lecture:02d}, which the question names")
+    for pid in order:
+        if len(chosen) >= max_pages:
+            break
+        section = (by_id[pid]["document_id"], by_id[pid]["section"])
+        if pid not in chosen and per_section[section] < max_per_section:
+            take(pid)
+
+    results = [{**by_id[pid], "distance": round(distance[pid], 4), "score": round(score[pid], 4),
+                "vector_rank": vector_rank[pid], "why": chosen[pid]}
+               for pid in sorted(chosen, key=lambda p: (-score[p], p))]
+    return {"results": results, "named_lectures": lectures,
+            "question_terms": sorted(terms[t]["title"] for t in asked_terms),
+            "skipped_divider_pages": skipped}
+
+
 def search_graph(query: str) -> dict:
     """Start with vector search, then expand candidates through adjacent pages and shared terms."""
     pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}
@@ -206,11 +363,26 @@ def run_full_context(agent, question: str, model, instructions: str, prompt_temp
 if __name__ == "__main__":
     parser = argparse.ArgumentParser(description="Search the lecture materials without using an agent")
     parser.add_argument("query", help="What to look up")
+    method = parser.add_mutually_exclusive_group()
+    method.add_argument("--neighbors", action="store_true", help="Homework: also return the pages before and after each hit")
+    method.add_argument("--hybrid", action="store_true", help="Homework: vector search + graph links, re-ranked")
+    parser.add_argument("--top-k", type=int, default=None, help="Number of vector search results (default: RAG_TOP_K)")
     args = parser.parse_args()
-    for i, result in enumerate(search(args.query), 1):
-        print(f"\n{'=' * 60}\nSearch result {i}\n{'=' * 60}")
+    if args.hybrid:
+        found = search_hybrid(args.query)
+        results = found["results"]
+    elif args.neighbors:
+        results = add_neighbor_pages(search(args.query, args.top_k))
+    else:
+        results = search(args.query, args.top_k)
+    for i, result in enumerate(results, 1):
+        print(f"\n{'=' * 60}\nSearch result {i} · {result['page_id']}\n{'=' * 60}")
         print(f"Lecture: {result['document_title']}")
         print(f"Section: {result['section']}")
         print(f"Title: {result['title']}")
         print(f"Page: {result.get('citation') or result['page']}")
+        if result.get("role") == "neighbor":
+            print(f"Added as the page {'before' if result['offset'] < 0 else 'after'} {result['neighbor_of']}")
+        if result.get("why"):
+            print(f"Why: {'; '.join(result['why'])}")
         print(f"\n{result['content']}")
diff --git a/app/tools.py b/app/tools.py
index a5bfa2e..29f76ad 100644
--- a/app/tools.py
+++ b/app/tools.py
@@ -97,6 +97,43 @@ def search_materials(query: str) -> str:
         return json.dumps({"error": api_error_message(e.code), "results": []}, ensure_ascii=False)
 
 
+def search_materials_with_neighbors(query: str) -> str:
+    """Search the main materials for Lectures 01–03 and return relevant pages plus the page just before and after each one.
+
+    Use query to specify what you want to look up. Pages with role "neighbor" were added because they sit next to a hit
+    (see neighbor_of); they may continue the explanation or may be unrelated, so check their text.
+    """
+    from google.genai.errors import APIError
+    import sqlite3
+    from app.retrieval import search_with_neighbors
+
+    try:
+        return json.dumps({"results": search_with_neighbors(query)}, ensure_ascii=False)
+    except (ValueError, FileNotFoundError, sqlite3.Error) as e:
+        return json.dumps({"error": str(e), "results": []}, ensure_ascii=False)
+    except APIError as e:
+        return json.dumps({"error": api_error_message(e.code), "results": []}, ensure_ascii=False)
+
+
+def search_hybrid(query: str) -> str:
+    """Search the main materials for Lectures 01–03 and return up to 7 relevant pages, chosen across sections.
+
+    Combines vector search with links between pages (the next page, shared course terms), then keeps the pages
+    closest to the question. `why` tells you how each page was found. Use query to specify what you want to look up;
+    for questions that combine topics, search each topic separately.
+    """
+    from google.genai.errors import APIError
+    import sqlite3
+    from app.retrieval import search_hybrid as search
+
+    try:
+        return json.dumps(search(query), ensure_ascii=False)
+    except (ValueError, OSError, sqlite3.Error) as e:
+        return json.dumps({"error": str(e), "results": []}, ensure_ascii=False)
+    except APIError as e:
+        return json.dumps({"error": api_error_message(e.code), "results": []}, ensure_ascii=False)
+
+
 def browse_tree(node_id: str | None = None) -> str:
     """Return the table of contents and the first sentence of each page. Specify a page ID to get its full text.
 
diff --git a/data/eval/lec05_questions.jsonl b/data/eval/lec05_questions.jsonl
new file mode 100644
index 0000000..05ec17f
--- /dev/null
+++ b/data/eval/lec05_questions.jsonl
@@ -0,0 +1,6 @@
+{"id": "q1_lora", "type": "single page", "question": "In Lecture 02, what does LoRA freeze and what does it train? What does QLoRA add?", "evidence": ["lec02-main-p052"], "note": "The exercise question. p.52 alone supports the full answer."}
+{"id": "q2_memory", "type": "multiple pages, two sections", "question": "In the Lecture 03 examples, how does compaction differ from memory across sessions? Do all daily notes go into long-term memory?", "evidence": ["lec03-main-p013", "lec03-main-p039", "lec03-main-p040"], "note": "Evidence listed in problem.md. p.39 = compaction versus external memory, p.40 = daily notes, p.13 = what memory is."}
+{"id": "q3_properties", "type": "across lectures", "question": "Which model properties from Lecture 02 become design assumptions for agents in Lecture 03, and which part of the agent design handles each one?", "evidence": ["lec03-main-p003", "lec02-main-p062"], "note": "Lecture 03 p.3 maps each property to a part; Lecture 02 p.62 is the same bridge seen from Lecture 02."}
+{"id": "q4_rag_vs_ft", "type": "across lectures, related terms", "question": "To add new knowledge to a chatbot, why does the course recommend RAG before fine-tuning, and how does the example chatbot in Lecture 01 use RAG?", "evidence": ["lec02-main-p046", "lec02-main-p047", "lec01-main-p049"], "note": "Lecture 02 p.46 and p.47 compare RAG and fine-tuning; Lecture 01 p.49 shows the example chatbot."}
+{"id": "q5_stop", "type": "adjacent pages", "question": "What are the three ways to stop an agent loop, and who should decide whether the task is done?", "evidence": ["lec03-main-p043", "lec03-main-p044"], "note": "Two consecutive pages in Lecture 03 Part 7."}
+{"id": "q6_absent", "type": "not in the materials", "question": "What are the measured average response time and accuracy of the RAG system we just built?", "evidence": [], "note": "The materials contain no measurement logs for this system; the right answer is that it cannot be verified."}
diff --git a/tests/test_lec05_homework.py b/tests/test_lec05_homework.py
new file mode 100644
index 0000000..bf04c94
--- /dev/null
+++ b/tests/test_lec05_homework.py
@@ -0,0 +1,156 @@
+"""Lecture 05 homework tests: result count setting, adjacent pages, hybrid retrieval (no API key needed).
+
+Instead of calling the embedding API, the query vector is replaced with the stored vector of one page,
+so that page should come back first. This checks the retrieval logic, not answer quality.
+"""
+
+import json
+import os
+import sqlite3
+import struct
+import subprocess
+import sys
+
+import pytest
+
+from app import retrieval, tools
+from app.agent import returned_pages
+from app.config import HYBRID_MAX_PAGES, HYBRID_MAX_PER_SECTION, HYBRID_MIN_CHARS, RAG_DB
+
+
+def stored_vector(page_id: str) -> list[float]:
+    with sqlite3.connect(RAG_DB) as db:
+        (blob,) = db.execute("SELECT embedding FROM chunks WHERE page_id = ?", (page_id,)).fetchone()
+    return list(struct.unpack(f"{len(blob) // 4}f", blob))
+
+
+@pytest.fixture
+def query_like(monkeypatch):
+    """Make every query embed to the stored vector of the given page."""
+    def use(page_id: str) -> None:
+        vector = stored_vector(page_id)
+        monkeypatch.setattr(retrieval, "embed_text", lambda text, task_type: vector)
+    return use
+
+
+def test_top_k_can_be_set_with_an_environment_variable():
+    code = "from app.config import RAG_TOP_K; print(RAG_TOP_K)"
+    default = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
+                             env={k: v for k, v in os.environ.items() if k != "AIE_RAG_TOP_K"}, check=True)
+    changed = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
+                             env={**os.environ, "AIE_RAG_TOP_K": "10"}, check=True)
+    assert default.stdout.strip() == "5"
+    assert changed.stdout.strip() == "10"
+
+
+def test_search_returns_the_requested_number_of_pages(query_like):
+    query_like("lec02-main-p052")
+    hits = retrieval.search("LoRA", top_k=3)
+    assert len(hits) == 3
+    assert hits[0]["page_id"] == "lec02-main-p052"
+    with pytest.raises(ValueError):
+        retrieval.search("LoRA", top_k=0)
+
+
+def test_neighbors_add_the_pages_before_and_after_without_duplicates(query_like):
+    query_like("lec03-main-p039")
+    results = retrieval.search_with_neighbors("memory")
+    ids = [r["page_id"] for r in results]
+    assert len(ids) == len(set(ids))
+    hits = [r for r in results if r["role"] == "hit"]
+    assert [r["rank"] for r in hits] == list(range(1, len(hits) + 1))
+    assert hits[0]["page_id"] == "lec03-main-p039"
+    for page in results:
+        if page["role"] == "neighbor":
+            hit = next(r for r in hits if r["page_id"] == page["neighbor_of"])
+            assert page["document_id"] == hit["document_id"]
+            assert page["offset"] in (-1, 1)
+            assert page["content"] and page["citation"]
+
+
+def test_neighbors_stay_inside_the_document():
+    first = retrieval.read_page("lec02-main-p001")
+    results = retrieval.add_neighbor_pages([{**first, "distance": 0.1}])
+    assert [r["page_id"] for r in results] == ["lec02-main-p001", "lec02-main-p002"]
+    last = retrieval.read_page("lec01-main-p073")
+    results = retrieval.add_neighbor_pages([{**last, "distance": 0.1}])
+    assert [r["page_id"] for r in results] == ["lec01-main-p072", "lec01-main-p073"]
+
+
+def test_a_page_that_is_a_hit_is_not_repeated_as_a_neighbor():
+    hits = [{**retrieval.read_page(pid), "distance": d} for pid, d in (("lec03-main-p039", 0.1), ("lec03-main-p040", 0.2))]
+    results = retrieval.add_neighbor_pages(hits)
+    roles = {r["page_id"]: r["role"] for r in results}
+    assert list(roles) == ["lec03-main-p038", "lec03-main-p039", "lec03-main-p040", "lec03-main-p041"]
+    assert roles["lec03-main-p040"] == "hit"
+
+
+def test_hybrid_returns_unique_content_pages_across_sections(query_like):
+    query_like("lec03-main-p039")
+    found = retrieval.search_hybrid("compaction and memory")
+    results = found["results"]
+    ids = [r["page_id"] for r in results]
+    assert ids[0] == "lec03-main-p039"
+    assert 1 <= len(ids) <= HYBRID_MAX_PAGES and len(ids) == len(set(ids))
+    assert all(len(r["content"].strip()) >= HYBRID_MIN_CHARS for r in results)
+    sections = [(r["document_id"], r["section"]) for r in results]
+    assert max(sections.count(s) for s in sections) <= HYBRID_MAX_PER_SECTION
+    assert all(r["why"] and r["citation"] for r in results)
+    assert found["skipped_divider_pages"] == [] or all(len(retrieval.read_page(p)["content"].strip()) < HYBRID_MIN_CHARS for p in found["skipped_divider_pages"])
+    assert [r["score"] for r in results] == sorted((r["score"] for r in results), reverse=True)
+
+
+def test_hybrid_skips_section_divider_pages(query_like):
+    query_like("lec03-main-p037")  # "Part 6 Memory": a divider page with only a title
+    found = retrieval.search_hybrid("memory")
+    assert "lec03-main-p037" not in [r["page_id"] for r in found["results"]]
+    assert "lec03-main-p037" in found["skipped_divider_pages"]
+
+
+def test_lecture_names_and_course_terms_are_read_from_the_question():
+    assert retrieval.named_lectures("In Lecture 02, what does LoRA freeze?") == {2}
+    assert retrieval.named_lectures("from Lecture 02 ... in Lecture 03") == {2, 3}
+    assert retrieval.named_lectures("Lectures 1 and 3") == {1, 3}
+    assert retrieval.named_lectures("What is RAG?") == set()
+    terms, _ = retrieval.load_terms({p["page_id"] for p in retrieval.load_pages()})
+    assert {"term:lora", "term:qlora"} <= retrieval.question_terms("What does QLoRA add to LoRA?", terms)
+    assert "term:fine-tuning" in retrieval.question_terms("Why RAG before FT?", terms)
+    assert "term:fine-tuning" not in retrieval.question_terms("a soft decision", terms)  # "ft" inside a word
+
+
+def test_hybrid_keeps_a_page_from_each_named_lecture(query_like):
+    query_like("lec03-main-p003")  # a Lecture 03 page: without help, Lecture 01 pages rank low
+    question = "How do Lecture 01 and Lecture 03 describe agents?"
+    found = retrieval.search_hybrid(question)
+    lectures = [r["lecture"] for r in found["results"]]
+    assert found["named_lectures"] == [1, 3] and 1 in lectures and 3 in lectures
+    reserved = [r for r in found["results"] if any("which the question names" in w for w in r["why"])]
+    assert {r["lecture"] for r in reserved} == {1, 3}
+    plain = retrieval.search_hybrid(question, reserve_lectures=False)
+    assert len(plain["results"]) == len(found["results"])
+
+
+def test_hybrid_term_bonus_marks_pages_that_mention_question_terms(query_like):
+    query_like("lec02-main-p052")
+    found = retrieval.search_hybrid("What does QLoRA add to LoRA?")
+    assert set(found["question_terms"]) == {"LoRA", "QLoRA"}
+    top = found["results"][0]
+    assert top["page_id"] == "lec02-main-p052"
+    assert any("mentions the question's terms" in w for w in top["why"])
+
+
+def test_tool_wrappers_return_json(query_like):
+    query_like("lec02-main-p052")
+    with_neighbors = json.loads(tools.search_materials_with_neighbors("LoRA"))
+    hybrid = json.loads(tools.search_hybrid("LoRA"))
+    assert with_neighbors["results"][0]["page_id"] == "lec02-main-p052"
+    assert hybrid["results"][0]["page_id"] == "lec02-main-p052"
+    assert json.loads(tools.search_hybrid("  "))["error"]
+
+
+def test_trace_lists_returned_pages():
+    content = json.dumps({"results": [{"page_id": "a"}, {"page_id": "b", "role": "neighbor", "neighbor_of": "a"}]})
+    assert returned_pages(content) == "results: a, b (neighbor of a)"
+    graph = json.dumps({"seeds": [{"page_id": "s"}], "expanded": [{"page_id": "e"}]})
+    assert returned_pages(graph) == "seeds: s | expanded: e"
+    assert returned_pages("not json") is None
diff --git a/tools/lec05_runs.sh b/tools/lec05_runs.sh
new file mode 100755
index 0000000..b1773bc
--- /dev/null
+++ b/tools/lec05_runs.sh
@@ -0,0 +1,108 @@
+#!/usr/bin/env bash
+# Lecture 05: run every comparison for the exercise and the homework, save the outputs, then commit and push.
+#
+# Usage (from the repository root, on the lec05 branch):  bash tools/lec05_runs.sh
+# Takes about 20 to 30 minutes. Safe to run again: finished runs are skipped, failed ones are retried.
+# Each output goes to lectures/05/runs/<name>.txt and starts with the exact command that produced it.
+set -u
+cd "$(git rev-parse --show-toplevel)"
+OUT=lectures/05/runs
+QUESTIONS=data/eval/lec05_questions.jsonl
+PAUSE=${PAUSE:-20}   # seconds between runs, to stay under the free-tier per-minute limits
+mkdir -p "$OUT"
+
+[ "$(git branch --show-current)" = "lec05" ] || { echo "Please switch to the lec05 branch first (git switch lec05)."; exit 1; }
+[ -n "${GEMINI_API_KEY:-}" ] || { echo "GEMINI_API_KEY is not set. Add the Codespaces secret and restart the Codespace."; exit 1; }
+
+question() {
+  python3 -c 'import json, sys
+for line in open(sys.argv[1], encoding="utf-8"):
+    if line.strip() and json.loads(line)["id"] == sys.argv[2]:
+        print(json.loads(line)["question"])' "$QUESTIONS" "$1"
+}
+
+# run NAME QUESTION_ID TOP_K FLAGS...   (TOP_K: a number sets AIE_RAG_TOP_K; "-" keeps the default of 5)
+run() {
+  local name=$1 qid=$2 topk=$3; shift 3
+  local file="$OUT/$name.txt" q env_setting=""
+  if [ -s "$file" ] && grep -q '^\[cost\]' "$file"; then echo "skip  $name (already done)"; return 0; fi
+  q=$(question "$qid")
+  [ "$topk" = "-" ] || env_setting="AIE_RAG_TOP_K=$topk"
+  for attempt in 1 2 3 4; do
+    echo "run   $name (attempt $attempt)"
+    {
+      echo "\$ ${env_setting:+$env_setting }uv run python -m app.agent --trace $* \"$q\""
+      echo
+      env $env_setting uv run python -m app.agent --trace "$@" "$q"
+    } > "$file" 2>&1
+    if grep -q '^\[cost\]' "$file"; then
+      grep -E '^\[(time|usage)\]' "$file" | sed 's/^/      /'
+      sleep "$PAUSE"
+      return 0
+    fi
+    echo "      not finished: $(grep -iE 'rate limit|busy|error|exceeded' "$file" | head -1 | cut -c1-120)"
+    sleep 60
+  done
+  echo "      gave up on $name after 4 attempts; the last output is kept in $file"
+}
+
+echo "== STEP 2: search results alone"
+if [ ! -s "$OUT/step2_retrieval.txt" ]; then
+  { echo '$ uv run python -m app.retrieval "LoRA QLoRA difference"'; echo; uv run python -m app.retrieval "LoRA QLoRA difference"; } > "$OUT/step2_retrieval.txt" 2>&1
+  sleep 5
+fi
+
+echo "== Retrieval-only comparison on questions with known evidence pages"
+uv run python tools/rag_eval.py --questions "$QUESTIONS" --embeddings "$OUT/query_embeddings.json" \
+  --out "$OUT/retrieval_eval.md" > "$OUT/retrieval_eval_console.txt" 2>&1 || echo "      retrieval comparison failed; see $OUT/retrieval_eval_console.txt"
+sleep 5
+
+echo "== Exercise: the same question with each method (q1), then a multi-page question (q2)"
+run q1_full       q1_lora   - --full-context
+run q1_vector     q1_lora   -
+run q1_tree       q1_lora   - --tree
+run q1_graph      q1_lora   - --graph
+run q2_vector     q2_memory -
+run q2_tree       q2_memory - --tree
+run q2_graph      q2_memory - --graph
+run q2_full       q2_memory - --full-context
+run q6_vector     q6_absent -
+
+echo "== Homework, Basic: 10 search results instead of 5"
+run q1_top10      q1_lora   10
+run q2_top10      q2_memory 10
+
+echo "== Homework, Implementation: add the pages before and after each hit"
+run q1_neighbors  q1_lora   - --neighbors
+run q2_neighbors  q2_memory - --neighbors
+run q5_vector     q5_stop   -
+run q5_neighbors  q5_stop   - --neighbors
+
+echo "== Homework, Advanced: question-aware hybrid retrieval"
+run q1_hybrid     q1_lora       - --hybrid
+run q2_hybrid     q2_memory     - --hybrid
+run q3_vector     q3_properties -
+run q3_graph      q3_properties - --graph
+run q3_hybrid     q3_properties - --hybrid
+run q4_vector     q4_rag_vs_ft  -
+run q4_graph      q4_rag_vs_ft  - --graph
+run q4_hybrid     q4_rag_vs_ft  - --hybrid
+run q5_hybrid     q5_stop       - --hybrid
+run q6_hybrid     q6_absent     - --hybrid
+
+echo "== Summary"
+for f in "$OUT"/q*.txt; do
+  printf '%-18s %s | %s\n' "$(basename "$f" .txt)" \
+    "$(grep -m1 '^\[time\]' "$f" | sed 's/\[time\] Answer completed in //; s/ (including.*//')" \
+    "$(grep -m1 '^\[usage\]' "$f" | sed 's/\[usage\] //')"
+done | tee "$OUT/summary.txt"
+
+missing=$(for f in "$OUT"/q*.txt; do grep -q '^\[cost\]' "$f" || basename "$f"; done)
+if [ -n "$missing" ]; then
+  echo "Some runs did not finish: $missing"
+  echo "Wait a few minutes and run this script again; finished runs are skipped."
+fi
+
+git add "$OUT" "$QUESTIONS"
+git commit -q -m "Lecture 05: comparison runs for the exercise and homework" && echo "Committed the results."
+git push -u origin lec05 && echo "Pushed to your fork (branch lec05)."
diff --git a/tools/rag_eval.py b/tools/rag_eval.py
new file mode 100644
index 0000000..c74f208
--- /dev/null
+++ b/tools/rag_eval.py
@@ -0,0 +1,171 @@
+"""Lecture 05 homework: compare retrieval methods on questions whose evidence pages are known.
+
+For each question in the question set, every method is run on the same query embedding, and we count how many of
+the known evidence pages it returns, how many pages it returns, and how much text it would add to the model input.
+No answer is generated, so this costs one embedding call per question (none if the embeddings are already saved).
+
+Usage (from the repository root):
+    uv run python tools/rag_eval.py --questions data/eval/lec05_questions.jsonl \
+        --embeddings lectures/05/runs/query_embeddings.json --out lectures/05/runs/retrieval_eval.md
+
+The query embeddings are saved so the comparison can be repeated (and new settings tried) without the API.
+"""
+
+import argparse
+import json
+import sys
+import time
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parent.parent
+sys.path.insert(0, str(ROOT))
+
+from app import retrieval  # noqa: E402
+
+
+def read_jsonl(path: Path) -> list[dict]:
+    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
+
+
+def embed_questions(questions: list[dict], cache_path: Path) -> dict[str, list[float]]:
+    """Return question text → query vector, calling the API only for questions not yet saved."""
+    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.is_file() else {}
+    real_embed = retrieval.embed_text
+    for q in questions:
+        text = q["question"].strip()
+        if text in cache:
+            continue
+        for attempt in range(1, 5):
+            try:
+                cache[text] = real_embed(text, "RETRIEVAL_QUERY")
+                break
+            except Exception as e:  # rate limits and busy errors: wait and retry
+                if attempt == 4:
+                    raise
+                print(f"  embedding failed ({type(e).__name__}: {str(e)[:80]}); retrying in 30 seconds")
+                time.sleep(30)
+        cache_path.parent.mkdir(parents=True, exist_ok=True)
+        cache_path.write_text(json.dumps(cache), encoding="utf-8")
+        time.sleep(2)
+    return cache
+
+
+def use_saved_embeddings(cache: dict[str, list[float]]) -> None:
+    """Make retrieval use the saved vectors instead of calling the API."""
+    def embed(text: str, task_type: str) -> list[float]:
+        if text.strip() not in cache:
+            raise KeyError(f"No saved embedding for: {text[:60]}")
+        return cache[text.strip()]
+    retrieval.embed_text = embed
+
+
+def graph_pages(query: str) -> list[dict]:
+    found = retrieval.search_graph(query)
+    return found["seeds"] + found["expanded"]
+
+
+METHODS = {
+    "Vector search, top 5 (provided)": lambda q: retrieval.search(q, top_k=5),
+    "Vector search, top 10 (Basic)": lambda q: retrieval.search(q, top_k=10),
+    "Vector top 5 + adjacent pages (Implementation)": lambda q: retrieval.add_neighbor_pages(retrieval.search(q, top_k=5)),
+    "Graph (provided)": graph_pages,
+    "Hybrid (Advanced)": lambda q: retrieval.search_hybrid(q)["results"],
+}
+ABLATIONS = {
+    "Hybrid without the divider-page filter": lambda q: retrieval.search_hybrid(q, min_chars=0)["results"],
+    "Hybrid without keeping a page per named lecture": lambda q: retrieval.search_hybrid(q, reserve_lectures=False)["results"],
+    "Hybrid without the question-term bonus": lambda q: retrieval.search_hybrid(q, term_bonus=0.0)["results"],
+    "Hybrid without the per-section cap": lambda q: retrieval.search_hybrid(q, max_per_section=99)["results"],
+    "Vector search, top 7 (same page count as hybrid)": lambda q: retrieval.search(q, top_k=7),
+}
+
+
+def evaluate(questions: list[dict], methods: dict) -> list[dict]:
+    rows = []
+    for name, run in methods.items():
+        for q in questions:
+            pages = run(q["question"])
+            ids = [p["page_id"] for p in pages]
+            evidence = q["evidence"]
+            rows.append({
+                "method": name, "question": q["id"], "pages": ids,
+                "found": [e for e in evidence if e in ids], "evidence": evidence,
+                "characters": sum(len(p["content"]) for p in pages),
+            })
+    return rows
+
+
+def evidence_ranks(questions: list[dict]) -> list[str]:
+    """Where each evidence page sits in the full similarity ranking (1 = most similar of 214 pages)."""
+    lines = []
+    for q in questions:
+        if not q["evidence"]:
+            continue
+        distance = retrieval.page_distances(q["question"])
+        ranked = sorted(distance, key=lambda pid: (distance[pid], pid))
+        parts = [f"{e} = rank {ranked.index(e) + 1}" for e in q["evidence"]]
+        lines.append(f"- {q['id']}: " + ", ".join(parts))
+    return lines
+
+
+def summary_table(rows: list[dict], questions: list[dict], methods: list[str]) -> list[str]:
+    answerable = [q["id"] for q in questions if q["evidence"]]
+    total = sum(len(q["evidence"]) for q in questions)
+    lines = ["| Method | Evidence pages found (of %d) | Questions with all evidence (of %d) | Average pages returned | Average characters returned |" % (total, len(answerable)),
+             "|---|---|---|---|---|"]
+    for m in methods:
+        mine = [r for r in rows if r["method"] == m]
+        found = sum(len(r["found"]) for r in mine)
+        complete = sum(1 for r in mine if r["question"] in answerable and len(r["found"]) == len(r["evidence"]))
+        pages = sum(len(r["pages"]) for r in mine) / len(mine)
+        chars = sum(r["characters"] for r in mine) / len(mine)
+        lines.append(f"| {m} | {found} | {complete} | {pages:.1f} | {chars:,.0f} |")
+    return lines
+
+
+def detail_table(rows: list[dict], questions: list[dict], methods: list[str]) -> list[str]:
+    lines = ["| Method | " + " | ".join(q["id"] for q in questions) + " |", "|---|" + "---|" * len(questions)]
+    for m in methods:
+        cells = []
+        for q in questions:
+            r = next(r for r in rows if r["method"] == m and r["question"] == q["id"])
+            got = f"{len(r['found'])}/{len(r['evidence'])}" if r["evidence"] else "n/a"
+            cells.append(f"{got} · {len(r['pages'])} p · {r['characters']:,} ch")
+        lines.append(f"| {m} | " + " | ".join(cells) + " |")
+    return lines
+
+
+def main() -> None:
+    parser = argparse.ArgumentParser(description="Compare retrieval methods on questions with known evidence pages")
+    parser.add_argument("--questions", type=Path, default=ROOT / "data/eval/lec05_questions.jsonl")
+    parser.add_argument("--embeddings", type=Path, default=ROOT / "lectures/05/runs/query_embeddings.json")
+    parser.add_argument("--out", type=Path, default=ROOT / "lectures/05/runs/retrieval_eval.md")
+    args = parser.parse_args()
+
+    questions = read_jsonl(args.questions)
+    cache = embed_questions(questions, args.embeddings)
+    use_saved_embeddings(cache)
+    rows = evaluate(questions, {**METHODS, **ABLATIONS})
+
+    out = ["# Retrieval comparison on questions with known evidence pages", "",
+           "Same query embedding for every method. No answers are generated here; this measures only what each method returns.",
+           "Characters = total page text returned (a rough measure of added input).", "",
+           "## Summary", "", *summary_table(rows, questions, list(METHODS)), "",
+           "## Per question (evidence found · pages · characters)", "", *detail_table(rows, questions, list(METHODS)), "",
+           "## Ablation of the hybrid method", "", *summary_table(rows, questions, ["Hybrid (Advanced)", *ABLATIONS]), "",
+           "## Where the evidence pages rank by similarity alone (214 pages)", "", *evidence_ranks(questions), "",
+           "## Pages returned", ""]
+    for r in rows:
+        if r["method"] in METHODS:
+            missing = [e for e in r["evidence"] if e not in r["found"]]
+            out.append(f"- {r['method']} · {r['question']}: {', '.join(r['pages'])}"
+                       + (f" — missing: {', '.join(missing)}" if missing else ""))
+    args.out.parent.mkdir(parents=True, exist_ok=True)
+    args.out.write_text("\n".join(out) + "\n", encoding="utf-8")
+    args.out.with_suffix(".json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
+    print("\n".join(out[:40]))
+    print(f"\nSaved: {args.out}")
+
+
+if __name__ == "__main__":
+    main()
LEC05_PATCH_END
  chmod +x tools/lec05_runs.sh
  echo "   Homework code added."
else
  echo "   Homework code already present."
fi

echo "== 4. Install and test (no API key needed)"
uv sync --frozen -q
uv run pytest -q

if [ -n "$(git status --porcelain)" ]; then
  git add app/agent.py app/config.py app/retrieval.py app/tools.py tests/test_lec05_homework.py \
          tools/rag_eval.py tools/lec05_runs.sh data/eval/lec05_questions.jsonl
  git commit -q -m "Lecture 05 homework code: search result count setting, adjacent pages, question-aware hybrid retrieval"
  echo "   Committed the homework code."
fi

echo
echo "Setup finished. Next, run the comparisons (about 20 to 30 minutes):"
echo "    bash tools/lec05_runs.sh"
