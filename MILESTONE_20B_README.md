# Milestone 20B — Controlled Live Correction Demo

Copy the included `app/` and `tests/` folders over your existing project. Do not replace your `.env`.

Start with `python -m uvicorn app.main:app --reload` and open http://127.0.0.1:8000.

1. Select **Mathematics · Linear equations** and **Controlled LIVE correction · judges demo**.
2. Enter exactly `3(x-2)+5=17`, and `I tried x=5`.
3. Select **Explore my method**, then expand **Behind the scenes**.
4. Trace should show an explicitly injected `3x+1=17` proposal, SymPy rejection, revision request to live Groq, and independent recheck of Groq's revision.
5. The demonstration may fail safely if Groq is unavailable or produces an invalid revision. Do not claim a successful correction unless the trace confirms it.

**Judging honesty:** The first wrong step is intentionally injected by a demo controller; it is not a spontaneous LLM error. The revision request uses the normal live Groq path. Ordinary `/learning/run` is unchanged. No API key is shipped.

Run `python -m pytest -q` to check the full test suite.
