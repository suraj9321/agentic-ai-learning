# Lesson 01: Claude Code is an agent, and you already know how it works

You've used Claude Code since Phase 0. Now look at it as an **engineer**: it is an agent harness built
on exactly the pieces you've studied. Everything in this phase (skills, MCP, subagents, hooks, the SDK)
is a way to plug into one part of that loop.

## The loop you wrote in Phase 1 lesson 06, at production scale

```
          ┌───────────────────────── context window ─────────────────────────┐
          │ system prompt + CLAUDE.md + skill descriptions + tool definitions │
          │ + the conversation so far (messages, tool calls, tool results)    │
          └───────────────────────────────┬───────────────────────────────────┘
                                          ▼
                                   call the model
                                          │
                   stop_reason == "tool_use"? ──no──► answer, wait for you
                                          │ yes
                                          ▼
         PreToolUse hooks ─► permission check (rules / mode / ask you) ─► run tool ─► PostToolUse hooks
                                          │
                              append tool_result, loop ◄┘
```

| Claude Code piece | Where you built or saw it | Plugs in via (this phase) |
|---|---|---|
| The loop (think → tool → observe) | Phase 1 lesson 06 `run_agent()` | Agent SDK (lesson 08) |
| Tools: Read, Edit, Bash, Grep, Glob, WebFetch… | Phase 1 lesson 05 `TOOLS` + `TOOL_FUNCTIONS` | **MCP** adds tools (lesson 04) |
| System prompt + project instructions | Phase 1 lesson 03 prompt engineering | **CLAUDE.md**, rules, output styles (lesson 02) |
| Knowledge loaded only when relevant | Phase 2 RAG: retrieve, then generate | **Skills** (lesson 03) |
| Step limit, guardrails, approval | Phase 3 middleware, Phase 1 `max_steps` | **Permissions, hooks** (lessons 02, 06) |
| Context management | Phase 3 summarisation middleware | `/compact`, **subagents** (lesson 05) |
| Multi-agent delegation | Phase 4 LangGraph supervisor/handoffs | **Subagents** (lesson 05) |
| Running without a human | Phase 5 evals in CI | **Headless `claude -p`**, GitHub Actions (lesson 07) |

> 💡 **WHY this matters for interviews:** "How does a coding agent like Claude Code work?" is a common
> question. You can now answer from the inside: the loop, the tool set, permissions, context management
> and extension points, and you've built each one yourself.

## See it for yourself

🧪 **TRY 1, watch the loop:** start `claude` and ask *"Find every place `trace.show_tool_call` is called
and summarise how its output differs between lessons."* Count the tool calls. Which were run **in parallel**
(several tool calls in one model turn, like Phase 1 lesson 07)?

🧪 **TRY 2, read the context:** run `/context`. Find the system prompt, tool definitions, MCP tools, skills and
memory files in the grid. Which part grows as you keep chatting?

🧪 **TRY 3, the same loop from a script:** run
```bash
claude -p "How many lesson files are in 01-llm-basics?" --output-format json
```
Look at the JSON: `result`, `num_turns`, `total_cost_usd`, `usage`. The same agent, without the chat window
(lesson 07 builds on this).

## Write it down
In `notes/interview-qa.md`, answer: *"Walk me through what happens inside a coding agent when I ask it to
fix a failing test."* Use the diagram above, in your own words.
