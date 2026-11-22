# Phase 2 exercises

Do them in order. Each one builds a skill you'll use in the project or in interviews.

## Warm-up
1. **Explain it.** Without looking: what is an embedding? Why do we chunk? What is RRF?
   Write your answers in `notes/interview-qa.md`.
2. **Similarity intuition.** In lesson 01, add 5 sentences of your own (two pairs that mean the same
   thing, one unrelated) and check whether the matrix shows the pairs.

## Retrieval
3. **Chunk-size sweep.** Copy the eval from lesson 05 into a new file `my_eval.py`. Run it for
   `max_chars` in `[200, 400, 600, 1000, 1500]` and print a table: chunk size × method → hit@3 / MRR.
   Which size wins? Is it the same for every method?
4. **Harder eval set.** Add 8 questions to `data/eval_questions.json`:
   2 paraphrases with no shared words, 2 with error codes, 2 that need two documents, and 2 that
   the docs can't answer (`"expected_source": null`). Update `evaluate()` to handle `null`.
5. **Freshness filter.** Make `HybridRetriever.search` accept `min_updated="2025-01-01"`, and check that
   "Can I get my money back?" no longer returns `faq_2024.md`.
6. **Contextual chunks.** Prepend `"{title} > {heading}: "` to each chunk's text *before embedding*
   (but show the original text to the LLM). Re-run the eval. Did it help?

## Generation
7. **Hallucination hunt.** In lesson 04, delete all the rules from `SYSTEM` except "answer the question".
   Ask 5 questions the docs can't answer. How often does the model make something up?
8. **Citations API.** Read the Claude API *citations* docs (linked in the README) and rebuild
   section 5 of lesson 04 using `documents` content blocks with `citations: {"enabled": true}` instead
   of prompt-based citations. Compare the two.

## Agentic
9. **Search budget.** In lesson 06, stop the agent from calling `search_help_center` more than 4 times
   per question (return an error string from the tool once the budget is used up). What does the model do?
10. **Fix Phase 1.** Replace the keyword `search_docs` in `01-llm-basics/06_agent_loop.py` with a
    `VectorIndex` over its `KNOWLEDGE_BASE`. Do the irrelevant results disappear?

## Stretch
11. **pgvector.** Run Postgres with Docker (`docker run -e POSTGRES_PASSWORD=pw -p 5432:5432 pgvector/pgvector:pg17`),
    store the Nimbus chunks in a `vector(384)` column, and query with `ORDER BY embedding <=> $1 LIMIT 4`.
    You'll use Postgres again for LangGraph checkpoints in Phase 7.
