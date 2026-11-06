/**
 * ProofVoice - Core Application JavaScript (v3)
 * Shared utilities, toast system, modals, accessibility, multi-tenant role-switcher.
 */

// Setup Notification Badge counts across topbar & sidebar

// ============================================================================
// INDIAN MOBILE NUMBER (+91) VALIDATION & FORMATTING HELPERS
// ============================================================================
function setupIndianPhoneInput(inputEl, errorEl) {
  if (!inputEl) return;

  inputEl.setAttribute('maxlength', '10');
  inputEl.setAttribute('inputmode', 'numeric');
  inputEl.setAttribute('pattern', '[6-9][0-9]{9}');

  // Clean initial value if pre-filled
  if (inputEl.value) {
    let clean = inputEl.value.replace(/\D/g, '');
    if (clean.startsWith('91') && clean.length === 12) clean = clean.slice(2);
    else if (clean.startsWith('0') && clean.length === 11) clean = clean.slice(1);
    inputEl.value = clean.slice(-10);
  }

  // Strictly accept numbers only on typing / pasting
  inputEl.addEventListener('input', (e) => {
    let raw = e.target.value;
    let digits = raw.replace(/\D/g, '');
    if (digits.startsWith('91') && digits.length > 10) digits = digits.slice(2);
    else if (digits.startsWith('0') && digits.length > 10) digits = digits.slice(1);
    
    digits = digits.slice(0, 10);
    e.target.value = digits;

    if (errorEl) {
      if (digits.length === 0) {
        errorEl.textContent = '';
        errorEl.style.display = 'none';
        inputEl.classList.remove('is-invalid');
      } else if (digits.length < 10) {
        errorEl.textContent = `Enter ${10 - digits.length} more digit${10 - digits.length === 1 ? '' : 's'} (exactly 10 digits required).`;
        errorEl.style.display = 'block';
        inputEl.classList.add('is-invalid');
      } else if (!/^[6-9]/.test(digits)) {
        errorEl.textContent = 'Indian mobile numbers must start with 6, 7, 8, or 9.';
        errorEl.style.display = 'block';
        inputEl.classList.add('is-invalid');
      } else {
        errorEl.textContent = '';
        errorEl.style.display = 'none';
        inputEl.classList.remove('is-invalid');
      }
    }
  });

  inputEl.addEventListener('blur', () => {
    const val = inputEl.value.replace(/\D/g, '');
    if (val.length > 0 && val.length < 10) {
      if (errorEl) {
        errorEl.textContent = 'Mobile number must be exactly 10 digits.';
        errorEl.style.display = 'block';
      }
      inputEl.classList.add('is-invalid');
    }
  });
}
window.setupIndianPhoneInput = setupIndianPhoneInput;

function validateIndianPhoneNumber(rawVal, isRequired = false) {
  if (!rawVal || !String(rawVal).trim()) {
    if (isRequired) return { valid: false, message: 'Contact mobile number is required.' };
    return { valid: true, value: '' };
  }
  let digits = String(rawVal).replace(/\D/g, '');
  if (digits.startsWith('91') && digits.length === 12) digits = digits.slice(2);
  else if (digits.startsWith('0') && digits.length === 11) digits = digits.slice(1);

  if (digits.length !== 10) {
    return { valid: false, message: 'Mobile number must be exactly 10 digits (no more, no less).' };
  }
  if (!/^[6-9]\d{9}$/.test(digits)) {
    return { valid: false, message: 'Please enter a valid Indian mobile number starting with 6, 7, 8, or 9.' };
  }
  return { valid: true, value: `+91 ${digits}`, digits };
}
window.validateIndianPhoneNumber = validateIndianPhoneNumber;

function updateNotificationBadges(count) {
  let unread = count;
  const isLive = window.proofVoiceApi && window.proofVoiceApi.isLiveSession && window.proofVoiceApi.isLiveSession();

  if (unread === undefined) {
    const cached = localStorage.getItem('proofvoice_unread_count');
    if (cached !== null) {
      unread = parseInt(cached, 10);
    } else if (window.proofVoiceDb) {
      const notifs = window.proofVoiceDb.getNotifications();
      unread = notifs.filter(n => !n.read && !n.is_read).length;
    } else {
      unread = 0;
    }
  }

  if (unread < 0 || isNaN(unread)) unread = 0;
  localStorage.setItem('proofvoice_unread_count', String(unread));

  const badgeText = unread > 9 ? '9+' : String(unread);
  const isVisible = unread > 0;

  // Update topbar badge counts
  document.querySelectorAll('.notification-badge-count').forEach(el => {
    el.textContent = badgeText;
    el.style.display = isVisible ? 'flex' : 'none';
  });

  // Update sidebar notification count pills
  document.querySelectorAll('#sidebarNotifCount, #adminSidebarNotifCount, .nav-count').forEach(el => {
    el.textContent = badgeText;
    el.style.display = isVisible ? 'inline-flex' : 'none';
  });
}
window.updateNotificationBadges = updateNotificationBadges;

