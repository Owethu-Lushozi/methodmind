"""Explainable rule-based algebra coaching, separate from simulated and Gemini agents."""

import re

from app.math_engine import MathInputError, verify_equation


def _extract_candidate(attempt: str) -> str | None:
    match = re.search(r"\bx\s*=\s*([-+]?\d+(?:\.\d+)?(?:/\d+)?)\b", attempt, flags=re.I)
    return match.group(1) if match else None


def run_coach(equation: str, student_attempt: str) -> dict:
    if not student_attempt.strip():
        return {"mode": "rule_based", "status": "needs_student_attempt", "question": "Tell me what you tried, even if you're unsure.", "events": []}
    checked = verify_equation(equation)
    if checked.classification != "unique_solution":
        raise MathInputError("This coach currently needs one linear equation with a unique solution.")

    answer = checked.correct_solution
    guidance = "Let's work through your equation together. Start by simplifying both sides, and I'll check each step before we move on."
    events = [{"agent": "diagnostic", "action": "inspect_student_input", "detail": "Rule-based check, not an AI inference."}]
    candidate = _extract_candidate(student_attempt)
    if candidate is not None:
        result = verify_equation(equation, candidate)
        if result.is_correct:
            diagnosis = f"Your submitted x={candidate} satisfies the equation. Let's check whether the method transfers to a new question."
        else:
            diagnosis = (f"Your x={candidate} gives left side {result.substituted_left} and right side {result.substituted_right}. "
                         "That confirms the answer doesn't balance. It doesn't establish which step caused the mistake.")
        events.append({"agent": "diagnostic", "action": "verify_student_answer", "detail": f"x={candidate}; pass={result.is_correct}"})
    else:
        diagnosis = "I can't identify a numeric answer from your description, so I'll demonstrate a reusable balancing method."

    lowered = student_attempt.lower()
    if any(word in lowered for word in ("distribut", "bracket", "expand")):
        diagnosis += " You mentioned brackets or distribution, so we'll pay special attention to expanding correctly."
        guidance += " Remember: a(b+c) means multiply a by BOTH terms inside the brackets. What would that look like here?"
    elif any(word in lowered for word in ("divide", "division", "divid")):
        diagnosis += " You mentioned division, so we'll emphasize dividing BOTH sides by the full coefficient of x."
        guidance += " When you reach division, remember to apply it equally to both sides."
    elif any(word in lowered for word in ("subtract", "minus", "sign", "negative")):
        diagnosis += " You mentioned subtraction or signs, so check that each balancing operation affects both sides."

    events.append({"agent": "teaching", "action": "invite_first_step", "detail": "Only the first prompt is revealed; verified transformations follow successful student attempts."})
    final_check = verify_equation(equation, answer)
    events.append({"agent": "reviewer", "action": "sympy_verify", "detail": f"pass={final_check.is_correct}; left={final_check.substituted_left}; right={final_check.substituted_right}"})
    if not final_check.is_correct:
        raise MathInputError("Internal answer verification failed.")
    return {
        "mode": "rule_based", "status": "verified", "diagnosis": diagnosis,
        "explanation": guidance, "verified_answer": None,
        "transfer_question": "4(x-1)+2=18", "revision_count": 0,
        "events": events,
        "disclaimer": "Offline rule-based coaching: steps are generated symbolically and checked with SymPy. Student misconceptions are not independently inferred or validated by AI.",
    }
