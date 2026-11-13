"""Live Gemini multi-agent teaching cycle; math judgments come from SymPy."""

import os
import re

from app.math_engine import MathInputError, verify_equation


class ProviderUnavailable(Exception):
    """Gemini is unconfigured or cannot complete a request."""


def run_gemini_learning_cycle(equation: str, student_attempt: str) -> dict:
    if not student_attempt.strip():
        return {"mode": "gemini", "status": "needs_student_attempt", "question": "Show me what you have tried first.", "events": []}

    original = verify_equation(equation)
    if original.classification != "unique_solution":
        raise MathInputError("Only one-variable equations with a unique solution are supported.")

    try:
        from dotenv import load_dotenv
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise ProviderUnavailable("Install google-genai and python-dotenv from requirements.txt.") from exc

    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        raise ProviderUnavailable("GEMINI_API_KEY is missing from your local .env file.")

    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    events: list[dict] = []
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options=types.HttpOptions(timeout=20000))

    def ask(role: str, instructions: str) -> str:
        try:
            response = client.models.generate_content(
                model=model,
                contents=instructions,
                config=types.GenerateContentConfig(temperature=0.2),
            )
            answer = (response.text or "").strip()
            if not answer:
                raise ProviderUnavailable(f"{role} agent returned an empty response.")
            events.append({"agent": role, "action": "generate", "detail": answer[:280]})
            return answer
        except ProviderUnavailable:
            raise
        except Exception as exc:
            raise ProviderUnavailable(f"Gemini request failed for {role}: {type(exc).__name__}: {str(exc)[:220]}") from exc

    diagnosis = ask("diagnostic", (
        "You are the MethodMind Diagnostic Agent. Focus on the STUDENT'S METHOD, not merely their answer. "
        "Identify one likely misconception, say when uncertain, and propose a short teaching objective. "
        "Do not claim to have seen steps not supplied. "
        f"Equation: {equation}\nStudent attempt: {student_attempt}"
    ))

    draft_prompt = (
        "You are the MethodMind Teaching Agent. Guide rather than just hand over the answer. "
        "Explain the generalizable algebra technique, show one worked step, then ask one reflective question. "
        "Always end with a separate last line formatted exactly ANSWER: x=<number>. "
        f"Equation: {equation}\nStudent attempt: {student_attempt}\nDiagnosis: {diagnosis}"
    )
    draft = ask("teaching", draft_prompt)
    revisions = 0
    verification = None
    for attempt in range(3):
        # Extract the actual claimed answer, never trust the agent to self-certify.
        matches = re.findall(r"ANSWER:\s*x\s*=\s*([-+]?\d+(?:\.\d+)?(?:/\d+)?)", draft, flags=re.I)
        if matches:
            try:
                verification = verify_equation(equation, matches[-1])
            except MathInputError:
                verification = None
        else:
            verification = None
        passed = bool(verification and verification.is_correct)
        events.append({"agent": "reviewer", "action": "sympy_verify", "detail": f"pass={passed}; proposed={matches[-1] if matches else 'missing'}"})
        if passed:
            break
        if attempt == 2:
            break
        revisions += 1
        feedback = ask("reviewer", (
            "You are the MethodMind Review Agent. Inspect the teaching draft for inaccurate algebra "
            "and learner clarity. Give concise correction instructions. A separate symbolic checker "
            "has REJECTED the answer or could not parse it. "
            f"Equation: {equation}\nDraft: {draft}\nSymbolically verified solution: x={original.correct_solution}"
        ))
        draft = ask("teaching", draft_prompt + "\nReviewer feedback: " + feedback +
                    f"\nThe independent checker requires the final answer x={original.correct_solution}. Correct and re-explain.")

    success = bool(verification and verification.is_correct)
    return {
        "mode": "gemini", "status": "verified" if success else "verification_failed",
        "diagnosis": diagnosis, "explanation": draft if success else None,
        "verified_answer": original.correct_solution if success else None,
        "transfer_question": "Try 4(x-1)+2=18. Which operation should you undo first?" if success else None,
        "revision_count": revisions, "events": events,
        "disclaimer": "Gemini generated the teaching content; SymPy independently checked the final numeric answer. Explanation accuracy still needs human review.",
    }
