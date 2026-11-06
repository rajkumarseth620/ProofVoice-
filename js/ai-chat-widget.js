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
    this.conversationId = null;

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
      this.stopRecBtn.addEventListener('click', () => this.stopVoiceRecording(false));
    }
    if (this.cancelRecBtn) {
      this.cancelRecBtn.addEventListener('click', () => this.cancelVoiceRecording());
    }

    // Language Select Change Listener
    if (this.langSelect) {
      this.langSelect.addEventListener('change', () => {
        const newLang = this.langSelect.value;
        if (this.speechRecognition) {
          this.speechRecognition.lang = newLang;
        }
        if (this.history.length <= 1) {
          this.renderInitialGreeting(newLang);
        }
      });
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
          this.speakText(item.speak_text || item.text, item.audio_base64, item.audio_content_type, item.language || this.langSelect?.value, item.audio_url);
        }
      }

      // Copy Code button delegate
      const copyBtn = e.target.closest('.ai-copy-code-btn');
      if (copyBtn) {
        const rawCode = decodeURIComponent(copyBtn.getAttribute('data-code') || '');
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(rawCode).then(() => {
            copyBtn.textContent = '✓ Copied!';
            copyBtn.style.color = '#10B981';
            setTimeout(() => {
              copyBtn.textContent = '📋 Copy Code';
              copyBtn.style.color = '';
            }, 2000);
          }).catch(() => {
            this.fallbackCopyText(rawCode, copyBtn);
          });
        } else {
          this.fallbackCopyText(rawCode, copyBtn);
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

  renderInitialGreeting(lang) {
    const activeLang = lang || (this.langSelect ? this.langSelect.value : 'en-IN');
    const studentName = this.currentUser ? (this.currentUser.fullName || this.currentUser.full_name || '') : '';
    const namePrefix = studentName ? studentName.split(' ')[0] : '';

    const greetings = {
      'hi-IN': {
        text: `नमस्ते${namePrefix ? ' ' + namePrefix : ''}! 🙏 **ProofVoice कैंपस AI असिस्टेंट** में आपका स्वागत है। मैं आपकी शिकायतों की स्थिति ट्रैक करने, नई वॉइस शिकायत दर्ज करने, आवेदन में बदलाव (Edit) या हटाने (Delete) और पासवर्ड अपडेट करने में सहायता कर सकता हूँ। आज आप क्या जानना चाहते हैं?`,
        speak: `नमस्ते${namePrefix ? ' ' + namePrefix : ''}! ProofVoice कैंपस असिस्टेंट में आपका स्वागत है। आज मैं आपकी क्या सहायता कर सकता हूँ?`,
        actions: ["मेरी सक्रिय शिकायतें दिखाओ", "वॉइस से शिकायत कैसे दर्ज करें?", "शिकायत एडिट या डिलीट कैसे करें?", "पासवर्ड कैसे बदलें?"]
      },
      'en-IN': {
        text: studentName
          ? `Hello **${studentName}**! Welcome to your ProofVoice Campus Assistant. I can help you record issues, track your tickets, check status updates, or explain institutional redressal rules. What can I help you with today?`
          : `Hello! Welcome to ProofVoice Campus Support. I can help answer questions about student registration, voice-first grievances, mandatory formal application reviews, and resolution timelines. How can I assist you today?`,
        speak: studentName ? `Hello ${studentName}! Welcome to ProofVoice. What can I help you with today?` : "Hello! Welcome to ProofVoice Support. How can I assist you today?",
        actions: studentName
          ? ["What are my active complaints?", "How do I record a voice complaint?", "What does 'Under Review' mean?", "How do I update my profile?"]
          : ["How do I register with an unlisted college?", "How does voice reporting work?", "Why is application review mandatory?", "What do complaint statuses mean?"]
      }
    };

    const config = greetings[activeLang] || greetings['en-IN'];
    this.history = [{
      role: 'assistant',
      text: config.text,
      speak_text: config.speak,
      suggested_actions: config.actions,
      language: activeLang,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }];

    this.renderChatMessages();
  }

  resetConversation() {
    this.stopAllAudio();
    this.stopVoiceRecording(false);
    this.history = [];
    this.conversationId = null;
    const activeLang = this.langSelect ? this.langSelect.value : 'en-IN';
    this.renderInitialGreeting(activeLang);
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

    // Detect language: Devanagari script for Hindi, natural Hinglish, or English
    let detectedScriptLang = null;
    if (/[\u0900-\u097F]/.test(questionText)) {
      detectedScriptLang = 'hi-IN';
    } else if (/\b(namaste|pranam|namaskar|kya|kaise|karna|meri|shikayat|paani|bijli|dhanyawad|madad|sahayata|batao|samjhao|shuru|karein|karu|kyu|kyon|hai|hain|nahi|tha|thi|the|mera|meri|mere|aapka|aapki|kripya)\b/i.test(questionText)) {
      detectedScriptLang = 'hi-IN';
    } else {
      detectedScriptLang = 'en-IN';
    }

    const selectedLang = this.langSelect ? this.langSelect.value : 'en-IN';
    const langToUse = detectedScriptLang || selectedLang || 'en-IN';
    if (detectedScriptLang && this.langSelect && this.langSelect.value !== detectedScriptLang) {
      this.langSelect.value = detectedScriptLang;
    }

    // Append user message
    this.history.push({
      role: 'user',
      text: questionText.trim(),
      language: langToUse,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
    this.renderChatMessages();

    // Show typing loader
    this.showTypingIndicator();

    try {
      let response;
      if (window.proofVoiceApi && typeof window.proofVoiceApi.chatWithAi === 'function') {
        response = await window.proofVoiceApi.chatWithAi(questionText, this.history, this.voiceMode, langToUse, this.conversationId);
      } else {
        response = {
          success: true,
          reply: "I am ready to assist. Please connect to the ProofVoice API to access live data.",
          speak_text: "I am ready to assist. Please connect to the ProofVoice API.",
          language: langToUse
        };
      }

      this.hideTypingIndicator();

      if (response && response.conversation_id) {
        this.conversationId = response.conversation_id;
      } else if (response && response.data && response.data.conversation_id) {
        this.conversationId = response.data.conversation_id;
      }

      const replyText = response.reply || response.data?.reply || "I couldn't process that query. Please try rephrasing.";
      const speakText = response.speak_text || response.data?.speak_text || replyText;
      const actions = response.suggested_actions || response.data?.suggested_actions || [];
      const audioBase64 = response.audio_base64 || response.data?.audio_base64;
      const contentType = response.audio_content_type || response.data?.audio_content_type || 'audio/wav';
      const audioUrl = response.audio_url || response.data?.audio_url;
      const respLang = response.language || (response.data && response.data.language) || langToUse;

      if (respLang && this.langSelect && this.langSelect.value !== respLang) {
        this.langSelect.value = respLang;
      }

      const assistantMsg = {
        role: 'assistant',
        text: replyText,
        speak_text: speakText,
        suggested_actions: actions,
        audio_base64: audioBase64,
        audio_content_type: contentType,
        audio_url: audioUrl,
        language: respLang,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      this.history.push(assistantMsg);
      this.renderChatMessages();

      // If voice mode is on, auto-speak in matching language
      if (this.voiceMode) {
        this.speakText(speakText, audioBase64, contentType, respLang, audioUrl);
      }

    } catch (err) {
      this.hideTypingIndicator();
      console.error('AI Chat Error:', err);
      this.history.push({
        role: 'assistant',
        text: "I encountered a network issue reaching the campus AI server. If this is urgent, you can review the FAQ below or contact your Dean of Student Welfare.",
        speak_text: "I encountered an issue reaching the server. Please check the FAQ below.",
        suggested_actions: ["How do I report an issue?", "What do statuses mean?"],
        language: langToUse,
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
      this.stopVoiceRecording(false);
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
    if (this.recTranscript) this.recTranscript.textContent = "Listening... Speak your question in English or Hindi.";

    // Start timer
    if (this.recTimer) this.recTimer.textContent = "00:00 / 02:00";
    clearInterval(this.recInterval);
    this.recInterval = setInterval(() => {
      this.recSeconds++;
      const mins = String(Math.floor(this.recSeconds / 60)).padStart(2, '0');
      const secs = String(this.recSeconds % 60).padStart(2, '0');
      if (this.recTimer) this.recTimer.textContent = `${mins}:${secs} / 02:00`;

      if (this.recSeconds >= 120) {
        this.stopVoiceRecording(false);
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

        this.speechRecognition.onend = () => {
          if (this.isRecording) {
            this.stopVoiceRecording(false);
          }
        };

        this.speechRecognition.start();
      } catch (e) {
        console.warn('Speech recognition start failed:', e);
      }
    }
  }

  stopVoiceRecording(submit = false) {
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
      // Keep transcribed text in input box so user can review and edit before sending
      if (this.textInput) {
        this.textInput.focus();
      }
    }
  }

  cancelVoiceRecording() {
    if (!this.isRecording) return;
    this.isRecording = false;
    clearInterval(this.recInterval);

    if (this.micBtn) this.micBtn.classList.remove('recording');
    if (this.recStrip) this.recStrip.classList.add('hidden');

    if (this.speechRecognition) {
      try { this.speechRecognition.stop(); } catch (e) {}
      this.speechRecognition = null;
    }

    if (this.textInput) {
      this.textInput.value = '';
    }
  }

  // Voice Output (TTS) Management
  speakText(cleanText, audioBase64 = null, contentType = 'audio/wav', langCode = null, audioUrl = null) {
    this.stopAllAudio();

    if (!cleanText && !audioBase64 && !audioUrl) return;

    // Show Voice Player
    if (this.voicePlayer) this.voicePlayer.classList.remove('hidden');
    if (this.playerStatus) this.playerStatus.textContent = "AI Voice: Speaking...";

    const targetLang = langCode || (this.langSelect ? this.langSelect.value : 'en-IN');
    const plain = this.stripMarkdown(cleanText);

    // 1. If backend returned audio from Gnani Timbre TTS:
    if (audioBase64 || audioUrl) {
      try {
        const audioSrc = audioUrl || `data:${contentType};base64,${audioBase64}`;
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
          this.tryWebVoicePlayback(plain, targetLang);
        };

        this.currentAudioObj.play().catch(() => {
          this.tryWebVoicePlayback(plain, targetLang);
        });
        return;
      } catch (err) {
        console.warn('Gnani audio playback fallback:', err);
      }
    }

    // 2. Stream online TTS or fallback to Web Speech API
    this.tryWebVoicePlayback(plain, targetLang);
  }

  tryWebVoicePlayback(text, langCode) {
    if (!text) return;
    const targetLang = langCode || (this.langSelect ? this.langSelect.value : 'en-IN');
    const prefix = targetLang.split('-')[0].toLowerCase();

    // For Indian regional languages (e.g. bn, hi, ta, te, gu, mr, kn, ml, pa, ur),
    // stream native spoken audio so the student hears authentic regional pronunciation.
    if (prefix === 'hi') {
      try {
        const chunk = text.slice(0, 180);
        const streamUrl = `https://translate.google.com/translate_tts?ie=UTF-8&tl=${prefix}&client=tw-ob&q=${encodeURIComponent(chunk)}`;
        const streamAudio = new Audio(streamUrl);
        this.currentAudioObj = streamAudio;
        this.isPlayingAudio = true;
        if (this.voicePlayer) this.voicePlayer.classList.remove('hidden');
        if (this.playerStatus) this.playerStatus.textContent = "AI Voice: Speaking...";

        streamAudio.onended = () => {
          this.isPlayingAudio = false;
          if (this.playerStatus) this.playerStatus.textContent = "AI Voice: Finished";
          setTimeout(() => {
            if (!this.isPlayingAudio && this.voicePlayer) this.voicePlayer.classList.add('hidden');
          }, 3000);
        };

        streamAudio.onerror = () => {
          this.fallbackSpeechSynthesis(text, targetLang);
        };

        streamAudio.play().catch(() => {
          this.fallbackSpeechSynthesis(text, targetLang);
        });
        return;
      } catch (e) {
        // Fall back to SpeechSynthesis
      }
    }

    this.fallbackSpeechSynthesis(text, targetLang);
  }

  fallbackSpeechSynthesis(text, langCode) {
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

      const targetLang = langCode || (this.langSelect ? this.langSelect.value : 'en-IN');
      this.currentUtterance.lang = targetLang;

      // Match voice specifically for the target Indian language
      const voices = window.speechSynthesis.getVoices() || [];
      const prefix = targetLang.split('-')[0].toLowerCase();

      const langKeywords = {
        'hi': ['hindi', '\u0939\u093f\u0928\u094d\u0926\u0940', '\u0939\u093f\u0902\u0926\u0940'],
        'en': ['english', 'india', 'en-in']
      };

      const keywords = langKeywords[prefix] || [prefix];
      let matchingVoice = voices.find(v => {
        const vLang = (v.lang || '').toLowerCase().replace('_', '-');
        return vLang === targetLang.toLowerCase() || vLang.startsWith(prefix);
      });

      if (!matchingVoice) {
        matchingVoice = voices.find(v => {
          const vName = (v.name || '').toLowerCase();
          return keywords.some(k => vName.includes(k.toLowerCase()));
        });
      }

      // CRITICAL: ONLY attach matchingVoice if it genuinely matches the target language!
      // NEVER attach an English voice to Bengali / Hindi / Tamil etc. text, as English voices cannot synthesize Indic Unicode.
      if (matchingVoice) {
        this.currentUtterance.voice = matchingVoice;
      } else if (prefix === 'en') {
        const enVoice = voices.find(v => (v.lang || '').startsWith('en'));
        if (enVoice) this.currentUtterance.voice = enVoice;
      } else {
        // Let the browser's native engine synthesize using targetLang
        this.currentUtterance.voice = null;
      }

      this.isPlayingAudio = true;
      if (this.voicePlayer) this.voicePlayer.classList.remove('hidden');
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

  fallbackCopyText(text, btn) {
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      if (btn) {
        btn.textContent = '✓ Copied!';
        btn.style.color = '#10B981';
        setTimeout(() => {
          btn.textContent = '📋 Copy Code';
          btn.style.color = '';
        }, 2000);
      }
    } catch (e) {
      console.warn('Fallback copy failed:', e);
    }
  }

  highlightCode(code, lang) {
    if (!code) return '';
    // Tokenize comments, strings, keywords, and numbers in a single pass to prevent nested replacement corruption
    const tokenRegex = /(\/\/[^\n]*|\/\*[\s\S]*?\*\/|#[^\n]*)|("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)|(\b(?:public|class|static|void|main|int|long|float|double|boolean|char|String|if|else|for|while|do|return|import|package|new|try|catch|finally|throw|throws|function|const|let|var|def|elif|lambda|async|await|switch|case|break|default|SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|JOIN|GROUP|BY|ORDER|HAVING|print|println|System|out|Scanner)\b)|(\b\d+(?:\.\d+)?\b)/g;

    let lastIndex = 0;
    let html = '';
    let match;

    while ((match = tokenRegex.exec(code)) !== null) {
      if (match.index > lastIndex) {
        html += this.escapeHtml(code.slice(lastIndex, match.index));
      }
      const [full, comment, string, keyword, number] = match;
      if (comment) {
        html += `<span style="color: #94A3B8; font-style: italic;">${this.escapeHtml(comment)}</span>`;
      } else if (string) {
        html += `<span style="color: #86EFAC;">${this.escapeHtml(string)}</span>`;
      } else if (keyword) {
        html += `<span style="color: #F472B6; font-weight: bold;">${this.escapeHtml(keyword)}</span>`;
      } else if (number) {
        html += `<span style="color: #FBBF24;">${this.escapeHtml(number)}</span>`;
      }
      lastIndex = tokenRegex.lastIndex;
    }
    if (lastIndex < code.length) {
      html += this.escapeHtml(code.slice(lastIndex));
    }
    return html;
  }

  formatMarkdown(str) {
    if (!str) return '';

    // Step 1: Extract code blocks
    const codeBlocks = [];
    let processed = str.replace(/```([a-zA-Z0-9_\-\.\+#]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const idx = codeBlocks.length;
      const cleanLang = (lang || 'code').trim().toUpperCase();
      const encodedCode = encodeURIComponent(code);
      const highlighted = this.highlightCode(code, cleanLang);
      
      const blockHtml = `
        <div class="ai-code-container" style="margin: 10px 0; border-radius: 8px; overflow: hidden; background: #0F172A; border: 1px solid #334155;">
          <div class="ai-code-header" style="display: flex; justify-content: space-between; align-items: center; padding: 6px 12px; background: #1E293B; border-bottom: 1px solid #334155; font-size: 11px; color: #94A3B8; font-family: monospace;">
            <span style="font-weight: 600; letter-spacing: 0.5px; color: #38BDF8;">${this.escapeHtml(cleanLang)}</span>
            <button type="button" class="ai-copy-code-btn" data-code="${encodedCode}" style="background: transparent; border: 1px solid #475569; color: #E2E8F0; padding: 2px 8px; border-radius: 4px; font-size: 11px; cursor: pointer; transition: all 0.2s;">
              📋 Copy Code
            </button>
          </div>
          <pre style="margin: 0; padding: 12px; overflow-x: auto; font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace; font-size: 12.5px; line-height: 1.5; color: #F8FAFC; background: #0F172A; tab-size: 4;"><code class="language-${this.escapeHtml(cleanLang.toLowerCase())}">${highlighted}</code></pre>
        </div>
      `;
      codeBlocks.push(blockHtml);
      return `__AI_CODE_BLOCK_${idx}__`;
    });

    // Step 2: Escape HTML for security
    let html = this.escapeHtml(processed);

    // Step 3: Markdown Headings
    html = html.replace(/^###\s+(.+)$/gm, '<h4 style="margin: 12px 0 6px 0; font-size: 14.5px; font-weight: 700; color: #0F172A;">$1</h4>');
    html = html.replace(/^##\s+(.+)$/gm, '<h3 style="margin: 14px 0 6px 0; font-size: 16px; font-weight: 700; color: #0F172A;">$1</h3>');
    html = html.replace(/^#\s+(.+)$/gm, '<h2 style="margin: 16px 0 8px 0; font-size: 17.5px; font-weight: 700; color: #0F172A;">$1</h2>');

    // Step 4: Horizontal Rules
    html = html.replace(/^(?:---|\*\*\*|___)\s*$/gm, '<hr style="border: none; border-top: 1px solid #E2E8F0; margin: 12px 0;">');

    // Step 5: Blockquotes
    html = html.replace(/^>\s+(.+)$/gm, '<blockquote style="border-left: 3px solid #0D9488; margin: 8px 0; padding: 6px 12px; background: #F0FDFA; color: #134E4A; border-radius: 0 4px 4px 0; font-style: italic;">$1</blockquote>');

    // Step 6: Tables
    html = html.replace(/((?:\|[^\n]+\|\r?\n)+)/g, (tableBlock) => {
      const rows = tableBlock.trim().split('\n').map(r => r.trim()).filter(Boolean);
      if (rows.length < 2) return tableBlock;
      
      let tableHtml = '<div style="overflow-x: auto; margin: 10px 0;"><table style="border-collapse: collapse; width: 100%; font-size: 12.5px; border: 1px solid #E2E8F0; border-radius: 6px;">';
      let isHeader = true;

      for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        if (/^\|[-:\s|]+\|$/.test(row)) {
          isHeader = false;
          continue;
        }
        const cells = row.split('|').slice(1, -1).map(c => c.trim());
        if (isHeader) {
          tableHtml += '<thead style="background: #F8FAFC; border-bottom: 2px solid #CBD5E1;"><tr>';
          cells.forEach(c => {
            tableHtml += `<th style="padding: 7px 10px; text-align: left; font-weight: 600; color: #334155;">${c}</th>`;
          });
          tableHtml += '</tr></thead><tbody>';
          isHeader = false;
        } else {
          const bg = (i % 2 === 0) ? '#FFFFFF' : '#F8FAFC';
          tableHtml += `<tr style="background: ${bg}; border-bottom: 1px solid #E2E8F0;">`;
          cells.forEach(c => {
            tableHtml += `<td style="padding: 6px 10px; color: #1E293B;">${c}</td>`;
          });
          tableHtml += '</tr>';
        }
      }
      tableHtml += '</tbody></table></div>';
      return tableHtml;
    });

    // Step 7: Markdown links: [text](url)
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color: #0D9488; text-decoration: underline; font-weight: 500;">$1</a>');

    // Step 8: Bold: **text**
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Step 9: Italic: *text* or _text_
    html = html.replace(/(?:^|\s)\*([^*]+)\*(?:$|\s)/g, ' <em>$1</em> ');
    html = html.replace(/(?:^|\s)_([^_]+)_(?:$|\s)/g, ' <em>$1</em> ');

    // Step 10: Inline code: `text`
    html = html.replace(/`([^`]+)`/g, '<code style="background: #F1F5F9; color: #0F172A; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-family: monospace; border: 1px solid #E2E8F0;">$1</code>');

    // Step 11: Lists
    const lines = html.split('\n');
    let inList = null;
    const formattedLines = [];

    for (let line of lines) {
      const bulletMatch = line.match(/^(\s*)(•|-|\*)\s+(.*)/);
      const numberMatch = line.match(/^(\s*)(\d+)\.\s+(.*)/);

      if (bulletMatch) {
        if (inList !== 'ul') {
          if (inList === 'ol') formattedLines.push('</ol>');
          formattedLines.push('<ul style="padding-left: 20px; margin: 6px 0; list-style-type: disc;">');
          inList = 'ul';
        }
        formattedLines.push(`<li style="margin: 3px 0;">${bulletMatch[3]}</li>`);
      } else if (numberMatch) {
        if (inList !== 'ol') {
          if (inList === 'ul') formattedLines.push('</ul>');
          formattedLines.push('<ol style="padding-left: 20px; margin: 6px 0;">');
          inList = 'ol';
        }
        formattedLines.push(`<li style="margin: 3px 0;">${numberMatch[3]}</li>`);
      } else {
        if (inList) {
          formattedLines.push(inList === 'ol' ? '</ol>' : '</ul>');
          inList = null;
        }
        if (line.trim().startsWith('__AI_CODE_BLOCK_') || line.trim().startsWith('<h') || line.trim().startsWith('<blockquote') || line.trim().startsWith('<hr') || line.trim().startsWith('<div')) {
          formattedLines.push(line);
        } else if (line.trim()) {
          formattedLines.push(`<p style="margin: 6px 0; line-height: 1.5;">${line}</p>`);
        }
      }
    }
    if (inList) {
      formattedLines.push(inList === 'ol' ? '</ol>' : '</ul>');
    }

    let result = formattedLines.join('\n');

    // Step 12: Restore code blocks
    codeBlocks.forEach((block, idx) => {
      result = result.replace(`__AI_CODE_BLOCK_${idx}__`, block);
    });

    return result;
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
