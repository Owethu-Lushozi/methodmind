from fastapi.testclient import TestClient
from app.main import app
from app.agents.groq_workflow import ProviderUnavailable

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
    assert result['misconception']['code'] == 'constant_balance_mismatch'


def test_incomplete_distribution_has_verified_specific_feedback():
    result = step(0, '3x-2+5=17').json()
    assert result['misconception']['code'] == 'incomplete_distribution'
    assert 'leaving the 2' in result['feedback']
    assert 'BOTH terms' in result['hint']
    assert result['revealed_step'] is None


def test_wrong_final_value_uses_substitution_without_revealing_solution():
    result = step(2, 'x=4').json()
    assert result['misconception']['code'] == 'incorrect_final_value'
    assert 'left side 11' in result['feedback']
    assert 'right side 17' in result['feedback']
    assert result['revealed_step'] is None


def test_unrecognized_error_does_not_invent_misconception():
    result = step(0, '2x+9=17').json()
    assert not result['correct']
    assert result['misconception'] is None


def test_repeated_attempts_progress_from_hint_to_smaller_example():
    payload = {'equation': '3(x-2)+5=17', 'stage': 0,
               'submitted_equation': '3x-2+5=17', 'coaching_mode': 'coach'}
    first = client.post('/learning/step', json={**payload, 'attempt_number': 1}).json()
    second = client.post('/learning/step', json={**payload, 'attempt_number': 2}).json()
    third = client.post('/learning/step', json={**payload, 'attempt_number': 3}).json()
    assert first['support_strategy'] == 'gentle_hint'
    assert second['support_strategy'] == 'focused_hint'
    assert third['support_strategy'] == 'smaller_example'
    assert '2(y-4)' in third['hint']
    assert all(result['revealed_step'] is None for result in (first, second, third))


def test_correct_attempt_is_checked_regardless_of_attempt_number():
    result = client.post('/learning/step', json={
        'equation': '3(x-2)+5=17', 'stage': 0,
        'submitted_equation': '3x-1=17', 'attempt_number': 4,
    }).json()
    assert result['correct'] and result['support_strategy'] == 'checked'


def test_repeated_groq_attempt_does_not_make_extra_model_call(monkeypatch):
    def unexpected(*args):
        raise AssertionError('Repeated attempts must use the verified scaffold')
    monkeypatch.setattr('app.learning.orchestrator.generate_adaptive_step_hint', unexpected)
    response = client.post('/learning/step', json={
        'equation': '3(x-2)+5=17', 'stage': 0,
        'submitted_equation': '3x-2+5=17', 'coaching_mode': 'groq',
        'attempt_number': 3,
    })
    assert response.status_code == 200
    assert response.json()['hint_source'] == 'adaptive_scaffold'


def test_early_final_answer_is_not_accepted_as_intermediate_step():
    result = step(0, 'x=6').json()
    assert not result['correct']
    assert 'correct solution' in result['feedback']


def test_invalid_equation_rejected():
    assert step(1, 'hello').status_code == 422


def test_different_equation():
    assert step(0, '2x+6=14', '2(x+3)=14').json()['correct']


def test_live_ai_hint_for_wrong_step(monkeypatch):
    def fake_hint(equation, stage, submitted_equation, symbolic_feedback, fallback_hint):
        assert stage == 0
        assert submitted_equation == '3x-2+5=17'
        return 'You multiplied the first term inside the brackets. What happens to the second term?'

    monkeypatch.setattr('app.learning.orchestrator.generate_adaptive_step_hint', fake_hint)
    response = client.post('/learning/step', json={
        'equation': '3(x-2)+5=17', 'stage': 0,
        'submitted_equation': '3x-2+5=17', 'coaching_mode': 'groq',
    })
    result = response.json()
    assert response.status_code == 200
    assert not result['correct']
    assert result['hint_source'] == 'live_ai'
    assert 'second term' in result['hint']
    assert result['revealed_step'] is None


def test_live_ai_unavailable_falls_back_to_symbolic_hint(monkeypatch):
    def unavailable(*args):
        raise ProviderUnavailable('Model busy')

    monkeypatch.setattr('app.learning.orchestrator.generate_adaptive_step_hint', unavailable)
    response = client.post('/learning/step', json={
        'equation': '3(x-2)+5=17', 'stage': 0,
        'submitted_equation': '3x-2+5=17', 'coaching_mode': 'groq',
    })
    assert response.status_code == 200
    assert response.json()['hint_source'] == 'symbolic_fallback'
    assert response.json()['hint']


def test_correct_live_step_does_not_spend_ai_request(monkeypatch):
    def unexpected(*args):
        raise AssertionError('No AI call should be made for correct work')

    monkeypatch.setattr('app.learning.orchestrator.generate_adaptive_step_hint', unexpected)
    response = client.post('/learning/step', json={
        'equation': '3(x-2)+5=17', 'stage': 0,
        'submitted_equation': '3x-1=17', 'coaching_mode': 'groq',
    })
    assert response.status_code == 200
    assert response.json()['correct']
    assert response.json()['hint_source'] is None
