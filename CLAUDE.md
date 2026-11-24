# Agentic AI course: instructions for Claude Code

This repo is a hands-on course (basics → LangGraph in production). The person working here is
**a learner**: your job is to help them understand, not to do the course for them.

## How to help
- **Don't solve exercises or mini-projects** (`exercises.md`, `project/`) unless the learner explicitly
  asks for a solution. Prefer hints, questions, and reviewing *their* code.
- Explain Python concepts inline when they first appear. Assume basic Python only.
- When you explain an agent concept, link it to what they built by hand in Phase 1
  (the agent loop in `01-llm-basics/06_agent_loop.py`, tool calling in `05_tool_calling.py`).

## Commands
- Run a lesson: `uv run python <phase-folder>/<file>.py` (never plain `python`; uv picks the `.venv`)
- Add a package: `uv add <package>` (never `pip install`)
- Check the setup: `uv run python 00-setup/check_setup.py`

## Conventions (follow them in any lesson code you write)
- Lesson files are heavily commented with these markers:
  `# 🐍 PYTHON NOTE:` (Python concept) · `# 💡 WHY:` (design reason) · `# ⚠️ GOTCHA:` (common mistake) · `# 🧪 TRY:` (experiment)
- Every lesson starts with a docstring: what it teaches, and a `Run:` line.
- LLM calls go through `course_utils/trace.py` (`trace.show_request` / `show_response` / `show_tool_call`);
  LangChain runs use the `Tracer` callback from `course_utils/lc_trace.py`.
- Shared helpers live in `course_utils/` (`tools.py`, `rag.py`, `trace.py`, `lc_trace.py`). Reuse them.
- The model comes from `MODEL` in `.env`. Never hard-code API keys; never read or print `.env`.

## Layout
`00-setup/` · `01-llm-basics/` · `02-rag/` · `03-langchain/` · `08-claude-code/` (later phases are added
over time). Each phase has `README.md`, numbered lessons, `exercises.md` and a `project/`.
Learner notes: `notes/interview-qa.md` (their own words; don't rewrite answers unless asked) and `notes/ideas.md`.
