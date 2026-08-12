/**
 * CiteRAG frontend runtime config.
 * - Local: defaults to http://localhost:8000
 * - Production: defaults to same-origin /api (Vercel rewrite → Render)
 * Override anytime: localStorage.setItem('citeRAG_apiBase', 'https://...')
 */
(function () {
  var host = (typeof location !== 'undefined' && location.hostname) || '';
  var isLocal = host === 'localhost' || host === '127.0.0.1' || host === '';
  if (!window.__API_BASE__) {
    window.__API_BASE__ = isLocal ? 'http://localhost:8000' : '/api';
  }
  if (!window.__DEMO_API_KEY__) {
    window.__DEMO_API_KEY__ = 'demo-public-key';
  }
})();
