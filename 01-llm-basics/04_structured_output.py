"""
Lesson 04: Structured output with Pydantic.

What you'll learn:
  - Why "please reply in JSON" isn't good enough for production
  - Pydantic models: describe the shape of data as a Python class
  - Getting validated, typed objects back from the LLM

This is how LLMs plug into normal software: extraction, classification, routing,
and filling databases all need structured output. Agents use it for decisions
("which step next?"). LangChain's `with_structured_output` (Phase 3) does the same thing.

Run:  uv run python 01-llm-basics/04_structured_output.py
"""

import os
from typing import Literal

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

from course_utils import trace  # shows each request/response (TRACE=full|brief|off in .env)

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
client = anthropic.Anthropic()


# ---------------------------------------------------------------------------
# 1. Pydantic basics (no LLM yet)
# ---------------------------------------------------------------------------
# 🐍 PYTHON NOTE: classes.
# A class is a blueprint for objects. `class Person(BaseModel):` means Person *inherits*
# from Pydantic's BaseModel, which gives it validation for free.
# Each line `name: type` declares a field. Pydantic reads these type hints and
# CHECKS the data at runtime (plain Python type hints don't do this).
class Person(BaseModel):
    name: str
    age: int


print("=" * 60)
print("1. Pydantic validates data")
print("=" * 60)

p = Person(name="Asha", age="29")  # "29" is a string, but Pydantic converts it to int
print(p, "| age type:", type(p.age).__name__)

try:
    Person(name="Ravi", age="twenty")  # can't be converted → error
except ValidationError as e:
    print("Validation error caught:", e.errors()[0]["msg"])
# 💡 WHY: LLM output is untrusted. Pydantic is the gatekeeper between "text from a model"
# and "data my program relies on".


# ---------------------------------------------------------------------------
# 2. A richer schema for a real task: extracting a lead from an email
# ---------------------------------------------------------------------------
class Address(BaseModel):
    city: str
    country: str

class Lead(BaseModel):
    """A sales lead extracted from an inbound email."""

    # Field(description=...) is sent to the model as part of the schema, so it acts as
    # instructions for that field. Good descriptions = better extraction.
    company: str = Field(description="Company name of the sender")
    contact_name: str
    email: str
    # 🐍 PYTHON NOTE: Literal["a", "b"] means "only these exact values are allowed".
    # Perfect for categories: the model can't invent a new one.
    intent: Literal["demo_request", "pricing_question", "support", "partnership", "other"]
    # 🐍 PYTHON NOTE: list[str] = a list whose items are strings.
    products_mentioned: list[str]
    team_size: int | None = Field(description="Number of people on their team, if stated")
    # 🐍 PYTHON NOTE: `int | None` means "an int OR None". None is Python's "no value".
    urgency: Literal["low", "medium", "high"]
    budget_mentioned: bool
    address: Address | None = Field(description="City and country of the sender, if stated")


email_text = """
Hi there, I'm Meera Iyer, Head of Ops at Brightpath Logistics (meera@brightpath.io).
We're a team of about 45 and are drowning in shipment-status emails. Saw your AI inbox
agent and the Slack integration. Could we get a demo this week? Our renewal with our
current vendor is up on the 1st so we need to decide fast.
"""

print("\n" + "=" * 60)
print("2. Extract a typed object from messy text")
print("=" * 60)

# messages.parse() sends the Pydantic schema to the API and constrains the output to it
# (the model cannot produce JSON that doesn't match), then validates it into a Lead object.
request = dict(
    model=MODEL,
    max_tokens=16000,
    messages=[{"role": "user", "content": f"Extract the lead from this email:\n\n<email>{email_text}</email>"}],
    output_format=Lead,
)
trace.show_request(request, label="extract a Lead")
response = client.messages.parse(**request)
trace.show_response(response, label="extract a Lead")
trace.note("The text block is raw JSON that matches the schema; parsed_output is that JSON validated into a Lead object.")

lead = response.parsed_output  # a real Lead object, not a dict, not a string
print(lead.model_dump_json(indent=2))  # 🐍 pretty-print the object as JSON

# Because it's typed, normal code can act on it safely:
if lead.intent == "demo_request" and lead.urgency == "high":
    print(f"\n→ Route to sales NOW: {lead.contact_name} at {lead.company} ({lead.team_size} people)")


# ---------------------------------------------------------------------------
# 3. Structured output for DECISIONS: the seed of agent routing
# ---------------------------------------------------------------------------
class RouteDecision(BaseModel):
    reasoning: str = Field(description="One sentence explaining the choice")
    # Put reasoning BEFORE the decision field: the model writes fields in order,
    # so it "thinks" first and decides second.
    route: Literal["faq_bot", "human_agent", "refund_flow", "unclear"]


print("\n" + "=" * 60)
print("3. Structured output as a routing decision")
print("=" * 60)

for msg in [
    "How do I reset my password?",
    "You charged me for a plan I cancelled 3 months ago and I want my money back.",
    "Your product deleted our client data and our lawyer will be in touch.",
    "In todays news , priminister of india announced new policies for startups. Can you summarize?",
]:
    request = dict(
        model=MODEL,
        max_tokens=16000,
        system="You route customer messages for a SaaS company.",
        messages=[{"role": "user", "content": msg}],
        output_format=RouteDecision,
    )
    trace.show_request(request, label="route a message")
    r = client.messages.parse(**request)
    trace.show_response(r, label="route decision")
    d = r.parsed_output
    print(f"{d.route:12} ← {msg[:60]}\n{'':15}({d.reasoning})")

# 💡 WHY: this is exactly the "router" pattern you'll build in LangGraph (Phase 4):
# an LLM makes a structured decision, and ordinary code branches on it.
# The LLM decides; your code controls. That keeps agents predictable.

# 🧪 TRY:
#   1. Add a field `budget_mentioned: bool` to Lead and re-run.
#   2. Add a nested model: `class Address(BaseModel): city: str; country: str` and use
#      `address: Address | None` inside Lead.
#   3. Feed a message that fits no route well. Add an "unclear" route. Does accuracy improve?
