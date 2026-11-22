"""
🛠 Phase 3 mini-project: the Phase 1 research assistant, rebuilt with LangChain, plus Phase 2's
document search.

Tools:
  web_search      Anthropic's server-side web search (runs on Anthropic's servers)
  search_my_docs  hybrid search + rerank over a folder of your PDFs/notes (Phase 2)
  calculator      the safe calculator from Phase 1
  list_files / read_file / write_report   sandboxed to ./workspace

Features: conversation memory (checkpointer + thread_id), call limits (middleware), local trace
panels, and LangSmith traces if you've set it up (lesson 05).

Run:
    uv run python 03-langchain/project/research_agent.py                 # docs: 02-rag/project/docs
    uv run python 03-langchain/project/research_agent.py ~/my-pdfs       # any folder

Commands: /cost  /reset (new conversation)  /quit
"""

import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from course_utils import trace
from course_utils import tools as course_tools
from course_utils.lc_trace import Tracer
from course_utils.rag import HybridRetriever, chunk_documents, load_documents

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
HERE = Path(__file__).parent
WORKSPACE = (HERE / "workspace").resolve()
WORKSPACE.mkdir(exist_ok=True)
DOCS = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else HERE.parent.parent / "02-rag" / "project" / "docs"


# ===========================================================================
# Tools
# ===========================================================================
_docs = load_documents(DOCS)
_retriever = HybridRetriever(chunk_documents(_docs, max_chars=800, overlap=120)) if _docs else None


@tool
def search_my_docs(query: str) -> str:
    """Search the user's own documents (PDFs, notes). Use for questions about their files,
    company or projects. Returns chunks with [file p.N] labels to cite."""
    if _retriever is None:
        return f"No documents found in {DOCS}."
    hits = _retriever.search(query, k=5)
    return "\n\n".join(f"[{h['source']}{' p.' + str(h['page']) if h.get('page') else ''}]\n{h['text']}"
                       for h in hits)


@tool
def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression, e.g. '(1200 * 0.18) / 12'. Use for all maths."""
    return course_tools.calculator(expression)


def _safe_path(relative: str) -> Path:
    path = (WORKSPACE / relative).resolve()
    if not path.is_relative_to(WORKSPACE):
        raise PermissionError(f"Access outside the workspace is not allowed: {relative}")
    return path


@tool
def list_files() -> str:
    """List the files in the user's workspace folder."""
    files = [str(p.relative_to(WORKSPACE)) for p in WORKSPACE.rglob("*") if p.is_file()]
    return "\n".join(files) or "(workspace is empty)"


@tool
def read_file(path: str) -> str:
    """Read a text file from the workspace, path relative to the workspace (e.g. 'notes.md')."""
    text = _safe_path(path).read_text(encoding="utf-8")
    return text[:20_000] + (f"\n[...truncated, {len(text) - 20_000} more chars]" if len(text) > 20_000 else "")


@tool
def write_report(filename: str, content: str) -> str:
    """Save a markdown report to the workspace. Use only when the user asks to save/write/export.
    `content` is the full markdown, including source links."""
    filename = filename if filename.endswith(".md") else filename + ".md"
    _safe_path(filename).write_text(content, encoding="utf-8")
    return f"Saved {len(content)} characters to workspace/{filename}"


# A server tool is passed as a plain dict: LangChain hands it to Anthropic unchanged.
WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search", "max_uses": 5}

SYSTEM = f"""You are a research assistant for an AI engineer who is building a startup.
- For facts about the world (companies, prices, news, tools), use web_search and cite URLs.
- For anything about the user's own documents, use search_my_docs and cite [file p.N].
- Use the calculator for all arithmetic.
- Only write files when asked. Be concise and structured.
Documents available to search_my_docs: {', '.join(sorted({d['source'] for d in _docs})) or 'none'}."""


def build_agent():
    model = init_chat_model(f"anthropic:{MODEL}", max_tokens=16000)
    return create_agent(
        model,
        tools=[WEB_SEARCH, search_my_docs, calculator, list_files, read_file, write_report],
        system_prompt=SYSTEM,
        middleware=[
            ModelCallLimitMiddleware(run_limit=12, exit_behavior="end"),  # per question
            ToolCallLimitMiddleware(tool_name="search_my_docs", run_limit=6),
        ],
        checkpointer=InMemorySaver(),  # memory: one conversation per thread_id
    )
    # Compare with 01-llm-basics/project/research_assistant.py: no JSON schemas, no loop, no
    # message bookkeeping. But you only understand what this does because you built that one.


def main() -> None:
    agent = build_agent()
    thread_id = str(uuid.uuid4())
    print(f"🔎 Research agent ready. Docs: {DOCS} ({len(_docs)} page(s)/doc(s)). Workspace: {WORKSPACE}")
    print("Commands: /cost /reset /quit")
    while True:
        try:
            question = input("\n🧑 ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question or question == "/quit":
            break
        if question == "/cost":
            trace.show_totals("Session")
            continue
        if question == "/reset":
            thread_id = str(uuid.uuid4())  # a new thread = a fresh conversation
            print("Started a new conversation.")
            continue

        config = {"configurable": {"thread_id": thread_id}, "callbacks": [Tracer()],
                  "run_name": "research-agent", "tags": ["phase-3-project"]}
        try:
            result = agent.invoke({"messages": [{"role": "user", "content": question}]}, config=config)
        except Exception as e:  # network/API errors: keep the session alive
            print(f"⚠️ {type(e).__name__}: {e}")
            continue
        final = result["messages"][-1]
        print(f"\n🤖 {final.text}")
        # ⚠️ GOTCHA: with server tools, a long search turn can end with stop_reason="pause_turn".
        # create_agent then stops (no tool_calls). Task 4 in the README fixes this.
        if final.response_metadata.get("stop_reason") == "pause_turn":
            print("(the model paused a long web-search turn: send 'continue' to resume)")
    trace.show_totals("Session")


if __name__ == "__main__":
    main()
