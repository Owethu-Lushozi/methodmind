# MethodMind Milestone 20A — Updates only

Copy the `app` and `tests` directories into your existing project, replacing matching files. No frontend files, backend routes, API contracts or secrets are changed.

Changes:
- Actual live Groq first-step proposal, reviewer decision, rejection reason, revision request and successful recheck appear in the existing optional agent trace.
- Three deterministic tests exercise the real correction loop using stubbed Groq responses.
- Four outdated test patch targets point to the actual orchestrator import.

Run: `python -m pytest -q`

Live verification: set GROQ_API_KEY locally, choose Live Groq AI, enter `3(x-2)+5=17` with `x=5`, click Explore my method, and expand Behind the scenes. A revision only appears if the live model actually makes a mistake. Never claim a correction occurred when revision_count is zero. Do not share API keys or .env files.
