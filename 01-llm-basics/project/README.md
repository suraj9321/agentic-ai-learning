# 🛠 Mini-project: CLI research assistant

A real agent, built with no framework, that searches the web, reads your notes, does maths,
and writes markdown reports into `workspace/`.

```bash
uv run python 01-llm-basics/project/research_assistant.py
```

Example session:
```
You: What are the 3 most popular open-source LLM observability tools? Compare them briefly.
  🌐 searching: open source LLM observability tools
  ...
You: Save that as a report called observability.md
  🔧 write_report(...)
You: /cost
```

## Read the code in this order
1. `TOOLS`: note the difference between the **server tool** (`web_search`: just `type` + `name`)
   and **client tools** (yours: full `input_schema`).
2. `_safe_path`: sandboxing. Why must file tools never trust the path the model sends?
3. `ResearchAgent.ask`: the same loop as lesson 06, plus `pause_turn` and server-tool blocks.
4. `self.messages`: lives on the object, so follow-up questions remember earlier ones.

## Your tasks (do at least 1–3)
1. **Drop a file into `workspace/`** (e.g. your startup idea notes) and ask the agent to
   research competitors for it and save a report.
2. **Add a tool** `fetch_url(url)` using `urllib.request` that downloads a page and returns
   its first 10,000 characters of text. (Hint: search "python strip html tags".)
3. **Add a `--model` command** (`/model claude-haiku-5-5`) to switch models mid-session, and
   compare quality vs `/cost` on the same question.
4. **Make errors safe:** if an API error happens in the middle of the loop, the history may
   end with an assistant `tool_use` that has no `tool_result`. Fix `main()` so it restores
   `agent.messages` to how it was before the question. (Hint: remember `len(agent.messages)`
   before calling `ask`, then slice.)
5. **Stretch:** stream the final answer token by token (lesson 02) instead of printing it at once.
6. **Stretch:** add a `confirm` step: before `write_report` runs, ask the human "Save? (y/n)".
   You've just built **human-in-the-loop**, which you'll do properly with LangGraph `interrupt` in Phase 4.

## Portfolio
Push this to GitHub with a short README and a GIF/screenshot of a session. Title idea:
*"Research agent from scratch: no frameworks, ~250 lines"*. That alone is a strong signal to interviewers.
