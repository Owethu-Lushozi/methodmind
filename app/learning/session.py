"""Bounded, short-lived in-memory evidence for an individual learning session.

This is intentionally not durable learner profiling or a claim of mastery.
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import RLock
from uuid import uuid4

from app.learning.contracts import LearningState
from app.learning.subjects import get_subject


SESSION_TTL = timedelta(hours=2)
MAX_SESSIONS = 300
MAX_EVENTS = 80
_lock = RLock()
_sessions: dict[str, "LearningSession"] = {}


@dataclass
class LearningSession:
    id: str
    subject: str
    problem: str
    state: LearningState = LearningState.GUIDED_PRACTICE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    events: list[dict] = field(default_factory=list)
    checked_steps: set[int] = field(default_factory=set)
    checked_concepts: set[int] = field(default_factory=set)
    checked_transfers: set[int] = field(default_factory=set)
    mistakes: Counter = field(default_factory=Counter)
    hints_received: int = 0


def _purge(now: datetime) -> None:
    for key, value in list(_sessions.items()):
        if now - value.updated_at > SESSION_TTL:
            del _sessions[key]
    while len(_sessions) >= MAX_SESSIONS:
        oldest = min(_sessions, key=lambda key: _sessions[key].updated_at)
        del _sessions[oldest]


def _snapshot(session: LearningSession) -> dict:
    failures = sum(not event["correct"] for event in session.events)
    repeated = [code for code, count in session.mistakes.items() if count >= 2]
    if session.state == LearningState.REFLECT:
        action = "reflect_on_method"
        message = "You completed the checks and transfer challenges. Explain your method in your own words."
    elif repeated and session.events and not session.events[-1]["correct"]:
        action = "teach_smaller_example"
        message = "Let's work through a smaller example of the part you're repeatedly finding difficult."
    elif session.events and not session.events[-1]["correct"]:
        action = "offer_focused_hint" if session.events[-1]["support_level"] < 3 else "teach_smaller_example"
        message = "Let's focus on the operation that caused the difficulty before trying again."
    elif session.state == LearningState.CONCEPT_CHECK:
        action, message = "check_reasoning", ("Now explain why the algebraic operations work." if session.subject == "algebra" else "Now explain the scientific reasoning behind your answer.")
    elif session.state == LearningState.TRANSFER:
        action, message = "try_new_problem", ("Apply the same method to a new equation and explain your reasoning." if session.subject == "algebra" else "Apply the same concept to a new scenario and explain your reasoning.")
    else:
        action, message = "continue_guided_practice", ("Continue with the next checked algebra step." if session.subject == "algebra" else "Continue with the next checked Life Sciences scenario.")
    return {
        "session_id": session.id,
        "subject": session.subject,
        "state": session.state.value,
        "evidence": {
            "attempts": len(session.events), "incorrect_attempts": failures,
            "checked_steps": sorted(session.checked_steps),
            "checked_concepts": sorted(session.checked_concepts),
            "checked_transfers": sorted(session.checked_transfers),
            "misconceptions": dict(session.mistakes),
            "hints_received": session.hints_received,
        },
        "next_action": action,
        "guidance": message,
        "notice": "Short-lived session evidence only; these checks do not prove mastery.",
    }


def create_session(subject: str, problem: str) -> dict:
    specialist = get_subject(subject)
    specialist.identify_concept(problem)
    now = datetime.now(timezone.utc)
    with _lock:
        _purge(now)
        session = LearningSession(id=uuid4().hex, subject=subject, problem=problem,
                                  created_at=now, updated_at=now)
        _sessions[session.id] = session
        return _snapshot(session)


def get_session(session_id: str) -> dict:
    now = datetime.now(timezone.utc)
    with _lock:
        _purge(now)
        session = _sessions.get(session_id)
        if not session:
            raise KeyError("Learning session not found or expired.")
        return _snapshot(session)


def record_evidence(session_id: str, subject: str, activity: str, stage: int,
                    result: dict, problem: str | None = None) -> dict:
    now = datetime.now(timezone.utc)
    with _lock:
        _purge(now)
        session = _sessions.get(session_id)
        if not session:
            raise KeyError("Learning session not found or expired.")
        if session.subject != subject or (problem is not None and session.problem != problem):
            raise ValueError("Session subject or equation does not match this request.")
        expected = {"guided_practice": LearningState.GUIDED_PRACTICE,
                    "concept_check": LearningState.CONCEPT_CHECK,
                    "transfer": LearningState.TRANSFER}
        if activity not in expected:
            raise ValueError("Unsupported learning activity.")
        if session.state != expected[activity]:
            raise ValueError("This activity is not available at the current learning state.")
        # Prevent skipped stages and repeated completed stages from forging progress.
        checked = {"guided_practice": session.checked_steps,
                   "concept_check": session.checked_concepts,
                   "transfer": session.checked_transfers}[activity]
        if stage != len(checked):
            raise ValueError("Complete the current activity before moving ahead.")
        correct = bool(result.get("correct", False))
        misconception = result.get("misconception")
        code = misconception.get("code") if isinstance(misconception, dict) else None
        if code and not correct:
            session.mistakes[code] += 1
        elif not correct and activity == "concept_check":
            session.mistakes[f"concept_{stage}"] += 1
        elif not correct and activity == "transfer":
            session.mistakes[f"transfer_{stage}"] += 1
        support = int(result.get("support_level") or 0)
        if not correct and (result.get("hint") or support):
            session.hints_received += 1
        session.events.append({"activity": activity, "stage": stage,
                               "correct": correct, "misconception": code,
                               "support_level": support})
        session.events = session.events[-MAX_EVENTS:]
        if correct:
            checked.add(stage)
            if activity == "guided_practice" and len(checked) == 3:
                session.state = LearningState.CONCEPT_CHECK
            elif activity == "concept_check" and len(checked) == 2:
                session.state = LearningState.TRANSFER
            elif activity == "transfer" and len(checked) == 2:
                session.state = LearningState.REFLECT
        session.updated_at = now
        return _snapshot(session)
