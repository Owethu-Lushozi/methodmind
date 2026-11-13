"""Routes learning actions through subject contracts and trusted checkers.

Session-state transitions and intent recognition will be added separately.
For now this is stateless and preserves the existing HTTP response contract.
"""

from app.agents.groq_workflow import ProviderUnavailable, generate_adaptive_step_hint, review_transfer_explanation
from app.learning.subjects import get_subject


def evaluate_step(subject_id: str, equation: str, stage: int,
                  submitted_equation: str, coaching_mode: str = "coach",
                  attempt_number: int = 1) -> dict:
    subject = get_subject(subject_id)
    result = subject.evaluate_response("guided_practice", equation=equation, stage=stage,
                                       submitted_equation=submitted_equation,
                                       attempt_number=attempt_number)
    result["hint_source"] = "symbolic" if not result["correct"] else None
    if not result["correct"] and coaching_mode == "groq" and result["support_level"] == 1:
        try:
            result["hint"] = generate_adaptive_step_hint(
                equation, stage, submitted_equation, result["feedback"], result["hint"])
            result["hint_source"] = "live_ai"
        except ProviderUnavailable:
            result["hint_source"] = "symbolic_fallback"
    elif not result["correct"] and coaching_mode == "groq":
        result["hint_source"] = "adaptive_scaffold"
    return result


def evaluate_concept(subject_id: str, stage: int, choice: int) -> dict:
    return get_subject(subject_id).evaluate_response("concept_check", stage=stage, choice=choice)


def evaluate_transfer(subject_id: str, stage: int, proposed_answer: str,
                      reasoning: str = "", coaching_mode: str = "coach") -> dict:
    subject = get_subject(subject_id)
    result = subject.evaluate_response("transfer", stage=stage,
                                       proposed_answer=proposed_answer, reasoning=reasoning)
    result["review_source"] = "offline_rubric"
    if result["answer_correct"] and coaching_mode == "groq" and reasoning.strip():
        try:
            review = review_transfer_explanation(subject.generate_transfer(stage)["equation"], reasoning)
            result["review_source"] = "groq_with_local_guard"
            if review["status"] != "supported":
                result.update(correct=False, practice_complete=False, next_stage=None,
                              next_question=None, reasoning_status=review["status"])
            if result["correct"] or review["status"] != "supported":
                result["feedback"] = "Your value satisfies the equation. " + review["feedback"]
            else:
                result["feedback"] += " The AI also found the explanation plausible, but more explicit reasoning is needed for this checkpoint."
        except ProviderUnavailable:
            result["review_source"] = "offline_fallback"
    return result
