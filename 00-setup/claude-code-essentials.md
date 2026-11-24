# Claude Code essentials (Phase 0, ~half a day)

Claude Code is an AI coding agent that runs in your terminal (and in VS Code/JetBrains, the desktop app
and the web). You'll use it for the whole course, and for every app you build alongside it.
This page gets you **productive and safe** with it. Phase 8 goes deep: you'll build your own skills,
MCP servers, subagents, hooks and plugins, and use its engine (the Agent SDK) in your own code.

> 💡 **WHY learn it on day 1:** building apps while you study is the fastest way to learn. A coding agent
> makes that possible, *if* you use it as a tutor and pair programmer, not as someone who does the course for you.

> ⚠️ **GOTCHA, the big one:** if Claude Code writes your exercises, you learn nothing and interviews will
> show it. This repo's `CLAUDE.md` tells it not to solve exercises unless you ask. Section 4 shows how to set it up for learning.

---

## 1. Install and first session (30 min)

```bash
# macOS / Linux / WSL (native installer, auto-updates)
curl -fsSL https://claude.ai/install.sh | bash
# Windows PowerShell:  irm https://claude.ai/install.ps1 | iex
# (Homebrew: brew install --cask claude-code · WinGet: winget install Anthropic.ClaudeCode)

claude --version
cd agentic-ai-learning-basics-to-langgraph-prod
claude                       # starts a session in THIS folder; log in when the browser opens
```

You need a Claude subscription (Pro/Max/…) or a Console account. If `ANTHROPIC_API_KEY` is set in your
shell and you approve it, Claude Code bills that API key instead of your subscription.

> ⚠️ **GOTCHA:** the API key in this repo's `.env` is for the *lessons* (your Python code). Claude Code does
> not read `.env`. Keep the two separate in your head: one is **a tool you use**, the other is **an API you program**.

**The basics inside a session**

| You type | What it does |
|---|---|
| plain text | Ask or instruct. Claude reads files, runs commands and edits code, asking permission as needed |
| `@01-llm-basics/06_agent_loop.py` | Put a file into the conversation (Tab autocompletes paths) |
| `!git status` | Run a shell command yourself; the output goes into the conversation |
| `/` | List commands. Try `/help`, `/model`, `/usage`, `/status` |
| `Esc` | Stop Claude mid-step (nothing is lost) |
| `Esc Esc` or `/rewind` | Go back to an earlier point: undo the conversation, the code changes, or both |
| `Shift+Tab` | Cycle permission modes (section 6), including **plan mode** |
| `claude --continue` / `/resume` | Pick up your last (or an older) session |

🧪 **TRY:** in a session, ask *"What does `course_utils/trace.py` do, and which lessons use it?"*
Watch the tool calls it makes (Read, Grep, …). That's an agent loop, the same one you'll build by hand in
Phase 1 lesson 06.

---

## 2. Context is your budget (45 min)

Everything from Phase 0's "How LLMs work" applies to Claude Code: the conversation, every file it reads
and every command output **fill the context window**, and every turn re-sends all of it (cost and
latency). When the context gets long, quality drops: older details get lost and it starts forgetting instructions.

| Command | When |
|---|---|
| `/context` | See what's using the context window (system prompt, tools, files, messages) |
| `/clear` | **Starting a different task.** A fresh context is the #1 habit of effective users |
| `/compact [what to keep]` | Same task, but the conversation is long. Summarises it and continues |
| `/usage` | Cost / plan limits for the session |
| `/model` | Switch model. A stronger model for planning and hard bugs, a faster one for simple edits |

**Habits that save tokens *and* get better answers**
- **Point, don't make it search.** `@03-langchain/03_tools_and_agents.py line 40: why bind_tools here?` beats
  *"why does the agent lesson use bind_tools?"*
- **One task per conversation.** `/clear` between them.
- **Paste the error, not a description of it.** `!uv run python … ` puts the real output in context.
- **Ask for short answers when that's all you need:** *"one paragraph"*, *"just the command"*.

> 💡 **WHY:** this is **context engineering**, the same skill you'll need when *your* agents' message lists grow
> (Phase 1 lesson 06, Phase 3 summarisation middleware). You're learning it from the user's side first.

---

## 3. Plan first, then code (45 min)

For anything bigger than a one-line change, use this workflow:

1. **Explore:** *"Read `02-rag/04_rag_by_hand.py` and `course_utils/rag.py`. Don't change anything yet."*
2. **Plan:** press `Shift+Tab` until the mode shows **plan** (or type `/plan <what you want>`).
   Claude researches and writes a plan **without editing files**. Read it, push back, ask questions.
3. **Code:** approve the plan. Claude implements it.
4. **Verify and commit:** run it yourself (`!uv run python …`), read the diff (`!git diff`), commit.

If it goes wrong, `Esc Esc` / `/rewind` restores the code and conversation to before the change.
Checkpoints track Claude's file edits, not everything: **git is still your real safety net. Commit often.**

> ⚠️ **GOTCHA:** don't accept a plan you don't understand. "Explain step 3 of the plan" is a great learning prompt.

---

## 4. Set it up for learning (30 min)

**Output styles** change how Claude Code talks to you. Two built-in styles are made for learning:

