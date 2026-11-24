# Phase 8: Build & extend Claude Code (Week 8)

You've used Claude Code since Phase 0 (see `00-setup/claude-code-essentials.md`). Now you know how agents work
inside: the loop, tools, RAG, middleware, multi-agent graphs, evals. This phase looks at Claude Code **as an
engineer**: a production agent harness with extension points, and each one maps to something you've built.

By the end you can build **skills, MCP servers, subagents, hooks and plugins**, run agents **headless in CI**,
and use the **Claude Agent SDK** to put the same harness inside your own products.

## Why this phase, and why now
- **For the job:** "How does a coding agent work? How would you extend it safely?" is a common interview
  question, and MCP is now the standard way to connect tools to AI apps.
- **For your startup:** MCP servers, automation in CI, and the Agent SDK are how you ship agent features fast.
- **Why near the end:** every lesson says *"you built this by hand in Phase N"*. That only works once you have.

## Lessons
Most lessons are markdown with hands-on tasks, because the subject is a tool, not a library. The code you'll
read and extend lives in this folder and in the repo's [`.claude/`](../.claude/), [`.mcp.json`](../.mcp.json)
and [`CLAUDE.md`](../CLAUDE.md).

| # | Lesson | You'll work with |
|---|---|---|
| 01 | [Claude Code is an agent](01_claude_code_as_an_agent.md): the loop, mapped to Phases 1–5 | `claude -p --output-format json` |
| 02 | [Memory, settings and permissions](02_memory_and_settings.md): requests vs guarantees, prompt injection | `CLAUDE.md`, `.claude/settings.json` |
| 03 | [Skills](03_skills.md): progressive disclosure, writing descriptions that trigger | `.claude/skills/quiz-me`, `run-lesson` |
| 04 | [MCP](04_mcp.md): build a server, connect it to Claude Code **and** your own agent | `mcp_server/server.py`, `mcp_server/agent_with_mcp.py` |
| 05 | [Subagents](05_subagents.md): context isolation, parallel work, cheaper models | `.claude/agents/code-reviewer.md`, `explainer.md` |
| 06 | [Hooks](06_hooks.md): guaranteed behaviour around tool calls | `.claude/hooks/*.py` |
| 07 | [Automation](07_automation_and_ci.md): headless mode, GitHub Actions, worktrees | `weekly_summary.sh` |
| 08 | [Plugins and the Agent SDK](08_plugins_and_agent_sdk.md): share your setup, put the harness in your product | `project/`, `08_agent_sdk.py` |

```bash
uv run python 08-claude-code/mcp_server/agent_with_mcp.py    # your agent using an MCP server
uv run python 08-claude-code/08_agent_sdk.py                 # the Agent SDK (needs Claude Code installed)
bash 08-claude-code/weekly_summary.sh                        # headless Claude Code with a JSON schema
```

## Suggested week
| Day | Do |
|---|---|
| Mon | Lessons 01–02. Audit `CLAUDE.md` and `.claude/settings.json`: what would you change for your own app repo? |
| Tue | Lesson 03 + build your `new-lesson-notes` skill |
| Wed | Lesson 04: the MCP server and the agent client, then exercises 1–3 of lesson 04 |
| Thu | Lessons 05–06: subagents and hooks |
| Fri | Lessons 07–08: headless, CI, plugins, Agent SDK |
| Weekend | 🛠 Mini-project: [the course companion plugin](project/README.md) + `exercises.md` |

