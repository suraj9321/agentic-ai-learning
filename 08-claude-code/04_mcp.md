# Lesson 04: MCP: build a server once, use it from any agent

**MCP (Model Context Protocol)** is an open standard for connecting AI applications to tools and data.
Before MCP, every app needed its own integration for every service (N apps × M services). With MCP,
a service writes **one server** and every MCP **client** can use it (N + M).

```
   HOST (the app you use)            CLIENT (one per server)        SERVER (exposes capabilities)
   Claude Code, Claude Desktop,  ──► MCP client ──(stdio/HTTP)──► course server (lesson code)
   your own agent, IDEs…         ──► MCP client ──(HTTP)───────► docs.langchain.com/mcp
```

## 1. What a server can offer

| Primitive | Who decides to use it | Example in our course server |
|---|---|---|
| **Tools** | The **model** (like Phase 1 tool calling) | `calculator`, `course_progress` |
| **Resources** | The **user/app** (attached as context, `@`-mentionable in Claude Code) | `course://interview-qa` |
| **Prompts** | The **user** (a template they pick, a `/` command in Claude Code) | `quiz_me(topic)` |

Transports: **stdio** (the client starts the server as a subprocess and they exchange JSON-RPC messages over
stdin/stdout; for local tools) and **Streamable HTTP** (a URL; for remote and shared servers. Older SSE is deprecated).

> 🔗 **You built half of MCP in Phase 1.** An MCP tool is exactly your Phase 1 tool definition:
> `name`, `description`, `input_schema`. MCP adds a standard way to **discover** tools (`tools/list`) and
> **call** them (`tools/call`) across process and network boundaries.

## 2. Read the server: [`mcp_server/server.py`](mcp_server/server.py)

```python
from mcp.server import MCPServer
mcp = MCPServer("course")

@mcp.tool()
def calculator(expression: str) -> str:
    """Evaluate a maths expression such as '(1200 * 0.18) / 12'. ..."""
```

The docstring becomes the description, the type hints become the JSON schema. Read the whole file: it has
a tool returning a dict, a resource and a prompt, and two GOTCHAs (the `FastMCP` → `MCPServer` rename in
`mcp` 2.x, and **never `print()` in a stdio server**: stdout is the protocol channel).

```bash
uv run python 08-claude-code/mcp_server/server.py      # waits silently for a client; Ctrl+C to stop
uv run --with "mcp[cli]" mcp dev 08-claude-code/mcp_server/server.py   # browser inspector (needs Node.js)
```

## 3. Connect it to Claude Code

Two equivalent ways:

```bash
# A. command line. Scope: local (default, only you, this project) | project (.mcp.json) | user (all your projects)
claude mcp add --transport stdio --scope project course -- uv run python 08-claude-code/mcp_server/server.py
claude mcp add --transport http  --scope project langchain-docs https://docs.langchain.com/mcp
```

```json
// B. .mcp.json at the repo root (what option A with --scope project writes). This repo already has it.
{
  "mcpServers": {
    "course":         { "type": "stdio", "command": "uv", "args": ["run", "python", "08-claude-code/mcp_server/server.py"] },
    "langchain-docs": { "type": "http",  "url": "https://docs.langchain.com/mcp" }
  }
}
```

Notes:
- Everything after `--` is the server command (so its own flags don't get mixed up with `claude`'s).
- Project servers from `.mcp.json` must be **approved** once per person (a cloned repo can't silently run code).
- Secrets: never commit them. Use `"headers": {"Authorization": "Bearer ${MY_API_KEY}"}`; `${VAR}` and
  `${VAR:-default}` are expanded from your environment. Servers that use OAuth: authenticate with `/mcp`.
- Manage servers with `claude mcp list | get <name> | remove <name>`, and `/mcp` inside a session.

🧪 **TRY:** in a session, ask *"How far am I through the course?"* Approve the `mcp__course__course_progress` call
(or note it's pre-allowed in `.claude/settings.json`). Then type `@` and find the `course://interview-qa` resource,
and `/` to find the `quiz_me` prompt.

## 4. Your own agent as an MCP client: [`mcp_server/agent_with_mcp.py`](mcp_server/agent_with_mcp.py)

```bash
uv run python 08-claude-code/mcp_server/agent_with_mcp.py
```

It's the Phase 1 agent loop with **one change**: tools come from `await mcp.list_tools()` and run through
`await mcp.call_tool(...)` instead of a hard-coded dict. Read `to_claude_tool()`: converting an MCP tool into
a Messages API tool is three lines, because they're the same thing.

> ⚠️ **GOTCHA, the ecosystem moves fast.** `mcp` 2.x (used here) renamed classes and changed APIs. Some
> libraries built on it (for example `langchain-mcp-adapters` at the time of writing) still need `mcp` 1.x.
> Check compatibility before mixing them; `uv` will tell you about version conflicts.

## 5. Security: an MCP server is code you run with your permissions

- A **stdio** server runs on your machine with your user's access. Treat it like installing a package.
- A server's tool **descriptions and results go into the model's context**, so a malicious or compromised
  server can attempt prompt injection ("tool poisoning"). Prefer official and well-known servers, pin versions,
  and review what `/mcp` shows it can do.
- Least privilege: give a server only the credentials it needs (a read-only database user, a scoped token).
- Use permission rules: allow only the read-only tools (`mcp__course__course_progress`); leave writes on "ask".

## 6. Hands-on
1. Add a tool `lesson_list(phase: int)` to `server.py` that returns the lesson files in a phase folder.
   Restart it (`/mcp` → reconnect), then use it from Claude Code **and** from `agent_with_mcp.py` without
   changing the agent. That's the point of MCP.
2. Make the tool safe: what happens with `phase=-1` or `phase=99`? Return a helpful error the model can act on.
3. Run the server over HTTP: change `mcp.run()` to `mcp.run(transport="streamable-http")`, connect with
   `claude mcp add --transport http course-http http://localhost:8000/mcp`. When would you deploy a server
   like this instead of using stdio?

## Write it down
`notes/interview-qa.md`: *"What is MCP, and how does it relate to tool calling? Tools vs resources vs prompts?"*
