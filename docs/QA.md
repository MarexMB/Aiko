# Aiko v0.1 verification

## Performed

- Windows; Python 3.11.5, PySide6 6.12.0, httpx 0.28.1. `pip check`: no broken requirements.
- 38 tests passed with live Ollama enabled; five GUI tests also passed on native Windows Qt.
- Ruff lint, formatting (27 Python files), and compilation passed.
- Real Ollama 0.40.15 / qwen3:8b metadata check and final-answer request succeeded.
- `ollama ps`: 100% GPU, 4096 context, about 5.6 GB on this machine.
- Native `main.py` launch through pythonw.exe produced a responding application process;
  the final build was relaunched through `.venv\Scripts\python.exe main.py`.
- Actual Qt widget previews rendered and visually inspected; Windows fonts explicitly loaded
  for headless previews. These are widget renders, not desktop compositor screenshots.

Tests cover validation, editable profiles, SQLite restart persistence, parameterized text,
cascade deletion, paging, request payloads, reasoning filtering, malformed/incomplete streams,
HTTP errors/redirects, missing service/model, remote-alias rejection before chat submission,
context limits, inert HTML, Enter/Shift+Enter, duplicate-send prevention, asynchronous replies,
cancellation, quit during generation, mascot painting/clicks/reduced motion, and clamping.

Computer-use helper: `Computer Use native pipe is unavailable ... os error 2`, including retry
and session reset. No successful live desktop inspection is claimed.

## Manual checklist — still unverified

1. Launch Aiko. Confirm transparent silhouette, no border/background on the actual desktop.
2. Click to toggle chat. Drag without opening chat. Right-click Open Chat / Settings / Quit.
3. Type in another app: idle Aiko must not steal focus. Observe blink/tilt/bounce and
   thinking/happy transitions during a real response.
4. Drag across monitors, quit, relaunch. Disconnect a monitor and verify recovery.
   Repeat at 100%, 150%, 200%, and mixed display scaling.
5. Reduced motion stops blinking/movement. Always-on-top changes stacking. Restart to verify.
6. Send Serbian and English prompts; inspect final replies and UI responsiveness. Stop
   during loading and generation, then send again.
7. Close Ollama; Check connection/send must show guidance. Restart and retry. Try a missing
   model name, then restore qwen3:8b; do not redownload an already installed model.
8. New Chat, reopen older chat, restart, browse pages. Cancel/confirm Delete and Clear all
   using disposable test chats, never unintended real history.
9. Export/edit/import settings; test Cancel versus Save and malformed JSON/invalid fields.
10. Quit during generation; confirm no orphan Aiko process or QThread warning. Ollama may
    independently keep its model loaded for five minutes.
11. Inspect Task Manager idle usage for several minutes, with and without reduced motion.
12. Disconnect Internet after setup; local inference must still work. Test sleep/resume
    and text readability at the minimum window size.

Automated tests use temporary databases and never the production history.
