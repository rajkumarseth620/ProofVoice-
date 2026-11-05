/**
 * ProofVoice - 3D Day/Night Theme Management System
 * Supports dark mode & light mode with persistent storage and system preference sync.
 * Features ultra-tactile 3D Sun / Moon interactive toggle.
 */
(function() {
  const THEME_KEY = 'proofvoice_theme';

  function getSavedTheme() {
    try {
      const saved = localStorage.getItem(THEME_KEY);
      if (saved === 'dark' || saved === 'light') return saved;
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
      }
    } catch (e) {}
    return 'light';
  }

  function applyTheme(theme, animate = false) {
    const root = document.documentElement;
    if (animate) {
      root.classList.add('theme-transitioning');
      setTimeout(() => root.classList.remove('theme-transitioning'), 400);
    }
    root.setAttribute('data-theme', theme);
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch (e) {}
    updateToggleElements(theme);
    window.dispatchEvent(new CustomEvent('proofvoice:theme-change', { detail: { theme } }));
  }

  function updateToggleElements(theme) {
    const isDark = theme === 'dark';
    document.querySelectorAll('.pv-theme-toggle').forEach(btn => {
      btn.setAttribute('aria-checked', isDark ? 'true' : 'false');
      btn.setAttribute('title', isDark ? 'Switch to Light mode' : 'Switch to Dark mode');
    });

    document.querySelectorAll('.pv-theme-toggle-label').forEach(label => {
      label.textContent = isDark ? 'Dark mode' : 'Light mode';
    });
  }

  // Apply saved theme immediately upon script execution to prevent flashing
  const initialTheme = getSavedTheme();
  document.documentElement.setAttribute('data-theme', initialTheme);

  // 3D Switch HTML template matching reference design
  function get3DToggleHtml(sizeClass = '') {
    const isDark = (document.documentElement.getAttribute('data-theme') || initialTheme) === 'dark';
    return `
      <div class="pv-theme-toggle-wrapper" title="${isDark ? 'Switch to Light mode' : 'Switch to Dark mode'}">
        <button type="button" class="pv-theme-toggle ${sizeClass}" role="switch" aria-label="Toggle dark and light mode" aria-checked="${isDark ? 'true' : 'false'}">
          <div class="pv-toggle-track">
            <!-- Day Sky Layer -->
            <div class="pv-sky-day">
              <div class="pv-cloud pv-cloud-1"></div>
              <div class="pv-cloud pv-cloud-2"></div>
              <div class="pv-cloud pv-cloud-3"></div>
            </div>
            <!-- Night Sky Layer -->
            <div class="pv-sky-night">
              <div class="pv-star pv-star-1"></div>
              <div class="pv-star pv-star-2"></div>
              <div class="pv-star pv-star-3"></div>
              <div class="pv-star pv-star-4"></div>
              <div class="pv-night-cloud pv-night-cloud-1"></div>
              <div class="pv-night-cloud pv-night-cloud-2"></div>
            </div>
            <!-- 3D Sun / Moon Knob -->
            <div class="pv-toggle-thumb">
              <!-- 3D Glowing Sun (Light Mode) -->
              <div class="pv-sun-face">
                <div class="pv-sun-cloud-puff"></div>
              </div>
              <!-- 3D Moon with Craters (Dark Mode) -->
              <div class="pv-moon-face">
                <div class="pv-moon-crater pv-crater-1"></div>
                <div class="pv-moon-crater pv-crater-2"></div>
                <div class="pv-moon-crater pv-crater-3"></div>
                <div class="pv-moon-cloud-puff"></div>
              </div>
            </div>
          </div>
        </button>
      </div>
    `.trim();
  }

  function initToggles() {
    // Check if slots already exist
    let slots = document.querySelectorAll('[data-theme-toggle-slot]');

    // If no manual slot declared, automatically find the best topbar or nav location
    if (slots.length === 0) {
      const topbarRight = document.querySelector('.app-topbar .topbar-right');
      const navActions = document.querySelector('.main-nav .nav-actions');
      const superTopbarRight = document.querySelector('.topbar-right');
      const authTopBar = document.querySelector('.auth-top-bar');

      const target = topbarRight || navActions || superTopbarRight || authTopBar;
      if (target) {
        const autoSlot = document.createElement('div');
        autoSlot.setAttribute('data-theme-toggle-slot', '');
        autoSlot.setAttribute('data-size', 'sm');
        autoSlot.style.display = 'inline-flex';
        autoSlot.style.alignItems = 'center';

        // Prepend before actions or append smoothly
        if (target.firstChild) {
          target.insertBefore(autoSlot, target.firstChild);
        } else {
          target.appendChild(autoSlot);
        }
        slots = [autoSlot];
      }
    }

    // Populate all declared or auto-injected slots
    slots.forEach(slot => {
      if (!slot.querySelector('.pv-theme-toggle')) {
        const size = slot.dataset.size === 'sm' ? 'pv-toggle-sm' : '';
        slot.innerHTML = get3DToggleHtml(size);
      }
    });

    updateToggleElements(window.proofVoiceTheme.get());
  }

  window.proofVoiceTheme = {
    get: () => document.documentElement.getAttribute('data-theme') || 'light',
    set: (theme) => applyTheme(theme, true),
    toggle: () => {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      applyTheme(next, true);
      return next;
    },
    getToggleHtml: get3DToggleHtml,
    mount: initToggles
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initToggles);
  } else {
    initToggles();
  }

  // Delegate click listener for all 3D toggle buttons
  document.addEventListener('click', (e) => {
    const toggleBtn = e.target.closest('.pv-theme-toggle');
    if (toggleBtn) {
      e.preventDefault();
      window.proofVoiceTheme.toggle();
    }
  });

  // Cross-tab synchronization
  window.addEventListener('storage', (e) => {
    if (e.key === THEME_KEY && (e.newValue === 'dark' || e.newValue === 'light')) {
      applyTheme(e.newValue, false);
    }
  });
})();
