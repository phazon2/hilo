# Hilo — Plan of Record

Pitch (identical everywhere, verbatim): **The agent you never re-explain your project to.**

## §0 Rules digest (verified live Fri Jul 17, from cloud)

- **Deadline: extended to July 20, 2026** — confirmed on the official announcement page
  (qwencloud.com/challenge/hackathon: "Submission Deadline Extended to July 20").
  Devpost rules legalese still shows the stale Jul 9 date — ignore it.
  No explicit cutoff time published for Jul 20 → treat as 2:00 PM PDT (5:00 PM Chile, Monday).
  **Our submit day: Sunday July 19, before dinner. Never deadline day.**
- **Track 1: MemoryAgent** — persistent memory, autonomously accumulates experience,
  cross-session. Judges' stated focus (use these exact phrases):
  *efficient memory storage and retrieval* · *timely forgetting of outdated information* ·
  *recalling critical memories within limited context windows*.
- **Judging**: Stage 1 pass/fail (reasonably fits track + reasonably applies the required
  APIs/SDKs). Stage 2: Innovation 30 · Technical depth 30 · Problem value 25 · Presentation 15.
- **Submission must include**: public repo with detectable open-source LICENSE (MIT ✓) ·
  text description · **proof of Alibaba Cloud deployment** (link the GitHub URL of `agent.py`;
  the terminal banner shows the dashscope-intl host on screen in the video) ·
  architecture diagram ✓ · video **under 3:00**, publicly visible on YouTube/Vimeo/Youku,
  no copyrighted music, English or subtitled · track selection ·
  optional blog-post URL (bonus: 10 × $500 cash + $500 credits).
- **Prizes**: track grand = $7,000 cash + $3,000 credits; 10 honorable mentions.
- Drafts are explicitly allowed before the deadline — create one tonight (Friday).

## §1 Locked decisions

- Name: **Hilo**. Pitch: the sentence at the top of this file. Never paraphrase it in artifacts.
- Track 1 MemoryAgent. Solo entry. MIT license.
- One core loop (`agent.py`), one memory engine (`memory.py`), nothing else. Compression beats sophistication.
- Model: `qwen-turbo` default; `test_connection.py` auto-discovers a working fallback if retired.
- **Feature freeze after Friday.** Saturday/Sunday are assets and the button, not code.
- A feature not in the demo video does not exist.

## §2 State

Done: registration ×2 (Devpost + lablab), Alibaba account + Model Studio (Singapore),
GitHub repo `hilo` created (empty), kit rebuilt + offline-tested in Claude's cloud
workspace, rules re-verified live, architecture diagram, deck (slots open),
Devpost description (§6), video script (§4), CI workflow for live smoke testing.

Done Fri night (live-verified via CI on the real endpoint): API key ✓ smoke GREEN
(qwen-turbo, 1.1s) ✓ first live session + restart-resume ✓ pushed to GitHub ✓.
Not done, in order: Devpost DRAFT (tonight) → (optional) free-quota check + $5 budget
alert → record video Sat → deck slots Sat → SUBMIT Sunday.

## §3 Day-by-day

- **Fri night**: API key (Singapore console → API-KEY → Create). Then EITHER
  laptop path (runbook in README quickstart) OR cloud path: add the key as GitHub
  Actions secret `DASHSCOPE_API_KEY` and let Claude push + trigger CI, which runs the
  live smoke test and a scripted brief→resume demo. Then Devpost draft (proves the window).
- **Sat**: record video per §4 (two takes max — done beats cinematic), upload public,
  screenshot into deck slide 3, fill [MODEL]/[USER] slots, optional 20-min blog post (§ bonus).
- **Sun**: fill description slots, run §7 checklist, SUBMIT before dinner,
  screenshot confirmation, send to Claude. Extraction session after.

## §4 Video script (target 2:10, hard max 2:59 — captions burned in, no music)

Terminal: dark theme, 18pt+ font, full screen. OBS or Loom. Speed up typing in edit.

| # | Time | On screen | Caption |
|---|---|---|---|
| 1 | 0:00–0:06 | Title card | **Hilo — the agent you never re-explain your project to.** |
| 2 | 0:06–0:18 | Empty terminal | Every AI session starts with amnesia. You pay a re-explanation tax, every time. |
| 3 | 0:18–0:55 | `python agent.py` → type the 5 brief lines (below) → `/quit` | Brief it once. On quit, **one extra Qwen call** distills the session into structured memory. |
| 4 | 0:55–1:10 | `cat memory.json` (Win: `type memory.json`) | facts · preferences · open threads. 40-item cap. Resolved threads get forgotten. |
| 5 | 1:10–1:35 | `python agent.py` again → resume greeting appears instantly. Hold 3s. | **New session. Zero re-explanation.** *(the money shot)* |
| 6 | 1:35–1:55 | Start a message, hit Ctrl+C mid-session → rerun → still remembers | Even a crash can't make it forget. Atomic saves, failure-safe distillation. |
| 7 | 1:55–2:10 | Track card | Efficient storage & retrieval ✓ Timely forgetting ✓ Critical recall in limited context ✓ — on Qwen, Alibaba Cloud Model Studio. |
| 8 | 2:10–2:20 | Close card + terminal banner visible (dashscope-intl host = deployment proof) | Pitch repeated + github.com/phazon2/hilo |

