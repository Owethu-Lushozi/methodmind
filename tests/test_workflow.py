from fastapi.testclient import TestClient

from app.agents.workflow import run_mock_learning_cycle
from app.main import app


def test_mock_cycle_shows_review_and_correction():
    result = run_mock_learning_cycle("3(x-2)+5=17", "I got x=5")
    assert result["mode"] == "mock"
    assert result["status"] == "verified"
    assert result["verified_answer"] == "6"
    assert result["revision_count"] == 1
    assert [event["agent"] for event in result["events"]] == [
        "diagnostic", "teaching", "reviewer", "orchestrator", "teaching", "reviewer"
    ]
    assert "simulated" in result["disclaimer"].lower()


def test_missing_attempt_asks_question():
    result = run_mock_learning_cycle("2x+6=14", "")
    assert result["status"] == "needs_student_attempt"


def test_demo_endpoint():
    response = TestClient(app).post("/learning/demo", json={
        "equation": "3(x-2)+5=17", "student_attempt": "x=5"
    })
    assert response.status_code == 200
    assert response.json()["revision_count"] == 1


def test_rejects_non_unique_equation():
    response = TestClient(app).post("/learning/demo", json={
        "equation": "x+1=x+1", "student_attempt": "x=1"
    })
    assert response.status_code == 422
