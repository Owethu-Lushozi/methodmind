"""Curated Life Sciences specialist: photosynthesis limiting factors.

Checks recognition and reasoning against explicit rubrics, not biological proof.
"""

import re
from typing import Any


TOPIC_ID = "photosynthesis_limiting_factors"

GUIDED = (
    {"question": "A plant gets more light, and its photosynthesis rate rises. Which factor was limiting at first?",
     "choices": ["Light intensity", "Soil colour", "Leaf shape"], "answer": 0,
     "why": "More light increased the rate, so light was limiting in this situation.",
     "hint": "Look at the variable that changed and the rate that responded.", "code": "confuses_limiting_factor"},
    {"question": "Light intensity increases further, but the rate stops rising. What is the best explanation?",
     "choices": ["Photosynthesis always stops in bright light", "Another factor, such as carbon dioxide, may now limit the rate", "Light is no longer needed"],
     "answer": 1, "why": "Once enough light is available, a different factor can cap the rate.",
     "hint": "A plateau does not mean light becomes irrelevant; what else does photosynthesis need?",
     "code": "assumes_unlimited_light_effect"},
    {"question": "At constant light and temperature, adding carbon dioxide raises photosynthesis. What does that suggest?",
     "choices": ["Carbon dioxide was limiting", "Water is never required", "Temperature must have risen"],
     "answer": 0, "why": "Increasing carbon dioxide increased the rate while the other conditions stayed fixed.",
     "hint": "Only one factor was changed. What does the resulting increase tell you?",
     "code": "misreads_controlled_variables"},
)

CONCEPTS = (
    {"question": "Why can adding more light eventually stop increasing the rate of photosynthesis?",
     "choices": ["Another required factor may become limiting", "Light has no role in photosynthesis", "Every plant has exactly the same maximum rate"],
     "answer": 0, "why": "The slowest available requirement can constrain the rate.",
     "hint": "Think about what happens when one ingredient is abundant but another is scarce.",
     "code": "single_factor_thinking"},
    {"question": "Why should we keep temperature constant when investigating the effect of light intensity?",
     "choices": ["To make photosynthesis happen without carbon dioxide", "To isolate light's effect from temperature's effect", "Because temperature never influences photosynthesis"],
     "answer": 1, "why": "Controlling other variables makes an observed change easier to attribute to light.",
     "hint": "What would be difficult to conclude if two variables changed together?",
     "code": "confuses_experimental_controls"},
)

TRANSFER = (
    {"question": "Two identical plants get equal light and water. Plant A has low CO₂ and B has more CO₂. B photosynthesises faster. What best explains the difference?",
     "choices": ["CO₂ availability limited A", "B must be receiving more light", "CO₂ does not affect photosynthesis"],
     "answer": 0, "why": "Carbon dioxide was the changed variable, so its availability explains the observed difference.",
     "hint": "Which condition actually differed between these plants?",
     "code": "ignores_variable_comparison",
     "reasoning_terms": ("carbon", "co2", "carbon dioxide"),
     "reasoning_cause": ("limit", "less", "more", "increase", "scarce", "available")},
    {"question": "A graph of photosynthesis against light rises, then levels off. A student says stronger light will ALWAYS increase the rate. Choose the best response.",
     "choices": ["Agree: light alone controls the rate", "Disagree: another factor may limit the rate at the plateau", "Agree: the graph must be wrong"],
     "answer": 1, "why": "The plateau means extra light did not increase the observed rate under these conditions.",
     "hint": "Use the flat portion of the graph as evidence.",
     "code": "ignores_rate_plateau",
     "reasoning_terms": ("light", "plateau", "level", "flat"),
     "reasoning_cause": ("limit", "carbon", "co2", "temperature", "another", "other", "saturat")},
)


class BiologySpecialist:
    subject_id = "biology"
    display_name = "Life Sciences · Photosynthesis"

    def identify_concept(self, problem: str, student_attempt: str = "") -> dict[str, Any]:
        if problem != TOPIC_ID:
            raise ValueError("Choose the supported photosynthesis topic.")
        return {"concept_id": TOPIC_ID, "student_evidence": student_attempt.strip(),
                "verification_source": "curated_rubric", "classification": "conceptual_topic"}

    def get_learning_objective(self, concept_id: str) -> str:
        if concept_id != TOPIC_ID:
            raise ValueError("Unknown Life Sciences concept.")
        return "Explain how light, carbon dioxide and other factors limit photosynthesis, and interpret controlled comparisons."

    def get_misconceptions(self, concept_id: str) -> list[str]:
        self.get_learning_objective(concept_id)
        return [item["code"] for item in (*GUIDED, *CONCEPTS, *TRANSFER)]

    def generate_activity(self, activity: str, stage: int = 0) -> dict[str, Any]:
        items = self._items(activity)
        if stage not in range(len(items)):
            raise ValueError("Unknown Life Sciences activity stage.")
        item = items[stage]
        return {"stage": stage, "activity": activity, "question": item["question"],
                "choices": item["choices"], "requires_reasoning": activity == "transfer",
                "total": len(items)}

    def evaluate_response(self, activity: str, **kwargs: Any) -> dict[str, Any]:
        stage, choice = kwargs["stage"], kwargs["choice"]
        items = self._items(activity)
        if stage not in range(len(items)) or not isinstance(choice, int) or choice not in (0, 1, 2):
            raise ValueError("Choose one of the available answers.")
        item = items[stage]
        correct_choice = choice == item["answer"]
        reasoning = kwargs.get("reasoning", "").lower().strip()
        reasoning_ok = True
        if activity == "transfer":
            # Conservative evidence threshold: one causal statement naming the
            # relevant variable and limitation. Not free-text semantic grading.
            reasoning_ok = (len(re.findall(r"\b[\w]+\b", reasoning)) >= 7
                            and any(term in reasoning for term in item["reasoning_terms"])
                            and any(term in reasoning for term in item["reasoning_cause"])
                            and not any(phrase in reasoning for phrase in
                                        ("light always", "never limit", "does not need", "no effect")))
        correct = correct_choice and reasoning_ok
        feedback = (item["why"] if correct else
                    "Your choice fits, but explain which factor changes and why it limits the rate." if correct_choice else
                    "Not quite. " + item["hint"])
        return {"stage": stage, "correct": correct, "choice_correct": correct_choice,
                "feedback": feedback, "hint": None if correct else item["hint"],
                "support_level": 0 if correct else min(kwargs.get("attempt_number", 1), 3),
                "misconception": None if correct else {"code": item["code"], "evidence": "Response did not meet the curated check."},
                "next_stage": stage + 1 if correct and stage + 1 < len(items) else None,
                "complete": correct and stage == len(items) - 1,
                "notice": "Curated conceptual check only; free-text reasoning is assessed conservatively and is not proof of mastery."}

    def generate_transfer(self, stage: int = 0) -> dict[str, Any]:
        return self.generate_activity("transfer", stage)

    @staticmethod
    def _items(activity: str) -> tuple[dict, ...]:
        try:
            return {"guided_practice": GUIDED, "concept_check": CONCEPTS, "transfer": TRANSFER}[activity]
        except KeyError as exc:
            raise ValueError("Unsupported Life Sciences activity.") from exc
