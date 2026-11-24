"""
PostToolUse hook (Phase 8, lesson 06): after Claude edits a .py file, check it still parses.

PostToolUse runs AFTER the tool, so it can't undo the edit. But exit code 2 sends our stderr
back to Claude as feedback, so it notices the broken file right away and fixes it.
"""

import json
import py_compile
import sys

event = json.load(sys.stdin)
path = event.get("tool_input", {}).get("file_path", "")

if path.endswith(".py"):
    try:
        py_compile.compile(path, doraise=True)
    except py_compile.PyCompileError as e:
        print(f"Syntax error after your edit to {path}:\n{e.msg}", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
