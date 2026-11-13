const form = document.querySelector('#learning-form');
const submit = document.querySelector('#submit');
const mode = document.querySelector('#mode');
const modeHint = document.querySelector('#mode-hint');
const empty = document.querySelector('#empty');
const result = document.querySelector('#result');
const set = (id, value) => { document.getElementById(id).textContent = value ?? 'Not available'; };
let transferStage = 0;
let pendingNextStage = null;
let tutorStage = 0;
let tutorNextStage = null;
let stageAttemptCount = 0;
let activeEquation = '';
let activeTutorMode = 'coach';
let conceptStage = 0;
let learningSessionId = null;

function updateLearningMemory(session) {
  if (!session) return;
  window.dispatchEvent(new CustomEvent('methodmind:checked-evidence', {detail: {subject: 'algebra'}}));
  const label = document.querySelector('#learning-memory');
  label.hidden = false;
  const names = {guided_practice: 'Guided practice', concept_check: 'Understanding check',
    transfer: 'Independent transfer', reflect: 'Reflection'};
  const evidence = session.evidence;
  label.textContent = `Learning colleague · ${names[session.state] || session.state} · ` +
    `${evidence.attempts} attempts · ${evidence.hints_received} hints. ${session.guidance}`;
}

async function showConcept(stage) {
  const response = await fetch(`/learning/concept/${stage}`);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Could not load the concept question.');
  conceptStage = stage;
  document.querySelector('#concept-wrap').hidden = false;
  document.querySelector('#concept-form').hidden = false;
  document.querySelector('#concept-next').hidden = true;
  document.querySelector('#concept-feedback').hidden = true;
  set('concept-progress', `Concept ${stage + 1} of 2`);
  set('concept-question', data.question);
  const options = document.querySelector('#concept-options');
  options.replaceChildren();
  data.choices.forEach((choice, index) => {
    const label = document.createElement('label');
    const radio = document.createElement('input');
    radio.type = 'radio';
    radio.name = 'concept-choice';
    radio.value = String(index);
    radio.required = true;
    label.append(radio, document.createTextNode(choice));
    options.appendChild(label);
  });
}

