---
name: quiz-me
description: Quiz the user on a topic or file they are studying, with interview-style questions one at a time, and optionally save their answers to a notes file. Use when the user asks to be quizzed, tested, or to practise interview questions.
argument-hint: "[file, folder or topic]"
---

# Quiz me

Topic: $ARGUMENTS (if empty, ask what they are studying).

1. If a file or folder was given, read it first and base every question on what it actually teaches.
2. Ask 5 questions, one at a time, waiting for each answer: 2 "explain it", 2 "what happens if / find the bug",
   1 trade-off or system design question.
3. After each answer: what was right, what was missing, and a model answer in 3–5 sentences. Be honest.
4. At the end: a score out of 5, the weakest areas, and what to re-read.
5. Offer to save the questions with **the user's own answers** (corrected where wrong) to a notes file.
   Use `notes/interview-qa.md` if it exists; otherwise ask where. Never save without a yes.
