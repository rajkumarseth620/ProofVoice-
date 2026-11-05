/**
 * ProofVoice - Student Dashboard, Complaints List & Detail Tracking Logic (v3)
 * Implements Section 6 & 9: Real-time complaint tracking, status timeline,
 * rejection notice display, reopening requests, and status breakdown.
 */

document.addEventListener('DOMContentLoaded', () => {
  const isDashboard = document.getElementById('studentStatsGrid');
  const isMyComplaints = document.getElementById('myComplaintsTableBody');
  const isDetailsPage = document.getElementById('complaintDetailsHeader');

  if (isDashboard) {
    loadStudentDashboard();
  }

  if (isMyComplaints) {
    loadMyComplaintsPage();
  }

  if (isDetailsPage) {
    loadComplaintDetailsPage();
  }
});

async function resolveStudentContext(filter) {
  try {
    if (window.proofVoiceApi && window.proofVoiceApi.isLiveSession()) {
      let user = window.proofVoiceApi.getStoredUser();
      if (!user && typeof window.proofVoiceApi.getCurrentUser === 'function') {
        try { user = await window.proofVoiceApi.getCurrentUser(); } catch (e) {}
      }
      if (!user && window.proofVoiceDb) {
        user = window.proofVoiceDb.getCurrentUser();
      }
      user = user || { fullName: 'Student', role: 'student', institutionName: 'Campus Institution' };

      let complaints = [];
      try {
        complaints = await window.proofVoiceApi.getComplaints(filter || {});
      } catch (err) {
        if (window.proofVoiceDb) complaints = window.proofVoiceDb.getComplaints(filter || {});
      }

      return {
        user,
        institution: {
          name: user.institutionName || 'Your Institution',
          categories: []
        },
        complaints: Array.isArray(complaints) ? complaints : []
      };
    }
  } catch (err) {
    console.warn('[ProofVoice] Live student context failed, falling back:', err);
  }

  const user = (window.proofVoiceDb && window.proofVoiceDb.getCurrentUser()) || { fullName: 'Student', role: 'student', institutionName: 'Campus Institution' };
  const instId = user ? (user.institutionId || user.institution_id) : null;
  const institution = (window.proofVoiceDb && instId ? window.proofVoiceDb.getInstitution(instId) : null) || { name: user.institutionName || 'Your Institution', categories: [] };
  const complaints = (window.proofVoiceDb && typeof window.proofVoiceDb.getComplaints === 'function') ? window.proofVoiceDb.getComplaints(filter || {}) : [];
  return { user, institution, complaints: Array.isArray(complaints) ? complaints : [] };
}

