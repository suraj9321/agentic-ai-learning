"""
Lesson 03: Tools and agents in LangChain.

What you'll learn:
  - Python decorators, then LangChain's @tool decorator (a function → a tool with a schema)
  - bind_tools() + a hand-written loop: Phase 1's agent loop with LangChain types
  - create_agent(): the same loop, prebuilt (it's a LangGraph graph under the hood)
  - Watching an agent step by step with stream(); conversation memory with a checkpointer

We reuse Phase 2: the help-centre retriever (hybrid + rerank) becomes a tool.

Run:  uv run python 03-langchain/03_tools_and_agents.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from course_utils import trace
from course_utils import tools as course_tools
from course_utils.lc_trace import Tracer
from course_utils.rag import HybridRetriever, chunk_documents, format_context, load_documents

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
model = init_chat_model(f"anthropic:{MODEL}", max_tokens=16000)
CONFIG = {"callbacks": [Tracer()]}

NIMBUS = Path(__file__).parent.parent / "02-rag" / "data" / "nimbus"
retriever = HybridRetriever(chunk_documents(load_documents(NIMBUS)))


# ---------------------------------------------------------------------------
# 1. Decorators, then @tool
# ---------------------------------------------------------------------------
trace.step("1. @tool: a Python function becomes a tool")

# 🐍 PYTHON NOTE: DECORATORS. A decorator is a function that takes a function and returns
# a new (usually wrapped) one. Writing `@loud` above `def f` means `f = loud(f)`.
def loud(func):
    def wrapper(*args, **kwargs):  # *args/**kwargs: accept any arguments and pass them on
        print(f"  (calling {func.__name__})")
        return func(*args, **kwargs)
    return wrapper


@loud
def greet(name: str) -> str:
    return f"hi {name}"


print(greet("Suraj"))
# LangChain's @tool works the same way, but instead of wrapping the call it builds a Tool
# object, reading the NAME from the function name, the DESCRIPTION from the docstring, and
# the INPUT SCHEMA from the type hints. That's the JSON schema you wrote by hand in Phase 1.


@tool
def search_help_center(query: str) -> str:
    """Search Nimbus's help centre (pricing, billing, refunds, security, integrations,
    troubleshooting). Use short, specific queries, one topic per search."""
    return format_context(retriever.search(query, k=4))


@tool
def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression like '(99 + 2 * 8) * 12'. Use for ALL maths."""
    return course_tools.calculator(expression)  # the safe AST calculator from Phase 1


TOOLS = [search_help_center, calculator]
for t in TOOLS:
    print(f"\ntool: {t.name}\n  description: {t.description[:80]}...\n  args schema: {t.args}")
# ⚠️ GOTCHA: the docstring IS the prompt that tells the model when to use the tool. A vague
# docstring → the model picks the wrong tool or none. Write it like instructions.


# ---------------------------------------------------------------------------
# 2. bind_tools + the agent loop by hand
# ---------------------------------------------------------------------------
trace.step("2. bind_tools(): the Phase 1 loop, in LangChain types")

model_with_tools = model.bind_tools(TOOLS)  # sends the tool schemas with every call
tools_by_name = {t.name: t for t in TOOLS}

messages = [
    SystemMessage("You are Nimbus support. Look facts up with search_help_center; use the calculator for maths."),
    HumanMessage("What does Pro cost per year for 12 people if we pay annually?"),
]
for step in range(1, 8):
    ai = model_with_tools.invoke(messages, config=CONFIG)
    messages.append(ai)
    if not ai.tool_calls:  # Phase 1: `if response.stop_reason != "tool_use"`
        break
    for call in ai.tool_calls:  # each call is a dict: {"name", "args", "id"}
        result = tools_by_name[call["name"]].invoke(call["args"], config=CONFIG)
        # ToolMessage = Phase 1's {"type": "tool_result", "tool_use_id": ..., "content": ...}
        messages.append(ToolMessage(content=result, tool_call_id=call["id"]))
