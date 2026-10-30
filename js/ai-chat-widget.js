/**
 * ProofVoice Intelligent Campus AI Chatbot & Voice Assistant (v5)
 * Seamlessly integrates text chat, voice STT (Gnani Prisma / Web Speech API),
 * and voice TTS (Gnani Timbre / Web Speech API) with complaint lifecycle intelligence.
 */

class ProofVoiceAiAssistant {
  constructor(options = {}) {
    this.container = document.getElementById(options.containerId || 'aiAssistantWidget');
    if (!this.container) return;

    // Elements
    this.chatBody = document.getElementById('aiChatBody');
    this.textInput = document.getElementById('aiTextInput');
    this.sendBtn = document.getElementById('aiSendBtn');
    this.micBtn = document.getElementById('aiMicBtn');
    this.modeToggleText = document.getElementById('aiModeText');
    this.modeToggleVoice = document.getElementById('aiModeVoice');
    this.clearBtn = document.getElementById('aiClearChatBtn');
    this.langSelect = document.getElementById('aiVoiceLangSelect');

    // Voice Player elements
    this.voicePlayer = document.getElementById('aiVoicePlayer');
    this.playerStatus = document.getElementById('aiPlayerStatus');
    this.playPauseBtn = document.getElementById('aiPlayerPlayPause');
    this.stopAudioBtn = document.getElementById('aiPlayerStop');

    // Live Recording elements
    this.recStrip = document.getElementById('aiRecStrip');
    this.recTimer = document.getElementById('aiRecTimer');
    this.recTranscript = document.getElementById('aiRecTranscript');
    this.stopRecBtn = document.getElementById('aiStopRecBtn');
    this.cancelRecBtn = document.getElementById('aiCancelRecBtn');

    // State
    this.voiceMode = false;
    this.isRecording = false;
    this.recInterval = null;
    this.recSeconds = 0;
    this.speechRecognition = null;
    this.currentUtterance = null;
    this.currentAudioObj = null;
    this.isPlayingAudio = false;
    this.history = [];
    this.currentUser = null;

    this.init();
  }

