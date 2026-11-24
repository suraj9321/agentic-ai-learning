---
name: quiz-me
description: Quiz the learner on a course lesson or topic with interview-style questions, then save their best answers to notes/interview-qa.md. Use when the learner asks to be quizzed, tested, or to practise interview questions.
argument-hint: "[lesson file or topic, e.g. 01-llm-basics/06_agent_loop.py or RAG]"
---

# Quiz me

Topic or lesson: $ARGUMENTS (if empty, ask which lesson; suggest the next unticked item in README.md's roadmap).

1. If a lesson file or folder was given, read it first (and the phase README's "Key concepts cheat sheet").
   Base every question on what that material actually teaches.
2. Ask **5 questions, one at a time**. Wait for the answer before the next one. Mix:
   - 2 × "explain it" (e.g. "what does stop_reason tell you?")
   - 2 × "what happens if…" (predict behaviour, find the bug)
   - 1 × system design / trade-off (the kind asked in AI engineer interviews)
3. After each answer: say what was right, what was missing, and give a model answer in 3–5 sentences.
   Be honest. Don't call a vague answer correct.
4. At the end: a score out of 5, the 1–2 weakest areas, and which lesson section to re-read.
5. Ask: "Shall I add your answers to notes/interview-qa.md?" Only if they say yes, append each question
   under the matching phase heading as `### <question>` followed by **the learner's own answer**,
   improved only where it was wrong (tell them what you changed). Don't paste your model answers instead.

See [examples.md](examples.md) for the question style.