async function loadStudentDashboard() {
  const { complaints, user, institution } = await resolveStudentContext();

  // Set greeting & institution
  const greetingEl = document.getElementById('studentGreetingName');
  const instBadgeEl = document.getElementById('studentInstitutionName');
  const userAvatarEl = document.getElementById('sidebarUserAvatar');
  const userNameEl = document.getElementById('sidebarUserName');

  const fullName = (user && (user.fullName || user.full_name || user.name || user.email)) || 'Student';
  const firstName = fullName.trim().split(/\s+/)[0] || fullName;

  if (greetingEl) greetingEl.textContent = firstName;
  if (instBadgeEl) instBadgeEl.textContent = (institution && institution.name) || (user && user.institutionName) || 'Your Institution';
  if (userAvatarEl) {
    if (user && user.profileImage) {
      userAvatarEl.textContent = '';
      userAvatarEl.style.backgroundImage = `url('${user.profileImage}')`;
      userAvatarEl.style.backgroundSize = 'cover';
      userAvatarEl.style.backgroundPosition = 'center';
    } else {
      userAvatarEl.style.backgroundImage = 'none';
      userAvatarEl.textContent = (user && user.avatar) || firstName.slice(0, 2).toUpperCase();
    }
  }
  if (userNameEl) userNameEl.textContent = fullName;
  if (window.syncGlobalUserAvatars) window.syncGlobalUserAvatars();

  // Compute Metrics
  const total = complaints.length;
  const submitted = complaints.filter(c => c.status === 'Submitted').length;
  const inProgress = complaints.filter(c => ['Under Review', 'Assigned', 'In Progress', 'Awaiting Student', 'Reopened'].includes(c.status)).length;
  const resolved = complaints.filter(c => c.status === 'Resolved').length;

  const totalEl = document.getElementById('statTotal');
  const subEl = document.getElementById('statSubmitted');
  const progEl = document.getElementById('statInProgress');
  const resEl = document.getElementById('statResolved');

  if (totalEl) totalEl.textContent = total;
  if (subEl) subEl.textContent = submitted;
  if (progEl) progEl.textContent = inProgress;
  if (resEl) resEl.textContent = resolved;

  // Render Status Distribution Chart with Chart.js
  const ctx = document.getElementById('studentStatusChart');
  if (ctx && typeof Chart !== 'undefined') {
    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Submitted', 'In Progress / Review', 'Resolved'],
        datasets: [{
          data: [submitted || (total === 0 ? 1 : 0), inProgress || (total === 0 ? 1 : 0), resolved || (total === 0 ? 1 : 0)],
          backgroundColor: ['#3157D5', '#7457F5', '#159B72'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' }
        },
        cutout: '70%'
      }
    });
  }

  // Render Recent Complaints Table
  const tableBody = document.getElementById('recentComplaintsTableBody');
  const emptyState = document.getElementById('dashboardEmptyState');

  if (complaints.length === 0) {
    if (tableBody) tableBody.innerHTML = '';
    if (emptyState) emptyState.style.display = 'flex';
  } else {
    if (emptyState) emptyState.style.display = 'none';
    if (tableBody) {
      tableBody.innerHTML = complaints.slice(0, 5).map(c => `
        <tr>
          <td class="cell-id">${escapeHtml(c.id)}</td>
          <td style="font-weight: 500;">
            <a href="complaint-details.html?id=${escapeHtml(c.id)}" onclick="sessionStorage.setItem('proofvoice_current_complaint_id', '${escapeHtml(c.id)}'); localStorage.setItem('proofvoice_last_viewed_complaint_id', '${escapeHtml(c.id)}');" style="color: var(--color-navy); text-decoration: none; font-weight:600;">
              ${escapeHtml(c.title)}
            </a>
            <div class="text-xs text-muted">Loc: ${escapeHtml(c.location)}</div>
          </td>
          <td><span class="badge" style="background:#F1F5F9; color:#475569;">${escapeHtml(c.category)}</span></td>
          <td class="text-muted text-xs">${formatDateOnly(c.submittedAt)}</td>
          <td>${renderStatusBadge(c.status)}</td>
          <td class="text-right">
            <a href="complaint-details.html?id=${escapeHtml(c.id)}" onclick="sessionStorage.setItem('proofvoice_current_complaint_id', '${escapeHtml(c.id)}'); localStorage.setItem('proofvoice_last_viewed_complaint_id', '${escapeHtml(c.id)}');" class="btn btn-secondary btn-sm">
              Track Progress
            </a>
          </td>
        </tr>
      `).join('');
    }
  }

  // Render Recent Activity Feed
  const activityList = document.getElementById('studentActivityFeed');
  if (activityList) {
    const recentActivities = [];
    complaints.forEach(c => {
      if (c.history && c.history.length > 0) {
        c.history.forEach(h => {
          recentActivities.push({
            complaintId: c.id,
            complaintTitle: c.title,
            status: h.status,
            timestamp: h.timestamp,
            actor: h.actor,
            remarks: h.remarks
          });
        });
      }
    });

    recentActivities.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    if (recentActivities.length > 0) {
      activityList.innerHTML = recentActivities.slice(0, 4).map(act => `
        <li class="activity-item">
          <div class="activity-dot"></div>
          <div class="activity-body">
            <div class="activity-title">
              <strong>${escapeHtml(act.complaintId)}:</strong> ${escapeHtml(act.status)}
            </div>
            <p class="activity-meta">${escapeHtml(act.remarks || '')}</p>
            <div class="activity-meta" style="font-size: 11px;">
              ${formatDateTime(act.timestamp)} by ${escapeHtml(act.actor)}
            </div>
          </div>
        </li>
      `).join('');
    } else {
      activityList.innerHTML = `<li class="text-muted text-xs" style="padding: 1rem 0;">No status changes recorded yet.</li>`;
    }
  }
}