document.querySelector('#concept-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const selected = document.querySelector('input[name="concept-choice"]:checked');
  if (!selected) return;
  const button = document.querySelector('#concept-check');
  const feedback = document.querySelector('#concept-feedback');
  button.disabled = true;
  try {
    const response = await fetch('/learning/concept', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({stage: conceptStage, choice: Number(selected.value), session_id: learningSessionId}),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not check your reasoning.');
    updateLearningMemory(data.learning_session);
    feedback.hidden = false;
    feedback.textContent = data.feedback;
    if (data.correct) {
      document.querySelector('#concept-form').hidden = true;
      if (data.complete) {
        feedback.textContent += '\nBoth concepts checked. Now try solving a new equation independently.';
        document.querySelector('#transfer-wrap').hidden = false;
      } else {
        document.querySelector('#concept-next').hidden = false;
      }
    }
  } catch (error) {
    feedback.hidden = false;
    feedback.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

document.querySelector('#concept-next').addEventListener('click', async () => {
  try { await showConcept(conceptStage + 1); }
  catch (error) {
    const feedback = document.querySelector('#concept-feedback');
    feedback.hidden = false;
    feedback.textContent = error.message;
  }
});

function resetTutor(equation, enabled) {
  activeEquation = equation;
  tutorStage = 0;
  tutorNextStage = null;
  stageAttemptCount = 0;
  document.querySelector('#concept-wrap').hidden = true;
  document.querySelector('#steps-wrap').hidden = !enabled;
  document.querySelector('#step-form').hidden = false;
  document.querySelector('#step-feedback').hidden = true;
  document.querySelector('#step-next').hidden = true;
  document.querySelector('#step-equation').value = '';
  document.querySelector('#revealed-steps').replaceChildren();
  set('step-prompt', 'Step 1 of 3: Expand brackets and combine like terms. Write the simplified equation.');
}

document.querySelector('#step-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = document.querySelector('#step-check');
  const feedback = document.querySelector('#step-feedback');
  button.disabled = true;
  button.textContent = 'Checking step…';
  try {
    const response = await fetch('/learning/step', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        equation: activeEquation,
        stage: tutorStage,
        submitted_equation: document.querySelector('#step-equation').value,
        coaching_mode: activeTutorMode,
        attempt_number: Math.min(stageAttemptCount + 1, 20),
        session_id: learningSessionId,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not check your step.');
    updateLearningMemory(data.learning_session);
    if (!data.correct) stageAttemptCount = Math.min(stageAttemptCount + 1, 20);
    feedback.hidden = false;
    const source = data.hint_source === 'live_ai' ? 'Personalised AI hint' :
      data.hint_source === 'symbolic_fallback' ? 'Verified offline hint (Groq unavailable)' :
      data.hint_source === 'adaptive_scaffold' ? 'Adaptive learning support' : 'Hint';
    const supportNotice = !data.correct && data.support_level > 1
      ? (data.support_level === 2 ? 'Let’s focus more closely on this step.' : 'Let’s pause and try a smaller example.')
      : '';
    feedback.textContent = [data.feedback, supportNotice, data.hint ? `${source}: ${data.hint}` : ''].filter(Boolean).join('\n');
    if (!data.correct && activeTutorMode === 'groq') {
      const events = document.querySelector('#events');
      const item = document.createElement('li');
      const heading = document.createElement('strong');
      heading.textContent = data.hint_source === 'live_ai'
        ? 'adaptive teaching · respond_to_mistake: '
        : data.hint_source === 'adaptive_scaffold' ? 'teaching · adjust_support: '
        : 'reviewer · offline_fallback: ';
      item.append(heading, document.createTextNode(data.hint_source === 'live_ai'
        ? `Personalised guidance generated for step ${tutorStage + 1}.`
        : data.hint_source === 'adaptive_scaffold'
        ? `Switched to ${data.support_strategy} after ${stageAttemptCount} unsuccessful attempts at this step.`
        : 'SymPy feedback remains available while Groq is unavailable.'));
      events.appendChild(item);
      set('event-count', String(events.children.length));
    }
    tutorNextStage = data.next_stage;
    if (data.correct) {
      const list = document.querySelector('#revealed-steps');
      const item = document.createElement('li');
      const equation = document.createElement('strong');
      equation.textContent = data.revealed_step;
      const explanation = document.createElement('small');
      explanation.textContent = data.step_reason;
      item.append(equation, explanation);
      list.appendChild(item);
      document.querySelector('#step-form').hidden = true;
      if (data.complete) {
        feedback.textContent += '\nAll three steps checked. Next, explain the ideas behind your method.';
        if (data.final_check) feedback.textContent += `\n${data.final_check}`;
        try { await showConcept(0); }
        catch (error) { feedback.textContent += `\nConcept check unavailable: ${error.message}`; }
      } else {
        const next = document.querySelector('#step-next');
        next.hidden = false;
        next.dataset.prompt = data.next_prompt;
      }
    }
  } catch (error) {
    feedback.hidden = false;
    feedback.textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = 'Check this step →';
  }
});

document.querySelector('#step-next').addEventListener('click', (event) => {
  if (tutorNextStage === null) return;
  tutorStage = tutorNextStage;
  tutorNextStage = null;
  stageAttemptCount = 0;
  set('step-prompt', event.currentTarget.dataset.prompt);
  document.querySelector('#step-form').hidden = false;
  document.querySelector('#step-equation').value = '';
  document.querySelector('#step-feedback').hidden = true;
  event.currentTarget.hidden = true;
  document.querySelector('#step-equation').focus();
});

function resetTransfer() {
  transferStage = 0;
  pendingNextStage = null;
  document.querySelector('#transfer-form').hidden = false;
  document.querySelector('#transfer-feedback').hidden = true;
  document.querySelector('#next-transfer').hidden = true;
  document.querySelector('#transfer-answer').value = '';
  document.querySelector('#transfer-reasoning').value = '';
}

document.querySelector('#transfer-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const check = document.querySelector('#check-transfer');
  const feedback = document.querySelector('#transfer-feedback');
  check.disabled = true;
  check.textContent = 'Checking…';
  try {
    const response = await fetch('/learning/transfer', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        stage: transferStage,
        proposed_answer: document.querySelector('#transfer-answer').value,
        reasoning: document.querySelector('#transfer-reasoning').value,
        coaching_mode: activeTutorMode,
        session_id: learningSessionId,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not check the answer.');
    updateLearningMemory(data.learning_session);
    feedback.hidden = false;
    feedback.textContent = data.feedback + (data.hint ? `\nHint: ${data.hint}` : '') +
      (data.answer_correct ? `\nReasoning review: ${data.review_source === 'groq_with_local_guard' ? 'AI review + local safeguards' : 'Local rubric'}. This is evidence of reasoning, not proof of mastery.` : '');
    pendingNextStage = data.next_stage;
    if (data.correct) {
      document.querySelector('#transfer-form').hidden = true;
      if (data.practice_complete) {
        feedback.textContent += '\nBoth answers and their explanations met the current checks. That is encouraging evidence, not proof of mastery.';
      } else {
        const next = document.querySelector('#next-transfer');
        next.hidden = false;
        next.textContent = 'Try the next challenge →';
        next.dataset.question = data.next_question;
      }
    }
  } catch (error) {
    feedback.hidden = false;
    feedback.textContent = error.message;
  } finally {
    check.disabled = false;
    check.textContent = 'Check my attempt ↗';
  }
});

document.querySelector('#next-transfer').addEventListener('click', (event) => {
  if (pendingNextStage === null) return;
  const question = event.currentTarget.dataset.question;
  transferStage = pendingNextStage;
  pendingNextStage = null;
  set('transfer', question);
  document.querySelector('#transfer-form').hidden = false;
  document.querySelector('#transfer-answer').value = '';
  document.querySelector('#transfer-reasoning').value = '';
  document.querySelector('#transfer-feedback').hidden = true;
  event.currentTarget.hidden = true;
  document.querySelector('#transfer-answer').focus();
});

document.querySelector('#example').addEventListener('click', () => {
  document.querySelector('#equation').value = '2(x+3)=14';
  document.querySelector('#attempt').value = 'I tried dividing by 2, but I am not sure what to do with the bracket.';
});

mode.addEventListener('change', () => {
  modeHint.textContent = mode.value === 'coach'
    ? 'Guided coaching generates checked algebra steps and responds to the answer you entered. It does not call an LLM.'
    : mode.value === 'demo'
    ? 'This explicitly simulated demo deliberately shows an error and correction between agents.'
    : 'Live mode calls GroqCloud. Free-tier capacity and rate limits apply; Guided coaching remains available offline.';
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  submit.disabled = true;
  submit.textContent = 'Thinking through your method…';
  const selectedMode = mode.value;
  try {
    const endpoint = selectedMode === 'coach' ? '/learning/coach' : selectedMode === 'demo' ? '/learning/demo' : '/learning/run';
    const response = await fetch(endpoint, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ equation: document.querySelector('#equation').value.trim(), student_attempt: document.querySelector('#attempt').value.trim() }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
    learningSessionId = null;
    document.querySelector('#learning-memory').hidden = true;
    if (['groq', 'rule_based'].includes(data.mode) && data.status === 'verified') {
      try {
        const sessionResponse = await fetch('/learning/session', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({subject: 'algebra', problem: document.querySelector('#equation').value.trim()}),
        });
        if (sessionResponse.ok) {
          const session = await sessionResponse.json();
          learningSessionId = session.session_id;
          window.dispatchEvent(new CustomEvent('methodmind:learning-session',
            {detail: {sessionId: learningSessionId, subject: 'algebra'}}));
          updateLearningMemory(session);
        }
      } catch (_) { /* Older backend: existing tutoring remains usable. */ }
    }
    empty.hidden = true;
    result.hidden = false;
    const badge = document.querySelector('#result-badge');
    badge.textContent = data.status === 'verified' ?
      (data.mode === 'rule_based' ? '✓ PROBLEM CHECKED' : data.mode === 'groq' ? '✓ AI GUIDANCE CHECKED' : '✓ VERIFIED ANSWER') :
      (data.status || 'NEEDS INPUT').toUpperCase();
    badge.style.background = data.status === 'verified' ? '#e7f6ef' : '#fff2dc';
    badge.style.color = data.status === 'verified' ? '#22896a' : '#986524';
    set('model-badge', data.mode === 'mock' ? 'SIMULATED DEMO' : data.mode === 'rule_based' ? 'OFFLINE COACH' : 'LIVE GROQ');
    set('diagnosis', data.diagnosis || data.question || 'We need a little more of your thinking to get started.');
    set('explanation', data.explanation || 'No verified explanation is available yet.');
    const coaching = ['rule_based', 'groq'].includes(data.mode) && data.status === 'verified';
    activeTutorMode = data.mode === 'groq' ? 'groq' : 'coach';
    resetTutor(document.querySelector('#equation').value.trim(), coaching);
    document.querySelector('#transfer-wrap').hidden = !data.transfer_question || coaching;
    document.querySelector('#concept-wrap').hidden = true;
    if (data.transfer_question) { set('transfer', data.transfer_question); resetTransfer(); }
    set('disclaimer', data.disclaimer || '');
    const events = document.querySelector('#events');
    events.replaceChildren();
    for (const item of data.events || []) {
      const li = document.createElement('li');
      const strong = document.createElement('strong');
      strong.textContent = `${item.agent} · ${item.action}: `;
      li.append(strong, document.createTextNode(item.detail || ''));
      events.appendChild(li);
    }
    set('event-count', String((data.events || []).length));
  } catch (error) {
    learningSessionId = null;
    document.querySelector('#learning-memory').hidden = true;
    empty.hidden = true;
    result.hidden = false;
    set('result-badge', 'NOT AVAILABLE');
    set('model-badge', selectedMode === 'run' ? 'LIVE GROQ' : selectedMode === 'coach' ? 'OFFLINE COACH' : 'SIMULATED DEMO');
    set('diagnosis', error.message);
    set('explanation', selectedMode === 'run' ? 'Groq may be busy or rate-limited. Switch to Guided coaching · offline to keep learning.' : 'Check that your FastAPI server is running and your equation is supported.');
    document.querySelector('#transfer-wrap').hidden = true;
    document.querySelector('#concept-wrap').hidden = true;
    document.querySelector('#steps-wrap').hidden = true;
    document.querySelector('#events').replaceChildren();
    set('event-count', '0');
    set('disclaimer', 'No verified result was produced.');
  } finally {
    submit.disabled = false;
    submit.replaceChildren(document.createTextNode('Explore my method '));
    const arrow = document.createElement('span'); arrow.textContent = '→'; submit.appendChild(arrow);
  }
});

// Life Sciences uses the same session-based learning pathway with a specialist
// rubric. The established mathematics workflow above remains unchanged.
const subjectSelect = document.querySelector('#subject-select');
let biologySessionId = null;
let biologyActivity = 'guided_practice';
let biologyStage = 0;
let biologyAttempts = 0;

subjectSelect.addEventListener('change', () => {
  const biology = subjectSelect.value === 'biology';
  form.hidden = biology;
  document.querySelector('#biology-intro').hidden = !biology;
  document.querySelector('#biology-result').hidden = true;
  result.hidden = true;
  empty.hidden = false;
  document.querySelector('.ask-card .card-title p').textContent = biology
    ? 'Investigate why photosynthesis rates change.'
    : 'Type any supported linear equation. No camera needed.';
  biologySessionId = null;
});

function biologyStatus(session) {
  window.dispatchEvent(new CustomEvent('methodmind:checked-evidence', {detail: {subject: 'biology'}}));
  const labels = {guided_practice: 'Guided scenarios', concept_check: 'Check the reasoning',
    transfer: 'Apply to a new situation', reflect: 'Reflect'};
  set('biology-memory', `Learning colleague · ${labels[session.state]} · ` +
    `${session.evidence.attempts} attempts · ${session.evidence.hints_received} hints. ${session.guidance}`);
}

async function loadBiologyActivity() {
  const response = await fetch(`/learning/biology/activity/${biologyActivity}/${biologyStage}`);
  const item = await response.json();
  if (!response.ok) throw new Error(item.detail || 'Could not load Life Sciences activity.');
  document.querySelector('#biology-form').hidden = false;
  document.querySelector('#biology-feedback').hidden = true;
  document.querySelector('#biology-next').hidden = true;
  const titles = {guided_practice: 'Guided scenario', concept_check: 'Concept check', transfer: 'Transfer challenge'};
  set('biology-progress', `${titles[biologyActivity]} ${biologyStage + 1} of ${item.total}`);
  set('biology-question', item.question);
  const options = document.querySelector('#biology-choices');
  options.replaceChildren();
  item.choices.forEach((choice, index) => {
    const label = document.createElement('label');
    const radio = document.createElement('input');
    radio.type = 'radio'; radio.name = 'biology-choice'; radio.value = String(index); radio.required = true;
    label.append(radio, document.createTextNode(choice));
    options.appendChild(label);
  });
  const reasoningRequired = item.requires_reasoning;
  const reasoning = document.querySelector('#biology-reasoning');
  reasoning.hidden = !reasoningRequired;
  reasoning.required = reasoningRequired;
  reasoning.value = '';
  document.querySelector('#biology-reasoning-label').hidden = !reasoningRequired;
  biologyAttempts = 0;
}

document.querySelector('#biology-start').addEventListener('click', async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    const response = await fetch('/learning/session', {method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({subject: 'biology', problem: 'photosynthesis_limiting_factors'})});
    const session = await response.json();
    if (!response.ok) throw new Error(session.detail || 'Could not start Life Sciences.');
    biologySessionId = session.session_id;
    window.dispatchEvent(new CustomEvent('methodmind:learning-session',
      {detail: {sessionId: biologySessionId, subject: 'biology'}}));
    biologyActivity = 'guided_practice'; biologyStage = 0;
    result.hidden = true; empty.hidden = true;
    document.querySelector('#biology-result').hidden = false;
    biologyStatus(session);
    await loadBiologyActivity();
  } catch (error) {
    alert(`Life Sciences unavailable: ${error.message}`);
  } finally { button.disabled = false; }
});

