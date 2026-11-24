"""
Phase 8, lesson 08: the Claude Agent SDK, Claude Code's engine as a Python library.

In Phase 1 you wrote the agent loop yourself. In Phase 4 LangChain's create_agent wrote it for you.
The Agent SDK goes one step further: you get Claude Code's WHOLE harness (the loop, built-in
tools like Read/Grep/Bash/Edit, permissions, hooks, subagents, MCP, context compaction) and
just configure it.

    Your code ──► query(prompt, options) ──► Claude Code harness ──► Claude
                       ▲                         │ runs tools, loops, compacts
                       └──── stream of messages ◄┘

This script builds a read-only "lesson reviewer": it may read and search the repo, use one
custom tool (in-process MCP), and must NOT edit anything.

Needs: Claude Code installed (`claude --version`) and logged in, or ANTHROPIC_API_KEY set.
Run:   uv run python 08-claude-code/08_agent_sdk.py
"""

import asyncio
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    query,
    tool,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# A custom tool, served by an IN-PROCESS MCP server (no subprocess, unlike lesson 04)
# ---------------------------------------------------------------------------
# 💡 WHY: the same MCP idea as mcp_server/server.py, but living inside this Python process,
# so the tool can use your app's own objects (a database connection, the current user, ...).
@tool("count_markers", "Count the course comment markers (WHY, GOTCHA, TRY, PYTHON NOTE) in a file.",
      {"path": str})
async def count_markers(args):
    text = (REPO_ROOT / args["path"]).read_text(encoding="utf-8")
    counts = {m: text.count(m) for m in ["💡 WHY", "⚠️ GOTCHA", "🧪 TRY", "🐍 PYTHON NOTE"]}
    return {"content": [{"type": "text", "text": str(counts)}]}


course_tools = create_sdk_mcp_server(name="course", version="1.0.0", tools=[count_markers])

options = ClaudeAgentOptions(
    cwd=str(REPO_ROOT),
    system_prompt="You review lessons in a Python course for beginners. Be specific and brief.",
    mcp_servers={"course": course_tools},
    # Tools that run WITHOUT asking. MCP tools are named mcp__<server>__<tool>.
    allowed_tools=["Read", "Grep", "Glob", "mcp__course__count_markers"],
    # ⚠️ GOTCHA: allowed_tools AUTO-APPROVES; it does not RESTRICT. To guarantee the agent can't
    # change anything, also DENY the writing tools (or use permission_mode="plan").
    disallowed_tools=["Edit", "Write", "Bash", "NotebookEdit"],
    max_turns=10,           # same idea as max_steps in your Phase 1 loop
    max_budget_usd=0.50,    # a hard cost cap; your Phase 1 loop didn't have one
)


async def main() -> None:
    prompt = (
        "Review 01-llm-basics/05_tool_calling.py. Use count_markers on it, then give 3 bullet points: "
        "one thing it explains well, one confusing spot for a beginner, one suggested 🧪 TRY exercise."
    )
    # query() yields messages as the agent works: assistant turns, tool calls, and a final result.
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"⚙️  {block.name}({block.input})")
                elif isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            cost = message.total_cost_usd or 0
            print(f"\n📊 {message.num_turns} turns · ${cost:.4f} · {message.subtype}")


if __name__ == "__main__":
    asyncio.run(main())
    # 🧪 TRY: remove "Edit" from disallowed_tools and ask it to fix the confusing spot. What happens?
    # (Without a terminal to ask you, the edit is denied. Now add permission_mode="acceptEdits".)