// Universally synchronize profile photos and initials across topbars, sidebars, and cards
function syncGlobalUserAvatars() {
  let user = null;
  if (window.proofVoiceApi && window.proofVoiceApi.getStoredUser) {
    user = window.proofVoiceApi.getStoredUser();
  }
  if (!user && window.proofVoiceDb) {
    user = window.proofVoiceDb.getCurrentUser();
  }
  if (!user) return;

  const displayName = user.fullName || user.full_name || user.name || user.email || 'Student';
  const firstName = displayName.trim().split(/\s+/)[0] || displayName;
  const initials = (user.avatar || (displayName ? displayName.split(' ').map(n => n[0]).join('').slice(0, 2) : 'PV')).toUpperCase();
  const photoUrl = user.profileImage || null;
  const isSuperAdmin = user.role === 'superadmin' || user.backendRole === 'PLATFORM_SUPERADMIN';
  const isAdmin = !isSuperAdmin && (user.role === 'admin' || user.backendRole === 'INSTITUTION_ADMIN');

  const avatarEls = document.querySelectorAll(
    '.user-avatar, #sidebarUserAvatar, #sidebarAvatar, #topbarAvatar, #adminTopbarAvatar, #adminSidebarAvatar, #profilePhotoDisplay, [id*="UserAvatar"], [id*="SidebarAvatar"], [id*="TopbarAvatar"]'
  );

  avatarEls.forEach(el => {
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') return;
    if (photoUrl) {
      el.textContent = '';
      el.style.backgroundImage = `url('${photoUrl}')`;
      el.style.backgroundSize = 'cover';
      el.style.backgroundPosition = 'center';
      el.style.backgroundColor = 'transparent';
      el.style.overflow = 'hidden';
    } else {
      el.style.backgroundImage = 'none';
      el.textContent = initials;
      el.style.backgroundColor = isSuperAdmin ? '#0F766E' : (isAdmin ? '#1E293B' : '#4F46E5');
      el.style.color = '#FFFFFF';
    }
  });

  // Update greeting immediately
  const greetingEls = document.querySelectorAll('#studentGreetingName, .greeting-user-name');
  greetingEls.forEach(el => {
    el.textContent = firstName;
  });

  // Update all user name displays including sidebar footers
  const userNameEls = document.querySelectorAll('#sidebarUserName, #adminUserName, #adminSidebarName, .user-name-display, .sidebar-footer .user-name, .user-name');
  userNameEls.forEach(el => {
    if (el.id !== 'studentGreetingName' && !el.classList.contains('greeting-user-name')) {
      el.textContent = displayName;
    }
  });

  const roleEls = document.querySelectorAll('#sidebarUserRole, #adminSidebarRole, .sidebar-footer .user-role-label, .user-role-label');
  roleEls.forEach(el => {
    if (isSuperAdmin) {
      el.textContent = 'Platform Super-Admin';
    } else if (isAdmin) {
      el.textContent = user.designation || 'Administrator';
    } else {
      const dept = user.department || 'Student';
      const sem = user.yearSemester ? ` • ${user.yearSemester}` : '';
      el.textContent = `${dept}${sem}`;
    }
  });

  const instName = user.institutionName || user.institution_name || (user.institution && user.institution.name) || '';
  if (instName) {
    const instEls = document.querySelectorAll(
      '#studentInstitutionName, #adminInstitutionName, #sidebarInstName, #topbarInst, .sidebar-institution-name, .user-tenant-display, .institution-pill span, [class*="sidebar-institution-name"], [id*="InstName"], [id*="InstitutionName"]'
    );
    instEls.forEach(el => {
      if (isSuperAdmin) {
        if (el.closest('.sidebar-institution-badge') || el.classList.contains('sidebar-institution-name')) {
          el.textContent = 'Platform Super-Admin';
          return;
        }
        if (el.id === 'topbarInst' || el.closest('.institution-pill')) {
          el.textContent = 'Campus Administration Workspace';
          return;
        }
      }
      if (el.textContent.includes('Tenant:')) {
        el.textContent = `Tenant: ${instName}`;
      } else {
        el.textContent = instName;
      }
    });
  }
}
window.syncGlobalUserAvatars = syncGlobalUserAvatars;
function showToast(type, title, message, duration = 4000) {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  let cleanMsg = '';
  if (message instanceof Error) {
    cleanMsg = message.message;
  } else if (message && typeof message === 'object') {
    cleanMsg = message.message || message.error || message.detail || (Array.isArray(message) ? message.join(', ') : JSON.stringify(message));
    if (typeof cleanMsg === 'object') cleanMsg = JSON.stringify(cleanMsg);
  } else {
    cleanMsg = String(message || '');
  }
  if (!cleanMsg || cleanMsg === '[object Object]') {
    cleanMsg = type === 'error' ? 'Action could not be completed.' : '';
  }

  const icons = {
    success: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`,
    error: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
    info: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
    warning: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`
  };

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-icon">${icons[type] || icons.info}</div>
    <div class="toast-content">
      <div class="toast-title">${escapeHtml(title)}</div>
      <div class="toast-message">${escapeHtml(cleanMsg)}</div>
    </div>
    <button class="toast-close" aria-label="Close">&times;</button>
  `;

  toast.querySelector('.toast-close').addEventListener('click', () => {
    toast.remove();
  });

  container.appendChild(toast);

  setTimeout(() => {
    if (toast.parentElement) toast.remove();
  }, duration);
}

// Modal helpers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('is-open');
    document.body.style.overflow = '';
  }
}

// Helper to escape HTML to prevent XSS
function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  if (typeof text === 'object') {
    text = text.message || text.error || text.detail || (Array.isArray(text) ? text.join(', ') : JSON.stringify(text));
    if (typeof text === 'object') text = JSON.stringify(text);
  }
  const str = String(text);
  if (str === '[object Object]') return '';
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return str.replace(/[&<>"']/g, m => map[m]);
}

// Helper for status badge HTML
function renderStatusBadge(status) {
  const s = (status || 'Submitted').toLowerCase().replace(/\s+/g, '-');
  return `<span class="badge badge-${s}"><span class="badge-dot"></span>${escapeHtml(status)}</span>`;
}

// Helper for priority badge HTML
function renderPriorityBadge(priority) {
  const p = (priority || 'medium').toLowerCase();
  return `<span class="badge badge-priority-${p}">${escapeHtml(priority)}</span>`;
}

// Format Date
function formatDateTime(isoStr) {
  if (!isoStr) return 'N/A';
  const d = new Date(isoStr);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function formatDateOnly(isoStr) {
  if (!isoStr) return 'N/A';
  const d = new Date(isoStr);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

// Speech Synthesis Audio Player (supports live Gnani AI Timbre TTS with browser fallback)
let currentTtsAudio = null;

async function speakText(text, onStart, onEnd, complaintId = null) {
  stopSpeaking();

  if (window.proofVoiceApi && window.proofVoiceApi.isLiveSession()) {
    try {
      showToast('info', 'Gnani AI Timbre TTS', 'Synthesizing voice audio via Gnani AI Timbre...', 2500);
      if (onStart) onStart();
      const audioUrl = await window.proofVoiceApi.textToSpeech(text, complaintId);
      if (audioUrl) {
        currentTtsAudio = new Audio(audioUrl);
        currentTtsAudio.onended = () => {
          currentTtsAudio = null;
          if (onEnd) onEnd();
        };
        currentTtsAudio.onerror = (e) => {
          console.warn('[ProofVoice TTS] Audio playback error on Gnani audio stream, falling back to browser synthesis:', e);
          currentTtsAudio = null;
          playBrowserSynthesis(text, onStart, onEnd);
        };
        await currentTtsAudio.play();
        return;
      }
    } catch (err) {
      console.warn('[ProofVoice TTS] Live Gnani TTS call failed, falling back to browser synthesis:', err);
    }
  }

  // Graceful fallback to browser speech synthesis
  playBrowserSynthesis(text, onStart, onEnd);
}

function playBrowserSynthesis(text, onStart, onEnd) {
  if (!('speechSynthesis' in window)) {
    showToast('warning', 'TTS Unavailable', 'Your browser does not support SpeechSynthesis.');
    if (onEnd) onEnd();
    return;
  }
  window.speechSynthesis.cancel();

  showToast('info', 'Audio Read Aloud', 'Playing preview via Browser SpeechSynthesis.', 2500);

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95;
  utterance.pitch = 1.0;

  if (onStart) utterance.onstart = onStart;
  if (onEnd) utterance.onend = onEnd;
  utterance.onerror = (err) => {
    console.error('Speech synthesis error:', err);
    if (onEnd) onEnd();
  };

  window.speechSynthesis.speak(utterance);
}

function stopSpeaking() {
  if (currentTtsAudio) {
    try {
      currentTtsAudio.pause();
      currentTtsAudio.currentTime = 0;
    } catch (e) {}
    currentTtsAudio = null;
  }
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
}

function getAppRootPrefix() {
  const path = (window.location.pathname || '').replace(/\\/g, '/');
  if (path.includes('/super-admin/dashboard/') || path.includes('/super-admin/login/')) {
    return '../../';
  }
  if (path.includes('/super-admin/')) {
    return '../';
  }
  return '';
}

function getNormalizedCurrentPage() {
  const path = (window.location.pathname || '').replace(/\\/g, '/');
  if (path.includes('/super-admin/dashboard/')) return 'super-admin-dashboard';
  if (path.includes('/super-admin/login/')) return 'super-admin-login';
  const parts = path.split('/');
  let filename = parts[parts.length - 1] || 'index.html';
  if (!filename.includes('.')) {
    filename = filename ? filename + '.html' : 'index.html';
  }
  return filename.toLowerCase().split('?')[0].split('#')[0];
}

const PUBLIC_ROUTES = new Set([
  '',
  '/',
  'index.html',
  'login.html',
  'register.html',
  'institution-register.html',
  'forgot-password.html',
  'help.html',
  'faq.html',
  'terms.html',
  'privacy.html',
  'super-admin-login',
  'super-admin-login.html'
]);

const STUDENT_ROUTES = new Set([
  'student-dashboard.html',
  'new-complaint.html',
  'review-complaint.html',
  'my-complaints.html',
  'complaint-details.html',
  'student-profile.html',
  'student-profile-complete.html',
  'student-notifications.html',
  'student-help.html'
]);

const ADMIN_ROUTES = new Set([
  'admin-dashboard.html',
  'admin-complaints.html',
  'admin-complaint-details.html',
  'departments.html',
  'users.html',
  'analytics.html',
  'institution-settings.html',
  'admin-profile.html',
  'admin-notifications.html',
  'admin-help.html'
]);

const SUPERADMIN_ROUTES = new Set([
  'super-admin.html',
  'super-admin-dashboard',
  '404.html'
]);

function enforceRouteGuard() {
  const page = getNormalizedCurrentPage();
  if (PUBLIC_ROUTES.has(page)) {
    return;
  }

  const rootPrefix = getAppRootPrefix();
  const token = localStorage.getItem('proofvoice_auth_token');
  const isAuth = Boolean(token && !String(token).startsWith('demo_token_'));

  if (!isAuth) {
    // Unauthenticated user attempting to access protected page
    const currentTarget = window.location.pathname.split('/').pop() + window.location.search + window.location.hash;
    window.location.replace(`${rootPrefix}login.html?redirect=${encodeURIComponent(currentTarget)}`);
    return;
  }

  const rawRole = (localStorage.getItem('proofvoice_active_role') || '').toLowerCase();
  const isAdmin = rawRole === 'admin' || rawRole === 'institution_admin';
  const isSuperAdmin = rawRole === 'superadmin' || rawRole === 'platform_superadmin';
  const isStudent = !isAdmin && !isSuperAdmin;

  if (STUDENT_ROUTES.has(page)) {
    if (isAdmin) {
      window.location.replace(`${rootPrefix}admin-dashboard.html`);
      return;
    }
    if (isSuperAdmin) {
      window.location.replace(`${rootPrefix}super-admin/dashboard/`);
      return;
    }
  }

  if (ADMIN_ROUTES.has(page)) {
    if (isStudent) {
      window.location.replace(`${rootPrefix}student-dashboard.html`);
      return;
    }
  }

  if (SUPERADMIN_ROUTES.has(page)) {
    if (!isSuperAdmin) {
      window.location.replace(isAdmin ? `${rootPrefix}admin-dashboard.html` : `${rootPrefix}student-dashboard.html`);
      return;
    }
  }
}

// Enforce route guard immediately
enforceRouteGuard();

// Centralized Protected Route Click Interceptor (captures clicks on links/buttons leading to protected features)
document.addEventListener('click', (e) => {
  const link = e.target.closest('a, button[data-target-url], [data-feature-target]');
  if (!link) return;

  let targetUrl = link.getAttribute('data-feature-target') || link.getAttribute('data-target-url') || link.getAttribute('href');
  if (!targetUrl || targetUrl.startsWith('#') || targetUrl.startsWith('javascript:')) return;

  const cleanTarget = targetUrl.split('?')[0].split('#')[0].split('/').pop();
  const isProtected = STUDENT_ROUTES.has(cleanTarget) || ADMIN_ROUTES.has(cleanTarget) || SUPERADMIN_ROUTES.has(cleanTarget);
  if (!isProtected) return;

  const token = localStorage.getItem('proofvoice_auth_token');
  const isAuth = Boolean(token && !String(token).startsWith('demo_token_'));

  if (!isAuth) {
    e.preventDefault();
    e.stopPropagation();
    const rootPrefix = getAppRootPrefix();
    const featureName = link.getAttribute('data-feature-name') || link.textContent.trim().slice(0, 40) || 'Feature';
    try { sessionStorage.setItem('proofvoice_auth_toast', `Please sign in to access ${featureName}.`); } catch (err) {}
    try { sessionStorage.setItem('proofvoice_return_to_home', 'true'); } catch (err) {}
    const redirectParam = encodeURIComponent(targetUrl);
    window.location.href = `${rootPrefix}login.html?redirect=${redirectParam}`;
    return;
  }
}, true);

// Also guard on back-forward cache restoration
window.addEventListener('pageshow', (event) => {
  enforceRouteGuard();
  
  const isHomePage = window.location.pathname.endsWith('index.html') ||
                     window.location.pathname === '/' ||
                     window.location.pathname.endsWith('ProofVoice/');

  if (isHomePage) {
    const returnFlag = sessionStorage.getItem('proofvoice_return_to_home') === 'true';
    const ref = document.referrer || '';
    const fromAuthOrDash = returnFlag || /login\.html|register\.html|dashboard/i.test(ref);

    if (event.persisted || fromAuthOrDash || !window.location.hash || window.location.hash === '#home') {
      try { sessionStorage.removeItem('proofvoice_return_to_home'); } catch (e) {}
      if (window.location.hash && window.location.hash !== '#home') {
        try { history.replaceState(null, document.title, window.location.pathname + window.location.search); } catch (e) {}
      }
      document.documentElement.style.scrollBehavior = 'auto';
      window.scrollTo(0, 0);
      const homeLink = document.getElementById('navLinkHome');
      if (homeLink) {
        document.querySelectorAll('#mainNavLinks .nav-link').forEach(l => l.classList.remove('active'));
        homeLink.classList.add('active');
        const navPill = document.getElementById('navActivePill');
        if (navPill && window.innerWidth > 768) {
          navPill.style.left = '0px';
          navPill.style.width = `${homeLink.getBoundingClientRect().width}px`;
          navPill.style.opacity = '1';
        }
      }
      setTimeout(() => {
        window.scrollTo(0, 0);
        document.documentElement.style.scrollBehavior = '';
      }, 50);
    }
  }
});

function setupLogoutLinks() {
  document.querySelectorAll('a[href="login.html"], a[href="404.html"], button[data-action="logout"], .logout-btn, #logoutBtn, #adminLogoutBtn, #superLogoutBtn, #portalSignOutBtn').forEach((link) => {
    link.addEventListener('click', async (e) => {
      e.preventDefault();

      const rawRole = (localStorage.getItem('proofvoice_active_role') || '').toLowerCase();
      let sessionUser = null;
      try { sessionUser = JSON.parse(localStorage.getItem('proofvoice_session_user') || 'null'); } catch (_) {}
      const isSuperAdmin = rawRole === 'superadmin' || rawRole === 'platform_superadmin' || Boolean(sessionUser && (sessionUser.is_superuser || sessionUser.role === 'superadmin' || sessionUser.backendRole === 'PLATFORM_SUPERADMIN'));
      const page = getNormalizedCurrentPage();
      const rootPrefix = getAppRootPrefix();

      // If Super Admin clicks logout from Admin Desk or Super Admin Console, redirect to 404 Gateway Hub
      if (isSuperAdmin && page !== '404.html') {
        window.location.replace(`${rootPrefix}404.html`);
        return;
      }

      // Normal student or institution admin sign-out (OR signing out from 404 gateway):
      // Completely flush all authentication credentials and redirect directly to login.html
      try {
        if (window.proofVoiceApi && window.proofVoiceApi.logout) {
          await window.proofVoiceApi.logout();
        }
      } catch (err) {}
      localStorage.removeItem('proofvoice_auth_token');
      localStorage.removeItem('proofvoice_session_user');
      localStorage.removeItem('proofvoice_active_role');
      localStorage.removeItem('proofvoice_active_tenant');
      localStorage.removeItem('proofvoice_unread_count');
      localStorage.removeItem('proofvoice_active_complaint_id');
      try { sessionStorage.clear(); } catch (e) {}
      window.location.replace(`${rootPrefix}login.html`);
    });
  });
}

// Global UI setup
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.breadcrumb-home-link, .auth-back-home-link, #authLogoHomeLink').forEach(link => {
    link.addEventListener('click', () => {
      try { sessionStorage.setItem('proofvoice_return_to_home', 'true'); } catch (e) {}
    });
  });
  setupLogoutLinks();
  initHomepageNavigationAndFeatures();

  // Highlight active nav links
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-link, .sidebar-nav-item').forEach(link => {
    const href = link.getAttribute('href');
    if (href && (href === currentPath || href.split('?')[0] === currentPath)) {
      link.classList.add('active');
    }
  });

  // Mobile menu toggle for public pages
  const mobileToggle = document.querySelector('.mobile-menu-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
      navLinks.classList.toggle('is-open');
    });
  }

  // Fully Working Sidebar Collapse / Expand Toggle (Desktop & Mobile)
  const sidebarToggles = document.querySelectorAll('.topbar-toggle-sidebar, #sidebarToggleBtn');
  const sidebar = document.querySelector('.app-sidebar') || document.getElementById('appSidebar');

  sidebarToggles.forEach(btn => {
    btn.setAttribute('title', 'Toggle Sidebar');
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();

      if (window.innerWidth > 768) {
        // Desktop: toggle body.sidebar-collapsed
        document.body.classList.toggle('sidebar-collapsed');
        const isCollapsed = document.body.classList.contains('sidebar-collapsed');
        try { localStorage.setItem('proofvoice_sidebar_collapsed', isCollapsed ? 'true' : 'false'); } catch (err) {}
      } else {
        // Mobile: toggle responsive off-canvas drawer with backdrop
        if (sidebar) {
          sidebar.classList.toggle('is-open');
          let backdrop = document.getElementById('sidebarMobileBackdrop');
          if (!backdrop) {
            backdrop = document.createElement('div');
            backdrop.id = 'sidebarMobileBackdrop';
            backdrop.className = 'sidebar-mobile-backdrop';
            backdrop.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.45);z-index:98;display:none;backdrop-filter:blur(2px);';
            document.body.appendChild(backdrop);
            backdrop.addEventListener('click', () => {
              sidebar.classList.remove('is-open');
              backdrop.style.display = 'none';
            });
          }
          backdrop.style.display = sidebar.classList.contains('is-open') ? 'block' : 'none';
        }
      }
    });
  });

  // Restore desktop sidebar collapsed preference if previously saved
  try {
    if (window.innerWidth > 768 && localStorage.getItem('proofvoice_sidebar_collapsed') === 'true') {
      document.body.classList.add('sidebar-collapsed');
    }
  } catch (err) {}

  // Interactive Profile & Settings Navigation (LK Avatar & Bottom Profile Section)
  function initProfileNavigation() {
    const rootPrefix = getAppRootPrefix();
    const isSuperAdminPage = window.location.pathname.includes('super-admin');
    let user = null;
    try {
      user = (window.proofVoiceApi && window.proofVoiceApi.getStoredUser) ? window.proofVoiceApi.getStoredUser() : null;
      if (!user && window.proofVoiceDb) user = window.proofVoiceDb.getCurrentUser();
    } catch (e) {}

    const isSuperAdminUser = (user && (user.role === 'superadmin' || user.role === 'super_admin' || user.backendRole === 'SUPER_ADMIN'));
    const isSuperAdmin = isSuperAdminPage || isSuperAdminUser;

    const isCurrentAdminPage = (window.location.pathname.includes('admin') && !isSuperAdminPage) ||
                               window.location.pathname.includes('analytics') ||
                               window.location.pathname.includes('departments') ||
                               window.location.pathname.includes('users') ||
                               window.location.pathname.includes('institution-settings');

    const isAdmin = !isSuperAdmin && (isCurrentAdminPage || (user && (user.role === 'admin' || user.backendRole === 'INSTITUTION_ADMIN')));

    let targetProfileUrl = `${rootPrefix}student-profile.html`;
    if (isSuperAdmin) {
      targetProfileUrl = isSuperAdminPage ? '#profile-settings' : `${rootPrefix}super-admin/dashboard/#profile-settings`;
    } else if (isAdmin) {
      targetProfileUrl = `${rootPrefix}admin-profile.html`;
    }

    function handleProfileNavigation(e, el) {
      if (isSuperAdmin && typeof window.switchSuperTab === 'function') {
        e.preventDefault();
        e.stopPropagation();
        window.switchSuperTab('profile-settings');
        return;
      }
      if (targetProfileUrl.startsWith('#')) {
        e.preventDefault();
        return;
      }
      const rawTarget = targetProfileUrl.replace(/^(\.\.\/)+/, '');
      if (!window.location.pathname.endsWith(rawTarget)) {
        e.preventDefault();
        e.stopPropagation();
        window.location.href = targetProfileUrl;
      }
    }

    // 1. Sidebar Footer (down for my profile)
    document.querySelectorAll('.sidebar-footer, #sidebarFooterUserLink, #superSidebarFooter').forEach(el => {
      el.style.cursor = 'pointer';
      el.setAttribute('title', 'Open Profile & Settings');
      if (el.tagName === 'A' && !isSuperAdmin) {
        el.setAttribute('href', targetProfileUrl);
      }
      el.addEventListener('click', (e) => handleProfileNavigation(e, el));
    });

    // 2. All User Avatars (LK Circle buttons in topbar and sidebar)
    document.querySelectorAll('.user-avatar, #sidebarUserAvatar, #sidebarAvatar, #topbarAvatar, #adminTopbarAvatar, #adminSidebarAvatar, #superSidebarAvatar, #superProfileLargeAvatar').forEach(el => {
      el.style.cursor = 'pointer';
      el.setAttribute('title', 'Open Profile & Settings');
      if (el.tagName === 'A' && !isSuperAdmin) {
        el.setAttribute('href', targetProfileUrl);
      }
      el.addEventListener('click', (e) => handleProfileNavigation(e, el));
    });

    // 3. Super Admin Profile Nav items and topbar pills
    document.querySelectorAll('#superTopbarProfilePill, #navSuperProfile').forEach(el => {
      el.style.cursor = 'pointer';
      el.setAttribute('title', 'Open Profile & Settings');
      el.addEventListener('click', (e) => handleProfileNavigation(e, el));
    });
  }

  initProfileNavigation();

  // Close modals when clicking backdrop
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('is-open');
        document.body.style.overflow = '';
      }
    });
  });

  // Setup Notification Badge counts in topbar and sidebar
  updateNotificationBadges();

  // Universally synchronize profile photos and initials across avatars
  syncGlobalUserAvatars();

  if (window.proofVoiceApi && window.proofVoiceApi.isLiveSession()) {
    window.proofVoiceApi.getCurrentUser().then(u => {
      if (u) syncGlobalUserAvatars();
    }).catch(() => {});
  }

  if (window.proofVoiceApi && window.proofVoiceApi.isLiveSession()) {
    window.proofVoiceApi.getNotifications().then(notifs => {
      if (Array.isArray(notifs)) {
        const liveUnread = notifs.filter(n => !n.read && !n.is_read).length;
        updateNotificationBadges(liveUnread);
      }
    }).catch(() => {});
  }

  // Setup Header Notification Dropdown
  setupNotificationDropdown();
});

