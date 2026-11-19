#!/usr/bin/env bash
# Lecture 05: run every comparison for the exercise and the homework, save the outputs, then commit and push.
#
# Usage (from the repository root, on the lec05 branch):  bash tools/lec05_runs.sh
# Takes about 20 to 30 minutes. Safe to run again: finished runs are skipped, failed ones are retried.
# Each output goes to lectures/05/runs/<name>.txt and starts with the exact command that produced it.
set -u
cd "$(git rev-parse --show-toplevel)"
OUT=lectures/05/runs
QUESTIONS=data/eval/lec05_questions.jsonl
PAUSE=${PAUSE:-20}   # seconds between runs, to stay under the free-tier per-minute limits
mkdir -p "$OUT"

[ "$(git branch --show-current)" = "lec05" ] || { echo "Please switch to the lec05 branch first (git switch lec05)."; exit 1; }
[ -n "${GEMINI_API_KEY:-}" ] || { echo "GEMINI_API_KEY is not set. Add the Codespaces secret and restart the Codespace."; exit 1; }

question() {
  python3 -c 'import json, sys
for line in open(sys.argv[1], encoding="utf-8"):
    if line.strip() and json.loads(line)["id"] == sys.argv[2]:
        print(json.loads(line)["question"])' "$QUESTIONS" "$1"
}

# run NAME QUESTION_ID TOP_K FLAGS...   (TOP_K: a number sets AIE_RAG_TOP_K; "-" keeps the default of 5)
run() {
  local name=$1 qid=$2 topk=$3; shift 3
  local file="$OUT/$name.txt" q env_setting=""
  if [ -s "$file" ] && grep -q '^\[cost\]' "$file"; then echo "skip  $name (already done)"; return 0; fi
  q=$(question "$qid")
  [ "$topk" = "-" ] || env_setting="AIE_RAG_TOP_K=$topk"
  for attempt in 1 2 3 4; do
    echo "run   $name (attempt $attempt)"
    {
      echo "\$ ${env_setting:+$env_setting }uv run python -m app.agent --trace $* \"$q\""
      echo
      env $env_setting uv run python -m app.agent --trace "$@" "$q"
    } > "$file" 2>&1
    if grep -q '^\[cost\]' "$file"; then
      grep -E '^\[(time|usage)\]' "$file" | sed 's/^/      /'
      sleep "$PAUSE"
      return 0
    fi
    echo "      not finished: $(grep -iE 'rate limit|busy|error|exceeded' "$file" | head -1 | cut -c1-120)"
    sleep 60
  done
  echo "      gave up on $name after 4 attempts; the last output is kept in $file"
}

echo "== STEP 2: search results alone"
if [ ! -s "$OUT/step2_retrieval.txt" ]; then
  { echo '$ uv run python -m app.retrieval "LoRA QLoRA difference"'; echo; uv run python -m app.retrieval "LoRA QLoRA difference"; } > "$OUT/step2_retrieval.txt" 2>&1
  sleep 5
fi

echo "== Retrieval-only comparison on questions with known evidence pages"
uv run python tools/rag_eval.py --questions "$QUESTIONS" --embeddings "$OUT/query_embeddings.json" \
  --out "$OUT/retrieval_eval.md" > "$OUT/retrieval_eval_console.txt" 2>&1 || echo "      retrieval comparison failed; see $OUT/retrieval_eval_console.txt"
sleep 5

echo "== Exercise: the same question with each method (q1), then a multi-page question (q2)"
run q1_full       q1_lora   - --full-context
run q1_vector     q1_lora   -
run q1_tree       q1_lora   - --tree
run q1_graph      q1_lora   - --graph
run q2_vector     q2_memory -
run q2_tree       q2_memory - --tree
run q2_graph      q2_memory - --graph
run q2_full       q2_memory - --full-context
run q6_vector     q6_absent -

echo "== Homework, Basic: 10 search results instead of 5"
run q1_top10      q1_lora   10
run q2_top10      q2_memory 10

echo "== Homework, Implementation: add the pages before and after each hit"
run q1_neighbors  q1_lora   - --neighbors
run q2_neighbors  q2_memory - --neighbors
run q5_vector     q5_stop   -
run q5_neighbors  q5_stop   - --neighbors

echo "== Homework, Advanced: question-aware hybrid retrieval"
run q1_hybrid     q1_lora       - --hybrid
run q2_hybrid     q2_memory     - --hybrid
run q3_vector     q3_properties -
run q3_graph      q3_properties - --graph
run q3_hybrid     q3_properties - --hybrid
run q4_vector     q4_rag_vs_ft  -
run q4_graph      q4_rag_vs_ft  - --graph
run q4_hybrid     q4_rag_vs_ft  - --hybrid
run q5_hybrid     q5_stop       - --hybrid
run q6_hybrid     q6_absent     - --hybrid

echo "== Summary"
for f in "$OUT"/q*.txt; do
  printf '%-18s %s | %s\n' "$(basename "$f" .txt)" \
    "$(grep -m1 '^\[time\]' "$f" | sed 's/\[time\] Answer completed in //; s/ (including.*//')" \
    "$(grep -m1 '^\[usage\]' "$f" | sed 's/\[usage\] //')"
done | tee "$OUT/summary.txt"

missing=$(for f in "$OUT"/q*.txt; do grep -q '^\[cost\]' "$f" || basename "$f"; done)
if [ -n "$missing" ]; then
  echo "Some runs did not finish: $missing"
  echo "Wait a few minutes and run this script again; finished runs are skipped."
fi

git add "$OUT" "$QUESTIONS"
git commit -q -m "Lecture 05: comparison runs for the exercise and homework" && echo "Committed the results."
git push -u origin lec05 && echo "Pushed to your fork (branch lec05)."
