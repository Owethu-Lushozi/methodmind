# MethodMind Milestone 22 — Small safe capability refinements

Copy `app` and `tests` into your existing project, replacing matching files. No backend endpoints or API keys are changed.

Changes:
- Keep the existing broad conversational Groq teaching for complex topics.
- Avoid suggesting checked linear practice for quadratic, calculus and other advanced questions.
- Distinguish unsupported equations, authentication errors and provider failures in the learning workspace.

Test: `python -m pytest -q`; start: `python -m uvicorn app.main:app --reload`.

Try a linear equation in the checked workspace, then ask Mindy about a quadratic or calculus problem in conversation. The latter is conversational guidance, not independently verified practice.
