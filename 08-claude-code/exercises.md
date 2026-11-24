# Phase 8 exercises

Each lesson ends with hands-on tasks. These are bigger challenges that combine several pieces.
Use Claude Code for them, in the **Learning** output style, and have the `code-reviewer` subagent review the result.

## Warm-up
1. **Explain it.** Draw the Claude Code loop from memory (lesson 01) and mark where CLAUDE.md, skills,
   MCP tools, subagents, permission rules and hooks act. Put the drawing in `notes/`.
2. **Audit a repo.** Clone any open-source repo that has a `.claude/` folder or `.mcp.json`. Before running
   `claude` in it, list everything that would run code on your machine (hooks, stdio MCP servers). Would you approve them?

## Build
3. **Docs-grounded answers.** A skill `ask-docs` that answers LangChain questions **only** from the
   `langchain-docs` MCP server and cites the doc URL for every claim, saying "not in the docs" otherwise.
   (Phase 2 RAG grounding rules, applied to an agent with an MCP retriever.)
4. **An MCP server for your startup idea.** Pick an API you'll need (a payments sandbox, a public dataset, your
   own SQLite database) and wrap 2–3 **read-only** tools as an MCP server with `MCPServer`. Connect it to
   Claude Code and to `agent_with_mcp.py`. Write tool descriptions as carefully as in Phase 1.
5. **Guarded writes.** Add a *write* tool to your server (e.g. `create_note`). Leave it on "ask" in permissions,
   and add a `PreToolUse` hook (matcher `mcp__course__.*`) that blocks it when the note is over 2,000 characters.
6. **Test gate.** A `Stop` hook that runs `uv run python -m py_compile` on every changed `.py` file
   (`git diff --name-only`) and, if any fail, blocks stopping with the error, so Claude keeps fixing.
   What stops this from looping forever? (Read about `stop_hook_active` in the hooks reference.)

## Automate
7. **Changelog bot.** `claude -p` with `--json-schema` that turns `git log` since the last tag into
   `{"added": [], "changed": [], "fixed": []}` and writes `CHANGELOG.md`. Budget-capped, with read-only git tools only.
8. **Eval the agent.** Run the `quiz-me` skill headless on 5 lessons (`claude -p "/quiz-me <lesson>"` with a
   prompt asking for the questions only). Use an LLM-as-judge prompt (Phase 5) to score the questions
   on "tests understanding, not recall". Which lesson gets the weakest questions, and why?

## SDK
9. **Your harness vs theirs.** Give the same task ("find and explain the bug in this file") to your Phase 1
   agent loop with Read/Grep tools you write, and to the Agent SDK. Compare turns, cost, answer quality and lines
   of code you wrote. When is each the better choice for a product?
