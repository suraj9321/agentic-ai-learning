"""
PreToolUse hook (Phase 8, lesson 06): block dangerous shell commands BEFORE they run.

Claude Code runs this script before every Bash tool call and sends the call as JSON on stdin:
    {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}, "cwd": "...", ...}

Exit code 0 → allow.  Exit code 2 → BLOCK, and what we print to stderr is shown to Claude,
so it can choose a safer approach. (Any other exit code is a non-blocking error.)

🔗 Same idea as LangChain middleware in Phase 3 lesson 06: code that runs around every tool call.
💡 WHY a hook and not a line in CLAUDE.md: CLAUDE.md is a request the model usually follows;
a hook is code that ALWAYS runs. Use hooks for rules that must never be broken.
"""

import json
import re
import sys

# (pattern, reason). Keep the reasons helpful: Claude reads them and adapts.
BLOCKED = [
    (r"\brm\s+-[a-zA-Z]*[rf][a-zA-Z]*\b", "recursive/forced delete (rm -rf). Delete specific files instead, or ask the user."),
    (r"\bgit\s+push\b.*(--force|-f\b)", "force push rewrites shared history. Ask the user first."),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard throws away uncommitted work. Ask the user first."),
    (r"(^|[\s;&|])(cat|less|more|head|tail|grep|sed|awk)\b[^|;&]*\.env(\s|$)", "the .env file holds secrets and must not be read."),
]

event = json.load(sys.stdin)
command = event.get("tool_input", {}).get("command", "")

for pattern, reason in BLOCKED:
    if re.search(pattern, command):
        print(f"Blocked by .claude/hooks/block_dangerous.py: {reason}", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
