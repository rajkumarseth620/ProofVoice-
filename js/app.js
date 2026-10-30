/**
 * ProofVoice - Core Application JavaScript (v3)
 * Shared utilities, toast system, modals, accessibility, multi-tenant role-switcher.
 */

// Setup Notification Badge counts across topbar & sidebar
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

  const initials = (user.avatar || (user.fullName ? user.fullName.split(' ').map(n => n[0]).join('').slice(0, 2) : 'PV')).toUpperCase();
  const photoUrl = user.profileImage || null;
  const isAdmin = user.role === 'admin' || user.backendRole === 'INSTITUTION_ADMIN';

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
      el.style.backgroundColor = isAdmin ? '#1E293B' : '#4F46E5';
      el.style.color = '#FFFFFF';
    }
  });

  const userNameEls = document.querySelectorAll('#sidebarUserName, #adminUserName, #adminSidebarName, .user-name-display');
  userNameEls.forEach(el => {
    if (user.fullName) el.textContent = user.fullName;
  });

  const roleEls = document.querySelectorAll('#sidebarUserRole, #adminSidebarRole');
  roleEls.forEach(el => {
    if (isAdmin) {
      el.textContent = user.designation || 'Administrator';
    } else {
      el.textContent = `${user.department || 'Student'}${user.yearSemester ? ' • ' + user.yearSemester : ''}`;
    }
  });

  const instEls = document.querySelectorAll('#studentInstitutionName, #adminInstitutionName, #sidebarInstName, #topbarInst, .user-tenant-display');
  instEls.forEach(el => {
    if (user.institutionName) el.textContent = user.institutionName;
  });
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
      <div class="toast-message">${escapeHtml(message)}</div>
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
  if (!text) return '';
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return String(text).replace(/[&<>"']/g, m => map[m]);
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

// Browser Text-To-Speech with honest disclosure (Gnani AI Timbre integration placeholder)
function speakText(text, onStart, onEnd) {
  if (!('speechSynthesis' in window)) {
    showToast('warning', 'TTS Unavailable', 'Your browser does not support SpeechSynthesis.');
    return;
  }
  window.speechSynthesis.cancel();

  showToast('info', 'Audio Read Aloud', 'Playing preview via Browser SpeechSynthesis (Gnani AI Timbre API is not connected yet).', 3000);

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
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
}

function getNormalizedCurrentPage() {
  const path = window.location.pathname || '';
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
  '404.html'
]);

const STUDENT_ROUTES = new Set([
  'student-dashboard.html',
  'new-complaint.html',
  'review-complaint.html',
  'my-complaints.html',
  'complaint-details.html',
  'student-profile.html',
  'student-profile-complete.html',
  'student-notifications.html'
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
  'admin-notifications.html'
]);

const SUPERADMIN_ROUTES = new Set([
  'super-admin.html'
]);

function enforceRouteGuard() {
  const page = getNormalizedCurrentPage();
  if (PUBLIC_ROUTES.has(page)) {
    return;
  }

  const token = localStorage.getItem('proofvoice_auth_token');
  const isAuth = Boolean(token && !String(token).startsWith('demo_token_'));

  if (!isAuth) {
    // Unauthenticated user attempting to access protected page
    window.location.replace('login.html');
    return;
  }

  const rawRole = (localStorage.getItem('proofvoice_active_role') || '').toLowerCase();
  const isAdmin = rawRole === 'admin' || rawRole === 'institution_admin';
  const isSuperAdmin = rawRole === 'superadmin' || rawRole === 'platform_superadmin';
  const isStudent = !isAdmin && !isSuperAdmin;

  if (STUDENT_ROUTES.has(page)) {
    if (isAdmin) {
      window.location.replace('admin-dashboard.html');
      return;
    }
    if (isSuperAdmin) {
      window.location.replace('super-admin.html');
      return;
    }
  }

  if (ADMIN_ROUTES.has(page)) {
    if (isStudent) {
      window.location.replace('student-dashboard.html');
      return;
    }
  }

  if (SUPERADMIN_ROUTES.has(page)) {
    if (!isSuperAdmin) {
      window.location.replace(isAdmin ? 'admin-dashboard.html' : 'student-dashboard.html');
      return;
    }
  }
}

// Enforce route guard immediately
enforceRouteGuard();

// Also guard on back-forward cache restoration
window.addEventListener('pageshow', () => {
  enforceRouteGuard();
});

function setupLogoutLinks() {
  document.querySelectorAll('a[href="login.html"], button[data-action="logout"], .logout-btn, #logoutBtn, #adminLogoutBtn').forEach((link) => {
    link.addEventListener('click', async (e) => {
      e.preventDefault();
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
      window.location.replace('login.html');
    });
  });
}

// Global UI setup
document.addEventListener('DOMContentLoaded', () => {
  setupLogoutLinks();

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

  // Sidebar toggle for app pages
  const sidebarToggle = document.querySelector('.topbar-toggle-sidebar') || document.getElementById('sidebarToggleBtn');
  const sidebar = document.querySelector('.app-sidebar') || document.getElementById('appSidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('is-open');
    });
  }

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
    window.proofVoiceApi.getNotifications().then(notifs => {
      if (Array.isArray(notifs)) {
        const liveUnread = notifs.filter(n => !n.read && !n.is_read).length;
        updateNotificationBadges(liveUnread);
      }
    }).catch(() => {});
  }

  // Check Profile Completion on Student Pages
  if (window.proofVoiceDb) {
    const user = window.proofVoiceDb.getCurrentUser();
    if (user && user.role === 'student' && !user.profileComplete) {
      const isProfilePage = window.location.pathname.includes('student-profile');
      if (!isProfilePage) {
        let onboardingBanner = document.getElementById('profileIncompleteBanner');
        if (!onboardingBanner) {
          const mainContent = document.querySelector('.app-content');
          if (mainContent) {
            onboardingBanner = document.createElement('div');
            onboardingBanner.id = 'profileIncompleteBanner';
            onboardingBanner.className = 'alert alert-warning';
            onboardingBanner.style.marginBottom = 'var(--space-6)';
            onboardingBanner.style.display = 'flex';
            onboardingBanner.style.justifyContent = 'space-between';
            onboardingBanner.style.alignItems = 'center';
            onboardingBanner.style.flexWrap = 'wrap';
            onboardingBanner.style.gap = 'var(--space-3)';
            onboardingBanner.innerHTML = `
              <div>
                <strong>Action Required: Complete Your Student Profile</strong>
                <div style="font-size:12px; margin-top:2px;">Your formal application letters require a verified student address and department to address institutional authorities.</div>
              </div>
              <a href="student-profile-complete.html" class="btn btn-warning btn-sm" style="font-weight:600;">Complete Profile Now →</a>
            `;
            mainContent.insertBefore(onboardingBanner, mainContent.firstChild);
          }
        }
      }
    }
  }
});
