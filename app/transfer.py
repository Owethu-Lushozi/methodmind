"""Deterministic practice checks for the hackathon learning-transfer demo."""

from app.math_engine import MathInputError, verify_equation

TRANSFER_PROBLEMS = (
    {"equation": "4(x-1)+2=18", "hint": "Start by undoing the addition of 2. Then undo multiplication by 4."},
    {"equation": "5(x+2)-3=22", "hint": "Undo the subtraction of 3 first, then divide by 5."},
)


def check_transfer(stage: int, proposed_answer: str, reasoning: str = "") -> dict:
    if stage not in range(len(TRANSFER_PROBLEMS)):
        raise MathInputError("Choose an available practice stage (0 or 1).")
    problem = TRANSFER_PROBLEMS[stage]
    answer = proposed_answer.strip().removeprefix("x=").removeprefix("x =").strip()
    if not answer:
        raise MathInputError("Enter a proposed value for x.")
    verification = verify_equation(problem["equation"], answer)
    correct = bool(verification.is_correct)
    # An answer checker cannot know whether reasoning is truly understood.
    reasoning_supplied = bool(reasoning.strip())
    return {
        "stage": stage,
        "equation": problem["equation"],
        "correct": correct,
        "feedback": (
            "Your value satisfies the equation. Nice transfer! Now explain why your steps work."
            if correct and not reasoning_supplied else
            "Your answer is correct. Your explanation is recorded, but it hasn't been assessed for conceptual accuracy."
            if correct else
            f"Not quite: x={answer} makes the left side {verification.substituted_left} and the right side {verification.substituted_right}. Try again."
        ),
        "hint": None if correct else problem["hint"],
        "next_stage": stage + 1 if correct and stage + 1 < len(TRANSFER_PROBLEMS) else None,
        "next_question": TRANSFER_PROBLEMS[stage + 1]["equation"] if correct and stage + 1 < len(TRANSFER_PROBLEMS) else None,
        "practice_complete": correct and stage == len(TRANSFER_PROBLEMS) - 1,
        "reasoning_assessed": False,
    }
