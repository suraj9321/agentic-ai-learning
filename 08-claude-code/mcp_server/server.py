"""
Phase 8, lesson 04: your own MCP server (the "course server").

An MCP server is a small program that offers TOOLS (and optionally RESOURCES and PROMPTS) to any
MCP client: Claude Code, Claude Desktop, your own agent (see agent_with_mcp.py), and others.

🔗 You built this by hand in Phase 1 lesson 05: a tool = name + description + JSON schema + a function
your code runs. MCP just standardises HOW a client discovers those tools and calls them, so you
write a tool once and every MCP client can use it.

This server offers:
    tool      calculator(expression)     → the safe calculator from course_utils/tools.py
    tool      course_progress(phase)     → reads the [x]/[ ] boxes in the main README.md
    resource  course://interview-qa      → your notes/interview-qa.md
    prompt    quiz_me(topic)             → a ready-made "quiz me" prompt

Run it by itself (it waits for a client on stdin/stdout, so you'll see nothing; press Ctrl+C):
    uv run python 08-claude-code/mcp_server/server.py

Inspect it in a browser UI (MCP Inspector, needs Node.js):
    uv run --with "mcp[cli]" mcp dev 08-claude-code/mcp_server/server.py

Connect it to Claude Code: the repo's .mcp.json already does (see lesson 04), then run /mcp.
"""

import re
from pathlib import Path

# ⚠️ GOTCHA: `mcp` 2.x renamed `FastMCP` to `MCPServer`. Most tutorials online still show
# `from mcp.server.fastmcp import FastMCP`, which fails on 2.x. Same idea, new name.
from mcp.server import MCPServer

from course_utils.tools import calculator as safe_calculator

# 🐍 PYTHON NOTE: Path(__file__) is this file's location. .parents[2] goes up 3 levels:
# mcp_server/ → 08-claude-code/ → the repo root. This works no matter which folder you run from.
REPO_ROOT = Path(__file__).resolve().parents[2]

mcp = MCPServer("course")


# ---------------------------------------------------------------------------
# Tools: the model can CALL these
# ---------------------------------------------------------------------------
# 💡 WHY: the docstring becomes the tool DESCRIPTION and the type hints become the JSON SCHEMA.
# It's exactly the TOOLS list you wrote by hand in Phase 1, generated for you.
@mcp.tool()
def calculator(expression: str) -> str:
    """Evaluate a maths expression such as '(1200 * 0.18) / 12'. Use for any arithmetic
    instead of doing it in your head."""
    try:
        return safe_calculator(expression)
    except (ValueError, SyntaxError, ZeroDivisionError) as e:
        # 💡 WHY: return the error as text so the model can read it and fix its input
        # (the same pattern as is_error in Phase 1 lesson 06).
        return f"Error: {e}"


@mcp.tool()
def course_progress(phase: int | None = None) -> dict:
    """Report the learner's progress through this course, read from the checkboxes in README.md.
    Pass a phase number (0-9) for one phase, or nothing for all phases."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    # Only the "## Roadmap" section: the resources section at the end has "### Phase N" headings too.
    readme = readme.split("## Roadmap", 1)[-1].split("\n---", 1)[0]

    # Split the roadmap into "### Phase N: title" sections and count the boxes in each.
    # 🐍 PYTHON NOTE: re.split with a capturing group (...) keeps the separators in the result,
    # so we get [before, heading1, body1, heading2, body2, ...].
    parts = re.split(r"^### (Phase \d+:[^\n]*)$", readme, flags=re.MULTILINE)
    phases = {}
    for heading, body in zip(parts[1::2], parts[2::2]):
        number = int(re.search(r"Phase (\d+)", heading).group(1))
        done = re.findall(r"^- \[x\] (.+)$", body, flags=re.MULTILINE)
        todo = re.findall(r"^- \[ \] (.+)$", body, flags=re.MULTILINE)
        phases[number] = {
            "title": heading,
            "done": len(done),
            "total": len(done) + len(todo),
            "next": todo[0] if todo else None,
        }

    if phase is None:
        return {"phases": phases}
    if phase not in phases:
        return {"error": f"No phase {phase}. Known phases: {sorted(phases)}"}
    return phases[phase]


# ---------------------------------------------------------------------------
# Resources: data the CLIENT (or user) can read, addressed by a URI
# ---------------------------------------------------------------------------
# 💡 WHY: tools are chosen by the MODEL; resources are usually picked by the USER or app
# (in Claude Code you can @-mention them). Same data could be a tool; the difference is who decides.
@mcp.resource("course://interview-qa")
def interview_qa() -> str:
    """The learner's interview Q&A notes (notes/interview-qa.md)."""
    return (REPO_ROOT / "notes" / "interview-qa.md").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Prompts: reusable prompt templates the user can pick
# ---------------------------------------------------------------------------
@mcp.prompt()
def quiz_me(topic: str) -> str:
    """Quiz me on a course topic, one question at a time."""
    return (
        f"Quiz me on '{topic}' from this course. Ask ONE interview-style question at a time, "
        "wait for my answer, then tell me what I got right, what I missed, and a model answer "
        "in 3-5 sentences. After 5 questions, list my weakest areas."
    )


if __name__ == "__main__":
    # stdio transport: the client starts this script as a subprocess and talks JSON-RPC over
    # stdin/stdout. ⚠️ GOTCHA: never print() in a stdio server; stdout IS the protocol channel.
    # Use logging (it goes to stderr) if you need debug output.
    mcp.run()
