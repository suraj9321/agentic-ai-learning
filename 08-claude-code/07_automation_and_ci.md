# Lesson 07: Automation: headless mode, CI and parallel sessions

So far there's been a human in the loop approving things. In a startup, a lot of agent value comes from
**automation**: review every pull request, triage issues, write the changelog, fix lint overnight.
Same agent, no chat window.

## 1. Headless mode: `claude -p`

```bash
claude -p "How many lesson files are in 01-llm-basics?"                       # plain text answer
claude -p "..." --output-format json                                          # result + cost + turns + session_id
claude -p "..." --output-format stream-json --verbose                         # one JSON event per line, live
claude -p "..." --output-format json --json-schema '{"type":"object",...}'    # → .structured_output
git diff | claude -p "Review this diff for bugs"                              # pipe data in
claude -p --continue "and now the tests"                                      # continue the last session
```

| Flag | Why it matters headless |
|---|---|
| `--allowedTools "Read" "Bash(git log *)"` | **Nobody is there to approve.** Pre-approve exactly what's needed; anything else is denied |
| `--disallowedTools "Edit" "Write"` | Make sure some tools are never used |
| `--permission-mode plan\|acceptEdits\|…` | The same modes as `Shift+Tab` |
| `--max-budget-usd 0.50` | **A hard cost cap. Always set one** (an agent loop can run for a while) |
| `--json-schema` | Structured output, the same idea as Phase 1 lesson 04, for the whole agent run |
| `--append-system-prompt "…"` | Add instructions for this run |
| `--bare` | Skip CLAUDE.md, hooks, skills, plugins and MCP: fast and reproducible (needs `ANTHROPIC_API_KEY`) |

The JSON result has `result`, `structured_output`, `is_error`, `subtype`, `num_turns`, `total_cost_usd`,
`usage` and `session_id`. Your scripts should check `is_error` and log the cost.

**Read and run** [`weekly_summary.sh`](weekly_summary.sh): it combines `git log`, the course MCP server
and a JSON schema into a study report.
```bash
bash 08-claude-code/weekly_summary.sh       # ≈ $0.20 per run with the default model
```

> ⚠️ **GOTCHA:** headless + broad permissions + untrusted input = danger. A CI job that runs `claude -p` on an
> issue written by a stranger, with `Bash` allowed, is a prompt-injection target. Give automation the
> **narrowest** tools, a budget cap, and no secrets it doesn't need.

> 💡 **WHY not just call the Messages API?** For a single prompt, do (Phase 1). `claude -p` is worth it when
> the job needs the *agent*: reading files, running commands, looping until done.

## 2. GitHub Actions: `@claude` on issues and PRs

In a repo on github.com, run `/install-github-app` inside Claude Code. It installs the Claude GitHub app,
adds the API key as a repository secret, and creates a workflow like this one:

```yaml
# .github/workflows/claude.yml
name: Claude Code
on:
  issue_comment:               { types: [created] }
  pull_request_review_comment: { types: [created] }
jobs:
  claude:
    if: contains(github.event.comment.body, '@claude')
    runs-on: ubuntu-latest
    permissions: { contents: write, pull-requests: write, issues: write, id-token: write, actions: read }
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 1 }
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          # prompt: "Review this PR for ..."   ← add a prompt to run automatically instead of on @claude
          # claude_args: "--model claude-sonnet-5-5"   ← any claude CLI flags
```

Now commenting `@claude fix the failing test` on a PR makes Claude push a commit. The action reads your
repo's `CLAUDE.md` too, so your conventions apply in CI. For code review there's also `/code-review`
(run it locally on your branch before you open a PR).

## 3. Parallel sessions with git worktrees

One Claude session per task, each on **its own branch in its own folder**, so they never edit the same files:

```bash
claude --worktree rag-exercises       # creates .claude/worktrees/rag-exercises on branch worktree-rag-exercises
claude --worktree langchain-project   # in a second terminal: a separate copy, a separate branch
```

- Gitignored files (like `.env`) are **not** copied. List them in a `.worktreeinclude` file (gitignore syntax).
- Worktrees with no changes are cleaned up when you exit. Otherwise you're asked; or use `git worktree remove`.
- Subagents can do the same: `isolation: worktree` in their frontmatter (lesson 05).

> 💡 **WHY:** this is how one engineer supervises several agents: you plan and review, they implement in
> parallel. It's also a real-world version of Phase 4's map-reduce pattern.

## 4. Hands-on
1. Run `weekly_summary.sh`. Then remove `"mcp__course__course_progress"` from `--allowedTools` and run it again.
   What does the JSON show under `permission_denials`, and how did the agent cope?
2. **Pre-commit review:** a script `review_staged.sh` that pipes `git diff --cached` into
   `claude -p` with `--json-schema` returning `{"blocking_issues": [...], "suggestions": [...]}`, and **exits 1**
   if there are blocking issues. Then hook it into git: `.git/hooks/pre-commit`.
3. If your course repo is on GitHub: run `/install-github-app`, open an issue *"@claude add a 🧪 TRY suggestion
   to lesson 02 of 01-llm-basics"* and review the PR it opens. Would you merge it?
4. Do two exercises in parallel with `claude --worktree`, then merge both branches.

## Write it down
`notes/interview-qa.md`: *"How would you run an AI agent safely in CI? What can go wrong?"*
