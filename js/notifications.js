/**
 * ProofVoice - Notification Center Management
 */

document.addEventListener('DOMContentLoaded', () => {
  const notifContainer = document.getElementById('notificationsList');
  if (!notifContainer) return;

  const markAllBtn = document.getElementById('markAllReadBtn');
  const filterSelect = document.getElementById('notifFilterSelect');

  async function renderNotifications() {
    const filter = filterSelect ? filterSelect.value : 'all';
    const isAdmin = window.location.pathname.includes('admin');
    let notifs = [];
    let hasLiveSuccess = false;

    if (window.proofVoiceApi && window.proofVoiceApi.isLiveSession()) {
      try {
        const liveNotifs = await window.proofVoiceApi.getNotifications();
        if (Array.isArray(liveNotifs)) {
          hasLiveSuccess = true;
          notifs = liveNotifs.map(n => {
            const compId = n.complaint_id || (n.complaint && (n.complaint.complaint_id || n.complaint.id)) || '';
            const targetLink = n.action_url || (compId ? (isAdmin ? `admin-complaint-details.html?id=${compId}` : `complaint-details.html?id=${compId}`) : '');
            return {
              id: n.id,
              title: n.title,
              message: n.message || n.body,
              type: n.notification_type || 'update',
              read: Boolean(n.is_read || n.read),
              timestamp: n.created_at || new Date().toISOString(),
              link: targetLink,
              complaintId: compId
            };
          });
        }
      } catch (e) {
        console.warn('Failed to fetch live notifications:', e);
      }
    }

    if (!hasLiveSuccess) {
      notifs = (window.proofVoiceDb ? window.proofVoiceDb.getNotifications() : []).map(n => {
        const compId = n.complaintId || (n.link && n.link.includes('id=') ? n.link.split('id=')[1] : '');
        return {
          ...n,
          complaintId: compId
        };
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
        <div class="empty-state">
          <div class="empty-state-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
          </div>
          <div class="empty-state-title">All Caught Up!</div>
          <div class="empty-state-text">You have no new unread notifications. Progress on your complaints will appear here in real-time.</div>
        </div>
      `;
      return;
    }

    notifContainer.innerHTML = notifs.map(n => {
      const isUnread = !n.read && !n.is_read;
      return `
      <div class="card notif-card-item" data-id="${n.id}" style="padding: var(--space-4) var(--space-5); margin-bottom: var(--space-3); ${isUnread ? 'border-left: 4px solid var(--color-primary); background: #FAFBFD;' : ''}">
        <div style="display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3);">
          <div style="display: flex; align-items: flex-start; gap: var(--space-3);">
            <div style="width: 36px; height: 36px; border-radius: 50%; background: ${n.type === 'resolution' ? 'var(--color-success-bg)' : 'var(--color-primary-light)'}; color: ${n.type === 'resolution' ? 'var(--color-success)' : 'var(--color-primary)'}; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px;">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                ${n.type === 'resolution' 
                  ? '<polyline points="20 6 9 17 4 12"/>' 
                  : '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>'}
              </svg>
            </div>
            <div>
              <div style="font-size: var(--text-sm); font-weight: 600; color: var(--color-navy); display: flex; align-items: center; gap: 8px;">
                ${escapeHtml(n.title)}
                ${isUnread ? '<span class="badge notif-new-pill" style="background:var(--color-primary-light); color:var(--color-primary); font-size:10px;">New</span>' : ''}
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
            ${isUnread ? `<button class="btn btn-ghost btn-sm mark-single-read-btn" data-id="${n.id}">Mark Read</button>` : ''}
          </div>
        </div>
      </div>
    `;
    }).join('');

    // Attach mark single read listeners
    document.querySelectorAll('.mark-single-read-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const id = btn.dataset.id;
        btn.disabled = true;
        btn.textContent = 'Updating...';

        // Optimistically remove "New" pill and clear highlight
        const card = btn.closest('.notif-card-item');
        if (card) {
          card.style.borderLeft = '';
          card.style.background = '';
          const newPill = card.querySelector('.notif-new-pill');
          if (newPill) newPill.remove();
          btn.style.display = 'none';
        }

        if (window.proofVoiceApi) {
          await window.proofVoiceApi.markNotificationRead(id);
        } else if (window.proofVoiceDb) {
          window.proofVoiceDb.markNotificationRead(id);
        }

        if (window.updateNotificationBadges) {
          window.updateNotificationBadges();
        }

        await renderNotifications();
        showToast('info', 'Notification Updated', 'Marked as read.');
      });
    });
  }

  if (markAllBtn) {
    markAllBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      markAllBtn.disabled = true;
      markAllBtn.textContent = 'Marking read...';
      if (window.proofVoiceApi) {
        await window.proofVoiceApi.markAllNotificationsRead();
      } else if (window.proofVoiceDb) {
        window.proofVoiceDb.markAllNotificationsRead();
      }
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

  renderNotifications();
});
