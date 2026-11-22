# Phase 3 exercises

## Warm-up
1. **Explain it.** What is a Runnable? What does `prompt | model | parser` build? What does `create_agent`
   do, in terms of your Phase 1 loop? Write the answers in `notes/interview-qa.md`.
2. **Read the source.** Ctrl/Cmd-click `create_agent` in VS Code and find where it decides to go
   from the "model" node to the "tools" node. Which field of the AIMessage does it check?

## LCEL and structured output
3. **Ticket triage pipeline.** One chain: classify a ticket (structured output) → if category is "bug",
   draft a reply asking for steps to reproduce; otherwise draft a normal reply. Hint: `RunnableLambda`
   with an `if`, or look up `RunnableBranch`. (In Phase 4 you'll do this as a LangGraph router.)
4. **Batch eval.** Run your classifier from lesson 02 over 20 tickets with `.batch(..., max_concurrency=5)`
   and time it against a plain `for` loop.

## Agents
5. **Port lesson 06 of Phase 2.** Rebuild `02-rag/06_agentic_rag.py` with `create_agent`. Count the lines.
   Then compare the traces: same number of model calls? Same queries?
6. **Tool error handling.** Make `lookup_order` raise `ValueError` for unknown ids. What does the agent see?
   Then write a `@wrap_tool_call` middleware that turns any exception into a friendly ToolMessage.
7. **Structured agent output.** Give `create_agent` a `response_format=SupportReply` (a Pydantic model with
   `answer`, `citations`, `needs_human: bool`) and read `result["structured_response"]`.

## LangSmith
8. **Bug hunt, round 2.** Ask a friend (or an LLM) to introduce a subtle bug into one of the project's tools.
   Find it using only LangSmith. Write down which part of the trace gave it away.
9. **Tag everything.** Add `metadata={"user": ..., "feature": ...}` to the project's runs. In LangSmith,
   build a filter that shows the 5 most expensive runs. What made them expensive?

## Stretch
10. **Provider swap.** If you have another provider's key, run lessons 01–03 with a different
    `init_chat_model` string. What breaks? (Usually: server tools, structured-output methods, cost.)
