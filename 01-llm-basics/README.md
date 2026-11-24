# Phase 1: LLM APIs from scratch (Week 1)

**Goal:** by Friday you've built a working agent in plain Python, using no framework.
After that, LangChain and LangGraph are just "conveniences over things I already understand."

## Why no framework yet?
Frameworks hide three things you *must* understand to debug agents in production:
1. **The message list.** What the model actually sees.
2. **The tool-call protocol.** How "the model calls a function" really works.
3. **The loop.** Who decides when the agent stops.

Interviewers often ask "what does LangChain's agent do under the hood?" After this week, you'll know.

## Lessons (run each with `uv run python 01-llm-basics/<file>`)

| # | File | You learn | Python you'll pick up |
|---|---|---|---|
| 01 | `01_first_call.py` | Messages, roles, system prompt, response object, tokens & cost | dicts, lists, attribute access |
| 02 | `02_conversation_and_streaming.py` | Statelessness, chat history, streaming | `while` loops, `with` blocks, iterators |
| 03 | `03_prompt_engineering.py` | Clear instructions, few-shot, XML tags, step-by-step | functions with defaults, multi-line strings |
| 04 | `04_structured_output.py` | Reliable JSON via Pydantic schemas | classes, `BaseModel`, `Literal`, `list[str]` |
| 05 | `05_tool_calling.py` | The tool-use protocol, one step at a time | JSON schema, `**kwargs`, dispatch dicts |
| 06 | `06_agent_loop.py` | **A full agent loop (ReAct)** | `while True` + `break`, error handling |
| 07 | `07_async_parallel.py` | Parallel LLM calls, latency | `async`/`await`, `asyncio.gather` |

Then the mini-project: **`project/`, a CLI research assistant agent.**

## Suggested week
| Day | Do |
|---|---|
| Mon | Phase 0 setup + lessons 01–02 |
| Tue | Lesson 03 + its exercises (prompting is a skill: practise it) |
| Wed | Lessons 04–05 |
| Thu | Lesson 06. Spend time here. Re-type it from memory at the end of the day. |
| Fri | Lesson 07 + start the mini-project |
| Sat | Finish mini-project, write `notes/interview-qa.md` answers |

## Key concepts cheat sheet

**Message roles**
- `system`: instructions and persona (passed as a separate `system=` parameter in the Claude API)
- `user`: input from the human, *or* tool results sent back by your code
- `assistant`: what the model said, including tool-call requests

**Response anatomy**: `response.content` is a **list of blocks**, not a string.
Block types: `text`, `tool_use`, `thinking`, ... Always check `block.type`.

**`stop_reason`**: *why* the model stopped:
- `end_turn`: finished normally
- `tool_use`: wants you to run a tool (the heart of agents)
- `max_tokens`: got cut off; your `max_tokens` was too small
- `refusal`: declined for safety reasons

**The agent loop in one sentence:**
> Call the model → if it asked for tools, run them and send the results back → repeat until it stops asking.

## Official docs to skim alongside
- Messages API: https://platform.claude.com/docs/en/api/messages
- Tool use: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- Prompt engineering: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
- "Building effective agents" (Anthropic, a must-read for interviews): https://www.anthropic.com/engineering/building-effective-agents

## 📺 Recommended videos & resources (by lesson)

| Lesson | Resource | Notes |
|---|---|---|
| All | ⭐ [Building with the Claude API](https://anthropic.skilljar.com/claude-with-the-anthropic-api) (Anthropic Academy, free, video) | The official video course; covers the whole of this phase and previews RAG, MCP and caching |
| All | [anthropics/courses](https://github.com/anthropics/courses) (notebooks) | API fundamentals, prompt engineering, tool use: runnable notebooks |
| 03 | ⭐ [Prompt engineering interactive tutorial](https://github.com/anthropics/prompt-eng-interactive-tutorial) | Nine chapters with exercises; do 1–2 chapters a day this week |
| 04 | [Pydantic: Models](https://docs.pydantic.dev/latest/concepts/models/) | `BaseModel`, validation and `model_json_schema()`, the basis of structured output |
| 05 | [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) (Anthropic) | How to name and describe tools and shape their results so the model uses them well |
| 06 | ⭐ [How We Build Effective Agents](https://www.youtube.com/watch?v=D7_ipDqhtwk) (Barry Zhang, Anthropic, AI Engineer, video) | The talk version of "Building effective agents": when to use an agent vs a workflow |
| 06 | [ReAct paper](https://arxiv.org/abs/2210.03629) (Yao et al.) | The paper behind the reason → act → observe loop you build by hand; the abstract and figure 1 are enough |
| 06 | [LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/) (Lilian Weng) | The classic overview: planning, memory, tool use |
| 06 | [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (Anthropic) | Why the messages list keeps growing and how to manage it; good interview material |
| 07 | [Python docs: Coroutines and Tasks](https://docs.python.org/3/library/asyncio-task.html) | `async`/`await`, `asyncio.gather`, `Semaphore` |
| Project | [Claude cookbooks](https://github.com/anthropics/claude-cookbooks) | Copy-able recipes for tool use, agents and more; browse for ideas to extend your assistant |
