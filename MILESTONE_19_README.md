# Milestone 19 — MethodMind interface refresh

## Start

From this folder:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 and hard-refresh (Ctrl+Shift+R) if your browser cached the previous interface. Copy `.env.example` to `.env` and set your own provider credentials for live AI; never commit or share real keys.

## What's new

- Violet/lime visual system with light and dark theme toggle (theme preference saved locally).
- Mindy mascot, conversation-first welcome screen and new chat button.
- Sidebar navigation and in-session recent conversations.
- Student-controlled activity opening; conversation moves into a collapsible right-hand panel while the existing checked activities remain in the middle.
- Responsive layout; no changes to Python backend or learning checkers.

## Important limits

- Conversation IDs are stored only in page memory; refresh does not restore a conversation. The existing backend expires conversations after two hours. The sidebar therefore shows only conversations created during this page session.
- Activity state may reset on a full refresh or when starting a new activity; avoid reloading mid-activity.
- 'My progress' is not a new analytics dashboard; current checked evidence remains within existing activity screens.
- The mascot image is a crop from the approved visual concept, not yet a production-ready transparent asset.

## Verification

`PYTHONPATH=. python -m pytest -q` (Linux/macOS) or `$env:PYTHONPATH='.'; python -m pytest -q` (PowerShell).

In this environment, 76 tests pass and 4 existing step-tutor tests fail due to missing `app.main.generate_adaptive_step_hint` symbol. The same four failures occur in the original uploaded ZIP. This UI change did not introduce them.

Manual browser checks still needed: send chat message, start algebra, start biology, link checked activity, collapse/reopen Mindy, switch themes, check mobile layout.