async function loadMyComplaintsPage() {
  const searchInput = document.getElementById('myComplaintsSearch');
  const statusFilter = document.getElementById('myComplaintsStatusFilter');
  const categoryFilter = document.getElementById('myComplaintsCategoryFilter');
  const tableBody = document.getElementById('myComplaintsTableBody');
  const emptyState = document.getElementById('myComplaintsEmpty');
  const countSpan = document.getElementById('complaintsCountSpan');

  const initial = await resolveStudentContext();
  const user = initial.user;
  const institution = initial.institution;

  // Populate Categories
  if (categoryFilter && institution && institution.categories) {
    categoryFilter.innerHTML = '<option value="All">All Categories</option>';
    institution.categories.forEach(cat => {
      categoryFilter.innerHTML += `<option value="${escapeHtml(cat)}">${escapeHtml(cat)}</option>`;
    });
  }

  async function renderList() {
    const filter = {
      search: searchInput ? searchInput.value.trim() : '',
      status: statusFilter ? statusFilter.value : 'All',
      category: categoryFilter ? categoryFilter.value : 'All'
    };

    const ctx = await resolveStudentContext(filter);
    const complaints = ctx.complaints;

    if (countSpan) countSpan.textContent = `Showing ${complaints.length} complaints`;

    if (complaints.length === 0) {
      if (tableBody) tableBody.innerHTML = '';
      if (emptyState) emptyState.style.display = 'flex';
    } else {
      if (emptyState) emptyState.style.display = 'none';
      if (tableBody) {
        tableBody.innerHTML = complaints.map(c => `
          <tr>
            <td class="cell-id">${escapeHtml(c.id)}</td>
            <td>
              <div style="font-weight: 600; color: var(--color-navy); margin-bottom: 2px;">
                <a href="complaint-details.html?id=${escapeHtml(c.id)}" onclick="sessionStorage.setItem('proofvoice_current_complaint_id', '${escapeHtml(c.id)}'); localStorage.setItem('proofvoice_last_viewed_complaint_id', '${escapeHtml(c.id)}');" style="text-decoration:none; color:inherit;">
                  ${escapeHtml(c.title)}
                </a>
              </div>
              <div class="text-xs text-muted" style="display:flex; gap:8px;">
                <span>Location: ${escapeHtml(c.location)}</span>
                <span>•</span>
                <span>Input: ${c.originalInputMethod === 'voice' ? '🎙️ Voice' : '⌨️ Text'}</span>
              </div>
            </td>
            <td><span class="badge" style="background:#F1F5F9; color:#475569;">${escapeHtml(c.category)}</span></td>
            <td>${renderPriorityBadge(c.priority)}</td>
            <td class="text-muted text-xs">${formatDateTime(c.submittedAt)}</td>
            <td>${renderStatusBadge(c.status)}</td>
            <td class="text-right">
              <div style="display:flex; justify-content:flex-end; gap:6px; flex-wrap:nowrap;">
                <a href="complaint-details.html?id=${escapeHtml(c.id)}" onclick="sessionStorage.setItem('proofvoice_current_complaint_id', '${escapeHtml(c.id)}'); localStorage.setItem('proofvoice_last_viewed_complaint_id', '${escapeHtml(c.id)}');" class="btn btn-secondary btn-sm" title="View details and track resolution">
                  View & Track
                </a>
                <button type="button" class="btn btn-outline btn-sm edit-my-complaint-btn" data-id="${escapeHtml(c.id)}" title="Edit Application" style="padding:4px 8px; font-size:11px; background:#fff; border-color:#CBD5E1; color:#0F172A;">
                  ✏️ Edit
                </button>
                <button type="button" class="btn btn-outline btn-sm delete-my-complaint-btn" data-id="${escapeHtml(c.id)}" title="Delete Complaint" style="padding:4px 8px; font-size:11px; background:#fff; border-color:#FECACA; color:#DC2626;">
                  🗑️ Delete
                </button>
              </div>
            </td>
          </tr>
        `).join('');
      }
    }
  }

  // Edit & Delete Complaint Handlers
  setupEditComplaintModal(renderList);

  if (tableBody) {
    tableBody.addEventListener('click', async (e) => {
      const editBtn = e.target.closest('.edit-my-complaint-btn');
      if (editBtn) {
        const id = editBtn.dataset.id;
        const ctx = await resolveStudentContext();
        const found = ctx.complaints.find(c => c.id === id);
        if (found && window.openEditComplaintModal) window.openEditComplaintModal(found);
      }

      const delBtn = e.target.closest('.delete-my-complaint-btn');
      if (delBtn) {
        const id = delBtn.dataset.id;
        const confirmed = window.confirm(`Are you sure you want to delete grievance application ${id}? This action cannot be undone.`);
        if (!confirmed) return;

        try {
          await window.proofVoiceApi.deleteComplaint(id);
          await renderList();
          showToast('success', 'Complaint Deleted', `Complaint ${id} has been deleted successfully.`);
        } catch (err) {
          showToast('error', 'Delete Failed', err.message || 'Unable to delete complaint.');
        }
      }
    });
  }

  if (searchInput) searchInput.addEventListener('input', renderList);
  if (statusFilter) statusFilter.addEventListener('change', renderList);
  if (categoryFilter) categoryFilter.addEventListener('change', renderList);

  renderList();
}

