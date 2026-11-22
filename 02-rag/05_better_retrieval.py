"""
Lesson 05: Better retrieval, and MEASURING it.

    Most bad RAG answers are retrieval failures: the right chunk was never in the prompt.

What you'll learn:
  - BM25 keyword search (the classic search-engine algorithm)
  - Hybrid search: combine keyword + vector results with Reciprocal Rank Fusion (RRF)
  - Reranking: re-score the top candidates with a slower, smarter model (a cross-encoder)
  - Query rewriting: let an LLM turn a messy question into good search queries
  - A retrieval eval: hit rate @k and MRR on a labelled question set, so you compare methods
    with NUMBERS instead of vibes

Run:  uv run python 02-rag/05_better_retrieval.py
"""

import json
import os
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi

from course_utils import trace
from course_utils.rag import VectorIndex, chunk_documents, load_documents, rerank_scores

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
client = anthropic.Anthropic()
HERE = Path(__file__).parent

chunks = chunk_documents(load_documents(HERE / "data" / "nimbus"))
vector_index = VectorIndex(chunks)


# ---------------------------------------------------------------------------
# 1. BM25: keyword search done properly
# ---------------------------------------------------------------------------
trace.step("1. BM25 keyword search")


def tokenize(text: str) -> list[str]:
    # Lowercase words; keep codes like "err-4012" and "$99" together.
    return re.findall(r"[a-z0-9$]+(?:[-.][a-z0-9]+)*", text.lower())


# 💡 WHY BM25 beats lesson 06's "any word matches": it scores each chunk by
#   - how often the query words appear in it (with diminishing returns),
#   - how RARE each word is across all chunks ("err-4012" appears once → very informative;
#     "the" appears everywhere → worth ~nothing),
#   - chunk length (a match in a short chunk counts more).
bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])


def bm25_search(query: str, k: int = 4) -> list[dict]:
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)[:k]
    return [{**chunks[i], "score": float(scores[i])} for i in ranked]


for q in ["ERR-5003", "my upload is huge and it fails"]:
    trace.show_retrieval(q, bm25_search(q, 3), label="BM25", score_name="bm25")
    trace.show_retrieval(q, vector_index.search(q, 3), label="vector", score_name="cosine")
# Keyword search wins on exact identifiers (error codes, product names, SKUs, people's names).
# Vector search wins on paraphrases. Users send both kinds of query, so use both.


# ---------------------------------------------------------------------------
# 2. Hybrid search with Reciprocal Rank Fusion
# ---------------------------------------------------------------------------
trace.step("2. Hybrid = BM25 + vectors, fused with RRF")


def rrf(result_lists: list[list[dict]], k: int = 60) -> list[dict]:
    """Reciprocal Rank Fusion: score(chunk) = Σ 1 / (k + rank in each list)."""
    # 💡 WHY ranks, not scores? BM25 scores (0–20) and cosine scores (0–1) are on different
    # scales, so you can't just add them. Ranks are comparable. k=60 is the standard constant;
    # it stops the #1 result of one list from dominating.
    fused: dict[str, dict] = {}
    for results in result_lists:
        for rank, r in enumerate(results, start=1):
            entry = fused.setdefault(r["id"], {**r, "score": 0.0})
            # 🐍 PYTHON NOTE: dict.setdefault(key, default) returns the existing value, or
            # inserts `default` first if the key is missing.
            entry["score"] += 1 / (k + rank)
    return sorted(fused.values(), key=lambda r: r["score"], reverse=True)


def hybrid_search(query: str, k: int = 4, candidates: int = 10) -> list[dict]:
    return rrf([bm25_search(query, candidates), vector_index.search(query, candidates)])[:k]


trace.show_retrieval("ERR-5003", hybrid_search("ERR-5003", 3), label="hybrid", score_name="rrf")


# ---------------------------------------------------------------------------
# 3. Reranking with a cross-encoder
# ---------------------------------------------------------------------------
trace.step("3. Rerank the top candidates")

# An embedding model encodes the query and the chunk SEPARATELY, then compares vectors:
# fast (chunk vectors are computed once), but a bit shallow.
# A cross-encoder reads query + chunk TOGETHER and outputs one relevance score: much more
# accurate, but too slow to run on every chunk. So: retrieve ~20 candidates fast, rerank them.
# Hosted options in production: Cohere Rerank, Voyage rerank, or an LLM as reranker.


def hybrid_rerank(query: str, k: int = 4, candidates: int = 10) -> list[dict]:
    pool = hybrid_search(query, k=candidates, candidates=candidates)
    scores = rerank_scores(query, [c["text"] for c in pool])
    for c, s in zip(pool, scores):
        c["score"] = s
    return sorted(pool, key=lambda c: c["score"], reverse=True)[:k]


q = "Can I get my money back?"
trace.show_retrieval(q, hybrid_search(q, 4), label="hybrid, before rerank", score_name="rrf")
trace.show_retrieval(q, hybrid_rerank(q, 4), label="after cross-encoder rerank", score_name="rerank")
# Rerank scores are raw model outputs (logits): only the ORDER matters, negatives are fine.
# ⚠️ GOTCHA: look at #1. The reranker loves faq_2024.md, because it contains the literal
# question "Can I get my money back?". But that FAQ is OUTDATED (30 days, old prices).
# Relevance ≠ correctness. Rankers can't know a document is stale; metadata can. Fixes:
# filter on `updated` (lesson 03), pass dates to the LLM (lesson 04), or delete old docs.
# Keeping the knowledge base clean is often the highest-impact RAG "technique".


