"""
course_utils.rag: the RAG building blocks you write by hand in Phase 2, packaged for reuse.

    from course_utils import rag

    docs   = rag.load_documents("02-rag/data/nimbus")      # files → list of {"text", "source", ...}
    chunks = rag.chunk_documents(docs)                       # documents → smaller pieces
    vecs   = rag.embed_documents([c["text"] for c in chunks])  # text → vectors (numbers)
    q      = rag.embed_query("can I get a refund?")

Lessons 01–03 build each of these step by step. Later lessons and projects import them
from here so the code stays short. Read the lesson first, then come back and compare.

Embeddings run LOCALLY with fastembed (no API key, free). The model (~70 MB) downloads
once into .cache/fastembed/ the first time you use it.
"""

import os
import re
from pathlib import Path

# Quieter Hugging Face downloads (the embedding model is fetched from there once).
os.environ.setdefault("HF_HUB_VERBOSITY", "error")

import numpy as np  # noqa: E402  (imported after setting env vars on purpose)

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / ".cache" / "fastembed"
CHROMA_DIR = REPO_ROOT / ".cache" / "chroma"

# A small, fast, good-quality English embedding model: 384 numbers per text.
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
# A cross-encoder that scores (query, passage) pairs directly. Used for reranking.
RERANK_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"

_embedder = None
_reranker = None


# =====================================================================================
# Loading
# =====================================================================================
def _parse_front_matter(text: str) -> tuple[dict, str]:
    """Split '---\\nkey: value\\n---\\nbody' into ({key: value}, body)."""
    meta = {}
    if text.startswith("---"):
        _, header, body = text.split("---", 2)
        for line in header.strip().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                meta[key.strip()] = value.strip()
        return meta, body.strip()
    return meta, text


def load_documents(folder: str | Path) -> list[dict]:
    """Read every .md / .txt / .pdf file in a folder.

    Returns one dict per document (per PAGE for PDFs):
        {"text": ..., "source": "pricing.md", "page": None, "title": ..., "updated": ...}
    """
    docs = []
    for path in sorted(Path(folder).glob("*")):
        suffix = path.suffix.lower()
        if suffix in (".md", ".txt"):
            meta, body = _parse_front_matter(path.read_text(encoding="utf-8"))
            docs.append({"text": body, "source": path.name, "page": None, **meta})
        elif suffix == ".pdf":
            from pypdf import PdfReader  # imported only when a PDF is actually present

            reader = PdfReader(path)
            for page_no, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                if text:  # scanned PDFs have no text layer: they'd need OCR
                    docs.append({"text": text, "source": path.name, "page": page_no,
                                 "title": path.stem})
    return docs


# =====================================================================================
# Chunking (lesson 02 explains every line of this)
# =====================================================================================
def _split(text: str, max_chars: int, separators: list[str]) -> list[str]:
    """Recursively split text on the 'biggest' separator that makes pieces small enough."""
    if len(text) <= max_chars:
        return [text]
    if not separators:  # nothing left to split on: hard cut
        return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]
    sep, rest = separators[0], separators[1:]
    pieces, current = [], ""
    for part in text.split(sep):
        candidate = f"{current}{sep}{part}" if current else part
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                pieces.append(current)
            # The part alone may still be too big: split it with the next separator.
            if len(part) > max_chars:
                pieces.extend(_split(part, max_chars, rest))
                current = ""
            else:
                current = part
    if current:
        pieces.append(current)
    return pieces


def chunk_text(text: str, max_chars: int = 600, overlap: int = 100, min_chars: int = 80) -> list[str]:
    """Split on headings → paragraphs → lines → sentences → words, merge tiny pieces, add overlap."""
    seps = ["\n## ", "\n\n", "\n", ". ", " "]
    pieces = [p.strip() for p in _split(text, max_chars, seps) if p.strip()]
    # Merge tiny pieces (e.g. a lone "# Title" heading) into the next piece: a chunk with no
    # real content only pollutes search results.
    merged = []
    for p in pieces:
        if merged and len(merged[-1]) < min_chars:
            merged[-1] = f"{merged[-1]}\n\n{p}"
        else:
            merged.append(p)
    pieces = merged
    if overlap <= 0:
        return pieces
    # Overlap: start each chunk with the tail of the previous one, so a fact that sits on
    # a boundary still appears whole in at least one chunk.
    out = [pieces[0]] if pieces else []
    for prev, cur in zip(pieces, pieces[1:]):
        tail = prev[-overlap:]
        tail = tail[tail.find(" ") + 1:] if " " in tail else tail  # don't start mid-word
        out.append(f"…{tail}\n{cur}")
    return out


def _heading_for(chunk: str, full_text: str) -> str:
    """The nearest markdown heading above where this chunk starts (for context)."""
    start = full_text.find(chunk.lstrip("…")[:80])
    headings = [m for m in re.finditer(r"^#+ (.+)$", full_text, flags=re.M) if m.start() <= max(start, 0)]
    return headings[-1].group(1) if headings else ""


def chunk_documents(docs: list[dict], max_chars: int = 600, overlap: int = 100) -> list[dict]:
    """Chunk every document. Each chunk keeps its document's metadata plus an id."""
    chunks = []
    for doc in docs:
        for i, piece in enumerate(chunk_text(doc["text"], max_chars, overlap)):
            page = f"-p{doc['page']}" if doc.get("page") else ""
            chunks.append({
                **{k: v for k, v in doc.items() if k != "text"},
                "id": f"{doc['source']}{page}#{i}",
                "chunk": i,
                "heading": _heading_for(piece, doc["text"]),
                "text": piece,
            })
    return chunks


