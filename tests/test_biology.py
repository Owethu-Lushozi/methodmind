"""Life Sciences specialist supports the shared 3-2-2 pathway."""

from fastapi.testclient import TestClient

from app.main import app
from app.learning.biology import TOPIC_ID
from app.learning.subjects import get_subject


def test_biology_contract_and_misconception():
    biology = get_subject("biology")
    assert biology.identify_concept(TOPIC_ID)["concept_id"] == TOPIC_ID
    wrong = biology.evaluate_response("guided_practice", stage=1, choice=0)
    assert not wrong["correct"]
    assert wrong["misconception"]["code"] == "assumes_unlimited_light_effect"
    assert "limit" in biology.get_learning_objective(TOPIC_ID)


def test_biology_full_path_and_guardrails():
    c = TestClient(app)
    assert any(s["id"] == "biology" for s in c.get("/learning/subjects").json()["subjects"])
    created = c.post("/learning/session", json={"subject": "biology", "problem": TOPIC_ID})
    assert created.status_code == 200
    sid = created.json()["session_id"]

    # A correctly chosen answer without a causal explanation cannot pass transfer.
    for activity, choices in (("guided_practice", (0, 1, 0)), ("concept_check", (0, 1))):
        for stage, choice in enumerate(choices):
            response = c.post("/learning/biology/check", json={
                "session_id": sid, "activity": activity, "stage": stage, "choice": choice})
            assert response.status_code == 200, response.text
            assert response.json()["correct"]
    no_explanation = c.post("/learning/biology/check", json={
        "session_id": sid, "activity": "transfer", "stage": 0, "choice": 0})
    assert not no_explanation.json()["correct"]
    for stage, choice, reasoning in (
        (0, 0, "Carbon dioxide availability limited plant A because less CO2 was available for photosynthesis."),
        (1, 1, "More light cannot always increase the rate because another factor can become limiting at the plateau."),
    ):
        response = c.post("/learning/biology/check", json={"session_id": sid,
            "activity": "transfer", "stage": stage, "choice": choice, "reasoning": reasoning})
        assert response.status_code == 200 and response.json()["correct"], response.text
    assert response.json()["learning_session"]["state"] == "reflect"
