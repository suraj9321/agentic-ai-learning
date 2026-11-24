"""
Phase 8, lesson 04: YOUR agent loop as an MCP client.

Claude Code is one MCP client. Here you write another one: the Phase 1 lesson 06 agent loop,
except the tools are NOT hard-coded. They are discovered from the MCP server at runtime.

    your agent ──(starts subprocess)──► server.py
        │  list_tools()   → names, descriptions, JSON schemas
        │  call_tool()    → runs the function on the server, returns the result
        ▼
    Claude (Messages API) only ever sees ordinary tool definitions, exactly like Phase 1.

💡 WHY this matters: write a tool once as an MCP server, and Claude Code, Claude Desktop,
your own agents and (via adapters) LangChain/LangGraph agents can all use it.

Run:  uv run python 08-claude-code/mcp_server/agent_with_mcp.py
"""

import asyncio
import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from mcp import Client, StdioServerParameters

from course_utils import trace

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
client = anthropic.AsyncAnthropic()  # the async client, because the MCP client is async (Phase 1 lesson 07)

SERVER = StdioServerParameters(
    # 🐍 PYTHON NOTE: sys.executable is the Python running THIS script (the project's .venv),
    # so the server gets the same installed packages.
    command=sys.executable,
    args=[str(Path(__file__).parent / "server.py")],
)

SYSTEM = """You are a study coach for an agentic-AI course.
Use course_progress to see where the learner is, and calculator for any arithmetic.
Be concise and encouraging."""


def to_claude_tool(mcp_tool) -> dict:
    """An MCP tool definition → a Messages API tool definition. They're almost the same thing."""
    return {
        "name": mcp_tool.name,
        "description": mcp_tool.description or "",
        "input_schema": mcp_tool.input_schema,
    }


async def run_agent(question: str, max_steps: int = 8) -> str:
    # 🐍 PYTHON NOTE: `async with` opens the connection (starts the server subprocess) and
    # guarantees it is closed again, even if an error happens inside the block.
    async with Client(SERVER) as mcp:
        listed = await mcp.list_tools()
        tools = [to_claude_tool(t) for t in listed.tools]
        trace.note(f"Discovered {len(tools)} tools from the MCP server: {[t['name'] for t in tools]}")

        messages = [{"role": "user", "content": question}]
        for step in range(1, max_steps + 1):
            trace.step(f"AGENT STEP {step}")
            request = dict(model=MODEL, max_tokens=16000, system=SYSTEM, tools=tools, messages=messages)
            trace.show_request(request, label=f"step {step}")
            response = await client.messages.create(**request)
            trace.show_response(response, label=f"step {step}")
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                return "".join(b.text for b in response.content if b.type == "text")

            results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                # The ONLY difference from Phase 1: instead of TOOL_FUNCTIONS[name](**input),
                # we ask the MCP server to run it.
                result = await mcp.call_tool(block.name, block.input)
                text = "\n".join(c.text for c in result.content if c.type == "text")
                trace.show_tool_call(block.name, block.input, text, is_error=result.is_error)
                results.append({
                    "type": "tool_result", "tool_use_id": block.id,
                    "content": text, "is_error": result.is_error,
                })
            messages.append({"role": "user", "content": results})

        return "Stopped: too many steps."


if __name__ == "__main__":
    answer = asyncio.run(run_agent(
        "How far am I through the course, as a percentage of all checkboxes? What should I do next?"
    ))
    print("\n" + answer)
    # 🧪 TRY: add a new @mcp.tool() to server.py (e.g. a word counter). Re-run this file without
    # changing it: the agent discovers the new tool on its own. That is the point of MCP.
