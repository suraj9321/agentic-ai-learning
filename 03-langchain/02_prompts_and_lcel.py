"""
Lesson 02: Prompt templates, LCEL pipes and structured output.

What you'll learn:
  - ChatPromptTemplate: prompts with {variables}, and MessagesPlaceholder for chat history
  - LCEL ("LangChain Expression Language"): prompt | model | parser
  - Runnables: RunnableLambda (your own function), RunnableParallel (fan out), RunnablePassthrough
  - with_structured_output(): Phase 1 lesson 04 (Pydantic output) in one line

Run:  uv run python 03-langchain/02_prompts_and_lcel.py
"""

import os
from typing import Literal

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from pydantic import BaseModel, Field

from course_utils import trace
from course_utils.lc_trace import Tracer

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
model = init_chat_model(f"anthropic:{MODEL}", max_tokens=16000)
CONFIG = {"callbacks": [Tracer()]}


# ---------------------------------------------------------------------------
# 1. Prompt templates
# ---------------------------------------------------------------------------
trace.step("1. ChatPromptTemplate")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You explain {topic} to a {audience}. Max 3 sentences."),
    ("human", "{question}"),
])
# A template is itself a Runnable: invoke() fills in the variables and returns messages.
filled = prompt.invoke({"topic": "AI engineering", "audience": "10-year-old",
                        "question": "What is a vector database?"})
print("prompt.invoke(...) returns:", type(filled).__name__)
for m in filled.to_messages():
    print(f"   {type(m).__name__:<14} {m.content}")
# 💡 WHY templates: prompts become reusable, testable objects with named inputs instead of
# f-strings scattered through your code. LangSmith can also version prompts (lesson 05).


# ---------------------------------------------------------------------------
# 2. LCEL: piping components together
# ---------------------------------------------------------------------------
trace.step("2. prompt | model | parser")

# 🐍 PYTHON NOTE: OPERATOR OVERLOADING. Python lets a class decide what `a | b` means by
# defining a method called __or__. Tiny example:
class Step:
    def __init__(self, name):
        self.name = name

    def __or__(self, other):  # called for `self | other`
        return Step(f"{self.name} → {other.name}")


print("Step('a') | Step('b') =", (Step("a") | Step("b")).name)
# LangChain's Runnables define __or__ to build a RunnableSequence: the output of the left
# side becomes the input of the right side. That's all LCEL is.

chain = prompt | model | StrOutputParser()  # StrOutputParser: AIMessage → plain string (.text)
answer = chain.invoke({"topic": "AI engineering", "audience": "10-year-old",
                       "question": "What is a vector database?"}, config=CONFIG)
print("\n💬", answer)
print("chain type:", type(chain).__name__)
# Without LCEL this is: messages = prompt.invoke(x); msg = model.invoke(messages); text = msg.text
# ⚠️ GOTCHA: LCEL is great for straight pipelines. For loops, branches and state, the
# LangChain team recommends LangGraph (Phase 4). Don't build agents out of giant LCEL chains.


# ---------------------------------------------------------------------------
# 3. Your own functions in a chain, and running branches in parallel
# ---------------------------------------------------------------------------
trace.step("3. RunnableLambda + RunnableParallel")

# Any Python function can become a chain step.
shout = RunnableLambda(lambda text: text.upper())

explain = (ChatPromptTemplate.from_template("Explain {concept} in one sentence.")
           | model | StrOutputParser())
example = (ChatPromptTemplate.from_template("Give one real-world product that uses {concept}. One line.")
           | model | StrOutputParser())

# RunnableParallel runs several chains on the SAME input at the same time and returns a dict.
both = RunnableParallel(explanation=explain, example=example, concept=RunnablePassthrough())
# RunnablePassthrough passes the input through unchanged (handy to keep it in the output).
result = both.invoke({"concept": "retrieval-augmented generation"}, config=CONFIG)
# 🐍 NOTE: the input was a dict, so result["concept"] is that same dict.
print("explanation:", result["explanation"])
print("example:    ", result["example"])
print("shouted:    ", shout.invoke("lcel is just function composition"))


# ---------------------------------------------------------------------------
# 4. Chat history with MessagesPlaceholder
# ---------------------------------------------------------------------------
trace.step("4. MessagesPlaceholder: slot for a list of messages")

chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant for Nimbus, an AI meeting-notes app."),
    MessagesPlaceholder("history"),  # the whole previous conversation goes here
    ("human", "{input}"),
])
chat_chain = chat_prompt | model | StrOutputParser()
history = [
    HumanMessage("My team is 12 people."),
    AIMessage("Got it, a team of 12. How can I help?"),
]
print("💬", chat_chain.invoke({"history": history, "input": "How many people did I say?"}, config=CONFIG))


# ---------------------------------------------------------------------------
# 5. Structured output
# ---------------------------------------------------------------------------
trace.step("5. with_structured_output()")


class Ticket(BaseModel):
    """A classified customer support ticket."""
    category: Literal["billing", "bug", "feature_request", "other"]
    urgency: int = Field(ge=1, le=5, description="1 = whenever, 5 = business is blocked")
    summary: str = Field(description="One-line summary for the support dashboard")


# method="json_schema" uses Claude's native structured outputs (constrained decoding), like
# messages.parse() in Phase 1. ⚠️ GOTCHA: the default method uses a forced tool call, which
# isn't supported on newer Claude models with thinking, and LangChain warns about it.
classifier = model.with_structured_output(Ticket, method="json_schema")
tickets = [
    "We were charged twice this month and finance is asking questions.",
    "The bot hasn't joined ANY meeting since this morning, our sales team is blind!!",
    "Would be cool if summaries could be exported to Confluence.",
]
results = classifier.batch(tickets, config=CONFIG)
for text, ticket in zip(tickets, results):
    print(f"{ticket.category:<16} urgency={ticket.urgency}  {ticket.summary}   ← {text[:40]}...")
# The result is a real Ticket object (validated by Pydantic), not a string.

trace.show_totals("Lesson 02 totals")

# 🧪 TRY:
#   1. Build a chain: translate → summarise → classify. Each step a prompt | model | parser,
#      joined with |. Hint: a RunnableLambda can reshape the output into the next prompt's input
#      dict: RunnableLambda(lambda text: {"text": text}).
#   2. Add a `language: str` field to Ticket and send a ticket in another language.
#   3. Print `chain` (just print(chain)). LCEL chains describe themselves. Also try
#      chain.get_graph().print_ascii() (needs `uv add grandalf`).