  init() {
    this.resolveUser();

    // Event listeners
    if (this.sendBtn) {
      this.sendBtn.addEventListener('click', () => this.handleSendMessage());
    }
    if (this.textInput) {
      this.textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.handleSendMessage();
        }
      });
    }
    if (this.micBtn) {
      this.micBtn.addEventListener('click', () => this.toggleVoiceRecording());
    }
    if (this.clearBtn) {
      this.clearBtn.addEventListener('click', () => this.resetConversation());
    }
    if (this.modeToggleText) {
      this.modeToggleText.addEventListener('click', () => this.setMode(false));
    }
    if (this.modeToggleVoice) {
      this.modeToggleVoice.addEventListener('click', () => this.setMode(true));
    }
    if (this.playPauseBtn) {
      this.playPauseBtn.addEventListener('click', () => this.toggleAudioPlayback());
    }
    if (this.stopAudioBtn) {
      this.stopAudioBtn.addEventListener('click', () => this.stopAllAudio());
    }
    if (this.stopRecBtn) {
      this.stopRecBtn.addEventListener('click', () => this.stopVoiceRecording(true));
    }
    if (this.cancelRecBtn) {
      this.cancelRecBtn.addEventListener('click', () => this.stopVoiceRecording(false));
    }

    // Delegate chips click
    this.chatBody.addEventListener('click', (e) => {
      const chip = e.target.closest('.ai-chip-btn');
      if (chip) {
        const text = chip.getAttribute('data-query') || chip.textContent.trim();
        this.askQuestion(text);
      }
      const speakBtn = e.target.closest('.ai-speak-btn');
      if (speakBtn) {
        const msgIndex = speakBtn.getAttribute('data-msg-idx');
        if (msgIndex !== null && this.history[msgIndex]) {
          const item = this.history[msgIndex];
          this.speakText(item.speak_text || item.text, item.audio_base64, item.audio_content_type);
        }
      }
    });

    // Render initial greeting
    this.renderInitialGreeting();
  }

  resolveUser() {
    try {
      if (window.proofVoiceApi && typeof window.proofVoiceApi.getCurrentUser === 'function') {
        this.currentUser = window.proofVoiceApi.getCurrentUser();
      }
      if (!this.currentUser) {
        const raw = localStorage.getItem('proofvoice_session_user') || localStorage.getItem('proofvoice_auth_user');
        if (raw) this.currentUser = JSON.parse(raw);
      }
    } catch (e) {
      this.currentUser = null;
    }
  }

  setMode(voiceActive) {
    this.voiceMode = Boolean(voiceActive);
    if (this.modeToggleText && this.modeToggleVoice) {
      this.modeToggleText.classList.toggle('active', !this.voiceMode);
      this.modeToggleVoice.classList.toggle('active', this.voiceMode);
    }
    if (this.voiceMode) {
      this.textInput.placeholder = "Voice mode active — tap the microphone to speak, or type here...";
      if (window.showToast) {
        window.showToast('Voice mode active: AI will speak answers aloud.', 'info');
      }
    } else {
      this.textInput.placeholder = "Ask anything about ProofVoice or your complaints...";
      this.stopAllAudio();
    }
  }

  renderInitialGreeting() {
    const studentName = this.currentUser ? (this.currentUser.fullName || this.currentUser.full_name || 'Student') : null;
    const greeting = studentName
      ? `Hello **${studentName}**! Welcome to your ProofVoice Campus Assistant. I can help you record issues, track your tickets, check status updates, or explain institutional redressal rules. What can I help you with today?`
      : `Hello! Welcome to ProofVoice Campus Support. I can help answer questions about student registration, voice-first grievances, mandatory formal application reviews, and resolution timelines. How can I assist you today?`;

    const initialActions = this.currentUser
      ? ["What are my active complaints?", "How do I record a voice complaint?", "What does 'Under Review' mean?", "How do I update my profile?"]
      : ["How do I register with an unlisted college?", "How does voice reporting work?", "Why is application review mandatory?", "What do complaint statuses mean?"];

    this.history = [{
      role: 'assistant',
      text: greeting,
      speak_text: studentName ? `Hello ${studentName}! Welcome to ProofVoice. What can I help you with today?` : "Hello! Welcome to ProofVoice Support. How can I assist you today?",
      suggested_actions: initialActions,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }];

    this.renderChatMessages();
  }

  resetConversation() {
    this.stopAllAudio();
    this.stopVoiceRecording(false);
    this.history = [];
    this.renderInitialGreeting();
    if (window.showToast) {
      window.showToast('AI conversation restarted.', 'info');
    }
  }

  async handleSendMessage() {
    const message = (this.textInput.value || '').trim();
    if (!message) return;

    this.textInput.value = '';
    await this.askQuestion(message);
  }

  async askQuestion(questionText) {
    if (!questionText || !questionText.trim()) return;

    // Append user message
    this.history.push({
      role: 'user',
      text: questionText.trim(),
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
    this.renderChatMessages();

    // Show typing loader
    this.showTypingIndicator();

    try {
      let response;
      if (window.proofVoiceApi && typeof window.proofVoiceApi.chatWithAi === 'function') {
        response = await window.proofVoiceApi.chatWithAi(questionText, this.history, this.voiceMode);
      } else {
        response = {
          success: true,
          reply: "I am ready to assist. Please connect to the ProofVoice API to access live data.",
          speak_text: "I am ready to assist. Please connect to the ProofVoice API."
        };
      }

      this.hideTypingIndicator();

      const replyText = response.reply || response.data?.reply || "I couldn't process that query. Please try rephrasing.";
      const speakText = response.speak_text || response.data?.speak_text || replyText;
      const actions = response.suggested_actions || response.data?.suggested_actions || [];
      const audioBase64 = response.audio_base64 || response.data?.audio_base64;
      const contentType = response.audio_content_type || response.data?.audio_content_type;

      const assistantMsg = {
        role: 'assistant',
        text: replyText,
        speak_text: speakText,
        suggested_actions: actions,
        audio_base64: audioBase64,
        audio_content_type: contentType,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      this.history.push(assistantMsg);
      this.renderChatMessages();

      // If voice mode is on, auto-speak
      if (this.voiceMode) {
        this.speakText(speakText, audioBase64, contentType);
      }

    } catch (err) {
      this.hideTypingIndicator();
      console.error('AI Chat Error:', err);
      this.history.push({
        role: 'assistant',
        text: "I encountered a network issue reaching the campus AI server. If this is urgent, you can review the FAQ below or contact your Dean of Student Welfare.",
        speak_text: "I encountered an issue reaching the server. Please check the FAQ below.",
        suggested_actions: ["How do I report an issue?", "What do statuses mean?"],
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      });
      this.renderChatMessages();
    }
  }

  showTypingIndicator() {
    this.hideTypingIndicator();
    const loader = document.createElement('div');
    loader.className = 'ai-msg ai-msg-assistant';
    loader.id = 'aiTypingLoader';
    loader.innerHTML = `
      <div class="ai-bot-msg-avatar">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
          <line x1="12" y1="19" x2="12" y2="22"/>
        </svg>
      </div>
      <div class="ai-typing-indicator">
        <span style="font-size: 11.5px; color: #64748B; margin-right: 6px;">ProofVoice AI is thinking...</span>
        <div class="ai-typing-dot"></div>
        <div class="ai-typing-dot"></div>
        <div class="ai-typing-dot"></div>
      </div>
    `;
    this.chatBody.appendChild(loader);
    this.scrollToBottom();
  }

  hideTypingIndicator() {
    const existing = document.getElementById('aiTypingLoader');
    if (existing) existing.remove();
  }

  renderChatMessages() {
    if (!this.chatBody) return;
    this.chatBody.innerHTML = '';

    const userInitial = this.currentUser ? (this.currentUser.fullName || this.currentUser.full_name || 'U').charAt(0).toUpperCase() : 'U';

    this.history.forEach((msg, idx) => {
      const msgDiv = document.createElement('div');
      msgDiv.className = `ai-msg ai-msg-${msg.role}`;

      if (msg.role === 'user') {
        msgDiv.innerHTML = `
          <div class="ai-user-avatar">${userInitial}</div>
          <div class="ai-msg-bubble">
            <div>${this.escapeHtml(msg.text)}</div>
            <div style="font-size: 10px; color: rgba(255,255,255,0.7); text-align: right; margin-top: 4px;">${msg.time || ''}</div>
          </div>
        `;
      } else {
        const formattedHtml = this.formatMarkdown(msg.text);
        let chipsHtml = '';
        if (msg.suggested_actions && msg.suggested_actions.length > 0) {
          chipsHtml = `
            <div class="ai-chips-wrap">
              ${msg.suggested_actions.map(act => `<button type="button" class="ai-chip-btn" data-query="${this.escapeHtml(act)}">💡 ${this.escapeHtml(act)}</button>`).join('')}
            </div>
          `;
        }

        msgDiv.innerHTML = `
          <div class="ai-bot-msg-avatar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="22"/>
            </svg>
          </div>
          <div class="ai-msg-bubble">
            <div>${formattedHtml}</div>
            ${chipsHtml}
            <div class="ai-bubble-footer">
              <span>ProofVoice Assistant • ${msg.time || ''}</span>
              <button type="button" class="ai-speak-btn" data-msg-idx="${idx}" title="Listen to answer">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                  <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
                </svg>
                Read Aloud
              </button>
            </div>
          </div>
        `;
      }

      this.chatBody.appendChild(msgDiv);
    });

    this.scrollToBottom();
  }

  scrollToBottom() {
    if (this.chatBody) {
      this.chatBody.scrollTop = this.chatBody.scrollHeight;
    }
  }

  // Voice Input (STT) Management
  toggleVoiceRecording() {
    if (this.isRecording) {
      this.stopVoiceRecording(true);
    } else {
      this.startVoiceRecording();
    }
  }

  startVoiceRecording() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec && !navigator.mediaDevices?.getUserMedia) {
      alert("Voice input is not supported in this browser. Please type your question.");
      return;
    }

    this.stopAllAudio();
    this.isRecording = true;
    this.recSeconds = 0;
    if (this.micBtn) this.micBtn.classList.add('recording');
    if (this.recStrip) this.recStrip.classList.remove('hidden');
    if (this.recTranscript) this.recTranscript.textContent = "Listening... Speak your question now.";

    // Start timer
    if (this.recTimer) this.recTimer.textContent = "00:00 / 02:00";
    clearInterval(this.recInterval);
    this.recInterval = setInterval(() => {
      this.recSeconds++;
      const mins = String(Math.floor(this.recSeconds / 60)).padStart(2, '0');
      const secs = String(this.recSeconds % 60).padStart(2, '0');
      if (this.recTimer) this.recTimer.textContent = `${mins}:${secs} / 02:00`;

      if (this.recSeconds >= 120) {
        this.stopVoiceRecording(true);
      }
    }, 1000);

    // Initialize Web Speech Recognition
    if (SpeechRec) {
      try {
        this.speechRecognition = new SpeechRec();
        this.speechRecognition.continuous = true;
        this.speechRecognition.interimResults = true;
        this.speechRecognition.lang = this.langSelect ? this.langSelect.value : 'en-IN';

        let accumulated = '';
        this.speechRecognition.onresult = (e) => {
          let interim = '';
          for (let i = e.resultIndex; i < e.results.length; i++) {
            const trans = e.results[i][0].transcript;
            if (e.results[i].isFinal) {
              accumulated += (accumulated ? ' ' : '') + trans;
            } else {
              interim += trans;
            }
          }
          const liveText = accumulated + (interim ? ' ' + interim : '');
          if (this.recTranscript) this.recTranscript.textContent = `"${liveText}"`;
          if (this.textInput) this.textInput.value = liveText;
        };

        this.speechRecognition.onerror = (e) => {
          console.warn('Speech Recognition error:', e);
        };

        this.speechRecognition.start();
      } catch (e) {
        console.warn('Speech recognition start failed:', e);
      }
    }
  }

  stopVoiceRecording(submit = true) {
    if (!this.isRecording) return;
    this.isRecording = false;
    clearInterval(this.recInterval);

    if (this.micBtn) this.micBtn.classList.remove('recording');
    if (this.recStrip) this.recStrip.classList.add('hidden');

    if (this.speechRecognition) {
      try { this.speechRecognition.stop(); } catch (e) {}
      this.speechRecognition = null;
    }

    if (submit) {
      const recognized = (this.textInput.value || '').trim();
      if (recognized) {
        this.handleSendMessage();
      }
    } else {
      if (this.textInput) this.textInput.value = '';
    }
  }

  // Voice Output (TTS) Management
  speakText(cleanText, audioBase64 = null, contentType = 'audio/wav') {
    this.stopAllAudio();

    if (!cleanText && !audioBase64) return;

    // Show Voice Player
    if (this.voicePlayer) this.voicePlayer.classList.remove('hidden');
    if (this.playerStatus) this.playerStatus.textContent = "AI Voice: Speaking...";

    // 1. If backend returned base64 audio from Gnani Timbre TTS:
    if (audioBase64) {
      try {
        const audioSrc = `data:${contentType};base64,${audioBase64}`;
        this.currentAudioObj = new Audio(audioSrc);
        this.isPlayingAudio = true;

        this.currentAudioObj.onended = () => {
          this.isPlayingAudio = false;
          if (this.playerStatus) this.playerStatus.textContent = "AI Voice: Finished";
          setTimeout(() => {
            if (!this.isPlayingAudio && this.voicePlayer) this.voicePlayer.classList.add('hidden');
          }, 3000);
        };

        this.currentAudioObj.onerror = () => {
          this.fallbackSpeechSynthesis(cleanText);
        };

        this.currentAudioObj.play().catch(() => {
          this.fallbackSpeechSynthesis(cleanText);
        });
        return;
      } catch (err) {
        console.warn('Gnani audio playback fallback:', err);
      }
    }

    // 2. Fallback to Web Speech API SpeechSynthesis
    this.fallbackSpeechSynthesis(cleanText);
  }

  fallbackSpeechSynthesis(text) {
    if (!window.speechSynthesis) {
      if (this.voicePlayer) this.voicePlayer.classList.add('hidden');
      return;
    }

    const plain = this.stripMarkdown(text);
    if (!plain) return;

    try {
      window.speechSynthesis.cancel();
      this.currentUtterance = new SpeechSynthesisUtterance(plain);
      this.currentUtterance.rate = 1.0;
      this.currentUtterance.pitch = 1.0;
      this.currentUtterance.lang = this.langSelect ? this.langSelect.value : 'en-IN';

      // Pick Indian English voice if available
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(v => v.lang === 'en-IN' || v.name.includes('India')) ||
                             voices.find(v => v.lang.startsWith('en'));
      if (preferredVoice) {
        this.currentUtterance.voice = preferredVoice;
      }

      this.isPlayingAudio = true;
      if (this.playerStatus) this.playerStatus.textContent = "AI Voice: Speaking...";

      this.currentUtterance.onend = () => {
        this.isPlayingAudio = false;
        if (this.playerStatus) this.playerStatus.textContent = "AI Voice: Finished";
        setTimeout(() => {
          if (!this.isPlayingAudio && this.voicePlayer) this.voicePlayer.classList.add('hidden');
        }, 3000);
      };

      this.currentUtterance.onerror = () => {
        this.isPlayingAudio = false;
        if (this.voicePlayer) this.voicePlayer.classList.add('hidden');
      };

      window.speechSynthesis.speak(this.currentUtterance);
    } catch (e) {
      console.warn('SpeechSynthesis error:', e);
      if (this.voicePlayer) this.voicePlayer.classList.add('hidden');
    }
  }

  toggleAudioPlayback() {
    if (this.currentAudioObj) {
      if (this.currentAudioObj.paused) {
        this.currentAudioObj.play();
        this.isPlayingAudio = true;
        if (this.playerStatus) this.playerStatus.textContent = "AI Voice: Speaking...";
      } else {
        this.currentAudioObj.pause();
        this.isPlayingAudio = false;
        if (this.playerStatus) this.playerStatus.textContent = "AI Voice: Paused";
      }
      return;
    }

    if (window.speechSynthesis) {
      if (window.speechSynthesis.speaking) {
        if (window.speechSynthesis.paused) {
          window.speechSynthesis.resume();
          this.isPlayingAudio = true;
          if (this.playerStatus) this.playerStatus.textContent = "AI Voice: Speaking...";
        } else {
          window.speechSynthesis.pause();
          this.isPlayingAudio = false;
          if (this.playerStatus) this.playerStatus.textContent = "AI Voice: Paused";
        }
      }
    }
  }

  stopAllAudio() {
    this.isPlayingAudio = false;
    if (this.currentAudioObj) {
      try {
        this.currentAudioObj.pause();
        this.currentAudioObj.currentTime = 0;
      } catch (e) {}
      this.currentAudioObj = null;
    }
    if (window.speechSynthesis) {
      try { window.speechSynthesis.cancel(); } catch (e) {}
    }
    if (this.voicePlayer) this.voicePlayer.classList.add('hidden');
  }

  // Utilities
  escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#039;');
  }

  formatMarkdown(str) {
    if (!str) return '';
    let html = this.escapeHtml(str);

    // Markdown links: [text](url)
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color:#2563EB; text-decoration:underline;">$1</a>');

    // Bold: **text**
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Italic: *text*
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Inline code: `text`
    html = html.replace(/`([^`]+)`/g, '<code style="background:#F1F5F9; color:#0F172A; padding:2px 5px; border-radius:4px; font-size:12px;">$1</code>');

    // Bullet points
    const lines = html.split('\n');
    let inList = false;
    const formatted = [];

    for (let line of lines) {
      const bulletMatch = line.match(/^(\s*)(•|-|\*)\s+(.*)/);
      const numberMatch = line.match(/^(\s*)(\d+)\.\s+(.*)/);

      if (bulletMatch) {
        if (!inList) {
          formatted.push('<ul style="padding-left:18px; margin:6px 0;">');
          inList = true;
        }
        formatted.push(`<li>${bulletMatch[3]}</li>`);
      } else if (numberMatch) {
        if (!inList) {
          formatted.push('<ol style="padding-left:18px; margin:6px 0;">');
          inList = 'ol';
        }
        formatted.push(`<li>${numberMatch[3]}</li>`);
      } else {
        if (inList) {
          formatted.push(inList === 'ol' ? '</ol>' : '</ul>');
          inList = false;
        }
        if (line.trim()) {
          formatted.push(`<p style="margin:4px 0;">${line}</p>`);
        }
      }
    }
    if (inList) formatted.push(inList === 'ol' ? '</ol>' : '</ul>');

    return formatted.join('');
  }

  stripMarkdown(text) {
    if (!text) return '';
    let clean = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
    clean = clean.replace(/`([^`]+)`/g, '$1');
    clean = clean.replace(/[*#_~`•✓⏳]/g, ' ');
    clean = clean.replace(/\s+/g, ' ').trim();
    return clean;
  }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('aiAssistantWidget')) {
    window.proofVoiceAiChat = new ProofVoiceAiAssistant();
  }
});
