"""
Lesson 05: Tool calling, step by step and fully by hand.

The most important idea in this course:
    THE MODEL NEVER RUNS YOUR TOOLS. It only ASKS you to run them.

The protocol has 4 steps:
    1. You send: user message + a list of tool DEFINITIONS (name, description, JSON schema)
    2. Model replies with stop_reason="tool_use" and a `tool_use` block: {name, input, id}
    3. YOUR code runs the real function and sends back a `tool_result` block (same id)
    4. Model reads the result and writes the final answer (or asks for another tool → lesson 06)

Run:  uv run python 01-llm-basics/05_tool_calling.py
"""

import json
import os

import anthropic
from dotenv import load_dotenv

from course_utils import trace  # prints each request/response/tool run (TRACE=full|brief|off in .env)

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
client = anthropic.Anthropic()


# ---------------------------------------------------------------------------
# The real Python functions (our "tools")
# ---------------------------------------------------------------------------
# Fake data so the lesson runs without other API keys. In the mini-project you'll use real tools.
FAKE_WEATHER = {"paris": (18, "cloudy"), "mumbai": (31, "humid"), "london": (12, "rain")}


def get_weather(city: str, unit: str = "celsius") -> dict:
    temp_c, conditions = FAKE_WEATHER.get(city.lower(), (20, "unknown"))
    temp = temp_c if unit == "celsius" else round(temp_c * 9 / 5 + 32)
    return {"city": city, "temperature": temp, "unit": unit, "conditions": conditions}


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    rates_to_usd = {"USD": 1.0, "EUR": 1.08, "INR": 0.012, "GBP": 1.27}
    usd = amount * rates_to_usd[from_currency.upper()]
    result = usd / rates_to_usd[to_currency.upper()]
    return {"amount": round(result, 2), "currency": to_currency.upper()}


# ---------------------------------------------------------------------------
# Tool DEFINITIONS: what the model sees
# ---------------------------------------------------------------------------
# The model sees ONLY this, never your Python code. So:
#   - `description` is a prompt: say WHAT it does and WHEN to use it
#   - `input_schema` is JSON Schema: names, types, required fields
# 💡 WHY: in practice, bad tool descriptions are the #1 cause of agents picking the wrong tool.
TOOLS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city. Use when the user asks about weather, temperature or conditions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'Paris'"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "Temperature unit"},
            },
            "required": ["city"],
        },
    },
    {
        "name": "convert_currency",
        "description": "Convert an amount of money between currencies (USD, EUR, INR, GBP).",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "from_currency": {"type": "string", "description": "3-letter code, e.g. USD"},
                "to_currency": {"type": "string", "description": "3-letter code, e.g. INR"},
            },
            "required": ["amount", "from_currency", "to_currency"],
        },
    },
]

# 🐍 PYTHON NOTE: functions are objects in Python. You can put them in a dict and call
# them later: TOOL_FUNCTIONS["get_weather"](city="Paris"). This "dispatch table" maps
# the name the model asks for to the real function.
TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "convert_currency": convert_currency,
}


# ---------------------------------------------------------------------------
# STEP 1: send the question + tool definitions
# ---------------------------------------------------------------------------
question = "What's the weather in Paris right now, in fahrenheit?"
messages = [{"role": "user", "content": question}]

trace.step("STEP 1: send the question + tool definitions")
# 🐍 PYTHON NOTE: build the request as a dict, then unpack it with **request.
# client.messages.create(**request) is the same as writing every argument out by hand,
# but now we can also PRINT exactly what we send.
request = dict(model=MODEL, max_tokens=16000, tools=TOOLS, messages=messages)
trace.show_request(request, label="question + tools")
response = client.messages.create(**request)

print(response.model_dump_json(indent=2))  # print the full raw response as JSON


# ---------------------------------------------------------------------------
# STEP 2: the model asks for a tool
# ---------------------------------------------------------------------------
trace.step("STEP 2: the model replies, asking for a tool")
trace.show_response(response, label="model asks for a tool")
trace.note("The model did NOT run anything. It only wrote a tool_use block: a request for our code.")


# ---------------------------------------------------------------------------
# STEP 3: WE run the tool and send the result back
# ---------------------------------------------------------------------------
trace.step("STEP 3: OUR code runs the tool and prepares tool_result blocks")
# First, append the assistant's turn exactly as received (the API needs it to match ids).
messages.append({"role": "assistant", "content": response.content})

tool_results = []
for block in response.content:
    if block.type == "tool_use":
        func = TOOL_FUNCTIONS[block.name]
        # 🐍 PYTHON NOTE: `**block.input` unpacks the dict into keyword arguments:
        # {"city": "Paris", "unit": "fahrenheit"} → get_weather(city="Paris", unit="fahrenheit")
        result = func(**block.input)
        trace.show_tool_call(block.name, block.input, json.dumps(result))
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,           # ⚠️ GOTCHA: must match the tool_use id
            "content": json.dumps(result),     # results are sent as text; JSON is a good format
        })

# Tool results go back in a USER message. (Roles: user = "things from outside the model".)
# ⚠️ GOTCHA: if the model asked for several tools at once, send ALL results in ONE user message.
messages.append({"role": "user", "content": tool_results})


# ---------------------------------------------------------------------------
# STEP 4: the model uses the result to answer
# ---------------------------------------------------------------------------
trace.step("STEP 4: send the WHOLE conversation back; the model uses the result")
request = dict(model=MODEL, max_tokens=16000, tools=TOOLS, messages=messages)
trace.show_request(request, label="conversation + tool results")
trace.note("Messages marked NEW were added since request #1. The rest are re-sent every time.")
final = client.messages.create(**request)
trace.show_response(final, label="final answer")
trace.show_totals()
print("\nFinal answer:", "".join(b.text for b in final.content if b.type == "text"))


# ---------------------------------------------------------------------------
# Look at the full message list: this IS the agent's "memory"
# ---------------------------------------------------------------------------
print("\n--- Full conversation sent in step 4 ---")
for m in messages:
    if isinstance(m["content"], str):
        # 🐍 PYTHON NOTE: isinstance(x, str) checks the type of a value.
        summary = m["content"]
    else:
        summary = [getattr(b, "type", None) or b.get("type") for b in m["content"]]
        # 🐍 getattr(obj, "attr", default) reads an attribute safely. Here content holds
        # SDK objects (assistant turn) or plain dicts (our tool_results).
    print(f"{m['role']:9} {summary}")

# 🧪 TRY:
#   1. Ask "What's 250 EUR in INR?" Which tool does it pick?
#   2. Ask "Weather in Mumbai and London?" Count the tool_use blocks in step 2 (parallel calls!).
#      Does this script handle it? (Yes, because of the loop in step 3.)
#   3. Ask something that needs BOTH tools, like "It's 18°C in Paris; how much is a €40 dinner in USD?"
#      After step 4 the model may want ANOTHER tool, and this script can't handle that.
#      → That's why we need a LOOP. On to lesson 06.
#   4. Make get_weather's description vague ("weather stuff"). Does tool choice get worse?
