#!/usr/bin/env bash
# Phase 8, lesson 07: Claude Code with no chat window (headless mode, `claude -p`).
#
# Writes a weekly study summary from your git history and course progress, as JSON you can
# feed into other tools. Run it yourself, from cron, or in CI.
#
#   bash 08-claude-code/weekly_summary.sh
#
# Needs: claude (logged in, or ANTHROPIC_API_KEY set) and python3.
set -euo pipefail   # stop on the first error, on unset variables, and on failures inside pipes
cd "$(dirname "$0")/.."   # run from the repo root, wherever the script is called from

OUT="$(mktemp)"   # a temporary file for the JSON result

SCHEMA='{
  "type": "object",
  "properties": {
    "lessons_done_this_week": {"type": "array", "items": {"type": "string"}},
    "percent_complete":       {"type": "number"},
    "next_step":              {"type": "string"},
    "one_tip":                {"type": "string"}
  },
  "required": ["lessons_done_this_week", "percent_complete", "next_step", "one_tip"]
}'

# 💡 WHY these flags:
#   -p                      print mode: run the agent loop once, print, exit (no chat)
#   --output-format json    machine-readable result with cost and turn count
#   --json-schema           force the final answer into this shape (→ .structured_output)
#   --allowedTools          headless = nobody to approve prompts, so pre-approve exactly what it needs.
#                           Everything else is denied. Read-only git + the course MCP server.
#   --max-budget-usd        a hard cost cap. Always set one in automation.
claude -p "Summarise my study week. Use 'git log --since=\"7 days ago\" --oneline' for what I did and the
course_progress MCP tool for overall progress. Be specific and encouraging." \
  --output-format json \
  --json-schema "$SCHEMA" \
  --allowedTools "Bash(git log *)" "mcp__course__course_progress" \
  --max-budget-usd 0.50 \
  < /dev/null > "$OUT"   # < /dev/null: no stdin to wait for

# Pretty-print the structured part, then the bookkeeping. (jq would also work: jq .structured_output)
python3 - "$OUT" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(json.dumps(d.get("structured_output"), indent=2, ensure_ascii=False))
print(f"\n{d['num_turns']} turns · ${d['total_cost_usd']:.4f} · {d['subtype']}")
PY
