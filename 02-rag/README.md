# Phase 2: RAG, giving agents knowledge (Week 2)

**Goal:** by Friday you've built retrieval by hand (embeddings → chunks → vector search →
hybrid → rerank), you can **measure** it, and you've shipped a "chat with your PDFs" app with citations.

## Why RAG?
An LLM only knows its training data. It doesn't know your company's docs, your customer's
contracts, or anything newer than its cutoff. **RAG (Retrieval-Augmented Generation)** fixes that
with no training at all:

```
question ──► RETRIEVE relevant chunks ──► AUGMENT: paste them into the prompt ──► GENERATE the answer
```

You already know the G part (Phase 1). This week is mostly about the **R**: most bad RAG answers
happen because the right chunk was never retrieved.

**RAG vs fine-tuning** (a classic interview question): RAG gives the model *facts* that can
change daily and be cited. Fine-tuning changes *behaviour/style* and is slow and expensive to update.
For "answer from our docs", RAG is almost always the answer.

## No new API key needed
Embeddings and reranking run **locally** with [fastembed](https://github.com/qdrant/fastembed)
(small ONNX models, CPU only). The first run downloads ~150 MB of models into `.cache/` (git-ignored).
In production you'd often use a hosted embedding API instead: Voyage AI (Anthropic's recommended
partner), OpenAI, or Cohere.

## Lessons (run each with `uv run python 02-rag/<file>`)

| # | File | You learn | API calls? |
|---|---|---|---|
| 01 | `01_embeddings.py` | Vectors, cosine similarity, semantic vs keyword search | no |
| 02 | `02_chunking.py` | Loading docs + metadata, fixed vs recursive chunking, overlap | no |
| 03 | `03_vector_store.py` | A vector store in 25 lines, metadata filters, Chroma | no |
| 04 | `04_rag_by_hand.py` | **The full RAG loop**, grounded prompts, "I don't know", citations | yes |
| 05 | `05_better_retrieval.py` | BM25, hybrid search (RRF), reranking, query rewriting, **retrieval eval** | 1 call |
| 06 | `06_agentic_rag.py` | Retrieval as a **tool** in your Phase 1 agent loop | yes |

Then the mini-project: **`project/`, chat with your documents.**

The sample data in `data/nimbus/` is the help centre of *Nimbus*, a made-up AI meeting-notes
startup. It has deliberate traps: an **outdated** 2024 FAQ that contradicts newer docs, exact
error codes (`ERR-4012`), and facts split across documents.

### New trace panels
- ✂️ **chunks**: how documents were split (id, size, start … end; `⏎` = line break)
- 🔎 **RETRIEVAL**: what the search returned, ranked, with scores
- 🔢 **embedding**: the first numbers of a vector

## Where the code lives
Lessons build each piece by hand. `course_utils/rag.py` then holds the same code packaged
(`load_documents`, `chunk_documents`, `VectorIndex`, `HybridRetriever`, `format_context`) so later
lessons stay short. **Read `course_utils/rag.py` after lesson 05**: you should understand every line.

## Suggested week
| Day | Do |
|---|---|
| Mon | Lessons 01–02. Play with the similarity matrix and chunk sizes. |
| Tue | Lesson 03 + read `course_utils/rag.py` (`_split`, `VectorIndex`) |
| Wed | Lesson 04. Break the prompt on purpose and watch hallucinations appear. |
| Thu | Lesson 05. **Spend time on the eval**: add questions, change chunk sizes, compare. |
| Fri | Lesson 06 + start the project with your own PDFs |
| Sat | Finish the project, write `notes/interview-qa.md` answers for Phase 2 |

