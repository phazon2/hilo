"""Hilo — the agent you never re-explain your project to.

Session loop: memory in -> conversation -> memory out.

This file is the Alibaba Cloud deployment proof for the Qwen Cloud hackathon:
every model call goes to Qwen on Alibaba Cloud Model Studio via the DashScope
international OpenAI-compatible endpoint (see QWEN_BASE_URL).
"""

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from memory import (
    MEMORY_FILE,
    distill,
    format_for_prompt,
    load_memory,
    prune,
    save_memory,
)

DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
RECENT_TURNS = 20  # limited context window: compact memory + recent turns only

SYSTEM_PROMPT = """You are Hilo, the user's standing project collaborator.
You keep continuity across sessions: the MEMORY block below is everything you
learned in previous sessions. Treat it as true unless the user corrects it.
Resume mid-project. Never ask the user to re-explain what memory already covers.
Be concise and concrete. When the user states a fact or makes a decision,
acknowledge it crisply and move forward.

MEMORY:
{memory}"""


def make_client():
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key or "your-key" in api_key:
        print("RED: DASHSCOPE_API_KEY missing. Copy .env.example to .env and paste your key.")
        sys.exit(1)
    base_url = os.environ.get("QWEN_BASE_URL", DEFAULT_BASE_URL)
    return OpenAI(api_key=api_key, base_url=base_url, timeout=60), base_url


def greeting(mem: dict) -> str:
    """Deterministic resume greeting — instant, zero API latency, demo-reliable."""
    if mem["session_count"] == 0:
        return "New project, blank memory. Brief me: what are we building?"
    nf, nt = len(mem["facts"]), len(mem["open_threads"])
    lines = [
        f"Welcome back - session {mem['session_count'] + 1}. "
        f"I'm holding {nf} fact{'s' if nf != 1 else ''} and {nt} open thread{'s' if nt != 1 else ''}."
    ]
    if mem["open_threads"]:
        lines.append("Where we left off:")
        lines.extend(f"  - {t}" for t in mem["open_threads"][:3])
    lines.append("Keep going, or /facts to see everything I remember.")
    return "\n".join(lines)


def show_facts(mem: dict) -> None:
    print("\n--- Hilo memory " + "-" * 24)
    print(format_for_prompt(mem))
    print("-" * 40 + "\n")


def main() -> None:
    load_dotenv()
    client, base_url = make_client()
    model = os.environ.get("QWEN_MODEL", "qwen-turbo")
    mem = load_memory()

    host = base_url.split("//")[-1].split("/")[0]
    print(f"Hilo | model: {model} | Qwen on Alibaba Cloud Model Studio ({host})")
    print(f"memory: {MEMORY_FILE} | commands: /facts /save /quit (Ctrl+C is safe too)\n")
    print(greeting(mem) + "\n")

    transcript: list = []
    try:
        while True:
            try:
                user = input("you> ").strip()
            except EOFError:
                break
            if not user:
                continue
            if user == "/quit":
                break
            if user == "/facts":
                show_facts(mem)
                continue
            if user == "/save":
                print("[hilo] checkpointing memory...")
                mem = distill(client, model, mem, transcript)
                save_memory(mem)
                print("[hilo] memory checkpointed.\n")
                continue

            transcript.append(("user", user))
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT.format(memory=format_for_prompt(mem))}
            ]
            for role, content in transcript[-RECENT_TURNS:]:
                messages.append(
                    {"role": "user" if role == "user" else "assistant", "content": content}
                )
            try:
                resp = client.chat.completions.create(model=model, messages=messages)
                answer = (resp.choices[0].message.content or "").strip()
            except Exception as exc:
                answer = (
                    f"[model call failed: {type(exc).__name__}] Your words are in the "
                    f"transcript and memory is safe. Details: {str(exc)[:200]}"
                )
            print(f"\nhilo> {answer}\n")
            transcript.append(("assistant", answer))
    except KeyboardInterrupt:
        print("\n[hilo] interrupted - saving memory before exit.")

    # Crash-safe close: distill whatever happened, atomically persist it.
    if transcript:
        print("[hilo] distilling session into memory...")
        mem = prune(distill(client, model, mem, transcript))
        mem["session_count"] = mem.get("session_count", 0) + 1
        save_memory(mem)
        nf, nt = len(mem["facts"]), len(mem["open_threads"])
        print(
            f"[hilo] memory saved to {MEMORY_FILE} - {nf} fact{'s' if nf != 1 else ''}, "
            f"{nt} open thread{'s' if nt != 1 else ''}. See you next session."
        )
    else:
        print("[hilo] nothing new this session; memory unchanged.")


if __name__ == "__main__":
    main()
