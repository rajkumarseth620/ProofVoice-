/**
 * ProofVoice - Complaint Creation & Formal Application Workflow (v3)
 * Implements Section 7 & 8: Profile-aware formal grievance synthesis addressed to
 * the Dean or configured authority, flexible campus locations, and review before submission.
 */

class ComplaintWorkflowManager {
  constructor() {
    this.sessionStorageKey = 'proofvoice_draft_complaint';
  }

  // Setup on new-complaint.html
  initCreationPage() {
    const user = window.proofVoiceDb ? window.proofVoiceDb.getCurrentUser() : null;
    const institution = user ? window.proofVoiceDb.getInstitution(user.institutionId) : null;

    // Display sender info banner so student sees their auto-populated profile credentials
    this.renderSenderProfilePreview(user, institution);

    // Tab switching (Voice vs Text)
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const target = btn.dataset.tab;
        tabBtns.forEach(b => b.classList.remove('active'));
        tabPanes.forEach(p => p.classList.remove('active'));

        btn.classList.add('active');
        const targetPane = document.getElementById(target);
        if (targetPane) targetPane.classList.add('active');
      });
    });

    // Character counter for text input
    const textDesc = document.getElementById('complaintTextDesc');
    const charCounter = document.getElementById('charCounter');
    if (textDesc && charCounter) {
      textDesc.addEventListener('input', () => {
        const len = textDesc.value.length;
        charCounter.textContent = `${len} / 2000 characters`;
      });
    }

    // Populate category dropdown from user's institution
    const categorySelect = document.getElementById('complaintCategory');
    if (categorySelect && institution && institution.categories) {
      categorySelect.innerHTML = '<option value="">-- Auto-detect from description --</option>';
      institution.categories.forEach(cat => {
        categorySelect.innerHTML += `<option value="${escapeHtml(cat)}">${escapeHtml(cat)}</option>`;
      });
    }

    // Recipient preview element
    if (categorySelect) {
      categorySelect.addEventListener('change', () => {
        this.updateRecipientPreview(categorySelect.value, institution);
      });
    }

    // Flexible Location helper listeners
    const campusSite = document.getElementById('locCampus');
    const building = document.getElementById('locBuilding');
    const floor = document.getElementById('locFloor');
    const room = document.getElementById('locRoom');
    const locationInput = document.getElementById('complaintLocation');

    const updateLocationString = () => {
      if (!locationInput) return;
      const parts = [];
      if (campusSite && campusSite.value.trim()) parts.push(campusSite.value.trim());
      if (building && building.value.trim()) parts.push(building.value.trim());
      if (floor && floor.value.trim()) parts.push(floor.value.trim());
      if (room && room.value.trim()) parts.push(room.value.trim());
      if (parts.length > 0) {
        locationInput.value = parts.join(', ');
      }
    };

    [campusSite, building, floor, room].forEach(el => {
      if (el) el.addEventListener('input', updateLocationString);
    });

    // Initialize Voice Recorder Engine
    if (document.getElementById('micRecordBtn')) {
      new VoiceRecorderEngine();
    }

    // Generate Formal Application Handler
    const generateBtn = document.getElementById('generateApplicationBtn');
    if (generateBtn) {
      generateBtn.addEventListener('click', () => this.handleGenerateApplication());
    }
  }

  renderSenderProfilePreview(user, institution) {
    const previewContainer = document.getElementById('senderProfilePreview');
    if (!previewContainer || !user) return;

    const hasAddress = Boolean(user.residentialAddress);
    const hasStudentId = Boolean(user.studentIdentifier);

    previewContainer.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
        <div>
          <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.5px; color:var(--color-text-muted); font-weight:600;">Sender Profile (Auto-Populated for Application Letter)</div>
          <div style="font-size:14px; font-weight:700; color:var(--color-navy); margin-top:2px;">
            ${escapeHtml(user.fullName)} 
            <span style="font-weight:normal; color:var(--color-text-secondary); font-size:12px;">• ${escapeHtml(user.studentIdentifier || 'Pending Student ID')}</span>
          </div>
          <div style="font-size:12px; color:var(--color-text-secondary); margin-top:2px;">
            ${escapeHtml(user.department || 'Department not specified')} • ${escapeHtml(institution ? institution.name : '')}
          </div>
          <div style="font-size:11px; color:var(--color-text-muted); margin-top:2px;">
            Correspondence Address: ${escapeHtml(user.residentialAddress || 'Not set in profile')}
          </div>
        </div>
        <div>
          ${!hasAddress || !hasStudentId ? `
            <a href="student-profile-complete.html" class="btn btn-secondary btn-sm" style="font-size:11px; color:var(--color-warning);">
              ⚠️ Complete Profile Details
            </a>
          ` : `
            <span class="badge badge-resolved" style="font-size:11px;">✓ Profile 100% Verified</span>
          `}
        </div>
      </div>
    `;
  }

  updateRecipientPreview(category, institution) {
    const previewEl = document.getElementById('recipientAuthorityPreview');
    if (!previewEl || !institution) return;

    const recipient = this.determineAuthorityTitle(category, institution);
    previewEl.textContent = recipient;
  }

  handleGenerateApplication() {
    const user = window.proofVoiceDb.getCurrentUser();
    const institution = window.proofVoiceDb.getInstitution(user.institutionId);

    // Determine active input method & description
    const activeTab = document.querySelector('.tab-btn.active')?.dataset.tab || 'voiceTab';
    let rawDescription = '';
    let inputMethod = 'text';

    if (activeTab === 'voiceTab') {
      inputMethod = 'voice';
      const transInput = document.getElementById('transcriptionInput');
      rawDescription = transInput ? transInput.value.trim() : '';
      if (!rawDescription) {
        const textDesc = document.getElementById('complaintTextDesc');
        if (textDesc && textDesc.value.trim()) {
          rawDescription = textDesc.value.trim();
        }
      }
    } else {
      inputMethod = 'text';
      const textDesc = document.getElementById('complaintTextDesc');
      rawDescription = textDesc ? textDesc.value.trim() : '';
      if (!rawDescription) {
        const transInput = document.getElementById('transcriptionInput');
        if (transInput && transInput.value.trim()) {
          rawDescription = transInput.value.trim();
          inputMethod = 'voice';
        }
      }
    }

    const titleInput = document.getElementById('complaintTitle');
    const categoryInput = document.getElementById('complaintCategory');
    const priorityInput = document.getElementById('complaintPriority');
    const locationInput = document.getElementById('complaintLocation');

    const title = titleInput ? titleInput.value.trim() : '';
    const category = categoryInput ? categoryInput.value : '';
    const priority = priorityInput ? priorityInput.value : 'Medium';
    const location = locationInput ? locationInput.value.trim() : '';

    // Validation
    if (!title) {
      showToast('error', 'Missing Information', 'Please provide a brief complaint title / subject.');
      titleInput?.focus();
      return;
    }

    if (!rawDescription) {
      showToast('error', 'Missing Description', 'Please record your voice or enter a text description of the problem.');
      return;
    }

    if (!location) {
      showToast('error', 'Missing Location', 'Please specify where the issue is located on campus.');
      locationInput?.focus();
      return;
    }

    // Auto-suggest category if not selected
    let finalCategory = category;
    if (!finalCategory) {
      finalCategory = this.suggestCategoryFromText(rawDescription + ' ' + title);
      if (categoryInput) categoryInput.value = finalCategory;
    }

    const suggestedDept = this.suggestDepartmentForCategory(finalCategory, institution);
    const recipientAuthority = this.determineAuthorityTitle(finalCategory, institution);

    // Show processing loading state on button
    const generateBtn = document.getElementById('generateApplicationBtn');
    const originalText = generateBtn.innerHTML;
    generateBtn.disabled = true;
    generateBtn.innerHTML = `<span class="spinner"></span> Synthesizing Formal Letter...`;

    setTimeout(() => {
      // Synthesize formal application letter matching Section 8.C template
      const formalLetter = this.synthesizeFormalLetter({
        studentName: user.fullName,
        studentId: user.studentIdentifier || '',
        studentDepartment: user.department || '',
        studentYear: user.yearSemester || '',
        studentAddress: user.residentialAddress || '',
        studentPhone: user.phone || '',
        institutionName: institution.name,
        institutionAddress: institution.officialAddress || `${institution.city}, ${institution.state}`,
        recipientAuthority,
        title,
        location,
        category: finalCategory,
        description: rawDescription
      });

      const draftPayload = {
        title,
        originalInputMethod: inputMethod,
        originalTranscription: rawDescription,
        category: finalCategory,
        priority,
        location,
        recipientAuthority,
        suggestedDepartment: suggestedDept,
        formalApplication: formalLetter,
        generatedAt: new Date().toISOString()
      };

      sessionStorage.setItem(this.sessionStorageKey, JSON.stringify(draftPayload));

      generateBtn.disabled = false;
      generateBtn.innerHTML = originalText;

      // Navigate to review & confirmation screen
      window.location.href = 'review-complaint.html';
    }, 1000);
  }

  suggestCategoryFromText(text) {
    const t = text.toLowerCase();
    if (t.includes('projector') || t.includes('computer') || t.includes('lab') || t.includes('screen') || t.includes('software') || t.includes('printer')) {
      return 'Classroom and Laboratory';
    }
    if (t.includes('water') || t.includes('washroom') || t.includes('toilet') || t.includes('tap') || t.includes('leak') || t.includes('cooler') || t.includes('purifier')) {
      return 'Water and Sanitation';
    }
    if (t.includes('light') || t.includes('fan') || t.includes('bulb') || t.includes('power') || t.includes('electric') || t.includes('wiring') || t.includes('switch')) {
      return 'Electricity and Lighting';
    }
    if (t.includes('wifi') || t.includes('wi-fi') || t.includes('internet') || t.includes('network') || t.includes('portal') || t.includes('lan')) {
      return 'Internet and IT';
    }
    if (t.includes('hostel') || t.includes('mess') || t.includes('warden') || t.includes('bed') || t.includes('dorm')) {
      return 'Hostel and Accommodation';
    }
    if (t.includes('bus') || t.includes('transport') || t.includes('shuttle') || t.includes('van')) {
      return 'Transport';
    }
    if (t.includes('book') || t.includes('library') || t.includes('reading room')) {
      return 'Library';
    }
    if (t.includes('guard') || t.includes('security') || t.includes('gate') || t.includes('theft') || t.includes('harassment')) {
      return 'Safety and Security';
    }
    return 'Infrastructure and Maintenance';
  }

  suggestDepartmentForCategory(category, institution) {
    if (institution && institution.recipientMappings && institution.recipientMappings[category]) {
      return institution.recipientMappings[category].department;
    }

    const map = {
      'Classroom and Laboratory': 'Information Technology Services',
      'Water and Sanitation': 'Water Works & Sanitation',
      'Electricity and Lighting': 'Electrical & Energy Management',
      'Internet and IT': 'Information Technology Services',
      'Hostel and Accommodation': 'Hostel & Residential Life',
      'Transport': 'Transport & Shuttle Operations',
      'Library': 'Library & Information Services',
      'Infrastructure and Maintenance': 'Infrastructure & Maintenance',
      'Safety and Security': 'Campus Security Services',
      'Administrative Services': 'General Administration'
    };
    return map[category] || 'General Administration';
  }

  determineAuthorityTitle(category, institution) {
    if (institution && institution.recipientMappings && institution.recipientMappings[category]) {
      return institution.recipientMappings[category].designation;
    }

    if (institution && institution.defaultRecipient && institution.defaultRecipient.designation) {
      return institution.defaultRecipient.designation;
    }

    return 'The Dean';
  }

  // Exact Formal Letter Format according to Section 8.C:
  synthesizeFormalLetter(data) {
    const formattedDate = new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });

    const senderAcademic = [
      data.studentDepartment ? `Department of ${data.studentDepartment}` : '',
      data.studentYear || ''
    ].filter(Boolean).join(', ');

    return `${data.studentName}
${data.studentId ? `Student ID: ${data.studentId}` : ''}
${senderAcademic}
${data.institutionName}
${data.studentAddress || data.institutionAddress}
${formattedDate}

To,
${data.recipientAuthority}
${data.institutionName}
${data.institutionAddress}

Subject: Formal Grievance Regarding ${data.title}

Respected Sir/Madam,

I am writing this formal application to respectfully draw your urgent attention to an ongoing issue regarding ${data.category.toLowerCase()} within our campus premises.

Location of Issue:
${data.location}

Description of Grievance:
${data.description}

Institutional Impact:
The aforementioned issue is causing substantial disruption to student routines and campus safety. Prompt rectification is necessary to maintain standard institutional hygiene and academic workflow.

I kindly request you to look into this matter and take the necessary action to resolve the issue.

Thank you for your time and consideration.

Yours sincerely,

${data.studentName}
${data.studentId ? `Student ID: ${data.studentId}` : ''}
${data.studentDepartment ? `Department of ${data.studentDepartment}` : ''}
${data.institutionName}
${data.studentPhone ? `Contact: ${data.studentPhone}` : ''}`;
  }

  // Review Page Logic
  initReviewPage() {
    const rawDraft = sessionStorage.getItem(this.sessionStorageKey);
    if (!rawDraft) {
      showToast('warning', 'No Draft Found', 'Please fill in a complaint first.');
      setTimeout(() => {
        window.location.href = 'new-complaint.html';
      }, 1500);
      return;
    }

    const draft = JSON.parse(rawDraft);
    const user = window.proofVoiceDb.getCurrentUser();
    const institution = window.proofVoiceDb.getInstitution(user.institutionId);

    // Populate review display
    const instEl = document.getElementById('reviewInstitutionName');
    const titleEl = document.getElementById('reviewTitle');
    const categoryEl = document.getElementById('reviewCategory');
    const locationEl = document.getElementById('reviewLocation');
    const priorityEl = document.getElementById('reviewPriority');
    const deptEl = document.getElementById('reviewDepartment');
    const letterBodyEl = document.getElementById('reviewLetterBody');
    const recipientSelect = document.getElementById('reviewRecipientSelect');

    if (instEl) instEl.textContent = institution.name;
    if (titleEl) titleEl.textContent = draft.title;
    if (categoryEl) categoryEl.textContent = draft.category;
    if (locationEl) locationEl.textContent = draft.location;
    if (priorityEl) priorityEl.innerHTML = renderPriorityBadge(draft.priority);
    if (deptEl) deptEl.textContent = draft.suggestedDepartment || 'General Administration';
    if (letterBodyEl) letterBodyEl.textContent = draft.formalApplication;

    // Recipient Selector setup
    if (recipientSelect) {
      recipientSelect.value = draft.recipientAuthority || 'The Dean';
      recipientSelect.addEventListener('change', () => {
        draft.recipientAuthority = recipientSelect.value;
        // Re-generate formal letter with new recipient
        draft.formalApplication = this.synthesizeFormalLetter({
          studentName: user.fullName,
          studentId: user.studentIdentifier || '',
          studentDepartment: user.department || '',
          studentYear: user.yearSemester || '',
          studentAddress: user.residentialAddress || '',
          studentPhone: user.phone || '',
          institutionName: institution.name,
          institutionAddress: institution.officialAddress || `${institution.city}, ${institution.state}`,
          recipientAuthority: draft.recipientAuthority,
          title: draft.title,
          location: draft.location,
          category: draft.category,
          description: draft.originalTranscription
        });
        sessionStorage.setItem(this.sessionStorageKey, JSON.stringify(draft));
        if (letterBodyEl) letterBodyEl.textContent = draft.formalApplication;
        showToast('info', 'Recipient Updated', `Application addressed to: ${draft.recipientAuthority}`);
      });
    }

    // Read Aloud handler (Timbre TTS notice & SpeechSynthesis)
    const ttsBtn = document.getElementById('reviewTtsBtn');
    let isSpeaking = false;
    if (ttsBtn) {
      ttsBtn.addEventListener('click', () => {
        if (!isSpeaking) {
          isSpeaking = true;
          ttsBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg> Stop Reading`;
          speakText(draft.formalApplication, null, () => {
            isSpeaking = false;
            ttsBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg> Read Aloud`;
          });
        } else {
          stopSpeaking();
          isSpeaking = false;
          ttsBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg> Read Aloud`;
        }
      });
    }

    // Print Application Button
    const printBtn = document.getElementById('reviewPrintBtn');
    if (printBtn) {
      printBtn.addEventListener('click', () => {
        window.print();
      });
    }

    // Edit Application Modal Handler
    const editBtn = document.getElementById('editApplicationBtn');
    const editTextArea = document.getElementById('editAppTextArea');
    const saveEditBtn = document.getElementById('saveAppEditBtn');

    if (editBtn && editTextArea) {
      editBtn.addEventListener('click', () => {
        editTextArea.value = draft.formalApplication;
        openModal('editAppModal');
      });
    }

    if (saveEditBtn && editTextArea) {
      saveEditBtn.addEventListener('click', () => {
        draft.formalApplication = editTextArea.value;
        sessionStorage.setItem(this.sessionStorageKey, JSON.stringify(draft));
        if (letterBodyEl) letterBodyEl.textContent = draft.formalApplication;
        closeModal('editAppModal');
        showToast('success', 'Changes Saved', 'Formal application text updated.');
      });
    }

    // Confirm and Submit Handler
    const submitBtn = document.getElementById('confirmSubmitBtn');
    const confirmCheckbox = document.getElementById('confirmVerificationCheck');

    if (submitBtn) {
      submitBtn.addEventListener('click', async () => {
        if (confirmCheckbox && !confirmCheckbox.checked) {
          showToast('error', 'Confirmation Required', 'Please check the box confirming you have reviewed the application before submitting.');
          return;
        }

        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span class="spinner"></span> Transmitting to Institutional Desk...`;

        try {
          const newComplaint = await window.proofVoiceApi.submitComplaint(draft);
          sessionStorage.removeItem(this.sessionStorageKey);

          // Populate success modal
          const modalIdEl = document.getElementById('successComplaintId');
          const modalDateEl = document.getElementById('successDate');
          const modalStatusEl = document.getElementById('successStatus');
          const modalRecipientEl = document.getElementById('successRecipient');
          const modalInstEl = document.getElementById('successInstitution');
          const viewLink = document.getElementById('successViewLink');

          if (modalIdEl) modalIdEl.textContent = newComplaint.id;
          if (modalDateEl) modalDateEl.textContent = formatDateTime(newComplaint.submittedAt);
          if (modalStatusEl) modalStatusEl.innerHTML = renderStatusBadge(newComplaint.status);
          if (modalRecipientEl) modalRecipientEl.textContent = newComplaint.recipientAuthority || 'The Dean';
          if (modalInstEl) modalInstEl.textContent = institution.name;
          sessionStorage.setItem('proofvoice_current_complaint_id', newComplaint.id);
          localStorage.setItem('proofvoice_last_viewed_complaint_id', newComplaint.id);
          if (viewLink) {
            viewLink.href = `complaint-details.html?id=${encodeURIComponent(newComplaint.id)}`;
            viewLink.onclick = () => {
              sessionStorage.setItem('proofvoice_current_complaint_id', newComplaint.id);
              localStorage.setItem('proofvoice_last_viewed_complaint_id', newComplaint.id);
            };
          }

          openModal('submissionSuccessModal');
          showToast('success', 'Complaint Submitted', `Complaint ${newComplaint.id} formally registered.`);
        } catch (err) {
          showToast('error', 'Submission Failed', err.message || 'Network error.');
          submitBtn.disabled = false;
          submitBtn.innerHTML = 'Confirm and Submit Application';
        }
      });
    }
  }
}

window.complaintWorkflow = new ComplaintWorkflowManager();
