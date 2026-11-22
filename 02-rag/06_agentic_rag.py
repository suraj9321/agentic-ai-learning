"""
Lesson 06: Agentic RAG, retrieval as a TOOL.

    Classic RAG (lesson 04):  always retrieve once  →  answer
    Agentic RAG (this one):   the MODEL decides whether to search, what to search for,
                              and whether to search again after reading the results

What you'll learn:
  - Wrap your retriever in a tool, then reuse the agent loop from Phase 1 lesson 06
  - Watch the model write its own search queries (built-in query rewriting!)
  - Multi-hop questions that need several searches + a calculation
  - The trade-off: more flexible and smarter, but slower and costlier than one-shot RAG

Run:  uv run python 02-rag/06_agentic_rag.py
"""

import os
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from course_utils import trace
from course_utils.rag import HybridRetriever, chunk_documents, format_context, load_documents
from course_utils.tools import calculator

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
client = anthropic.Anthropic()

# HybridRetriever = lesson 05's BM25 + vectors + RRF + rerank, packaged in course_utils/rag.py.
retriever = HybridRetriever(chunk_documents(load_documents(Path(__file__).parent / "data" / "nimbus")))


# ===========================================================================
# Tools
# ===========================================================================
def search_help_center(query: str, k: int = 4) -> str:
    """The retriever, exposed as a tool. Returns chunks in the same XML format as lesson 04."""
    hits = retriever.search(query, k=min(k, 8))
    trace.show_retrieval(query, hits, label="tool: search_help_center", score_name="rerank")
    return format_context(hits)


TOOLS = [
    {
        "name": "search_help_center",
        "description": (
            "Search Nimbus's help centre (pricing, billing, refunds, security, integrations, "
            "troubleshooting, onboarding). Returns the most relevant document chunks with ids "
            "and `updated` dates. Use short, specific queries, one topic per search. Search "
            "again with different words if the results don't answer the question."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "e.g. 'Microsoft Teams plan availability'"},
                "k": {"type": "integer", "description": "How many chunks to return (1-8, default 4)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "calculator",
        "description": "Evaluate an arithmetic expression. Use for ANY maths instead of computing in your head.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "e.g. '99 * 12 * 0.85'"}},
            "required": ["expression"],
        },
    },
]
TOOL_FUNCTIONS = {"search_help_center": search_help_center, "calculator": calculator}

SYSTEM = """You are Nimbus's customer support assistant.
Always use search_help_center before answering questions about Nimbus; never rely on memory.
If a question has several parts, search for each part separately.
Use the calculator for all arithmetic.
Cite chunk ids in square brackets, e.g. [pricing.md#2]. If documents disagree, trust the most
recently updated one. If the help centre doesn't answer something, say so."""


def run_tool(name: str, tool_input: dict) -> tuple[str, bool]:
    if name not in TOOL_FUNCTIONS:
        return f"Unknown tool: {name}", True
    try:
        return TOOL_FUNCTIONS[name](**tool_input), False
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}", True


# ===========================================================================
# The agent loop: the same as Phase 1 lesson 06 (compare them side by side!)
# ===========================================================================
def run_agent(question: str, max_steps: int = 10) -> str:
    messages = [{"role": "user", "content": question}]
    for step in range(1, max_steps + 1):
        trace.step(f"AGENT STEP {step}: THINK")
        request = dict(model=MODEL, max_tokens=16000, system=SYSTEM, tools=TOOLS, messages=messages)
        trace.show_request(request, label=f"agent step {step}")
        response = client.messages.create(**request)
        trace.show_response(response, label=f"agent step {step}")
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            trace.note(f"stop_reason is '{response.stop_reason}', so the loop ends after {step} model call(s).")
            return "".join(b.text for b in response.content if b.type == "text")

        trace.step(f"AGENT STEP {step}: ACT")
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                started = time.perf_counter()
                result, is_error = run_tool(block.name, block.input)
                trace.show_tool_call(block.name, block.input, result, is_error,
                                     seconds=time.perf_counter() - started)
                tool_results.append({"type": "tool_result", "tool_use_id": block.id,
                                     "content": result, "is_error": is_error})
        messages.append({"role": "user", "content": tool_results})
    return f"Stopped: reached max_steps={max_steps}."


if __name__ == "__main__":
    questions = [
        # Multi-hop: Teams availability (integrations) → plan price + seats (pricing) → maths
        "We're a team of 12 on Starter and we need Microsoft Teams recordings. Which plan do we "
        "need, and what would it cost per year if we pay annually?",
        # Two unrelated parts → the model should search twice with different queries
        "Two things: how do I fix ERR-4012, and how long do you keep our transcripts on Pro?",
    ]
    for q in questions:
        print("\n" + "=" * 70 + f"\n❓ {q}\n" + "=" * 70)
        print("\n✅ FINAL ANSWER:\n", run_agent(q))
        trace.show_totals("All calls so far")

    # 💡 WHY / WHEN agentic RAG:
    #   + handles multi-part and multi-hop questions, rephrases bad queries, skips retrieval
    #     for "hi!" or follow-ups it can already answer
    #   − 2-5x more LLM calls → slower and costlier; less predictable
    # Common in practice: one-shot RAG for a simple FAQ bot, agentic RAG for research-style
    # assistants. In Phase 4 you'll build both as LangGraph graphs, and a hybrid ("route
    # simple questions to one-shot RAG, hard ones to the agent").

# 🧪 TRY:
#   1. Compare the token totals above with lesson 04's single RAG calls.
#   2. Remove "search for each part separately" from SYSTEM. Does the model still split
#      the second question into two searches?
#   3. Ask something the docs can't answer ("Do you integrate with Webex?"). How many times
#      does it search before giving up? Would a max-searches limit be useful?
#   4. Go back to Phase 1's 06_agent_loop.py and replace its keyword search_docs with this
#      retriever. That's the fix for "search returns every document".
