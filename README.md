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
- ~1.5h: read the lesson README and official docs
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
