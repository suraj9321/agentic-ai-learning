"""
Lesson 02: Conversations (statelessness) and streaming.

What you'll learn:
  - The model remembers NOTHING between calls. Your code keeps the history.
  - How to build a chat loop
  - Streaming: show tokens as they're generated (huge UX win)

Run:  uv run python 01-llm-basics/02_conversation_and_streaming.py
"""

import os

import anthropic
from dotenv import load_dotenv

from course_utils import trace  # shows each request/response (TRACE=full|brief|off in .env)

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
client = anthropic.Anthropic()


def text_of(response) -> str:
    """Join all text blocks of a response into one string."""
    # 🐍 PYTHON NOTE: "".join(list_of_strings) glues strings together.
    # The part inside join(...) is a *generator expression*, like a list comprehension
    # but lazy (values are produced one at a time, without building a list first).
    return "".join(b.text for b in response.content if b.type == "text")


# ---------------------------------------------------------------------------
# 1. Proof that the model is stateless
# ---------------------------------------------------------------------------
print("=" * 60)
print("1. Two separate calls: the model forgets")
print("=" * 60)

request = dict(
    model=MODEL, max_tokens=16000,
    messages=[{"role": "user", "content": "My name is Suraj and I'm learning agentic AI."}],
)
trace.show_request(request, label="call 1: introduce myself")
r1 = client.messages.create(**request)
trace.show_response(r1, label="call 1")
print("Call 1 →", text_of(r1)[:150], "...")

request = dict(
    model=MODEL, max_tokens=16000,
    messages=[{"role": "user", "content": "What's my name?"}],
)
trace.show_request(request, label="call 2: a brand-new list, so no history")
r2 = client.messages.create(**request)
trace.show_response(r2, label="call 2")
print("Call 2 →", text_of(r2)[:150])
# It doesn't know! Each API call is completely independent.


# ---------------------------------------------------------------------------
# 2. "Memory" = re-sending the history yourself
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("2. Same thing, but we send the history")
print("=" * 60)

history = [
    {"role": "user", "content": "My name is Suraj and I'm learning agentic AI."},
    {"role": "assistant", "content": text_of(r1)},  # what the model said before
    {"role": "user", "content": "What's my name?"},
]
request = dict(model=MODEL, max_tokens=16000, messages=history)
trace.show_request(request, label="call 3: WITH the history")
r3 = client.messages.create(**request)
trace.show_response(r3, label="call 3")
print("With history →", text_of(r3)[:150])
print(f"(input tokens this time: {r3.usage.input_tokens}. The history costs tokens on EVERY call)")

# 💡 WHY this matters for agents: every "memory" feature in LangChain/LangGraph
# (chat history, checkpointers, summarisation) is just a strategy for deciding WHAT
# goes into this list. When the conversation grows, you must trim or summarise it,
# because cost and latency grow with every turn.


# ---------------------------------------------------------------------------
# 3. Streaming: print tokens as they arrive
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("3. Streaming")
print("=" * 60)

# 🐍 PYTHON NOTE: `with ... as stream:` is a *context manager*. It sets something up
# (here: opens a streaming HTTP connection) and GUARANTEES cleanup when the block ends,
# even if an error happens. You've seen this pattern with `with open("file") as f:`.
request = dict(
    model=MODEL,
    max_tokens=64000,  # 💡 streaming avoids HTTP timeouts, so a higher ceiling is safe
    messages=[{"role": "user", "content": "Explain what an LLM token is in 4 short bullet points."}],
)
trace.show_request(request, label="streaming")
print("⏩ streaming tokens as they arrive:\n")
with client.messages.stream(**request) as stream:
    # 🐍 PYTHON NOTE: `stream.text_stream` is an *iterator*: a `for` loop pulls
    # one chunk at a time, as the network delivers it.
    for chunk in stream.text_stream:
        print(chunk, end="", flush=True)  # end="" → no newline; flush → show immediately

    final = stream.get_final_message()  # the complete response, same type as messages.create()

print()
trace.show_response(final, label="streaming (the assembled final message)")

print(f"\n\n(stop_reason={final.stop_reason}, output tokens={final.usage.output_tokens})")
# 💡 WHY: total time is the same, but the user sees the first words in ~1 second instead of
# waiting 10 seconds for everything. Every chat product streams. You'll stream from
# FastAPI to a browser in Phase 7.


# ---------------------------------------------------------------------------
# 4. A real chat loop (interactive)
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("4. Chat with the model (type 'quit' to exit)")
print("=" * 60)

messages = []  # the whole conversation lives here

while True:
    user_input = input("\nYou: ").strip()  # 🐍 .strip() removes surrounding spaces/newlines
    if user_input.lower() in ("quit", "exit", ""):
        break

    messages.append({"role": "user", "content": user_input})  # 🐍 .append adds to the end of a list

    request = dict(
        model=MODEL,
        max_tokens=64000,
        system="You are a friendly tutor for someone learning agentic AI. Be concise.",
        messages=messages,
    )
    # Watch this panel: earlier turns show as "(sent before)". They're re-sent EVERY turn.
    trace.show_request(request, label=f"chat turn {len(messages) // 2 + 1}")
    print("Claude: ", end="", flush=True)
    with client.messages.stream(**request) as stream:
        for chunk in stream.text_stream:
            print(chunk, end="", flush=True)
        reply = stream.get_final_message()
    print()
    trace.show_response(reply, label="chat reply")

    # ⚠️ GOTCHA: append the assistant's FULL content (all blocks), not just the text.
    # Later (tool use, thinking) the API needs those blocks back exactly as it sent them.
    messages.append({"role": "assistant", "content": reply.content})
    print(f"\n   [turn input tokens: {reply.usage.input_tokens}]")  # watch this grow!

# 🧪 TRY:
#   1. Chat for 6–8 turns and watch "turn input tokens" grow. That's the cost of memory.
#   2. Keep only the last 4 messages: messages[-4:]. What breaks? (Hint: the first message must be "user".)
#   3. Ask it to "repeat what I said 3 messages ago" with and without trimming.
