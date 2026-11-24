# Agentic AI Engineering — from basics to LangGraph in production

A hands-on, 8-week course (full-time pace) built for two goals:
1. **Getting hired as an AI engineer**: portfolio projects plus a solid grasp of how agents actually work.
2. **Building your own AI product**: shipping, keeping costs down, and reliability.

**How the course works:** build each idea **by hand first**, then use a framework for it.
You'll write an agent loop in plain Python before touching LangChain, so the frameworks never feel like magic.

---

## Quick start

```bash
cd agentic-ai-learning-basics-to-langgraph-prod
cp .env.example .env              # then paste your ANTHROPIC_API_KEY into .env
uv sync                           # installs everything into .venv
uv run python 00-setup/check_setup.py
```

Run any lesson with `uv run python <path-to-file>`, e.g.
`uv run python 01-llm-basics/01_first_call.py`

## How to read the code

Every lesson file is heavily commented. Watch for these markers:

| Marker | Meaning |
|---|---|
| `# 🐍 PYTHON NOTE:` | A Python concept explained the first time it appears |
| `# 💡 WHY:` | The design reason behind the code |
| `# ⚠️ GOTCHA:` | A common mistake (often asked about in interviews) |
| `# 🧪 TRY:` | A small change to make and observe |

## Tracing: see every step
Every lesson uses `course_utils/trace.py` to print what happens at each step:
- 📤 **REQUEST**: everything sent to the model: system prompt, tools offered, and every message,
  with **NEW** marking the ones added since the last call (older ones are dimmed, but still re-sent)
- 📥 **RESPONSE**: every content block (text / tool_use / thinking ...), `stop_reason` and its meaning,
  tokens, cost and time
- ⚙️ **YOUR CODE RUNS THE TOOL**: which function ran, the arguments the model chose, and the result

Phase 2 adds ✂️ **chunks** and 🔎 **RETRIEVAL** panels. Phase 3 shows the same panels for LangChain runs
via `course_utils/lc_trace.py`, a LangChain callback handler (pass `config={"callbacks": [Tracer()]}`).

Control it from `.env` with no code changes: `TRACE=full` (default) · `TRACE=brief` (one line per call) · `TRACE=off`,
and `TRACE_MAX_CHARS=500` to cut long texts (`0` = show everything).

## Daily rhythm (full-time)
- ~1.5h: read the lesson README and official docs, and watch the ⭐ videos in its "📺 Recommended videos & resources" section
- ~4h: run the code, **break it**, change it, do the exercises
- ~1h: build or extend the mini-project
- ~30m: write notes in `notes/` in your own words, as answers to interview questions

---

## Roadmap & progress

Tick boxes as you go (`[ ]` → `[x]`).

### Phase 0: Setup & mental model (Day 1) → `00-setup/`
- [x] Environment working (`check_setup.py` passes)
- [x] Read "How LLMs work for engineers"

### Phase 1: LLM APIs from scratch, no frameworks (Week 1) → `01-llm-basics/`
- [x] 01 First call: messages, roles, system prompts, tokens, cost
- [x] 02 Conversations & streaming
- [x] 03 Prompt engineering
- [x] 04 Structured output with Pydantic
- [x] 05 Tool calling by hand
- [x] 06 Agent loop from scratch (ReAct)
- [x] 07 Async & parallel calls
- [x] 🛠 Mini-project: CLI research assistant

### Phase 2: RAG (Week 2) → `02-rag/`
- [ ] 01 Embeddings & cosine similarity
- [ ] 02 Loading & chunking documents
- [ ] 03 Vector stores: by hand, then Chroma
- [ ] 04 RAG by hand: grounded prompts, "I don't know", citations
- [ ] 05 Better retrieval: BM25, hybrid (RRF), reranking, query rewriting + retrieval eval
- [ ] 06 Agentic RAG: retrieval as a tool
- [ ] 🛠 Mini-project: chat with your documents (PDFs) with citations

### Phase 3: LangChain + LangSmith (Week 3) → `03-langchain/`
- [ ] LangSmith account + tracing on (`.env`)
- [ ] 01 Chat models & messages (`init_chat_model`, invoke/stream/batch)
- [ ] 02 Prompt templates, LCEL, structured output
- [ ] 03 Tools & `create_agent` (by hand with `bind_tools` first), memory
- [ ] 04 RAG with LangChain (splitters, vector stores, retrievers, custom retriever)
- [ ] 05 LangSmith: tags/metadata, `@traceable`, feedback, 🐛 bug hunt
- [ ] 06 Middleware: limits, model routing, guardrails, PII, summarisation
- [ ] 🛠 Mini-project: research agent rebuilt with LangChain + your documents

### Phase 4: LangGraph (Weeks 4–5) → `04-langgraph/`
- [ ] State, nodes, edges, reducers, conditional routing
- [ ] Persistence / checkpointers, short- and long-term memory
- [ ] Human-in-the-loop (`interrupt`), streaming, time travel
- [ ] Patterns: router, chaining, map-reduce, reflection, plan-and-execute
- [ ] Multi-agent: supervisor, hierarchical, handoffs, subgraphs
- [ ] 🛠 Multi-agent "startup research analyst"

### Phase 5: Observability & evals (Week 6a) → `05-observability-evals/`
- [ ] LangSmith datasets, experiments, LLM-as-judge, online monitoring
- [ ] Agent evals: final answer, trajectory, single step
- [ ] Langfuse / Arize Phoenix / OpenTelemetry overview
- [ ] 🛠 Eval suite for the Phase 4 project

