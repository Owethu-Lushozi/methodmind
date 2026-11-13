"""MethodMind API: symbolic verification, mock workflow, and live AI workflow."""

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field

from app.math_engine import MathInputError, Verification, verify_equation
from app.agents.workflow import run_mock_learning_cycle
from app.agents.groq_workflow import ProviderUnavailable, run_groq_learning_cycle
from app.agents.coach import run_coach
from app.learning.orchestrator import evaluate_step, evaluate_concept, evaluate_transfer
from app.learning.subjects import get_subject, list_subjects
from app.learning.session import create_session, get_session, record_evidence
from app.learning.biology import TOPIC_ID
from app.learning.conversation import (start_conversation, get_conversation, send_message,
                                       link_learning_session, sync_learning_evidence)

app = FastAPI(title="MethodMind", version="0.1.0")
WEB_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "project": "MethodMind", "phase": "scaffold"}


@app.get("/learning/subjects")
def learning_subjects() -> dict:
    """Discover currently supported specialist subjects."""
    return {"subjects": list_subjects(), "default_subject": "algebra"}


@app.post("/conversation/start")
def conversation_start() -> dict:
    return start_conversation()


class ConversationMessageRequest(BaseModel):
    conversation_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=1500)


@app.post("/conversation/message")
def conversation_message(request: ConversationMessageRequest) -> dict:
    try:
        return send_message(request.conversation_id, request.message)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/conversation/{conversation_id}")
def conversation_status(conversation_id: str) -> dict:
    try:
        return get_conversation(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


class ConversationLinkRequest(BaseModel):
    conversation_id: str = Field(min_length=1, max_length=64)
    learning_session_id: str = Field(min_length=1, max_length=64)


@app.post("/conversation/link-session")
def conversation_link_session(request: ConversationLinkRequest) -> dict:
    try:
        return link_learning_session(request.conversation_id, request.learning_session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class ConversationSyncRequest(BaseModel):
    conversation_id: str = Field(min_length=1, max_length=64)


@app.post("/conversation/sync-evidence")
def conversation_sync_evidence(request: ConversationSyncRequest) -> dict:
    try:
        return sync_learning_evidence(request.conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class SessionStartRequest(BaseModel):
    subject: str = Field(default="algebra", max_length=40)
    problem: str = Field(min_length=3, max_length=241)


@app.post("/learning/session")
def learning_session_start(request: SessionStartRequest) -> dict:
    try:
        return create_session(request.subject, request.problem)
    except (MathInputError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/learning/session/{session_id}")
def learning_session_status(session_id: str) -> dict:
    try:
        return get_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/learning/biology/activity/{activity}/{stage}")
def biology_activity(activity: str, stage: int) -> dict:
    try:
        return get_subject("biology").generate_activity(activity, stage)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class BiologyCheckRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    activity: str = Field(pattern="^(guided_practice|concept_check|transfer)$")
    stage: int = Field(ge=0, le=2)
    choice: int = Field(ge=0, le=2)
    reasoning: str = Field(default="", max_length=1000)
    attempt_number: int = Field(default=1, ge=1, le=20)


@app.post("/learning/biology/check")
def biology_check(request: BiologyCheckRequest) -> dict:
    try:
        result = get_subject("biology").evaluate_response(
            request.activity, stage=request.stage, choice=request.choice,
            reasoning=request.reasoning, attempt_number=request.attempt_number)
        result["learning_session"] = record_evidence(
            request.session_id, "biology", request.activity, request.stage, result, TOPIC_ID)
        return result
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class MathVerificationRequest(BaseModel):
    equation: str = Field(min_length=3, max_length=241)
    proposed_answer: str | None = Field(default=None, max_length=120)


@app.post("/math/verify")
def verify_math(request: MathVerificationRequest) -> Verification:
    try:
        return verify_equation(request.equation, request.proposed_answer)
    except MathInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class LearningDemoRequest(BaseModel):
    equation: str = Field(min_length=3, max_length=241)
    student_attempt: str = Field(default="", max_length=1000)


@app.post("/learning/coach")
def learning_coach(request: LearningDemoRequest) -> dict:
    try:
        return run_coach(request.equation, request.student_attempt)
    except MathInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/learning/demo")
def learning_demo(request: LearningDemoRequest) -> dict:
    try:
        return run_mock_learning_cycle(request.equation, request.student_attempt)
    except MathInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/learning/run")
def learning_run(request: LearningDemoRequest) -> dict:
    """Live Groq agents, independently checked by the math engine."""
    try:
        return run_groq_learning_cycle(request.equation, request.student_attempt)
    except MathInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


class TransferRequest(BaseModel):
    stage: int = Field(ge=0, le=1)
    proposed_answer: str = Field(min_length=1, max_length=120)
    reasoning: str = Field(default="", max_length=1000)
    coaching_mode: str = Field(default="coach", pattern="^(coach|groq)$")
    session_id: str | None = Field(default=None, max_length=64)


class StepRequest(BaseModel):
    equation: str = Field(min_length=3, max_length=241)
    stage: int = Field(ge=0, le=2)
    submitted_equation: str = Field(min_length=3, max_length=241)
    coaching_mode: str = Field(default="coach", pattern="^(coach|groq)$")
    attempt_number: int = Field(default=1, ge=1, le=20)
    session_id: str | None = Field(default=None, max_length=64)


@app.post("/learning/step")
def learning_step(request: StepRequest) -> dict:
    try:
        response = evaluate_step("algebra", request.equation, request.stage,
                                 request.submitted_equation, request.coaching_mode,
                                 request.attempt_number)
        if request.session_id:
            response["learning_session"] = record_evidence(
                request.session_id, "algebra", "guided_practice", request.stage,
                response, request.equation)
        return response
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (MathInputError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/learning/transfer")
def learning_transfer(request: TransferRequest) -> dict:
    try:
        response = evaluate_transfer("algebra", request.stage, request.proposed_answer,
                                     request.reasoning, request.coaching_mode)
        if request.session_id:
            response["learning_session"] = record_evidence(
                request.session_id, "algebra", "transfer", request.stage, response)
        return response
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (MathInputError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class ConceptRequest(BaseModel):
    stage: int = Field(ge=0, le=1)
    choice: int = Field(ge=0, le=2)
    session_id: str | None = Field(default=None, max_length=64)


@app.get("/learning/concept/{stage}")
def learning_concept_question(stage: int) -> dict:
    try:
        return get_subject("algebra").generate_activity("concept_check", stage)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/learning/concept")
def learning_concept_check(request: ConceptRequest) -> dict:
    try:
        response = evaluate_concept("algebra", request.stage, request.choice)
        if request.session_id:
            response["learning_session"] = record_evidence(
                request.session_id, "algebra", "concept_check", request.stage, response)
        return response
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
