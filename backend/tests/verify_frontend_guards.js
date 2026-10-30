const assert = require('assert');

// Mock localStorage
const storage = {};
global.localStorage = {
  getItem: (k) => storage[k] || null,
  setItem: (k, v) => { storage[k] = String(v); },
  removeItem: (k) => { delete storage[k]; },
  clear: () => { Object.keys(storage).forEach(k => delete storage[k]); }
};

let redirectedTo = null;
global.window = {
  location: {
    pathname: '/student-dashboard.html',
    replace: (url) => { redirectedTo = url; }
  },
  addEventListener: () => {}
};

// Import guard logic
const PUBLIC_ROUTES = new Set([
  '', '/', 'index.html', 'login.html', 'register.html', 'institution-register.html',
  'forgot-password.html', 'help.html', 'faq.html', 'terms.html', 'privacy.html', '404.html'
]);
const STUDENT_ROUTES = new Set([
  'student-dashboard.html', 'new-complaint.html', 'review-complaint.html', 'my-complaints.html',
  'complaint-details.html', 'student-profile.html', 'student-profile-complete.html', 'student-notifications.html'
]);
const ADMIN_ROUTES = new Set([
  'admin-dashboard.html', 'admin-complaints.html', 'admin-complaint-details.html', 'departments.html',
  'users.html', 'analytics.html', 'institution-settings.html', 'admin-profile.html', 'admin-notifications.html'
]);
const SUPERADMIN_ROUTES = new Set(['super-admin.html']);

function enforceRouteGuard() {
  const path = window.location.pathname || '';
  const parts = path.split('/');
  let filename = parts[parts.length - 1] || 'index.html';
  if (!filename.includes('.')) filename = filename ? filename + '.html' : 'index.html';
  const page = filename.toLowerCase().split('?')[0].split('#')[0];

  if (PUBLIC_ROUTES.has(page)) return;

  const token = localStorage.getItem('proofvoice_auth_token');
  const isAuth = Boolean(token && !String(token).startsWith('demo_token_'));

  if (!isAuth) {
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

// Case 1: Unauthenticated direct student dashboard access -> redirect login.html
localStorage.clear();
window.location.pathname = '/student-dashboard.html';
redirectedTo = null;
enforceRouteGuard();
assert.strictEqual(redirectedTo, 'login.html', 'Unauthenticated student dashboard access must redirect to login.html');
console.log('PASS: Unauthenticated student dashboard access redirected to login.html');

// Case 2: Unauthenticated direct admin dashboard access -> redirect login.html
window.location.pathname = '/admin-dashboard.html';
redirectedTo = null;
enforceRouteGuard();
assert.strictEqual(redirectedTo, 'login.html', 'Unauthenticated admin dashboard access must redirect to login.html');
console.log('PASS: Unauthenticated admin dashboard access redirected to login.html');

// Case 3: Fake demo token -> redirect login.html
localStorage.setItem('proofvoice_auth_token', 'demo_token_1730000000');
window.location.pathname = '/student-dashboard.html';
redirectedTo = null;
enforceRouteGuard();
assert.strictEqual(redirectedTo, 'login.html', 'Fake demo token must be rejected');
console.log('PASS: Fake demo token rejected and redirected to login.html');

// Case 4: Authenticated student attempting admin page -> redirect student-dashboard.html
localStorage.setItem('proofvoice_auth_token', 'real_valid_token_abc123');
localStorage.setItem('proofvoice_active_role', 'student');
window.location.pathname = '/admin-dashboard.html';
redirectedTo = null;
enforceRouteGuard();
assert.strictEqual(redirectedTo, 'student-dashboard.html', 'Student accessing admin page must redirect to student-dashboard.html');
console.log('PASS: Student attempting to access admin dashboard redirected to student-dashboard.html');

// Case 5: Authenticated admin attempting student page -> redirect admin-dashboard.html
localStorage.setItem('proofvoice_active_role', 'admin');
window.location.pathname = '/student-dashboard.html';
redirectedTo = null;
enforceRouteGuard();
assert.strictEqual(redirectedTo, 'admin-dashboard.html', 'Admin accessing student page must redirect to admin-dashboard.html');
console.log('PASS: Admin attempting to access student dashboard redirected to admin-dashboard.html');

// Case 6: Public page access allowed
window.location.pathname = '/login.html';
redirectedTo = null;
enforceRouteGuard();
assert.strictEqual(redirectedTo, null, 'Public pages must not be blocked');
console.log('PASS: Public pages accessible without redirect');

console.log('\n>>> ALL FRONTEND ROUTE GUARD TESTS PASSED! <<<');
