"""MethodMind API: symbolic verification, mock workflow, and live AI workflow."""

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field

from app.math_engine import MathInputError, Verification, verify_equation
from app.agents.workflow import run_mock_learning_cycle
from app.agents.groq_workflow import ProviderUnavailable, run_groq_learning_cycle, generate_adaptive_step_hint, review_transfer_explanation
from app.transfer import TRANSFER_PROBLEMS, check_transfer
from app.agents.coach import run_coach
from app.step_tutor import check_step
from app.concept_check import check_concept, get_concept_question

app = FastAPI(title="MethodMind", version="0.1.0")
WEB_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "project": "MethodMind", "phase": "scaffold"}


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


class StepRequest(BaseModel):
    equation: str = Field(min_length=3, max_length=241)
    stage: int = Field(ge=0, le=2)
    submitted_equation: str = Field(min_length=3, max_length=241)
    coaching_mode: str = Field(default="coach", pattern="^(coach|groq)$")
    attempt_number: int = Field(default=1, ge=1, le=20)


@app.post("/learning/step")
def learning_step(request: StepRequest) -> dict:
    try:
        response = check_step(request.equation, request.stage, request.submitted_equation,
                              request.attempt_number)
        response["hint_source"] = "symbolic" if not response["correct"] else None
        if (not response["correct"] and request.coaching_mode == "groq" and
                response["support_level"] == 1):
            try:
                response["hint"] = generate_adaptive_step_hint(
                    request.equation, request.stage, request.submitted_equation,
                    response["feedback"], response["hint"],
                )
                response["hint_source"] = "live_ai"
            except ProviderUnavailable:
                # Never break tutoring because the model is overloaded or unavailable.
                response["hint_source"] = "symbolic_fallback"
        elif not response["correct"] and request.coaching_mode == "groq":
            # Repeated attempts use verified scaffolding, without extra paid AI calls.
            response["hint_source"] = "adaptive_scaffold"
        return response
    except MathInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/learning/transfer")
def learning_transfer(request: TransferRequest) -> dict:
    try:
        result = check_transfer(request.stage, request.proposed_answer, request.reasoning)
        result["review_source"] = "offline_rubric"
        if result["answer_correct"] and request.coaching_mode == "groq" and request.reasoning.strip():
            try:
                review = review_transfer_explanation(TRANSFER_PROBLEMS[request.stage]["equation"], request.reasoning)
                result["review_source"] = "groq_with_local_guard"
                # The model can request more explanation, but cannot bypass local checks.
                if review["status"] != "supported":
                    result["correct"] = False
                    result["practice_complete"] = False
                    result["next_stage"] = None
                    result["next_question"] = None
                    result["reasoning_status"] = review["status"]
                if result["correct"] or review["status"] != "supported":
                    result["feedback"] = "Your value satisfies the equation. " + review["feedback"]
                else:
                    result["feedback"] += " The AI also found the explanation plausible, but more explicit reasoning is needed for this checkpoint."
            except ProviderUnavailable:
                result["review_source"] = "offline_fallback"
        return result
    except MathInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class ConceptRequest(BaseModel):
    stage: int = Field(ge=0, le=1)
    choice: int = Field(ge=0, le=2)


@app.get("/learning/concept/{stage}")
def learning_concept_question(stage: int) -> dict:
    try:
        return get_concept_question(stage)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/learning/concept")
def learning_concept_check(request: ConceptRequest) -> dict:
    try:
        return check_concept(request.stage, request.choice)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
