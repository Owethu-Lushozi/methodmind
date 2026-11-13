# MethodMind — Koa's Lab

**Colleague Zero Autonomous Agent Hackathon | 13–14 November 2026**

> Don't just learn the answer. Learn how to solve the problem.

MethodMind is a proposed autonomous learning colleague that diagnoses a student's difficulty with an algebra problem, creates a transferable learning activity, independently verifies the mathematics, revises errors, and assesses a fresh attempt.

**Status: initial scaffold.** AI orchestration and mathematical validation have not yet been implemented. This repository deliberately distinguishes the intended design from working features.

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

Visit `http://127.0.0.1:8000/docs` for the API documentation. Currently the API only exposes a health check; the AI workflow is not yet available.

```bash
pytest
```

## Proposed milestones

- [x] Document problem, scope, agent roles, and setup
- [x] Backend scaffold and health endpoint
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