## Key concepts cheat sheet
- **Embedding**: text → vector (e.g. 384 numbers). Similar meaning → nearby vectors.
- **Cosine similarity**: the angle between two vectors. Compare scores for the *same* query only.
- **Chunking**: split docs into ~500–1,000-character pieces, respecting structure, with 10–20% overlap.
- **Metadata**: source, page, date, tenant… → citations and **filters** (exact rules, e.g. permissions).
- **Vector DB**: stores vectors + ANN index (HNSW) for fast approximate search. Startups: **pgvector** first.
- **BM25**: keyword ranking that weights rare words. Wins on codes, names, and exact terms.
- **Hybrid + RRF**: run both searches and fuse them by *rank*: `Σ 1/(60 + rank)`.
- **Reranker (cross-encoder)**: reads query + chunk together and scores them. Accurate but slow → only on the top ~20.
- **Query rewriting**: turn follow-ups and messy messages into standalone search queries.
- **Agentic RAG**: retrieval is a tool; the model decides when and what to search.
- **Retrieval eval**: hit@k (was the right doc in the top k?) and MRR (how high was it?).

**Failure modes to name in interviews:** the right chunk was never retrieved · a fact split across
chunks · stale or contradictory docs · too many irrelevant chunks (distraction and cost) · the model
ignores the context or invents citations · data leaking between tenants (a missing filter).

## Official docs to skim alongside
- Anthropic, Contextual Retrieval (a must-read): https://www.anthropic.com/news/contextual-retrieval
- Embeddings guide: https://platform.claude.com/docs/en/build-with-claude/embeddings
- Citations feature of the Claude API (built-in alternative to our prompt-based citations): https://platform.claude.com/docs/en/build-with-claude/citations
- Chroma docs: https://docs.trychroma.com · pgvector: https://github.com/pgvector/pgvector

## 📺 Recommended videos & resources (by lesson)

| Lesson | Resource | Notes |
|---|---|---|
| All | ⭐ [RAG From Scratch](https://www.youtube.com/playlist?list=PLfaIDFEXuae2LXbO1_PKyVJiQ23ZztA0x) (LangChain, video playlist) | Short videos (~5–10 min each) on indexing, query rewriting, routing, reranking; watch alongside lessons 03–06 |
| All | [What is Retrieval-Augmented Generation (RAG)?](https://www.youtube.com/watch?v=T-D1OfcDW1M) (IBM Technology, video) | A 6-minute "why RAG" before you start |
| 01 | ⭐ [What are embeddings?](https://vickiboykis.com/what_are_embeddings/) (Vicki Boykis) | The best deep dive on embeddings for engineers; read the first chapters this week |
| 01 | [Transformers, the tech behind LLMs](https://www.youtube.com/watch?v=wjZofJX0v4M) (3Blue1Brown, video) | The first ~10 minutes show embeddings as directions in space |
| 02 | ⭐ [The 5 Levels of Text Splitting](https://www.youtube.com/watch?v=8OJC21T2SL4) (Greg Kamradt, video) | Character → recursive → document-aware → semantic → agentic chunking |
| 02 | [Chunking strategies](https://www.pinecone.io/learn/chunking-strategies/) (Pinecone) | The same ideas in a reading version, with trade-offs |
| 05 | [Rerankers and two-stage retrieval](https://www.pinecone.io/learn/series/rag/rerankers/) (Pinecone) | Why bi-encoder + cross-encoder beats either alone |
| 05 | [Retrieve & Re-Rank](https://www.sbert.net/examples/applications/retrieve_rerank/README.html) (Sentence Transformers) | A short, clear diagram of the same pipeline |
| 05 | [Reciprocal Rank Fusion paper](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) (Cormack et al.) | Two pages; the formula you implemented in hybrid search |
| 04–06 | [Patterns for Building LLM-based Systems](https://eugeneyan.com/writing/llm-patterns/) (Eugene Yan) | RAG, evals, guardrails and caching in one long read; great interview prep |
| Going further | [Retrieval Augmented Generation (RAG)](https://www.coursera.org/learn/retrieval-augmented-generation-rag) (DeepLearning.AI on Coursera) | A full course (several weeks) if you want to go deeper than this phase |
