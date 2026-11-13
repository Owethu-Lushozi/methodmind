from app.learning.conversation import _stage_suggestions


def test_exercise_overrides_stale_model_suggestions():
    actual = _stage_suggestions("I'm ready to try one myself", "Great! Try solving 3x - 4 = 11. What is x?", "Linear equations", ["I need a simple example", "I'm ready to try one myself"])
    assert "Can you give me a hint?" in actual
    assert "I'm ready to try one myself" not in actual


def test_quadratic_exercise_is_stage_aware():
    actual = _stage_suggestions("Give me a quadratic", "Your turn: solve this equation: x² - 5x + 6 = 0", "Quadratic equations", [])
    assert "Explain the first step" in actual


def test_non_exercise_keeps_model_suggestions():
    actual = _stage_suggestions("Explain factoring", "Factoring rewrites a polynomial as a product.", "Quadratic equations", ["I want to see another example"])
    assert actual == ["I want to see another example"]


def test_answer_prompts_reflection():
    actual = _stage_suggestions("I got x=5", "Thanks for your answer.", "Linear equations", [])
    assert "Can you check my reasoning?" in actual


def test_exercise_worded_for_you_to_solve_overrides_stale_suggestions():
    actual = _stage_suggestions(
        "Give me a linear equation to try.",
        "Here's a simple linear equation for you to solve: 3x + 5 = 20.",
        "Linear equations",
        ["I need a simple example", "I'm ready to try one myself"],
    )
    assert actual == ["I want to try answering", "Can you give me a hint?", "Explain the first step"]
