"""Milestone 18A conversational discovery and safety boundaries."""

from fastapi.testclient import TestClient

from app.main import app
from app.learning import conversation
from app.agents.groq_workflow import ProviderUnavailable


def test_offline_conversation_keeps_context(monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise ProviderUnavailable("offline")
    monkeypatch.setattr(conversation, "_model_response", unavailable)
    client = TestClient(app)
    created = client.post("/conversation/start")
    assert created.status_code == 200
    cid = created.json()["conversation_id"]
    response = client.post("/conversation/message", json={
        "conversation_id": cid, "message": "I'm struggling with photosynthesis"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["source"] == "offline_fallback"
    assert data["topic"] == "Photosynthesis"
    assert not data["verified"]
    assert data["next_action"] == "offer_checked_practice"
    assert len(client.get(f"/conversation/{cid}").json()["messages"]) == 3
    assert client.get("/conversation/nonexistent").status_code == 404


def test_model_intent_validated_and_bounded(monkeypatch):
    monkeypatch.setattr(conversation, "_model_response", lambda *_args: {
        "intent": "request_example", "subject": "Mathematics", "topic": "Calculus",
        "reply": "What part of substitution is confusing?", "suggestions": ["When to use it", "How to calculate"],
    })
    c = TestClient(app)
    cid = c.post("/conversation/start").json()["conversation_id"]
    data = c.post("/conversation/message", json={"conversation_id": cid,
        "message": "How do I use integration by substitution?"}).json()
    assert data["intent"] == "request_example"
    assert data["source"] == "groq"
    assert data["verified"] is False
    assert len(data["suggestions"]) == 2


def test_invalid_model_action_falls_back(monkeypatch):
    monkeypatch.setattr(conversation, "_model_response", lambda *_args: {
        "intent": "award_mastery", "reply": "You are verified!"})
    c = TestClient(app)
    cid = c.post("/conversation/start").json()["conversation_id"]
    result = c.post("/conversation/message", json={"conversation_id": cid,
        "message": "I am struggling with algebra"}).json()
    assert result["source"] == "offline_fallback"
    assert result["verified"] is False
    assert "verified!" not in result["reply"].lower()


def test_supported_activity_offer_is_server_approved(monkeypatch):
    monkeypatch.setattr(conversation, "_model_response", lambda *_args: {
        "intent": "request_practice", "subject": "Biology", "topic": "Photosynthesis",
        "reply": "Let's practise a limiting-factor scenario.",
        "suggestions": ["What is photosynthesis?", "I want a simple example"],
        "practice_offer": {"subject_id": "arbitrary_tool", "activity": "award_mastery"},
    })
    c = TestClient(app)
    cid = c.post("/conversation/start").json()["conversation_id"]
    result = c.post("/conversation/message", json={"conversation_id": cid,
        "message": "I need practice on photosynthesis"}).json()
    assert result["practice_offer"]["subject_id"] == "biology"
    assert result["practice_offer"]["activity"] == "guided_practice"
    assert result["suggestions"] == ["I want a simple example"]
    assert result["verified"] is False


def test_unsupported_calculus_never_offers_algebra(monkeypatch):
    monkeypatch.setattr(conversation, "_model_response", lambda *_args: {
        "intent": "diagnose", "subject": "Mathematics", "topic": "Calculus",
        "reply": "Let's look at the chain rule.", "suggestions": [],
        "practice_offer": {"subject_id": "algebra"},
    })
    c = TestClient(app)
    cid = c.post("/conversation/start").json()["conversation_id"]
    result = c.post("/conversation/message", json={"conversation_id": cid,
        "message": "I'm struggling with integration by substitution"}).json()
    assert result["practice_offer"] is None
    assert result["next_action"] == "ask_followup"


def test_model_question_loop_turns_into_explanation(monkeypatch):
    monkeypatch.setattr(conversation, "_model_response", lambda *_args: {
        "intent": "diagnose", "subject": "Mathematics", "topic": "Calculus",
        "reply": "Which part is confusing?", "suggestions": []})
    c = TestClient(app)
    cid = c.post("/conversation/start").json()["conversation_id"]
    for message in ("Calculus", "Chain rule", "Still confused"):
        result = c.post("/conversation/message", json={
            "conversation_id": cid, "message": message}).json()
    assert "derivative of" in result["reply"]
    assert result["verified"] is False


def test_checked_evidence_link_requires_offered_subject(monkeypatch):
    monkeypatch.setattr(conversation, "_model_response", lambda *_args: {
        "intent": "request_practice", "subject": "Life Sciences", "topic": "Photosynthesis",
        "reply": "Let's practise.", "suggestions": []})
    c = TestClient(app)
    cid = c.post("/conversation/start").json()["conversation_id"]
    c.post("/conversation/message", json={"conversation_id": cid,
        "message": "I need practice on photosynthesis"})
    algebra = c.post("/learning/session", json={"subject": "algebra",
        "problem": "3(x-2)+5=17"}).json()["session_id"]
    rejected = c.post("/conversation/link-session", json={"conversation_id": cid,
        "learning_session_id": algebra})
    assert rejected.status_code == 422
    assert c.post("/conversation/sync-evidence", json={"conversation_id": cid}).status_code == 422


def test_chat_sync_reads_backend_checked_evidence_only(monkeypatch):
    from app.learning.session import record_evidence
    monkeypatch.setattr(conversation, "_model_response", lambda *_args: {
        "intent": "request_practice", "subject": "Life Sciences", "topic": "Photosynthesis",
        "reply": "Let's practise.", "suggestions": []})
    c = TestClient(app)
    cid = c.post("/conversation/start").json()["conversation_id"]
    c.post("/conversation/message", json={"conversation_id": cid,
        "message": "I need photosynthesis practice"})
    sid = c.post("/learning/session", json={"subject": "biology",
        "problem": "photosynthesis_limiting_factors"}).json()["session_id"]
    assert c.post("/conversation/link-session", json={"conversation_id": cid,
        "learning_session_id": sid}).status_code == 200
    empty = c.post("/conversation/sync-evidence", json={"conversation_id": cid}).json()
    assert empty["updated"] is False
    record_evidence(sid, "biology", "guided_practice", 0,
                    {"correct": False, "hint": "Think about light.",
                     "misconception": {"code": "limiting_factor"}},
                    "photosynthesis_limiting_factors")
    updated = c.post("/conversation/sync-evidence", json={"conversation_id": cid}).json()
    assert updated["updated"] is True
    assert updated["checked_evidence"]["attempts"] == 1
    assert updated["checked_evidence"]["incorrect_attempts"] == 1
    assert updated["verified"] is False
    assert c.post("/conversation/sync-evidence", json={"conversation_id": cid}).json()["updated"] is False


def test_suggested_reply_rejects_instructions():
    assert conversation._student_suggestions([
        "Try expanding a simple product", "Show me an example", "I need a simple example"]) == ["I need a simple example"]