print(f"\n✅ (by hand, {step} model calls) {messages[-1].text}")


# ---------------------------------------------------------------------------
# 3. create_agent: the same thing, prebuilt
# ---------------------------------------------------------------------------
trace.step("3. create_agent()")

agent = create_agent(
    model,
    tools=TOOLS,
    system_prompt="You are Nimbus support. Look facts up with search_help_center; use the calculator for maths. Cite chunk ids.",
)
result = agent.invoke(
    {"messages": [{"role": "user", "content": "How do I fix ERR-4012, and is Teams supported on Starter?"}]},
    config=CONFIG,
)
# The result is the agent's final STATE: a dict whose "messages" key holds the whole history.
print("\nmessage types:", [type(m).__name__ for m in result["messages"]])
print("\n✅", result["messages"][-1].text)
print("\nagent type:", type(agent).__name__)
# 💡 WHY "CompiledStateGraph": create_agent builds a LangGraph graph with two nodes,
# "model" and "tools", and an edge that loops back while the model asks for tools. Exactly
# your Phase 1 loop. Print the graph:
print(agent.get_graph().draw_mermaid())  # paste into https://mermaid.live to see it drawn


# ---------------------------------------------------------------------------
# 4. Watch it step by step with stream()
# ---------------------------------------------------------------------------
trace.step("4. agent.stream(stream_mode='updates')")

question = {"messages": [{"role": "user", "content": "Do students get a discount? What would Starter cost a student per year, monthly billing?"}]}
for update in agent.stream(question, stream_mode="updates", config={"callbacks": []}):
    # Each update is {node_name: state_changes}. We turned the tracer off here (callbacks=[])
    # so you can see the raw stream: one line per node that ran.
    for node, changes in update.items():
        last = changes["messages"][-1]
        what = (f"tool_calls={[c['name'] for c in last.tool_calls]}" if getattr(last, "tool_calls", None)
                else f"{type(last).__name__}: {last.text[:90]!r}")
        print(f"  ▶ node '{node}' → {what}")
# 💡 WHY: stream_mode="updates" is how you show progress in a UI ("Searching the help
# centre..."). stream_mode="messages" streams tokens. You'll use both in Phase 4 and 7.


# ---------------------------------------------------------------------------
# 5. Memory across turns: a checkpointer + thread_id
# ---------------------------------------------------------------------------
trace.step("5. Conversation memory with a checkpointer")

memory_agent = create_agent(model, tools=TOOLS, checkpointer=InMemorySaver(),
                            system_prompt="You are Nimbus support. Be brief.")
thread = {"configurable": {"thread_id": "customer-42"}, "callbacks": [Tracer()]}
memory_agent.invoke({"messages": [{"role": "user", "content": "Hi, we're on the Starter plan with 3 people."}]}, config=thread)
r = memory_agent.invoke({"messages": [{"role": "user", "content": "How long are our transcripts kept?"}]}, config=thread)
print("\n✅", r["messages"][-1].text)
# We only sent the NEW message, but the agent knew we're on Starter. The checkpointer saved
# the state after the first call under thread_id "customer-42" and loaded it for the second.
# (Look at the 📤 panel of the second call: the earlier messages are there.)
# A different thread_id = a separate conversation. InMemorySaver forgets everything when the
# program exits; SqliteSaver / PostgresSaver persist it (Phase 4 and 7).

trace.show_totals("Lesson 03 totals")

# 🧪 TRY:
#   1. Count the lines of section 2 vs Phase 1's run_agent(). What did LangChain save you?
#      What does create_agent hide that you can no longer see (without tracing)?
#   2. Make the calculator docstring vague ("does stuff") and ask a maths question. Does the
#      model still use it?
#   3. Make a tool raise an exception. What does create_agent do with it? (Look for the
#      ToolMessage with status="error" in the trace.)
#   4. Use a different thread_id for the second question in section 5. What changes?