Brief lines to type in frame 3 (exactly these — they seed the §5/§6 story):
1. `We're building Hilo: a memory agent for the Qwen Cloud hackathon, Track 1 MemoryAgent.`
2. `Stack: Python plus Qwen on Alibaba Cloud Model Studio via the DashScope international endpoint.`
3. `The demo deadline is Sunday evening, Chile time.`
4. `Decision: MIT license, single-file agent plus a memory engine, nothing else.`
5. `Open question: which Qwen model gives the fastest demo latency?`

## §5 Deck outline (6 slides — file: hilo-deck.pptx)

1. Title + pitch (verbatim).
2. Problem: the re-explanation tax (every session starts from zero).
3. Demo screenshot **[SLOT: resume-greeting screenshot from video frame 5]**.
4. Architecture (assets/architecture.png).
5. Track fit: three judges' phrases → three design decisions. qwen-turbo (locked — live-verified Fri, 1.1s response).
6. Links + what's next. **[SLOT: USER — github.com/phazon2/hilo]**.

## §6 Devpost description (paste as-is; model locked: qwen-turbo)

**Tagline:** The agent you never re-explain your project to.

**Inspiration.** Every AI chat starts with amnesia. If you use an assistant across a
multi-day project, you pay a re-explanation tax at the start of every single session —
pasting context, restating decisions, re-asking questions you already answered.

**What it does.** Brief Hilo once. When you leave (`/quit` — or even Ctrl+C), one extra
Qwen call distills the entire session into structured memory: `facts`, `preferences`,
`open_threads`, stored in `memory.json`. The next session injects that compact memory
and opens by resuming exactly where you left off: "Welcome back — session 4. Where we
left off: …". No re-explanation, ever.

**How we built it.** Python. All inference is Qwen (qwen-turbo) on Alibaba Cloud Model
Studio via the DashScope international OpenAI-compatible endpoint. `agent.py` runs the
session loop — it is the deployment-proof file; every model call in it goes to Alibaba
Cloud. `memory.py` owns distillation, forgetting, and crash-safe atomic persistence.

**Track fit (MemoryAgent).** *Efficient memory storage and retrieval*: one distillation
call per session compresses the whole transcript into ≤40 structured items. *Timely
forgetting of outdated information*: resolved threads are dropped at distill time, stale
facts are rewritten instead of appended, and a hard 40-item cap prunes oldest-first.
*Recalling critical memories within limited context windows*: sessions inject only the
compact memory block plus recent turns — never past transcripts — so recall costs
hundreds of tokens, not a context window.

**Challenges.** Making memory unbreakable: atomic writes (temp file + rename), corrupt-file
quarantine, and failure-safe distillation — if the model call fails at quit time, memory
degrades to "unchanged", never to "corrupted". We demo a mid-session crash on video.

**What's next.** Multi-project memory namespaces; semantic retrieval over long memories;
shared team memory so a whole team never re-explains the project either.

**Built with:** python · qwen · alibaba-cloud · dashscope · openai-sdk

## §7 Submission checklist (Sunday)

- [ ] Repo public; GitHub About panel shows **MIT license** (= detectable)
- [ ] `.env` NOT in repo (GitHub search the repo for `DASHSCOPE` → only `.env.example` hits)
- [ ] README renders; architecture.png displays; pitch verbatim at top
- [ ] `python test_connection.py` GREEN on the final code
- [ ] Video: under 3:00 · public · plays in incognito · no music · English captions
- [ ] Devpost fields: title **Hilo** · tagline = pitch verbatim · description = §6 with [MODEL] filled
- [ ] Track 1 MemoryAgent selected
- [ ] Repo URL + deployment proof URL = `https://github.com/phazon2/hilo/blob/main/agent.py`
- [ ] Architecture diagram attached/linked
- [ ] Video URL attached · optional blog URL attached
- [ ] SUBMIT → screenshot confirmation → send to Claude
- [ ] Extraction session: binding constraint, problem class, transferable principle

## §8 Working rules for AI-assisted sessions

1. One feature per session, stated in one sentence before starting.
2. After every accepted change: `python test_connection.py`, then run the feature.
3. Never accept a diff you can't read; too big to read = too big, ask smaller.
4. A feature not in the demo video does not exist — cut it.
5. Stuck > 30 min → paste the artifact (error/code/screenshot) to chat Claude → one move + one check back.
6. Scope is closed. The remaining work is assets and the button, not code.
