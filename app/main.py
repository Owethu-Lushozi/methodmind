"""MethodMind API: symbolic verification, mock workflow, and live AI workflow."""

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field

from app.math_engine import MathInputError, Verification, verify_equation
from app.agents.workflow import run_mock_learning_cycle
from app.agents.gemini_workflow import ProviderUnavailable, run_gemini_learning_cycle
from app.transfer import check_transfer
from app.agents.coach import run_coach

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
    """Live Gemini agents, independently checked by the math engine."""
    try:
        return run_gemini_learning_cycle(request.equation, request.student_attempt)
    except MathInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


class TransferRequest(BaseModel):
    stage: int = Field(ge=0, le=1)
    proposed_answer: str = Field(min_length=1, max_length=120)
    reasoning: str = Field(default="", max_length=1000)


@app.post("/learning/transfer")
def learning_transfer(request: TransferRequest) -> dict:
    try:
        return check_transfer(request.stage, request.proposed_answer, request.reasoning)
    except MathInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
