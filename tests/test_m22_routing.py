from app.learning.conversation import _practice_offer


def history(message):
    return [{'role': 'user', 'text': message}]


def test_linear_practice_is_offered():
    assert _practice_offer('Mathematics', 'Linear equations', history('Help me solve an equation'))['subject_id'] == 'algebra'


def test_quadratic_is_not_misrouted():
    assert _practice_offer('Mathematics', 'Quadratic equations', history('Help me solve an equation x^2-5x+6=0')) is None


def test_calculus_is_not_misrouted():
    assert _practice_offer('Mathematics', 'Calculus', history('Help me solve an equation using derivatives')) is None


def test_photosynthesis_still_offered():
    assert _practice_offer('Life Sciences', 'Photosynthesis', history('I struggle with photosynthesis'))['subject_id'] == 'biology'
