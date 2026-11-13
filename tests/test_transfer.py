from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_first_transfer_correct_advances():
    data = client.post('/learning/transfer', json={'stage': 0, 'proposed_answer': '5',
        'reasoning': 'I expanded the brackets, then added and divided both sides to preserve equality.'}).json()
    assert data['correct'] is True
    assert data['next_stage'] == 1
    assert data['reasoning_assessed'] is True


def test_wrong_answer_gets_hint_without_solution():
    data = client.post('/learning/transfer', json={'stage': 0, 'proposed_answer': '4'}).json()
    assert data['correct'] is False
    assert data['hint']
    assert 'unique solution' not in data['feedback']


def test_second_transfer_can_finish():
    data = client.post('/learning/transfer', json={'stage': 1, 'proposed_answer': '3',
        'reasoning': 'I added three to both sides, then divided both sides by five to keep them equal.'}).json()
    assert data['practice_complete'] is True
    assert data['reasoning_status'] == 'supported'


def test_correct_answer_without_reasoning_does_not_unlock_next_question():
    data = client.post('/learning/transfer', json={'stage': 0, 'proposed_answer': '5'}).json()
    assert data['answer_correct'] is True
    assert data['correct'] is False
    assert data['next_stage'] is None
    assert data['reasoning_status'] == 'needs_detail'


def test_one_sided_explanation_is_flagged():
    data = client.post('/learning/transfer', json={'stage': 0, 'proposed_answer': '5',
        'reasoning': 'I added four to the left side only and divided by four.'}).json()
    assert data['correct'] is False
    assert data['reasoning_status'] == 'misconception'


def test_invalid_numeric_input_returns_422():
    assert client.post('/learning/transfer', json={'stage': 0, 'proposed_answer': 'hello'}).status_code == 422
