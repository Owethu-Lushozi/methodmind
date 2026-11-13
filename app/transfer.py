"""Deterministic practice checks for the hackathon learning-transfer demo."""

import re

from app.math_engine import MathInputError, verify_equation

TRANSFER_PROBLEMS = (
    {"equation": "4(x-1)+2=18", "hint": "Start by undoing the addition of 2. Then undo multiplication by 4."},
    {"equation": "5(x+2)-3=22", "hint": "Undo the subtraction of 3 first, then divide by 5."},
)


def assess_explanation(reasoning: str, stage: int) -> dict:
    """Conservative local rubric: useful evidence, never a proof of mastery."""
    explanation = reasoning.strip().lower()
    if len(explanation.split()) < 6:
        return {"status": "needs_detail", "feedback": "Explain what you did to both sides and why it keeps the equation balanced."}
    if (re.search(r"(only|just)\s+(?:on|to)\s+(?:the\s+)?(?:left|right)(?:\s+side)?", explanation)
            or re.search(r"(?:left|right)\s+side\s+only", explanation)):
        return {"status": "misconception", "feedback": "Changing one side alone usually breaks equality. What operation must you apply to both sides?"}
    balance = bool(re.search(r"both\s+sides|each\s+side|same\s+operation|keep\s+(?:it\s+)?balanced|preserv\w*\s+equal", explanation))
    operation = bool(re.search(r"add|subtract|minus|plus|multiply|divide|divid|distribut|expand|undo|isolat", explanation))
    if balance and operation:
        return {"status": "supported", "feedback": "Your explanation mentions an operation and preserving equality. That's useful reasoning evidence; try applying it to a new problem."}
    if not balance:
        return {"status": "needs_detail", "feedback": "You mention a method, but why is it valid? Explain what happens to BOTH sides of the equation."}
    return {"status": "needs_detail", "feedback": "You mention balance. Name the operation you used to isolate x and explain why."}


def check_transfer(stage: int, proposed_answer: str, reasoning: str = "") -> dict:
    if stage not in range(len(TRANSFER_PROBLEMS)):
        raise MathInputError("Choose an available practice stage (0 or 1).")
    problem = TRANSFER_PROBLEMS[stage]
    answer = proposed_answer.strip().removeprefix("x=").removeprefix("x =").strip()
    if not answer:
        raise MathInputError("Enter a proposed value for x.")
    verification = verify_equation(problem["equation"], answer)
    correct = bool(verification.is_correct)
    assessment = assess_explanation(reasoning, stage) if correct else {"status": "not_checked", "feedback": ""}
    complete_step = correct and assessment["status"] == "supported"
    return {
        "stage": stage,
        "equation": problem["equation"],
        "correct": complete_step,
        "answer_correct": correct,
        "feedback": (
            "Your value satisfies the equation. " + assessment["feedback"]
            if correct else
            f"Not quite: x={answer} makes the left side {verification.substituted_left} and the right side {verification.substituted_right}. Try again."
        ),
        "hint": None if correct else problem["hint"],
        "next_stage": stage + 1 if complete_step and stage + 1 < len(TRANSFER_PROBLEMS) else None,
        "next_question": TRANSFER_PROBLEMS[stage + 1]["equation"] if complete_step and stage + 1 < len(TRANSFER_PROBLEMS) else None,
        "practice_complete": complete_step and stage == len(TRANSFER_PROBLEMS) - 1,
        "reasoning_assessed": correct,
        "reasoning_status": assessment["status"],
    }
