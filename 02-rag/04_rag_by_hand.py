"""
Lesson 04: RAG by hand, Retrieval-Augmented Generation.

    question ──► RETRIEVE (vector search) ──► AUGMENT (paste chunks into the prompt) ──► GENERATE (LLM)

What you'll learn:
  - Why an LLM can't answer questions about YOUR data, and how RAG fixes that
  - How to build a grounded prompt: documents in XML tags, rules, citations
  - Saying "I don't know" instead of making things up
  - Structured answers with citations you can verify in code

Run:  uv run python 02-rag/04_rag_by_hand.py
"""

import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from course_utils import trace
from course_utils.rag import VectorIndex, chunk_documents, format_context, load_documents

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
client = anthropic.Anthropic()
DATA = Path(__file__).parent / "data" / "nimbus"

# VectorIndex is the TinyVectorStore you built in lesson 03, moved into course_utils/rag.py.
index = VectorIndex(chunk_documents(load_documents(DATA)))


def text_of(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


# ---------------------------------------------------------------------------
# 1. Without RAG: the model doesn't know your company
# ---------------------------------------------------------------------------
trace.step("1. No retrieval: ask the model directly")

question = "How long do I have to get a refund from Nimbus, and how do I ask for one?"
request = dict(model=MODEL, max_tokens=16000,
               messages=[{"role": "user", "content": question}])
trace.show_request(request, label="no context")
response = client.messages.create(**request)
trace.show_response(response, label="no context")
# 💡 WHY: the model has never seen Nimbus's help centre (it's made up, and your real company's
# docs are private too). A good model says it doesn't know. A weaker prompt or model may
# invent a plausible policy ("30 days, email support@..."): a hallucination.


# ---------------------------------------------------------------------------
# 2. RAG: retrieve → augment → generate
# ---------------------------------------------------------------------------
trace.step("2. RAG: retrieve, then answer from the documents")

SYSTEM = """You are Nimbus's customer support assistant.
Answer ONLY using the documents provided in <documents>. Rules:
- Cite the document id in square brackets after each fact, e.g. [pricing.md#2].
- If the documents don't contain the answer, say "I don't know based on our docs" and suggest
  contacting support. Never use outside knowledge about Nimbus.
- If documents disagree, trust the one with the most recent `updated` date and mention the change.
- Be concise: 2-4 sentences."""


def rag_answer(question: str, k: int = 4) -> str:
    # ① RETRIEVE
    hits = index.search(question, k=k)
    trace.show_retrieval(question, hits, label=f"top {k}")

    # ② AUGMENT: put the documents FIRST and the question LAST.
    # 💡 WHY: models answer better when long documents come before the question, and XML
    # tags make clear where each document starts and ends and what its id is.
    user_content = f"{format_context(hits)}\n\n<question>{question}</question>"
    request = dict(model=MODEL, max_tokens=16000, system=SYSTEM,
                   messages=[{"role": "user", "content": user_content}])
    trace.show_request(request, label="RAG prompt")

    # ③ GENERATE
    response = client.messages.create(**request)
    trace.show_response(response, label="RAG answer")
    return text_of(response)


print("\n💬", rag_answer(question))
# Open the 📤 REQUEST panel above: THAT is RAG. The model sees your documents in the prompt.
# Nothing was trained or fine-tuned. Change a doc and the answer changes immediately.


# ---------------------------------------------------------------------------
# 3. When the answer isn't in the docs
# ---------------------------------------------------------------------------
trace.step("3. A question the docs can't answer")
print("\n💬", rag_answer("Does Nimbus have an Android app?"))
# ⚠️ GOTCHA: retrieval ALWAYS returns k chunks, even when none of them is relevant
# (look at the low scores). The prompt rule "say I don't know" is what stops the model
# from stretching unrelated chunks into an answer.


# ---------------------------------------------------------------------------
# 4. Conflicting sources
# ---------------------------------------------------------------------------
trace.step("4. Old and new documents disagree")
print("\n💬", rag_answer("Can I get my money back? What's the guarantee period?", k=5))
# faq_2024.md says 30 days, refunds_and_billing.md (updated 2026) says 14. Because we pass
# `updated` in each <document> tag and the system prompt says to trust the newest, the model
# can resolve the conflict. Without that metadata it might pick either one.


# ---------------------------------------------------------------------------
# 5. Structured answer + citation check in code
# ---------------------------------------------------------------------------
trace.step("5. Structured output with verified citations")


class CitedAnswer(BaseModel):
    answer: str = Field(description="The answer, 1-4 sentences, without citation brackets")
    citations: list[str] = Field(description="ids of the documents the answer is based on")
    answerable: bool = Field(description="False if the documents don't contain the answer")


q = "Which plans include the Slack integration, and what does it do?"
hits = index.search(q, k=4)
trace.show_retrieval(q, hits, label="top 4")
request = dict(
    model=MODEL, max_tokens=16000, system=SYSTEM,
    messages=[{"role": "user", "content": f"{format_context(hits)}\n\n<question>{q}</question>"}],
    output_format=CitedAnswer,
)
trace.show_request(request, label="structured RAG")
response = client.messages.parse(**request)
trace.show_response(response, label="structured RAG")
result = response.parsed_output

retrieved_ids = {h["id"] for h in hits}
# 🐍 PYTHON NOTE: {... for ...} with no colon is a *set comprehension* (unique values).
invalid = [c for c in result.citations if c not in retrieved_ids]
print(f"\n💬 {result.answer}")
print(f"   citations: {result.citations}   answerable: {result.answerable}")
print(f"   ✅ all citations point to retrieved chunks" if not invalid else f"   ❌ invented citations: {invalid}")
# 💡 WHY: in a product, citations become clickable links to the source. Checking them in
# code catches a model citing a document it was never shown. For a support bot you
# could also refuse to show answers with answerable=False and hand over to a human.

trace.show_totals("Lesson 04 totals")

# 🧪 TRY:
#   1. Remove the "If documents disagree..." rule and re-run section 4. Does the answer change?
#   2. Set k=1 and k=10 in section 2. What happens to answer quality and to input tokens/cost?
#   3. Ask "What's the price of Pro billed annually?" The doc has the formula. Does the model
#      calculate correctly? (In lesson 06 the agent can use a calculator tool.)
#   4. Put the question BEFORE the documents in the prompt. Any difference? (Small here; it
#      matters with long contexts.)
