"""
course_utils.trace: see EXACTLY what goes in and out of every LLM call.

Usage in a lesson:

    from course_utils import trace

    request = dict(model=MODEL, max_tokens=16000, messages=messages, tools=TOOLS)
    trace.show_request(request, label="ask the model")    # 📤 what we SEND
    response = client.messages.create(**request)
    trace.show_response(response)                          # 📥 what we GET BACK
    ...
    trace.show_tool_call(name, tool_input, result)         # ⚙️  what OUR code ran

Control the detail level from .env (no code changes needed):
    TRACE=full | brief | off          (default: full)
    TRACE_MAX_CHARS=500               (cut long texts; 0 = never cut)

Phase 2 (RAG) adds:
    trace.show_vector(text, vector)            # 🔢 what an embedding looks like
    trace.show_chunks(chunks)                  # ✂️  how documents were split
    trace.show_retrieval(query, results)       # 🔎 what the search returned, with scores

Phase 3 (LangChain) adds course_utils/lc_trace.py, which prints the same panels for
LangChain/LangGraph runs.

This is a "poor man's LangSmith". In Phase 3 you'll get the same view in a web UI.
"""

import json
import os
import time

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

console = Console()

# Prices in USD per 1M tokens (input, output). Used only to show cost in traces.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}

STOP_REASONS = {
    "end_turn": "the model finished its answer",
    "tool_use": "the model wants YOUR code to run tool(s), then send the results back",
    "max_tokens": "cut off! The answer hit max_tokens",
    "stop_sequence": "hit one of your stop sequences",
    "pause_turn": "a long server-side tool turn paused. Send the conversation back to continue",
    "refusal": "the model declined the request",
}

# --- module state (lets us number calls and spot which messages are new) -----------
_call_no = 0
_last_messages_id = None
_last_messages_len = 0
_request_started = None
_clock_start = time.perf_counter()
_totals = {"calls": 0, "in": 0, "out": 0, "cost": 0.0}


# =====================================================================================
# Settings
# =====================================================================================
def _level() -> str:
    # Read on every call (not at import) so load_dotenv() in the lesson has already run.
    return os.getenv("TRACE", "full").strip().lower()


def _max_chars() -> int:
    try:
        return int(os.getenv("TRACE_MAX_CHARS", "500"))
    except ValueError:
        return 500


