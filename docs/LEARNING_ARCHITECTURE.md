# MethodMind reusable learning colleague — Milestone 15

## Purpose

Preserve the reliable linear-equation prototype while separating **how we teach**
from **what subject is being taught**. This is the foundation for adding one
focused Life Sciences topic without copying the entire tutoring workflow.

## Current implementation

1. **API** (`app/main.py`) retains the existing routes and response shapes.
2. **Learning orchestrator** (`app/learning/orchestrator.py`) routes guided
   steps, conceptual checks, and transfer practice to the chosen specialist.
   Optional Groq feedback is used only where supported; the underlying subject
   checker remains authoritative.
3. **Subject contract** (`app/learning/contracts.py`) declares seven future
   learning states and six standard specialist operations.
4. **Subject registry** (`app/learning/subjects.py`) currently exposes the
   verified Algebra specialist. The `/learning/subjects` endpoint lists only
   subjects actually implemented.
5. **Existing engines** (`math_engine.py`, `step_tutor.py`, `concept_check.py`,
   `transfer.py`) remain the working source of math validation and feedback.

## Specialist operations

| Operation | Purpose |
| --- | --- |
| `identify_concept` | Extract supported concept and validated evidence |
| `get_learning_objective` | State what the student should learn |
| `get_misconceptions` | List patterns a checker can look for |
| `generate_activity` | Provide a guided step or conceptual question |
| `evaluate_response` | Delegate response checking to subject-specific logic |
| `generate_transfer` | Supply a new question to test independent application |

## Milestone 16 — session learning intelligence

- `app/learning/session.py` creates an opaque per-session identifier and keeps
  at most 300 sessions in process memory. Inactive sessions expire after two
  hours and evidence history is bounded to 80 events.
- The original step, concept and transfer endpoints accept an **optional**
  `session_id`; old clients remain compatible. When supplied, correct and
  incorrect attempts are recorded with state-aware progression.
- Verified correct algebra steps unlock concept checks; two checked concepts
  unlock transfer challenges; two checked answers **with acceptable reasoning**
  unlock reflection. Invalid or skipped stages are rejected.
- Repeated misconception patterns trigger a smaller-example recommendation.
  Evidence shows what was attempted and checked, not proof of mastery.
- The front end creates a session after successfully starting coaching and
  displays the learning state, attempts, hints and the next recommendation.
- State lasts only while this server process runs; restarting or deploying
  multiple workers discards/isolates sessions. Persistence is future work.

## Milestone 17 — Life Sciences specialist

- `app/learning/biology.py` implements the same six-operation subject contract
  for a single curated topic: **photosynthesis limiting factors**.
- A subject selector switches the website between existing Mathematics and a
  focused Life Sciences learning pathway. Mathematics routes and UI behaviour
  are unchanged.
- Biology follows three guided scenarios, two concept checks, and two transfer
  scenarios with an explanation requirement. This uses the existing session
  state and evidence tracker introduced in Milestone 16.
- Answers are checked against curated choices and conservative keyword-based
  reasoning criteria. These checks are not a general semantic evaluation or
  proof that a learner understands biology.
- Relevant misconceptions include unlimited-light assumptions, not controlling
  experimental variables, and misreading a rate plateau.
- The new API routes are `GET /learning/biology/activity/{activity}/{stage}`
  and `POST /learning/biology/check`. Biology sessions use
  `POST /learning/session` with `subject=biology` and
  `problem=photosynthesis_limiting_factors`.

## Next milestones — not implemented yet

- **18D:** Durable session state, broader interruption/resume support, usability,
  and personality refinement.

## Milestone 18C — connected learning evidence and adaptive follow-up

- Clicking an approved practice offer and starting a checked activity links its
  opaque backend session ID to the active conversation via
  `POST /conversation/link-session`. The server rejects mismatched subjects and
  conversations with no approved practice offer.
- After a checked answer, the frontend calls `POST /conversation/sync-evidence`.
  The backend itself reads session evidence from `get_session`: the browser
  cannot submit its own correctness flag, misconception or mastery claim.
- New checked attempts are summarized once into the chat; duplicate syncs are
  no-ops. Recognized photosynthesis misconception codes receive focused advice;
  repeated difficulty triggers an invitation to try a smaller example.
- The AI's next conversational turn sees the bounded server-originated feedback
  in history, but does not become the verifier. All existing checked activity
  endpoints still determine correctness and progression.
- Quick replies are restricted more tightly to learner-voice phrases, with
  safe defaults when a model provides tutor instructions. A deterministic
  teaching nudge also recognizes "expanding brackets" from learner history.
- Scope is intentionally short-lived and single-process. Reloaded chat sessions,
  multiple workers, and broad topic-specific verified exercises remain future work.

## Milestone 18B — bounded conversational teaching and practice handoff

- The live model is prompted to explain or give a miniature example after a
  short diagnosis, rather than only asking follow-up questions. A limited
  server-side guard supplies a compact teaching example if three consecutive
  assistant turns consist solely of questions about a supported focus.
- Suggested chat replies are filtered to favour learner-voice statements.
- The backend computes `practice_offer` from a narrow allowlist: verified linear
  equations or curated photosynthesis limiting-factor scenarios. It ignores
  any tool request fabricated by the model. Generic biology and unsupported
  calculus topics do not grant a checked activity offer.
- The learner must click the offer: algebra focuses the existing equation form;
  photosynthesis starts the existing curated pathway. There is no automatic
  answer submission, grading, or mastery advancement from chat.
- Existing subject-specific checking endpoints remain authoritative. Feedback
  from those checks is **not yet synchronized back into chat**; that linkage is
  explicitly deferred to 18C to avoid untrusted client claims of correctness.
- Session state guidance now uses subject-appropriate biology language.

## Milestone 18A — conversational foundation

- New chat panel above the structured learning cards. Learners can type freely,
  receive a clarifying question, and select optional suggested replies.
- `POST /conversation/start`, `POST /conversation/message`, and
  `GET /conversation/{conversation_id}` support bounded two-hour conversations.
- Groq is used for constrained intent/topic discovery and friendly follow-up
  questions when available. Responses must match an allowed intent and schema;
  invalid or unavailable model responses use a clearly labelled offline fallback.
- History retains up to 12 recent messages per conversation and keeps at most
  200 active conversations in process memory. It resets on backend restart.
- **No topic answer is independently verified by the chat.** The conversation
  cannot award mastery, advance checked stages, or call assessment tools yet.
- Existing algebra and Life Sciences forms and endpoints are unchanged.
  followed by personality and aesthetic redesign.

## Invariants

- An LLM can suggest a hint but cannot override a failed symbolic check.
- The app cannot claim unsupported subjects are available.
- Earlier API clients and the existing hackathon demo remain functional.
- Session states track observed evidence only; they are not certified mastery.
