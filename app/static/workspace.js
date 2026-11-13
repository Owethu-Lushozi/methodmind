/* Milestone 19: presentation-only application shell. Existing learning handlers are untouched. */
(() => {
  const body = document.body;
  const chat = document.querySelector('.conversation-card');
  const chatHome = chat.parentElement;
  const activity = document.querySelector('#activity-layout');
  const slot = document.querySelector('#workspace-chat-slot');
  const toolbar = document.querySelector('#workspace-toolbar');
  const toggle = document.querySelector('#chat-panel-toggle');
  const saved = localStorage.getItem('methodmind-theme');
  if (saved === 'dark') body.dataset.theme = 'dark';
  const themeButton = document.querySelector('#theme-toggle');
  function syncTheme() {
    themeButton.textContent = body.dataset.theme === 'dark' ? '☀ Light mode' : '☾ Dark mode';
    themeButton.setAttribute('aria-pressed', String(body.dataset.theme === 'dark'));
  }
  themeButton.addEventListener('click', () => {
    body.dataset.theme = body.dataset.theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('methodmind-theme', body.dataset.theme); syncTheme();
  });
  syncTheme();
  function selectNav(view) {
    document.querySelectorAll('[data-view]').forEach(button => button.classList.toggle('active', button.dataset.view === view));
  }
  function openChat() {
    if (chat.parentElement !== chatHome) chatHome.insertBefore(chat, activity);
    body.classList.remove('workspace-mode','chat-collapsed');
    toolbar.hidden = true;
    selectNav('chat');
    window.scrollTo({top:0,behavior:'smooth'});
  }
  function openWorkspace() {
    if (chat.parentElement !== slot) slot.appendChild(chat);
    body.classList.add('workspace-mode'); body.classList.remove('chat-collapsed');
    toolbar.hidden = false;
    toggle.textContent = 'Hide Mindy ◧'; toggle.setAttribute('aria-expanded','true');
    selectNav('workspace');
    window.scrollTo({top:0,behavior:'smooth'});
  }
  toggle.addEventListener('click', () => {
    const collapsed = body.classList.toggle('chat-collapsed');
    toggle.textContent = collapsed ? 'Show Mindy ◨' : 'Hide Mindy ◧';
    toggle.setAttribute('aria-expanded', String(!collapsed));
  });
  document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
    if (button.dataset.view === 'chat') openChat();
    else {
      openWorkspace();
      if (button.dataset.view === 'activities') document.querySelector('.ask-card').scrollIntoView({behavior:'smooth'});
    }
  }));
  // Focused learning: keep original form and activity state mounted, only hide the form.
  const askCard = document.querySelector('.ask-card');
  const activityLayout = document.querySelector('#activity-layout');
  const resultPanel = document.querySelector('#result');
  const biologyPanel = document.querySelector('#biology-result');
  const resultBadge = document.querySelector('#result-badge');
  const focusBar = document.createElement('div');
  focusBar.className = 'learning-focus-bar';
  focusBar.hidden = true;
  const problemLabel = document.createElement('div');
  problemLabel.className = 'learning-focus-description';
  const editButton = document.createElement('button');
  editButton.type = 'button';
  editButton.className = 'learning-edit-button';
  editButton.textContent = 'Edit problem';
  focusBar.append(problemLabel, editButton);
  activityLayout.insertBefore(focusBar, askCard);
  function focusOnLearning(subject) {
    if (!body.classList.contains('workspace-mode')) openWorkspace();
    const isBiology = subject === 'biology';
    problemLabel.textContent = isBiology
      ? 'Life Sciences · Photosynthesis'
      : 'Mathematics · ' + (document.querySelector('#equation')?.value.trim() || 'Linear equations');
    askCard.hidden = true;
    focusBar.hidden = false;
    activityLayout.classList.add('learning-focused');
    document.querySelector('.response-card')?.scrollIntoView({behavior:'smooth',block:'start'});
  }
  editButton.addEventListener('click', () => {
    askCard.hidden = false;
    focusBar.hidden = true;
    activityLayout.classList.remove('learning-focused');
    askCard.scrollIntoView({behavior:'smooth',block:'start'});
    document.querySelector('#equation')?.focus({preventScroll:true});
  });
  // The original learning handlers control the result. Never collapse on failure.
  function checkSuccessfulResult() {
    if (resultPanel && !resultPanel.hidden && resultBadge?.textContent?.includes('✓')) {
      focusOnLearning('algebra');
    } else if (biologyPanel && !biologyPanel.hidden) {
      focusOnLearning('biology');
    }
  }
  const observer = new MutationObserver(checkSuccessfulResult);
  if (resultPanel) observer.observe(resultPanel,{attributes:true,attributeFilter:['hidden']});
  if (resultBadge) observer.observe(resultBadge,{childList:true,subtree:true});
  if (biologyPanel) observer.observe(biologyPanel,{attributes:true,attributeFilter:['hidden']});
  document.querySelector('#biology-start')?.addEventListener('click', () => {
    // The biology activity becomes visible only after a successful backend response.
    setTimeout(checkSuccessfulResult, 0);
  });
  window.MethodMindUI = {openChat,openWorkspace};
  // Entering an activity directly is always a student action.
  document.querySelector('#learning-form')?.addEventListener('submit', openWorkspace);
  document.querySelector('#biology-start')?.addEventListener('click', openWorkspace);
})();
