"""
Lesson 06: Middleware, customising what create_agent does at each step.

    create_agent's loop:     before_model → [model call] → after_model → [tool calls] → repeat
    Middleware = your code plugged into those points, like the middleware in a web framework.

What you'll learn:
  - Built-in guards: limit model calls and tool calls (cost and runaway-loop protection)
  - @wrap_model_call: model ROUTING, a cheap model for easy turns and a smart one for hard ones
  - @wrap_tool_call: a tool guardrail that blocks dangerous actions
  - PIIMiddleware: redact emails before the model sees them
  - SummarizationMiddleware: keep long conversations within budget

Everything here is something you'd otherwise hand-code inside your Phase 1 loop. Seeing
each as a hook helps you understand LangGraph (Phase 4), where you control the graph yourself.

Run:  uv run python 03-langchain/06_middleware.py
"""

import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    PIIMiddleware,
    SummarizationMiddleware,
    ToolCallLimitMiddleware,
    before_model,
    wrap_model_call,
    wrap_tool_call,
)
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from course_utils import trace
from course_utils.lc_trace import Tracer

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
smart = init_chat_model(f"anthropic:{MODEL}", max_tokens=16000)
cheap = init_chat_model("anthropic:claude-haiku-5-5", max_tokens=4000)
CONFIG = {"callbacks": [Tracer()]}


@tool
def lookup_order(order_id: str) -> str:
    """Look up a customer's order by id, e.g. 'A-1001'."""
    orders = {"A-1001": "Pro plan, annual, paid $1,009.80 on 2026-11-02, status: active"}
    return orders.get(order_id, f"No order with id {order_id}")


@tool
def issue_refund(order_id: str, amount_usd: float) -> str:
    """Refund an amount (USD) for an order. Irreversible."""
    return f"Refunded ${amount_usd:.2f} for order {order_id}."


# ---------------------------------------------------------------------------
# 1. Built-in limits
# ---------------------------------------------------------------------------
trace.step("1. Call limits: stop runaway agents")

limited = create_agent(
    smart, tools=[lookup_order],
    middleware=[
        ModelCallLimitMiddleware(run_limit=6, exit_behavior="end"),         # max 6 model calls per run
        ToolCallLimitMiddleware(tool_name="lookup_order", run_limit=2),     # max 2 lookups per run
    ],
)
r = limited.invoke({"messages": [{"role": "user", "content":
                                  "Look up orders A-1001, A-1002, A-1003 and A-1004 one at a time, then summarise."}]},
                   config=CONFIG)
print("\n🤖", r["messages"][-1].text[:400])
# Phase 1's max_steps, but per tool and with a choice of behaviour.
# Look at the 📤 panels: after 2 lookups, the next lookup gets an error ToolMessage
# instead of running, and the model has to answer with what it has.
# 🧪 Set ModelCallLimitMiddleware(run_limit=2) to see the other guard stop the run instead.


# ---------------------------------------------------------------------------
# 2. Model routing with @wrap_model_call
# ---------------------------------------------------------------------------
trace.step("2. Route easy turns to a cheap model")


@wrap_model_call
def route_by_difficulty(request, handler):
    """Runs AROUND every model call. `handler(request)` performs the actual call."""
    last = request.messages[-1]
    is_short_question = last.type == "human" and len(last.text) < 60
    chosen = cheap if is_short_question else smart
    print(f"   🔀 router: last message is {last.type} ({len(last.text)} chars) → {chosen.model}")
    # (Our simple rule only routes on human messages; after a tool result we use the smart model.)
    # request.override(...) returns a COPY of the request with some fields changed.
    return handler(request.override(model=chosen))


router_agent = create_agent(smart, tools=[lookup_order], middleware=[route_by_difficulty])
for q in ["What's order A-1001?",
          "A customer on order A-1001 says the annual discount was applied wrongly and wants to know "
          "exactly what they should have paid for Pro at $99/month with 15% off. Explain the maths."]:
    r = router_agent.invoke({"messages": [{"role": "user", "content": q}]}, config=CONFIG)
    print("🤖", r["messages"][-1].text[:200], "...\n")
# 💡 WHY: Haiku costs 1/20th of Opus. If 60% of your traffic is simple, routing cuts the bill
# dramatically. Real routers use a classifier (an LLM call or a small model) instead of length.
# Watch the 📥 panels: the tokens and cost differ per model.


