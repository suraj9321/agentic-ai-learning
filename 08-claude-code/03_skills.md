# Lesson 03: Skills: teach the agent a procedure, loaded only when needed

A **skill** is a folder with a `SKILL.md` file: instructions (and optionally scripts, templates and
reference docs) for one task. Claude sees only each skill's **description** until the skill is needed,
then loads the rest.

## 1. Anatomy

```
.claude/skills/quiz-me/          ← project skill (committed, the whole team gets it)
├── SKILL.md                     ← required: frontmatter + instructions
└── examples.md                  ← optional: loaded only if SKILL.md points to it and it's needed
```

Open [`.claude/skills/quiz-me/SKILL.md`](../.claude/skills/quiz-me/SKILL.md):

```markdown
---
name: quiz-me
description: Quiz the learner on a course lesson or topic with interview-style questions, then save
  their best answers to notes/interview-qa.md. Use when the learner asks to be quizzed, tested, ...
argument-hint: "[lesson file or topic]"
---
Topic or lesson: $ARGUMENTS ...
```

| Frontmatter | What it does |
|---|---|
| `name` | The command: `/quiz-me` (defaults to the folder name) |
| `description` | **The most important line.** It's how Claude decides to use the skill on its own. Say what it does *and when to use it* |
| `argument-hint` | Shown when you type `/quiz-me` |
| `disable-model-invocation: true` | Only **you** can start it (for actions with side effects, e.g. deploy, commit) |
| `user-invocable: false` | Only **Claude** uses it (background knowledge, not a command) |
| `allowed-tools` | Tools it may use without asking while the skill runs |
| `context: fork` | Runs it in a separate subagent context (lesson 05) |
| `model`, `effort` | Use a different model or effort level for this skill |

Inside the body: `$ARGUMENTS` (everything after the command), `$0`, `$1`… (single arguments),
`${CLAUDE_SKILL_DIR}` (the skill's folder, for scripts). A line starting with `` !`command` `` runs the command
**before** Claude sees the skill and inserts its output, e.g. `` !`git diff HEAD` ``.

Where skills live: `.claude/skills/` (project), `~/.claude/skills/` (you, all projects), or inside a plugin
(lesson 08). Old-style `.claude/commands/*.md` files still work, but skills replace them.

## 2. Progressive disclosure, the key idea

| Level | Loaded | Cost |
|---|---|---|
| 1. `name` + `description` | Always, for every skill | A few dozen tokens each |
| 2. `SKILL.md` body | When the skill is used | Up to a few thousand tokens |
| 3. Other files (`examples.md`, scripts' output) | Only when the body says to read or run them | Only if needed |

> 🔗 **You've seen this pattern twice.** Phase 1: the model sees tool *descriptions* and decides when to call
> them. Phase 2: RAG retrieves only the relevant chunks instead of stuffing everything into the prompt.
> Skills apply the same idea to *instructions*. You can install 50 skills and pay for only the descriptions.

> ⚠️ **GOTCHA:** a vague description means the skill never triggers (or triggers at the wrong time). "Helps
> with lessons" ❌. "Run a course lesson with uv and explain the trace output. Use when the learner wants to
> run a lesson and understand what happened" ✅. Same lesson as writing tool descriptions in Phase 1.

## 3. Skills vs. the alternatives

| Use… | When |
|---|---|
| **CLAUDE.md** | Facts and rules needed in *every* session (short!) |
| **Skill** | A *procedure* needed sometimes: review checklist, release steps, a quiz, a report format |
| **MCP server** | New *capabilities*: calling an API, querying a database (lesson 04) |
| **Subagent** | A task that needs its *own context window* (lesson 05) |
| **Hook** | Something that must *always* happen, guaranteed (lesson 06) |

Skills and MCP work well together: MCP gives the *ability* (query the database), a skill gives the
*know-how* (which tables, what to check, how to format the report).

## 4. Hands-on

1. Use both repo skills: `/quiz-me 01-llm-basics/06_agent_loop.py` and `/run-lesson 01-llm-basics/05_tool_calling.py`.
   Then just ask *"test me on embeddings"*. Does `quiz-me` trigger without the slash command? Why can't
   `run-lesson` trigger that way? (Look at its frontmatter.)
2. Read [`.claude/skills/run-lesson/SKILL.md`](../.claude/skills/run-lesson/SKILL.md): why does it allow
   `Bash(TRACE=brief uv run python *)` separately? (Lesson 02, GOTCHA 1.)
3. **Build your own:** `new-lesson-notes`. It reads a lesson file and writes a one-page summary to
   `notes/<lesson-name>.md` using a template stored in the skill folder (`template.md`). Requirements:
   - the description makes it trigger on *"summarise this lesson for my notes"*
   - the template is a separate file (progressive disclosure)
   - it never overwrites an existing notes file without asking
4. Run `/skill-doctor` (if available in your version) or `/context` and find how much context your skills cost.

## Write it down
`notes/interview-qa.md`: *"What is progressive disclosure, and where does it show up in agent design?"*
