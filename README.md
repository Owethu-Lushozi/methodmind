# MethodMind 🧠

**Think Beyond the Answer.**  
**Colleague Zero Autonomous Agent Hackathon | 13–14 November 2026**  
**Team:** Koa's Lab · **Solo developer:** Owethu Lushozi

## Overview

MethodMind is an AI learning colleague built to address a familiar problem: students may understand a worked example but struggle to apply the same method to a new question. Rather than simply providing answers, MethodMind combines conversation, guided practice, independent mathematical checks, and a bounded agent correction workflow.

**Status:** Working hackathon prototype. The application is deployed on Render; the independently verified learning pathway currently focuses on supported **one-variable linear equations**.

## What students can do

- **Chat with Mindy:** Ask about learning topics, receive AI-generated explanations, and use suggested follow-up questions. General chat is not independently graded or mathematically verified.
- **Bring a problem:** Enter a supported linear equation and an attempted answer. MethodMind checks an explicit numeric answer by substitution before using it in diagnostic feedback.
- **Practise the method:** Complete three progressively revealed, symbolically checked algebra steps. Incorrect attempts receive targeted hints and, for recognised error patterns, specific feedback.
- **Check understanding:** Answer short conceptual questions about distribution and equality-preserving operations.
- **Try transfer:** Solve a different equation and explain why the method works. The answer is checked mathematically; the explanation receives conservative local checks and, in live mode, AI feedback. This is practice evidence, **not proof of mastery**.
- **Inspect agent collaboration:** View a visual timeline of agent actions and expand the technical event log.

## How the agents work

| Component | Role |
| --- | --- |
| **Diagnostic Agent (Groq)** | Interprets the submitted attempt using verified mathematical facts; does not claim to know unseen student reasoning. |
| **Teaching Agent (Groq)** | Generates contextual guidance and proposes an algebra transformation. |
| **SymPy Reviewer** | Independently verifies supported mathematical steps; it is a deterministic checker, not a language model. |
| **Orchestrator** | Coordinates hand-offs, accepts verified proposals, requests a bounded revision after rejection, or stops safely. |

### Verification and correction

```text
Student problem + attempt
          |
   Symbolic answer check
          |
   AI Diagnostic Agent
          |
    AI Teaching Agent
          |
    SymPy verification
       /         \
    PASS         FAIL
     |             |
  Guidance    Request one AI revision
                   |
             SymPy re-check
                /      \
              PASS     FAIL
               |        |
          Guidance   Safe stop
```

The model does not get to declare its own mathematical output correct. SymPy checks the proposed step independently.

### Controlled LIVE correction demo

For an inspectable demonstration, the application can **deliberately inject a known incorrect step** into the live workflow:

- Original equation: `3(x-2)+5=17`
- Injected incorrect proposal: `3x+1=17` — **rejected**
- Orchestrator requests a live AI revision.
- Revised proposal: `3x-1=17` — **verified** by SymPy.

The initial fault is **injected for demonstration**, not a spontaneous Groq mistake. The revision request and symbolic re-check are real. A separate mock/simulated mode is also available and must not be described as live AI.

## Technology

| Layer | Technology |
| --- | --- |
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI |
| AI provider | Groq API (`openai/gpt-oss-20b` used during development) |
| Mathematics | SymPy |
| Hosting | Render |
| Source control | GitHub |

## Run locally

**Requirements:** Python 3.11+, Git, and a Groq API key for live AI functionality.

```bash
git clone https://github.com/Owethu-Lushozi/methodmind.git
cd methodmind
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create a local `.env` file in the project root:

```dotenv
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

**Never commit `.env` or a real API key.** For deployment, configure `GROQ_API_KEY` in the hosting provider's private environment variables.

Start the app:

```bash
python -m uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000** for the interface or **http://127.0.0.1:8000/docs** for the FastAPI documentation.

## Suggested demonstration

1. Open **Home & Chat** and ask Mindy to explain a topic. Show its follow-up suggestions.
2. Open **My Workspace**, select the supported linear-equation activity, and enter `3(x-2)+5=17` with the attempted answer `x=5`.
3. Show the verified diagnostic feedback and the guided steps: `3x-1=17`, `3x=18`, `x=6`.
4. Show the conceptual checks and the independent transfer exercise `4(x-1)+2=18`.
5. Run **Controlled LIVE Correction** and explain the red rejected step, revision request, and green verified correction. Clearly identify the deliberately injected fault.
6. Expand the technical event log if the judges want implementation evidence.

## Tests

From the project root:

```bash
python -m pytest -q
```

The automated suite covers the project's supported workflows. Passing tests does not establish correctness for arbitrary mathematical problems or demonstrate learning gains.

## Scope and limitations

- The **independently checked learning workflow** currently supports one-variable linear equations, not arbitrary quadratic, calculus, or other advanced mathematics.
- Mindy can **discuss broader topics conversationally**, but those responses do not receive the same symbolic verification as the checked algebra activity.
- The teaching sequence is structured; the system makes bounded, verification-driven decisions rather than autonomously designing an entire curriculum.
- The controlled correction demo injects a known fault transparently. It does not prove that a spontaneous model error occurred.
- Progress and feedback in the prototype are not a validated measure of durable student learning.
- Live AI requests require a configured Groq key and provider availability. Offline guided coaching is available for the supported algebra workflow.

## Future work

Expand the set of independently verified mathematical topics, add adaptive teaching-plan selection based on learner evidence, strengthen progress tracking, and evaluate learning outcomes with students.

## Security and responsible use

Keep credentials in private environment variables. Do not commit `.env` files, API keys, or identifiable learner data. Use synthetic examples during public demonstrations. AI-generated explanations should be treated as guidance; the independent symbolic checker applies only within its supported scope.

---

**MethodMind — Think Beyond the Answer.**
