/* ═══════════════════════════════════════════════════════════════════════════
   HMS Frontend JavaScript
   ═══════════════════════════════════════════════════════════════════════════ */

var HMS = HMS || {};

/* ── Theme ─────────────────────────────────────────────────────────────── */
HMS.Theme = {
  _key: 'hms-theme',

  init: function () {
    var saved = localStorage.getItem(this._key);
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    this._syncIcons();
  },

  toggle: function () {
    document.documentElement.classList.toggle('dark');
    var isDark = document.documentElement.classList.contains('dark');
    localStorage.setItem(this._key, isDark ? 'dark' : 'light');
    this._syncIcons();
  },

  _syncIcons: function () {
    var isDark = document.documentElement.classList.contains('dark');
    var light = document.getElementById('theme-icon-light');
    var dark = document.getElementById('theme-icon-dark');
    if (light) light.classList.toggle('hidden', isDark);
    if (dark) dark.classList.toggle('hidden', !isDark);
  }
};

/* ── Sidebar ───────────────────────────────────────────────────────────── */
HMS.Sidebar = {
  _sidebar: null,
  _overlay: null,

  init: function () {
    this._sidebar = document.getElementById('app-sidebar');
    this._overlay = document.getElementById('sidebar-overlay');
    if (!this._sidebar) return;

    // Restore collapsed state
    if (localStorage.getItem('hms-sidebar-collapsed') === '1' && window.innerWidth >= 1024) {
      this._sidebar.classList.add('collapsed');
      this._updateIcon();
    }
  },

  toggle: function () {
    if (!this._sidebar) return;
    this._sidebar.classList.toggle('collapsed');
    localStorage.setItem('hms-sidebar-collapsed', this._sidebar.classList.contains('collapsed') ? '1' : '0');
    this._updateIcon();
  },

  open: function () {
    if (!this._sidebar || !this._overlay) return;
    this._sidebar.classList.remove('-translate-x-full');
    this._overlay.classList.add('active');
    // Trap focus
    this._sidebar.querySelector('a, button').focus();
  },

  close: function () {
    if (!this._sidebar || !this._overlay) return;
    if (window.innerWidth < 1024) {
      this._sidebar.classList.add('-translate-x-full');
      this._overlay.classList.remove('active');
    }
  },

  _updateIcon: function () {
    var icon = document.getElementById('sidebar-collapse-icon');
    if (!icon) return;
    icon.style.transform = this._sidebar.classList.contains('collapsed') ? 'rotate(180deg)' : '';
  }
};

/* ── Toast ─────────────────────────────────────────────────────────────── */
HMS.Toast = {
  _container: null,
  _maxToasts: 5,

  init: function () {
    this._container = document.getElementById('toast-container');
  },

  show: function (type, title, message, duration) {
    if (!this._container) return;
    duration = duration || 5000;

    var tpl = document.getElementById('toast-template-' + type);
    if (!tpl) return;

    var el = tpl.content.cloneNode(true);
    var wrapper = document.createElement('div');
    wrapper.className = 'toast-item toast-enter';
    wrapper.appendChild(el.firstElementChild);

    var titleEl = wrapper.querySelector('.toast-title');
    var msgEl = wrapper.querySelector('.toast-message');
    if (titleEl) titleEl.textContent = title;
    if (msgEl) msgEl.textContent = message || '';

    this._container.appendChild(wrapper);

    // Auto-dismiss
    var self = this;
    setTimeout(function () { self.dismiss(wrapper); }, duration);

    // Limit total toasts
    while (this._container.children.length > this._maxToasts) {
      this.dismiss(this._container.children[0]);
    }
  },

  dismiss: function (el) {
    if (!el || !el.parentNode) return;
    el.classList.remove('toast-enter');
    el.classList.add('toast-exit');
    setTimeout(function () {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, 300);
  }
};

/* ── Notifications ─────────────────────────────────────────────────────── */
HMS.Notifications = {
  _open: false,

  toggle: function () {
    var panel = document.getElementById('notifications-panel');
    if (!panel) return;
    this._open = !this._open;
    panel.classList.toggle('hidden', !this._open);
    // Close user menu if open
    var userPanel = document.getElementById('user-menu-panel');
    if (userPanel) userPanel.classList.add('hidden');
  },

  markAllRead: function () {
    var badge = document.getElementById('notification-badge');
    if (badge) badge.classList.add('hidden');
  },

  close: function () {
    var panel = document.getElementById('notifications-panel');
    if (panel) panel.classList.add('hidden');
    this._open = false;
  }
};

/* ── User Menu ─────────────────────────────────────────────────────────── */
HMS.UserMenu = {
  _open: false,

  toggle: function () {
    var panel = document.getElementById('user-menu-panel');
    if (!panel) return;
    this._open = !this._open;
    panel.classList.toggle('hidden', !this._open);
    // Close notifications if open
    HMS.Notifications.close();
  },

  close: function () {
    var panel = document.getElementById('user-menu-panel');
    if (panel) panel.classList.add('hidden');
    this._open = false;
  }
};

/* ── Auth helpers ──────────────────────────────────────────────────────── */
HMS.Auth = {
  togglePasswordVisibility: function (btn) {
    var input = btn.closest('.relative').querySelector('input');
    if (!input) return;
    var isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    var open = btn.querySelector('.eye-open');
    var closed = btn.querySelector('.eye-closed');
    if (open) open.classList.toggle('hidden', !isPassword);
    if (closed) closed.classList.toggle('hidden', isPassword);
    btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
  },

  logout: function () {
    fetch('/api/v1/auth/logout', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: '' })
    }).then(function () {
      window.location.href = '/auth/login';
    }).catch(function () {
      window.location.href = '/auth/login';
    });
  },

  resendMFAPush: function () {
    HMS.Toast.show('info', 'Push sent', 'A new push notification has been sent to your device.');
  }
};