function setupNotificationDropdown() {
  const notifBtns = document.querySelectorAll('.topbar-notification-btn');
  if (!notifBtns.length) return;

  const isNotifPage = window.location.pathname.includes('notifications.html');
  const rootPrefix = getAppRootPrefix();
  const isSuperAdminPage = window.location.pathname.includes('super-admin');

  notifBtns.forEach(btn => {
    // Super-Admin dashboard has its own dedicated notification console & dropdown
    if (btn.id === 'superAdminNotifBtn' || isSuperAdminPage) {
      return;
    }

    const parent = btn.parentElement;
    if (parent && getComputedStyle(parent).position === 'static') {
      parent.style.position = 'relative';
    }

    btn.addEventListener('click', async (e) => {
      if (isNotifPage) return; // Allow normal navigation on dedicated notification pages
      e.preventDefault();
      e.stopPropagation();

      let existingDropdown = parent.querySelector('.topbar-notif-dropdown');
      if (existingDropdown) {
        existingDropdown.remove();
        return;
      }

      // Close any other open dropdowns
      document.querySelectorAll('.topbar-notif-dropdown[data-dynamic-dropdown="true"]').forEach(d => d.remove());

      let currentUser = (window.proofVoiceApi && typeof window.proofVoiceApi.getStoredUser === 'function') 
        ? window.proofVoiceApi.getStoredUser() 
        : (window.proofVoiceDb ? window.proofVoiceDb.getCurrentUser() : null);

      const isCurrentAdminPage = (window.location.pathname.includes('admin') && !isSuperAdminPage) ||
                                 window.location.pathname.includes('analytics') ||
                                 window.location.pathname.includes('departments') ||
                                 window.location.pathname.includes('users') ||
                                 window.location.pathname.includes('institution-settings');
      const isAdminUser = isCurrentAdminPage || (currentUser && (currentUser.role === 'admin' || currentUser.backendRole === 'INSTITUTION_ADMIN'));

      const dropdown = document.createElement('div');
      dropdown.className = 'topbar-notif-dropdown';
      dropdown.dataset.dynamicDropdown = 'true';
      dropdown.style.cssText = 'position:absolute; top:46px; right:0; width:390px; max-width:92vw; background:var(--color-card, #FFFFFF); border:1px solid var(--color-border, #E2E8F0); border-radius:14px; box-shadow:0 18px 45px rgba(0,0,0,0.18); z-index:99999; overflow:hidden; text-align:left; animation: fadeIn 0.15s ease-out;';
      dropdown.innerHTML = `
        <div class="topbar-notif-header" style="padding:12px 16px; border-bottom:1px solid var(--color-border, #E2E8F0); display:flex; justify-content:space-between; align-items:center; background:rgba(15, 118, 110, 0.04);">
          <div style="font-weight:700; color:var(--color-navy, #0F172A); font-size:13px; display:flex; align-items:center; gap:6px;">
            <span>Notifications</span>
            <span class="badge" id="dropUnreadCountBadge" style="background:var(--color-primary-light, rgba(15, 118, 110, 0.1)); color:var(--color-primary, #0F766E); font-size:10px; padding:2px 7px; border-radius:999px;">...</span>
          </div>
          <div style="display:flex; align-items:center; gap:6px;">
            <button type="button" class="btn btn-ghost btn-sm" id="dropMarkAllReadBtn" style="font-size:11px; padding:2px 8px; cursor:pointer;">Mark All Read</button>
            <button type="button" class="btn btn-ghost btn-sm" id="dropClearAllBtn" style="font-size:11px; padding:2px 8px; color:#EF4444; cursor:pointer;" title="Delete all notifications">Clear All</button>
          </div>
        </div>
        <div class="topbar-notif-list" id="dropNotifList" style="max-height:360px; overflow-y:auto;">
          <div style="padding:20px; text-align:center; color:var(--color-text-secondary, #64748B); font-size:12px;">Loading alerts...</div>
        </div>
      `;
      parent.appendChild(dropdown);

      // Fetch latest notifications
      let notifs = [];
      let isLiveFetch = false;
      if (window.proofVoiceApi && window.proofVoiceApi.isLiveSession()) {
        try {
          const live = await window.proofVoiceApi.getNotifications();
          if (Array.isArray(live)) {
            notifs = live;
            isLiveFetch = true;
          }
        } catch (err) {}
      }
      if (!isLiveFetch && window.proofVoiceDb) {
        notifs = window.proofVoiceDb.getNotifications() || [];
        if (currentUser) {
          const uid = String(currentUser.id || '').toLowerCase();
          const uemail = String(currentUser.email || '').toLowerCase();
          const instId = currentUser.institutionId || (currentUser.institution && currentUser.institution.id);
          notifs = notifs.filter(n => {
            if (isAdminUser) {
              if (n.institution_id && instId && String(n.institution_id) !== String(instId)) return false;
              if (n.institutionId && instId && String(n.institutionId) !== String(instId)) return false;
              return true;
            }
            const nRecipId = String(n.recipient_id || n.recipientId || '').toLowerCase();
            const nRecipEmail = String(n.recipient_email || n.recipientEmail || '').toLowerCase();
            if (nRecipId && nRecipId === uid) return true;
            if (uemail && nRecipEmail && nRecipEmail === uemail) return true;
            return false;
          });
        }
      }

      const listEl = dropdown.querySelector('#dropNotifList');
      const countBadge = dropdown.querySelector('#dropUnreadCountBadge');
      const unreadCount = notifs.filter(n => !n.is_read && !n.read).length;
      if (countBadge) countBadge.textContent = `${unreadCount} Unread`;

      function updateDropdownBadges() {
        const remaining = listEl.querySelectorAll('.topbar-notif-item').length;
        const remainingUnread = listEl.querySelectorAll('.topbar-notif-item.unread').length;
        if (countBadge) countBadge.textContent = `${remainingUnread} Unread`;
        if (window.updateNotificationBadges) window.updateNotificationBadges(remainingUnread);
        if (remaining === 0) {
          listEl.innerHTML = `<div style="padding:28px 16px; text-align:center; color:var(--color-text-secondary, #64748B); font-size:12px;">No notifications yet.</div>`;
        }
      }

      if (!notifs.length) {
        listEl.innerHTML = `<div style="padding:28px 16px; text-align:center; color:var(--color-text-secondary, #64748B); font-size:12px;">No notifications yet.</div>`;
      } else {
        listEl.innerHTML = notifs.slice(0, 10).map(n => {
          const isUnread = !n.is_read && !n.read;
          const compId = n.complaint_identifier || n.complaint_id || (n.complaint && (n.complaint.complaint_id || n.complaint.id)) || '';
          let targetUrl = n.action_url;
          if (!targetUrl) {
            if (compId) {
              targetUrl = `${rootPrefix}complaint-details.html?id=${compId}`;
            } else if (isAdminUser) {
              targetUrl = `${rootPrefix}admin-dashboard.html`;
            } else {
              targetUrl = `${rootPrefix}student-dashboard.html`;
            }
          } else if (!targetUrl.startsWith('http') && !targetUrl.startsWith('#')) {
            targetUrl = `${rootPrefix}${targetUrl.replace(/^\//, '')}`;
          }

          let timeStr = 'Recently';
          if (n.created_at) {
            try {
              const cleanStr = String(n.created_at).replace(/([+-]\d{2})(\d{2})$/, '$1:$2');
              const d = new Date(cleanStr);
              if (!isNaN(d.getTime())) {
                timeStr = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
              }
            } catch (e) {}
          }

          return `
            <div class="topbar-notif-item ${isUnread ? 'unread' : ''}" data-id="${n.id}" data-comp-id="${compId}" style="display:flex; align-items:flex-start; justify-content:space-between; gap:8px; padding:10px 14px; border-bottom:1px solid var(--color-border, #E2E8F0); background:${isUnread ? 'rgba(15, 118, 110, 0.05)' : 'transparent'}; border-left:3px solid ${isUnread ? 'var(--color-primary, #0F766E)' : 'transparent'}; transition:background 0.15s ease;">
              <a href="${targetUrl}" class="notif-content-link" style="flex:1; text-decoration:none; color:inherit;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                  <strong style="font-size:12px; color:var(--color-navy, #0F172A);">${escapeHtml(n.title || 'Notification')}</strong>
                  <span style="font-size:10px; color:var(--color-text-secondary, #64748B);">${timeStr}</span>
                </div>
                <div style="font-size:11px; color:var(--color-text-secondary, #64748B); line-height:1.4; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;">
                  ${escapeHtml(n.message || '')}
                </div>
              </a>
              <button type="button" class="btn-delete-notif" data-id="${n.id}" title="Delete notification" style="background:transparent; border:none; color:var(--color-text-secondary, #94A3B8); cursor:pointer; padding:2px 6px; font-size:16px; line-height:1; border-radius:4px; flex-shrink:0;" onmouseover="this.style.color='#EF4444'" onmouseout="this.style.color='var(--color-text-secondary, #94A3B8)'">&times;</button>
            </div>
          `;
        }).join('');

        // Link click: mark read and navigate
        listEl.querySelectorAll('.notif-content-link').forEach(link => {
          link.addEventListener('click', async (ev) => {
            const item = link.closest('.topbar-notif-item');
            if (!item) return;
            const id = item.dataset.id;
            const cId = item.dataset.compId;
            if (cId) {
              sessionStorage.setItem('proofvoice_current_complaint_id', cId);
              localStorage.setItem('proofvoice_last_viewed_complaint_id', cId);
            }
            if (window.proofVoiceApi) {
              await window.proofVoiceApi.markNotificationRead(id).catch(() => {});
            }
          });
        });

        // Delete button click
        listEl.querySelectorAll('.btn-delete-notif').forEach(delBtn => {
          delBtn.addEventListener('click', async (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
            const id = delBtn.dataset.id;
            const item = delBtn.closest('.topbar-notif-item');
            if (item) {
              item.style.opacity = '0.4';
            }
            if (window.proofVoiceApi) {
              await window.proofVoiceApi.deleteNotification(id).catch(() => {});
            }
            if (window.proofVoiceDb) {
              window.proofVoiceDb.deleteNotification(id);
            }
            if (item) {
              item.remove();
            }
            updateDropdownBadges();
          });
        });
      }

      // Mark all read button
      const markAllBtn = dropdown.querySelector('#dropMarkAllReadBtn');
      if (markAllBtn) {
        markAllBtn.addEventListener('click', async (evt) => {
          evt.stopPropagation();
          markAllBtn.textContent = 'Updating...';
          if (window.proofVoiceApi) {
            await window.proofVoiceApi.markAllNotificationsRead().catch(() => {});
          } else if (window.proofVoiceDb) {
            window.proofVoiceDb.markAllNotificationsRead();
          }
          if (window.updateNotificationBadges) window.updateNotificationBadges(0);
          if (countBadge) countBadge.textContent = '0 Unread';
          dropdown.querySelectorAll('.topbar-notif-item').forEach(it => {
            it.classList.remove('unread');
            it.style.background = 'transparent';
            it.style.borderLeftColor = 'transparent';
          });
          markAllBtn.textContent = 'All Read \u2713';
          markAllBtn.disabled = true;
        });
      }

      // Clear all notifications button
      const clearAllBtn = dropdown.querySelector('#dropClearAllBtn');
      if (clearAllBtn) {
        clearAllBtn.addEventListener('click', async (evt) => {
          evt.stopPropagation();
          clearAllBtn.textContent = 'Clearing...';
          if (window.proofVoiceApi) {
            await window.proofVoiceApi.clearAllNotifications().catch(() => {});
          } else if (window.proofVoiceDb) {
            window.proofVoiceDb.clearAllNotifications();
          }
          if (window.updateNotificationBadges) window.updateNotificationBadges(0);
          if (countBadge) countBadge.textContent = '0 Unread';
          listEl.innerHTML = `<div style="padding:28px 16px; text-align:center; color:var(--color-text-secondary, #64748B); font-size:12px;">No notifications yet.</div>`;
          clearAllBtn.textContent = 'Cleared \u2713';
          clearAllBtn.disabled = true;
        });
      }
    });
  });

  // Global dismiss listener - ONLY remove dynamically created dropdowns, NEVER remove static DOM dropdowns
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.topbar-notif-dropdown') && !e.target.closest('.topbar-notification-btn')) {
      document.querySelectorAll('.topbar-notif-dropdown[data-dynamic-dropdown="true"]').forEach(d => d.remove());
      const superDD = document.getElementById('superAdminNotifDropdown');
      if (superDD && !e.target.closest('#superAdminNotifBtn')) {
        superDD.style.display = 'none';
      }
    }
  });
}


