"""
Lesson 01: LangChain chat models, the same API calls behind a common interface.

What you'll learn:
  - What LangChain is (and isn't): a common interface over many providers + building blocks
  - init_chat_model("provider:model"): switch providers by changing one string
  - Message objects: SystemMessage, HumanMessage, AIMessage
  - What's inside an AIMessage (content, usage_metadata, response_metadata)
  - invoke / stream / batch: the 3 ways to call ANY LangChain component

Compare every section with Phase 1 lessons 01–02, which did the same with the raw SDK.

Run:  uv run python 03-langchain/01_chat_models.py
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from course_utils import trace
from course_utils.lc_trace import Tracer

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")

# One Tracer for the whole lesson: it prints the 📤/📥 panels for every model call.
# You pass it in `config={"callbacks": [tracer]}`. Lesson 05 replaces this with LangSmith.
tracer = Tracer()
CONFIG = {"callbacks": [tracer]}


# ---------------------------------------------------------------------------
# 1. Create a model
# ---------------------------------------------------------------------------
trace.step("1. init_chat_model")

# "anthropic:claude-..." → LangChain imports langchain_anthropic.ChatAnthropic for you.
# Other providers need their package installed, then just a different string:
#   init_chat_model("openai:gpt-5.1")          # uv add langchain-openai
#   init_chat_model("google_genai:gemini-3-pro")  # uv add langchain-google-genai
#   init_chat_model("ollama:llama3.3")         # local models, uv add langchain-ollama
# 💡 WHY this matters for a startup: you can A/B test providers on cost and quality, or fall
# back to another provider during an outage, without rewriting your app.
model = init_chat_model(f"anthropic:{MODEL}", max_tokens=16000)
print(f"type: {type(model).__name__}   model: {model.model}")
# ⚠️ GOTCHA: "a common interface" isn't magic. Provider-specific features (Claude's server
# tools, thinking settings, prompt caching) still need provider-specific options, and quality
# differs between models. Switching providers ALWAYS needs re-testing (evals, Phase 5).


# ---------------------------------------------------------------------------
# 2. invoke(): one call
# ---------------------------------------------------------------------------
trace.step("2. invoke() with a string, then with messages")

reply = model.invoke("In one sentence, what is LangChain?", config=CONFIG)
# A plain string is shorthand for [HumanMessage("...")].

messages = [
    SystemMessage("You are a concise tutor. Answer in at most 2 sentences."),
    HumanMessage("What's the difference between LangChain and LangGraph?"),
]
# Raw SDK equivalent (Phase 1): system="..." as a separate parameter, plus
# messages=[{"role": "user", "content": "..."}]. LangChain puts the system prompt in the list
# and converts it for each provider (Claude wants it separate, OpenAI wants it in the list).
reply = model.invoke(messages, config=CONFIG)


# ---------------------------------------------------------------------------
# 3. Inside an AIMessage
# ---------------------------------------------------------------------------
trace.step("3. AIMessage anatomy")

print("type:              ", type(reply).__name__)
print("reply.text:        ", reply.text[:120])          # all text blocks joined: what you usually want
print("reply.content type:", type(reply.content).__name__)  # str OR a list of blocks (thinking, tool_use, ...)
print("usage_metadata:    ", {k: reply.usage_metadata[k] for k in ("input_tokens", "output_tokens", "total_tokens")})
print("stop_reason:       ", reply.response_metadata.get("stop_reason"))
print("response_metadata keys:", list(reply.response_metadata.keys()))
# 💡 WHY two views: usage_metadata is STANDARDISED across providers (the same keys for OpenAI,
# Gemini...). response_metadata is the provider's raw extra info. Code that should work with
# any provider reads usage_metadata and .text; provider-specific code reads response_metadata.

# A conversation is just a growing list: the model is still stateless (Phase 1 lesson 02).
messages.append(reply)  # an AIMessage goes straight back into the list
messages.append(HumanMessage("Give me a one-line analogy for that."))
reply = model.invoke(messages, config=CONFIG)  # watch the 📤 panel: NEW vs (sent before)
print("\n💬", reply.text)


# ---------------------------------------------------------------------------
# 4. stream(): tokens as they arrive
# ---------------------------------------------------------------------------
trace.step("4. stream()")

full = None
print("⏩ streaming (the 📤 panel appears first, then tokens as they arrive):")
for chunk in model.stream("List 3 uses of AI agents as short bullet points.", config=CONFIG):
    # Each chunk is an AIMessageChunk with a little bit of text.
    print(chunk.text, end="", flush=True)
    # 🐍 PYTHON NOTE: chunks support `+` (the class defines __add__), which merges them.
    # `full = chunk if full is None else full + chunk` is a one-line if/else (a "conditional expression").
    full = chunk if full is None else full + chunk
print(f"\n(merged {type(full).__name__}: {len(full.text)} chars, usage={full.usage_metadata['output_tokens']} output tokens)")


# ---------------------------------------------------------------------------
# 5. batch(): many inputs in parallel
# ---------------------------------------------------------------------------
trace.step("5. batch(): parallel calls without writing asyncio yourself")

questions = ["Capital of Japan? One word.", "Capital of Kenya? One word.", "Capital of Peru? One word."]
replies = model.batch(questions, config={**CONFIG, "max_concurrency": 3})
# 🐍 PYTHON NOTE: {**CONFIG, "max_concurrency": 3} copies CONFIG and adds one more key.
print([r.text for r in replies])
# This is Phase 1 lesson 07 (asyncio.gather + Semaphore) in one line. There's also
# model.ainvoke / astream / abatch for async code (you'll use them in FastAPI, Phase 7).

trace.show_totals("Lesson 01 totals")

# 💡 THE BIG IDEA: invoke / stream / batch (and their async a-versions) exist on EVERY
# LangChain component: models, prompts, parsers, retrievers, chains, agents. That shared
# interface is called a "Runnable", and it's why you can pipe components together (lesson 02).

# 🧪 TRY:
#   1. Change MODEL in .env to claude-haiku-5-5 and compare the same answers and the cost.
#   2. Print `reply` itself (not .text). What extra fields do you see? Find `id`.
#   3. Pass max_tokens=20 to init_chat_model and look at stop_reason in the 📥 panel.
#   4. If you have an OpenAI key: `uv add langchain-openai`, set OPENAI_API_KEY in .env, and
#      run section 2 with init_chat_model("openai:gpt-5.1-mini"). Nothing else changes.
