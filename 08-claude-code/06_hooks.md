# Lesson 06: Hooks: code that ALWAYS runs at fixed points in the agent loop

A **hook** is a command (or HTTP call, prompt, …) that Claude Code runs automatically on an **event**:
before a tool runs, after it runs, when you submit a prompt, when Claude stops, when a session starts…
Unlike CLAUDE.md (a *request*), a hook is a **guarantee**: it runs every time, whatever the model decides.

> 🔗 **Phase 3 lesson 06 again:** LangChain middleware wraps the model and tool calls with your code
> (limits, PII redaction, guardrails). Hooks are the same idea in Claude Code.

## 1. The events you'll use most

| Event | Fires | Typical use |
|---|---|---|
| `PreToolUse` | Before a tool runs. **Can block it** | Block dangerous commands, protect files |
| `PostToolUse` | After a tool succeeds | Format or lint edited files, run tests, log |
| `UserPromptSubmit` | When you send a prompt. Can add context or block | Add the current branch or date, catch secrets pasted by mistake |
| `Stop` | When Claude finishes its answer. Can make it continue | "Don't stop until the tests pass" |
| `SessionStart` | New or resumed session | Load context (e.g. `git status`, today's TODO) |
| `Notification` | Claude needs your attention | Desktop or phone notification |

(There are many more: `SubagentStop`, `PreCompact`, `PermissionRequest`, `FileChanged`, …; see the docs.)

## 2. How a hook talks to Claude Code

```
Claude Code ──JSON on stdin──► your script ──exit code + stdout/stderr──► Claude Code
  {"hook_event_name": "PreToolUse", "tool_name": "Bash",
   "tool_input": {"command": "rm -rf build"}, "cwd": "...", "session_id": "..."}
```

| Exit code | Meaning |
|---|---|
| `0` | OK, continue (for some events, stdout can return JSON with more detailed decisions) |
| `2` | **Block.** Your stderr is shown **to Claude**, so it can adapt |
| anything else | Non-blocking error (shown to you; the action goes ahead) |

## 3. Read this repo's hooks

[`.claude/settings.json`](../.claude/settings.json):
```json
"hooks": {
  "PreToolUse":  [{ "matcher": "Bash",       "hooks": [{ "type": "command", "command": "python3 \"${CLAUDE_PROJECT_DIR}/.claude/hooks/block_dangerous.py\"" }] }],
  "PostToolUse": [{ "matcher": "Edit|Write", "hooks": [{ "type": "command", "command": "python3 \"${CLAUDE_PROJECT_DIR}/.claude/hooks/check_python_syntax.py\"" }] }]
}
```

- `matcher` picks the tools: an exact name, `Edit|Write`, or a regex (`mcp__course__.*`). Empty or `"*"` = all.
- `${CLAUDE_PROJECT_DIR}` keeps the path right whatever folder Claude is in.
- We call `python3` with only the standard library, so the hook is fast and needs no `uv` start-up.
  (On Windows, use `python`.)

[`block_dangerous.py`](../.claude/hooks/block_dangerous.py) blocks `rm -rf`, force pushes, `git reset --hard`
and **shell commands that read `.env`**, which closes the gap from lesson 02 GOTCHA 2.
[`check_python_syntax.py`](../.claude/hooks/check_python_syntax.py) compiles every edited `.py` file and, if it's
broken, tells Claude immediately.

> ⚠️ **GOTCHA 1, hooks beat allow rules.** Even if a permission rule allows `Bash(rm *)`, the PreToolUse hook
> still blocks `rm -rf`. (While building this course, the hook even blocked one of *our own* commands that
> happened to contain that text: it applies to every session in the repo.)

> ⚠️ **GOTCHA 2, hooks run with YOUR permissions, automatically.** A hook in a cloned repo's
> `.claude/settings.json` is code that runs on your machine. Read the hooks of any repo you don't trust
> (`/hooks` lists them all, read-only).

> ⚠️ **GOTCHA 3, regex blocklists are leaky.** `rm -r -f`, `find . -delete` or a Python one-liner all get past
> our pattern. Hooks are a safety *net*, not a sandbox (lesson 02, section 4).

## 4. Test hooks without Claude
Hooks are just scripts reading JSON, so test them directly:
```bash
echo '{"tool_name":"Bash","tool_input":{"command":"cat .env"}}' | python3 .claude/hooks/block_dangerous.py; echo "exit: $?"
echo '{"tool_name":"Bash","tool_input":{"command":"cat .env.example"}}' | python3 .claude/hooks/block_dangerous.py; echo "exit: $?"
```

## 5. Hands-on
1. Run the two test commands above. Then extend `BLOCKED` to also catch `find … -delete`, and test it the same way.
2. **Protect the lessons:** a `PreToolUse` hook (matcher `Edit|Write`) that blocks edits to files under
   `01-llm-basics/`, `02-rag/` and `03-langchain/` unless the file is inside a `project/` folder or named `my_*.py`.
   Message to Claude: *"Lesson files are read-only; copy it to my_<name>.py first."*
3. **Notification:** a `Notification` hook that shows a desktop notification when Claude needs you
   (macOS: `osascript -e 'display notification "Claude needs you" with title "Claude Code"'`).
4. **SessionStart context:** a hook that prints the next unticked roadmap item from `README.md`. For
   `SessionStart`, stdout is added to Claude's context, so every session starts knowing where you are.
   (Reuse the regex from `course_progress` in the MCP server.)

## Write it down
`notes/interview-qa.md`: *"Prompt instructions vs. hooks/middleware for agent guardrails: when do you need each?"*
