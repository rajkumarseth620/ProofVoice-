/**
 * ProofVoice - Notification Center Management
 */

const escapeHtml = window.escapeHtml || (s => s ? String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m])) : '');

const formatDateTime = window.formatDateTime || (d => {
  if (!d) return 'N/A';
  try {
    let cleanStr = String(d).trim();
    // Normalize ISO string missing colon in timezone (e.g. +0530 -> +05:30)
    cleanStr = cleanStr.replace(/([+-]\d{2})(\d{2})$/, '$1:$2');
    const dt = new Date(cleanStr);
    return isNaN(dt.getTime()) ? String(d) : dt.toLocaleString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true
    });
  } catch (e) {
    return String(d);
  }
});

function initNotificationsPage() {
  const notifContainer = document.getElementById('notificationsList');
  if (!notifContainer) return;

  const markAllBtn = document.getElementById('markAllReadBtn');
  const filterSelect = document.getElementById('notifFilterSelect');

  async function renderNotifications() {
    const filter = filterSelect ? filterSelect.value : 'all';
    const isAdmin = window.location.pathname.includes('admin');
    let notifs = [];
    let hasLiveSuccess = false;

    // Show clean loading spinner if currently empty
    if (!notifContainer.children.length) {
      notifContainer.innerHTML = `
        <div style="padding: 32px 16px; text-align: center; color: var(--color-text-secondary); font-size: 13px;">
          <span class="spinner" style="margin-right: 8px;"></span> Loading notifications...
        </div>
      `;
    }

    try {
      if (window.proofVoiceApi && window.proofVoiceApi.isLiveSession()) {
        try {
          const liveNotifs = await window.proofVoiceApi.getNotifications();
          if (Array.isArray(liveNotifs) && liveNotifs.length > 0) {
            hasLiveSuccess = true;
            notifs = liveNotifs.map(n => {
              const compId = n.complaint_identifier || n.complaint_id || (n.complaint && (n.complaint.complaint_id || n.complaint.id)) || '';
              const targetLink = n.action_url || (compId ? (isAdmin ? `admin-complaint-details.html?id=${compId}` : `complaint-details.html?id=${compId}`) : '');
              return {
                id: n.id,
                title: n.title,
                message: n.message || n.body || '',
                type: (n.notification_type || 'update').toLowerCase(),
                read: Boolean(n.is_read || n.read),
                timestamp: n.created_at || new Date().toISOString(),
                link: targetLink,
                complaintId: compId,
                recipientId: n.recipient_id || n.recipientId,
                recipientEmail: n.recipient_email || n.recipientEmail,
                institutionId: n.institution_id || n.institutionId
              };
            });
          }
        } catch (e) {
          console.warn('[ProofVoice Notifications] Live API fetch warning:', e);
        }
      }

      // Offline / demonstration fallback
      if (!hasLiveSuccess || notifs.length === 0) {
        const localList = (window.proofVoiceDb ? window.proofVoiceDb.getNotifications() : []) || [];
        if (localList.length > 0 && !hasLiveSuccess) {
          notifs = localList.map(n => {
            const compId = n.complaintId || (n.link && n.link.includes('id=') ? n.link.split('id=')[1] : '');
            return {
              ...n,
              type: (n.type || 'update').toLowerCase(),
              read: Boolean(n.read || n.is_read),
              complaintId: compId
            };
          });
        }
      }

      // User session filtering
      let currentUser = (window.proofVoiceApi && typeof window.proofVoiceApi.getStoredUser === 'function')
        ? window.proofVoiceApi.getStoredUser()
        : null;
      if (!currentUser && window.proofVoiceDb) {
        currentUser = window.proofVoiceDb.getCurrentUser();
      }

      if (!isAdmin && currentUser) {
        const currentUserId = String(currentUser.id || '').toLowerCase();
        const currentUserEmail = String(currentUser.email || '').toLowerCase();

        notifs = notifs.filter(n => {
          if (hasLiveSuccess) return true;

          const nRecipId = String(n.recipientId || n.recipient_id || '').toLowerCase();
          const nRecipEmail = String(n.recipientEmail || n.recipient_email || '').toLowerCase();

          return (nRecipId && nRecipId === currentUserId) ||
                 (currentUserEmail && nRecipEmail && nRecipEmail === currentUserEmail) ||
                 (!nRecipId && !nRecipEmail);
        });
      }

      if (isAdmin && currentUser) {
        const currentInstId = currentUser.institutionId || (currentUser.institution && (currentUser.institution.id || currentUser.institution.code));
        notifs = notifs.filter(n => {
          if (hasLiveSuccess) return true;

          if (n.institutionId && currentInstId && String(n.institutionId) !== String(currentInstId)) {
            return false;
          }
          return true;
        });
      }

      const unreadCount = notifs.filter(n => !n.read && !n.is_read).length;
      if (window.updateNotificationBadges) {
        window.updateNotificationBadges(unreadCount);
      }

      if (filter === 'unread') {
        notifs = notifs.filter(n => !n.read && !n.is_read);
      }

      if (notifs.length === 0) {
        notifContainer.innerHTML = `
          <div class="empty-state" style="padding: 48px 24px; text-align: center;">
            <div class="empty-state-icon" style="width: 48px; height: 48px; border-radius: 50%; background: var(--color-primary-light); color: var(--color-primary); display: inline-flex; align-items: center; justify-content: center; margin-bottom: 12px;">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
            </div>
            <div class="empty-state-title" style="font-size: 15px; font-weight: 700; color: var(--color-navy); margin-bottom: 6px;">All Caught Up!</div>
            <div class="empty-state-text" style="font-size: 13px; color: var(--color-text-secondary); max-width: 420px; margin: 0 auto; line-height: 1.5;">You have no unread notifications. Progress on campus grievances, milestone updates, and administrator actions will appear here in real-time.</div>
          </div>
        `;
        return;
      }

      notifContainer.innerHTML = notifs.map(n => {
        const isUnread = !n.read && !n.is_read;
        const isRes = n.type === 'resolution' || (n.title && n.title.toLowerCase().includes('resolved'));
        return `
        <div class="card notif-card-item" data-id="${n.id}" style="padding: var(--space-4) var(--space-5); margin-bottom: var(--space-3); ${isUnread ? 'border-left: 4px solid var(--color-primary); background: #FAFBFD;' : ''}">
          <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3);">
            <div style="display: flex; align-items: flex-start; gap: var(--space-3);">
              <div style="width: 36px; height: 36px; border-radius: 50%; background: ${isRes ? 'var(--color-success-bg, rgba(52,211,153,0.16))' : 'var(--color-primary-light)'}; color: ${isRes ? 'var(--color-success, #059669)' : 'var(--color-primary)'}; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  ${isRes 
                    ? '<polyline points="20 6 9 17 4 12"/>' 
                    : '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>'}
                </svg>
              </div>
              <div>
                <div style="font-size: var(--text-sm); font-weight: 600; color: var(--color-navy); display: flex; align-items: center; gap: 8px;">
                  ${escapeHtml(n.title)}
                  ${isUnread ? '<span class="badge notif-new-pill" style="background:var(--color-primary-light); color:var(--color-primary); font-size:10px; font-weight:700;">New</span>' : ''}
                </div>
                <p style="font-size: var(--text-sm); color: var(--color-text-primary); margin-top: 2px; line-height: 1.4;">
                  ${escapeHtml(n.message)}
                </p>
                <div style="font-size: 11px; color: var(--color-text-muted); margin-top: 6px;">
                  ${formatDateTime(n.timestamp)}
                </div>
              </div>
            </div>
            <div style="display: flex; align-items: center; gap: var(--space-2); flex-shrink: 0;">
              ${n.link ? `<a href="${n.link}" onclick="if ('${escapeHtml(n.complaintId || '')}') { sessionStorage.setItem('proofvoice_current_complaint_id', '${escapeHtml(n.complaintId || '')}'); localStorage.setItem('proofvoice_last_viewed_complaint_id', '${escapeHtml(n.complaintId || '')}'); }" class="btn btn-secondary btn-sm">View</a>` : ''}
              ${isUnread ? `<button type="button" class="btn btn-ghost btn-sm mark-single-read-btn" data-id="${n.id}">Mark Read</button>` : ''}
              <button type="button" class="btn btn-outline btn-sm delete-single-notif-btn" data-id="${n.id}" style="color:var(--color-error); border-color:#FECACA; background:#fff; padding:4px 8px; font-size:11px;" title="Delete notification">
                🗑️ Delete
              </button>
            </div>
          </div>
        </div>
      `;
      }).join('');

      bindNotificationItemActions();

    } catch (err) {
      console.error('[ProofVoice Notifications] Render error:', err);
      notifContainer.innerHTML = `
        <div class="empty-state" style="padding: 32px 16px; text-align: center;">
          <div style="color: var(--color-error); font-weight: 600; margin-bottom: 8px;">Unable to load notifications.</div>
          <p style="color: var(--color-text-secondary); font-size: 12px; margin-bottom: 12px;">${escapeHtml(err.message || 'Please refresh to try again.')}</p>
          <button type="button" class="btn btn-secondary btn-sm" onclick="window.renderProofVoiceNotifications && window.renderProofVoiceNotifications()">Retry</button>
        </div>
      `;
    }
  }

  function bindNotificationItemActions() {
    // Mark single read
    document.querySelectorAll('.mark-single-read-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const id = btn.dataset.id;
        btn.disabled = true;
        btn.textContent = 'Updating...';

        const card = btn.closest('.notif-card-item');
        if (card) {
          card.style.borderLeft = '';
          card.style.background = '';
          const newPill = card.querySelector('.notif-new-pill');
          if (newPill) newPill.remove();
          btn.style.display = 'none';
        }

        try {
          if (window.proofVoiceApi) {
            await window.proofVoiceApi.markNotificationRead(id);
          } else if (window.proofVoiceDb) {
            window.proofVoiceDb.markNotificationRead(id);
          }
        } catch (e) {}

        if (window.updateNotificationBadges) {
          window.updateNotificationBadges();
        }

        await renderNotifications();
        showToast('info', 'Notification Updated', 'Marked as read.');
      });
    });

    // Delete single notification
    document.querySelectorAll('.delete-single-notif-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const id = btn.dataset.id;
        if (!confirm('Are you sure you want to delete this notification?')) return;
        btn.disabled = true;
        btn.textContent = 'Deleting...';
        try {
          if (window.proofVoiceApi && typeof window.proofVoiceApi.deleteNotification === 'function') {
            await window.proofVoiceApi.deleteNotification(id);
          } else if (window.proofVoiceDb) {
            window.proofVoiceDb.deleteNotification(id);
          }
          await renderNotifications();
          showToast('success', 'Notification Deleted', 'The notification has been removed.');
        } catch (err) {
          showToast('error', 'Delete Failed', err.message || 'Unable to delete notification.');
          btn.disabled = false;
          btn.textContent = '🗑️ Delete';
        }
      });
    });
  }

  // Clear All button
  const clearAllBtn = document.getElementById('clearAllNotifsBtn');
  if (clearAllBtn) {
    clearAllBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      if (!confirm('Are you sure you want to delete all notifications? This cannot be undone.')) return;
      clearAllBtn.disabled = true;
      clearAllBtn.textContent = 'Clearing...';
      try {
        if (window.proofVoiceApi && typeof window.proofVoiceApi.clearAllNotifications === 'function') {
          await window.proofVoiceApi.clearAllNotifications();
        } else if (window.proofVoiceDb) {
          window.proofVoiceDb.clearAllNotifications();
        }
        await renderNotifications();
        showToast('info', 'Notifications Cleared', 'All notifications have been removed.');
      } catch (err) {
        showToast('error', 'Clear Failed', err.message || 'Unable to clear notifications.');
      } finally {
        clearAllBtn.disabled = false;
        clearAllBtn.textContent = 'Clear All';
      }
    });
  }

  // Mark all read button
  if (markAllBtn) {
    markAllBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      markAllBtn.disabled = true;
      markAllBtn.textContent = 'Marking read...';
      try {
        if (window.proofVoiceApi) {
          await window.proofVoiceApi.markAllNotificationsRead();
        } else if (window.proofVoiceDb) {
          window.proofVoiceDb.markAllNotificationsRead();
        }
      } catch (e) {}

      if (window.updateNotificationBadges) {
        window.updateNotificationBadges(0);
      }
      await renderNotifications();
      markAllBtn.disabled = false;
      markAllBtn.textContent = 'Mark All as Read';
      showToast('success', 'Notifications Cleared', 'All notifications marked as read.');
    });
  }

  if (filterSelect) {
    filterSelect.addEventListener('change', renderNotifications);
  }

  window.renderProofVoiceNotifications = renderNotifications;
  renderNotifications();
}

// Immediate execution guard: runs immediately if DOM is ready, or on DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initNotificationsPage);
} else {
  initNotificationsPage();
}
