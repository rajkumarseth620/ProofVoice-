/**
 * ProofVoice - Administrator Dashboard, Complaints Management & Analytics (v3)
 * Implements Section 10 & 11: Multi-tenant administrative overview, status transitions,
 * internal notes, public remarks, CSV export, and filtered views.
 */

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('adminStatsGrid')) {
    loadAdminDashboard();
  }

  if (document.getElementById('adminComplaintsTableBody')) {
    loadAdminComplaintsTable();
  }

  if (document.getElementById('adminDetailsHeader')) {
    loadAdminComplaintDetails();
  }

  if (document.getElementById('analyticsChartsGrid')) {
    loadAnalyticsPage();
  }
});

async function resolveAdminContext(filter) {
  if (window.proofVoiceApi && window.proofVoiceApi.isLiveSession()) {
    let user = window.proofVoiceApi.getStoredUser();
    if (!user && typeof window.proofVoiceApi.getCurrentUser === 'function') {
      try {
        user = await window.proofVoiceApi.getCurrentUser();
      } catch (e) {}
    }
    user = user || {};
    const instObj = (window.proofVoiceDb && user.institutionId) ? (window.proofVoiceDb.getInstitution(user.institutionId) || {}) : {};
    let complaints = [];
    try {
      complaints = await window.proofVoiceApi.getComplaints(filter || {}, 'admin');
    } catch (e) {
      console.warn('Failed to fetch admin complaints:', e);
    }
    if (!Array.isArray(complaints)) complaints = [];
    return {
      user,
      institution: {
        name: (user.role === 'superadmin' || user.backendRole === 'PLATFORM_SUPERADMIN') ? 'Campus Administration Workspace' : (user.institutionName || instObj.name || 'Campus Administration Workspace'),
        departments: (instObj.departments && instObj.departments.length > 0) ? instObj.departments : [
          'Estate & Maintenance',
          'Hostel Administration',
          'Academic Affairs',
          'IT & Network Services',
          'Dean of Student Welfare'
        ],
        categories: (instObj.categories && instObj.categories.length > 0) ? instObj.categories : [
          'Hostel & Accommodation',
          'Infrastructure & Maintenance',
          'Academic & Faculty',
          'Sanitation & Hygiene',
          'IT & Network Issues',
          'Classroom and Laboratory',
          'Water and Sanitation',
          'Other'
        ]
      },
      complaints
    };
  }
  const user = (window.proofVoiceDb ? window.proofVoiceDb.getCurrentUser() : null) || {};
  const institution = (window.proofVoiceDb && user.institutionId) ? (window.proofVoiceDb.getInstitution(user.institutionId) || {}) : { name: 'Campus Administration Workspace' };
  const complaints = (window.proofVoiceDb ? window.proofVoiceDb.getComplaints(filter || {}, 'admin') : []) || [];
  return { user, institution, complaints: Array.isArray(complaints) ? complaints : [] };
}

