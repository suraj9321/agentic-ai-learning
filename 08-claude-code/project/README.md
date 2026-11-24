# 🛠 Mini-project: "Course companion" Claude Code plugin

Package what you built in this phase into a **plugin** that another learner (or your future team) can
install with two commands. It also makes a good portfolio piece: it shows you understand agent extension points,
context costs and safety, not just prompting.

```bash
claude plugin marketplace add ./08-claude-code/project
claude plugin install course-companion@agentic-course
```

## What's here (the reference version)
```
project/
├── .claude-plugin/marketplace.json        ← the marketplace: lists the plugins in this folder
└── course-companion/
    ├── .claude-plugin/plugin.json         ← manifest
    ├── skills/quiz-me/SKILL.md            ← generalised version of the repo's quiz-me (works in any repo)
    ├── skills/explain-then-quiz/SKILL.md  ← explain code, then check understanding
    ├── agents/code-reviewer.md            ← read-only reviewer subagent
    ├── hooks/hooks.json + block_dangerous.py   ← safety hook (uses ${CLAUDE_PLUGIN_ROOT})
    └── .mcp.json                          ← live docs: LangChain + Claude API
```

## Your tasks
Build your **own** version first (copy only `plugin.json` and `marketplace.json`), then compare.

1. **Skills (lesson 03):** `quiz-me` and one skill of your own design. Both descriptions must trigger reliably
   from plain requests. Test each one 3 times with different wording.
2. **Subagent (lesson 05):** `code-reviewer`, read-only (check: it must not be able to edit).
3. **Hook (lesson 06):** the safety hook, plus a `SessionStart` hook that reminds the user of their next step.
4. **MCP (lesson 04):** the two docs servers. **Stretch:** ship your own course MCP server inside the plugin
   (`"command": "uv", "args": ["run", "--with", "mcp", "python", "${CLAUDE_PLUGIN_ROOT}/server.py"]`).
5. **Quality bar:**
   - `claude plugin validate` passes with no warnings
   - `plugin details` always-on cost **under 400 tokens**
   - a `README.md` in the plugin explaining what each part does, and what it runs on the user's machine (hooks, servers)
6. **Ship it:** push to a GitHub repo, then on another machine (or a teammate's):
   `claude plugin marketplace add <you>/<repo>` → install → `/course-companion:quiz-me`.

## Interview talking points
- Why each piece is the right extension point (skill vs subagent vs hook vs MCP).
- Context cost: how progressive disclosure keeps the always-on cost low.
- Safety: which parts are *requests* (skills, prompts) and which are *guarantees* (hooks), and why a plugin user
  should read `hooks/` and `.mcp.json` before installing.
