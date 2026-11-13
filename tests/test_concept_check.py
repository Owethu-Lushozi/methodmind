from fastapi.testclient import TestClient

from app.concept_check import check_concept, get_concept_question
from app.main import app


def test_concept_questions_have_three_choices_without_answer_key():
    for stage in (0, 1):
        item = get_concept_question(stage)
        assert len(item["choices"]) == 3
        assert "answer" not in item


def test_concept_mistakes_receive_specific_feedback_and_do_not_advance():
    first = check_concept(0, 1)
    assert first["correct"] is False
    assert first["next_stage"] is None
    assert "constant" in first["feedback"]
    second = check_concept(1, 2)
    assert not second["correct"]
    assert "Both sides" in second["feedback"]


def test_concept_questions_advance_only_on_correct_choice():
    first = check_concept(0, 0)
    assert first["correct"] is True
    assert first["next_stage"] == 1
    assert first["complete"] is False
    second = check_concept(1, 1)
    assert second["correct"] is True
    assert second["complete"] is True
    assert second["next_stage"] is None


def test_concept_endpoints():
    client = TestClient(app)
    assert client.get('/learning/concept/0').status_code == 200
    assert client.get('/learning/concept/2').status_code == 422
    assert client.post('/learning/concept', json={"stage": 0, "choice": 1}).json()["correct"] is False
    assert client.post('/learning/concept', json={"stage": 0, "choice": 0}).json()["next_stage"] == 1
    assert client.post('/learning/concept', json={"stage": 2, "choice": 0}).status_code == 422
