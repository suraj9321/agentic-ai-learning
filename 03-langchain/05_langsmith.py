"""
Lesson 05: LangSmith, observability for LLM apps.

    Your local Tracer prints panels in the terminal. LangSmith records the SAME events (it uses
    the same callback system) and keeps them in a web UI: a searchable tree of every run, with
    inputs, outputs, latency, tokens, cost and errors. Teams use it to debug production.

What you'll learn:
  - Turning on tracing with 3 environment variables (no code changes for LangChain)
  - Naming runs and adding tags + metadata so you can FIND them later
  - @traceable: trace your own Python functions (retrieval, pre/post-processing)
  - wrap_anthropic: trace raw Anthropic SDK calls (your Phase 1 code!)
  - Collecting user feedback (👍/👎) on a run
  - 🐛 Debugging a broken agent by reading its trace

SETUP (5 minutes, free):
  1. Sign up at https://smith.langchain.com
  2. Settings → API Keys → Create API Key
  3. In .env, uncomment and fill in:
        LANGSMITH_TRACING=true
        LANGSMITH_API_KEY=lsv2_...
        LANGSMITH_PROJECT=agentic-ai-learning
  The lesson also runs WITHOUT LangSmith (you'll still see the local trace panels).

Run:  uv run python 03-langchain/05_langsmith.py
"""

import os
import uuid
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langsmith import Client, traceable
from langsmith.wrappers import wrap_anthropic

from course_utils import trace
from course_utils.lc_trace import Tracer
from course_utils.rag import HybridRetriever, chunk_documents, format_context, load_documents

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
model = init_chat_model(f"anthropic:{MODEL}", max_tokens=16000)
NIMBUS = Path(__file__).parent.parent / "02-rag" / "data" / "nimbus"

LANGSMITH_ON = os.getenv("LANGSMITH_TRACING", "").lower() == "true" and bool(os.getenv("LANGSMITH_API_KEY"))
PROJECT = os.getenv("LANGSMITH_PROJECT", "default")

trace.step("0. Is LangSmith on?")
if LANGSMITH_ON:
    print(f"✅ LangSmith tracing is ON. Runs go to project '{PROJECT}' at https://smith.langchain.com")
else:
    print("⚪ LangSmith is OFF (see SETUP at the top of this file). Everything still runs;\n"
          "   you'll see local trace panels only. Come back once you've set it up: it's worth it.")
# 💡 WHY env vars: tracing is configuration, not code. The same app can trace in staging and
# sample 10% of traffic in production, just by changing environment variables.


# ---------------------------------------------------------------------------
# 1. Trace a LangChain agent with a name, tags and metadata
# ---------------------------------------------------------------------------
trace.step("1. A named, tagged, traced agent run")

retriever = HybridRetriever(chunk_documents(load_documents(NIMBUS)))


@tool
def search_help_center(query: str) -> str:
    """Search Nimbus's help centre. Use short, specific queries, one topic per search."""
    return format_context(retriever.search(query, k=4))


agent = create_agent(model, tools=[search_help_center],
                     system_prompt="You are Nimbus support. Search before answering. Be brief.")

run_id = uuid.uuid4()  # we choose the run id up front so we can attach feedback to it later
config = {
    "callbacks": [Tracer()],
    "run_name": "support-agent",           # the name shown in LangSmith instead of "LangGraph"
    "tags": ["lesson-05", "support"],      # filter by tag in the UI
    "metadata": {"user_id": "u_42", "plan": "starter", "app_version": "0.3.1"},  # filter/group by these
    "run_id": run_id,
}
result = agent.invoke({"messages": [{"role": "user", "content": "Can I export summaries to Notion on Starter?"}]},
                      config=config)
print("\n✅", result["messages"][-1].text)
# In LangSmith: open the project → click "support-agent" → you'll see a TREE:
#   support-agent → model (ChatAnthropic) → tools → search_help_center → model ...
# Click any node to see its exact inputs/outputs. Filter runs by tag or metadata
# (e.g. all runs for plan=starter), and sort by latency or cost to find the slow/expensive ones.


# ---------------------------------------------------------------------------
# 2. @traceable: your own functions become nodes in the trace tree
# ---------------------------------------------------------------------------
trace.step("2. @traceable on plain Python functions")

# Not everything is a LangChain component. Your retrieval, validation or business logic
# can be traced too. run_type="retriever" makes LangSmith display the output as documents.
@traceable(run_type="retriever", name="hybrid_search")
def hybrid_search(query: str) -> list[dict]:
    hits = retriever.search(query, k=3)
    # LangSmith renders retriever runs nicely when they return page_content + metadata.
    return [{"page_content": h["text"], "metadata": {"id": h["id"], "score": h["score"]}} for h in hits]


@traceable(name="answer_ticket", tags=["pipeline"])
def answer_ticket(ticket: str) -> str:
    """A hand-written pipeline: retrieve → answer. In LangSmith this is ONE tree with 2 children."""
    docs = hybrid_search(ticket)
    context = "\n\n".join(f"[{d['metadata']['id']}] {d['page_content']}" for d in docs)
    reply = model.invoke(f"Answer from these docs only, citing [ids]:\n{context}\n\nQuestion: {ticket}",
                         config={"callbacks": [Tracer()]})
    return reply.text


