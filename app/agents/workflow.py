"""Mock-mode multi-role workflow for developing MethodMind safely.

The mock provider deliberately emits an incorrect first draft to exercise the
review/correction plumbing. This is NOT evidence of live AI autonomy.
"""

import re
from dataclasses import dataclass
from typing import Protocol

from app.math_engine import MathInputError, verify_equation


@dataclass
class TeachingDraft:
    explanation: str
    proposed_answer: str


class DraftProvider(Protocol):
    def draft(self, equation: str, objective: str, correct_answer: str) -> TeachingDraft: ...
    def revise(self, equation: str, objective: str, reviewer_feedback: str, correct_answer: str) -> TeachingDraft: ...


class MockProvider:
    """Deterministic placeholder; always creates a deliberate first error."""

    def draft(self, equation: str, objective: str, correct_answer: str) -> TeachingDraft:
        return TeachingDraft(
            explanation="Mock draft: I incorrectly conclude that x = 5.",
            proposed_answer="5" if correct_answer != "5" else "6",
        )

    def revise(self, equation: str, objective: str, reviewer_feedback: str, correct_answer: str) -> TeachingDraft:
        return TeachingDraft(
            explanation=f"Mock revision: solving {equation} gives x = {correct_answer}. Check by substitution.",
            proposed_answer=correct_answer,
        )


def run_mock_learning_cycle(equation: str, student_attempt: str, max_revisions: int = 2) -> dict:
    if not student_attempt.strip():
        return {
            "mode": "mock", "status": "needs_student_attempt",
            "question": "What have you tried, or which step feels confusing?",
            "events": [],
        }

    verified_problem = verify_equation(equation)
    if verified_problem.classification != "unique_solution":
        raise MathInputError("The current learning demo needs an equation with one solution.")
    answer = verified_problem.correct_solution
    events: list[dict] = []

    def log(agent: str, action: str, detail: str):
        events.append({"agent": agent, "action": action, "detail": detail})

    # A mock diagnosis is based on the presence of attempted work. It is not a
    # clinically/pedagogically reliable inferred misconception.
    attempt_match = re.search(r"(?:x\s*=\s*)(-?\d+(?:\.\d+)?)", student_attempt, flags=re.I)
    if attempt_match:
        attempted = verify_equation(equation, attempt_match.group(1))
        objective = "check algebraic steps by substituting the candidate into the original equation"
        log("diagnostic", "inspect_attempt", f"Detected proposed x={attempt_match.group(1)}; verification={attempted.is_correct}.")
    else:
        objective = "solve a one-variable linear equation and verify the result"
        log("diagnostic", "request_instruction", "Attempt supplied without a parseable x=value; use a general linear-equation objective.")

    provider: DraftProvider = MockProvider()
    draft = provider.draft(equation, objective, answer)
    log("teaching", "draft", f"Proposed x={draft.proposed_answer} (simulated output).")
    review = verify_equation(equation, draft.proposed_answer)
    log("reviewer", "verify", f"PASS={review.is_correct}; left={review.substituted_left}, right={review.substituted_right}.")
    revisions = 0
    while not review.is_correct and revisions < max_revisions:
        revisions += 1
        log("orchestrator", "request_revision", f"Reviewer flagged incorrect answer; attempt {revisions}/{max_revisions}.")
        draft = provider.revise(equation, objective, review.explanation, answer)
        log("teaching", "revise", f"Proposed x={draft.proposed_answer} (simulated revision).")
        review = verify_equation(equation, draft.proposed_answer)
        log("reviewer", "recheck", f"PASS={review.is_correct}; left={review.substituted_left}, right={review.substituted_right}.")

    status = "verified" if review.is_correct else "verification_failed"
    # This is only a canned transfer exercise until live generation is added.
    transfer_equation = "4(x-1)+2=18"
    return {
        "mode": "mock", "status": status,
        "diagnosis": objective,
        "explanation": draft.explanation if review.is_correct else None,
        "verified_answer": review.correct_solution if review.is_correct else None,
        "transfer_question": transfer_equation if review.is_correct else None,
        "revision_count": revisions,
        "events": events,
        "disclaimer": "Mock-mode outputs are simulated. No LLM was called.",
    }
