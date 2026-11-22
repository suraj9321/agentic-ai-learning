# 🛠 Mini-project: research agent, LangChain edition

The Phase 1 research assistant rebuilt with `create_agent`, plus Phase 2's document search, memory,
call limits, and LangSmith tracing.

```bash
uv run python 03-langchain/project/research_agent.py               # docs: 02-rag/project/docs
uv run python 03-langchain/project/research_agent.py ~/my-pdfs     # your own documents
```

Example session:
```
🧑 What is the learning budget in my handbook, and how does it compare with the current price
   of a ticket to the AI Engineer World's Fair conference? Keep it short.
   ⚙️ search_my_docs("learning budget")   🌐 web_search(...)
🤖 Handbook: USD 1,500 per year [nimbus_employee_handbook.pdf p.2] ... Engineering ticket $1,499 ...
🧑 Save that as a report called learning-budget.md
🤖 Saved the report to learning-budget.md in your workspace.
```

## Read the code in this order
1. The tools: `@tool` functions vs the `WEB_SEARCH` dict (a server tool passed through to Anthropic).
2. `build_agent()`: model + tools + system prompt + middleware + checkpointer. That's the whole agent.
3. `main()`: `thread_id` is the conversation's identity, and `/reset` just makes a new one.
4. Open `01-llm-basics/project/research_assistant.py` side by side. What did you NOT have to write?

## Your tasks (do at least 1–4)
1. **Compare the two versions.** Write a short table in this README: lines of code, number of model calls
   for the same question, total tokens, and what was easier or harder to debug. That table is interview gold.
2. **Watch the cost.** Web search results are big: the example question above used ~79k input tokens
   (~$0.18 on Sonnet). Find the expensive steps in LangSmith (or with `/cost`). Then try: `max_uses=2`,
   running on Haiku, or a summarisation middleware. Measure each change.
3. **Persistent memory.** Replace `InMemorySaver` with `SqliteSaver` (`uv add langgraph-checkpoint-sqlite`)
   and keep the same `thread_id` across restarts (e.g. read it from a file). Your agent now remembers
   yesterday's research.
4. **`pause_turn`.** Long web-search turns can stop with `stop_reason="pause_turn"`. Write an `@after_model`
   middleware or a small loop in `main()` that automatically re-invokes the agent to continue.
5. **Approve before writing.** Add a `@wrap_tool_call` middleware that asks `Save report X? (y/n)` in the
   terminal before `write_report` runs. (Phase 4 does this properly with LangGraph `interrupt`, which also
   works in a web app where `input()` doesn't.)
6. **Stretch: streaming.** Use `agent.stream(..., stream_mode="messages")` to print the final answer token by
   token, and `stream_mode="updates"` to show "🔎 searching your docs..." progress lines.

## Portfolio
Put the Phase 1 and Phase 3 versions in one repo with the comparison table from task 1 and a LangSmith
trace screenshot. *"I built the same agent from scratch and with LangChain, and here's what each costs you"*
shows depth that most candidates don't have.
