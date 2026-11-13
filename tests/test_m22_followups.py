from app.learning.conversation import _topic_suggestions


def test_quadratic_followups_when_model_omits_them():
    choices = _topic_suggestions('Can you explain quadratic equations?', 'Quadratic equations', [])
    assert len(choices) == 3
    assert 'quadratic' in choices[0].lower()


def test_calculus_followups_when_model_omits_them():
    choices = _topic_suggestions('I am struggling with the chain rule', 'Calculus', [])
    assert len(choices) == 3
    assert 'chain rule' in choices[0].lower()


def test_keep_valid_model_followups():
    assert _topic_suggestions('integration', 'Calculus', ['How do I start?']) == ['How do I start?']