async function loadAdminDashboard() {
  const { user, institution, complaints } = await resolveAdminContext();

  // Institution title & admin details
  const instNameEl = document.getElementById('adminInstitutionName');
  const sidebarAvatar = document.getElementById('adminSidebarAvatar');
  const sidebarName = document.getElementById('adminSidebarName');
  const sidebarRole = document.getElementById('adminSidebarRole');

  if (instNameEl) instNameEl.textContent = institution.name;
  if (sidebarAvatar) {
    if (user.profileImage) {
      sidebarAvatar.textContent = '';
      sidebarAvatar.style.backgroundImage = `url('${user.profileImage}')`;
      sidebarAvatar.style.backgroundSize = 'cover';
      sidebarAvatar.style.backgroundPosition = 'center';
    } else {
      sidebarAvatar.style.backgroundImage = 'none';
      sidebarAvatar.textContent = user.avatar || user.fullName.slice(0, 2).toUpperCase();
    }
  }
  if (sidebarName) sidebarName.textContent = user.fullName;
  if (sidebarRole) sidebarRole.textContent = user.designation || 'Administrator';
  if (window.syncGlobalUserAvatars) window.syncGlobalUserAvatars();

  // Try fetching live dashboard metrics from Django API
  let liveMetrics = null;
  if (window.proofVoiceApi && window.proofVoiceApi.isLiveSession()) {
    try {
      const resp = await window.proofVoiceApi.getAdminDashboardMetrics();
      if (resp && resp.metrics) {
        liveMetrics = resp.metrics;
      }
    } catch (e) {
      console.warn('Could not fetch live dashboard metrics:', e);
    }
  }

  // Compute Metrics
  const total = liveMetrics ? liveMetrics.total_complaints : complaints.length;
  const newSubmissions = liveMetrics ? (liveMetrics.unassigned_complaints !== undefined ? liveMetrics.unassigned_complaints : liveMetrics.pending_review) : complaints.filter(c => c.status === 'Submitted').length;
  const underReview = liveMetrics ? liveMetrics.under_review : complaints.filter(c => c.status === 'Under Review').length;
  const inProgress = liveMetrics ? liveMetrics.in_progress : complaints.filter(c => ['In Progress', 'Assigned'].includes(c.status)).length;
  const resolved = liveMetrics ? liveMetrics.resolved : complaints.filter(c => c.status === 'Resolved').length;

  document.getElementById('adminStatTotal').textContent = total;
  document.getElementById('adminStatNew').textContent = newSubmissions;
  document.getElementById('adminStatReview').textContent = underReview;
  document.getElementById('adminStatProgress').textContent = inProgress;
  document.getElementById('adminStatResolved').textContent = resolved;

  // Check for pending staff/administrator access requests
  try {
    let pendingCount = 0;
    if (liveMetrics && liveMetrics.pending_admin_access_requests !== undefined) {
      pendingCount = liveMetrics.pending_admin_access_requests;
    } else {
      let adminReqs = [];
      if (window.proofVoiceApi && typeof window.proofVoiceApi.getAdminAccessRequests === 'function') {
        adminReqs = await window.proofVoiceApi.getAdminAccessRequests() || [];
      } else if (window.proofVoiceDb) {
        adminReqs = window.proofVoiceDb.getAdminRequests() || [];
      }
      pendingCount = (adminReqs || []).filter(r => (r.status || '').toUpperCase() === 'PENDING').length;
    }
    const existingBanner = document.getElementById('pendingAdminReqsAlert');
    if (pendingCount > 0) {
      if (!existingBanner) {
        const banner = document.createElement('div');
        banner.id = 'pendingAdminReqsAlert';
        banner.className = 'alert alert-info';
        banner.style.cssText = 'margin-bottom:var(--space-6); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; border-left:4px solid var(--color-primary);';
        banner.innerHTML = `
          <div style="display:flex; align-items:center; gap:12px;">
            <div style="width:36px; height:36px; border-radius:50%; background:var(--color-primary-light); color:var(--color-primary); display:flex; align-items:center; justify-content:center; font-weight:700; font-size:16px;">
              👥
            </div>
            <div>
              <strong style="color:var(--color-navy); font-size:14px;">Staff Administrator Requests Pending:</strong>
              <div class="text-xs text-muted" style="margin-top:2px;">
                ${pendingCount} staff member(s) have requested administrator access to your institution. Review their credentials to approve or reject.
              </div>
            </div>
          </div>
          <a href="users.html?tab=requests" class="btn btn-primary btn-sm" style="white-space:nowrap;">
            Review Access Requests (${pendingCount}) →
          </a>
        `;
        const statsGrid = document.getElementById('adminStatsGrid');
        if (statsGrid && statsGrid.parentNode) {
          statsGrid.parentNode.insertBefore(banner, statsGrid);
        }
      } else {
        existingBanner.querySelector('strong').textContent = 'Staff Administrator Requests Pending:';
        existingBanner.querySelector('.text-muted').textContent = `${pendingCount} staff member(s) have requested administrator access to your institution. Review their credentials to approve or reject.`;
        const link = existingBanner.querySelector('a');
        if (link) link.textContent = `Review Access Requests (${pendingCount}) →`;
      }
    } else if (existingBanner) {
      existingBanner.remove();
    }

    // Update sidebar link with pending badge if applicable
    const usersSidebarLinks = document.querySelectorAll('a[href="users.html"]');
    usersSidebarLinks.forEach(link => {
      if (pendingReqs.length > 0) {
        let b = link.querySelector('.sidebar-badge-requests');
        if (!b) {
          b = document.createElement('span');
          b.className = 'badge sidebar-badge-requests';
          b.style.cssText = 'margin-left:auto; background:var(--color-primary-light); color:var(--color-primary); font-size:10px; padding:2px 6px; border-radius:10px; font-weight:700;';
          link.appendChild(b);
        }
        b.textContent = pendingReqs.length;
      }
    });
  } catch (err) {
    console.warn('[ProofVoice Dashboard] Failed to check pending admin requests:', err);
  }

  // Render Charts with Chart.js
  if (typeof Chart !== 'undefined') {
    // 1. Status Distribution Doughnut
    const statusCtx = document.getElementById('adminStatusChart');
    if (statusCtx) {
      new Chart(statusCtx, {
        type: 'doughnut',
        data: {
          labels: ['Submitted', 'Under Review', 'In Progress', 'Resolved'],
          datasets: [{
            data: [newSubmissions || (total === 0 ? 1 : 0), underReview || (total === 0 ? 1 : 0), inProgress || (total === 0 ? 1 : 0), resolved || (total === 0 ? 1 : 0)],
            backgroundColor: ['#3157D5', '#D97706', '#7457F5', '#159B72'],
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom' } },
          cutout: '68%'
        }
      });
    }

    // 2. Category Distribution Bar Chart
    const catCtx = document.getElementById('adminCategoryChart');
    if (catCtx) {
      const catCounts = {};
      complaints.forEach(c => {
        catCounts[c.category] = (catCounts[c.category] || 0) + 1;
      });
      const catLabels = Object.keys(catCounts);
      const catData = Object.values(catCounts);

      new Chart(catCtx, {
        type: 'bar',
        data: {
          labels: catLabels.length > 0 ? catLabels : ['IT', 'Sanitation', 'Electricity', 'Labs'],
          datasets: [{
            label: 'Complaints',
            data: catData.length > 0 ? catData : [4, 3, 2, 5],
            backgroundColor: '#3157D5',
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true, ticks: { precision: 0 } }
          },
          plugins: { legend: { display: false } }
        }
      });
    }
  }

  // Populate Recent Complaints in Dashboard
  const tableBody = document.getElementById('adminRecentTableBody');
  if (tableBody) {
    if (complaints.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 2rem;">No complaints filed yet for this institution.</td></tr>`;
    } else {
      tableBody.innerHTML = complaints.slice(0, 5).map(c => `
        <tr>
          <td class="cell-id">${escapeHtml(c.id)}</td>
          <td>
            <a href="admin-complaint-details.html?id=${escapeHtml(c.id)}" onclick="sessionStorage.setItem('proofvoice_current_complaint_id', '${escapeHtml(c.id)}'); localStorage.setItem('proofvoice_last_viewed_complaint_id', '${escapeHtml(c.id)}');" style="font-weight:600; color:var(--color-navy); text-decoration:none;">
              ${escapeHtml(c.title)}
            </a>
            <div class="text-xs text-muted">By: ${escapeHtml(c.studentName)} (${escapeHtml(c.studentIdentifier)})</div>
          </td>
          <td><span class="badge" style="background:#F1F5F9; color:#475569;">${escapeHtml(c.category)}</span></td>
          <td>${renderPriorityBadge(c.priority)}</td>
          <td>${escapeHtml(c.assignedDepartment || 'Unassigned')}</td>
          <td>${renderStatusBadge(c.status)}</td>
          <td class="text-right">
            <a href="admin-complaint-details.html?id=${escapeHtml(c.id)}" onclick="sessionStorage.setItem('proofvoice_current_complaint_id', '${escapeHtml(c.id)}'); localStorage.setItem('proofvoice_last_viewed_complaint_id', '${escapeHtml(c.id)}');" class="btn btn-secondary btn-sm">
              Review
            </a>
          </td>
        </tr>
      `).join('');
    }
  }
}

async function loadAdminComplaintsTable() {
  const searchInput = document.getElementById('adminSearch');
  const statusFilter = document.getElementById('adminStatusFilter');
  const categoryFilter = document.getElementById('adminCategoryFilter');
  const deptFilter = document.getElementById('adminDeptFilter');
  const tableBody = document.getElementById('adminComplaintsTableBody');
  const countSpan = document.getElementById('adminTableCount');

  // Check URL query parameters (e.g. ?status=Unassigned or ?status=Under+Review)
  const urlParams = new URLSearchParams(window.location.search);
  const initialStatus = urlParams.get('status');
  if (initialStatus && statusFilter) {
    statusFilter.value = initialStatus;
  }

  const initial = await resolveAdminContext();
  const user = initial.user;
  const institution = initial.institution;

  // Sync workspace brand headers and user profile in sidebar & topbar
  const instNameEls = document.querySelectorAll('.sidebar-institution-name, #adminInstitutionName, #sidebarInstName, #topbarInst');
  instNameEls.forEach(el => { el.textContent = institution.name; });

  const sidebarAvatar = document.getElementById('adminSidebarAvatar');
  const sidebarName = document.getElementById('adminSidebarName');
  const sidebarRole = document.getElementById('adminSidebarRole');
  const topbarAvatar = document.getElementById('adminTopbarAvatar');

  if (sidebarName) sidebarName.textContent = user.fullName || 'Administrator';
  if (sidebarRole) sidebarRole.textContent = user.designation || 'Administrator';
  if (window.syncGlobalUserAvatars) {
    window.syncGlobalUserAvatars();
  } else {
    if (sidebarAvatar) sidebarAvatar.textContent = user.avatar || (user.fullName ? user.fullName.slice(0, 2).toUpperCase() : 'AD');
    if (topbarAvatar) topbarAvatar.textContent = user.avatar || (user.fullName ? user.fullName.slice(0, 2).toUpperCase() : 'AD');
  }

  if (deptFilter && institution && institution.departments) {
    deptFilter.innerHTML = '<option value="All">All Departments</option>';
    institution.departments.forEach(dept => {
      deptFilter.innerHTML += `<option value="${escapeHtml(dept)}">${escapeHtml(dept)}</option>`;
    });
  }

  if (categoryFilter && institution && institution.categories) {
    categoryFilter.innerHTML = '<option value="All">All Categories</option>';
    institution.categories.forEach(cat => {
      categoryFilter.innerHTML += `<option value="${escapeHtml(cat)}">${escapeHtml(cat)}</option>`;
    });
  }

  const isSuperAdmin = user.role === 'superadmin' || user.backendRole === 'PLATFORM_SUPERADMIN';
  let instFilter = document.getElementById('adminInstFilter');
  if (isSuperAdmin && !instFilter) {
    const filtersContainer = document.querySelector('.table-filters');
    if (filtersContainer) {
      instFilter = document.createElement('select');
      instFilter.id = 'adminInstFilter';
      instFilter.className = 'form-control';
      instFilter.style.cssText = 'width:auto; max-width:200px;';
      instFilter.innerHTML = '<option value="All">All Campuses</option>';
      filtersContainer.insertBefore(instFilter, filtersContainer.firstChild);

      if (window.proofVoiceApi && typeof window.proofVoiceApi.getInstitutions === 'function') {
        window.proofVoiceApi.getInstitutions().then(insts => {
          if (Array.isArray(insts)) {
            insts.forEach(it => {
              instFilter.innerHTML += `<option value="${escapeHtml(String(it.id))}">${escapeHtml(it.name)}</option>`;
            });
          }
        }).catch(() => {});
      }
      instFilter.addEventListener('change', renderRows);
    }
  }

  async function renderRows() {
    const filter = {
      search: searchInput ? searchInput.value.trim() : '',
      status: statusFilter ? statusFilter.value : 'All',
      category: categoryFilter ? categoryFilter.value : 'All',
      department: deptFilter ? deptFilter.value : 'All'
    };
    if (instFilter && instFilter.value !== 'All') {
      filter.institution_id = instFilter.value;
    }

    const ctx = await resolveAdminContext(filter);
    let complaints = ctx.complaints || [];

    // Special status check for Unassigned
    if (filter.status === 'Unassigned') {
      complaints = complaints.filter(c => !c.assignedDepartment || c.assignedDepartment === 'Unassigned');
    }

    if (countSpan) countSpan.textContent = `Showing ${complaints.length} records`;

    if (complaints.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="8" class="text-center text-muted" style="padding: 2.5rem;">No complaints match the selected filter criteria.</td></tr>`;
      return;
    }

    tableBody.innerHTML = complaints.map(c => `
      <tr>
        <td class="cell-id">${escapeHtml(c.id)}</td>
        <td>
          <a href="admin-complaint-details.html?id=${escapeHtml(c.id)}" onclick="sessionStorage.setItem('proofvoice_current_complaint_id', '${escapeHtml(c.id)}'); localStorage.setItem('proofvoice_last_viewed_complaint_id', '${escapeHtml(c.id)}');" style="font-weight:600; color:var(--color-navy); text-decoration:none;">
            ${escapeHtml(c.title)}
          </a>
          <div class="text-xs text-muted">
            ${isSuperAdmin && c.institutionName ? `Campus: <strong>${escapeHtml(c.institutionName)}</strong> • ` : ''}
            By: ${escapeHtml(c.studentName || 'Student')} (${escapeHtml(c.studentIdentifier || 'Verified')})
          </div>
        </td>
        <td><span class="badge" style="background:#F1F5F9; color:#475569;">${escapeHtml(c.category)}</span></td>
        <td>${renderPriorityBadge(c.priority)}</td>
        <td class="text-xs text-muted">${formatDateOnly(c.submittedAt)}</td>
        <td>${escapeHtml(c.assignedDepartment || 'Unassigned')}</td>
        <td>${renderStatusBadge(c.status)}</td>
        <td class="text-right">
          <a href="admin-complaint-details.html?id=${escapeHtml(c.id)}" onclick="sessionStorage.setItem('proofvoice_current_complaint_id', '${escapeHtml(c.id)}'); localStorage.setItem('proofvoice_last_viewed_complaint_id', '${escapeHtml(c.id)}');" class="btn btn-secondary btn-sm">
            Manage
          </a>
        </td>
      </tr>
    `).join('');
  }

  if (searchInput) searchInput.addEventListener('input', () => { renderRows(); });
  if (statusFilter) statusFilter.addEventListener('change', () => { renderRows(); });
  if (categoryFilter) categoryFilter.addEventListener('change', () => { renderRows(); });
  if (deptFilter) deptFilter.addEventListener('change', () => { renderRows(); });

  await renderRows();
}

async function loadAdminComplaintDetails() {
  const urlParams = new URLSearchParams(window.location.search);
  let complaintId = urlParams.get('id') || urlParams.get('complaint_id');

  if (!complaintId) {
    complaintId = sessionStorage.getItem('proofvoice_current_complaint_id') || localStorage.getItem('proofvoice_last_viewed_complaint_id');
  }

  // If still missing, automatically pick the latest institutional complaint
  if (!complaintId) {
    try {
      const adminCtx = await resolveAdminContext();
      if (adminCtx && adminCtx.complaints && adminCtx.complaints.length > 0) {
        complaintId = adminCtx.complaints[0].id;
        sessionStorage.setItem('proofvoice_current_complaint_id', complaintId);
        window.history.replaceState({}, '', '?id=' + encodeURIComponent(complaintId));
      }
    } catch (e) {}
  }

  if (!complaintId) {
    const mainEl = document.getElementById('adminDetailsHeader');
    if (mainEl) {
      mainEl.innerHTML = `
        <div class="card" style="padding: 3rem; text-align: center;">
          <h2 style="color:var(--color-navy); margin-bottom: 1rem;">No Complaint Selected</h2>
          <p class="text-muted" style="margin-bottom: 1.5rem;">Please select a complaint to manage from the complaints desk.</p>
          <a href="admin-complaints.html" class="btn btn-primary">Return to Complaints Desk</a>
        </div>
      `;
    }
    return;
  }

  let complaint = null;
  if (window.proofVoiceApi && window.proofVoiceApi.isLiveSession()) {
    try {
      complaint = await window.proofVoiceApi.getComplaint(complaintId, 'admin');
    } catch (e) {
      console.warn('[ProofVoice Admin] Live complaint fetch error, falling back to local DB:', e);
    }
  }
  if (!complaint) {
    complaint = window.proofVoiceDb.getComplaintById(complaintId, 'admin');
  }

  // Safety net: Check initial demo complaints directly if custom session user
  if (!complaint && typeof INITIAL_DEMO_DATA !== 'undefined' && INITIAL_DEMO_DATA.complaints) {
    complaint = INITIAL_DEMO_DATA.complaints.find(c => String(c.id).toLowerCase() === String(complaintId).toLowerCase() || String(c.numericId) === String(complaintId));
  }

  if (!complaint) {
    showToast('error', 'Record Not Found', `Complaint record "${complaintId}" was not found.`);
    const mainEl = document.getElementById('adminDetailsHeader');
    if (mainEl) {
      mainEl.innerHTML = `
        <div class="card" style="padding: 3rem; text-align: center;">
          <h2 style="color:var(--color-navy); margin-bottom: 1rem;">Complaint Record Inaccessible</h2>
          <p class="text-muted" style="margin-bottom: 1.5rem;">Complaint identifier <strong>${escapeHtml(complaintId)}</strong> could not be located in this institutional workspace.</p>
          <a href="admin-complaints.html" class="btn btn-primary">Return to All Complaints</a>
        </div>
      `;
    }
    return;
  }

  sessionStorage.setItem('proofvoice_current_complaint_id', complaint.id);
  localStorage.setItem('proofvoice_last_viewed_complaint_id', complaint.id);

  function renderDetails(c) {
    // Populate Left Column
    const adminIdEl = document.getElementById('adminId');
    if (adminIdEl) adminIdEl.textContent = c.id;
    const adminTitleEl = document.getElementById('adminTitle');
    if (adminTitleEl) adminTitleEl.textContent = c.title;
    const statusBadgeEl = document.getElementById('adminStatusBadge');
    if (statusBadgeEl) statusBadgeEl.innerHTML = renderStatusBadge(c.status);
    const priorityBadgeEl = document.getElementById('adminPriorityBadge');
    if (priorityBadgeEl) priorityBadgeEl.innerHTML = renderPriorityBadge(c.priority);
    const dateEl = document.getElementById('adminDate');
    if (dateEl) dateEl.textContent = formatDateTime(c.submittedAt);
    const studentNameEl = document.getElementById('adminStudentName');
    if (studentNameEl) studentNameEl.textContent = `${c.studentName || 'Student'} (${c.studentIdentifier || 'Verified'})`;
    const locEl = document.getElementById('adminLocation');
    if (locEl) locEl.textContent = c.location || 'Campus Premises';
    const catEl = document.getElementById('adminCategory');
    if (catEl) catEl.textContent = c.category;
    const origInputEl = document.getElementById('adminOriginalInput');
    if (origInputEl) origInputEl.textContent = c.originalTranscription || 'N/A';
    const formalLetterEl = document.getElementById('adminFormalLetter');
    if (formalLetterEl) formalLetterEl.textContent = c.formalApplication || 'N/A';

    // Populate Right Column Controls
    const statusSelect = document.getElementById('updateStatusSelect');
    const assigneeInput = document.getElementById('updateAssigneeInput');
    const publicRemarkInput = document.getElementById('updatePublicRemark');

    if (statusSelect) statusSelect.value = c.status;
    if (assigneeInput && !assigneeInput.value) assigneeInput.value = c.assignedTo || '';
    if (publicRemarkInput && c.resolutionSummary && !publicRemarkInput.value) publicRemarkInput.value = c.resolutionSummary;

    // Activity History
    const historyList = document.getElementById('adminHistoryTimeline');
    if (historyList && c.history) {
      historyList.innerHTML = c.history.map((h, i) => `
        <div class="timeline-item ${i === c.history.length - 1 ? 'is-current' : 'is-completed'}">
          <div class="timeline-dot">${i === c.history.length - 1 ? '●' : '✓'}</div>
          <div class="timeline-content">
            <div class="timeline-header">
              <span class="timeline-title">${escapeHtml(h.status)}</span>
              <span class="timeline-date">${formatDateTime(h.timestamp)}</span>
            </div>
            <div class="text-xs text-muted">By: ${escapeHtml(h.actor)}</div>
            ${h.remarks ? `<p class="timeline-remark">${escapeHtml(h.remarks)}</p>` : ''}
          </div>
        </div>
      `).join('');
    }

    // Internal Notes (Isolated from students)
    const notesContainer = document.getElementById('adminInternalNotesList');
    if (notesContainer) {
      if (c.adminNotes && c.adminNotes.length > 0) {
        notesContainer.innerHTML = c.adminNotes.map(n => `
          <div style="background:#FFFBEB; border:1px solid #FEF3C7; border-radius:var(--radius-md); padding:10px 14px; margin-bottom:8px;">
            <div class="text-xs font-semibold" style="color:#92400E; display:flex; justify-content:space-between;">
              <span>🔒 ${escapeHtml(n.author)}</span>
              <span style="font-weight:normal;">${formatDateTime(n.timestamp)}</span>
            </div>
            <div class="text-xs" style="color:#78350F; margin-top:4px; line-height:1.4;">${escapeHtml(n.text)}</div>
          </div>
        `).join('');
      } else {
        notesContainer.innerHTML = `<div class="text-xs text-muted">No internal notes added yet. Internal notes are invisible to students.</div>`;
      }
    }
  }

  // Initial render
  renderDetails(complaint);

  // Setup Read Aloud for Admin (Section 11)
  const ttsBtn = document.getElementById('adminTtsBtn');
  let isSpeaking = false;
  if (ttsBtn) {
    ttsBtn.addEventListener('click', () => {
      if (!isSpeaking) {
        isSpeaking = true;
        ttsBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg> Stop`;
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

  // Populate departments dropdown
  const statusSelect = document.getElementById('updateStatusSelect');
  const deptSelect = document.getElementById('updateDeptSelect');
  const assigneeInput = document.getElementById('updateAssigneeInput');
  const publicRemarkInput = document.getElementById('updatePublicRemark');

  const adminCtx = await resolveAdminContext();
  const institution = adminCtx.institution;
  if (deptSelect && institution.departments) {
    deptSelect.innerHTML = '<option value="">-- Unassigned --</option>';
    institution.departments.forEach(d => {
      deptSelect.innerHTML += `<option value="${escapeHtml(d)}" ${complaint.assignedDepartment === d ? 'selected' : ''}>${escapeHtml(d)}</option>`;
    });
  }

  // Save Status Updates Button
  const saveBtn = document.getElementById('saveAdminStatusBtn');
  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      const newStatus = statusSelect.value;
      const dept = deptSelect.value;
      const assignee = assigneeInput.value.trim();
      const publicRemark = publicRemarkInput.value.trim();
      const internalNoteInput = document.getElementById('updateInternalNote');
      const internalNote = internalNoteInput ? internalNoteInput.value.trim() : '';

      // Consequential Action Confirmation (Section 10)
      if (newStatus === 'Resolved' && !publicRemark) {
        if (!confirm('You are marking this complaint as Resolved. It is recommended to provide a resolution remark for the student. Proceed anyway?')) {
          return;
        }
      }

      if (newStatus === 'Rejected' && !publicRemark) {
        showToast('error', 'Rejection Reason Required', 'Please enter a public remark explaining the reason for rejection to the student.');
        publicRemarkInput.focus();
        return;
      }

      saveBtn.disabled = true;
      saveBtn.innerHTML = `<span class="spinner"></span> Saving Changes...`;

      try {
        await window.proofVoiceApi.updateComplaintStatus(complaint.id, newStatus, publicRemark, internalNote, dept, assignee);

        // Update in-memory complaint object
        complaint.status = newStatus;
        if (dept && dept !== '-- Unassigned --') complaint.assignedDepartment = dept;
        if (assignee) complaint.assignedTo = assignee;
        if (publicRemark) complaint.resolutionSummary = publicRemark;

        // Re-fetch latest complaint or append history locally
        if (window.proofVoiceApi.isLiveSession()) {
          try {
            const fresh = await window.proofVoiceApi.getComplaint(complaint.id, 'admin');
            if (fresh) complaint = fresh;
          } catch (e) {}
        } else {
          const fresh = window.proofVoiceDb.getComplaintById(complaint.id, 'admin');
          if (fresh) complaint = fresh;
        }

        renderDetails(complaint);
        if (internalNoteInput) internalNoteInput.value = '';
        showToast('success', 'Complaint Updated', `Status updated to ${newStatus}. Student notified.`);
      } catch (err) {
        showToast('error', 'Update Failed', err.message || 'Could not save update.');
      } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = 'Apply Updates & Notify Student';
      }
    });
  }
}

