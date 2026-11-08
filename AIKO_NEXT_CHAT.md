# Aiko — handoff for the next chat

Paste this document into the next chat to continue working on my existing project.
Read the actual repository before making changes; this is a snapshot, not a substitute for inspection.

## What I am building

I am a beginner programmer building **Aiko**, a local-first Windows 11 desktop AI companion.
Act as a senior Python desktop engineer and pragmatic QA engineer. Implement actual changes,
keep the project maintainable, and give clear Windows PowerShell instructions.

- Workspace: `C:\Users\vikto\OneDrive\Desktop\AikoAI\Aiko`
- GitHub remote: `https://github.com/MarexMB/Aiko.git`
- Branch: `main`
- Hardware target: NVIDIA RTX 5060 Ti, 8 GB VRAM, 32 GB RAM.
- Stack: Python, PySide6, httpx, SQLite, local Ollama.
- Default model: `qwen3:8b`; URL: `http://127.0.0.1:11434`; context: 4096.
- Windows is the primary target. Do not switch development to Linux.
- Python 3.13 is preferred for a new install, but the working environment here uses Python 3.11.5.
- Tested dependency versions: PySide6 6.12.0, httpx 0.28.1, Ollama 0.40.15.

## Latest user feedback — especially important

I requested yellow hair, blue eyes, and pixel art. That design was implemented and retained.
I then requested a livelier, higher-resolution version. The attempted update mostly moved
the model around, added awkward hair detail, and did not feel like real animation.

My exact feedback was:

> there is no real animation its just her model moving around, and hair feels akward, please fix or revert changes to before last prompt

The assistant chose to **revert the entire latest visual update**. That revert is complete.
The current accepted baseline is the earlier **40×50 pixel-art design**, yellow hair, blue eyes,
violet dress, and blue star pin. It has basic blinking, pixel-step bouncing, thinking dots,
and a happy eye expression. It does not have a full animation system.

If I ask for animation improvements again, use actual changes in pose/expression/body parts
and coherent animation frames. Translating the whole sprite or adding thin hair streaks did
not satisfy me. Do not silently restore the rejected implementation. Preserve the accepted
baseline until the next requested change is clear.

## Current Git state

Working tree was clean before this handoff file was created. No commits were pushed during
the previous work. Inspect status and remotes again; remote state may have changed.

Relevant commits:

```text
d9fbc90 fix: restore previous pixel-art mascot design
b9a1def feat: increase mascot pixel detail and add lively gestures
6f4cd2a feat: redesign Aiko as a blonde blue-eyed pixel-art mascot
a4533c2 docs: add Windows setup architecture QA guide and Qt previews
02a6462 fix: timestamp connection status and test large-history navigation
06b574e fix: reject remote model aliases and preserve bounded history navigation
b9d0ffe feat: add original animated mascot with dragging and screen-safe placement
caf0870 feat: build responsive chat UI with history settings and cancellation
172fbf5 feat: implement bounded local Ollama inference with thinking disabled
f66a5a8 feat: persist chat sessions and explicit preferences in SQLite
2577454 feat: add validated local settings and editable Aiko profile
7ba59b9 chore: initialize Python package and privacy-conscious gitignore
e684665 Initial commit
```

`b9a1def` is the rejected update; `d9fbc90` restores the affected files exactly to `6f4cd2a`.
Preserve history and user changes. Use focused Conventional Commits after meaningful changes,
stage deliberately, and inspect the staged diff. Do not force-push or rewrite history.
Push only if I explicitly authorize it.

## Run the existing project

In PowerShell:

```powershell
cd 'C:\Users\vikto\OneDrive\Desktop\AikoAI\Aiko'
.\.venv\Scripts\python.exe main.py
```

Click the mascot to open/toggle chat. Right-click for Open Chat, Settings, or Quit.
Closing the chat hides it; it does not exit the application. After source changes,
quit the running Aiko instance and relaunch. There is no hot reload or single-instance guard.
Do not assume the running process reflects the latest source.

Check Ollama:

```powershell
ollama --version
ollama list
ollama ps
```

`qwen3:8b` was already installed. Do not automatically download it again. Start Ollama from
the Start menu if necessary, or run `ollama serve` in a separate terminal. A local inference
test succeeded; `ollama ps` reported **100% GPU, 4096 context, approximately 5.6 GB** during
that run. This is a recorded observation, not a guarantee for every setting or future run.

For a fresh environment only:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Preserve the existing working `.venv`. Earlier sandboxed commands incorrectly appeared to
show a missing Python installation; running with appropriate tool permissions exposed the
working base interpreter. Do not conclude the environment is broken from that error alone.

## Implemented functionality

- Borderless transparent mascot, always-on-top option, drag to move, position persistence,
  screen-bound clamping, click-to-chat and right-click menu.
- Compact dark chat window with violet accents; Enter sends, Shift+Enter adds a newline.
- QThread worker with asyncio/httpx; widgets updated through Qt signals.
- Duplicate sends prevented; Stop cancels the request; Quit handles worker shutdown.
- Ollama `think: false`, `/no_think` in personality, discarded `thinking` field, residual
  think-tag filtering. Only the final answer is shown.
- Validated numeric loopback HTTP endpoints; no redirects or environment proxies.
- Local model metadata checked before sending conversation text. Cloud model names and
  remote aliases are rejected. Current validation expects local GGUF metadata.
