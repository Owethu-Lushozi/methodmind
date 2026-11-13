from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_first_transfer_correct_advances():
    data = client.post('/learning/transfer', json={'stage': 0, 'proposed_answer': '5'}).json()
    assert data['correct'] is True
    assert data['next_stage'] == 1
    assert data['reasoning_assessed'] is False


def test_wrong_answer_gets_hint_without_solution():
    data = client.post('/learning/transfer', json={'stage': 0, 'proposed_answer': '4'}).json()
    assert data['correct'] is False
    assert data['hint']
    assert 'unique solution' not in data['feedback']


def test_second_transfer_can_finish():
    data = client.post('/learning/transfer', json={'stage': 1, 'proposed_answer': '3', 'reasoning': 'Undo -3 then divide by 5'}).json()
    assert data['practice_complete'] is True
    assert data['reasoning_assessed'] is False


def test_invalid_numeric_input_returns_422():
    assert client.post('/learning/transfer', json={'stage': 0, 'proposed_answer': 'hello'}).status_code == 422
