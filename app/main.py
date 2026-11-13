"""Minimal API scaffold. Agent execution is not implemented yet."""

from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.math_engine import MathInputError, Verification, verify_equation
from app.agents.workflow import run_mock_learning_cycle

app = FastAPI(title="MethodMind", version="0.1.0")


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


@app.post("/learning/demo")
def learning_demo(request: LearningDemoRequest) -> dict:
    try:
        return run_mock_learning_cycle(request.equation, request.student_attempt)
    except MathInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
