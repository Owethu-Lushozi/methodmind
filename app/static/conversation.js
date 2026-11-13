/* Milestone 18C — activity session linkage and server-originated evidence. */
(() => {
  const form = document.querySelector('#conversation-form');
  const input = document.querySelector('#conversation-input');
  const sendButton = document.querySelector('#conversation-send');
  const messages = document.querySelector('#conversation-messages');
  const suggestions = document.querySelector('#conversation-suggestions');
  const status = document.querySelector('#conversation-status');
  const practice = document.querySelector('#conversation-practice');
  let conversationId = null;
  let activeHistory = [];
  let currentTitle = "New conversation";
  let pendingSubject = null;
  let linkedSubject = null;
  let syncInFlight = false;

  async function post(path, data) {
    const response = await fetch(path, {method: 'POST',
      headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)});
    const value = await response.json();
    if (!response.ok) throw new Error(value.detail || 'Could not connect the learning activity.');
    return value;
  }

  window.addEventListener('methodmind:learning-session', async (event) => {
    if (!conversationId || pendingSubject !== event.detail.subject) return;
    try {
      await post('/conversation/link-session', {
        conversation_id: conversationId, learning_session_id: event.detail.sessionId});
      linkedSubject = event.detail.subject;
      pendingSubject = null;
      status.textContent = 'Checked activity linked. I can now respond to feedback recorded by its checker.';
    } catch (error) {
      status.textContent = `The activity is still available, but chat linking failed: ${error.message}`;
    }
  });

  window.addEventListener('methodmind:checked-evidence', async (event) => {
    if (event.detail.subject !== linkedSubject || syncInFlight || !conversationId) return;
    syncInFlight = true;
    try {
      const data = await post('/conversation/sync-evidence', {conversation_id: conversationId});
      if (data.updated) {
        bubble('assistant', data.reply);
        status.textContent = `Connected to checked ${data.checked_evidence.subject} activity · ${data.checked_evidence.attempts} attempts recorded. Chat itself did not grade an answer.`;
      }
    } catch (error) {
      status.textContent = `Checked activity remains usable. Couldn't sync to chat: ${error.message}`;
    } finally { syncInFlight = false; }
  });

  function bubble(role, text) {
    const item = document.createElement('div');
    item.className = `conversation-bubble ${role === 'user' ? 'student' : 'assistant'}`;
    item.textContent = text;
    messages.appendChild(item);
    if (role === "user" && currentTitle === "New conversation") { currentTitle = text.slice(0, 38); updateHistory(); }
    messages.scrollTop = messages.scrollHeight;
  }

  function suggestionButtons(items) {
    suggestions.replaceChildren();
    (items || []).forEach((choice) => {
      const button = document.createElement('button');
      button.type = 'button'; button.textContent = choice;
      button.addEventListener('click', () => {
        if (sendButton.disabled) return;
        input.value = choice;
        form.requestSubmit();
      });
      suggestions.appendChild(button);
    });
  }

  function practiceOffer(offer) {
    practice.replaceChildren();
    if (!offer || !['algebra', 'biology'].includes(offer.subject_id) ||
        offer.activity !== 'guided_practice') return;
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = `${offer.label} →`;
    button.addEventListener('click', () => {
      pendingSubject = offer.subject_id;
      const subject = document.querySelector('#subject-select');
      subject.value = offer.subject_id;
      subject.dispatchEvent(new Event('change', {bubbles: true}));
      window.MethodMindUI?.openWorkspace();
      const card = document.querySelector('.ask-card');
      card.scrollIntoView({behavior: 'smooth', block: 'start'});
      if (offer.subject_id === 'biology') {
        // Learner explicitly starts the curated session; this never submits an answer.
        document.querySelector('#biology-start').click();
      } else {
        document.querySelector('#equation').focus({preventScroll: true});
      }
      status.textContent = 'Checked activity opened below. Submit your own work there to receive verified feedback.';
    });
    practice.appendChild(button);
  }

  function updateHistory() {
    const list = document.querySelector('#chat-history');
    list.replaceChildren();
    activeHistory.forEach((entry) => {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'history-entry';
      button.textContent = entry.title || 'Conversation';
      if (entry.id === conversationId) button.classList.add('selected');
      button.addEventListener('click', () => restore(entry.id));
      list.appendChild(button);
    });
  }
  async function restore(id) {
    if (id === conversationId) { window.MethodMindUI?.openChat(); return; }
    try {
      const response = await fetch(`/conversation/${encodeURIComponent(id)}`);
      if (!response.ok) throw new Error('This conversation is no longer available on the server.');
      const data = await response.json();
      conversationId = id;
      currentTitle = activeHistory.find((x) => x.id === id)?.title || 'Conversation';
      pendingSubject = null; linkedSubject = null;
      messages.replaceChildren(); suggestionButtons([]); practiceOffer(null);
      data.messages.forEach((item) => bubble(item.role, item.text));
      updateHistory(); window.MethodMindUI?.openChat();
      status.textContent = 'Conversation restored. Checked activity links are not restored automatically.';
    } catch (error) { status.textContent = error.message; }
  }
  async function start() {
    const response = await fetch('/conversation/start', {method: 'POST'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Conversation could not start.');
    conversationId = data.conversation_id;
    currentTitle = 'New conversation';
    activeHistory.unshift({id: conversationId, title: currentTitle});
    activeHistory = activeHistory.slice(0, 15);
    updateHistory();
    pendingSubject = null; linkedSubject = null;
    practiceOffer(null);
    messages.replaceChildren();
    data.messages.forEach((item) => bubble(item.role, item.text));
    window.MethodMindUI?.openChat();
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message || !conversationId) return;
    sendButton.disabled = true;
    input.disabled = true;
    suggestionButtons([]);
    practiceOffer(null);
    input.value = '';
    bubble('user', message);
    const entry = activeHistory.find((x) => x.id === conversationId);
    if (entry) entry.title = currentTitle;
    updateHistory();
    status.textContent = 'MethodMind is considering your question…';
    try {
      const response = await fetch('/conversation/message', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({conversation_id: conversationId, message}),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Conversation unavailable.');
      bubble('assistant', data.reply);
      suggestionButtons(data.suggestions);
      practiceOffer(data.practice_offer);
      status.textContent = `${data.source === 'groq' ? 'Live AI conversation' : 'Offline topic guidance'} · ${data.subject || 'Subject not confirmed'}${data.topic ? ` · ${data.topic}` : ''}. Chat is not graded; checked activities are separate.`;
    } catch (error) {
      bubble('assistant', `I couldn't process that just now: ${error.message}. Your verified learning activities below are still available.`);
      status.textContent = 'Conversation temporarily unavailable.';
    } finally {
      sendButton.disabled = false;
      input.disabled = false;
      input.focus();
    }
  });

  document.querySelector('#new-chat')?.addEventListener('click', () => start().catch(error => {status.textContent = error.message;}));
  start().catch((error) => {
    status.textContent = `Could not start conversation: ${error.message}. The learning activities below are still available.`;
    input.disabled = true;
    sendButton.disabled = true;
  });
})();
