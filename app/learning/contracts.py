"""Shared contracts for subject specialists and learning actions.

These contracts deliberately do not assert a student's mastery. Individual
answers are evidence; future session-state logic will interpret that evidence.
"""

from enum import Enum
from typing import Any, Protocol, runtime_checkable


class LearningState(str, Enum):
    DISCOVER = "discover"
    DIAGNOSE = "diagnose"
    TEACH = "teach"
    GUIDED_PRACTICE = "guided_practice"
    CONCEPT_CHECK = "concept_check"
    TRANSFER = "transfer"
    REFLECT = "reflect"


@runtime_checkable
class SubjectSpecialist(Protocol):
    subject_id: str
    display_name: str

    def identify_concept(self, problem: str, student_attempt: str = "") -> dict[str, Any]: ...

    def get_learning_objective(self, concept_id: str) -> str: ...

    def get_misconceptions(self, concept_id: str) -> list[str]: ...

    def generate_activity(self, activity: str, stage: int = 0) -> dict[str, Any]: ...

    def evaluate_response(self, activity: str, **kwargs: Any) -> dict[str, Any]: ...

    def generate_transfer(self, stage: int = 0) -> dict[str, Any]: ...
