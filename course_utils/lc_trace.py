"""
course_utils.lc_trace: the same 📤 / 📥 / ⚙️ / 🔎 panels as course_utils.trace, for LangChain
and LangGraph runs.

    from course_utils.lc_trace import Tracer

    tracer = Tracer()
    model.invoke("hi", config={"callbacks": [tracer]})
    agent.invoke({"messages": [...]}, config={"callbacks": [tracer]})

HOW IT WORKS: LangChain fires *callback events* at each step of a run: chat model starts,
LLM ends, tool starts, tool ends, retriever ends... A callback handler is an object with
methods named after those events (on_chat_model_start, on_tool_end, ...). LangChain calls
them for you, passing the messages, outputs and run ids.

LangSmith uses exactly this mechanism: when LANGSMITH_TRACING=true, LangChain adds a
LangSmith handler that sends the same events to the web UI. So this file is a tiny local
LangSmith, and reading it shows you what LangSmith records.

Uses the same TRACE=full|brief|off and TRACE_MAX_CHARS settings from .env.
"""

import time
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from rich.markup import escape
from rich.panel import Panel

from course_utils import trace as t  # reuse rendering helpers, prices and totals


def _msg_role(m: BaseMessage) -> str:
    # LangChain message types: system, human (= user), ai (= assistant), tool (= tool result)
    return {"human": "human (user)", "ai": "ai (assistant)", "tool": "tool (result)"}.get(m.type, m.type)


def _render_message(m: BaseMessage) -> list[str]:
    lines = t._render_content(m.content) if m.content else []
    if m.type == "ai":
        # LangChain normalises every provider's tool requests into AIMessage.tool_calls.
        # Anthropic's raw tool_use blocks are already shown via content, so only add them if absent.
        has_blocks = isinstance(m.content, list) and any(t._get(b, "type") == "tool_use" for b in m.content)
        for call in getattr(m, "tool_calls", []) or []:
            if not has_blocks:
                lines.append(f"🔧 [bold yellow]tool_call[/] name=[yellow]{call['name']}[/] id={call['id']}\n"
                             f"   args = {escape(t._short(t._json(call['args'])))}")
    if m.type == "tool":
        lines = [f"📥 [bold green]ToolMessage[/] name={getattr(m, 'name', '')} for id={m.tool_call_id}\n"
                 f"   content = {escape(t._short(m.content if isinstance(m.content, str) else t._json(m.content)))}"]
    return lines


def _summary(m: BaseMessage) -> str:
    if m.type == "ai" and getattr(m, "tool_calls", None):
        calls = ", ".join(f"{c['name']}({t._one_line(t._json(c['args']), 30)})" for c in m.tool_calls)
        return escape(f"tool_calls: {calls}")
    if m.type == "tool":
        return escape(f"result for {m.tool_call_id}: {t._one_line(m.content, 50)}")
    return t._summary(m.content)


def _sig(m: BaseMessage) -> tuple:
    return (m.type, m.id or str(m.content)[:200])