// ============================================================================
// HOMEPAGE NAVIGATION, SMOOTH SCROLLING & ACTIVE INDICATOR SPY
// ============================================================================
function initHomepageNavigationAndFeatures() {
  const isHomePage = window.location.pathname.endsWith('index.html') ||
                     window.location.pathname === '/' ||
                     window.location.pathname.endsWith('ProofVoice/');

  if (!isHomePage) return;

  if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
  }

  const navLinksContainer = document.getElementById('mainNavLinks');
  const navPill = document.getElementById('navActivePill');
  const header = document.querySelector('.site-header');

  const navItems = [
    { id: 'home', link: document.getElementById('navLinkHome') },
    { id: 'how-it-works', link: document.getElementById('navLinkHowItWorks') },
    { id: 'features', link: document.getElementById('navLinkFeatures') },
    { id: 'ai-assistant', link: document.getElementById('navLinkAiAssistant') },
    { id: 'languages', link: document.getElementById('navLinkLanguages') },
    { id: 'institutions', link: document.getElementById('navLinkInstitutions') },
    { id: 'faq', link: document.getElementById('navLinkFaq') }
  ].filter(item => item.link !== null);

  let activeNavId = 'home';
  let isClickScrolling = false;
  let scrollTimeout = null;

  function updateActivePill(activeLink) {
    if (!navPill || !navLinksContainer || !activeLink) {
      if (navPill) navPill.style.opacity = '0';
      return;
    }

    navLinksContainer.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    activeLink.classList.add('active');

    // On mobile dropdown menu (viewport <= 768px), keep text active but hide floating pill
    if (window.innerWidth <= 768) {
      navPill.style.opacity = '0';
      return;
    }

    const containerRect = navLinksContainer.getBoundingClientRect();
    const linkRect = activeLink.getBoundingClientRect();
    const offsetLeft = linkRect.left - containerRect.left;
    const width = linkRect.width;

    navPill.style.left = `${offsetLeft}px`;
    navPill.style.width = `${width}px`;
    navPill.style.opacity = '1';
  }

  function setActiveSection(targetId) {
    activeNavId = targetId;
    const match = navItems.find(item => item.id === targetId);
    if (match && match.link) {
      updateActivePill(match.link);
    }
  }

  // Smooth scroll handler for nav items
  navItems.forEach(item => {
    item.link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetEl = document.getElementById(item.id);
      if (!targetEl) return;

      isClickScrolling = true;
      setActiveSection(item.id);

      // Close mobile navigation menu if open
      const mobileNav = document.querySelector('.nav-links');
      if (mobileNav && mobileNav.classList.contains('is-open')) {
        mobileNav.classList.remove('is-open');
      }

      const headerHeight = header ? header.offsetHeight : 70;
      const targetOffset = targetEl.getBoundingClientRect().top + window.pageYOffset - (headerHeight + 20);

      window.scrollTo({
        top: Math.max(0, targetOffset),
        behavior: 'smooth'
      });

      if (scrollTimeout) clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        isClickScrolling = false;
        setActiveSection(item.id);
      }, 750);
    });
  });

  // Header Logo click smooth scrolls to top
  const headerLogo = document.getElementById('headerLogoLink');
  if (headerLogo) {
    headerLogo.addEventListener('click', (e) => {
      e.preventDefault();
      isClickScrolling = true;
      setActiveSection('home');
      window.scrollTo({ top: 0, behavior: 'smooth' });
      setTimeout(() => { isClickScrolling = false; }, 750);
    });
  }

  // Scroll Spy with requestAnimationFrame
  let ticking = false;
  function onScrollSpy() {
    if (isClickScrolling) return;

    const scrollY = window.pageYOffset || document.documentElement.scrollTop;
    const headerHeight = header ? header.offsetHeight : 70;
    const scrollPosition = scrollY + headerHeight + 50;

    // 1. Top of page
    if (scrollY < 120) {
      setActiveSection('home');
      return;
    }

    // 2. Near bottom of page
    if ((window.innerHeight + scrollY) >= (document.documentElement.scrollHeight - 80)) {
      setActiveSection('faq');
      return;
    }

    // 3. Middle sections in sequential order
    let currentId = 'home';
    for (let i = 0; i < navItems.length; i++) {
      const secEl = document.getElementById(navItems[i].id);
      if (secEl) {
        const top = secEl.offsetTop;
        if (scrollPosition >= top) {
          currentId = navItems[i].id;
        }
      }
    }
    setActiveSection(currentId);
  }

  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        onScrollSpy();
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });

  window.addEventListener('resize', () => {
    const currentActive = navItems.find(item => item.id === activeNavId);
    if (currentActive && currentActive.link) {
      updateActivePill(currentActive.link);
    }
  }, { passive: true });

  // Ensure returning from login or dashboard immediately resets to top Home menu
  const returnFlag = sessionStorage.getItem('proofvoice_return_to_home') === 'true';
  const ref = document.referrer || '';
  const fromAuthOrDash = returnFlag || /login\.html|register\.html|dashboard/i.test(ref);
  const shouldForceHome = fromAuthOrDash || !window.location.hash || window.location.hash === '#home';

  if (shouldForceHome) {
    try { sessionStorage.removeItem('proofvoice_return_to_home'); } catch (e) {}
    if (window.location.hash && window.location.hash !== '#home') {
      try { history.replaceState(null, document.title, window.location.pathname + window.location.search); } catch (e) {}
    }
    document.documentElement.style.scrollBehavior = 'auto';
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    setActiveSection('home');
    setTimeout(() => {
      window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
      setActiveSection('home');
      document.documentElement.style.scrollBehavior = '';
    }, 50);
  } else {
    // Hash exists and was intentionally navigated
    setTimeout(() => {
      const currentActive = navItems.find(item => item.id === activeNavId) || navItems[0];
      if (currentActive && currentActive.link) {
        updateActivePill(currentActive.link);
      }
    }, 100);
  }

  // Handle browser back/forward buttons (popstate)
  window.addEventListener('popstate', () => {
    if (!window.location.hash || window.location.hash === '#home') {
      document.documentElement.style.scrollBehavior = 'auto';
      window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
      setActiveSection('home');
      setTimeout(() => {
        document.documentElement.style.scrollBehavior = '';
      }, 50);
    }
  });

  // Track buttons that leave homepage for login/register so return always goes straight to Home
  document.querySelectorAll('#navLoginBtn, #heroSignInBtn, #heroGetStartedBtn, #finalCtaReportIssueBtn').forEach(btn => {
    btn.addEventListener('click', () => {
      try { sessionStorage.setItem('proofvoice_return_to_home', 'true'); } catch (e) {}
    });
  });

  // -------------------------------------------------------------------------
  // 14 FEATURE CARDS CLICK & AUTHENTICATION HANDLERS
  // -------------------------------------------------------------------------
  const featureCards = document.querySelectorAll('.feature-card');
  featureCards.forEach(card => {
    const targetUrl = card.getAttribute('data-feature-target');
    const featureName = card.getAttribute('data-feature-name') || 'Feature';
    const featureRole = card.getAttribute('data-feature-role') || 'student';

    function handleCardActivation(e) {
      e.preventDefault();

      const token = localStorage.getItem('proofvoice_auth_token');
      const isAuth = Boolean(token && !String(token).startsWith('demo_token_'));

      if (!isAuth) {
        // Unauthenticated visitor -> Redirect to login with friendly message & safe return URL
        const authMsg = `Please log in or create an account to explore ${featureName}.`;
        try { sessionStorage.setItem('proofvoice_auth_toast', authMsg); } catch (err) {}
        try { sessionStorage.setItem('proofvoice_return_to_home', 'true'); } catch (err) {}
        const redirectParam = encodeURIComponent(targetUrl);
        const featureParam = encodeURIComponent(featureName);
        window.location.href = `login.html?redirect=${redirectParam}&feature=${featureParam}`;
        return;
      }

      // Authenticated visitor -> Check role boundaries
      const rawRole = (localStorage.getItem('proofvoice_active_role') || '').toLowerCase();
      const isAdmin = rawRole === 'admin' || rawRole === 'institution_admin' || rawRole === 'superadmin' || rawRole === 'platform_superadmin';

      if (featureRole === 'admin' && !isAdmin) {
        if (typeof showToast === 'function') {
          showToast('info', 'Institutional Feature', 'This administrative workspace is reserved for authorized campus staff. Redirecting to your student dashboard.');
        } else {
          alert('This administrative workspace is reserved for authorized campus staff. Redirecting to your student dashboard.');
        }
        setTimeout(() => {
          window.location.href = 'student-dashboard.html';
        }, 1000);
        return;
      }

      if (isAdmin && (targetUrl === 'student-dashboard.html' || targetUrl.startsWith('student-dashboard.html'))) {
        window.location.href = 'admin-dashboard.html';
        return;
      }

      window.location.href = targetUrl;
    }

    card.addEventListener('click', handleCardActivation);
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        handleCardActivation(e);
      }
    });
  });

  // -------------------------------------------------------------------------
  // HOMEPAGE FAQ ACCORDION INTERACTION
  // -------------------------------------------------------------------------
  const faqItems = document.querySelectorAll('.home-faq-item');
  faqItems.forEach(item => {
    const trigger = item.querySelector('.home-faq-trigger');
    if (!trigger) return;

    trigger.addEventListener('click', () => {
      const isOpen = item.classList.contains('is-open');

      // Close all other FAQ items for accordion feel
      faqItems.forEach(otherItem => {
        if (otherItem !== item) {
          otherItem.classList.remove('is-open');
          const otherTrigger = otherItem.querySelector('.home-faq-trigger');
          if (otherTrigger) otherTrigger.setAttribute('aria-expanded', 'false');
        }
      });

      // Toggle current item
      if (isOpen) {
        item.classList.remove('is-open');
        trigger.setAttribute('aria-expanded', 'false');
      } else {
        item.classList.add('is-open');
        trigger.setAttribute('aria-expanded', 'true');
      }
    });
  });
}
