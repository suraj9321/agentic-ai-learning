"""
Lesson 07: Async and parallel LLM calls.

What you'll learn:
  - Why sequential LLM calls are slow (each takes seconds, mostly waiting on the network)
  - async/await: run many calls at the same time
  - Limiting concurrency so you don't hit rate limits

Where this shows up later:
  - Parallel tool execution in agents
  - The "parallelization" / map-reduce pattern in LangGraph (Phase 4)
  - Running evals over a dataset of 100s of examples (Phase 5)
  - FastAPI servers, which are async (Phase 7)

Run:  uv run python 01-llm-basics/07_async_parallel.py
"""

# 🐍 PYTHON NOTE: async in 60 seconds.
#   - A normal function runs start to finish. While waiting for the network, Python does nothing.
#   - An `async def` function is a *coroutine*. When it hits `await something_slow()`, it
#     PAUSES and lets other coroutines run while it waits.
#   - `asyncio.run(main())` starts the "event loop" that juggles all the paused coroutines.
#   - `asyncio.gather(a(), b(), c())` runs a, b and c concurrently and waits for all of them.
#   Rule: you can only use `await` inside an `async def` function.

import asyncio
import os
import time

import anthropic
from dotenv import load_dotenv

# For async we use trace.event(): one timestamped line per start/finish, so you can SEE
# whether calls overlap. (Full request panels from 5 calls at once would be unreadable.)
from course_utils import trace

load_dotenv(override=True)
MODEL = os.getenv("MODEL", "claude-opus-5-5")

# The async version of the client. Same methods, but you `await` them.
async_client = anthropic.AsyncAnthropic()

REVIEWS = [
    "Setup took 5 minutes and the AI drafts are scarily good. Love it.",
    "Crashes every time I upload a PDF over 10MB. Support hasn't replied in 4 days.",
    "Decent, but pricey for a small team. The Slack integration is the best part.",
    "Billing charged me twice. Refund came through quickly though, so I'm okay.",
    "It's fine. Does what it says. Nothing special.",
]


async def classify(review: str) -> str:
    rid = REVIEWS.index(review) + 1
    trace.event(f"▶ start  review {rid}: {review[:40]}...")
    response = await async_client.messages.create(  # ← `await`: pause here while waiting for the network
        model=MODEL,
        max_tokens=16000,
        messages=[{
            "role": "user",
            "content": f"Sentiment of this review: positive, negative or mixed? Reply with one word.\n\n<review>{review}</review>",
        }],
    )
    label = "".join(b.text for b in response.content if b.type == "text").strip().lower()
    trace.event(f"■ finish review {rid} → {label}  ({response.usage.input_tokens}→{response.usage.output_tokens} tokens)")
    return label


async def sequential() -> list[str]:
    results = []
    for r in REVIEWS:
        results.append(await classify(r))  # waits for each one before starting the next
    return results


async def parallel() -> list[str]:
    # 🐍 PYTHON NOTE: the * "unpacks" the list into separate arguments:
    # gather(*[a, b, c]) == gather(a, b, c). Results come back in the SAME order as the inputs.
    return await asyncio.gather(*[classify(r) for r in REVIEWS])


# A semaphore limits how many calls run at once. With 500 items you don't want 500
# simultaneous requests: you'd hit rate limits (HTTP 429).
semaphore = asyncio.Semaphore(3)


async def classify_limited(review: str) -> str:
    # `async with` = context manager for async code. At most 3 coroutines can be inside at once.
    async with semaphore:
        return await classify(review)


async def main() -> None:
    print(f"Classifying {len(REVIEWS)} reviews...\n")

    print("--- Sequential: each call starts only after the previous one finishes ---")
    trace.reset_clock()
    t0 = time.perf_counter()  # 🐍 a precise timer for measuring durations
    seq = await sequential()
    t_seq = time.perf_counter() - t0
    print(f"Sequential: {t_seq:5.1f}s  {seq}")

    print("\n--- Parallel: all start together; they finish in whatever order the network returns ---")
    trace.reset_clock()
    t0 = time.perf_counter()
    par = await parallel()
    t_par = time.perf_counter() - t0
    print(f"Parallel:   {t_par:5.1f}s  {par}")

    print("\n--- Limited to 3 at a time: review 4 starts only when one of the first 3 finishes ---")
    trace.reset_clock()
    t0 = time.perf_counter()
    lim = await asyncio.gather(*[classify_limited(r) for r in REVIEWS])
    t_lim = time.perf_counter() - t0
    print(f"Limited(3): {t_lim:5.1f}s  {lim}")

    print(f"\n→ Parallel was {t_seq / t_par:.1f}x faster for the SAME cost (same tokens).")
    # 💡 WHY: latency is a product feature. If your agent needs 5 independent lookups, do
    # them in parallel. Claude itself often requests several tools at once for this reason.
    # ⚠️ GOTCHA: only parallelise INDEPENDENT work. If step B needs step A's output, it must wait.


if __name__ == "__main__":
    asyncio.run(main())

# 🧪 TRY:
#   1. Add 15 more reviews (ask an LLM to generate them!) and compare timings again.
#   2. Change the Semaphore to 1. It should take about as long as sequential. Why?
#   3. Make one call fail (e.g. set model="nope" for one review). What does gather do?
#      Then look up `asyncio.gather(..., return_exceptions=True)`.