# ---------------------------------------------------------------------------
# 3. A tool guardrail with @wrap_tool_call
# ---------------------------------------------------------------------------
trace.step("3. Block dangerous tool calls")

REFUND_LIMIT = 100


@wrap_tool_call
def refund_guard(request, handler):
    """Runs AROUND every tool call. We can inspect the args and refuse."""
    call = request.tool_call  # {"name", "args", "id"}
    if call["name"] == "issue_refund" and call["args"].get("amount_usd", 0) > REFUND_LIMIT:
        print(f"   🛑 guard: blocked refund of ${call['args']['amount_usd']}")
        return ToolMessage(
            content=f"DENIED: refunds over ${REFUND_LIMIT} need human approval. Tell the customer a "
                    "teammate will review it within 1 business day.",
            tool_call_id=call["id"], status="error")
    return handler(request)  # allowed: run the tool normally


support = create_agent(smart, tools=[lookup_order, issue_refund], middleware=[refund_guard],
                       system_prompt="You are a support agent who can look up orders and issue refunds.")
r = support.invoke({"messages": [{"role": "user", "content":
                                  "I want a full refund for order A-1001, I signed up 3 days ago."}]}, config=CONFIG)
print("🤖", r["messages"][-1].text)
# ⚠️ GOTCHA: NEVER rely on the system prompt alone ("don't refund over $100"). A prompt
# injection or a confused model can ignore it. Enforce rules in CODE, around the tool.
# Phase 4 turns "needs human approval" into a real pause-and-approve step (interrupt).


# ---------------------------------------------------------------------------
# 4. PII redaction
# ---------------------------------------------------------------------------
trace.step("4. PIIMiddleware: redact emails before the model sees them")

pii_agent = create_agent(cheap, tools=[], middleware=[PIIMiddleware("email", strategy="redact")])
r = pii_agent.invoke({"messages": [{"role": "user", "content":
                                    "Hi, I'm jane.doe@acme.com, please repeat my email back to me."}]}, config=CONFIG)
print("🤖", r["messages"][-1].text)
# Look at the 📤 panel: the model received [REDACTED_EMAIL], not the address. Useful when
# you're not allowed to send personal data to a third-party model provider.


# ---------------------------------------------------------------------------
# 5. Summarisation for long conversations
# ---------------------------------------------------------------------------
trace.step("5. SummarizationMiddleware")


@before_model
def show_history_size(state, runtime):
    """Runs before every model call. Returning None means 'change nothing'."""
    print(f"   📏 the model is about to see {len(state['messages'])} messages")
    return None


chat = create_agent(
    cheap, tools=[],
    middleware=[
        # When history exceeds 6 messages, replace older ones with a summary, keeping the last 2.
        SummarizationMiddleware(model=cheap, trigger=("messages", 6), keep=("messages", 2)),
        show_history_size,
    ],
    checkpointer=InMemorySaver(),
    system_prompt="You are a friendly assistant. One sentence per answer.",
)
thread = {"configurable": {"thread_id": "long-chat"}, "callbacks": [Tracer()]}
for msg in ["My name is Suraj.", "I'm building a startup for AI meeting notes.", "Our first customer is a law firm.",
            "We use LangGraph.", "What do you know about me and my startup?"]:
    r = chat.invoke({"messages": [{"role": "user", "content": msg}]}, config=thread)
    print(f"🧑 {msg}\n🤖 {r['messages'][-1].text}")
# Watch 📏: the count grows, then drops after the summary is created (look for the summary
# message in the 📤 panel). Does the last answer still remember the details?
# 💡 WHY: without this, cost and latency grow with every turn (Phase 1 lesson 02). The trade-off
# is that summaries lose detail.

trace.show_totals("Lesson 06 totals")

# 🧪 TRY:
#   1. Change REFUND_LIMIT to 2000 and re-run section 3. What does the agent do now?
#   2. Add PIIMiddleware("credit_card", strategy="block") and send a fake card number
#      (4111 1111 1111 1111). What happens?
#   3. Write an @after_model middleware that prints the tokens used by each call
#      (state["messages"][-1].usage_metadata).
#   4. Make the router use an LLM classifier: ask `cheap` "Is this question simple or complex?"
#      with structured output, and route on the answer.
