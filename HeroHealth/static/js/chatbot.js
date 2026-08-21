(() => {
  'use strict';

  const root = document.querySelector('.hero-chat-widget') || document.querySelector('.hero-chat-page');
  if (!root) return;

  const $ = (s) => root.querySelector(s);
  const form = $('#chatForm');
  const input = $('#chatInput');
  const messages = $('#chatMessages');
  const status = $('#chatStatus');

  const state = {
    language: 'en',
    busy: false,
    recognition: null,
    utterance: null
  };

  const labels = {
    en: {
      welcome: 'Hello! I am Hero AI. I can provide general health information and guidance, but I cannot diagnose conditions or prescribe medicine. What would you like to know?',
      placeholder: 'Ask a health question...',
      thinking: 'Hero AI is thinking...'
    },
    ne: {
      welcome: 'नमस्ते! म Hero AI हुँ। म तपाईंलाई सामान्य स्वास्थ्य जानकारी र मार्गदर्शन प्रदान गर्न सक्छु। म रोगको निदान वा औषधि लेख्न सक्दिनँ। तपाईंलाई के बारेमा जानकारी चाहिएको छ?',
      placeholder: 'स्वास्थ्यसम्बन्धी प्रश्न सोध्नुहोस्...',
      thinking: 'Hero AI सोच्दैछ...'
    }
  };

  const csrf = () => form.querySelector('[name=csrfmiddlewaretoken]').value;
  const announce = (text) => { status.textContent = text; };
  const scroll = () => { messages.scrollTop = messages.scrollHeight; };
  const setText = (node, text) => { node.textContent = text; return node; };

  // Simple Markdown link and bold text parser with XSS protection
  function parseMarkdown(text) {
    let escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');

    // Bold text: **text** -> <strong>text</strong>
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Inline links: [anchor](url) -> <a href="url" class="chat-link">anchor</a>
    escaped = escaped.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" class="chat-link">$1</a>');

    // Newlines -> HTML line breaks
    escaped = escaped.replace(/\n/g, '<br>');

    return escaped;
  }

  function action(icon, label, callback) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'hero-message-action';
    b.title = label;
    b.setAttribute('aria-label', label);
    b.innerHTML = `<i class="fa-solid ${icon}" aria-hidden="true"></i>`;
    b.addEventListener('click', callback);
    return b;
  }

  function render(role, text, emergency = false) {
    const item = document.createElement('article');
    item.className = `hero-message hero-message--${role}${emergency ? ' hero-message--emergency' : ''}`;

    const bubble = document.createElement('div');
    bubble.className = 'hero-message-bubble';

    const senderLabel = document.createElement('strong');
    senderLabel.textContent = role === 'assistant' ? 'Hero AI' : 'You';
    bubble.append(senderLabel);

    const bodyParagraph = document.createElement('p');
    if (role === 'assistant') {
      bodyParagraph.innerHTML = parseMarkdown(text);
    } else {
      bodyParagraph.textContent = text;
    }
    bubble.append(bodyParagraph);

    if (role === 'assistant') {
      const controls = document.createElement('div');
      controls.className = 'hero-message-actions';
      controls.append(
        action('fa-volume-high', 'Read response aloud or stop reading', () => speak(text)),
        action('fa-copy', 'Copy response', () => copy(text))
      );
      bubble.append(controls);
    }

    item.append(bubble);
    messages.append(item);
    scroll();
    return item;
  }

  async function request(url, options = {}) {
    let response;
    try {
      response = await fetch(url, {
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': csrf(),
          ...(options.headers || {})
        },
        ...options
      });
    } catch (err) {
      console.error("Fetch Network Error:", err);
      throw new Error('Network error: Unable to reach the server. Please check your connection.');
    }

    let data = {};
    const text = await response.text();
    try {
      data = JSON.parse(text);
    } catch (e) {
      console.error("Failed to parse JSON response:", text);
      throw new Error(`Server returned status ${response.status}. Please check your console/server logs.`);
    }

    if (!response.ok || !data.success) {
      console.error("Server error response:", response.status, data);
      throw new Error(data.error || `Server error (Status ${response.status}).`);
    }
    return data;
  }

  function updateCounter() {
    $('#chatCounter').textContent = `${input.value.length} / 1200`;
  }

  function setBusy(busy) {
    state.busy = busy;
    input.disabled = busy;
    $('#sendButton').disabled = busy;
  }

  async function sendMessage(value = input.value.trim()) {
    if (!value || state.busy) return;
    render('user', value);
    input.value = '';
    updateCounter();
    setBusy(true);

    const pending = render('assistant', labels[state.language].thinking);
    pending.classList.add('hero-message--pending');

    try {
      const data = await request(root.dataset.messageUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: value, language: state.language })
      });
      pending.remove();
      render('assistant', data.reply, data.is_emergency);
      announce('Hero AI replied.');
    } catch (error) {
      pending.remove();
      render('assistant', error.message);
      announce(error.message);
    } finally {
      setBusy(false);
      input.focus();
    }
  }

  async function loadHistory() {
    try {
      const data = await request(root.dataset.historyUrl);
      if (data.messages.length) {
        data.messages.forEach((m) => render(m.role, m.content));
      } else {
        render('assistant', labels[state.language].welcome);
      }
    } catch {
      render('assistant', labels[state.language].welcome);
    }
  }

  async function newChat() {
    if (state.busy) return;
    try {
      await request(root.dataset.resetUrl, { method: 'POST' });
      messages.replaceChildren();
      render('assistant', labels[state.language].welcome);
      announce('New chat started.');
    } catch (error) {
      announce(error.message);
    }
  }

  async function copy(text) {
    try {
      await navigator.clipboard.writeText(text);
      announce('Response copied.');
    } catch {
      announce('Unable to copy this response.');
    }
  }

  function speak(text) {
    if (!('speechSynthesis' in window)) {
      return announce('Speech output is not supported in this browser.');
    }
    if (state.utterance) {
      speechSynthesis.cancel();
      state.utterance = null;
      return announce('Reading stopped.');
    }
    const utterance = new SpeechSynthesisUtterance(text);
    if (state.language === 'ne') {
      const voices = speechSynthesis.getVoices();
      // Try to find a native Nepali voice
      let voice = voices.find(v => v.lang.startsWith('ne'));
      if (!voice) {
        // Fallback to Hindi voice which sounds very close and is widely pre-installed
        voice = voices.find(v => v.lang.startsWith('hi'));
      }
      if (voice) {
        utterance.voice = voice;
        utterance.lang = voice.lang;
      } else {
        utterance.lang = 'ne-NP';
      }
    } else {
      utterance.lang = 'en-US';
    }

    utterance.onend = () => {
      state.utterance = null;
      announce('Reading finished.');
    };
    utterance.onerror = () => {
      state.utterance = null;
      announce(state.language === 'ne' ? 'नेपाली आवाज यस उपकरणमा उपलब्ध नहुन सक्छ।' : 'Speech output is unavailable.');
    };
    state.utterance = utterance;
    speechSynthesis.speak(utterance);
    announce('Reading response aloud. Select the speaker again to stop.');
  }

  function setLanguage(language) {
    state.language = language;
    root.querySelectorAll('[data-language]').forEach((b) => {
      const active = b.dataset.language === language;
      b.classList.toggle('active', active);
      b.setAttribute('aria-pressed', String(active));
    });
    input.placeholder = labels[language].placeholder;
  }

  function setupVoice() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const button = $('#voiceButton');
    const voiceStatus = $('#voiceStatus');

    if (!Recognition) {
      button.disabled = true;
      voiceStatus.textContent = 'Voice input not supported.';
      return;
    }

    button.addEventListener('click', () => {
      if (state.recognition) return state.recognition.stop();
      const r = new Recognition();
      state.recognition = r;
      r.lang = state.language === 'ne' ? 'ne-NP' : 'en-US';
      r.interimResults = false;
      r.maxAlternatives = 1;

      r.onstart = () => {
        button.classList.add('recording');
        button.setAttribute('aria-label', 'Stop voice input');
        voiceStatus.textContent = state.language === 'ne' ? 'सुन्दैछ...' : 'Listening...';
      };
      r.onresult = (e) => {
        input.value = e.results[0][0].transcript;
        updateCounter();
        voiceStatus.textContent = state.language === 'ne' ? 'रेकर्डिङ रोकियो।' : 'Recording stopped.';
      };
      r.onerror = (e) => {
        console.error("Speech Recognition Error:", e);
        if (e.error === 'not-allowed') {
          voiceStatus.textContent = 'Microphone permission denied. Enable microphone access in browser settings.';
        } else if (e.error === 'network') {
          voiceStatus.textContent = 'Network error during speech recognition. Ensure internet access.';
        } else if (e.error === 'no-speech') {
          voiceStatus.textContent = 'No speech detected. Please try again.';
        } else {
          voiceStatus.textContent = `Voice recognition failed (Error: ${e.error}).`;
        }
      };
      r.onend = () => {
        state.recognition = null;
        button.classList.remove('recording');
        button.setAttribute('aria-label', 'Start voice input');
      };
      r.start();
    });
  }

  // Toggle Visibility for Floating Widget
  const trigger = document.getElementById('chatTriggerBtn');
  const windowEl = document.getElementById('chatWindow');
  const closeBtn = document.getElementById('closeChatBtn');

  if (trigger && windowEl) {
    trigger.addEventListener('click', () => {
      windowEl.classList.toggle('chat-window-hidden');
      if (!windowEl.classList.contains('chat-window-hidden')) {
        input.focus();
        scroll();
      }
    });
  }
  if (closeBtn && windowEl) {
    closeBtn.addEventListener('click', () => {
      windowEl.classList.add('chat-window-hidden');
    });
  }

  // Setup other listeners
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    sendMessage();
  });

  input.addEventListener('input', updateCounter);

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  root.querySelectorAll('[data-language]').forEach((b) => {
    b.addEventListener('click', () => setLanguage(b.dataset.language));
  });

  $('#newChatButton').addEventListener('click', newChat);

  root.querySelectorAll('[data-prompt]').forEach((b) => {
    b.addEventListener('click', () => {
      input.value = b.dataset.prompt;
      updateCounter();
      input.focus();
    });
  });

  setupVoice();
  loadHistory();
})();
