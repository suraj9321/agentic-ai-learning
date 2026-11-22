"""
Lesson 03: Vector stores, by hand and with Chroma.

What you'll learn:
  - A vector store is just: chunks + their vectors + "find the nearest vectors to this one"
  - Build one in ~25 lines with numpy
  - Use a real one (Chroma): persistence, metadata filters, and why you'd want a database
  - Where pgvector, Pinecone, Qdrant etc. fit in

No API key needed.

Run:  uv run python 02-rag/03_vector_store.py
"""

import time
from pathlib import Path

import chromadb
import numpy as np
from dotenv import load_dotenv

from course_utils import trace
from course_utils.rag import CHROMA_DIR, chunk_documents, embed_documents, embed_query, load_documents

load_dotenv(override=True)
DATA = Path(__file__).parent / "data" / "nimbus"

chunks = chunk_documents(load_documents(DATA))
print(f"{len(chunks)} chunks from {DATA.name}/")


# ---------------------------------------------------------------------------
# 1. A vector store by hand
# ---------------------------------------------------------------------------
trace.step("1. A vector store in 25 lines")


class TinyVectorStore:
    """Keeps chunks and their vectors in memory. Search = cosine similarity against all of them."""

    # 🐍 PYTHON NOTE: __init__ runs when you create an object: store = TinyVectorStore().
    # `self` is the object itself; self.chunks is data stored ON the object.
    def __init__(self):
        self.chunks: list[dict] = []
        self.vectors = np.zeros((0, 384), dtype=np.float32)  # an empty table with 384 columns

    def add(self, chunks: list[dict]) -> None:
        vecs = embed_documents([c["text"] for c in chunks])
        vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)  # normalise once, at write time
        self.chunks.extend(chunks)
        self.vectors = np.vstack([self.vectors, vecs])  # 🐍 vstack = stack rows on top of each other

    def search(self, query: str, k: int = 3, where: dict | None = None) -> list[dict]:
        q = embed_query(query)
        q = q / np.linalg.norm(q)
        scores = self.vectors @ q  # one matrix multiply = cosine similarity with EVERY chunk
        # 🐍 PYTHON NOTE: np.argsort gives the indices that would sort the array (ascending);
        # [::-1] reverses it, so the best match comes first.
        results = []
        for i in np.argsort(scores)[::-1]:
            chunk = self.chunks[i]
            # Metadata filter: skip chunks whose fields don't match, e.g. {"source": "pricing.md"}
            if where and any(chunk.get(key) != value for key, value in where.items()):
                continue
            results.append({**chunk, "score": float(scores[i])})
            if len(results) == k:
                break
        return results


t0 = time.perf_counter()
store = TinyVectorStore()
store.add(chunks)
print(f"Embedded and stored {len(store.chunks)} chunks in {time.perf_counter() - t0:.2f}s. "
      f"Vectors table shape: {store.vectors.shape}")

for question in ["Can I get my money back?", "the bot never showed up in my call", "ERR-4012"]:
    trace.show_retrieval(question, store.search(question, k=3), label="TinyVectorStore")

# 💡 WHY this is "brute force": every search compares the query with EVERY vector. That's fine
# for 10,000 chunks (a few ms). At 10 million it's too slow, so real vector databases use an
# *approximate nearest neighbour* (ANN) index such as HNSW: a graph that finds "almost
# certainly the closest" vectors without checking them all. Interviewers love this question.


# ---------------------------------------------------------------------------
# 2. Metadata filters
# ---------------------------------------------------------------------------
trace.step("2. Metadata filters")

q = "how much does Pro cost?"
trace.show_retrieval(q, store.search(q, k=3), label="no filter")
# The 2024 FAQ has OLD prices ($79). If it ranks high, the LLM might answer with stale facts.
recent = [c for c in chunks if c.get("updated", "") >= "2025-01-01"]
# 🐍 PYTHON NOTE: dates written as "YYYY-MM-DD" strings sort correctly as plain text.
print(f"Chunks updated since 2025: {len(recent)} of {len(chunks)}")
fresh = TinyVectorStore()
fresh.add(recent)
trace.show_retrieval(q, fresh.search(q, k=3), label="only docs updated since 2025")
# 💡 WHY: filters are how you do multi-tenancy (where={"customer_id": 42}: one customer must
# NEVER see another's documents), permissions, freshness, language, product... Filters are
# exact rules you control, unlike similarity.


# ---------------------------------------------------------------------------
# 3. The same with Chroma, a real vector database
# ---------------------------------------------------------------------------
trace.step("3. Chroma: a vector database")

# PersistentClient saves to disk, so the index survives between runs (try running twice:
# the second run skips re-embedding). Stored in .cache/chroma/ (git-ignored).
client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = client.get_or_create_collection(
    name="nimbus-lesson03",
    # Use cosine distance (Chroma's default is squared L2 distance).
    configuration={"hnsw": {"space": "cosine"}},
)

if collection.count() == 0:
    print("Empty collection → embedding and adding chunks...")
    collection.add(
        ids=[c["id"] for c in chunks],                                  # must be unique
        documents=[c["text"] for c in chunks],
        embeddings=embed_documents([c["text"] for c in chunks]).tolist(),  # we embed ourselves
        # ⚠️ GOTCHA: Chroma metadata values must be str/int/float/bool. None is not allowed.
        metadatas=[{"source": c["source"], "updated": c.get("updated", ""), "heading": c["heading"]}
                   for c in chunks],
    )
else:
    print(f"Collection already has {collection.count()} chunks (loaded from disk, no re-embedding).")

res = collection.query(
    query_embeddings=[embed_query("Can I get my money back?").tolist()],
    n_results=3,
    where={"source": {"$ne": "faq_2024.md"}},  # filter: source is NOT the archived FAQ
)
# Chroma returns lists of lists (one inner list per query, since you can send several queries).
hits = [{"id": i, "text": d, "score": 1 - dist}  # cosine DISTANCE = 1 - cosine similarity
        for i, d, dist in zip(res["ids"][0], res["documents"][0], res["distances"][0])]
trace.show_retrieval("Can I get my money back?", hits, label="Chroma, excluding faq_2024.md",
                     score_name="cosine")
print("Raw Chroma result keys:", list(res.keys()))

# 💡 WHY a database instead of TinyVectorStore? Persistence, ANN indexes, filters on
# millions of rows, concurrent writes, deletes/updates by id, backups.
# Which one in production?
#   - pgvector (a Postgres extension): your vectors live next to your normal data, with SQL
#     filters and transactions. The default choice for most startups: one less system to run.
#   - Chroma / LanceDB: great locally and for prototypes.
#   - Pinecone / Qdrant / Weaviate / Turbopuffer: managed, scale to billions of vectors.

# 🧪 TRY:
#   1. Search store for "ERR-4012" and "error 4012". Does the vector search find the
#      troubleshooting chunk for both? (Lesson 05 shows why exact codes are hard for embeddings.)
#   2. Change a sentence in pricing.md and re-run. Chroma still has the OLD text. Why?
#      Fix it: delete the collection (client.delete_collection("nimbus-lesson03")) or use
#      collection.upsert(). Keeping an index in sync with changing documents is a real job.
#   3. Time store.search() over 1,000 copies of the chunks (store.add(chunks * 40)).
