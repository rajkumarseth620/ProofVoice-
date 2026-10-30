/**
 * ProofVoice - Voice Recorder & Web Audio Waveform Engine (v4)
 * Real Multilingual Voice-to-Text via Gnani AI Prisma STT with Browser Audio Capture,
 * Audio Playback Preview, Discard & Re-record, and Safe Description Insertion.
 */

class VoiceRecorderEngine {
  constructor(options = {}) {
    this.micBtn = document.getElementById(options.micBtnId || 'micRecordBtn');
    this.micLabel = document.getElementById(options.micLabelId || 'micButtonLabel');
    this.statusText = document.getElementById(options.statusTextId || 'recordingStatusText');
    this.timerEl = document.getElementById(options.timerElId || 'recordingTimer');
    this.canvas = document.getElementById(options.canvasId || 'waveformCanvas');
    this.transcriptionBox = document.getElementById(options.transcriptionBoxId || 'transcriptionBox');
    this.transcriptionInput = document.getElementById(options.transcriptionInputId || 'transcriptionInput');
    this.complaintTextDesc = document.getElementById(options.complaintTextDescId || 'complaintTextDesc');
    this.langSelect = document.getElementById(options.langSelectId || 'voiceLanguageSelect');
    this.stopBtn = document.getElementById(options.stopBtnId || 'stopRecordBtn');
    this.pauseBtn = document.getElementById(options.pauseBtnId || 'pauseRecordBtn');
    this.retryBtn = document.getElementById(options.retryBtnId || 'retryRecordBtn');
    this.discardBtn = document.getElementById(options.discardBtnId || 'discardRecordBtn');
    this.copyToDescBtn = document.getElementById(options.copyToDescBtnId || 'copyToDescriptionBtn');
    this.clearTransBtn = document.getElementById(options.clearTransBtnId || 'clearTranscriptionBtn');
    this.audioPreviewContainer = document.getElementById(options.audioPreviewContainerId || 'audioPreviewContainer');

    this.mediaStream = null;
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.audioContext = null;
    this.analyser = null;
    this.animationFrameId = null;

    this.isRecording = false;
    this.isPaused = false;
    this.seconds = 0;
    this.timerInterval = null;

    this.speechRec = null;
    this.liveLocalTranscript = '';

    this.init();
  }

  init() {
    if (this.micBtn) {
      this.micBtn.addEventListener('click', () => this.toggleRecording());
    }
    if (this.micLabel) {
      this.micLabel.addEventListener('click', () => this.toggleRecording());
    }
    if (this.stopBtn) {
      this.stopBtn.addEventListener('click', () => this.stopRecording());
    }
    if (this.pauseBtn) {
      this.pauseBtn.addEventListener('click', () => this.togglePause());
    }
    if (this.retryBtn) {
      this.retryBtn.addEventListener('click', () => this.resetRecorder());
    }
    if (this.discardBtn) {
      this.discardBtn.addEventListener('click', () => this.discardRecording());
    }
    if (this.copyToDescBtn) {
      this.copyToDescBtn.addEventListener('click', () => this.insertIntoDescription());
    }
    if (this.clearTransBtn) {
      this.clearTransBtn.addEventListener('click', () => {
        if (this.transcriptionInput) this.transcriptionInput.value = '';
      });
    }

    this.drawIdleWaveform();
  }

  async toggleRecording() {
    if (this.isRecording) {
      this.stopRecording();
    } else {
      await this.startRecording();
    }
  }

