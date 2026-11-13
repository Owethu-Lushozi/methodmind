"""Minimal API scaffold. Agent execution is not implemented yet."""

from fastapi import FastAPI

app = FastAPI(title="MethodMind", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "project": "MethodMind", "phase": "scaffold"}
