"""
Lesson 04: RAG with LangChain, mapping Phase 2 onto LangChain's building blocks.

    Phase 2 (by hand)                 LangChain
    ─────────────────────────────     ──────────────────────────────────────
    {"text": ..., "source": ...}      Document(page_content=..., metadata={...})
    chunk_documents()                 RecursiveCharacterTextSplitter
    embed_documents / embed_query     an Embeddings class
    VectorIndex / Chroma              a VectorStore (Chroma, PGVector, Pinecone, ...)
    index.search(query, k)            a Retriever: retriever.invoke(query)
    format_context + prompt + call    an LCEL chain

What you'll learn:
  - Each block above, and the interfaces that make them swappable
  - A RAG chain in LCEL that also returns its sources
  - Plugging YOUR OWN retriever (Phase 2's hybrid + rerank) into LangChain
  - Agentic RAG with create_agent in a few lines

Run:  uv run python 03-langchain/04_rag_with_langchain.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_chroma import Chroma
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.tools import create_retriever_tool
from langchain_text_splitters import RecursiveCharacterTextSplitter

from course_utils import trace
from course_utils.lc_trace import Tracer
from course_utils.rag import HybridRetriever, chunk_documents, langchain_embeddings, load_documents

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")
model = init_chat_model(f"anthropic:{MODEL}", max_tokens=16000)
CONFIG = {"callbacks": [Tracer()]}
NIMBUS = Path(__file__).parent.parent / "02-rag" / "data" / "nimbus"


# ---------------------------------------------------------------------------
# 1. Documents and splitting
# ---------------------------------------------------------------------------
trace.step("1. Document objects + RecursiveCharacterTextSplitter")

raw = load_documents(NIMBUS)  # our Phase 2 loader (LangChain has loaders too: see the README)
docs = [Document(page_content=d["text"], metadata={k: v for k, v in d.items() if k != "text" and v is not None})
        for d in raw]
print(f"{len(docs)} Documents. Example metadata: {docs[0].metadata}")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=600, chunk_overlap=100,
    separators=["\n## ", "\n\n", "\n", ". ", " ", ""],  # the same order as our _split()
)
splits = splitter.split_documents(docs)
counters: dict[str, int] = {}
for s in splits:  # give each chunk an id for citations: file#0, file#1, ... per file
    n = counters.get(s.metadata["source"], 0)
    s.metadata["id"] = f"{s.metadata['source']}#{n}"
    counters[s.metadata["source"]] = n + 1
print(f"LangChain splitter: {len(splits)} chunks.   Our chunk_documents(): {len(chunk_documents(raw))} chunks.")
# Same idea, slightly different details. Look at the search results below: LangChain's splitter
# keeps a lone "# Refunds, invoices and billing" heading as its own chunk, which our
# chunk_documents() merges into the next piece (min_chars).
# 💡 WHY know both: in interviews, "what does RecursiveCharacterTextSplitter do?" is common,
# and you can now answer "it's this 40-line function, here's how I'd tune it".


# ---------------------------------------------------------------------------
# 2. Embeddings + vector store + retriever
# ---------------------------------------------------------------------------
trace.step("2. Embeddings → Chroma → retriever")

# langchain_embeddings() wraps our local fastembed model in LangChain's Embeddings interface.
# Open course_utils/rag.py and look at it: a class with just embed_documents() and embed_query().
# 🐍 PYTHON NOTE: `class LocalEmbeddings(Embeddings)` is INHERITANCE. LocalEmbeddings
# promises to provide the methods that the Embeddings "interface" requires, so any LangChain
# code that accepts an Embeddings object accepts ours. That's how every integration plugs in.
embeddings = langchain_embeddings()

vector_store = Chroma(
    collection_name="nimbus-langchain",
    embedding_function=embeddings,
    collection_configuration={"hnsw": {"space": "cosine"}},
    # persist_directory=".cache/chroma-lc",  # uncomment to keep it on disk between runs
)
vector_store.add_documents(splits, ids=[s.metadata["id"] for s in splits])

for doc, score in vector_store.similarity_search_with_relevance_scores("Can I get my money back?", k=3):
    print(f"  {score:.3f}  {doc.metadata['id']:<26} {doc.page_content[:60]!r}")

# A retriever is the "search" interface: string in, list[Document] out. It's a Runnable.
retriever = vector_store.as_retriever(search_kwargs={"k": 4})
found = retriever.invoke("the bot never joined my call", config=CONFIG)  # → 🔎 panel
print(f"retriever.invoke → {len(found)} {type(found[0]).__name__}s")


# ---------------------------------------------------------------------------
# 3. A RAG chain in LCEL
# ---------------------------------------------------------------------------
trace.step("3. RAG chain: retriever | format | prompt | model | parser")

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer ONLY from the documents. Cite ids like [pricing.md#2]. If documents disagree, "
               "trust the newest `updated` date. If the answer isn't there, say you don't know."),
    ("human", "{context}\n\n<question>{question}</question>"),
])


def format_docs(documents: list[Document]) -> str:
    return "\n".join(
        f'<document id="{d.metadata["id"]}" updated="{d.metadata.get("updated", "")}">\n{d.page_content}\n</document>'
        for d in documents)


rag_chain = (
    # A dict in a chain = RunnableParallel: both keys are computed from the SAME input (the question).
    {"context": retriever | RunnableLambda(format_docs), "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)
print("💬", rag_chain.invoke("How long do I have to request a refund?", config=CONFIG))

# Return the sources too (for showing citations in a UI):
#   .assign(key=...) adds a new key to the dict flowing through the chain, keeping the old ones.
rag_with_sources = (
    RunnablePassthrough.assign(docs=lambda x: retriever.invoke(x["question"]))
    .assign(answer=lambda x: (prompt | model | StrOutputParser()).invoke(
        {"context": format_docs(x["docs"]), "question": x["question"]}))
)
out = rag_with_sources.invoke({"question": "Which plans have the public API?"}, config=CONFIG)
print("💬", out["answer"])
print("   sources:", [d.metadata["id"] for d in out["docs"]])


# ---------------------------------------------------------------------------
# 4. Plug in your own retriever
# ---------------------------------------------------------------------------
trace.step("4. A custom retriever: Phase 2's hybrid + rerank, inside LangChain")


class NimbusHybridRetriever(BaseRetriever):
    """Wraps our HybridRetriever so LangChain can use it like any other retriever."""

    # 🐍 PYTHON NOTE: BaseRetriever is a Pydantic model, so its fields are declared like this.
    # arbitrary_types_allowed lets a field hold a non-Pydantic object (our HybridRetriever).
    hybrid: object
    k: int = 4
    model_config = {"arbitrary_types_allowed": True}

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> list[Document]:
        return [Document(page_content=h["text"],
                         metadata={"id": h["id"], "source": h["source"], "updated": h.get("updated", ""),
                                   "score": round(h["score"], 3)})
                for h in self.hybrid.search(query, k=self.k)]


hybrid = NimbusHybridRetriever(hybrid=HybridRetriever(chunk_documents(raw)))
# Swap it into the SAME chain. Nothing else changes: that's the point of the interfaces.
hybrid_chain = ({"context": hybrid | RunnableLambda(format_docs), "question": RunnablePassthrough()}
                | prompt | model | StrOutputParser())
print("💬", hybrid_chain.invoke("What does ERR-5003 mean?", config=CONFIG))


# ---------------------------------------------------------------------------
# 5. Agentic RAG in a few lines
# ---------------------------------------------------------------------------
trace.step("5. Agentic RAG: the retriever as a tool")

help_center = create_retriever_tool(
    hybrid,
    name="search_help_center",
    description="Search Nimbus's help centre. Use short, specific queries, one topic per search.",
    # How each Document is turned into text for the model. {id}, {updated} come from metadata.
    # Without this, the model would only see page contents, with no ids to cite.
    document_prompt=PromptTemplate.from_template("[{id}] (updated {updated})\n{page_content}"),
)
agent = create_agent(model, tools=[help_center],
                     system_prompt="You are Nimbus support. Always search before answering. Cite [ids]. Be concise.")
result = agent.invoke({"messages": [{"role": "user", "content":
                                     "Is Nimbus OK for recording therapy sessions, and where is data stored?"}]},
                      config=CONFIG)
print("\n✅", result["messages"][-1].text)
# Compare with Phase 2 lesson 06: ~90 lines of loop and schemas → ~10 lines here.

trace.show_totals("Lesson 04 totals")

# 🧪 TRY:
#   1. Swap Chroma for InMemoryVectorStore (from langchain_core.vectorstores import
#      InMemoryVectorStore). Only the constructor line changes.
#   2. Use vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 4, "fetch_k": 12}).
#      MMR (maximal marginal relevance) avoids returning 4 near-identical chunks.
#   3. Add a metadata filter: as_retriever(search_kwargs={"k": 4, "filter": {"source": "pricing.md"}}).
#   4. Remove document_prompt from create_retriever_tool. Can the agent still cite sources?
