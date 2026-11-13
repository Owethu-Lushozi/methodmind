"""Strict, deterministic verification for single-variable linear equations.

This deliberately does not use sympy.sympify or parse_expr on user text.
Only numbers, x, +, -, *, / and parentheses are accepted.
"""

import ast
import re
from dataclasses import dataclass

from sympy import Poly, Rational, Symbol, cancel, expand, simplify


X = Symbol("x")
MAX_LENGTH = 120
MAX_TOKENS = 80
MAX_DEPTH = 18
TOKEN = re.compile(r"\d+(?:\.\d+)?|x|[()+\-*/]")


class MathInputError(ValueError):
    """Unsupported or invalid mathematics input."""


@dataclass(frozen=True)
class Verification:
    equation: str
    classification: str
    correct_solution: str | None
    proposed_answer: str | None
    is_correct: bool | None
    substituted_left: str | None
    substituted_right: str | None
    explanation: str


def _tokens(value: str) -> list[str]:
    text = re.sub(r"\s+", "", value.lower()).replace("×", "*").replace("÷", "/")
    if not text or len(text) > MAX_LENGTH:
        raise MathInputError("Expression is empty or too long (maximum 120 characters).")
    tokens = TOKEN.findall(text)
    if "".join(tokens) != text or len(tokens) > MAX_TOKENS:
        raise MathInputError("Use numbers, x, +, -, *, / and parentheses only.")
    return tokens


def _expression(value: str, allow_variable: bool = True):
    tokens = _tokens(value)
    augmented: list[str] = []
    for i, token in enumerate(tokens):
        if i:
            prev = tokens[i - 1]
            ends_factor = prev == "x" or prev == ")" or prev[0].isdigit()
            starts_factor = token == "x" or token == "(" or token[0].isdigit()
            if ends_factor and starts_factor:
                # Reject adjacent numeric literals (e.g. "2 3") rather than guessing.
                if prev[0].isdigit() and token[0].isdigit():
                    raise MathInputError("Separate numbers with an operator.")
                augmented.append("*")
        augmented.append(token)
    try:
        tree = ast.parse("".join(augmented), mode="eval")
    except SyntaxError as exc:
        raise MathInputError("Expression syntax is invalid.") from exc

    def walk(node, depth=0):
        if depth > MAX_DEPTH:
            raise MathInputError("Expression is too deeply nested.")
        if isinstance(node, ast.Expression):
            return walk(node.body, depth + 1)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return Rational(str(node.value))
        if isinstance(node, ast.Name) and node.id == "x" and allow_variable:
            return X
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            result = walk(node.operand, depth + 1)
            return result if isinstance(node.op, ast.UAdd) else -result
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            left, right = walk(node.left, depth + 1), walk(node.right, depth + 1)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if right.has(X) or right == 0:
                raise MathInputError("Division by a variable or zero is unsupported.")
            return left / right
        raise MathInputError("Unsupported operation or variable.")

    return walk(tree)


def verify_equation(equation: str, proposed_answer: str | None = None) -> Verification:
    """Solve and check one real linear equation in x.

    A proposed answer must be a numeric expression, e.g. '5' or '7/2'.
    """
    if equation.count("=") != 1:
        raise MathInputError("Enter one equation with exactly one equals sign.")
    left_text, right_text = equation.split("=", 1)
    lhs, rhs = _expression(left_text), _expression(right_text)
    difference = cancel(lhs - rhs)
    try:
        poly = Poly(expand(difference), X)
    except Exception as exc:
        raise MathInputError("Only linear equations in x are supported.") from exc
    if poly.degree() > 1:
        raise MathInputError("Only linear equations in x are supported.")

    coefficient = poly.coeff_monomial(X)
    constant = poly.coeff_monomial(1)
    if coefficient == 0:
        classification = "all_real_numbers" if constant == 0 else "no_solution"
        solution = None
    else:
        classification = "unique_solution"
        solution = simplify(-constant / coefficient)

    if proposed_answer is None or not proposed_answer.strip():
        return Verification(equation, classification, str(solution) if solution is not None else None,
                            None, None, None, None, "Equation classified; no answer submitted for checking.")
    guess = _expression(proposed_answer, allow_variable=False)
    if guess.has(X):
        raise MathInputError("The proposed answer must be numeric.")
    left_value = simplify(lhs.subs(X, guess))
    right_value = simplify(rhs.subs(X, guess))
    correct = bool(simplify(left_value - right_value) == 0)
    if classification == "all_real_numbers":
        explanation = "Every real number satisfies the equation; there is no unique x."
    elif classification == "no_solution":
        explanation = "No value of x satisfies both sides of the equation."
    elif correct:
        explanation = "The proposed answer satisfies the equation and is the unique solution."
    else:
        explanation = f"The proposed value gives left side {left_value} and right side {right_value}; the unique solution is {solution}."
    return Verification(equation, classification, str(solution) if solution is not None else None,
                        str(guess), correct, str(left_value), str(right_value), explanation)
