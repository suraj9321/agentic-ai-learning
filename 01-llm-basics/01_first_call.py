"""
Lesson 01: Your first LLM call.

What you'll learn:
  - The shape of a request: model, max_tokens, system, messages
  - The shape of a response: content blocks, stop_reason, usage (tokens)
  - How to compute what a call costs

Run:  uv run python 01-llm-basics/01_first_call.py
"""

import os

import anthropic
from dotenv import load_dotenv

# Our tracing helper (course_utils/trace.py) prints exactly what we send and get back.
# Set TRACE=brief or TRACE=off in .env to see less.
from course_utils import trace

# Copies values from .env into environment variables.
# override=True: .env WINS over variables already set in your terminal, so editing .env
# always takes effect. (By default dotenv keeps existing variables. That's the right choice
# in production, where real environment variables should win, but confusing while learning.)
load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")

# 💡 WHY: create the client once and reuse it. It holds an HTTP connection pool,
# so making a new client per call is slower.
# With no arguments it reads ANTHROPIC_API_KEY from the environment.
client = anthropic.Anthropic()


# ---------------------------------------------------------------------------
# 1. The simplest possible call
# ---------------------------------------------------------------------------
print("=" * 60)
print("1. Simplest call")
print("=" * 60)

# 🐍 PYTHON NOTE: we put the request in a dict first, then "unpack" it with **request.
# client.messages.create(**request) is exactly the same as typing model=..., max_tokens=...
# by hand, but having it in a variable lets the tracer show what we send.
request = dict(
    model=MODEL,
    # max_tokens = the maximum number of tokens the model may *generate*.
    # ⚠️ GOTCHA: too small and the answer is cut off mid-sentence (stop_reason == "max_tokens").
    # It's a ceiling, not a target: you only pay for tokens actually generated.
    max_tokens=1600,
    # 🐍 PYTHON NOTE: `messages` is a list of dicts. A dict is {key: value} pairs.
    # Each message is {"role": ..., "content": ...}. The first one must be "user".
    messages=[
        {"role": "user", "content": "In one sentence, what is an AI agent?"},
    ],
)
trace.show_request(request, label="simplest call")
response = client.messages.create(**request)
trace.show_response(response, label="simplest call")

# The response is a Python object (a Pydantic model; more in lesson 04).
# 🐍 PYTHON NOTE: `response.content` is attribute access (dot syntax) on an object,
# unlike `my_dict["key"]` for dicts.
#
# ⚠️ GOTCHA: response.content is a LIST of blocks, not a string. A response can contain
# several blocks (e.g. a `thinking` block, then a `text` block, or a `tool_use` block).
for block in response.content:
    if block.type == "text":
        print(block.text)


# ---------------------------------------------------------------------------
# 2. Look inside the response: this is what you'll debug with all course long
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("2. Response anatomy")
print("=" * 60)

print("id:           ", response.id)
print("model:        ", response.model)
print("stop_reason:  ", response.stop_reason)  # why did it stop? (see README cheat sheet)
print("block types:  ", [b.type for b in response.content])
# 🐍 PYTHON NOTE: `[b.type for b in response.content]` is a *list comprehension*:
# a compact way to build a list: "for each b in content, take b.type".
print("input tokens: ", response.usage.input_tokens)
print("output tokens:", response.usage.output_tokens)


# ---------------------------------------------------------------------------
# 3. What did that cost?
# ---------------------------------------------------------------------------
# Prices in USD per 1 MILLION tokens: (input, output).
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


def cost_usd(usage, model: str) -> float:
    """Return the cost in dollars of one API call."""
    # 🐍 PYTHON NOTE: dict.get(key, default) returns default if key is missing,
    # instead of raising KeyError like dict[key] would.
    # Tuple unpacking: `a, b = (1, 2)` sets a=1, b=2.
    in_price, out_price = PRICES.get(model, (4.00, 20.00))
    return usage.input_tokens / 1_000_000 * in_price + usage.output_tokens / 1_000_000 * out_price
    # 🐍 PYTHON NOTE: 1_000_000 is just 1000000. Underscores make big numbers readable.


print(f"\nThis call cost ${cost_usd(response.usage, MODEL):.6f}")
# 💡 WHY: get in the habit of tracking cost now. For a startup, cost per user decides
# whether the business works. A 10-step agent re-sends the growing history each step,
# so cost grows much faster than the number of steps.


# ---------------------------------------------------------------------------
# 4. System prompt: setting behaviour
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("4. Same question, with a system prompt")
print("=" * 60)

request = dict(
    model=MODEL,
    max_tokens=1600,
    # The system prompt is the model's "job description". It applies to the whole conversation.
    system=(
        "You are a pirate. "
        "Explain with a concrete everyday analogy. Maximum 3 sentences."
    ),
    # 🐍 PYTHON NOTE: strings in parentheses next to each other are joined automatically.
    # A neat way to write long strings across several lines.
    messages=[{"role": "user", "content": "What is an AI agent?"}],
)
trace.show_request(request, label="with a system prompt")
response = client.messages.create(**request)
trace.show_response(response, label="with a system prompt")

for block in response.content:
    if block.type == "text":
        print(block.text)

print(f"\nThis call cost ${cost_usd(response.usage, MODEL):.6f}")
print(response.to_json())  # print the full raw response as JSON

# 🧪 TRY:
#   1. Change the system prompt to "You are a pirate." and re-run.
#   2. Set max_tokens=20 and look at stop_reason. What happens to the text?
#   3. Change MODEL in .env to claude-haiku-5-5 and compare answer quality AND cost.
#   4. Print `response.to_json()` to see the full raw response.