### Phase 6: Ecosystem (Week 6b) → `06-ecosystem/`
- [ ] MCP: build a server, connect it to an agent
- [ ] Guardrails & security (prompt injection, tool permissions, PII)
- [ ] Reliability: retries, fallbacks, caching, rate limits
- [ ] Tour: OpenAI Agents SDK, Claude Agent SDK, Pydantic AI, CrewAI

### Phase 7: Production (Week 7) → `07-production/`
- [ ] FastAPI + streaming (SSE), simple frontend
- [ ] Postgres checkpointer, Docker, deployment
- [ ] Cost engineering: model routing, prompt caching, token budgets
- [ ] LLM system design practice

### Phase 8: Capstone (Week 8) → `08-capstone/`
- [ ] Idea picked (keep `notes/ideas.md` growing until then!)
- [ ] LangGraph agent + RAG + tools/MCP + human-in-the-loop
- [ ] Tracing + eval suite with a score
- [ ] Deployed, README with architecture diagram, 2-min demo video

---

Phases 4–8 are written when you reach them, so each one fits your pace and questions
and uses the latest LangChain/LangGraph APIs (they change often).

---

## 📺 All recommended videos & resources

Everything from the phase READMEs in one place. ⭐ = start here. Each phase README says which lesson each one goes with.

### Phase 0: How LLMs work
- ⭐ 🎥 [Large Language Models explained briefly](https://www.youtube.com/watch?v=LPZh9BOjkQs) (3Blue1Brown, 8 min)
- ⭐ 🎥 [Intro to Large Language Models](https://www.youtube.com/watch?v=zjkBMFhNj_g) (Andrej Karpathy, 1 h)
- 🎥 [Deep Dive into LLMs like ChatGPT](https://www.youtube.com/watch?v=7xTGNNLPyMI) (Andrej Karpathy, 3.5 h)
- 🎥 [Transformers, the tech behind LLMs](https://www.youtube.com/watch?v=wjZofJX0v4M) and [Attention, step-by-step](https://www.youtube.com/watch?v=eMlx5fFNoYc) (3Blue1Brown)
- 🎥 [Let's build the GPT Tokenizer](https://www.youtube.com/watch?v=zduSFxRajkE) (Andrej Karpathy, 2 h)
- 🔧 [Tiktokenizer](https://tiktokenizer.vercel.app): see how text splits into tokens
- 📖 [The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/) (Jay Alammar)

### Phase 1: LLM APIs from scratch
- ⭐ 🎓 [Building with the Claude API](https://anthropic.skilljar.com/claude-with-the-anthropic-api) (Anthropic Academy, free video course)
- ⭐ 📓 [Prompt engineering interactive tutorial](https://github.com/anthropics/prompt-eng-interactive-tutorial) (Anthropic)
- ⭐ 🎥 [How We Build Effective Agents](https://www.youtube.com/watch?v=D7_ipDqhtwk) (Barry Zhang, Anthropic)
- 📓 [anthropics/courses](https://github.com/anthropics/courses): API fundamentals, prompting and tool use notebooks
- 📖 [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) (Anthropic)
- 📖 [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) (Anthropic)
- 📖 [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (Anthropic)
- 📖 [ReAct paper](https://arxiv.org/abs/2210.03629) (Yao et al.)
- 📖 [LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/) (Lilian Weng)
- 📖 [Pydantic: Models](https://docs.pydantic.dev/latest/concepts/models/) · [Python asyncio: Coroutines and Tasks](https://docs.python.org/3/library/asyncio-task.html)
- 📓 [Claude cookbooks](https://github.com/anthropics/claude-cookbooks)

### Phase 2: RAG
- ⭐ 🎥 [RAG From Scratch](https://www.youtube.com/playlist?list=PLfaIDFEXuae2LXbO1_PKyVJiQ23ZztA0x) (LangChain, playlist)
- ⭐ 📖 [What are embeddings?](https://vickiboykis.com/what_are_embeddings/) (Vicki Boykis)
- ⭐ 🎥 [The 5 Levels of Text Splitting](https://www.youtube.com/watch?v=8OJC21T2SL4) (Greg Kamradt)
- ⭐ 📖 [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) (Anthropic)
- 🎥 [What is Retrieval-Augmented Generation (RAG)?](https://www.youtube.com/watch?v=T-D1OfcDW1M) (IBM Technology, 6 min)
- 📖 [Chunking strategies](https://www.pinecone.io/learn/chunking-strategies/) · [Rerankers and two-stage retrieval](https://www.pinecone.io/learn/series/rag/rerankers/) (Pinecone)
- 📖 [Retrieve & Re-Rank](https://www.sbert.net/examples/applications/retrieve_rerank/README.html) (Sentence Transformers)
- 📖 [Reciprocal Rank Fusion paper](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) (Cormack et al.)
- 📖 [Patterns for Building LLM-based Systems](https://eugeneyan.com/writing/llm-patterns/) (Eugene Yan)
- 🎓 [Retrieval Augmented Generation (RAG)](https://www.coursera.org/learn/retrieval-augmented-generation-rag) (DeepLearning.AI on Coursera, going further)

### Phase 3: LangChain + LangSmith
- ⭐ 🎓 [LangChain Essentials (Python)](https://academy.langchain.com/courses/langchain-essentials-python) (LangChain Academy, free)
- ⭐ 📖 [LangSmith observability quickstart](https://docs.langchain.com/langsmith/observability-quickstart)
- 🎓 [Intro to Building Agents](https://academy.langchain.com/bundles/intro-to-building-agents) (LangChain Academy, free)
- 📖 [LangChain v1 release notes](https://docs.langchain.com/oss/python/releases/langchain-v1): check this before following older tutorials

🎥 video · 🎓 course · 📓 notebooks/tutorial · 📖 reading · 🔧 tool. More resources get added here as Phases 4–8 are written.
