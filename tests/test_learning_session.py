"""Milestone 16: real evidence tracking without premature mastery claims."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_session_progression_and_adaptation():
    client = TestClient(app)
    start = client.post("/learning/session", json={"problem": "3(x-2)+5=17"})
    assert start.status_code == 200
    session_id = start.json()["session_id"]
    def step(stage, equation):
        response = client.post("/learning/step", json={
            "session_id": session_id, "equation": "3(x-2)+5=17",
            "stage": stage, "submitted_equation": equation,
            "coaching_mode": "coach"})
        assert response.status_code == 200
        return response.json()

    for _ in range(2):
        incorrect = step(0, "3x-2+5=17")
    assert incorrect["learning_session"]["next_action"] == "teach_smaller_example"
    assert incorrect["learning_session"]["evidence"]["misconceptions"]["incomplete_distribution"] == 2
    assert step(0, "3x-1=17")["correct"]
    assert step(1, "3x=18")["correct"]
    completed = step(2, "x=6")
    assert completed["learning_session"]["state"] == "concept_check"

    for stage, choice in ((0, 0), (1, 1)):
        response = client.post("/learning/concept", json={
            "session_id": session_id, "stage": stage, "choice": choice})
        assert response.status_code == 200 and response.json()["correct"]
    assert response.json()["learning_session"]["state"] == "transfer"

    for stage, answer in ((0, "5"), (1, "3")):
        response = client.post("/learning/transfer", json={"session_id": session_id,
            "stage": stage, "proposed_answer": answer,
            "reasoning": "I used subtraction and division on both sides to preserve equality.",
            "coaching_mode": "coach"})
        assert response.status_code == 200, response.text
        assert response.json()["correct"]
    assert response.json()["learning_session"]["state"] == "reflect"
    assert "not prove mastery" in client.get(f"/learning/session/{session_id}").json()["notice"]


def test_session_security_and_legacy_routes():
    client = TestClient(app)
    assert client.get("/learning/session/not-a-session").status_code == 404
    a = client.post("/learning/session", json={"problem": "3(x-2)+5=17"}).json()["session_id"]
    mismatch = client.post("/learning/step", json={"session_id": a,
        "equation": "2(x+3)=14", "stage": 0, "submitted_equation": "2x+6=14"})
    assert mismatch.status_code == 422
    skipped = client.post("/learning/step", json={"session_id": a,
        "equation": "3(x-2)+5=17", "stage": 2, "submitted_equation": "x=6"})
    assert skipped.status_code == 422
    legacy = client.post("/learning/step", json={"equation": "3(x-2)+5=17",
        "stage": 0, "submitted_equation": "3x-1=17"})
    assert legacy.status_code == 200 and legacy.json()["correct"]