document.querySelector('#biology-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const selected = document.querySelector('input[name="biology-choice"]:checked');
  if (!selected || !biologySessionId) return;
  const button = document.querySelector('#biology-check');
  const feedback = document.querySelector('#biology-feedback');
  button.disabled = true;
  try {
    biologyAttempts += 1;
    const response = await fetch('/learning/biology/check', {method: 'POST',
      headers: {'Content-Type': 'application/json'}, body: JSON.stringify({
        session_id: biologySessionId, activity: biologyActivity, stage: biologyStage,
        choice: Number(selected.value), reasoning: document.querySelector('#biology-reasoning').value,
        attempt_number: Math.min(biologyAttempts, 20),
      })});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not check Life Sciences response.');
    biologyStatus(data.learning_session);
    feedback.hidden = false;
    feedback.textContent = [data.feedback, data.hint ? `Hint: ${data.hint}` : ''].filter(Boolean).join('\n');
    if (data.correct) {
      document.querySelector('#biology-form').hidden = true;
      const next = document.querySelector('#biology-next');
      next.hidden = false;
      if (data.learning_session.state === 'reflect') {
        feedback.textContent += '\nYou have completed the checks. What idea would you use on a fresh graph or experiment?';
        next.hidden = true;
      }
    }
  } catch (error) {
    feedback.hidden = false; feedback.textContent = error.message;
  } finally { button.disabled = false; }
});

document.querySelector('#biology-next').addEventListener('click', async () => {
  try {
    if (biologyActivity === 'guided_practice' && biologyStage === 2) {
      biologyActivity = 'concept_check'; biologyStage = 0;
    } else if (biologyActivity === 'concept_check' && biologyStage === 1) {
      biologyActivity = 'transfer'; biologyStage = 0;
    } else { biologyStage += 1; }
    await loadBiologyActivity();
  } catch (error) {
    const feedback = document.querySelector('#biology-feedback');
    feedback.hidden = false; feedback.textContent = error.message;
  }
});
