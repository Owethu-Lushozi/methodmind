from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def coach(equation, attempt):
    return client.post('/learning/coach', json={'equation': equation, 'student_attempt': attempt})


def test_symbolic_steps_and_transfer_question():
    data = coach('3(x-2)+5=17', 'I tried x=5').json()
    assert data['status'] == 'verified'
    assert data['verified_answer'] is None
    assert 'x = 6' not in data['explanation']
    assert 'simplifying' in data['explanation']
    assert data['transfer_question'] == '4(x-1)+2=18'


def test_different_wrong_answers_different_feedback():
    first = coach('3(x-2)+5=17', 'I tried x=2').json()['diagnosis']
    second = coach('3(x-2)+5=17', 'I tried x=5').json()['diagnosis']
    assert first != second
    assert 'left side 5' in first
    assert 'left side 14' in second


def test_distribution_mention_gets_targeted_guidance():
    data = coach('3(x-2)+5=17', 'I am stuck distributing the bracket').json()
    assert 'BOTH terms' in data['explanation']


def test_correct_answer_acknowledged():
    data = coach('2(x+3)=14', 'x=4').json()
    assert 'satisfies' in data['diagnosis']


def test_unsupported_equation_rejected():
    assert coach('x^2=4', 'x=2').status_code == 422
