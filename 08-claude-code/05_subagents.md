# Lesson 05: Subagents: a fresh context window for a focused job

A **subagent** is a separate agent that Claude Code starts for one task. It has **its own context window**,
its own system prompt and (optionally) a restricted tool set and a different model. It works, then returns
**only its final answer** to the main conversation.

```
main conversation (your context) ──"review my exercise"──► code-reviewer subagent
                                                              reads 12 files, runs git diff
                                                              (all of that stays in ITS context)
main conversation ◄──── 6 findings, 300 words ────────────────┘
```

> 💡 **WHY:** context is the budget (Phase 0). Exploring a codebase can fill tens of thousands of tokens
> with file contents you'll never need again. A subagent does the reading and hands back the conclusion.
> It's the **supervisor/worker** pattern from LangGraph multi-agent (Phase 4), built into the tool.

## 1. Built-in subagents
Claude Code already delegates to some on its own, e.g. **Explore** (fast, read-only codebase search), **Plan**
(research during plan mode) and **general-purpose** (any multi-step task). When you see "Explore(...)" in the
transcript, that's a subagent.

## 2. Define your own: `.claude/agents/<name>.md`

Open [`.claude/agents/code-reviewer.md`](../.claude/agents/code-reviewer.md):

```markdown
---
name: code-reviewer
description: Reviews the learner's exercise or project code for bugs, agent-specific mistakes and clarity,
  without rewriting it. Use after the learner finishes an exercise or asks for a review.
tools: Read, Grep, Glob, Bash(git diff *), Bash(git status)
model: sonnet
---
You review code written by someone learning to build AI agents in Python. ...
```

| Field | Meaning |
|---|---|
| `name`, `description` | Required. The description decides when Claude delegates on its own (a prompt again!) |
| `tools` | Allowlist. Leave out → inherits all tools. **Read-only reviewers shouldn't have Edit or Write** |
| `model` | `haiku` / `sonnet` / `opus` / a full model ID / `inherit`. Cheap models for simple jobs (Phase 0 cost table) |
| body | The subagent's **system prompt**. It does *not* see your conversation, so write it to be self-contained |

Other useful fields: `permissionMode`, `maxTurns`, `skills` (preload skills), `mcpServers`, `isolation: worktree`
(works on its own copy of the repo, lesson 07), `memory`. Locations: `.claude/agents/` (project),
`~/.claude/agents/` (you), plugins (lesson 08).

**Starting one:** Claude delegates automatically when the description matches, or you ask
(*"use the code-reviewer subagent on my exercise 3"*), or `@agent-code-reviewer`, or `claude --agent code-reviewer`
to make it the main agent for a whole session.

## 3. When to use a subagent (and when not to)

| ✅ Good fit | ❌ Poor fit |
|---|---|
| Lots of reading, short answer (search, review, research) | Needs the back-and-forth of your conversation |
| Needs **different permissions** (read-only reviewer) | Tiny tasks: starting a subagent has overhead |
| Independent tasks that can run **in parallel** | Steps that depend on each other's details |
| A **cheaper model** is good enough (`explainer` uses haiku) | You need to watch every step |

> ⚠️ **GOTCHA:** the subagent only knows what's in its prompt and what it reads. "Review it" fails; "review
> `02-rag/exercises` solution in `my_hybrid.py` for the RRF exercise" works. Same as briefing a colleague.

## 4. Hands-on
1. Write a small exercise solution (any Phase 1–3 exercise), then: *"Use the code-reviewer subagent on it."*
   Compare `/context` before and after: how much of the reviewer's file reading ended up in *your* context?
2. Ask *"How does hybrid search work in this repo?"* Does Claude choose the `explainer` subagent by itself?
   If not, improve its `description` until it does.
3. **Parallel:** *"Use three explainer subagents in parallel to explain lessons 01, 02 and 03 of 02-rag, then
   combine them into one study sheet."* This is fan-out/fan-in, the map-reduce pattern from Phase 4.
4. **Build your own:** `quiz-writer` (model: haiku, tools: Read only) that writes 10 questions for a lesson file.
   Then make the `quiz-me` skill use it: add `context: fork` and `agent: quiz-writer` to the skill's frontmatter.
   What changed?

## Write it down
`notes/interview-qa.md`: *"Why do multi-agent systems use subagents? What's the trade-off?"*
