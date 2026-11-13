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
# Live Groq workflow

Install updated dependencies with `python -m pip install -r requirements.txt`.
Keep `GROQ_API_KEY=...` in your local `.env` file (never commit it).
Set `GROQ_MODEL=openai/gpt-oss-20b` or another model listed in your GroqCloud account.

POST `/learning/run` with `{"equation":"3(x-2)+5=17","student_attempt":"I tried x=5"}` for live Diagnostic and Teaching agents. SymPy independently checks the proposed first step. When Groq is unavailable, use `/learning/coach` for fully offline tutoring; `/learning/demo` is simulated.
# Offline symbolic coaching (Milestone 6)

POST `/learning/coach` with `{"equation":"3(x-2)+5=17","student_attempt":"I tried x=2"}`.
This mode uses a strict algebra parser and SymPy to build valid solving steps, checks the student's proposed numeric answer by substitution, and responds to explicitly mentioned topics such as brackets, division, or signs. It does not claim to infer an unseen misconception or assess conceptual mastery. The existing `/learning/demo` remains an explicitly simulated self-correction trace, while `/learning/run` invokes live Groq when available. On the website, select **Guided coaching · offline** to try the offline functionality.
# Interactive step tutoring (Milestone 7)

In **Guided coaching · offline**, the learner now works through three intermediate equations before unlocking the transfer exercise. The `/learning/step` endpoint accepts `{ "equation": "3(x-2)+5=17", "stage": 0, "submitted_equation": "3x-1=17" }` and checks both sides against the symbolically derived target form. Stages 1 and 2 then expect `3x=18` and `x=6`. Incorrect work receives a stage-specific hint; correct work advances. This is stateless practice checking, not authentication, persistent tracking, or a proof of mastery.
# Progressive reveal (Milestone 8)

Offline coaching starts with the current learning objective and a prompt, rather than showing the solved equation. The checked solution is not returned in the initial `/learning/coach` payload. Each successful `/learning/step` response provides `revealed_step` and a rationale for the just-completed transformation; incorrect attempts receive a hint but no target equation. After the final step, the verified answer and substitution check become visible, and the browser unlocks the transfer exercise. The endpoint itself is stateless and does **not** enforce authenticated completion or prevent direct API requests for later stages; this feature is an educational reveal flow, not a security boundary.

# Live AI with progressive tutoring (Milestone 9)

The website's **Live Groq AI** mode asks a real **Diagnostic Agent** to interpret the *supplied* learner attempt and a **Teaching Agent** for an individualised opening question. The Teaching Agent privately proposes the first algebra transformation, which a separate **SymPy Reviewer** independently checks. If incorrect, the teaching agent gets one revision opportunity. The proposed equation and final answer are **not** sent to the browser; the learner completes the same three verified, progressively revealed steps as offline coaching. Only after step 3 does the transfer exercise unlock. The later step checks remain deterministic; a correct equation does not prove understanding.

Set these values in your local `.env` (do not share or commit the key):

```dotenv
GROQ_API_KEY=your_real_key_here
GROQ_MODEL=openai/gpt-oss-20b
# Optional model fallback, if both are available to your account:
# GROQ_MODELS=openai/gpt-oss-20b,openai/gpt-oss-120b
```

Create a GroqCloud API key at https://console.groq.com/keys and check model availability at https://console.groq.com/docs/models. The system never labels offline tutoring as live AI; when an AI hint request fails during a step, symbolic feedback is used. During the demo, open **Behind the scenes** for the diagnostic and teaching actions and independent verification. Run `python -m pytest -q` before presenting.

## Evidence-based learner diagnosis

When the learner explicitly submits a single numeric value such as `x=5`, the live workflow checks it with SymPy **before** asking Groq for a diagnosis. The verified substitution values appear in the diagnostic feedback, and the model is told that an incorrect answer alone does not identify which unseen algebra step was wrong. Ambiguous or missing candidate answers are not treated as verified numeric attempts. An incorrect answer never receives generic "great job" praise from the opening teaching response. The correct solution remains hidden until the learner completes the three-step reveal.

## Verified intermediate-step misconceptions (Milestone 11)

`/learning/step` now returns a `misconception` field only when a submitted equation matches an independently checked error pattern. Supported patterns include incomplete distribution (for example, replacing `3(x-2)+5` with `3x-2+5`), incorrect movement of constants after gathering x terms, and wrong final numeric values (checked through substitution). Every detected pattern includes `code`, `evidence`, and a conceptual `hint`. Unrecognised mistakes retain general feedback and `misconception: null`; the system never invents an unseen cause. Checked intermediate answers remain hidden until the student completes the current step.

## Adaptive teaching (Milestone 12)

The browser counts unsuccessful submissions **per tutoring step** and sends `attempt_number` (1–20) to `/learning/step`. Attempt 1 uses a gentle hint, attempt 2 offers focused guidance, and attempts 3+ offer a smaller worked example using different symbols or numbers without giving away the current equation's next step. A correct step unlocks the next stage and resets its attempt counter. In Live Groq mode, the first error may receive a personalised model-generated hint; repeated errors use deterministic SymPy-grounded scaffolds to conserve API quota and keep the presentation dependable. The count is client-maintained within the current browser session, not persistent student history or evidence of learning mastery.
# Milestone 13 — Conceptual understanding checkpoint

After all three algebra steps are checked, learners answer two short questions
about why distribution and balancing work before the transfer challenge appears.
Wrong answers receive choice-specific feedback and can be retried. The checks
are deterministic, require no additional Groq calls, and assess **recognition
of the rules**, not free-text reasoning or proof of conceptual mastery.

# Milestone 14 — Explain the method

Transfer exercises now require an explanation. SymPy first checks the numeric
answer; a conservative local rubric checks whether the explanation mentions an
operation and why both sides remain equal. Vague or one-sided explanations do
not advance. In Live Groq mode, a separate AI reasoning reviewer adds more
specific feedback; AI cannot override the local minimum-evidence requirement.
If Groq is unavailable, the local rubric remains usable. Correct answers,
appropriate multiple-choice selections, and passing the explanation rubric
are **not proof of conceptual mastery**. The opening AI tutor also rejects
responses that reveal the first intermediate equation too soon.

