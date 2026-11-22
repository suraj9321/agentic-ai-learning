"""
🛠 Phase 2 mini-project: chat with your documents (PDF / Markdown / text), with citations.

Pipeline for every message:

    your message ──► ① REWRITE into a standalone search query (uses chat history; cheap model)
                 ──► ② RETRIEVE: hybrid BM25 + vectors → cross-encoder rerank
                 ──► ③ ANSWER from the retrieved chunks, streamed, with [file p.N] citations

Run:
    uv run python 02-rag/project/doc_chat.py                  # uses 02-rag/project/docs/
    uv run python 02-rag/project/doc_chat.py ~/Downloads/pdfs # any folder of .pdf/.md/.txt

Commands while chatting:  /sources  /cost  /reset  /quit
"""

import os
import sys
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from course_utils import trace
from course_utils.rag import HybridRetriever, chunk_documents, load_documents

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
# 💡 WHY a second model: rewriting a query is an easy task, so use the cheapest, fastest model.
# This is "model routing", a key cost lever for a startup (Phase 7).
REWRITE_MODEL = os.getenv("REWRITE_MODEL", "claude-haiku-5-5")
client = anthropic.Anthropic()

ANSWER_SYSTEM = """You answer questions using ONLY the documents in <documents>.
- After each fact, cite its source as [file p.N] (or [file] when there's no page), using the
  `source` and `page` attributes of the document.
- If the documents don't contain the answer, say so plainly. Don't guess.
- If documents disagree, prefer the most recently `updated` one and mention the disagreement.
- Be concise; use bullet points for lists."""


class Rewrite(BaseModel):
    query: str = Field(description="Standalone search query capturing what the user is asking now")


def cite_label(chunk: dict) -> str:
    return f"{chunk['source']} p.{chunk['page']}" if chunk.get("page") else chunk["source"]


def format_docs(chunks: list[dict]) -> str:
    parts = []
    for c in chunks:
        attrs = f'source="{c["source"]}"' + (f' page="{c["page"]}"' if c.get("page") else "")
        attrs += f' updated="{c["updated"]}"' if c.get("updated") else ""
        parts.append(f"<document {attrs}>\n{c['text']}\n</document>")
    return "<documents>\n" + "\n".join(parts) + "\n</documents>"


class DocChat:
    def __init__(self, folder: Path, k: int = 5):
        t0 = time.perf_counter()
        docs = load_documents(folder)
        if not docs:
            sys.exit(f"No .pdf/.md/.txt files with text found in {folder}")
        self.chunks = chunk_documents(docs, max_chars=800, overlap=120)
        self.retriever = HybridRetriever(self.chunks)
        files = sorted({d["source"] for d in docs})
        print(f"📚 Indexed {len(files)} file(s), {len(docs)} page(s)/doc(s), {len(self.chunks)} chunks "
              f"in {time.perf_counter() - t0:.1f}s: {', '.join(files)}")
        self.k = k
        # Chat history as plain {"role", "content"} strings. We store the user's ORIGINAL
        # messages and the assistant's answers, NOT the retrieved documents. Re-sending old
        # documents every turn would multiply the cost.
        self.history: list[dict] = []
        self.last_sources: list[dict] = []

    # ① REWRITE ---------------------------------------------------------------
    def rewrite(self, message: str) -> str:
        if not self.history:  # first message: nothing to resolve
            return message
        recent = self.history[-6:]  # the last 3 exchanges are enough context
        transcript = "\n".join(f"{m['role']}: {m['content'][:500]}" for m in recent)
        request = dict(
            model=REWRITE_MODEL, max_tokens=1000,
            system="Rewrite the latest message as a standalone search query, resolving references "
                   "like 'it', 'that plan' or 'the second one' from the chat history.",
            messages=[{"role": "user", "content":
                       f"<chat_history>\n{transcript}\n</chat_history>\n<latest>{message}</latest>"}],
            output_format=Rewrite,
        )
        trace.show_request(request, label="① rewrite")
        response = client.messages.parse(**request)
        trace.show_response(response, label="① rewrite")
        return response.parsed_output.query

    # ② + ③ RETRIEVE and ANSWER ---------------------------------------------------
    def ask(self, message: str) -> str:
        query = self.rewrite(message)
        trace.step("② retrieve")
        hits = self.retriever.search(query, k=self.k)
        trace.show_retrieval(query, hits, label="② hybrid + rerank", score_name="rerank")
        self.last_sources = hits

        trace.step("③ answer")
        # The documents go into the LATEST user message only; history stays small.
        messages = self.history + [{"role": "user",
                                    "content": f"{format_docs(hits)}\n\n<question>{message}</question>"}]
        request = dict(model=MODEL, max_tokens=16000, system=ANSWER_SYSTEM, messages=messages)
        trace.show_request(request, label="③ answer")
        print("\n🤖 ", end="", flush=True)
        with client.messages.stream(**request) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
            final = stream.get_final_message()
        print()
        trace.show_response(final, label="③ answer")

        answer = "".join(b.text for b in final.content if b.type == "text")
        self.history += [{"role": "user", "content": message}, {"role": "assistant", "content": answer}]
        return answer


def main() -> None:
    folder = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path(__file__).parent / "docs"
    # 🐍 PYTHON NOTE: sys.argv is the list of command-line words: ["doc_chat.py", "~/pdfs"].
    # .expanduser() turns "~" into your home folder.
    chat = DocChat(folder)
    print("Ask questions about your documents. Commands: /sources /cost /reset /quit")
    while True:
        try:
            message = input("\n🧑 ").strip()
        except (EOFError, KeyboardInterrupt):  # Ctrl-D / Ctrl-C
            break
        if not message or message == "/quit":
            break
        if message == "/sources":
            for c in chat.last_sources:
                print(f"  [{cite_label(c)}] score={c['score']:.2f}  {c['text'][:120]!r}")
            continue
        if message == "/cost":
            trace.show_totals("Session")
            continue
        if message == "/reset":
            chat.history.clear()
            print("History cleared.")
            continue
        try:
            chat.ask(message)
        except anthropic.APIError as e:
            print(f"⚠️ API error: {e}")
    trace.show_totals("Session")


if __name__ == "__main__":
    main()
