"""
Phase 0: check that your environment is ready.

Run:  uv run python 00-setup/check_setup.py
"""

# 🐍 PYTHON NOTE: imports.
# `import x` loads a module (a .py file or installed package) so you can use x.something.
# `from x import y` pulls one name out of the module so you can write y directly.
import os
import sys

from dotenv import load_dotenv


def ok(msg: str) -> None:
    # 🐍 PYTHON NOTE: type hints. `msg: str` and `-> None` document what goes in
    # and what comes out. Python doesn't enforce them at runtime, but editors and
    # tools (and libraries like Pydantic, lesson 04) use them heavily.
    print(f"  ✅ {msg}")


def fail(msg: str) -> None:
    # 🐍 PYTHON NOTE: f-strings. f"..." lets you embed variables in {braces}.
    print(f"  ❌ {msg}")


def main() -> None:
    print("Checking your setup...\n")
    all_good = True

    # 1. Python version
    if sys.version_info >= (3, 12):
        ok(f"Python {sys.version.split()[0]}")
    else:
        fail("Python 3.12+ required. Run with `uv run`, which picks the right version.")
        all_good = False

    # 2. Packages installed?
    try:
        import anthropic  # noqa: F401  (imported only to test it exists)

        ok(f"anthropic SDK {anthropic.__version__}")
    except ImportError:
        # 🐍 PYTHON NOTE: try/except. Code in `try` runs; if it raises the named
        # error, the `except` block runs instead of crashing the program.
        fail("anthropic not installed. Run `uv sync`")
        all_good = False

    # 3. .env loaded and key present?
    load_dotenv(override=True)
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if key.startswith("sk-ant-") and key != "sk-ant-...":
        # ⚠️ GOTCHA: never print a full API key, not even in your own terminal. Logs leak.
        ok(f"ANTHROPIC_API_KEY found ({key[:10]}...)")
    else:
        fail("ANTHROPIC_API_KEY missing. Put your real key in .env")
        all_good = False

    model = os.getenv("MODEL", "claude-opus-5-5")
    ok(f"MODEL = {model}")

    # 4. A real (tiny) API call
    if all_good:
        import anthropic

        try:
            client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
            response = client.messages.create(
                model=model,
                max_tokens=1000,
                messages=[{"role": "user", "content": "Reply with exactly: setup works"}],
            )
            text = next(b.text for b in response.content if b.type == "text")
            ok(f"API call works. Model said: {text!r}")
        except anthropic.AuthenticationError:
            fail("API key rejected. Check it in .env")
            all_good = False
        except anthropic.APIError as e:
            fail(f"API error: {e}")
            all_good = False

    print("\n🎉 All set! Start with 01-llm-basics/README.md" if all_good else "\nFix the ❌ items above and re-run.")


# 🐍 PYTHON NOTE: this "main guard" means: run main() only when this file is executed
# directly (`python check_setup.py`), not when another file imports it.
if __name__ == "__main__":
    main()