# =====================================================================================
# Small helpers
# =====================================================================================
def _get(obj, key, default=None):
    """Read a field from either a dict (what WE build) or an SDK object (what the API returns)."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _plain(obj):
    """Turn SDK/Pydantic objects into plain dicts/lists so they can be shown as JSON."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(exclude_none=True)
    if isinstance(obj, (list, tuple)):
        return [_plain(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    return obj


def _json(obj) -> str:
    return json.dumps(_plain(obj), ensure_ascii=False, default=str)


def _short(text, limit: int | None = None) -> str:
    text = str(text)
    limit = _max_chars() if limit is None else limit
    if limit <= 0 or len(text) <= limit:
        return text
    return text[:limit] + f" …[+{len(text) - limit} chars]"


def _one_line(text, limit: int = 90) -> str:
    return _short(" ".join(str(text).split()), limit)


def _cost(usage, model: str) -> float:
    pin, pout = PRICES.get(model, PRICES["claude-opus-5-5"])
    return usage.input_tokens / 1e6 * pin + usage.output_tokens / 1e6 * pout


def _indent(text: str, spaces: int = 6) -> str:
    pad = " " * spaces
    return text.replace("\n", "\n" + pad)


# =====================================================================================
# Rendering one content block (text, tool_use, tool_result, thinking, ...)
# =====================================================================================
def _render_block(block) -> str:
    t = _get(block, "type")

    if t == "text":
        return f"💬 [bold]text[/]: {escape(_short(_get(block, 'text', '')))}"

    if t == "tool_use":
        return (
            f"🔧 [bold yellow]tool_use[/]  name=[yellow]{_get(block, 'name')}[/]  id={_get(block, 'id')}\n"
            f"   input = {escape(_short(_json(_get(block, 'input'))))}"
        )

    if t == "tool_result":
        content = _get(block, "content")
        content = content if isinstance(content, str) else _json(content)
        err = "  [bold red](is_error=True)[/]" if _get(block, "is_error") else ""
        return (
            f"📥 [bold green]tool_result[/]  for id={_get(block, 'tool_use_id')}{err}\n"
            f"   content = {escape(_short(content))}"
        )

    if t == "server_tool_use":
        return (
            f"🌐 [bold blue]server_tool_use[/] (runs on Anthropic's servers)  name={_get(block, 'name')}\n"
            f"   input = {escape(_short(_json(_get(block, 'input'))))}"
        )

    if t and t.endswith("_tool_result"):  # e.g. web_search_tool_result
        content = _get(block, "content")
        if isinstance(content, list):
            titles = [escape(_one_line(_get(r, "title", "?"), 60)) for r in content[:5]]
            more = f" (+{len(content) - 5} more)" if len(content) > 5 else ""
            return f"📄 [bold blue]{t}[/]: {len(content)} results\n   " + "\n   ".join(titles) + more
        return f"📄 [bold blue]{t}[/]: {escape(_short(_json(content)))}"

    if t == "thinking":
        txt = _get(block, "thinking") or ""
        shown = escape(_short(txt)) if txt else "[dim](reasoning not shown; still billed as output tokens)[/]"
        return f"🧠 [magenta]thinking[/]: {shown}"

    if t == "redacted_thinking":
        return "🧠 [magenta]redacted_thinking[/] [dim](encrypted reasoning; pass it back unchanged)[/]"

    return f"▫️  {t}: {escape(_short(_json(block)))}"


def _render_content(content) -> list[str]:
    if isinstance(content, str):
        return [f"💬 [bold]text[/]: {escape(_short(content))}"]
    return [_render_block(b) for b in content]


def _summary(content) -> str:
    """One short line describing a message (used for messages already shown before)."""
    if isinstance(content, str):
        return escape(_one_line(content))
    parts = []
    for b in content:
        t = _get(b, "type")
        if t == "text":
            parts.append(f"text: {_one_line(_get(b, 'text', ''), 50)}")
        elif t == "tool_use":
            parts.append(f"tool_use {_get(b, 'name')}({_one_line(_json(_get(b, 'input')), 40)})")
        elif t == "tool_result":
            parts.append(f"tool_result: {_one_line(_get(b, 'content'), 40)}")
        else:
            parts.append(str(t))
    return escape(" | ".join(parts))


# =====================================================================================
# Public API
# =====================================================================================
def step(title: str) -> None:
    """Print a section divider: use it to mark the stages of a lesson."""
    if _level() != "off":
        console.rule(f"[bold]{escape(title)}[/]")


def note(text: str) -> None:
    """A short explanation printed in the trace."""
    if _level() == "full":
        console.print(f"[dim]ℹ️  {escape(text)}[/]")


def show_request(request: dict, label: str = "") -> None:
    """Show everything we're about to send to the model."""
    global _call_no, _last_messages_id, _last_messages_len, _request_started
    _call_no += 1
    _request_started = time.perf_counter()
    level = _level()
    if level == "off":
        return

    messages = request.get("messages", [])
    tools = request.get("tools") or []
    tool_names = [_get(t, "name") for t in tools]
    title = f"📤 REQUEST #{_call_no}" + (f": {label}" if label else "")

    # Which messages did we already show in the previous request? (same list, grown)
    same_list = id(messages) == _last_messages_id and _last_messages_len <= len(messages)
    already_shown = _last_messages_len if same_list else 0
    _last_messages_id, _last_messages_len = id(messages), len(messages)

    if level == "brief":
        console.print(
            f"[cyan]{escape(title)}[/]  model={request.get('model')}  "
            f"messages={len(messages)}  tools={tool_names or '-'}"
        )
        return

    lines = [f"[bold]model[/]: {request.get('model')}    [bold]max_tokens[/]: {request.get('max_tokens')}"]

    system = request.get("system")
    if system:
        sys_text = system if isinstance(system, str) else _json(system)
        lines.append(f"[bold]system[/]: {escape(_short(sys_text))}")

    if tool_names:
        lines.append(f"[bold]tools offered[/]: {', '.join(map(str, tool_names))}")

    for key, value in request.items():
        if key in ("model", "max_tokens", "system", "tools", "messages"):
            continue
        if isinstance(value, type):  # e.g. output_format=SomePydanticModel
            shown = f"{value.__name__} (Pydantic schema: the output must match it)"
        else:
            shown = _short(_json(value), 200)
        lines.append(f"[bold]{escape(key)}[/]: {escape(shown)}")

    lines.append("")
    lines.append(
        f"[bold]messages[/]: {len(messages)} in total. "
        "[dim]The model sees ALL of them on every call (it has no memory of its own).[/]"
    )
    for i, msg in enumerate(messages):
        role = _get(msg, "role")
        content = _get(msg, "content")
        idx = escape(f"[{i}]")
        if i < already_shown:
            lines.append(f"[dim]  {idx} {role:<9} (sent before) {_summary(content)}[/]")
        else:
            tag = "[bold green]NEW[/] " if already_shown else ""
            lines.append(f"  {idx} {tag}[bold]{role}[/]")
            for rendered in _render_content(content):
                lines.append("      " + _indent(rendered))

    console.print(Panel("\n".join(lines), title=title, title_align="left", border_style="cyan"))


def show_response(response, label: str = "") -> None:
    """Show what came back: every content block, why it stopped, tokens, cost, time."""
    elapsed = time.perf_counter() - _request_started if _request_started else None
    usage = response.usage
    cost = _cost(usage, response.model)
    _totals["calls"] += 1
    _totals["in"] += usage.input_tokens
    _totals["out"] += usage.output_tokens
    _totals["cost"] += cost

    level = _level()
    if level == "off":
        return

    stop = response.stop_reason
    meaning = STOP_REASONS.get(stop, "")
    timing = f"{elapsed:.2f}s" if elapsed is not None else "?"
    title = f"📥 RESPONSE #{_call_no}" + (f": {label}" if label else "")
    block_types = [b.type for b in response.content]

    if level == "brief":
        console.print(
            f"[magenta]{escape(title)}[/]  stop_reason={stop}  blocks={block_types}  "
            f"tokens={usage.input_tokens}→{usage.output_tokens}  ${cost:.5f}  {timing}"
        )
        return

    lines = [f"[bold]stop_reason[/]: [bold yellow]{stop}[/]  [dim]→ {meaning}[/]", ""]
    lines.append(f"[bold]content[/]: {len(response.content)} block(s) {block_types}")
    for i, block in enumerate(response.content):
        lines.append(f"  {escape(f'[{i}]')} " + _indent(_render_block(block)))

    parsed = getattr(response, "parsed_output", None)
    if parsed is not None:
        lines.append("")
        lines.append(f"[bold]parsed_output[/] ({type(parsed).__name__}): {escape(_short(_json(parsed)))}")

    details = getattr(usage, "output_tokens_details", None)
    thinking = getattr(details, "thinking_tokens", None) if details else None
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    lines.append("")
    usage_line = f"[bold]tokens[/]: {usage.input_tokens} in → {usage.output_tokens} out"
    if thinking:
        usage_line += f" (of which {thinking} thinking)"
    if cache_read:
        usage_line += f", {cache_read} read from cache"
    lines.append(usage_line + f"    [bold]cost[/]: ${cost:.6f}    [bold]time[/]: {timing}")

    console.print(Panel("\n".join(lines), title=title, title_align="left", border_style="magenta"))


def show_tool_call(name: str, tool_input: dict, result: str, is_error: bool = False,
                   seconds: float | None = None) -> None:
    """Show a tool that OUR code executed on the model's behalf."""
    level = _level()
    if level == "off":
        return
    timing = f"  ({seconds * 1000:.0f} ms)" if seconds is not None else ""
    status = "[bold red]ERROR[/]" if is_error else "[green]ok[/]"
    if level == "brief":
        console.print(f"[yellow]⚙️  ran {name}({escape(_one_line(_json(tool_input), 60))})[/] → {status}{timing}")
        return
    body = (
        f"[bold]function[/]: {name}\n"
        f"[bold]arguments[/] (chosen by the model): {escape(_short(_json(tool_input)))}\n"
        f"[bold]result[/] {status}{timing}: {escape(_short(result))}"
    )
    console.print(Panel(body, title="⚙️  YOUR CODE RUNS THE TOOL", title_align="left", border_style="yellow"))


def event(text: str) -> None:
    """A timestamped one-liner, handy for watching concurrent (async) work interleave."""
    if _level() != "off":
        console.print(f"[dim][+{time.perf_counter() - _clock_start:6.2f}s][/] {escape(text)}")


def reset_clock() -> None:
    global _clock_start
    _clock_start = time.perf_counter()


def show_totals(label: str = "Totals") -> None:
    """Print totals for all calls traced so far (calls, tokens, cost)."""
    if _level() == "off":
        return
    t = _totals
    console.print(
        f"[bold]📊 {escape(label)}[/]: {t['calls']} model call(s), "
        f"{t['in']} input + {t['out']} output tokens, ≈ ${t['cost']:.5f}"
    )


# =====================================================================================
# Phase 2: RAG views
# =====================================================================================
def show_vector(text: str, vector, label: str = "") -> None:
    """Show what an embedding is: a list of numbers."""
    if _level() == "off":
        return
    vals = ", ".join(f"{v:+.3f}" for v in list(vector)[:8])
    console.print(
        f"[bold]🔢 embedding{': ' + escape(label) if label else ''}[/] "
        f"\"{escape(_one_line(text, 50))}\" → [{vals}, … ] [dim]({len(vector)} numbers)[/]"
    )


def show_chunks(chunks: list[dict], label: str = "chunks", limit: int = 6) -> None:
    """Show how documents were split: id, size, and the start/end of each chunk."""
    level = _level()
    if level == "off":
        return
    sizes = [len(c["text"]) for c in chunks]
    head = (f"✂️  {label}: {len(chunks)} chunks, size min/avg/max = "
            f"{min(sizes)}/{sum(sizes) // len(sizes)}/{max(sizes)} chars")
    if level == "brief":
        console.print(escape(head))
        return
    table = Table(title=head, title_justify="left", show_lines=True)
    table.add_column("id", style="cyan", no_wrap=True)
    table.add_column("chars", justify="right")
    table.add_column("text (start … end)")
    for c in chunks[:limit]:
        t = c["text"]
        shown = t if len(t) <= 160 else t[:90] + "  …  " + t[-60:]
        shown = shown.replace("\n", "⏎ ")  # make line breaks visible (and the table shorter)
        table.add_row(escape(str(c.get("id", "?"))), str(len(t)), escape(shown))
    if len(chunks) > limit:
        table.caption = f"(+{len(chunks) - limit} more)"
    console.print(table)


def show_retrieval(query: str, results: list[dict], label: str = "", score_name: str = "score") -> None:
    """Show search results ranked: score, which chunk, and a snippet.

    Each result is a dict with at least "text" and "score", plus optional "id"/"source".
    """
    level = _level()
    if level == "off":
        return
    title = f"🔎 RETRIEVAL{': ' + label if label else ''}  query=\"{_one_line(query, 70)}\""
    if level == "brief":
        ids = [str(r.get("id", r.get("source", "?"))) for r in results]
        console.print(f"[green]{escape(title)}[/] → {escape(', '.join(ids))}")
        return
    table = Table(title=escape(title), title_justify="left")
    table.add_column("#", justify="right")
    table.add_column(score_name, justify="right", style="bold")
    table.add_column("chunk id", style="cyan", no_wrap=True)
    table.add_column("snippet")
    for rank, r in enumerate(results, start=1):
        score = r.get("score")
        score_s = f"{score:.3f}" if isinstance(score, (int, float)) else str(score)
        table.add_row(str(rank), score_s, escape(str(r.get("id", r.get("source", "?")))),
                      escape(_one_line(r["text"], 90)))
    console.print(table)