async function loadAnalyticsPage() {
  const { complaints } = await resolveAdminContext();

  // Export CSV handler
  const exportBtn = document.getElementById('exportCsvBtn');
  if (exportBtn) {
    exportBtn.addEventListener('click', () => {
      let csvContent = 'data:text/csv;charset=utf-8,Complaint ID,Title,Student,Category,Status,Department,Submission Date\n';
      complaints.forEach(c => {
        csvContent += `"${c.id}","${c.title}","${c.studentName}","${c.category}","${c.status}","${c.assignedDepartment || ''}","${c.submittedAt}"\n`;
      });
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement('a');
      link.setAttribute('href', encodedUri);
      link.setAttribute('download', `proofvoice_report_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      showToast('success', 'Export Complete', 'Institutional complaint report downloaded as CSV.');
    });
  }

  // Print handler
  const printBtn = document.getElementById('printReportBtn');
  if (printBtn) {
    printBtn.addEventListener('click', () => {
      window.print();
    });
  }

  if (typeof Chart === 'undefined') return;

  // Monthly Volume Chart
  const monthlyCtx = document.getElementById('analyticsMonthlyChart');
  if (monthlyCtx) {
    new Chart(monthlyCtx, {
      type: 'line',
      data: {
        labels: ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
        datasets: [{
          label: 'Total Submissions',
          data: [14, 22, 19, 31, 28, complaints.length + 35],
          borderColor: '#3157D5',
          backgroundColor: 'rgba(49, 87, 213, 0.08)',
          fill: true,
          tension: 0.35
        }, {
          label: 'Resolved',
          data: [12, 18, 17, 28, 25, 32],
          borderColor: '#159B72',
          backgroundColor: 'transparent',
          tension: 0.35
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'top' } }
      }
    });
  }

  // Department Breakdown
  const deptCtx = document.getElementById('analyticsDeptChart');
  if (deptCtx) {
    new Chart(deptCtx, {
      type: 'bar',
      data: {
        labels: ['IT Services', 'Water & Sanitation', 'Electrical', 'Hostel', 'Labs'],
        datasets: [{
          label: 'Complaints Managed',
          data: [18, 12, 9, 14, 7],
          backgroundColor: ['#3157D5', '#7457F5', '#F59E0B', '#10B981', '#6366F1'],
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
      }
    });
  }
}