class Tracer(BaseCallbackHandler):
    """Prints what goes in and out of every model call, tool call and retriever in a LangChain run."""

    def __init__(self):
        self._starts: dict[UUID, float] = {}
        self._tool_inputs: dict[UUID, tuple[str, object]] = {}
        self._queries: dict[UUID, str] = {}
        self._models: dict[UUID, str] = {}
        self._prev: list[tuple] = []

    # ---------------------------------------------------------------- model calls
    def on_chat_model_start(self, serialized, messages, *, run_id, invocation_params=None, **kwargs):
        t._call_no += 1
        self._starts[run_id] = time.perf_counter()
        params = invocation_params or kwargs.get("invocation_params") or {}
        model = params.get("model") or params.get("model_name") or (kwargs.get("metadata") or {}).get("ls_model_name", "?")
        self._models[run_id] = model
        msgs: list[BaseMessage] = messages[0]
        tools = params.get("tools") or []
        tool_names = [x.get("name") or x.get("function", {}).get("name") for x in tools if isinstance(x, dict)]
        name = kwargs.get("name") or (serialized or {}).get("name", "")
        title = f"📤 REQUEST #{t._call_no}: {name} → {model}"

        sig = [_sig(m) for m in msgs]
        already = len(self._prev) if self._prev and sig[:len(self._prev)] == self._prev else 0
        self._prev = sig

        level = t._level()
        if level == "off":
            return
        if level == "brief":
            t.console.print(f"[cyan]{escape(title)}[/]  messages={len(msgs)}  tools={tool_names or '-'}")
            return
        lines = [f"[bold]model[/]: {model}    [bold]max_tokens[/]: {params.get('max_tokens')}"]
        if tool_names:
            lines.append(f"[bold]tools offered[/]: {', '.join(map(str, tool_names))}")
        lines += ["", f"[bold]messages[/]: {len(msgs)} in total "
                      "[dim](LangChain message objects; converted to the provider's format before sending)[/]"]
        for i, m in enumerate(msgs):
            idx = escape(f"[{i}]")
            if i < already:
                lines.append(f"[dim]  {idx} {_msg_role(m):<14} (sent before) {_summary(m)}[/]")
            else:
                tag = "[bold green]NEW[/] " if already else ""
                lines.append(f"  {idx} {tag}[bold]{_msg_role(m)}[/]  [dim]{type(m).__name__}[/]")
                for r in _render_message(m):
                    lines.append("      " + t._indent(r))
        t.console.print(Panel("\n".join(lines), title=title, title_align="left", border_style="cyan"))

    def on_llm_end(self, response, *, run_id, **kwargs):
        started = self._starts.pop(run_id, None)
        elapsed = f"{time.perf_counter() - started:.2f}s" if started else "?"
        gen = response.generations[0][0]
        msg = getattr(gen, "message", None)
        if msg is None:
            return
        usage = getattr(msg, "usage_metadata", None) or {}
        model = (msg.response_metadata or {}).get("model_name") or self._models.pop(run_id, "?")
        pin, pout = t.PRICES.get(model, t.PRICES["claude-opus-5-5"])
        tin, tout = usage.get("input_tokens", 0), usage.get("output_tokens", 0)
        cost = tin / 1e6 * pin + tout / 1e6 * pout
        t._totals["calls"] += 1
        t._totals["in"] += tin
        t._totals["out"] += tout
        t._totals["cost"] += cost
        stop = (msg.response_metadata or {}).get("stop_reason") or (msg.response_metadata or {}).get("finish_reason")

        level = t._level()
        if level == "off":
            return
        title = f"📥 RESPONSE #{t._call_no}: {type(msg).__name__}"
        if type(msg).__name__ == "AIMessageChunk":  # streamed: tokens were just printed on this line
            print()
        if level == "brief":
            calls = [c["name"] for c in getattr(msg, "tool_calls", []) or []]
            t.console.print(f"[magenta]{escape(title)}[/]  stop_reason={stop}  tool_calls={calls or '-'}  "
                            f"tokens={tin}→{tout}  ${cost:.5f}  {elapsed}")
            return
        lines = [f"[bold]stop_reason[/]: [bold yellow]{stop}[/]  [dim]→ {t.STOP_REASONS.get(stop, '')}[/]", ""]
        lines.append("[bold]content[/]:")
        for r in t._render_content(msg.content) if msg.content else ["[dim](empty)[/]"]:
            lines.append("  " + t._indent(r, 4))
        calls = getattr(msg, "tool_calls", []) or []
        if calls:
            lines.append("")
            lines.append(f"[bold]tool_calls[/] [dim](LangChain's provider-neutral view of the tool requests)[/]: "
                         + escape(t._short(t._json([{"name": c["name"], "args": c["args"]} for c in calls]))))
        thinking = (usage.get("output_token_details") or {}).get("reasoning")
        lines.append("")
        lines.append(f"[bold]tokens[/]: {tin} in → {tout} out" + (f" (of which {thinking} thinking)" if thinking else "")
                     + f"    [bold]cost[/]: ${cost:.6f}    [bold]time[/]: {elapsed}")
        t.console.print(Panel("\n".join(lines), title=title, title_align="left", border_style="magenta"))

    # ---------------------------------------------------------------- tools
    def on_tool_start(self, serialized, input_str, *, run_id, inputs=None, **kwargs):
        self._starts[run_id] = time.perf_counter()
        name = (serialized or {}).get("name") or kwargs.get("name", "?")
        self._tool_inputs[run_id] = (name, inputs if inputs is not None else input_str)

    def _tool_done(self, run_id, result, is_error):
        started = self._starts.pop(run_id, None)
        name, args = self._tool_inputs.pop(run_id, ("?", {}))
        text = getattr(result, "content", result)
        t.show_tool_call(name, args if isinstance(args, dict) else {"input": args},
                         text if isinstance(text, str) else t._json(text), is_error,
                         seconds=time.perf_counter() - started if started else None)

    def on_tool_end(self, output, *, run_id, **kwargs):
        status = getattr(output, "status", "success")
        self._tool_done(run_id, output, is_error=(status == "error"))

    def on_tool_error(self, error, *, run_id, **kwargs):
        self._tool_done(run_id, f"{type(error).__name__}: {error}", is_error=True)

    # ---------------------------------------------------------------- retrievers
    def on_retriever_start(self, serialized, query, *, run_id, **kwargs):
        self._queries[run_id] = query

    def on_retriever_end(self, documents, *, run_id, **kwargs):
        query = self._queries.pop(run_id, "?")
        results = [{"id": d.metadata.get("id") or d.metadata.get("source", "?"),
                    "text": d.page_content,
                    "score": d.metadata.get("score", "-")} for d in documents]
        t.show_retrieval(query, results, label="retriever")
