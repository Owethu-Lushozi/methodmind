from fastapi.testclient import TestClient

from app.main import app
from app.agents.groq_workflow import ProviderUnavailable, _parse_json, _student_answer_evidence, run_groq_learning_cycle
import pytest


def test_gemini_requires_attempt_without_api_call():
    response = TestClient(app).post("/learning/run", json={"equation": "x+2=4", "student_attempt": ""})
    assert response.status_code == 200
    assert response.json()["status"] == "needs_student_attempt"


def test_gemini_rejects_nonunique_without_api_call():
    response = TestClient(app).post("/learning/run", json={"equation": "x=x", "student_attempt": "x=1"})
    assert response.status_code == 422


def test_structured_agent_json_parser():
    assert _parse_json('{"diagnosis":"Needs help","focus":"distribution"}')["focus"] == "distribution"
    assert _parse_json('```json\n{"opening":"Start here"}\n```')["opening"] == "Start here"


def test_invalid_agent_json_is_not_accepted():
    with pytest.raises(ProviderUnavailable):
        _parse_json("This is not JSON")
    with pytest.raises(ProviderUnavailable):
        _parse_json('["not", "an object"]')


def test_explicit_wrong_answer_is_checked_by_sympy():
    evidence = _student_answer_evidence('3(x-2)+5=17', "I tried x=5 but don't know why")
    assert evidence == {'candidate': '5', 'correct': False, 'left': '14', 'right': '17'}


def test_unseen_steps_are_not_diagnosed_as_a_numeric_attempt():
    assert _student_answer_evidence('3(x-2)+5=17', 'I struggle to expand brackets') is None
    assert _student_answer_evidence('3(x-2)+5=17', 'I tried x=5, then x=6') is None


def test_incorrect_answer_cannot_get_unearned_praise(monkeypatch):
    calls = []

    def fake_ask(client, models, prompt, role, events):
        calls.append((role, prompt))
        events.append({'agent': role, 'action': 'live_generate', 'detail': 'test'})
        if role == 'diagnostic':
            return {'diagnosis': 'Numbers are confusing.', 'focus': 'expansion'}
        return {'opening': 'Great job! Expand the brackets.', 'first_step_equation': '3x-1=17'}

    monkeypatch.setattr('app.agents.groq_workflow._client', lambda: object())
    monkeypatch.setattr('app.agents.groq_workflow._models', lambda: ['test'])
    monkeypatch.setattr('app.agents.groq_workflow._ask', fake_ask)
    result = run_groq_learning_cycle('3(x-2)+5=17', 'I tried x=5')
    assert 'left side is 14' in result['diagnosis']
    assert 'right side is 17' in result['diagnosis']
    assert "we'd need your working" in result['diagnosis']
    assert 'Great job' not in result['explanation']
    assert 'candidate_is_correct=False' in calls[0][1]
    assert any(e['action'] == 'check_student_answer' for e in result['events'])
