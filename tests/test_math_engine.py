import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.math_engine import MathInputError, verify_equation


def test_detects_incorrect_answer():
    result = verify_equation("3(x-2)+5=17", "5")
    assert result.classification == "unique_solution"
    assert result.correct_solution == "6"
    assert result.is_correct is False
    assert (result.substituted_left, result.substituted_right) == ("14", "17")


@pytest.mark.parametrize("equation,answer", [
    ("2x+6=14", "4"),
    ("3(x-2)+5=17", "6"),
    ("-2x+8=0", "4"),
    ("x/2+1=3", "4"),
    ("0.5x=1.25", "5/2"),
])
def test_valid_answers(equation, answer):
    assert verify_equation(equation, answer).is_correct is True


def test_no_solution():
    result = verify_equation("2x+1=2x+3", "2")
    assert result.classification == "no_solution"
    assert result.correct_solution is None
    assert result.is_correct is False


def test_infinite_solutions():
    result = verify_equation("2(x+1)=2x+2", "3")
    assert result.classification == "all_real_numbers"
    assert result.correct_solution is None
    assert result.is_correct is True  # Every real value works, but there is no unique solution.


@pytest.mark.parametrize("equation", [
    "x**2=4", "x^2=4", "x/0=2", "x/(x+1)=2", "sin(x)=0",
    "__import__('os')=1", "x+1", "x+y=2", "x*x=4", "x=",
])
def test_rejects_unsupported_input(equation):
    with pytest.raises(MathInputError):
        verify_equation(equation)


def test_endpoint_returns_structured_verification():
    response = TestClient(app).post("/math/verify", json={
        "equation": "3(x-2)+5=17", "proposed_answer": "5"
    })
    assert response.status_code == 200
    assert response.json()["is_correct"] is False
    assert response.json()["correct_solution"] == "6"


def test_endpoint_rejects_unsupported():
    response = TestClient(app).post("/math/verify", json={"equation": "x**2=4"})
    assert response.status_code == 422
