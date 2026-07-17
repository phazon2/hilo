"""Offline test - no API key, no network. Proves the memory engine end to end.

Simulates the exact demo flow: session 1 (brief) -> quit-distill -> restart ->
resume greeting -> session 2 resolves a thread (timely forgetting) -> hard cap
-> corrupt-file recovery -> distill-failure safety.

Run: python test_offline.py     (exit 0 + GREEN = all good)
"""

import json
import os
import sys
import tempfile
import types

# Route memory to a temp file BEFORE importing the modules under test.
_tmpdir = tempfile.mkdtemp(prefix="hilo-test-")
os.environ["HILO_MEMORY_FILE"] = os.path.join(_tmpdir, "memory.json")

import memory as M  # noqa: E402
from agent import greeting  # noqa: E402

PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


class FakeClient:
    """Stands in for the OpenAI client: returns a canned distillation payload."""

    def __init__(self, payload=None, raise_exc=False):
        def create(**kwargs):
            if raise_exc:
                raise RuntimeError("simulated network failure")
            msg = types.SimpleNamespace(content="```json\n" + json.dumps(payload) + "\n```")
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])

        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(create=create)
        )


def main() -> None:
    path = os.environ["HILO_MEMORY_FILE"]

    print("1) fresh start")
    mem = M.load_memory(path)
    check("empty memory on first run", mem == M.EMPTY_MEMORY)
    check("first-session greeting", "Brief me" in greeting(mem))

    print("2) session 1: brief -> distill -> save -> reload")
    session1 = FakeClient(payload={
        "facts": [
            "Building Hilo: memory agent for the Qwen Cloud hackathon, Track 1 MemoryAgent",
            "Stack: Python + Qwen via DashScope international endpoint",
            "Deadline: submit Sunday evening (Chile time)",
        ],
        "preferences": ["User wants concise, concrete answers"],
        "open_threads": [
            "Which Qwen model gives the fastest demo latency?",
            "Record the demo video Saturday",
        ],
    })
    transcript = [("user", "We're building Hilo..."), ("assistant", "Got it.")]
    mem = M.prune(M.distill(session1, "fake-model", mem, transcript))
    mem["session_count"] += 1
    M.save_memory(mem, path)
    reloaded = M.load_memory(path)
    check("round-trip identical", reloaded == mem)
    check("3 facts stored", len(reloaded["facts"]) == 3)
    check("2 open threads stored", len(reloaded["open_threads"]) == 2)

    print("3) restart: the money shot")
    g = greeting(reloaded)
    check("greeting announces session 2", "session 2" in g)
    check("greeting resumes open thread", "fastest demo latency" in g)

    print("4) session 2: thread resolved -> timely forgetting")
    session2 = FakeClient(payload={
        "facts": reloaded["facts"] + ["Chosen model: qwen-turbo (fastest in smoke test)"],
        "preferences": reloaded["preferences"],
        "open_threads": ["Record the demo video Saturday"],  # latency question resolved -> dropped
    })
    mem2 = M.prune(M.distill(session2, "fake-model", reloaded, [("user", "qwen-turbo won"), ("assistant", "Locked.")]))
    mem2["session_count"] += 1
    check("resolved thread forgotten", all("latency" not in t for t in mem2["open_threads"]))
    check("new fact merged", any("qwen-turbo" in f for f in mem2["facts"]))

    print("5) hard cap (40 items)")
    flood = FakeClient(payload={
        "facts": [f"fact number {i}" for i in range(60)],
        "preferences": ["pref"],
        "open_threads": ["thread"],
    })
    capped = M.distill(flood, "fake-model", mem2, [("user", "x")])
    total = len(capped["facts"]) + len(capped["preferences"]) + len(capped["open_threads"])
    check("total items <= 40", total <= M.MAX_ITEMS, f"got {total}")

    print("6) corrupt file recovery")
    with open(path, "w", encoding="utf-8") as f:
        f.write("{ this is not json !!!")
    recovered = M.load_memory(path)
    check("corrupt file -> fresh memory, no crash", recovered == M.EMPTY_MEMORY)
    check("corrupt file quarantined", os.path.exists(path + ".corrupt"))

    print("7) distill failure safety")
    broken = FakeClient(raise_exc=True)
    unchanged = M.distill(broken, "fake-model", mem2, [("user", "hello")])
    check("failed distill keeps memory intact",
          unchanged["facts"] == mem2["facts"] and unchanged["open_threads"] == mem2["open_threads"])

    print()
    if FAIL == 0:
        print(f"GREEN: all {PASS} offline checks passed. The memory engine round-trips.")
        sys.exit(0)
    print(f"RED: {FAIL} of {PASS + FAIL} checks failed.")
    sys.exit(1)


if __name__ == "__main__":
    main()
