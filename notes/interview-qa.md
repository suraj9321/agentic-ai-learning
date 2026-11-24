# Interview Q&A: in my own words

Answer each question after the lesson that covers it. Short, clear, with an example.
Rewrite answers as your understanding improves. This becomes your interview prep doc.

## Phase 0–1: LLM basics & agents
### What is a token, and why do engineers care?

### What does it mean that the model is "stateless"?

### Agent vs. workflow: what's the difference? When do you use each?

### Walk through a tool call, message by message.

### How do you keep an agent safe and within budget?

## Phase 2: RAG
### What is RAG, and when would you use it instead of fine-tuning?

### What is an embedding? How does semantic search work?

### How do you choose a chunk size? What does overlap do?

### Why use hybrid search? How does Reciprocal Rank Fusion work?

### What does a reranker do, and why not use it for the whole search?

### How do you evaluate a RAG system? (retrieval metrics vs answer quality)

### Your RAG bot gives a wrong answer. How do you debug it?

### How do you stop a RAG bot from hallucinating? From leaking one customer's data to another?

### Classic RAG vs agentic RAG: trade-offs?

## Phase 3: LangChain + LangSmith
### What is a Runnable / LCEL? When would you NOT use LCEL?

### What does `create_agent` do under the hood?

### How does a tool's docstring affect agent behaviour?

### How does conversation memory work in a LangChain agent (checkpointer, thread_id)?

### What is middleware in LangChain agents? Give 3 production uses.

### How do you debug an agent that gives a confident but wrong answer?

### LangChain vs the raw provider SDK: trade-offs? When would you pick each?

### What do you look at in a LangSmith trace? How do tags, metadata and feedback help in production?

## Phase 8: Claude Code & agent tooling
### Walk me through what happens inside a coding agent when I ask it to fix a failing test.

### How would you stop a coding agent from leaking secrets? Name at least three layers.

### What is progressive disclosure, and where does it show up in agent design?

### What is MCP, and how does it relate to tool calling? Tools vs resources vs prompts?

### Why do multi-agent systems use subagents? What's the trade-off?

### Prompt instructions vs hooks/middleware for agent guardrails: when do you need each?

### How would you run an AI agent safely in CI? What can go wrong?

### Raw API vs a framework vs an agent SDK: how do you choose for a new product?