## Key concepts cheat sheet
- **Requests vs guarantees:** CLAUDE.md, skills and output styles are *context* (the model should follow them). Permission rules, hooks and sandboxing are *enforced* by the harness.
- **CLAUDE.md:** loaded every session, so keep it short. Scopes: user / project / local, plus `.claude/rules/` and on-demand subfolder files.
- **Permission rules:** `Tool(specifier)`, deny > ask > allow, and they match command **text** (`TRACE=x uv run…` ≠ `uv run…`).
- **Skill:** `SKILL.md` = frontmatter (the `description` decides when it's used) + instructions + optional files. Progressive disclosure: description → body → files.
- **MCP:** host ↔ client ↔ server, over stdio or Streamable HTTP. Tools (model decides), resources (app/user decides), prompts (user picks). An MCP tool = a Phase 1 tool definition plus discovery and calling.
- **Subagent:** its own context window, prompt, tools and model. Returns only its conclusion. Supervisor/worker built in.
- **Hook:** a command on an event (`PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`…). JSON in on stdin; exit 2 = block and tell Claude why.
- **Headless:** `claude -p` + `--output-format json` + `--allowedTools` + `--max-budget-usd` (+ `--json-schema`).
- **Plugin:** skills + agents + hooks + MCP in one installable, namespaced package, distributed through marketplaces.
- **Agent SDK:** `query()` / `ClaudeSDKClient` with `ClaudeAgentOptions`. Claude Code's harness as a library. `allowed_tools` approves, `disallowed_tools` restricts.

**Interview answer, MCP in one breath:** "MCP standardises tool calling across apps: a server exposes tools,
resources and prompts with JSON schemas; any MCP client discovers them with `list_tools` and calls them with
`call_tool`. You write an integration once instead of once per app. The risks are the same as any tool use,
plus supply chain: a server runs code and puts text in the model's context."

## 📺 Recommended videos & resources (by lesson)

| Lesson | Resource | Notes |
|---|---|---|
| All | ⭐ [Claude Code docs](https://code.claude.com/docs/en/overview) | The source of truth; features change monthly. Also available as an MCP server: `https://code.claude.com/docs/mcp` |
| 01–02 | ⭐ [Claude Code best practices](https://code.claude.com/docs/en/best-practices) | Context, CLAUDE.md, workflows, from the team that builds it |
| 02 | [Settings](https://code.claude.com/docs/en/settings) · [Memory](https://code.claude.com/docs/en/memory) | Every scope and setting, with examples |
| 03 | ⭐ [Skills](https://code.claude.com/docs/en/skills) | All frontmatter fields and argument substitutions |
| 04 | ⭐ [Model Context Protocol: introduction](https://modelcontextprotocol.io/introduction) | The official spec site: architecture, primitives, security |
| 04 | [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) · [Claude Code + MCP](https://code.claude.com/docs/en/mcp) | `MCPServer`, clients, transports · `claude mcp add`, scopes, OAuth |
| 05 | [Subagents](https://code.claude.com/docs/en/sub-agents) | All frontmatter fields, built-in agents |
| 06 | [Hooks guide](https://code.claude.com/docs/en/hooks-guide) · [Hooks reference](https://code.claude.com/docs/en/hooks) | Recipes first, then every event and input field |
| 07 | [Headless mode](https://code.claude.com/docs/en/headless) · [GitHub Actions](https://code.claude.com/docs/en/github-actions) | Flags and JSON output · the `claude-code-action` setup |
| 08 | [Plugins](https://code.claude.com/docs/en/plugins/overview) · ⭐ [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview) | Packaging and marketplaces · `query`, options, custom tools |
| 01, 05 | [How We Build Effective Agents](https://www.youtube.com/watch?v=D7_ipDqhtwk) (Barry Zhang, Anthropic, video) | Rewatch it: which of its ideas does Claude Code implement? |
| 02, 04 | [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (Anthropic) | Why progressive disclosure, subagents and compaction exist |
| 04 | [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) (Anthropic) | Tool naming and descriptions, which matter even more for MCP servers |

## ✅ Done when
- You can draw the Claude Code loop and point to where skills, MCP, subagents and hooks plug in
- Your own skill, subagent and hook work, and `/quiz-me` has saved answers to your notes
- `server.py` has a tool you added, used from **both** Claude Code and `agent_with_mcp.py`
- `weekly_summary.sh` runs with a budget cap, and you can explain each flag
- Your plugin installs from a marketplace and passes `claude plugin validate`
- `notes/interview-qa.md` has answers for the Phase 8 questions
