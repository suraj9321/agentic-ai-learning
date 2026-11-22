"""
Lesson 06: An agent loop from scratch (the ReAct pattern).

    ReAct = REason + ACT. The model thinks, acts (calls a tool), observes the result,
    and repeats until it can answer.

        ┌──────────────────────────────────────────────┐
        │  call model with messages + tools            │
        │        │                                     │
        │        ▼                                     │
        │  stop_reason == "tool_use"? ──no──► DONE     │
        │        │ yes                                 │
        │        ▼                                     │
        │  run each requested tool                     │
        │  append assistant turn + tool results        │
        │        │                                     │
        └────────┘ (loop)                              │

That's it. Every agent framework (LangChain's create_agent, LangGraph's ReAct agent,
OpenAI Agents SDK, ...) is this loop plus extras: memory, streaming, retries, tracing.
After this lesson you can say in an interview: "I've built one from scratch."

Run:  uv run python 01-llm-basics/06_agent_loop.py
"""

import ast
import operator
import os
import time

import anthropic
from dotenv import load_dotenv

# Our tracing helper (course_utils/trace.py): shows every request, response and tool run.
# Set TRACE=brief or TRACE=off in .env for less output.
from course_utils import trace

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
client = anthropic.Anthropic()


# ===========================================================================
# Tools
# ===========================================================================
def calculator(expression: str) -> str:
    """Safely evaluate a maths expression like '(1200 * 0.18) / 12'."""
    # ⚠️ GOTCHA: NEVER use Python's eval() on model output. The model (or a prompt
    # injection inside a web page it read) could send "__import__('os').system('rm -rf ~')".
    # Instead we parse the expression into a syntax tree and allow only arithmetic.
    allowed = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.Mod: operator.mod,
    }

    # 🐍 PYTHON NOTE: a function defined inside a function (a "nested function").
    # It calls itself (recursion) to walk the tree: (1 + 2) * 3 → Mult(Add(1, 2), 3).
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in allowed:
            return allowed[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed:
            return allowed[type(node.op)](_eval(node.operand))
        raise ValueError(f"Unsupported expression: {ast.dump(node)[:60]}")

    return str(_eval(ast.parse(expression, mode="eval").body))


# A tiny fake "company knowledge base" so the agent has something to look up.
KNOWLEDGE_BASE = {
    "pricing": "Starter plan: $29/month for 3 seats. Pro plan: $99/month for 10 seats. Extra seats: $8/seat/month on Pro only.",
    "refunds": "Refunds are available within 14 days of purchase. Annual plans get a 15% discount.",
    "limits": "Starter: 1,000 AI tasks/month. Pro: 10,000 AI tasks/month. Overage: $0.02 per task.",
}


def search_docs(query: str) -> str:
    """Keyword search over the knowledge base (a stand-in for real RAG in Phase 2)."""
    words = query.lower().split()
    hits = [text for topic, text in KNOWLEDGE_BASE.items() if any(w in topic or w in text.lower() for w in words)]
    return "\n".join(hits) if hits else "No matching documents."


TOOLS = [
    {
        "name": "search_docs",
        "description": (
            "Search the company's internal documentation (pricing, refunds, usage limits). "
            "Use this before answering any question about our plans or policies. Never guess them."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "A few keywords, e.g. 'pricing seats'"}},
            "required": ["query"],
        },
    },
    {
        "name": "calculator",
        "description": "Evaluate an arithmetic expression. Use for ANY maths instead of computing in your head.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "e.g. '99 + 5 * 8'"}},
            "required": ["expression"],
        },
    },
]
TOOL_FUNCTIONS = {"search_docs": search_docs, "calculator": calculator}


def run_tool(name: str, tool_input: dict) -> tuple[str, bool]:
    """Run one tool. Returns (result_text, is_error)."""
    # 🐍 PYTHON NOTE: `tuple[str, bool]` means the function returns two values, e.g.
    # `return "42", False`, and the caller writes `text, is_error = run_tool(...)`.
    if name not in TOOL_FUNCTIONS:
        return f"Unknown tool: {name}", True
    try:
        return TOOL_FUNCTIONS[name](**tool_input), False
    except Exception as e:  # catch anything the tool raises
        # 💡 WHY: don't crash the agent when a tool fails. Send the error back to the
        # model. It can often fix its own mistake (e.g. correct a bad expression) and retry.
        return f"Error: {type(e).__name__}: {e}", True


