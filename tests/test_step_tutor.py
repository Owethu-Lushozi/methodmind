from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def step(stage, supplied, equation='3(x-2)+5=17'):
    return client.post('/learning/step', json={'equation': equation, 'stage': stage, 'submitted_equation': supplied})


def test_accurate_three_stage_solution():
    first = step(0, '3x-1=17').json()
    assert first['correct'] and first['next_stage'] == 1
    assert first['revealed_step'] == '3*x - 1 = 17'
    second = step(1, '3x=18').json()
    assert second['correct'] and second['next_stage'] == 2
    third = step(2, 'x=6').json()
    assert third['correct'] and third['complete']
    assert third['revealed_step'] == 'x = 6'
    assert 'Substitution verifies' in third['final_check']


def test_wrong_step_has_hint():
    result = step(1, '3x=17').json()
    assert not result['correct']
    assert result['hint']
    assert result['revealed_step'] is None


def test_early_final_answer_is_not_accepted_as_intermediate_step():
    result = step(0, 'x=6').json()
    assert not result['correct']
    assert 'correct solution' in result['feedback']


def test_invalid_equation_rejected():
    assert step(1, 'hello').status_code == 422


def test_different_equation():
    assert step(0, '2x+6=14', '2(x+3)=14').json()['correct']