- Bounded context, generation duration, output size, and history display.
- SQLite sessions/messages and a separate explicit-preferences table; no automatic fact extraction.
- New Chat, older conversations, paged messages, confirmed delete-one/delete-all controls.
- Settings dialog plus JSON import/export. Import takes effect on Save; JSON is not automatically
  loaded on startup. `settings.example.json` is provided.
- Separate editable character profile, with only Aiko implemented.
- Local rotating event/error logging without chat text or raw server error bodies.

## Key files and architecture

```text
main.py                         entry point
aiko/app.py                     controller, lifecycle, GUI-thread database ownership
aiko/config.py                  validated settings and per-user storage paths
aiko/characters/profile.py      CharacterProfile and CharacterManager
aiko/characters/aiko.json       personality, colors, animation preferences
aiko/ai/ollama_client.py         local HTTP client, metadata checks, final-answer filtering
aiko/ai/conversation_service.py conservative recent-context budget
aiko/memory/database.py         parameterized SQLite persistence
aiko/ui/worker.py               QThread/asyncio cancellation and result signals
aiko/ui/chat_window.py          chat widgets and escaped inert message text
aiko/ui/settings_dialog.py      settings validation/import/export
aiko/ui/mascot_window.py        desktop window, dragging, menus, screen placement
aiko/ui/mascot_widget.py        original code-drawn pixel-art renderer
aiko/resources/README.md        original artwork/license and renderer notes
scripts/render_preview.py       actual Qt widget renders with labeled sample conversation
docs/images/mascot-preview.png  current mascot preview
docs/images/chat-preview.png    chat widget preview (sample text)
docs/QA.md                     tested vs manual/unverified checks
README.md                       full setup, architecture, storage, troubleshooting, roadmap
```

Character profile controls the prompt, colors (`hair`, `eyes`, `accent`, `dress`, `skin`),
and animation settings. Keep it independent from AI code. Current hair is `#f8d34f`, eyes
`#318ee8`. The renderer draws a 40×50 transparent image and enlarges it without smoothing.

SQLite stays on the GUI thread; workers get copied messages and immutable settings.
History is not unlimited model memory: at most 40 recent messages are considered, with
a conservative UTF-8 byte budget reserving 768 output tokens and 256 template tokens.
Display pages are capped at 20 messages / 100k characters; answers at 768 tokens / 32k characters.

## Hard scope and privacy restrictions

- **NO voice chat, microphone, STT, TTS, audio playback, lip-sync, or voice placeholders/dependencies.**
- No screen capture/watching, OCR, webcam, vision features, or autonomous computer tools in Aiko.
- No AI shell execution, file editing, browsing automation, cloud model routing, analytics,
  telemetry, accounts, paid tools, or API keys.
- No automatic model/dependency downloads, updates, scheduled agents, or login auto-start.
- Only one character now. Keep extensibility, but do not build a marketplace/picker or rigged engine.
- Use original or clearly licensed artwork; no proprietary Capri/copyrighted character assets.
- Treat model output as untrusted chat text; never execute it.
- Offline operation after dependencies and model are installed is required.

Local data is `%LOCALAPPDATA%\Aiko\aiko.sqlite3`; logs are in the same folder (`aiko.log`
and rotated backups). Data is plaintext, not encrypted. Quit before deleting/resetting it.
UI history deletion keeps preferences. Do not commit chats, databases, logs, secrets, or models.

## Validation and limits of what was verified

Earlier full MVP verification: **38 tests passed with the real Ollama test enabled**;
**5 GUI tests passed using native Windows Qt**. Lint, formatting, compilation, and dependency
checks passed. The app launched and its process was responding.

After the accepted pixel-art redesign: **37 tests passed, 1 live integration test skipped**.
The rejected update passed its five GUI tests but failed my visual expectations. The final
revert was verified by exact file comparison to the accepted design; tests were not rerun
after that exact restoration. Do not claim newer tests were run without running them.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m compileall -q aiko main.py
.\.venv\Scripts\python.exe -m pip check
```

Optional real local model test (no download):

```powershell
$env:AIKO_TEST_LIVE = '1'
.\.venv\Scripts\python.exe -m pytest -q
Remove-Item Env:AIKO_TEST_LIVE
```

Native Windows Qt GUI tests:

```powershell
$env:QT_QPA_PLATFORM = 'windows'
.\.venv\Scripts\python.exe -m pytest tests/test_gui.py -q
Remove-Item Env:QT_QPA_PLATFORM
```

Preview: `.\.venv\Scripts\python.exe scripts/render_preview.py`.
Previews are real widget renders, not desktop compositor screenshots. Chat text in them is
clearly labeled sample text. The Windows computer-use helper previously failed with
`Computer Use native pipe is unavailable ... os error 2`, including retry/reset.
Live desktop transparency, focus stealing, mixed DPI/cross-monitor dragging, and sustained
idle CPU/GPU usage remain manual checks. Linux and Python 3.13 were not tested here.

## How to continue

Start with `git status`, inspect the relevant files, and follow my next request.
The last requested action was to create this handoff, not to resume the rejected redesign.
Make reasonable decisions without excessive questions, keep changes focused, test what matters,
and clearly separate actual verification from assumptions.
