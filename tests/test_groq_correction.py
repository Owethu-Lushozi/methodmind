"""Offline, deterministic tests of the real Groq correction orchestration."""
import pytest
from app.agents import groq_workflow as workflow


def _fake_provider(monkeypatch, proposals):
    calls = []
    def fake_ask(client, models, prompt, role, events):
        calls.append((role, prompt))
        events.append({"agent": role, "action": "test_stub", "detail": "Deterministic test response."})
        if role == "diagnostic":
            return {"diagnosis": "Let's check your working.", "focus": "expanding brackets"}
        return {"opening": "Try expanding the brackets first.",
                "first_step_equation": proposals.pop(0)}
    monkeypatch.setattr(workflow, "_client", lambda: object())
    monkeypatch.setattr(workflow, "_models", lambda: ["stub-model"])
    monkeypatch.setattr(workflow, "_ask", fake_ask)
    return calls


def test_rejected_step_is_revised_and_rechecked(monkeypatch):
    calls = _fake_provider(monkeypatch, ["3x-2+5=17", "3x-1=17"])
    result = workflow.run_groq_learning_cycle("3(x-2)+5=17", "I tried x=5")
    assert result["status"] == "verified"
    assert result["revision_count"] == 1
    assert [role for role, _ in calls] == ["diagnostic", "teaching", "teaching_reviser"]
    reviews = [e for e in result["events"] if e["action"] == "sympy_verify_first_step"]
    assert len(reviews) == 2
    assert "valid=False" in reviews[0]["detail"]
    assert "valid=True" in reviews[1]["detail"]
    assert "3x-2+5=17" in reviews[0]["detail"]
    assert any(e["action"] == "correction_verified" for e in result["events"])


def test_correct_first_step_requires_no_revision(monkeypatch):
    calls = _fake_provider(monkeypatch, ["3x-1=17"])
    result = workflow.run_groq_learning_cycle("3(x-2)+5=17", "I tried x=5")
    assert result["revision_count"] == 0
    assert len(calls) == 2
    assert not any(e["action"] == "request_revision" for e in result["events"])


def test_second_rejection_fails_closed(monkeypatch):
    _fake_provider(monkeypatch, ["3x-2+5=17", "3x+5=17"])
    with pytest.raises(workflow.ProviderUnavailable, match="failed independent review"):
        workflow.run_groq_learning_cycle("3(x-2)+5=17", "I tried x=5")


def test_controlled_live_demo_injects_error_then_uses_real_revision_path(monkeypatch):
    calls = _fake_provider(monkeypatch, ["3x-1=17", "3x-1=17"])
    result = workflow.run_groq_learning_cycle("3(x-2)+5=17", "I tried x=5", controlled_demo=True)
    assert result["controlled_demo"] is True
    assert result["revision_count"] == 1
    assert [r for r, _ in calls] == ["diagnostic", "teaching", "teaching_reviser"]
    assert any(e["action"] == "inject_known_error" for e in result["events"])
    reviews = [e for e in result["events"] if e["action"] == "sympy_verify_first_step"]
    assert "proposed=3x+1=17; valid=False" in reviews[0]["detail"]
    assert "proposed=3x-1=17; valid=True" in reviews[1]["detail"]
    assert "deliberately injected" in result["disclaimer"]


def test_controlled_live_demo_rejects_other_equations(monkeypatch):
    _fake_provider(monkeypatch, ["3x-1=17"])
    with pytest.raises(workflow.MathInputError, match="supports only"):
        workflow.run_groq_learning_cycle("2(x+3)=14", "x=4", controlled_demo=True)


def test_controlled_live_demo_fails_closed_on_bad_revision(monkeypatch):
    _fake_provider(monkeypatch, ["3x-1=17", "3x+2=17"])
    with pytest.raises(workflow.ProviderUnavailable, match="failed independent review"):
        workflow.run_groq_learning_cycle("3(x-2)+5=17", "x=5", controlled_demo=True)