# =====================================================================================
# Embeddings
# =====================================================================================
def _get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding

        _embedder = TextEmbedding(EMBED_MODEL, cache_dir=str(CACHE_DIR))
    return _embedder


def embed_documents(texts: list[str]) -> np.ndarray:
    """Texts → a 2-D array with one row (vector) per text, shape (len(texts), 384)."""
    return np.array(list(_get_embedder().embed(texts)))


def embed_query(text: str) -> np.ndarray:
    """A search query → one vector. (bge models embed queries slightly differently.)"""
    return np.array(next(iter(_get_embedder().query_embed(text))))


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Cosine similarity between vector a and each row of b (or vector b)."""
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b, axis=-1, keepdims=True)
    return b @ a


class VectorIndex:
    """Lesson 03's TinyVectorStore: chunks + normalised vectors + brute-force cosine search."""

    def __init__(self, chunks: list[dict] | None = None):
        self.chunks: list[dict] = []
        self.vectors = np.zeros((0, 384), dtype=np.float32)
        if chunks:
            self.add(chunks)

    def add(self, chunks: list[dict]) -> None:
        vecs = embed_documents([c["text"] for c in chunks])
        self.vectors = np.vstack([self.vectors, vecs / np.linalg.norm(vecs, axis=1, keepdims=True)])
        self.chunks.extend(chunks)

    def search(self, query: str, k: int = 4, where: dict | None = None) -> list[dict]:
        q = embed_query(query)
        scores = self.vectors @ (q / np.linalg.norm(q))
        results = []
        for i in np.argsort(scores)[::-1]:
            chunk = self.chunks[i]
            if where and any(chunk.get(key) != value for key, value in where.items()):
                continue
            results.append({**chunk, "score": float(scores[i])})
            if len(results) == k:
                break
        return results


def format_context(chunks: list[dict]) -> str:
    """Retrieved chunks → XML-tagged text to paste into a prompt (lesson 04)."""
    parts = []
    for c in chunks:
        attrs = f'id="{c["id"]}" source="{c["source"]}"'
        if c.get("page"):
            attrs += f' page="{c["page"]}"'
        if c.get("updated"):
            attrs += f' updated="{c["updated"]}"'
        parts.append(f"<document {attrs}>\n{c['text']}\n</document>")
    return "<documents>\n" + "\n".join(parts) + "\n</documents>"


# =====================================================================================
# Reranking
# =====================================================================================
def rerank_scores(query: str, texts: list[str]) -> list[float]:
    """Score each text for relevance to the query with a cross-encoder (higher = better)."""
    global _reranker
    if _reranker is None:
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        _reranker = TextCrossEncoder(RERANK_MODEL, cache_dir=str(CACHE_DIR))
    return [float(s) for s in _reranker.rerank(query, texts)]


# =====================================================================================
# Hybrid search + rerank (lesson 05, packaged)
# =====================================================================================
def tokenize(text: str) -> list[str]:
    """Lowercase words; keeps codes like 'err-4012' and '$99' together (for BM25)."""
    return re.findall(r"[a-z0-9$]+(?:[-.][a-z0-9]+)*", text.lower())


def rrf(result_lists: list[list[dict]], k: int = 60) -> list[dict]:
    """Reciprocal Rank Fusion: score(chunk) = sum of 1 / (k + rank) over the lists."""
    fused: dict[str, dict] = {}
    for results in result_lists:
        for rank, r in enumerate(results, start=1):
            fused.setdefault(r["id"], {**r, "score": 0.0})["score"] += 1 / (k + rank)
    return sorted(fused.values(), key=lambda r: r["score"], reverse=True)


class HybridRetriever:
    """BM25 + vectors fused with RRF, then (optionally) a cross-encoder rerank."""

    def __init__(self, chunks: list[dict]):
        from rank_bm25 import BM25Okapi

        self.chunks = chunks
        self.vectors = VectorIndex(chunks)
        self.bm25 = BM25Okapi([tokenize(c["text"]) for c in chunks])

    def _bm25(self, query: str, k: int, where: dict | None) -> list[dict]:
        scores = self.bm25.get_scores(tokenize(query))
        out = []
        for i in sorted(range(len(self.chunks)), key=lambda i: scores[i], reverse=True):
            c = self.chunks[i]
            if where and any(c.get(key) != value for key, value in where.items()):
                continue
            out.append({**c, "score": float(scores[i])})
            if len(out) == k:
                break
        return out

    def search(self, query: str, k: int = 4, rerank: bool = True, candidates: int = 12,
               where: dict | None = None) -> list[dict]:
        pool = rrf([self._bm25(query, candidates, where),
                    self.vectors.search(query, candidates, where)])[:candidates]
        if not rerank:
            return pool[:k]
        for c, score in zip(pool, rerank_scores(query, [c["text"] for c in pool])):
            c["score"] = score
        return sorted(pool, key=lambda c: c["score"], reverse=True)[:k]


# =====================================================================================
# LangChain adapter (used in Phase 3)
# =====================================================================================
def langchain_embeddings():
    """Our local embedder wrapped in LangChain's Embeddings interface (see Phase 3 lesson 04)."""
    from langchain_core.embeddings import Embeddings

    class LocalEmbeddings(Embeddings):
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return embed_documents(texts).tolist()

        def embed_query(self, text: str) -> list[float]:
            return embed_query(text).tolist()

    return LocalEmbeddings()
