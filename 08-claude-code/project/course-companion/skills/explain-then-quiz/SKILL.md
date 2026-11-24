---
name: explain-then-quiz
description: Explain a piece of code or a concept at a beginner level, then check understanding with two short questions. Use when the user says they don't understand some code or a concept.
argument-hint: "<file, function or concept>"
---

# Explain, then check

1. Find and read the code for `$ARGUMENTS` (or recall the concept).
2. Explain it as a short story of what happens, in order, citing `file:line`. Explain any Python feature a
   beginner might not know in one sentence. Use one analogy.
3. Ask two short questions that the user can answer only if they understood. Wait for the answers and give feedback.
Do not modify any files.
