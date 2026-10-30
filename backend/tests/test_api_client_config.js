const assert = require('assert');

// Test the resolveApiBaseUrl logic
function createTestEnvironment(customWindow = {}, customStorage = {}) {
  const localStorage = {
    getItem: (k) => customStorage[k] || null,
    setItem: (k, v) => { customStorage[k] = String(v); },
    removeItem: (k) => { delete customStorage[k]; }
  };
  const window = customWindow;

  let PRODUCTION_BACKEND_URL = '';
  const LOCAL_BACKEND_URL = 'http://127.0.0.1:8000/api/v1';

  function resolveApiBaseUrl() {
    if (typeof window !== 'undefined' && window.PROOFVOICE_API_BASE) {
      const base = String(window.PROOFVOICE_API_BASE).trim().replace(/\/+$/, '');
      return base.endsWith('/api/v1') ? base : `${base}/api/v1`;
    }

    if (typeof localStorage !== 'undefined') {
      const custom = localStorage.getItem('proofvoice_api_base_url');
      if (custom && custom.trim()) {
        const base = custom.trim().replace(/\/+$/, '');
        return base.endsWith('/api/v1') ? base : `${base}/api/v1`;
      }
    }

    if (PRODUCTION_BACKEND_URL && PRODUCTION_BACKEND_URL.trim()) {
      const base = PRODUCTION_BACKEND_URL.trim().replace(/\/+$/, '');
      return base.endsWith('/api/v1') ? base : `${base}/api/v1`;
    }

    return LOCAL_BACKEND_URL;
  }

  return { resolveApiBaseUrl, setProdUrl: (u) => { PRODUCTION_BACKEND_URL = u; } };
}

// Case 1: Default local development fallback
const env1 = createTestEnvironment({ location: { hostname: 'localhost' } });
assert.strictEqual(env1.resolveApiBaseUrl(), 'http://127.0.0.1:8000/api/v1');
console.log('PASS: Local development defaults to http://127.0.0.1:8000/api/v1');

// Case 2: Configured via window.PROOFVOICE_API_BASE
const env2 = createTestEnvironment({ PROOFVOICE_API_BASE: 'https://actual-render-service.onrender.com' });
assert.strictEqual(env2.resolveApiBaseUrl(), 'https://actual-render-service.onrender.com/api/v1');
console.log('PASS: window.PROOFVOICE_API_BASE correctly resolves with /api/v1');

// Case 3: Configured via localStorage
const env3 = createTestEnvironment({}, { proofvoice_api_base_url: 'https://render-test.onrender.com/' });
assert.strictEqual(env3.resolveApiBaseUrl(), 'https://render-test.onrender.com/api/v1');
console.log('PASS: localStorage override correctly resolves without double slashes');

// Case 4: Pre-suffixed with /api/v1
const env4 = createTestEnvironment({}, { proofvoice_api_base_url: 'https://render-test.onrender.com/api/v1' });
assert.strictEqual(env4.resolveApiBaseUrl(), 'https://render-test.onrender.com/api/v1');
console.log('PASS: Existing /api/v1 suffix is not duplicated');

// Case 5: Configured via PRODUCTION_BACKEND_URL constant
const env5 = createTestEnvironment();
env5.setProdUrl('https://my-live-proofvoice.onrender.com');
assert.strictEqual(env5.resolveApiBaseUrl(), 'https://my-live-proofvoice.onrender.com/api/v1');
console.log('PASS: PRODUCTION_BACKEND_URL constant correctly resolves');

console.log('\n>>> ALL API CLIENT CONFIGURATION TESTS PASSED! <<<');
