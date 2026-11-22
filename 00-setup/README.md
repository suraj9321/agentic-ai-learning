# Phase 0: Setup & the mental model you need

## 1. Setup (30 min)

### Tools
- **uv**: a fast Python package and environment manager (it replaces `pip` + `venv` + `pyenv`). It's already installed on your machine.
- **VS Code** with the Python extension, or any editor you like.
- **git**: this folder is already a git repo. Commit after each lesson so you can always roll back.

> 🐍 **PYTHON NOTE: virtual environments.**
> Every project has its own isolated folder of installed packages (`.venv/`), so
> project A can use `anthropic 2.x` while project B uses `1.x` without conflicts.
> `uv sync` creates `.venv` from `pyproject.toml`. `uv run python file.py` runs your
> file *inside* that environment, so you never have to "activate" it by hand.
>
> - `uv add <package>`: install a package and record it in `pyproject.toml`
> - `uv sync`: install everything listed in `pyproject.toml`
> - `uv run <cmd>`: run a command inside the project's environment

### API key
1. Create an account at https://platform.claude.com and add a small amount of credit ($10–20 is plenty for this whole course if you're careful).
2. Create an API key: **Settings → API Keys**.
3. Paste it into `.env` (already created from `.env.example`):
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
4. Run: `uv run python 00-setup/check_setup.py`

> 🐍 **PYTHON NOTE: environment variables & `.env`.**
> Secrets never go in code. We put them in a `.env` file (which is git-ignored), and
> `load_dotenv(override=True)` copies them into the process's environment variables. Code then reads
> them with `os.getenv("NAME")`. In production you set real environment variables
> instead of using a file. The code doesn't change.

### Choosing a model (cost)
`.env` has `MODEL=claude-opus-5-5`, the strongest default. Prices are per **1 million tokens** (input / output):

| Model | Input | Output | Good for |
|---|---|---|---|
| `claude-opus-5-5` | $4 | $20 | Default. Best reasoning and agent work |
| `claude-sonnet-5-5` | $2 | $10 | Strong and cheaper. Great for production workloads |
| `claude-haiku-5-5` | $0.10 | $0.50 | Very cheap and fast. Simple tasks, high volume |

A typical lesson run uses about 1–5K tokens, which costs fractions of a cent on any model.
The agent lessons use more because they loop. Switching models is a one-line change in `.env`.
Try the same lesson on different models later: **comparing models is a real AI-engineer skill.**

---

## 2. How LLMs work, for engineers (read this, ~45 min)

You don't need the maths. You do need these 8 facts, because every design decision later comes back to them.

### 1. An LLM predicts the next token, over and over
A **token** is a chunk of text, roughly ¾ of an English word (`"unbelievable"` → `un` `believ` `able`).
The model reads all the tokens so far and predicts the next one, appends it, and repeats.
That's all "generation" is.

### 2. You pay per token: input + output
Every call costs `input_tokens × input_price + output_tokens × output_price`.
Output tokens cost about 5× more than input. **Agents are expensive** because every loop iteration
re-sends the whole conversation as input. For startups, *cost per user* lives or dies here.

### 3. The context window is the model's entire memory
The model knows only (a) what it learned in training and (b) what's in the current request.
That request has a maximum size called the **context window** (1M tokens for current Claude models).
**The model is stateless.** It remembers nothing between API calls. A "chat" works because *your code*
re-sends the full history every time. "Memory" in agents is always *your code deciding what to put in context*.

### 4. Outputs vary from run to run
Same prompt, different answer. Never write code that assumes an exact output string.
Validate structure (lesson 04), and **evaluate across many runs** (Phase 5).
(Older APIs exposed a `temperature` knob. Newer Claude models removed it, and you steer
with prompts and an `effort` setting instead.)

### 5. Models can't *do* anything; they can only *ask*
An LLM outputs text. "Tool use" means the model outputs a structured request
(`call get_weather with {"city": "Paris"}`), *your code* runs it, and you send back the result.
**An agent is just that in a loop.** You'll build it yourself in lesson 06.

### 6. Prompts are code
A system prompt is the spec for the model's behaviour. Treat it like code: version it, test it, review changes.

### 7. Models hallucinate
When the model lacks information, it may confidently make something up. The fixes are engineering, not hope:
give it the facts (RAG, Phase 2), give it tools, ask for citations, and evaluate.

### 8. Latency matters
Generation runs at roughly 50–150 tokens/sec. A 1,000-token answer takes seconds.
That's why we **stream** (lesson 02) and run independent calls **in parallel** (lesson 07).

---

## ✅ Done when
- `check_setup.py` prints all green
- You can explain to a friend, in your own words: token, context window, why the model is "stateless", and what tool use really is.
  (Write it in `notes/interview-qa.md`!)
