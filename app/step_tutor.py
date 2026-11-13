"""Stateless three-stage equation practice with symbolic mistake detection."""

import re

from sympy import expand, simplify

from app.math_engine import MathInputError, X, _expression, verify_equation


STEP_PROMPTS = (
    "Step 1 of 3: Expand brackets and combine like terms. Write the simplified equation.",
    "Step 2 of 3: Collect x terms on the left and numbers on the right. Write that equation.",
    "Step 3 of 3: Isolate x. Write your final equation in the form x=your-answer.",
)

STEP_HINTS = (
    "Multiply every term inside each bracket, then combine terms on each side.",
    "Subtract the x term on the right from both sides; move constants by adding or subtracting equally.",
    "Divide BOTH sides by the coefficient of x.",
)

SMALL_EXAMPLES = (
    "Try a smaller example: 2(y-4) becomes 2y-8 because 2 multiplies EACH term. Now apply that rule to your bracket.",
    "Try a smaller example: 2y-3=9 becomes 2y=12 after adding 3 to BOTH sides. What operation does your step need?",
    "Try a smaller example: 2y=10 becomes y=5 after dividing BOTH sides by 2. What must you divide by here?",
)


def _sides(equation: str):
    if equation.count("=") != 1:
        raise MathInputError("Write an equation with exactly one equals sign.")
    left, right = equation.split("=", 1)
    return _expression(left), _expression(right)


def _detect_mistake(equation: str, stage: int, submitted_equation: str,
                    provided_left, provided_right, expected_left, expected_right) -> dict | None:
    """Label only independently reproducible error patterns, not inferred intent."""
    if stage == 0:
        # Recognize the specific, common error k(x +/- n) -> k*x +/- n,
        # where the student multiplied x but left the bracket's constant alone.
        bracket = re.compile(
            r"(?<![\w.])([+-]?\d+(?:\.\d+)?)\s*\(\s*x\s*([+-])\s*(\d+(?:\.\d+)?)\s*\)",
            flags=re.I,
        )
        for match in bracket.finditer(equation.split("=", 1)[0]):
            coefficient, sign, constant = match.groups()
            if coefficient in ("1", "+1", "-1"):
                continue
            replacement = f"({coefficient}*x{sign}{constant})"
            left_text, right_text = equation.split("=", 1)
            candidate_text = left_text[:match.start()] + replacement + left_text[match.end():]
            try:
                mistaken_left = _expression(candidate_text)
                original_right = _expression(right_text)
            except MathInputError:
                continue
            if (simplify(provided_left - mistaken_left) == 0 and
                    simplify(provided_right - original_right) == 0 and
                    simplify(provided_left - expected_left) != 0):
                return {
                    "code": "incomplete_distribution",
                    "evidence": (f"The submitted expression matches multiplying x by {coefficient} "
                                 f"but leaving the {constant} inside the brackets unchanged."),
                    "hint": "The outside factor applies to BOTH terms inside the brackets. What happens to the number term?",
                }
        if simplify(provided_right - expected_right) != 0:
            return {
                "code": "unexpected_right_side_change",
                "evidence": "The right-hand side changed, although this step only asks you to simplify both sides.",
                "hint": "Check the right-hand side again. Does expanding the left bracket require changing it?",
            }
    if (stage == 1 and simplify(provided_left - expected_left) == 0 and
            simplify(provided_right - expected_right) != 0):
        return {
            "code": "constant_balance_mismatch",
            "evidence": ("The x terms are collected correctly on the left, but the number on "
                         "the right does not preserve equality."),
            "hint": "Which number did you add or subtract on the left? Apply that SAME operation on the right.",
        }
    if stage == 2 and simplify(provided_left - expected_left) == 0 and not provided_right.has(X):
        checked = verify_equation(equation, str(provided_right))
        if checked.is_correct is False:
            return {
                "code": "incorrect_final_value",
                "evidence": (f"Substitution of your proposed value gives left side "
                             f"{checked.substituted_left} and right side {checked.substituted_right}."),
                "hint": "The sides do not balance. Did you divide BOTH sides by the coefficient of x?",
            }
    return None


def check_step(equation: str, stage: int, submitted_equation: str,
               attempt_number: int = 1) -> dict:
    if stage not in (0, 1, 2):
        raise MathInputError("Tutoring step must be 0, 1, or 2.")
    if not 1 <= attempt_number <= 20:
        raise MathInputError("Attempt number must be between 1 and 20.")
    verified = verify_equation(equation)
    if verified.classification != "unique_solution":
        raise MathInputError("Step tutoring supports one-variable linear equations with a unique solution.")
    original_left, original_right = _sides(equation)
    left, right = expand(original_left), expand(original_right)
    a, b = simplify(left.coeff(X)), simplify(left.subs(X, 0))
    c, d = simplify(right.coeff(X)), simplify(right.subs(X, 0))
    targets = ((left, right), (simplify((a - c) * X), simplify(d - b)), (X, _expression(verified.correct_solution, allow_variable=False)))
    provided_left, provided_right = _sides(submitted_equation)
    expected_left, expected_right = targets[stage]

    correct_form = bool(simplify(provided_left - expected_left) == 0 and simplify(provided_right - expected_right) == 0)
    mistake = None
    if correct_form:
        feedback = "Nice work. Both sides are in the requested form and are algebraically correct."
    else:
        # A mathematically equivalent equation may still be the wrong requested stage.
        try:
            candidate = verify_equation(submitted_equation)
            same_answer = candidate.classification == "unique_solution" and candidate.correct_solution == verified.correct_solution
        except MathInputError:
            same_answer = False
        if same_answer:
            feedback = ("That equation has the correct solution, but it isn't in the form requested for this step. "
                        "Try showing the intermediate transformation.")
        else:
            mistake = _detect_mistake(equation, stage, submitted_equation, provided_left,
                                      provided_right, expected_left, expected_right)
            feedback = (mistake["evidence"] if mistake else
                        "Not quite. Check your operations on both sides and try again.")

    complete = correct_form and stage == 2
    reveal = f"{expected_left} = {expected_right}" if correct_form else None
    rationale = (
        "Expanding and combining terms preserves the equation."
        if stage == 0 else
        "The same additions/subtractions on both sides preserve equality."
        if stage == 1 else
        "Dividing both sides by the non-zero coefficient isolates x."
    ) if correct_form else None
    final_check = verify_equation(equation, verified.correct_solution) if complete else None
    support_level = 0 if correct_form else min(attempt_number, 3)
    if correct_form:
        hint = None
    elif support_level == 3:
        hint = SMALL_EXAMPLES[stage]
    elif support_level == 2:
        hint = ((mistake["hint"] if mistake else STEP_HINTS[stage]) +
                " Focus on that one operation, then rewrite your step.")
    else:
        hint = mistake["hint"] if mistake else STEP_HINTS[stage]
    return {
        "stage": stage, "correct": correct_form, "feedback": feedback,
        "hint": hint, "support_level": support_level,
        "support_strategy": ("checked" if correct_form else "gentle_hint" if support_level == 1 else
                             "focused_hint" if support_level == 2 else "smaller_example"),
        "misconception": mistake,
        "revealed_step": reveal, "step_reason": rationale,
        "final_check": f"Substitution verifies both sides equal {final_check.substituted_left}." if final_check else None,
        "next_stage": stage + 1 if correct_form and stage < 2 else None,
        "next_prompt": STEP_PROMPTS[stage + 1] if correct_form and stage < 2 else None,
        "complete": complete,
        "notice": "Checks symbolic equation form, not independently whether the student understands each operation.",
    }
