---
name: run-lesson
description: Run a course lesson file with uv and explain the trace output step by step. Use when the learner wants to run a lesson and understand what happened.
argument-hint: "<path to lesson .py file>"
disable-model-invocation: true
allowed-tools: Bash(uv run python *) Bash(TRACE=brief uv run python *) Read
---

# Run a lesson and explain it

1. Read `$ARGUMENTS` (the docstring tells you what the lesson teaches).
2. Run it with `TRACE=brief uv run python $ARGUMENTS` (brief keeps the output short; say they can use
   `TRACE=full` to see every message).
3. Explain the output **in the order it happened**: each model call (what was sent, why it stopped),
   each tool run, and the totals (tokens, cost). Point to the line in the file that produced each step.
4. End with the lesson's `🧪 TRY:` suggestions as a short checklist. Don't make the changes yourself.

If it fails: explain the error in plain words and the likely cause (missing `.env` key, not using
`uv run`, network). Don't edit lesson files to make it pass.
