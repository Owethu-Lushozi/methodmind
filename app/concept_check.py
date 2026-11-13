"""Short, deterministic checks of mathematical rules, not claims of mastery."""

QUESTIONS = (
    {
        "question": "Why does 3(x − 2) become 3x − 6?",
        "choices": [
            "The 3 multiplies both x and −2.",
            "The 3 multiplies x only.",
            "Subtract 2 from 3 first.",
        ],
        "answer": 0,
        "hints": (
            "Correct: the distributive property applies the outside factor to every term.",
            "That would leave the constant unchanged. Try multiplying 3 by −2 as well.",
            "The 2 is inside the brackets; distribute the 3 to both terms first.",
        ),
    },
    {
        "question": "When solving 3x − 1 = 17, why can we add 1 to both sides?",
        "choices": [
            "Because moving a number always changes its sign.",
            "Because doing the same operation to both sides preserves equality.",
            "Because we should add 1 to the left side only.",
        ],
        "answer": 1,
        "hints": (
            "Changing a sign is a shortcut, not the reason. What happens when both sides receive the same addition?",
            "Correct: applying the same operation on both sides maintains the balance.",
            "Adding only to the left changes the balance. Both sides need the same operation.",
        ),
    },
)


def get_concept_question(stage: int) -> dict:
    if stage not in range(len(QUESTIONS)):
        raise ValueError("Concept stage must be 0 or 1.")
    item = QUESTIONS[stage]
    return {"stage": stage, "question": item["question"], "choices": item["choices"]}


def check_concept(stage: int, choice: int) -> dict:
    item = get_concept_question(stage)
    if choice not in range(len(item["choices"])):
        raise ValueError("Choose one of the available answers.")
    question = QUESTIONS[stage]
    correct = choice == question["answer"]
    return {
        "correct": correct,
        "feedback": question["hints"][choice],
        "next_stage": stage + 1 if correct and stage + 1 < len(QUESTIONS) else None,
        "complete": correct and stage == len(QUESTIONS) - 1,
        "notice": "This checks recognition of two rules, not independent conceptual mastery.",
    }