/* ── Search ────────────────────────────────────────────────────────────── */
HMS.Search = {
  init: function () {
    var input = document.getElementById('global-search');
    var results = document.getElementById('search-results');
    if (!input || !results) return;

    // Close on outside click
    document.addEventListener('click', function (e) {
      if (!e.target.closest('#global-search-wrapper')) {
        results.classList.add('hidden');
      }
    });

    // Close on Escape
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        results.classList.add('hidden');
        input.blur();
      }
    });
  }
};

/* ── Keyboard navigation ───────────────────────────────────────────────── */
HMS.Keyboard = {
  init: function () {
    var self = this;
    document.addEventListener('keydown', function (e) {
      self._handleEscape(e);
      self._handleArrowNav(e);
    });
  },

  _handleEscape: function (e) {
    if (e.key !== 'Escape') return;
    // Close dropdowns
    HMS.Notifications.close();
    HMS.UserMenu.close();
    HMS.Sidebar.close();
    // Close search
    var results = document.getElementById('search-results');
    if (results) results.classList.add('hidden');
  },

  _handleArrowNav: function (e) {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    var active = document.activeElement;
    if (!active || active.tagName !== 'A') return;

    var items = Array.from(active.closest('nav, [role="menu"]')?.querySelectorAll('a, button, [role="menuitem"]') || []);
    var idx = items.indexOf(active);
    if (idx === -1) return;

    e.preventDefault();
    var next = e.key === 'ArrowDown' ? idx + 1 : idx - 1;
    if (next >= 0 && next < items.length) {
      items[next].focus();
    }
  }
};

/* ── Form validation helpers ───────────────────────────────────────────── */
HMS.Form = {
  validateEmail: function (email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  },

  // Attach to forms: show inline error
  showError: function (containerId, message) {
    var el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = '<p class="text-sm text-red-700 dark:text-red-300">' + message + '</p>';
    el.classList.remove('hidden');
  },

  hideError: function (containerId) {
    var el = document.getElementById(containerId);
    if (el) el.classList.add('hidden');
  }
};

/* ── Close menus on outside click ──────────────────────────────────────── */
document.addEventListener('click', function (e) {
  if (!e.target.closest('#notifications-wrapper')) HMS.Notifications.close();
  if (!e.target.closest('#user-menu-wrapper')) HMS.UserMenu.close();
});

/* ── Close sidebar on resize to desktop ────────────────────────────────── */
window.addEventListener('resize', function () {
  if (window.innerWidth >= 1024) {
    var overlay = document.getElementById('sidebar-overlay');
    var sidebar = document.getElementById('app-sidebar');
    if (overlay) overlay.classList.remove('active');
    if (sidebar) sidebar.classList.remove('-translate-x-full');
  }
});

/* ── Init on DOMContentLoaded ──────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
  HMS.Theme.init();
  HMS.Sidebar.init();
  HMS.Toast.init();
  HMS.Search.init();
  HMS.Keyboard.init();
});

/* ── HTMX event hooks ──────────────────────────────────────────────────── */
document.addEventListener('htmx:responseError', function (e) {
  var status = e.detail.xhr.status;
  var msg = 'An error occurred. Please try again.';
  if (status === 401) msg = 'Invalid credentials. Please check your email and password.';
  else if (status === 403) msg = 'Account locked. Please contact your administrator.';
  else if (status === 422) msg = 'Please check your input and try again.';

  // Determine which error container to use
  var target = e.detail.target ? e.detail.target.id : '';
  if (target.includes('login')) HMS.Form.showError('login-error', msg);
  else if (target.includes('mfa')) HMS.Form.showError('mfa-error', msg);
  else if (target.includes('reset')) HMS.Form.showError('reset-error', msg);
  else if (target.includes('confirm')) HMS.Form.showError('confirm-error', msg);
  else HMS.Toast.show('error', 'Error', msg);
});

document.addEventListener('htmx:afterRequest', function (e) {
  // Hide error when form is resubmitted
  var target = e.detail.target ? e.detail.target.id : '';
  if (target.includes('login')) HMS.Form.hideError('login-error');
  else if (target.includes('mfa')) HMS.Form.hideError('mfa-error');
});
