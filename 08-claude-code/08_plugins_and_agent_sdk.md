# Lesson 08: Plugins (share your setup) and the Agent SDK (put the harness in your product)

Two ways to take what you built in this phase further: **plugins** package skills, subagents, hooks and
MCP servers so anyone can install them with one command. The **Claude Agent SDK** gives you Claude
Code's whole agent harness as a library for your own apps.

## Part A: Plugins

### 1. Structure
```
course-companion/
├── .claude-plugin/plugin.json      ← manifest (only this goes inside .claude-plugin/)
├── skills/quiz-me/SKILL.md         ← skills         → /course-companion:quiz-me
├── agents/code-reviewer.md         ← subagents
├── hooks/hooks.json                ← hooks (same shape as the "hooks" key in settings.json)
├── hooks/block_dangerous.py
└── .mcp.json                       ← MCP servers
```
```json
// .claude-plugin/plugin.json (only "name" is required)
{ "name": "course-companion", "description": "...", "version": "1.0.0", "author": { "name": "..." } }
```

- Plugin skills are **namespaced** (`/course-companion:quiz-me`), so two plugins can't clash.
- Inside a plugin, refer to your own files with `${CLAUDE_PLUGIN_ROOT}` (see `hooks/hooks.json`): the plugin
  is installed into a cache folder, not where you wrote it.

### 2. Try, validate, share
```bash
claude --plugin-dir 08-claude-code/project/course-companion          # load it for one session (no install)
claude plugin validate 08-claude-code/project/course-companion       # check the manifest and files
claude --plugin-dir 08-claude-code/project/course-companion plugin details course-companion
```
`plugin details` shows each component and its **context cost**. Here's ours:
```
Projected token cost
  Always-on:   ~216 tok   added to every session
  component          always-on  on-invoke
  quiz-me                  ~80       ~250
  code-reviewer            ~60       ~270
```
That's progressive disclosure (lesson 03) in numbers: a few dozen tokens per skill until it's used.

**Marketplaces** are how plugins get shared: a repo (or folder) with `.claude-plugin/marketplace.json` listing plugins.
```bash
claude plugin marketplace add ./08-claude-code/project               # a local folder, or owner/repo on GitHub
claude plugin install course-companion@agentic-course
claude plugin list
```
For a team, commit the marketplace to a GitHub repo, and everyone runs the two commands above.

> ⚠️ **GOTCHA:** installing a plugin = running its hooks and MCP servers on your machine. Same rule as
> lessons 04 and 06: read it before you install it, especially `hooks/` and `.mcp.json`.

## Part B: The Claude Agent SDK

### 3. What it is
Your Phase 1 loop, LangChain's `create_agent` (Phase 3) and the Agent SDK are three levels of the same idea:

| | You write | You get |
|---|---|---|
| Phase 1: Messages API | The loop, tools, everything | Full control, full responsibility |
| Phase 3/4: LangChain / LangGraph | Graph or agent config, your tools | Model-agnostic building blocks, state, persistence |
| **Agent SDK** | Options + your custom tools | Claude Code's harness: built-in file/shell/web tools, permissions, hooks, subagents, MCP, context compaction, sessions |

Choose the SDK when your product's agent needs to **work on files and run commands** (a coding,
data-analysis or ops agent) and you'd rather not rebuild a harness. Choose LangGraph when you need custom
control flow, any model provider, or durable workflows with human approval steps (Phase 4).

### 4. Read and run [`08_agent_sdk.py`](08_agent_sdk.py)
```bash
uv run python 08-claude-code/08_agent_sdk.py        # ≈ $0.15–0.20 per run with the default model
```
Things to notice:
- `query(prompt, options)` is an **async generator**: it yields messages as the agent works (Phase 1 lesson 07).
- A custom tool with `@tool(...)` + `create_sdk_mcp_server(...)`: an **in-process MCP server**. It's the same
  protocol as lesson 04, without a subprocess. Its name is `mcp__course__count_markers`.
- `allowed_tools` **auto-approves**, it doesn't restrict; `disallowed_tools` restricts. (The GOTCHA in the file.)
- `max_turns` and `max_budget_usd`: the limits your Phase 1 loop had (`max_steps`) plus one it didn't (a budget).
- The SDK runs the Claude Code harness under the hood. By default (`setting_sources=None`) it loads the
  same settings the CLI does: `CLAUDE.md`, `.claude/settings.json` **and its hooks**.
  ⚠️ GOTCHA: if your product runs the SDK in a folder it doesn't control (a user's uploaded repo), pass
  `setting_sources=[]`. Otherwise that folder's `.claude/settings.json` can run hooks on your server.

### 5. Hands-on
1. **Install your plugin** through the local marketplace. Run `/course-companion:quiz-me` and check that the
   hook blocks `rm -rf` (ask Claude to delete a throwaway folder that way).
2. **Add to the plugin:** an `explainer` subagent and a `SessionStart` hook (lesson 06 exercise 4). Bump `version`, validate, update.
3. **SDK, add a hook in code:** `ClaudeAgentOptions(hooks=...)` takes Python callbacks. Add a `PreToolUse` hook
   that logs every tool call to a file. Compare with the `.claude/hooks/*.py` scripts.
4. **SDK, your own product agent:** a "lesson doctor" that takes a lesson path, runs it with `Bash(uv run python *)`
   allowed, and if it crashes, explains why in plain words (read-only: no edits). Cap it at $0.30.

## Write it down
`notes/interview-qa.md`: *"Raw API vs a framework vs an agent SDK: how do you choose for a new product?"*