# ---------------------------------------------------------------------------
# 4. Measure it: a retrieval eval
# ---------------------------------------------------------------------------
trace.step("4. Retrieval eval: which method finds the right document?")

# A labelled set: each question + the file that contains the answer. 12 questions is tiny;
# real eval sets have 50–500, often built from real user questions. (Phase 5 goes deep.)
EVAL = json.loads((HERE / "data" / "eval_questions.json").read_text())

METHODS = {
    "vector": lambda q, k: vector_index.search(q, k),
    "bm25": bm25_search,
    "hybrid": hybrid_search,
    "hybrid+rerank": hybrid_rerank,
}
K = 3


def evaluate(search_fn) -> tuple[float, float, list[str]]:
    hits, reciprocal_ranks, misses = 0, [], []
    for item in EVAL:
        sources = [r["source"] for r in search_fn(item["question"], K)]
        if item["expected_source"] in sources:
            hits += 1
            reciprocal_ranks.append(1 / (sources.index(item["expected_source"]) + 1))
        else:
            reciprocal_ranks.append(0)
            misses.append(item["question"])
    return hits / len(EVAL), sum(reciprocal_ranks) / len(EVAL), misses


print(f"{'method':<15} hit@{K}   MRR    (on {len(EVAL)} questions)")
for name, fn in METHODS.items():
    hit_rate, mrr, misses = evaluate(fn)
    print(f"{name:<15} {hit_rate:5.0%}   {mrr:.2f}")
    for m in misses:
        print(f"{'':<17}✗ {m}")
# hit@3 = in how many questions the right document was in the top 3 at all.
# MRR (mean reciprocal rank) = 1.0 if it's always FIRST, 0.5 if always second, ...
# ⚠️ GOTCHA: with 12 questions, one question = 8 percentage points. Differences of one
# question are noise. Notice too that hybrid can have a LOWER MRR than pure vector here: BM25
# drags keyword-matching but wrong chunks upward. Techniques that win on benchmarks don't
# automatically win on YOUR data. That's exactly why you measure.
# 💡 WHY this matters: now you can change chunk size, the embedding model or k and KNOW
# whether it got better. Without this, RAG tuning is guesswork. Interviewers ask
# "how did you evaluate your RAG system?". This is the first half of the answer
# (the second half, judging the generated ANSWERS, comes in Phase 5).


# ---------------------------------------------------------------------------
# 5. Query rewriting with an LLM
# ---------------------------------------------------------------------------
trace.step("5. Query rewriting")


class StandaloneQuery(BaseModel):
    query: str = Field(description="A self-contained search query that makes sense without the chat")


# In a chat, follow-up messages only make sense together with the earlier turns.
chat_history = [
    {"role": "user", "content": "How long are transcripts kept on the Starter plan?"},
    {"role": "assistant", "content": "On Starter, recordings and transcripts are kept for 90 days."},
]
follow_up = "and on the pricier one?"

trace.show_retrieval(follow_up, hybrid_rerank(follow_up, 3), label="raw follow-up", score_name="rerank")
# Searching for "and on the pricier one?" alone finds pricing chunks: the search has no idea
# we're talking about transcript RETENTION.

history_text = "\n".join(f"{m['role']}: {m['content']}" for m in chat_history)
request = dict(
    model=MODEL, max_tokens=16000,
    system=("Rewrite the user's latest message as a standalone search query for a help-centre "
            "search engine, using the chat history to fill in what it refers to."),
    messages=[{"role": "user", "content":
               f"<chat_history>\n{history_text}\n</chat_history>\n\n<latest_message>{follow_up}</latest_message>"}],
    output_format=StandaloneQuery,
)
trace.show_request(request, label="rewrite the follow-up")
response = client.messages.parse(**request)
trace.show_response(response, label="standalone query")
rewritten = response.parsed_output.query

trace.show_retrieval(rewritten, hybrid_rerank(rewritten, 3), label="rewritten query", score_name="rerank")
# 💡 WHY: every chat-over-documents product needs this step (the project uses it). It costs
# one extra small LLM call: use a cheap model like Haiku for it. Related tricks:
#   - multi-query: rewrite into 2-3 different queries, search each, fuse with rrf()
#   - HyDE: ask the LLM for a fake ANSWER and embed that (answers look more like documents
#     than questions do)

trace.show_totals("Lesson 05 totals")

# 🧪 TRY:
#   1. Re-chunk with max_chars=300 and max_chars=1200 (chunk_documents(..., max_chars=...)) and
#      re-run the eval. Which size wins for each method?
#   2. Add 5 harder questions to data/eval_questions.json (paraphrases, error codes, questions
#      that need two documents). Which method breaks first?
#   3. Change K to 1. Rerankers shine when only the very top result counts.
#   4. Multi-query: ask the LLM for 3 rewrites of a messy message ("ugh it stopped recording
#      after i changed my google password??"), search each, and fuse with rrf().
