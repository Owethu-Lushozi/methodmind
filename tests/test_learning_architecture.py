"""Reusable subject interface and backward-compatible routing."""

import pytest
from fastapi.testclient import TestClient

from app.learning.contracts import LearningState, SubjectSpecialist
from app.learning.subjects import get_subject, list_subjects
from app.learning.orchestrator import evaluate_step, evaluate_concept, evaluate_transfer
from app.main import app


def test_subject_contract_and_registry():
    algebra = get_subject("algebra")
    assert isinstance(algebra, SubjectSpecialist)
    assert {item["id"] for item in list_subjects()} == {"algebra", "biology"}
    assert len(LearningState) == 7
    with pytest.raises(ValueError, match="Unsupported subject"):
        get_subject("chemistry")


def test_subject_reuses_verified_math_engine():
    algebra = get_subject("algebra")
    assert algebra.identify_concept("3(x-2)+5=17")["classification"] == "unique_solution"
    assert algebra.generate_activity("guided_practice", 0)["stage"] == 0
    assert algebra.generate_transfer(0)["equation"] == "4(x-1)+2=18"


def test_orchestration_maintains_feedback_and_gate():
    wrong = evaluate_step("algebra", "3(x-2)+5=17", 0, "3x-2+5=17", "coach", 3)
    assert not wrong["correct"]
    assert wrong["support_strategy"] == "smaller_example"
    assert wrong["hint_source"] == "symbolic"
    correct = evaluate_step("algebra", "3(x-2)+5=17", 0, "3x-1=17")
    assert correct["correct"] and correct["next_stage"] == 1
    assert evaluate_concept("algebra", 0, 0)["correct"]
    answer_only = evaluate_transfer("algebra", 0, "5", "")
    assert answer_only["answer_correct"] and not answer_only["correct"]


def test_existing_http_routes_still_work():
    client = TestClient(app)
    response = client.get("/learning/subjects")
    assert response.status_code == 200
    assert response.json()["default_subject"] == "algebra"
    response = client.post("/learning/step", json={
        "equation": "3(x-2)+5=17", "stage": 0,
        "submitted_equation": "3x-1=17", "coaching_mode": "coach"})
    assert response.status_code == 200 and response.json()["correct"]
