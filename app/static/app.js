const form = document.querySelector('#learning-form');
const submit = document.querySelector('#submit');
const mode = document.querySelector('#mode');
const modeHint = document.querySelector('#mode-hint');
const empty = document.querySelector('#empty');
const result = document.querySelector('#result');
const set = (id, value) => { document.getElementById(id).textContent = value ?? 'Not available'; };
let transferStage = 0;
let pendingNextStage = null;

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
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not check the answer.');
    feedback.hidden = false;
    feedback.textContent = data.feedback + (data.hint ? `\nHint: ${data.hint}` : '');
    pendingNextStage = data.next_stage;
    if (data.correct) {
      document.querySelector('#transfer-form').hidden = true;
      if (data.practice_complete) {
        feedback.textContent += '\nBoth practice questions passed. This shows successful answer transfer, but does not prove conceptual mastery.';
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
    : 'Live mode calls Gemini. Google may return 503 while capacity is limited; choose Guided coaching for reliable offline help.';
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
    empty.hidden = true;
    result.hidden = false;
    const badge = document.querySelector('#result-badge');
    badge.textContent = data.status === 'verified' ? '✓ VERIFIED ANSWER' : (data.status || 'NEEDS INPUT').toUpperCase();
    badge.style.background = data.status === 'verified' ? '#e7f6ef' : '#fff2dc';
    badge.style.color = data.status === 'verified' ? '#22896a' : '#986524';
    set('model-badge', data.mode === 'mock' ? 'SIMULATED DEMO' : data.mode === 'rule_based' ? 'OFFLINE COACH' : 'LIVE GEMINI');
    set('diagnosis', data.diagnosis || data.question || 'We need a little more of your thinking to get started.');
    set('explanation', data.explanation || 'No verified explanation is available yet.');
    document.querySelector('#transfer-wrap').hidden = !data.transfer_question;
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
    empty.hidden = true;
    result.hidden = false;
    set('result-badge', 'NOT AVAILABLE');
    set('model-badge', selectedMode === 'run' ? 'LIVE GEMINI' : selectedMode === 'coach' ? 'OFFLINE COACH' : 'SIMULATED DEMO');
    set('diagnosis', error.message);
    set('explanation', selectedMode === 'run' ? 'Gemini may be busy. Switch to Guided demo to explore the workflow without relying on Google.' : 'Check that your FastAPI server is running and your equation is supported.');
    document.querySelector('#transfer-wrap').hidden = true;
    document.querySelector('#events').replaceChildren();
    set('event-count', '0');
    set('disclaimer', 'No verified result was produced.');
  } finally {
    submit.disabled = false;
    submit.replaceChildren(document.createTextNode('Explore my method '));
    const arrow = document.createElement('span'); arrow.textContent = '→'; submit.appendChild(arrow);
  }
});
