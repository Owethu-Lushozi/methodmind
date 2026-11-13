"""Subject registry. Algebra is the first fully verified specialist."""

from typing import Any

from app.concept_check import get_concept_question, check_concept
from app.math_engine import verify_equation
from app.step_tutor import STEP_PROMPTS, check_step
from app.transfer import TRANSFER_PROBLEMS, check_transfer
from app.learning.contracts import SubjectSpecialist
from app.learning.biology import BiologySpecialist


class AlgebraSpecialist:
    subject_id = "algebra"
    display_name = "Mathematics · Linear equations"

    def identify_concept(self, problem: str, student_attempt: str = "") -> dict[str, Any]:
        verified = verify_equation(problem)
        return {
            "concept_id": "linear_equations",
            "classification": verified.classification,
            "student_evidence": student_attempt.strip(),
            "verification_source": "sympy",
        }

    def get_learning_objective(self, concept_id: str) -> str:
        if concept_id != "linear_equations":
            raise ValueError("Unknown algebra concept.")
        return "Solve a one-variable linear equation and explain why each operation preserves equality."

    def get_misconceptions(self, concept_id: str) -> list[str]:
        if concept_id != "linear_equations":
            raise ValueError("Unknown algebra concept.")
        return ["incomplete_distribution", "constant_balance_mismatch", "incorrect_final_value"]

    def generate_activity(self, activity: str, stage: int = 0) -> dict[str, Any]:
        if activity == "guided_practice":
            if stage not in range(len(STEP_PROMPTS)):
                raise ValueError("Unknown algebra step.")
            return {"stage": stage, "prompt": STEP_PROMPTS[stage]}
        if activity == "concept_check":
            return get_concept_question(stage)
        if activity == "transfer":
            return self.generate_transfer(stage)
        raise ValueError("Unknown algebra activity.")

    def evaluate_response(self, activity: str, **kwargs: Any) -> dict[str, Any]:
        if activity == "guided_practice":
            return check_step(kwargs["equation"], kwargs["stage"],
                              kwargs["submitted_equation"], kwargs.get("attempt_number", 1))
        if activity == "concept_check":
            return check_concept(kwargs["stage"], kwargs["choice"])
        if activity == "transfer":
            return check_transfer(kwargs["stage"], kwargs["proposed_answer"], kwargs.get("reasoning", ""))
        raise ValueError("Unknown algebra activity.")

    def generate_transfer(self, stage: int = 0) -> dict[str, Any]:
        if stage not in range(len(TRANSFER_PROBLEMS)):
            raise ValueError("Unknown algebra transfer stage.")
        return {"stage": stage, **TRANSFER_PROBLEMS[stage]}


_SUBJECTS: dict[str, SubjectSpecialist] = {"algebra": AlgebraSpecialist(), "biology": BiologySpecialist()}


def get_subject(subject_id: str) -> SubjectSpecialist:
    try:
        return _SUBJECTS[subject_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported subject: {subject_id}") from exc


def list_subjects() -> list[dict[str, str]]:
    return [{"id": item.subject_id, "name": item.display_name} for item in _SUBJECTS.values()]