print("💬", answer_ticket("My upload fails with ERR-5003"))
# 🐍 PYTHON NOTE: @traceable(...) is a decorator that takes arguments: traceable(name=...) returns
# the real decorator, which then wraps the function. Same `@` syntax as lesson 03.


# ---------------------------------------------------------------------------
# 3. wrap_anthropic: trace raw SDK calls (no LangChain needed)
# ---------------------------------------------------------------------------
trace.step("3. wrap_anthropic: tracing Phase 1-style code")

client = wrap_anthropic(anthropic.Anthropic())  # same client, now every call is traced
request = dict(model=MODEL, max_tokens=1000,
               messages=[{"role": "user", "content": "Name one LLM observability tool other than LangSmith. One line."}])
trace.show_request(request, label="raw SDK, wrapped")
response = client.messages.create(**request)
trace.show_response(response, label="raw SDK, wrapped")
# 💡 WHY this matters: LangSmith isn't only for LangChain. Any app (raw SDK, other frameworks)
# can send traces. Its competitors (Langfuse, Arize Phoenix, Braintrust...) do the same,
# often via OpenTelemetry. Phase 5 compares them.


# ---------------------------------------------------------------------------
# 4. User feedback on a run
# ---------------------------------------------------------------------------
trace.step("4. Attaching user feedback to a run")

if LANGSMITH_ON:
    ls = Client()
    # In a real app this happens when the user clicks 👍/👎 next to the answer.
    ls.create_feedback(run_id, key="user_rating", score=1, comment="Helpful, correct answer")
    print(f"👍 feedback attached to run {run_id}. In LangSmith, filter runs by feedback score to "
          "find the answers users disliked: your best source of eval examples (Phase 5).")
else:
    print("(skipped: needs LangSmith) In an app, a 👍/👎 button calls "
          "Client().create_feedback(run_id, key='user_rating', score=1).")


# ---------------------------------------------------------------------------
# 5. 🐛 Debug this agent
# ---------------------------------------------------------------------------
trace.step("5. 🐛 Find the bug using the trace")

PLAN_PRICES = {"Free": 0, "Starter": 29, "Pro": 99}


@tool
def get_plan_price(plan: str) -> str:
    """Get the monthly price in USD of a Nimbus plan: Free, Starter, Pro or Enterprise."""
    price = PLAN_PRICES.get(plan.title().replace("Plan", "").strip(), PLAN_PRICES["Starter"])
    return f"{price} USD per month"


@tool
def seat_info(plan: str) -> str:
    """How many seats a plan includes and what extra seats cost."""
    return {"starter": "3 seats included, no extra seats",
            "pro": "10 seats included, extra seats $8 per seat per month"}.get(plan.lower(), "unknown plan")


buggy = create_agent(model, tools=[get_plan_price, seat_info],
                     system_prompt="You are a sales assistant. Use the tools for every fact. Be brief.")
r = buggy.invoke({"messages": [{"role": "user", "content":
                                "What's the monthly price for Enterprise, and for a team of 12 on the professional plan?"}]},
                 config={"callbacks": [Tracer()], "run_name": "buggy-sales-agent", "tags": ["lesson-05", "bug-hunt"]})
print("\n🤖", r["messages"][-1].text)
print("""
🐛 Something in the answer above is WRONG. Check it against 02-rag/data/nimbus/pricing.md.
   (A good model may even sound unsure. A weaker one states it confidently.) Your job:
   1. Find the ⚙️ tool panels above (or the 'buggy-sales-agent' run in LangSmith).
   2. For each tool call: what did the model send, and what came back?
   3. Which line of get_plan_price causes it? Why is this kind of bug dangerous?
   (The answer is at the bottom of this file. Don't peek until you've looked at the trace!)""")

trace.show_totals("Lesson 05 totals")

# 🧪 TRY:
#   1. In LangSmith, open a run and click "Playground": edit the prompt and re-run that exact
#      model call. Great for debugging a single bad step.
#   2. Set LANGSMITH_TRACING=false and run again: nothing is sent. In production, many teams
#      trace a sample: `LANGSMITH_TRACING_SAMPLING_RATE=0.1` (10%).
#   3. Add metadata={"customer": ...} to a run, then filter by it in the UI.
#   4. Fix the bug, re-run, and compare the two runs side by side in LangSmith.

# ─────────────────────────────────────────────────────────────────────────────
# 🐛 ANSWER: get_plan_price silently falls back to the Starter price for any plan it doesn't
# recognise: `.get(..., PLAN_PRICES["Starter"])`. "Enterprise" → 29 USD (and if the model had
# sent "Professional" instead of "Pro", that would be 29 USD too). The model receives a
# plausible number and has no reliable way to know it's wrong.
# A silent fallback in a tool is worse than an error: return "Unknown plan 'X'. Valid plans:
# Free, Starter, Pro, Enterprise (custom pricing)" instead, so the model can correct itself.
# Only the trace shows this: the final answer looks perfectly confident.