async function loadComplaintDetailsPage() {
  const urlParams = new URLSearchParams(window.location.search);
  let complaintId = urlParams.get('id') || urlParams.get('complaint_id');

  if (!complaintId) {
    complaintId = sessionStorage.getItem('proofvoice_current_complaint_id') || localStorage.getItem('proofvoice_last_viewed_complaint_id');
  }

  // If still missing, automatically pick the student's latest complaint
  if (!complaintId) {
    try {
      const studentCtx = await resolveStudentContext();
      if (studentCtx && studentCtx.complaints && studentCtx.complaints.length > 0) {
        complaintId = studentCtx.complaints[0].id;
        sessionStorage.setItem('proofvoice_current_complaint_id', complaintId);
        window.history.replaceState({}, '', '?id=' + encodeURIComponent(complaintId));
      }
    } catch (e) {}
  }

  if (!complaintId) {
    const mainEl = document.getElementById('complaintDetailsHeader');
    if (mainEl) {
      mainEl.innerHTML = `
        <div class="card" style="padding:3rem; text-align:center;">
          <h2 style="color:var(--color-navy); margin-bottom:1rem;">No Complaint Selected</h2>
          <p class="text-muted" style="margin-bottom:1.5rem;">You do not have an active complaint selected to view. Create a new complaint or choose one from your list.</p>
          <div style="display:flex; justify-content:center; gap:12px;">
            <a href="new-complaint.html" class="btn btn-primary">Create New Complaint</a>
            <a href="my-complaints.html" class="btn btn-secondary">My Complaints</a>
          </div>
        </div>
      `;
    }
    return;
  }

  let complaint = null;
  try {
    if (window.proofVoiceApi && window.proofVoiceApi.isLiveSession()) {
      complaint = await window.proofVoiceApi.getComplaint(complaintId);
    }
  } catch (err) {
    console.warn('[ProofVoice Student] Live fetch by ID failed, falling back:', err);
  }

  if (!complaint) {
    complaint = window.proofVoiceDb.getComplaintById(complaintId);
  }

  // Safety net: Check initial demo complaints directly if custom session user
  if (!complaint && typeof INITIAL_DEMO_DATA !== 'undefined' && INITIAL_DEMO_DATA.complaints) {
    complaint = INITIAL_DEMO_DATA.complaints.find(c => String(c.id).toLowerCase() === String(complaintId).toLowerCase());
  }

  if (!complaint) {
    showToast('error', 'Complaint Not Found', `Complaint record "${complaintId}" was not found.`);
    const mainEl = document.getElementById('complaintDetailsHeader');
    if (mainEl) {
      mainEl.innerHTML = `
        <div class="card" style="padding:3rem; text-align:center;">
          <h2 style="color:var(--color-navy); margin-bottom:1rem;">Complaint Record Inaccessible</h2>
          <p class="text-muted" style="margin-bottom:1.5rem;">Complaint <strong>${escapeHtml(complaintId)}</strong> could not be located in your active student records.</p>
          <a href="my-complaints.html" class="btn btn-primary">Return to My Complaints</a>
        </div>
      `;
    }
    return;
  }

  sessionStorage.setItem('proofvoice_current_complaint_id', complaint.id);
  localStorage.setItem('proofvoice_last_viewed_complaint_id', complaint.id);

  function renderStudentComplaint(c) {
    // Fill Header Elements
    const idEl = document.getElementById('detailsComplaintId');
    const titleEl = document.getElementById('detailsComplaintTitle');
    const statusBadgeEl = document.getElementById('detailsStatusBadge');
    const priorityBadgeEl = document.getElementById('detailsPriorityBadge');
    const dateEl = document.getElementById('detailsSubmissionDate');
    const deptEl = document.getElementById('detailsAssignedDept');
    const locationEl = document.getElementById('detailsLocation');
    const origDescEl = document.getElementById('detailsOriginalDescription');
    const formalAppEl = document.getElementById('detailsFormalApplication');

    if (idEl) idEl.textContent = c.id;
    if (titleEl) titleEl.textContent = c.title;
    if (statusBadgeEl) statusBadgeEl.innerHTML = renderStatusBadge(c.status);
    if (priorityBadgeEl) priorityBadgeEl.innerHTML = renderPriorityBadge(c.priority);
    if (dateEl) dateEl.textContent = formatDateTime(c.submittedAt);
    if (deptEl) deptEl.textContent = c.assignedDepartment || 'Pending Assignment';
    if (locationEl) locationEl.textContent = c.location || 'Campus Premises';
    if (origDescEl) origDescEl.textContent = c.originalTranscription || 'N/A';
    if (formalAppEl) formalAppEl.textContent = c.formalApplication || 'N/A';

    // Render Status Timeline with actual events (Section 9)
    const timelineContainer = document.getElementById('detailsTimeline');
    if (timelineContainer && c.history) {
      timelineContainer.innerHTML = c.history.map((h, idx) => {
        const isLast = idx === c.history.length - 1;
        return `
          <div class="timeline-item ${isLast ? 'is-current' : 'is-completed'}">
            <div class="timeline-dot">
              ${isLast ? '●' : '✓'}
            </div>
            <div class="timeline-content">
              <div class="timeline-header">
                <span class="timeline-title">${escapeHtml(h.status)}</span>
                <span class="timeline-date">${formatDateTime(h.timestamp)}</span>
              </div>
              <div class="text-xs text-muted">Action by: ${escapeHtml(h.actor)}</div>
              ${h.remarks ? `<p class="timeline-remark">${escapeHtml(h.remarks)}</p>` : ''}
            </div>
          </div>
        `;
      }).join('');
    }

    // Display Special Status Notices: Resolved, Rejected, or Awaiting Student
    const alertContainer = document.getElementById('specialStatusAlertContainer');
    if (alertContainer) {
      if (c.status === 'Resolved') {
        alertContainer.innerHTML = `
          <div class="alert alert-success" style="margin-bottom:var(--space-6);">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
              <div>
                <strong>Grievance Marked as Resolved</strong>
                <div style="font-size:13px; margin-top:2px;">${escapeHtml(c.resolutionSummary || 'The assigned institutional department has verified and completed the necessary resolution.')}</div>
              </div>
              <button type="button" class="btn btn-secondary btn-sm" id="openReopenModalBtn" style="background:#FFFFFF;">
                Issue Persists? Request Reopening
              </button>
            </div>
          </div>
        `;
      } else if (c.status === 'Rejected') {
        const lastHistory = c.history && c.history.length > 0 ? c.history[c.history.length - 1] : null;
        alertContainer.innerHTML = `
          <div class="alert alert-danger" style="margin-bottom:var(--space-6);">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
              <div>
                <strong>Application Rejected by Administration</strong>
                <div style="font-size:13px; margin-top:2px;">Reason: ${escapeHtml(lastHistory?.remarks || 'Application does not fall within institutional jurisdiction or lacks specific evidence.')}</div>
              </div>
              <button type="button" class="btn btn-secondary btn-sm" id="openReopenModalBtn" style="background:#FFFFFF;">
                Submit Appeal / Request Reopening
              </button>
            </div>
          </div>
        `;
      } else if (c.status === 'Awaiting Student') {
        const lastHistory = c.history && c.history.length > 0 ? c.history[c.history.length - 1] : null;
        alertContainer.innerHTML = `
          <div class="alert alert-warning" style="margin-bottom:var(--space-6);">
            <strong>Action Required: Additional Information Requested</strong>
            <div style="font-size:13px; margin-top:2px;">${escapeHtml(lastHistory?.remarks || 'The handling department requires additional photos or room location details.')}</div>
          </div>
        `;
      } else {
        alertContainer.innerHTML = '';
      }

      // Bind Reopen Button if present
      const reopenBtn = document.getElementById('openReopenModalBtn');
      if (reopenBtn) {
        reopenBtn.addEventListener('click', () => {
          openModal('reopenComplaintModal');
        });
      }
    }
  }

  // Initial render
  renderStudentComplaint(complaint);

  // Setup Read Aloud TTS for application
  const ttsBtn = document.getElementById('detailsTtsBtn');
  let isSpeaking = false;
  if (ttsBtn) {
    ttsBtn.addEventListener('click', () => {
      if (!isSpeaking) {
        isSpeaking = true;
        ttsBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg> Stop Reading`;
        speakText(complaint.formalApplication, null, () => {
          isSpeaking = false;
          ttsBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg> Read Aloud`;
        });
      } else {
        stopSpeaking();
        isSpeaking = false;
        ttsBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg> Read Aloud`;
      }
    });
  }

  // Handle Reopen Submission Modal
  const submitReopenBtn = document.getElementById('submitReopenBtn');
  const reopenReasonInput = document.getElementById('reopenReasonInput');

  if (submitReopenBtn && reopenReasonInput) {
    submitReopenBtn.addEventListener('click', async () => {
      const reason = reopenReasonInput.value.trim();
      if (!reason) {
        showToast('error', 'Missing Explanation', 'Please explain why the issue persists.');
        return;
      }

      submitReopenBtn.disabled = true;
      submitReopenBtn.innerHTML = `<span class="spinner"></span> Transmitting Request...`;

      try {
        await window.proofVoiceApi.reopenComplaint(complaint.id, reason);
        complaint.status = 'Reopened';
        if (!complaint.history) complaint.history = [];
        complaint.history.push({
          status: 'Reopened',
          timestamp: new Date().toISOString(),
          actor: 'You (Student)',
          remarks: `Student requested reopening: ${reason}`
        });

        renderStudentComplaint(complaint);
        closeModal('reopenComplaintModal');
        reopenReasonInput.value = '';
        showToast('success', 'Complaint Reopened', 'Reopening request transmitted to administration.');
      } catch (err) {
        showToast('error', 'Reopening Failed', err.message || 'Could not transmit request.');
      } finally {
        submitReopenBtn.disabled = false;
        submitReopenBtn.innerHTML = 'Submit Reopen Request';
      }
    });
  }

  // Handle Edit Application & Delete on Details Page
  const detailsEditBtn = document.getElementById('detailsEditBtn');
  const detailsDeleteBtn = document.getElementById('detailsDeleteBtn');

  setupEditComplaintModal(() => {
    window.location.reload();
  });

  if (detailsEditBtn) {
    detailsEditBtn.addEventListener('click', () => {
      window.openEditComplaintModal(complaint);
    });
  }

  if (detailsDeleteBtn) {
    detailsDeleteBtn.addEventListener('click', async () => {
      const confirmed = window.confirm(`Are you sure you want to delete grievance application ${complaint.id}? This action cannot be undone.`);
      if (!confirmed) return;

      try {
        await window.proofVoiceApi.deleteComplaint(complaint.id);
        showToast('success', 'Complaint Deleted', `Complaint ${complaint.id} has been deleted successfully.`);
        setTimeout(() => {
          window.location.href = 'my-complaints.html';
        }, 1000);
      } catch (err) {
        showToast('error', 'Delete Failed', err.message || 'Unable to delete complaint.');
      }
    });
  }
}

function setupEditComplaintModal(onSuccessCallback) {
  const editModal = document.getElementById('editComplaintModal');
  const editForm = document.getElementById('editComplaintForm');
  const closeEditBtn = document.getElementById('closeEditModalBtn');
  const cancelEditBtn = document.getElementById('cancelEditModalBtn');
  const saveEditBtn = document.getElementById('saveEditModalBtn');

  window.openEditComplaintModal = function(complaint) {
    if (!editModal) return;
    document.getElementById('editTargetComplaintId').value = complaint.id;
    document.getElementById('editModalComplaintId').textContent = complaint.id;
    document.getElementById('editComplaintTitle').value = complaint.title || '';
    document.getElementById('editComplaintCategory').value = complaint.category || '';
    document.getElementById('editComplaintUrgency').value = complaint.priority || complaint.urgency || 'Medium';
    document.getElementById('editComplaintLocation').value = complaint.location || complaint.fullIssueLocation || '';
    document.getElementById('editComplaintText').value = complaint.formalApplication || complaint.description || complaint.originalTranscription || '';
    editModal.style.display = 'flex';
  };

  function closeEditModal() {
    if (editModal) editModal.style.display = 'none';
  }

  if (closeEditBtn) closeEditBtn.addEventListener('click', closeEditModal);
  if (cancelEditBtn) cancelEditBtn.addEventListener('click', closeEditModal);

  if (editForm && !editForm._boundListener) {
    editForm._boundListener = true;
    editForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const id = document.getElementById('editTargetComplaintId').value;
      const title = document.getElementById('editComplaintTitle').value.trim();
      const category = document.getElementById('editComplaintCategory').value.trim();
      const urgency = document.getElementById('editComplaintUrgency').value;
      const location = document.getElementById('editComplaintLocation').value.trim();
      const text = document.getElementById('editComplaintText').value.trim();

      if (!title || !location || !text) {
        showToast('error', 'Missing Information', 'Please complete title, location, and application text.');
        return;
      }

      if (saveEditBtn) {
        saveEditBtn.disabled = true;
        saveEditBtn.textContent = 'Saving Changes...';
      }

      try {
        await window.proofVoiceApi.updateComplaint(id, {
          title,
          category,
          urgency,
          priority: urgency,
          location,
          formalApplication: text,
          description: text
        });

        closeEditModal();
        if (typeof onSuccessCallback === 'function') {
          await onSuccessCallback();
        }
        showToast('success', 'Application Updated', `Complaint ${id} application has been updated successfully.`);
      } catch (err) {
        showToast('error', 'Update Failed', err.message || 'Unable to update complaint application.');
      } finally {
        if (saveEditBtn) {
          saveEditBtn.disabled = false;
          saveEditBtn.textContent = 'Save Application Changes';
        }
      }
    });
  }
}