# ===========================================================================
# The agent loop
# ===========================================================================
SYSTEM = """You are a helpful sales assistant for an AI-automation SaaS company.
Use search_docs to look up facts and calculator for every calculation.
Be concise. Show the final numbers clearly."""


def run_agent(question: str, max_steps: int = 10) -> str:
    messages = [{"role": "user", "content": question}]
    total_in = total_out = 0  # 🐍 chained assignment: both start at 0

    # 🐍 PYTHON NOTE: range(1, n + 1) gives 1, 2, ..., n.
    for step in range(1, max_steps + 1):
        trace.step(f"AGENT STEP {step}: THINK (ask the model what to do next)")

        # 🐍 PYTHON NOTE: we build the request as a dict, then unpack it with **request.
        # client.messages.create(**request) == client.messages.create(model=..., messages=...)
        # Having it in a variable lets us print exactly what we send.
        request = dict(model=MODEL, max_tokens=16000, system=SYSTEM, tools=TOOLS, messages=messages)
        trace.show_request(request, label=f"agent step {step}")
        response = client.messages.create(**request)
        trace.show_response(response, label=f"agent step {step}")

        total_in += response.usage.input_tokens
        total_out += response.usage.output_tokens

        # Always append the model's turn (with ALL its blocks) to the history.
        messages.append({"role": "assistant", "content": response.content})

        # ---- Decide whether to stop -----------------------------------------
        if response.stop_reason != "tool_use":
            # ⚠️ GOTCHA: handle every stop reason, not just the happy path.
            if response.stop_reason == "max_tokens":
                print("  ⚠️ answer was cut off (max_tokens)")
            elif response.stop_reason == "refusal":
                print("  ⚠️ model declined this request")
            trace.note(f"stop_reason is '{response.stop_reason}', not 'tool_use', so the loop ends here.")
            print(f"  📊 {step} model calls, {total_in} input + {total_out} output tokens")
            return "".join(b.text for b in response.content if b.type == "text")

        # ---- Run every requested tool ------------------------------------------
        trace.step(f"AGENT STEP {step}: ACT (our code runs the requested tools)")
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                started = time.perf_counter()
                result, is_error = run_tool(block.name, block.input)
                trace.show_tool_call(block.name, block.input, result, is_error,
                                     seconds=time.perf_counter() - started)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                    "is_error": is_error,
                })

        trace.note(f"OBSERVE: sending {len(tool_results)} tool result(s) back as a 'user' message, then looping.")
        # All results in ONE user message, then loop: the model sees what happened.
        messages.append({"role": "user", "content": tool_results})

    # 💡 WHY a step limit: without one, a confused agent can loop forever and burn money.
    # Every production agent has a max-iterations guard (LangGraph calls it recursion_limit).
    return f"Stopped: reached max_steps={max_steps} without a final answer."


# ===========================================================================
# Try it
# ===========================================================================
if __name__ == "__main__":
    questions = [
        # Needs: search → calculator (multi-step)
        "A customer has a team of 14. What would Pro cost them per year, including extra seats?",
        # Needs: search twice (pricing + limits) → calculator
        "If a Starter customer runs 1,800 AI tasks this month, what's their total bill?",
    ]
    for q in questions:
        print("\n" + "=" * 70)
        print("❓", q)
        print("=" * 70)
        answer = run_agent(q)
        print("\n✅ FINAL ANSWER:\n", answer)
        trace.show_totals("All calls so far")

    # Interactive mode
    print("\n\nAsk your own questions (empty line to quit):")
    while q := input("\n❓ ").strip():
        # 🐍 PYTHON NOTE: `:=` is the "walrus operator". It assigns AND tests in one go:
        # read input into q, and keep looping while q isn't empty.
        print("\n✅", run_agent(q))

# 🧪 TRY:
#   1. Ask "What's 15% off the annual Pro price?" and watch the chain of tool calls.
#   2. Make calculator raise on purpose (e.g. ask it to compute "2 ** 'a'") and watch the
#      model recover from the error.
#   3. Set max_steps=1. What happens? Why must real agents have this limit?
#   4. Add a new tool `get_customer(name)` that returns fake account info, and ask:
#      "How much will Acme Corp pay next month?"
#   5. Set TRACE=brief in .env and run again: one line per call. Good once you understand the flow.
#   6. CHALLENGE: close this file and rewrite run_agent() from memory. If you can, you
#      understand agents better than most people who only use frameworks.