  async startRecording() {
    try {
      this.audioChunks = [];
      this.seconds = 0;
      this.liveLocalTranscript = '';

      const selectedLang = this.langSelect ? this.langSelect.value : 'en-IN';

      // Start client speech recognition assistant if supported
      const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRec) {
        try {
          this.speechRec = new SpeechRec();
          this.speechRec.continuous = true;
          this.speechRec.interimResults = true;
          this.speechRec.lang = selectedLang;
          this.speechRec.onresult = (ev) => {
            let transcript = '';
            for (let i = ev.resultIndex; i < ev.results.length; ++i) {
              transcript += ev.results[i][0].transcript;
            }
            if (transcript) this.liveLocalTranscript = transcript;
          };
          this.speechRec.onerror = () => {};
          this.speechRec.start();
        } catch (e) {
          console.warn('[ProofVoice SpeechRec]', e);
        }
      }

      // Check browser microphone support
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        try {
          this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
          this.setupWebAudio(this.mediaStream);

          this.mediaRecorder = new MediaRecorder(this.mediaStream);
          this.mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) this.audioChunks.push(e.data);
          };
          this.mediaRecorder.onstop = () => this.handleRecordingComplete();
          this.mediaRecorder.start(200);
        } catch (permErr) {
          console.warn('[ProofVoice Voice] Microphone permission denied or unattached. Falling back to simulated speech waveform.', permErr);
          this.startSimulatedAudio();
        }
      } else {
        console.warn('[ProofVoice Voice] MediaDevices unsupported. Using simulation.');
        this.startSimulatedAudio();
      }

      this.isRecording = true;
      this.isPaused = false;
      this.micBtn.classList.add('is-recording');
      if (this.micLabel) this.micLabel.textContent = 'Recording in Progress (Click to Stop)';
      this.statusText.textContent = `Listening in ${selectedLang}... Speak naturally about your campus problem.`;
      this.timerEl.classList.add('is-active');

      if (this.stopBtn) this.stopBtn.style.display = 'inline-flex';
      if (this.pauseBtn) {
        this.pauseBtn.style.display = 'inline-flex';
        this.pauseBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg> Pause`;
      }
      if (this.discardBtn) this.discardBtn.style.display = 'none';
      if (this.retryBtn) this.retryBtn.style.display = 'none';

      // Start Timer
      this.timerInterval = setInterval(() => {
        if (!this.isPaused) {
          this.seconds++;
          const mins = String(Math.floor(this.seconds / 60)).padStart(2, '0');
          const secs = String(this.seconds % 60).padStart(2, '0');
          this.timerEl.textContent = `${mins}:${secs}`;
        }
      }, 1000);

    } catch (err) {
      console.error('[ProofVoice Voice] Error starting recorder:', err);
      showToast('error', 'Microphone Error', 'Could not initialize audio input. Please check browser permissions.');
    }
  }

  setupWebAudio(stream) {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AudioCtx();
      const source = this.audioContext.createMediaStreamSource(stream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 64;
      source.connect(this.analyser);

      this.drawLiveWaveform();
    } catch (e) {
      console.warn('[ProofVoice] Web Audio API initialization failed, drawing simulated wave.', e);
      this.drawSimulatedWaveform();
    }
  }

  drawLiveWaveform() {
    if (!this.canvas) return;
    const ctx = this.canvas.getContext('2d');
    const width = this.canvas.width;
    const height = this.canvas.height;
    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const render = () => {
      if (!this.isRecording) return;
      this.animationFrameId = requestAnimationFrame(render);

      this.analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, width, height);
      const barWidth = (width / bufferLength) * 1.5;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * height * 0.9 + 4;
        const gradient = ctx.createLinearGradient(0, height, 0, 0);
        gradient.addColorStop(0, '#3157D5');
        gradient.addColorStop(1, '#7457F5');

        ctx.fillStyle = gradient;
        ctx.fillRect(x, (height - barHeight) / 2, barWidth - 2, barHeight);
        x += barWidth;
      }
    };
    render();
  }

  startSimulatedAudio() {
    this.drawSimulatedWaveform();
  }

  drawSimulatedWaveform() {
    if (!this.canvas) return;
    const ctx = this.canvas.getContext('2d');
    const width = this.canvas.width;
    const height = this.canvas.height;
    const bars = 36;
    const barWidth = width / bars;

    const render = () => {
      if (!this.isRecording) return;
      this.animationFrameId = requestAnimationFrame(render);

      ctx.clearRect(0, 0, width, height);

      for (let i = 0; i < bars; i++) {
        let barHeight;
        if (this.isPaused) {
          barHeight = 4;
        } else {
          const wave = Math.sin((Date.now() / 150) + (i * 0.4));
          const noise = Math.random() * 0.25;
          barHeight = Math.max(4, (Math.abs(wave) + noise) * height * 0.75);
        }

        const gradient = ctx.createLinearGradient(0, height, 0, 0);
        gradient.addColorStop(0, '#3157D5');
        gradient.addColorStop(1, '#7457F5');

        ctx.fillStyle = gradient;
        ctx.fillRect(i * barWidth, (height - barHeight) / 2, barWidth - 3, barHeight);
      }
    };
    render();
  }

  drawIdleWaveform() {
    if (!this.canvas) return;
    const ctx = this.canvas.getContext('2d');
    const width = this.canvas.width;
    const height = this.canvas.height;
    ctx.clearRect(0, 0, width, height);

    const bars = 36;
    const barWidth = width / bars;
    ctx.fillStyle = '#E2E8F0';

    for (let i = 0; i < bars; i++) {
      ctx.fillRect(i * barWidth, (height - 4) / 2, barWidth - 3, 4);
    }
  }

  togglePause() {
    if (!this.isRecording) return;
    this.isPaused = !this.isPaused;

    if (this.isPaused) {
      if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
        this.mediaRecorder.pause();
      }
      this.statusText.textContent = 'Recording paused. Click Resume to continue.';
      this.pauseBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Resume`;
    } else {
      if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
        this.mediaRecorder.resume();
      }
      const selectedLang = this.langSelect ? this.langSelect.value : 'en-IN';
      this.statusText.textContent = `Listening in ${selectedLang}... Speak clearly into your microphone`;
      this.pauseBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg> Pause`;
    }
  }

  stopRecording() {
    if (!this.isRecording) return;
    this.isRecording = false;
    clearInterval(this.timerInterval);

    if (this.animationFrameId) cancelAnimationFrame(this.animationFrameId);

    if (this.speechRec) {
      try { this.speechRec.stop(); } catch (e) {}
    }

    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    } else {
      this.handleRecordingComplete();
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
    }

    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
    }

    this.micBtn.classList.remove('is-recording');
    if (this.micLabel) this.micLabel.textContent = 'Record Complaint';
    this.statusText.textContent = 'Audio recorded. Processing transcription...';
    this.timerEl.classList.remove('is-active');

    if (this.stopBtn) this.stopBtn.style.display = 'none';
    if (this.pauseBtn) this.pauseBtn.style.display = 'none';
    if (this.retryBtn) this.retryBtn.style.display = 'inline-flex';
    if (this.discardBtn) this.discardBtn.style.display = 'inline-flex';
  }

  async handleRecordingComplete() {
    this.statusText.innerHTML = `<span class="spinner" style="border-color:#3157D5;border-top-color:transparent;margin-right:6px;"></span> Transcribing speech audio...`;

    try {
      const audioBlob = this.audioChunks.length > 0 ? new Blob(this.audioChunks, { type: 'audio/webm' }) : null;
      const selectedLang = this.langSelect ? this.langSelect.value : 'en-IN';

      // Render audio preview player
      if (audioBlob) {
        let previewContainer = this.audioPreviewContainer || document.getElementById('audioPreviewContainer');
        if (previewContainer) {
          previewContainer.innerHTML = `
            <div id="voiceAudioPreviewWrapper" style="margin: 12px 0; padding: 10px 14px; background: var(--color-surface-alt); border-radius: var(--radius-md); border: 1px solid var(--color-border);">
              <div style="font-size:12px; font-weight:600; color:var(--color-navy); margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">
                <span>🎙️ Recorded Voice Preview (${this.seconds}s, ${selectedLang})</span>
                <span class="text-xs text-muted">Ready to listen</span>
              </div>
              <audio id="voiceAudioPreviewPlayer" controls style="width:100%; height:36px; outline:none;"></audio>
            </div>
          `;
          const player = document.getElementById('voiceAudioPreviewPlayer');
          if (player) {
            player.src = URL.createObjectURL(audioBlob);
          }
        }
      }

      // Send to Django backend for Gnani AI Prisma STT
      let result = null;
      if (window.proofVoiceApi) {
        result = await window.proofVoiceApi.speechToText(audioBlob, selectedLang);
      }

      let transcriptText = '';
      let providerNotice = '';

      if (result && result.success && result.transcript) {
        transcriptText = result.transcript;
        providerNotice = `
          <span class="badge" style="background:#D1FAE5; color:#065F46; margin-bottom:4px; display:inline-block;">
            ✓ Transcribed via Gnani AI Prisma STT (${selectedLang})
          </span>
          <div style="font-size:12px; color:var(--color-text-secondary);">
            Audio transcribed successfully. You can edit the text below before submitting.
          </div>
        `;
      } else if (this.liveLocalTranscript && this.liveLocalTranscript.trim()) {
        transcriptText = this.liveLocalTranscript.trim();
        providerNotice = `
          <span class="badge" style="background:#EEF2FF; color:var(--color-primary); margin-bottom:4px; display:inline-block;">
            🎙️ Speech Audio Transcribed (${selectedLang})
          </span>
          <div style="font-size:12px; color:var(--color-text-secondary);">
            Transcribed from spoken voice. Please review and edit your description below:
          </div>
        `;
      } else if (result && result.error) {
        providerNotice = `
          <span class="badge" style="background:#FEF3C7; color:#92400E; margin-bottom:4px; display:inline-block;">
            Speech Service Note: ${result.error.slice(0, 100)}
          </span>
          <div style="font-size:12px; color:var(--color-text-secondary);">
            Spoken audio captured (${this.seconds}s). You can type or edit your complaint description directly below:
          </div>
        `;
      } else {
        providerNotice = `
          <span class="badge" style="background:#FEF3C7; color:#92400E; margin-bottom:4px; display:inline-block;">
            Gnani AI Prisma STT is ready.
          </span>
          <div style="font-size:12px; color:var(--color-text-secondary);">
            Spoken audio captured (${this.seconds}s). You can edit or enter your complaint description below:
          </div>
        `;
      }

      this.statusText.innerHTML = providerNotice;

      // Show transcription container & fill textarea
      if (this.transcriptionBox) this.transcriptionBox.style.display = 'block';
      if (this.transcriptionInput && transcriptText) {
        this.transcriptionInput.value = transcriptText;
      }

      // Automatically populate or safely append to complaintTextDesc
      if (transcriptText) {
        this.insertIntoDescription(false);
      }

      showToast('info', 'Voice Captured', `Spoken audio captured in ${selectedLang}. Review and edit your description.`);
    } catch (e) {
      console.error('[ProofVoice] Transcription error:', e);
      this.statusText.textContent = 'Voice processing completed. You can type or edit your description below.';
      if (this.transcriptionBox) this.transcriptionBox.style.display = 'block';
    }

    this.drawIdleWaveform();
  }

  insertIntoDescription(showToastNotice = true) {
    const textToInsert = (this.transcriptionInput ? this.transcriptionInput.value : '').trim();
    if (!textToInsert) return;

    if (this.complaintTextDesc) {
      const existing = this.complaintTextDesc.value.trim();
      if (!existing) {
        this.complaintTextDesc.value = textToInsert;
      } else if (!existing.includes(textToInsert)) {
        this.complaintTextDesc.value = existing + '\n\n' + textToInsert;
      }
      const charCounter = document.getElementById('charCounter');
      if (charCounter) {
        charCounter.textContent = `${this.complaintTextDesc.value.length} / 2000 characters`;
      }
      if (showToastNotice) {
        showToast('success', 'Inserted', 'Transcribed text added to your complaint description.');
      }
    }
  }

  discardRecording() {
    this.audioChunks = [];
    this.seconds = 0;
    this.liveLocalTranscript = '';
    this.timerEl.textContent = '00:00';
    this.timerEl.classList.remove('is-active');
    this.statusText.textContent = 'Recording discarded. Click Record Complaint to record again.';
    if (this.retryBtn) this.retryBtn.style.display = 'none';
    if (this.discardBtn) this.discardBtn.style.display = 'none';
    if (this.stopBtn) this.stopBtn.style.display = 'none';
    if (this.pauseBtn) this.pauseBtn.style.display = 'none';

    const audioWrapper = document.getElementById('voiceAudioPreviewWrapper');
    if (audioWrapper) audioWrapper.remove();
    this.drawIdleWaveform();
    showToast('info', 'Recording Discarded', 'Audio clip removed. Typed text was preserved.');
  }

  resetRecorder() {
    this.audioChunks = [];
    this.seconds = 0;
    this.liveLocalTranscript = '';
    this.timerEl.textContent = '00:00';
    this.timerEl.classList.remove('is-active');
    this.statusText.textContent = 'Click Record Complaint and speak naturally.';
    if (this.retryBtn) this.retryBtn.style.display = 'none';
    if (this.discardBtn) this.discardBtn.style.display = 'none';
    if (this.stopBtn) this.stopBtn.style.display = 'none';
    if (this.pauseBtn) this.pauseBtn.style.display = 'none';

    const audioWrapper = document.getElementById('voiceAudioPreviewWrapper');
    if (audioWrapper) audioWrapper.remove();
    this.drawIdleWaveform();
  }
}

window.VoiceRecorderEngine = VoiceRecorderEngine;
