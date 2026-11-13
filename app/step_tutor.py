"""Stateless three-stage equation practice with symbolic form checking."""

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


def _sides(equation: str):
    if equation.count("=") != 1:
        raise MathInputError("Write an equation with exactly one equals sign.")
    left, right = equation.split("=", 1)
    return _expression(left), _expression(right)


def check_step(equation: str, stage: int, submitted_equation: str) -> dict:
    if stage not in (0, 1, 2):
        raise MathInputError("Tutoring step must be 0, 1, or 2.")
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
    if correct_form:
        feedback = "Nice work. Both sides are in the requested form and are algebraically correct."
    else:
        # A mathematically equivalent equation may still be the wrong requested stage.
        try:
            candidate = verify_equation(submitted_equation)
            same_answer = candidate.classification == "unique_solution" and candidate.correct_solution == verified.correct_solution
        except MathInputError:
            same_answer = False
        feedback = ("That equation has the correct solution, but it isn't in the form requested for this step. "
                    "Try showing the intermediate transformation." if same_answer else
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
    return {
        "stage": stage, "correct": correct_form, "feedback": feedback,
        "hint": None if correct_form else STEP_HINTS[stage],
        "revealed_step": reveal, "step_reason": rationale,
        "final_check": f"Substitution verifies both sides equal {final_check.substituted_left}." if final_check else None,
        "next_stage": stage + 1 if correct_form and stage < 2 else None,
        "next_prompt": STEP_PROMPTS[stage + 1] if correct_form and stage < 2 else None,
        "complete": complete,
        "notice": "Checks symbolic equation form, not independently whether the student understands each operation.",
    }
