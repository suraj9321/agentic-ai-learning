# Phase 3: LangChain + LangSmith (Week 3)

**Goal:** by Friday you can build anything from Phases 1–2 with LangChain in a fraction of the code,
you know exactly what each abstraction does underneath, and every run is visible in LangSmith.

## What LangChain is (2026, v1.x)
- **`langchain-core`**: the interfaces: messages, `Runnable` (invoke/stream/batch), prompts, tools,
  retrievers, embeddings, vector stores, callbacks.
- **`langchain`**: `init_chat_model`, **`create_agent`** (a prebuilt agent loop) and **middleware**.
- **Integration packages**: `langchain-anthropic`, `langchain-openai`, `langchain-chroma`, ... one per provider.
- **`langgraph`**: the runtime underneath `create_agent`. You'll use it directly in Phase 4.
- **LangSmith**: tracing, evals, and monitoring. It works with or without LangChain.

The pitch: **swappable components with common interfaces**, plus a fast path to agents.
The cost: another layer of abstraction. That's why you built everything by hand first. Each lesson
starts with a "Phase 1/2 equivalent" so you can see what the abstraction replaces.

## Setup: LangSmith (do this on Monday)
1. Sign up free at https://smith.langchain.com → Settings → API Keys → create a key.
2. In `.env`, uncomment and fill in:
   ```
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=lsv2_...
   LANGSMITH_PROJECT=agentic-ai-learning
   ```
3. Run any lesson and open the project in LangSmith. That's it: LangChain sends traces automatically.

Every lesson also prints the usual 📤/📥/⚙️/🔎 panels locally, using `course_utils/lc_trace.py`.
It's a LangChain **callback handler**, the same mechanism LangSmith uses. Read it in lesson 05.

## Lessons (run each with `uv run python 03-langchain/<file>`)

| # | File | You learn | Replaces (by hand) |
|---|---|---|---|
| 01 | `01_chat_models.py` | `init_chat_model`, messages, AIMessage, invoke/stream/batch | Phase 1 lessons 01, 02, 07 |
| 02 | `02_prompts_and_lcel.py` | Prompt templates, the `\|` pipe, Runnables, `with_structured_output` | Phase 1 lessons 03, 04 |
| 03 | `03_tools_and_agents.py` | `@tool`, `bind_tools`, **`create_agent`**, streaming steps, memory | Phase 1 lessons 05, 06 |
| 04 | `04_rag_with_langchain.py` | Documents, splitters, vector stores, retrievers, RAG chains, custom retriever | Phase 2 |
| 05 | `05_langsmith.py` | **LangSmith**: tags/metadata, `@traceable`, `wrap_anthropic`, feedback, 🐛 bug hunt | `course_utils/trace.py` |
| 06 | `06_middleware.py` | Call limits, model routing, tool guardrails, PII redaction, summarisation | the extras you'd hand-code |

Then the mini-project: **`project/`, the Phase 1 research agent, rebuilt with LangChain plus your documents.**

Python you'll pick up: operator overloading (`__or__`), decorators (and decorators with arguments),
inheritance and interfaces, Pydantic fields.

## Suggested week
| Day | Do |
|---|---|
| Mon | LangSmith setup + lessons 01–02 |
| Tue | Lesson 03. Compare section 2 (by hand) with section 3 (`create_agent`) line by line. |
| Wed | Lesson 04 + read the source of `RecursiveCharacterTextSplitter` (Ctrl/Cmd-click it in VS Code) |
| Thu | Lesson 05 in LangSmith: do the bug hunt **only** from the trace. Then lesson 06. |
| Fri | Project: port + compare |
| Sat | Exercises + `notes/interview-qa.md` for Phase 3 |

## Key concepts cheat sheet
- **Runnable**: anything with `invoke / stream / batch` (+ `ainvoke` ...). Models, prompts, parsers, retrievers, chains, agents.
- **LCEL**: `a | b | c` = a `RunnableSequence`. A dict in a chain = `RunnableParallel`. Good for pipelines, *not* for agents with loops (use LangGraph).
- **Messages**: `SystemMessage`, `HumanMessage`, `AIMessage` (`.text`, `.tool_calls`, `.usage_metadata`), `ToolMessage`.
- **`with_structured_output(Model, method="json_schema")`**: validated Pydantic output.
- **`@tool`**: name from the function, description from the docstring, schema from the type hints. The docstring is a prompt.
- **`create_agent`**: the Phase 1 loop as a LangGraph graph (`model ⇄ tools`). The result is the final **state** (`{"messages": [...]}`).
- **Checkpointer + `thread_id`**: conversation memory that persists between `invoke` calls.
- **Middleware**: hooks (`before_model`, `wrap_model_call`, `wrap_tool_call`, `after_model` ...) for limits, routing, guardrails, PII, summarisation.
- **Callbacks**: events emitted during a run. LangSmith and our `Tracer` both listen to them.
- **LangSmith**: env-var tracing, run tree, tags/metadata filters, `@traceable`, `wrap_anthropic`, feedback, playground.

**When NOT to use LangChain** (a good interview answer): a single prompt → a single call (just use the SDK);
you need a brand-new provider feature on day one; or the team wants zero abstraction layers. Many
production teams use LangGraph for orchestration and call provider SDKs directly inside nodes.

## Official docs to skim alongside
- LangChain (Python) overview: https://docs.langchain.com/oss/python/langchain/overview
- Agents (`create_agent`) and middleware: https://docs.langchain.com/oss/python/langchain/agents
- LangSmith observability: https://docs.langchain.com/langsmith/observability
- Anthropic integration: https://docs.langchain.com/oss/python/integrations/chat/anthropic
