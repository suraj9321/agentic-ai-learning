"""
Lesson 02: Loading documents and chunking them.

What you'll learn:
  - Why we split documents into chunks before embedding them
  - Fixed-size chunking with overlap, built by hand
  - "Recursive" chunking that respects headings and paragraphs (what LangChain does)
  - Keeping metadata (source file, heading, date) attached to every chunk

No API key needed.

Run:  uv run python 02-rag/02_chunking.py
"""

from pathlib import Path

from dotenv import load_dotenv

from course_utils import trace
from course_utils.rag import chunk_documents, load_documents

load_dotenv(override=True)

# 🐍 PYTHON NOTE: Path(__file__) is the path of THIS script. .parent is its folder.
# Building paths from it means the lesson works no matter which folder you run it from.
# The `/` operator on Path objects joins path parts: Path("a") / "b" → a/b.
DATA = Path(__file__).parent / "data" / "nimbus"


# ---------------------------------------------------------------------------
# 1. Load the documents
# ---------------------------------------------------------------------------
trace.step("1. Load documents")

# Our knowledge base: the help centre of "Nimbus", a made-up AI meeting-notes startup.
# Open 02-rag/data/nimbus/ and skim the files. You'll query them all week.
docs = load_documents(DATA)
for d in docs:
    print(f"  {d['source']:<24} {len(d['text']):>5} chars   updated={d.get('updated')}   title={d.get('title')}")
# The block between the two `---` lines at the top of each file is "front matter":
# metadata about the document. We keep it, because metadata becomes search filters later.

# 💡 WHY chunk at all? Three reasons:
#   1. Precision: one vector for a whole 10-page document is a blurry average of everything
#      in it. A vector per paragraph matches specific questions much better.
#   2. Cost: you only paste the relevant chunks into the prompt, not whole documents.
#   3. Limits: embedding models have a max input length (bge-small: 512 tokens ≈ 2,000 chars).
#      Text past that limit is silently cut off and never searchable.


# ---------------------------------------------------------------------------
# 2. Fixed-size chunking, by hand
# ---------------------------------------------------------------------------
trace.step("2. Fixed-size chunks (the naive way)")


def fixed_chunks(text: str, size: int = 300, overlap: int = 50) -> list[str]:
    """Cut every `size` characters. Each chunk repeats the last `overlap` chars of the previous one."""
    step = size - overlap
    # 🐍 PYTHON NOTE: range(start, stop, step) → 0, 250, 500, ...
    # text[a:b] is "slicing": characters from index a up to (not including) b.
    return [text[i:i + size] for i in range(0, len(text), step)]


pricing = next(d for d in docs if d["source"] == "pricing.md")
# 🐍 PYTHON NOTE: next(generator) returns the first item the generator produces:
# here, the first document whose source is pricing.md.

naive = [{"id": f"pricing.md#{i}", "text": t} for i, t in enumerate(fixed_chunks(pricing["text"]))]
trace.show_chunks(naive, label="fixed 300 chars, 50 overlap", limit=4)
# ⚠️ GOTCHA: look at where chunks start and end: mid-word, mid-sentence, a heading at the
# END of one chunk and its content in the next. A chunk like "...Extra seats cost" + "$8 per
# seat..." split across two chunks means neither chunk answers "how much is an extra seat?".


# ---------------------------------------------------------------------------
# 3. Overlap: why it exists
# ---------------------------------------------------------------------------
trace.step("3. What overlap buys you")

import re  # 🐍 `re` = regular expressions, a mini-language for finding patterns in text

# Split the text into sentences, then check: is each sentence COMPLETE inside some chunk?
sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n+", pricing["text"]) if len(x.strip()) > 20]
# (The pattern means: split after . ! or ? followed by whitespace, OR on newlines.)


def broken(chunks: list[str]) -> list[str]:
    """Sentences that don't appear whole in any chunk."""
    return [sent for sent in sentences if not any(sent in ch for ch in chunks)]


for ov in (0, 50, 100):
    lost = broken(fixed_chunks(pricing["text"], size=300, overlap=ov))
    print(f"overlap={ov:>3}: {len(lost)} of {len(sentences)} sentences are cut in half")
    if ov == 0 and lost:
        print(f"           e.g. {lost[0]!r}")
# 🐍 PYTHON NOTE: {ov:>3} right-aligns the number in 3 spaces; {x!r} shows quotes and \n.
# More overlap → fewer facts split across two chunks. A split fact is half-findable at best.
# Overlap costs extra storage and tokens (text is duplicated), so 10–20% of chunk size is typical.


# ---------------------------------------------------------------------------
# 4. Recursive chunking: split on structure first
# ---------------------------------------------------------------------------
trace.step("4. Recursive chunks (respecting headings and paragraphs)")

# The idea (used by LangChain's RecursiveCharacterTextSplitter, which you'll meet in Phase 3):
#   try to split on "\n## " (section headings). Any piece still too big? split it on "\n\n"
#   (paragraphs). Still too big? "\n" (lines), then ". " (sentences), then " " (words).
# Note: max_chars is the limit BEFORE the overlap is prepended, so chunks can be a bit longer.
# Pieces under 80 chars (like a lone "# Title" line) are merged into the next piece.
# Open course_utils/rag.py and read _split() and chunk_text(). It's ~40 lines, and you should
# be able to explain it in an interview.
chunks = chunk_documents([pricing], max_chars=600, overlap=100)
trace.show_chunks(chunks, label="recursive, max 600 chars, 100 overlap", limit=4)

print("\nEach chunk carries metadata, which is what makes citations and filters possible:")
c = chunks[1]
print({k: v for k, v in c.items() if k != "text"})
# 💡 WHY "heading"? A chunk that says "Extra seats cost $8" is clearer when you know it's
# under "## Plans". Some systems prepend the heading (or a 1-sentence document summary
# written by an LLM) to the chunk before embedding: "contextual retrieval".


# ---------------------------------------------------------------------------
# 5. The whole knowledge base
# ---------------------------------------------------------------------------
trace.step("5. Chunk everything")
all_chunks = chunk_documents(docs)
trace.show_chunks(all_chunks, label="all Nimbus docs", limit=8)

# 💡 WHY there's no "right" chunk size: small chunks (200–400 chars) match precise questions
# but lose context; big chunks (1,500+) keep context but dilute the vector and cost more
# tokens. Start around 500–1,000 characters, then MEASURE with an eval (lesson 05 shows how).

# 🧪 TRY:
#   1. Change max_chars to 200 and 1500 in section 5. How many chunks do you get each time?
#      Re-run lesson 05's eval with each size later and compare hit rates.
#   2. Drop any PDF into 02-rag/data/nimbus/ and re-run. Each page becomes a document with
#      a "page" field. Look at the extracted text quality: PDFs are messy!
#   3. Write a `chunk_by_heading(text)` that makes one chunk per "## " section, no size limit.
#      When would that be better than recursive chunking?
