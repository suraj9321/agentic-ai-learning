"""
Lesson 01: Embeddings, turning meaning into numbers.

What you'll learn:
  - An embedding is a list of numbers (a vector) that represents what a text MEANS
  - Texts with similar meaning get similar vectors, even with no words in common
  - Cosine similarity: how "close" two vectors are
  - Why this beats keyword search (remember lesson 06's search_docs returning everything?)

No LLM calls and no API key needed: the embedding model runs on your laptop.
The first run downloads it (~70 MB) into .cache/fastembed/.

Run:  uv run python 02-rag/01_embeddings.py
"""

import os

os.environ.setdefault("HF_HUB_VERBOSITY", "error")  # hide download warnings

import numpy as np
from dotenv import load_dotenv
from fastembed import TextEmbedding

from course_utils import trace
from course_utils.rag import CACHE_DIR

load_dotenv(override=True)  # only for TRACE settings; this lesson needs no API key

# ---------------------------------------------------------------------------
# 1. Load an embedding model and embed one sentence
# ---------------------------------------------------------------------------
trace.step("1. One sentence → one vector")

# 💡 WHY a separate model? LLMs like Claude GENERATE text. Embedding models only turn text
# into vectors, which is what search needs. They're tiny and cheap: this one runs on a CPU.
# Options in production: Voyage AI (Anthropic's recommended partner), OpenAI
# text-embedding-3, Cohere, or open-source models like this one (BAAI's bge family).
model = TextEmbedding("BAAI/bge-small-en-v1.5", cache_dir=str(CACHE_DIR))

# 🐍 PYTHON NOTE: model.embed() returns a *generator* (values produced lazily, one by one).
# list(...) forces it to produce them all. Each item is a numpy array.
vector = list(model.embed(["Can I get my money back?"]))[0]

trace.show_vector("Can I get my money back?", vector)
print(f"type: {type(vector).__name__}, shape: {vector.shape}, dtype: {vector.dtype}")
# 🐍 PYTHON NOTE: numpy ("np") is Python's library for fast maths on arrays of numbers.
# vector.shape == (384,) means "a 1-D array of 384 numbers".
# The individual numbers mean nothing to humans. Only distances BETWEEN vectors matter.


# ---------------------------------------------------------------------------
# 2. Cosine similarity, by hand
# ---------------------------------------------------------------------------
trace.step("2. Cosine similarity: how close are two vectors?")


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """1.0 = same direction (same meaning), ~0 = unrelated."""
    # cos(angle) = (a · b) / (|a| × |b|)
    # 🐍 PYTHON NOTE: `a @ b` is the "dot product": multiply element by element, then sum.
    # np.linalg.norm(a) is the vector's length: sqrt(a1² + a2² + ...).
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


# Real customer questions vs. sentences from a help centre.
query = "Can I get my money back?"
candidates = [
    "Refunds are available within 14 days of your first payment.",   # same meaning, no shared words!
    "Get money back on the Pro plan.",                               # shares words, different meaning-ish
    "Our office cat is called Biscuit.",                             # unrelated
    "Pro costs $99 per month and includes 10 seats.",                # related topic (billing)
    "Can I get my data back after cancelling?",                      # very similar WORDS, different need
]

q_vec = list(model.query_embed(query))[0]
# ⚠️ GOTCHA: some models (like bge) embed a QUERY slightly differently from a DOCUMENT.
# fastembed's query_embed() handles that. Mixing them up quietly lowers search quality.
c_vecs = list(model.embed(candidates))

results = [{"id": f"candidate {i}", "text": t, "score": cosine(q_vec, v)}
           for i, (t, v) in enumerate(zip(candidates, c_vecs))]
# 🐍 PYTHON NOTE: zip(a, b) walks two lists side by side: (a[0], b[0]), (a[1], b[1]), ...
# enumerate(...) adds a counter: (0, item0), (1, item1), ...
results.sort(key=lambda r: r["score"], reverse=True)
# 🐍 PYTHON NOTE: `lambda r: r["score"]` is a tiny unnamed function. sort() calls it on each
# item to decide the order. reverse=True → biggest first.
trace.show_retrieval(query, results, label="ranked by cosine similarity", score_name="cosine")

# 💡 WHY: look at the refund sentence. It shares NO words with the query, yet it scores ~0.7,
# far above the unrelated cat sentence: the model learned that "money back" ≈ "refund".
# ⚠️ GOTCHA: but notice it is NOT ranked first. Small embedding models still reward surface
# similarity ("get my ... back"), so "data back" scores almost as high. Embeddings are good
# at finding CANDIDATES, not perfect at ordering them. Lesson 05 fixes the ordering with a
# reranker. Also: scores are relative. 0.7 doesn't mean "70% similar"; compare scores
# for the same query, never against a fixed threshold from another model.


# ---------------------------------------------------------------------------
# 3. Compare with keyword overlap (what lesson 06's search_docs did)
# ---------------------------------------------------------------------------
trace.step("3. The same ranking with keyword overlap")


def keyword_score(q: str, text: str) -> float:
    """Fraction of query words that appear in the text."""
    # 🐍 PYTHON NOTE: set(...) keeps unique items; `a & b` is the set intersection.
    q_words = set(q.lower().replace("?", "").split())
    t_words = set(text.lower().replace(".", "").split())
    return len(q_words & t_words) / len(q_words)


kw = [{"id": f"candidate {i}", "text": t, "score": keyword_score(query, t)}
      for i, t in enumerate(candidates)]
kw.sort(key=lambda r: r["score"], reverse=True)
trace.show_retrieval(query, kw, label="ranked by shared words", score_name="overlap")
# Keyword search isn't useless, though: for exact codes like "ERR-4012" it is often BETTER
# than embeddings. Lesson 05 combines both ("hybrid search").


# ---------------------------------------------------------------------------
# 4. A similarity matrix: every sentence vs every other sentence
# ---------------------------------------------------------------------------
trace.step("4. Similarity matrix")

sentences = [
    "How do I cancel my subscription?",
    "I want to stop paying for Nimbus.",
    "The bot didn't join my Zoom call.",
    "Nimbus Notetaker was missing from the meeting.",
    "What's the weather in Paris?",
]
vecs = np.array(list(model.embed(sentences)))
# Normalise every row to length 1, then one matrix multiply gives ALL pairwise cosines.
unit = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
matrix = unit @ unit.T  # 🐍 .T = transpose (rows become columns)

print("      " + "  ".join(f"  s{i}" for i in range(len(sentences))))
for i, row in enumerate(matrix):
    print(f"s{i}  " + "  ".join(f"{v:5.2f}" for v in row) + f"   {sentences[i]}")
# 💡 WHY: s0/s1 (both mean "cancel", with almost no shared words) score highest in their rows.
# s4 (weather) is far from everything. s2/s3 ("bot didn't join") are close, but s2 also looks
# close to s0. All the support questions sit in one "customer problem" region of the space,
# while the weather question sits far away.

# 🧪 TRY:
#   1. Add a query in another language ("¿Puedo recuperar mi dinero?"). This model is
#      English-only. Then try "intfloat/multilingual-e5-small" (supported by fastembed).
#   2. Embed a single word ("bank") and compare it with "river bank" and "bank account".
#   3. Print np.linalg.norm(vector). bge vectors are already normalised to length ~1. Why
#      does that make cosine similarity == dot product?
