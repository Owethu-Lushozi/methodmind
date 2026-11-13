from fastapi.testclient import TestClient

from app.main import app


def test_gemini_requires_attempt_without_api_call():
    response = TestClient(app).post("/learning/run", json={"equation": "x+2=4", "student_attempt": ""})
    assert response.status_code == 200
    assert response.json()["status"] == "needs_student_attempt"


def test_gemini_rejects_nonunique_without_api_call():
    response = TestClient(app).post("/learning/run", json={"equation": "x=x", "student_attempt": "x=1"})
    assert response.status_code == 422
