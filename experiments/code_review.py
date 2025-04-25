"""
Iterated author / reviewer loop that keeps patching until tests pass.

Usage:
    python -m experiments.code_review
"""

import asyncio, subprocess, sys, tempfile, textwrap, random, re, os
from experiments import run_pair

SPECS = [
    ("is_prime",
     "Write a Python function `is_prime(n)` that returns True if n is prime.",
     textwrap.dedent("""
        assert is_prime(2) and is_prime(13) and not is_prime(15)
     """)),
    ("fibonacci",
     "Write a Python function `fibonacci(n)` that returns the first n Fibonacci numbers.",
     textwrap.dedent("""
        assert fibonacci(6)==[0,1,1,2,3,5]
     """)),
]

def run_py(code: str, test_block: str) -> bool:
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py") as f:
        f.write(code + "\n" + test_block + "\nprint('PASS')")
        path = f.name
    try:
        proc = subprocess.run([sys.executable, path],
                              capture_output=True, text=True, timeout=5)
        return proc.returncode == 0 and "PASS" in proc.stdout
    finally:
        os.remove(path)

async def main():
    func_name, spec_text, test_block = random.choice(SPECS)

    author_cfg = dict(
        name="Author",
        system_msg="You write concise, efficient Python that passes the spec.",
        temperature=0.3,
    )
    reviewer_cfg = dict(
        name="Reviewer",
        system_msg=(
            "You are a strict code reviewer. "
            "If code fails tests, reply with a patch in ```python ``` block; "
            "otherwise reply APPROVED."
        ),
        temperature=0.3,
    )

    sched = await run_pair(author_cfg, reviewer_cfg,
        seed_message=f"New task:\n{spec_text}\nPlease collaborate until tests pass.",
        max_ticks=60)

    # Scan messages from Author for code blocks, run tests
    for msg in sched.ctx.recent_messages:
        if msg["name"] == "Author":
            if "```python" in msg["content"]:
                code = re.search(r"```python(.*?)```", msg["content"], re.S)
                if code:
                    ok = run_py(code.group(1), test_block)
                    if ok:
                        print("✅ Tests passed.")
                        break
    else:
        print("❌ Tests never passed within 60 ticks.")

if __name__ == "__main__":
    asyncio.run(main()) 