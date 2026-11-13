# MethodMind — Koa's Lab

**Colleague Zero Autonomous Agent Hackathon | 13–14 November 2026**

> Don't just learn the answer. Learn how to solve the problem.

MethodMind is a proposed autonomous learning colleague that diagnoses a student's difficulty with an algebra problem, creates a transferable learning activity, independently verifies the mathematics, revises errors, and assesses a fresh attempt.

**Status: Milestone 2 mock-mode workflow implemented locally.** It demonstrates role hand-offs and a review/revision loop with deterministic sample outputs; it does not yet call a real AI model. The mathematical checker is real.

## Planned architecture

1. **Diagnostic agent:** interpret the learner's attempt and choose the underlying learning objective.
2. **Teaching agent:** write a worked explanation and a structurally different practice question.
3. **Reviewer agent:** validate mathematics with SymPy, flag mistakes, request a revision, and re-check.
4. **Orchestrator:** decide next actions, record agent hand-offs, impose retry limits, and return the verified result or a clear failure.

The design uses separate roles and structured hand-offs. Simply chaining three prompts is not the goal.

## Proposed live-demo path

Student attempt → diagnosis → teaching draft → independent math check → correction if required → verified explanation → new question → feedback on the student's attempt.

The demo will show a genuine incorrect intermediate result, a reviewer flag, an automatic correction, and the successful re-check. Until implemented and tested, this remains the target rather than a demonstrated capability.

## Scope

- **MVP topic:** one-variable linear algebra equations.
- **Storage:** no database needed for a single live learning session. In-memory state first; optional SQLite later for progress/history.
- **Backend:** Python + FastAPI; SymPy for deterministic checking; LLM provider to be selected.
- **Frontend:** a small React interface later if the backend works reliably.

## Local setup

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for the API documentation. The `/health` and `/math/verify` endpoints work. `/learning/demo` runs the mock workflow only.

For the mock workflow, use **POST /learning/demo**:

```json
{"equation": "3(x-2)+5=17", "student_attempt": "I tried x=5"}
```

The response includes a diagnosis, a simulated incorrect teaching draft, a real SymPy verification failure, a simulated revision, and a successful re-check. The response explicitly identifies `mode: mock`. **Do not present this as live AI autonomy.**

To test the checker, open **POST /math/verify** in the API docs, click **Try it out**, and submit:

```json
{
  "equation": "3(x-2)+5=17",
  "proposed_answer": "5"
}
```

It should report `is_correct: false`, with left side `14`, right side `17`, and `correct_solution: "6"`.

Supported notation: numbers (including decimals), `x`, `+`, `-`, `*`, `/`, parentheses, `2x` and `3(x+1)`. Only linear equations in x are supported; exponentiation and division by x are intentionally rejected. For equations with infinitely many solutions, an individual numeric candidate may satisfy the equation even though no unique solution exists: inspect `classification` as well as `is_correct`.

```bash
pytest
```

## Proposed milestones

- [x] Document problem, scope, agent roles, and setup
- [x] Backend scaffold and health endpoint
- [x] Implement strict algebra parser and deterministic solution verification
- [x] Build mock-provider workflow with separate role functions and visible review/revision log
- [ ] Replace mock responses with real model-backed agent decisions
- [ ] Implement structured agent inputs/outputs and orchestration
- [ ] Connect an LLM securely via environment variables
- [ ] Integrate SymPy review and bounded correction loop
- [ ] Add transfer-question evaluation
- [ ] Build a simple learner UI and visible agent log
- [ ] Rehearse a full live demo and failure handling

## Judging alignment

| Criterion | Planned evidence |
| --- | --- |
| Reasoning & planning | Input-dependent plan and next-action log |
| Self-correction | Real error flagged, fixed, and rechecked |
| Reliability | End-to-end demo with sensible error handling |
| Multi-agent collaboration | Distinct roles and visible structured hand-offs |
| EdTech impact | New problem tests transfer, not memorisation |
| Presentation & Q&A | Clear architecture and live demo |
| Professionalism | Honest documentation, tests, and version history |

## Security

Never commit API keys, `.env` files, student-identifying information, or real learner data. Use synthetic examples for the hackathon demo.

**Team:** Koa's Lab · **Solo developer:** Owethu Lushozi
# Live Gemini workflow (Milestone 3)

Install updated dependencies with `python -m pip install -r requirements.txt`.
Keep `GEMINI_API_KEY=...` in your local `.env` file (never commit it).
You may also set `GEMINI_MODEL=gemini-3.8-flash`; use a model available to your own account.

POST `/learning/run` with `{"equation":"3(x-2)+5=17","student_attempt":"I tried x=5"}` for live Diagnostic, Teaching and Review agents. The independent SymPy verifier checks the final answer and asks for revisions when needed. If Gemini is overloaded, the endpoint returns HTTP 503; use `/learning/demo` for the clearly labeled simulated demonstration. This is an early prototype for single-variable equations, not a guarantee that all generated teaching explanations are correct.
# Offline symbolic coaching (Milestone 6)

POST `/learning/coach` with `{"equation":"3(x-2)+5=17","student_attempt":"I tried x=2"}`.
This mode uses a strict algebra parser and SymPy to build valid solving steps, checks the student's proposed numeric answer by substitution, and responds to explicitly mentioned topics such as brackets, division, or signs. It does not claim to infer an unseen misconception or assess conceptual mastery. The existing `/learning/demo` remains an explicitly simulated self-correction trace, while `/learning/run` invokes live Gemini when available. On the website, select **Guided coaching · offline** to try the new functionality.
# Interactive step tutoring (Milestone 7)

In **Guided coaching · offline**, the learner now works through three intermediate equations before unlocking the transfer exercise. The `/learning/step` endpoint accepts `{ "equation": "3(x-2)+5=17", "stage": 0, "submitted_equation": "3x-1=17" }` and checks both sides against the symbolically derived target form. Stages 1 and 2 then expect `3x=18` and `x=6`. Incorrect work receives a stage-specific hint; correct work advances. This is stateless practice checking, not authentication, persistent tracking, or a proof of mastery.
# Progressive reveal (Milestone 8)

Offline coaching starts with the current learning objective and a prompt, rather than showing the solved equation. The checked solution is not returned in the initial `/learning/coach` payload. Each successful `/learning/step` response provides `revealed_step` and a rationale for the just-completed transformation; incorrect attempts receive a hint but no target equation. After the final step, the verified answer and substitution check become visible, and the browser unlocks the transfer exercise. The endpoint itself is stateless and does **not** enforce authenticated completion or prevent direct API requests for later stages; this feature is an educational reveal flow, not a security boundary.
