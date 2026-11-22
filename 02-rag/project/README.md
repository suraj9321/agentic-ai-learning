# 🛠 Mini-project: chat with your documents

A command-line chat over any folder of PDFs, Markdown, or text files, with page-level citations.

```bash
uv run python 02-rag/project/doc_chat.py                    # sample: docs/nimbus_employee_handbook.pdf
uv run python 02-rag/project/doc_chat.py ~/Documents/papers # your own folder
```

Example session:
```
📚 Indexed 1 file(s), 2 page(s)/doc(s), 4 chunks in 0.7s: nimbus_employee_handbook.pdf
🧑 How many vacation days do I get and can I carry them over?
🤖 - 25 days of paid vacation per year plus public holidays [nimbus_employee_handbook.pdf p.1]
   - up to 5 unused days carry over, to be used before 31 March [nimbus_employee_handbook.pdf p.1]
🧑 and what about parental leave for the secondary caregiver?
   ① rewrite → "parental leave entitlement for secondary caregiver employee handbook"
🤖 - 8 weeks of fully paid leave, regardless of country [nimbus_employee_handbook.pdf p.1]
🧑 /sources
```

## Read the code in this order
1. `DocChat.__init__`: load → chunk → `HybridRetriever` (everything from lessons 02–05).
2. `rewrite()`: why does the *first* message skip this step? Why use a cheaper model for it?
3. `ask()`: where the documents go (only the latest message) and why the history doesn't keep them.
4. `format_docs()`: how `source` and `page` become `[file p.N]` citations.

## Your tasks (do at least 1–4)
1. **Use your own documents.** Drop 3–5 real PDFs into a folder (papers, a rental contract, product
   manuals) and chat with them. Write down 3 questions it got wrong and *why* (retrieval or generation?
   Use `/sources` to check).
2. **Persist the index.** Re-embedding every start is slow for big folders. Store chunks + vectors in
   Chroma (lesson 03) and only re-embed files whose modification time changed (`path.stat().st_mtime`).
3. **Clickable citations.** After each answer, print the cited chunks' first 200 characters under a
   "Sources" heading, only for sources the answer actually cited (parse `[file p.N]` with a regex).
4. **"I don't know" guard.** If the best rerank score is below a threshold (find one by looking at
   scores for unanswerable questions), skip the LLM call and reply "I couldn't find that in your
   documents." That saves money *and* prevents hallucination.
5. **Stretch: scanned PDFs.** Some PDFs have no text layer (`load_documents` skips empty pages).
   Send the page as an image to Claude instead (look up "vision" / PDF support in the Claude docs).
6. **Stretch: evaluation.** Write 10 question → expected-page pairs for your own documents and measure
   hit@5. Change `max_chars` and `k`. Keep the best settings.

## Portfolio
A README with a GIF of a session plus a table from task 6 ("hit@5 went from 70% to 90% after hybrid
search + reranking") is exactly what interviewers want to see: you **measured** your RAG system.