```
/output-style Learning      # it stops and asks YOU to write the key pieces of code
/output-style Explanatory   # it explains its choices and the codebase as it works
/output-style               # list styles / go back to Default
```

Use **Learning** while doing lessons and exercises, and **Explanatory** or Default when building your own apps.
(The choice is saved in `.claude/settings.local.json`, which is personal and not committed.)

**Prompts that make you learn instead of copy**

| Instead of… | Ask… |
|---|---|
| "Write the solution to exercise 3" | "Give me a hint for exercise 3, not the solution" |
| "Fix this" | "What's wrong here? Explain, don't fix it" |
| "Write an agent that…" | "I wrote this agent. Review it like a senior engineer" (Phase 8 gives you a `code-reviewer` subagent for this) |
| "Explain RAG" | "Quiz me on RAG, one question at a time" (try `/quiz-me RAG`: it's a skill in this repo) |

---

## 5. CLAUDE.md: tell Claude about your project (30 min)

`CLAUDE.md` is a markdown file Claude Code **loads into context at the start of every session**: project
commands, conventions and rules. This repo already has one: open [`/CLAUDE.md`](../CLAUDE.md) and read it.
It's why Claude Code knows to use `uv run`, follows the `💡 WHY` marker style and doesn't solve your exercises.

| File | Scope | Committed? |
|---|---|---|
| `./CLAUDE.md` | This project, everyone | ✅ yes |
| `./CLAUDE.local.md` | This project, only you | ❌ (in `.gitignore`) |
| `~/.claude/CLAUDE.md` | All your projects | — |

🧪 **TRY:**
1. Create `CLAUDE.local.md` with things about *you*, e.g. *"I know basic Python. I'm also studying deep learning.
   Explain with analogies to neural networks where it helps."*
2. Run `/memory` to see which memory files are loaded (and toggle **auto memory**, notes Claude saves for itself).
3. For your *own* app repos, start with `/init`: it reads the code and drafts a `CLAUDE.md` for you to edit.

> ⚠️ **GOTCHA:** CLAUDE.md is *context*, not a guarantee. Keep it short (every line costs tokens on every
> turn) and specific (*"run lessons with `uv run python`"*, not *"write good code"*). For rules that must
> never be broken, use permissions and hooks (next section, and Phase 8).

---

## 6. Permissions: what it may do without asking (30 min)

By default Claude Code **asks** before editing files or running commands. Read what it wants to run
before approving. `Shift+Tab` cycles through the **permission modes**:

| Mode | Behaviour | Use when |
|---|---|---|
| default | Asks before edits and commands | Learning, unfamiliar code |
| acceptEdits | Edits files freely, still asks for commands | You're watching and will review the diff |
| plan | Read-only research and a plan | Before any non-trivial change |
| auto | A safety classifier approves or blocks each action | Longer tasks you trust, on supported plans |

Rules make the common, safe things silent. This repo's [`.claude/settings.json`](../.claude/settings.json) allows
`uv run python …` and read-only git commands, and **denies reading `.env`**. Run `/permissions` to see them.

> ⚠️ **GOTCHA:** never run `--dangerously-skip-permissions` (bypass mode) on your real machine. A prompt
> injection in a web page or file it reads could make it run anything. Phase 8 lesson 02 explains why.

---

## 7. Use Skills and MCP servers (30 min)

Two ways to give Claude Code new abilities. Phase 8 teaches you to **build** both. For now, **use** them.

**Skills** are folders of instructions (`SKILL.md`) that Claude loads *only when needed*. This repo includes two:
- `/quiz-me <lesson or topic>`: interview-style quiz, saves your answers to `notes/interview-qa.md`
- `/run-lesson <file>`: runs a lesson and walks you through the trace output

**MCP servers** connect Claude Code to external tools and data through a standard protocol (MCP, the Model
Context Protocol). This repo's [`.mcp.json`](../.mcp.json) configures three:
- `langchain-docs` and `claude-platform-docs`: search the **official, current** LangChain and Claude API docs
  (frameworks change faster than any model's training data)
- `course`: a small server *you'll write yourself* in Phase 8 (course progress + a calculator)

The first time you start `claude` in this repo it asks you to **approve** the project's MCP servers. Then:
```
/mcp                                             # status of each server
How do I add memory to a create_agent agent? Check the LangChain docs.
How far am I through the course?                 # uses the course server
```

To add a server yourself (for your own projects), for example Claude Code's own docs:
```bash
claude mcp add --transport http claude-code-docs https://code.claude.com/docs/mcp
claude mcp list
```

> 🔗 **Phase 1 connection:** an MCP tool is exactly a tool definition (name, description, JSON schema), like the
> ones you write by hand in Phase 1 lesson 05. MCP standardises how any app finds and calls them.

> ⚠️ **GOTCHA:** an MCP server runs code and feeds text into Claude's context. Only add servers you trust,
> the same as installing a package.

---

## ✅ Done when
- `claude` runs in this repo, the MCP servers are approved, and `/mcp` shows them connected
- You've used: `@file`, `!command`, `/clear`, `/context`, plan mode, and `Esc Esc` to rewind one change
- You created `CLAUDE.local.md` and switched to the **Learning** output style
- You ran `/quiz-me` once and asked a docs question through an MCP server
- You can explain in your own words: why `/clear` matters, and the difference between CLAUDE.md and a permission rule
