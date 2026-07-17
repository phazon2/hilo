"""Hilo memory engine — distill sessions into durable, structured memory.

Track mapping (Qwen Cloud hackathon, Track 1: MemoryAgent):
  * distill()            -> efficient memory storage and retrieval
                            (one call compresses a whole session into <=40 items)
  * prune() + distill    -> timely forgetting of outdated information
                            (resolved threads dropped, stale facts rewritten,
                             hard cap prunes oldest-first)
  * format_for_prompt()  -> recalling critical memories within limited
                            context windows (compact block, never raw transcripts)
"""

from __future__ import annotations

import json
import os
import tempfile

MEMORY_FILE = os.environ.get("HILO_MEMORY_FILE", "memory.json")
MAX_ITEMS = 40  # hard cap: facts + preferences + open_threads combined

EMPTY_MEMORY = {
    "facts": [],
    "preferences": [],
    "open_threads": [],
    "session_count": 0,
}

DISTILL_PROMPT = """You maintain long-term memory for Hilo, a project collaborator agent.
Merge the PREVIOUS MEMORY with what happened in the SESSION TRANSCRIPT.

Return ONLY a JSON object with exactly these keys:
  "facts": stable project truths (goal, stack, names, decisions made). One line each.
  "preferences": how the user likes to work or communicate.
  "open_threads": unresolved questions or next steps. DROP any thread the transcript resolved.

Rules:
- Merge and deduplicate. Rewrite outdated facts instead of keeping both versions.
- Timely forgetting: drop anything the transcript made obsolete or resolved.
- Keep at most {max_items} items total across the three lists; prefer recent and important.
- Each item under 140 characters. No commentary outside the JSON object.
"""


def load_memory(path: str = MEMORY_FILE) -> dict:
    """Load memory from disk. Never crashes: a corrupt file is quarantined
    (renamed to *.corrupt) instead of destroyed, and a fresh memory is returned."""
    if not os.path.exists(path):
        return dict(EMPTY_MEMORY)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("memory root is not a JSON object")
        mem = dict(EMPTY_MEMORY)
        for key in ("facts", "preferences", "open_threads"):
            value = data.get(key, [])
            mem[key] = [str(x).strip() for x in value if str(x).strip()] if isinstance(value, list) else []
        mem["session_count"] = int(data.get("session_count", 0) or 0)
        return mem
    except Exception:
        try:
            os.replace(path, path + ".corrupt")
        except OSError:
            pass
        return dict(EMPTY_MEMORY)


def save_memory(mem: dict, path: str = MEMORY_FILE) -> None:
    """Atomic write: temp file + os.replace. A crash mid-save can never
    leave a half-written memory file."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".memory-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(mem, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def prune(mem: dict, max_items: int = MAX_ITEMS) -> dict:
    """Timely forgetting, mechanical part: enforce the hard item cap.

    Distillation already drops resolved threads; this is the backstop.
    Drop order when over cap: oldest facts, then oldest open threads, then
    oldest preferences (preferences last — cheapest to store, costliest to re-learn).
    """
    mem = {**mem, "facts": list(mem["facts"]), "preferences": list(mem["preferences"]),
           "open_threads": list(mem["open_threads"])}

    def total() -> int:
        return len(mem["facts"]) + len(mem["preferences"]) + len(mem["open_threads"])

    for key in ("facts", "open_threads", "preferences"):
        while total() > max_items and mem[key]:
            mem[key].pop(0)  # oldest first
    return mem


def format_for_prompt(mem: dict) -> str:
    """Compact memory block injected at session start.
    This — not a transcript dump — is what makes recall fit a limited context window."""
    if mem["session_count"] == 0 and not (mem["facts"] or mem["open_threads"]):
        return "No prior memory. This is the first session."
    lines = [f"Sessions so far: {mem['session_count']}"]
    if mem["facts"]:
        lines.append("Project facts:")
        lines.extend(f"  - {x}" for x in mem["facts"])
    if mem["preferences"]:
        lines.append("User preferences:")
        lines.extend(f"  - {x}" for x in mem["preferences"])
    if mem["open_threads"]:
        lines.append("Open threads (unresolved):")
        lines.extend(f"  - {x}" for x in mem["open_threads"])
    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    """Parse model output into JSON, tolerating code fences and stray prose."""
    text = (text or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in model output")
    return json.loads(text[start : end + 1])


def distill(client, model: str, mem: dict, transcript: list) -> dict:
    """One extra model call turns a finished session into durable memory.

    Failure-safe by design: if the call or the parse fails, the previous
    memory is returned untouched. Memory can degrade to 'unchanged',
    never to 'corrupted'. Does not modify session_count — the caller owns that.
    """
    if not transcript:
        return dict(mem)
    convo = "\n".join(f"{role.upper()}: {content}" for role, content in transcript)
    prev = json.dumps(
        {k: mem[k] for k in ("facts", "preferences", "open_threads")},
        ensure_ascii=False,
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": DISTILL_PROMPT.format(max_items=MAX_ITEMS)},
                {"role": "user", "content": f"PREVIOUS MEMORY:\n{prev}\n\nSESSION TRANSCRIPT:\n{convo}"},
            ],
        )
        data = _extract_json(resp.choices[0].message.content)
        new_mem = dict(mem)
        for key in ("facts", "preferences", "open_threads"):
            value = data.get(key, [])
            if isinstance(value, list):
                new_mem[key] = [str(x).strip() for x in value if str(x).strip()][:MAX_ITEMS]
        return prune(new_mem)
    except Exception as exc:  # any failure means "keep old memory", never corrupt it
        print(f"[hilo] distillation failed ({type(exc).__name__}); keeping previous memory intact.")
        return dict(mem)
