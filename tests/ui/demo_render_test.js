#!/usr/bin/env node
/* Run the REAL demo.html render functions against REAL live API payloads.
 *
 * No browser needed: stub a minimal DOM, eval the page's own inline script,
 * call its own functions, and assert on the HTML they actually produce. This
 * is what proves the verification panel and decision layer render real data —
 * a 200 from the API tells you nothing about the front end.
 *
 * Usage:
 *   node tests/ui/demo_render_test.js                 # uses captured fixtures
 *   node tests/ui/demo_render_test.js <html> <json>   # explicit paths
 *
 * Capture fresh fixtures with: python3 tests/ui/capture_payloads.py
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const REPO = path.resolve(__dirname, '..', '..');
const DEMO = process.argv[2] || path.join(REPO, 'demo.html');
const PAYLOAD_PATH = process.argv[3] || path.join(__dirname, 'fixtures', 'live_payloads.json');

if (!fs.existsSync(PAYLOAD_PATH)) {
  console.error('No payloads at ' + PAYLOAD_PATH);
  console.error('Run: python3 tests/ui/capture_payloads.py');
  process.exit(2);
}
const PAYLOADS = JSON.parse(fs.readFileSync(PAYLOAD_PATH, 'utf8'));

const html = fs.readFileSync(DEMO, 'utf8');
// Pull the largest inline <script> block (the app logic) out of the page.
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
if (!scripts.length) { console.error('no inline script found in ' + DEMO); process.exit(2); }
const js = scripts.reduce((a, b) => (b.length > a.length ? b : a));

// ---- DOM stub -------------------------------------------------------------
function mkEl(id) {
  return {
    id,
    innerHTML: '',
    textContent: '',
    value: '',
    style: {},
    className: '',
    scrollTop: 0,
    scrollHeight: 0,
    querySelector: () => mkEl(id + '>q'),
    querySelectorAll: () => [],
    classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
    addEventListener() {},
    appendChild() {},
    remove() {},
  };
}
const els = {};
global.document = {
  getElementById: (id) => (els[id] ||= mkEl(id)),
  querySelector: (s) => mkEl(s),
  querySelectorAll: () => [],
  addEventListener() {},
  body: mkEl('body'),
};
global.window = { __API_BASE__: 'http://stub', __DEMO_API_KEY__: 'stub' };
global.localStorage = { getItem: () => null, setItem() {} };
global.sessionStorage = { getItem: () => null, setItem() {} };
global.fetch = () => Promise.reject(new Error('offline in harness'));
global.setInterval = () => 0;
global.setTimeout = (f) => 0;

// Strip the auto-run tail so nothing fires on load, then export internals.
const src = js
  .replace(/^\s*checkHealth\(\);\s*$/m, '')
  .replace(/^\s*setInterval\(checkHealth[^\n]*$/m, '')
  + '\nglobal.__X = { renderVerification, renderDecisionLayer, renderAnswer, esc, hasPage, fmtPage, pageSuffix, renderInlineMarkdown };\n';

vm.runInThisContext(src, { filename: 'demo-inline.js' });
const { renderVerification, renderAnswer, esc, hasPage, fmtPage, pageSuffix, renderInlineMarkdown } = global.__X;

// ---- Assertions -----------------------------------------------------------
let pass = 0, fail = 0;
function check(label, cond, extra) {
  if (cond) { pass++; console.log('  PASS  ' + label); }
  else { fail++; console.log('  FAIL  ' + label + (extra ? '\n        ' + extra : '')); }
}
function strip(h) { return h.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim(); }

for (const [name, p] of Object.entries(PAYLOADS)) {
  const v = p.verification || {};
  const gate = p.gate || null;
  console.log('\n== payload: ' + name + ' (engine=' + v.engine + ') ==');

  // reset panel state
  els['decision-layer'] = mkEl('decision-layer');
  els['verify-details'] = mkEl('verify-details');

  renderVerification(v, p.citations || [], gate);

  const det = els['verify-details'].innerHTML;
  const dl = els['decision-layer'].innerHTML;
  const dlVisible = els['decision-layer'].style.display;

  console.log('  score: ' + els['verify-score-num'].textContent + ' / ' + els['verify-score-label'].textContent);

  if (v.engine === 'jev') {
    check('decision panel rendered', dl.includes('Decision layer'), dl.slice(0, 120));
    check('panel visible', dlVisible === 'block', String(dlVisible));
    check('engine badge shows jev', dl.includes('engine-badge jev') && dl.includes('>jev<'), dl.slice(0, 200));
    check('decision cost rendered', /Decision cost.*\$0\.\d{6}/.test(strip(dl)), strip(dl).slice(0, 200));
    check('per-claim confidence bars rendered',
      (det.match(/conf-bar/g) || []).length === (v.details || []).length,
      'bars=' + (det.match(/conf-bar/g) || []).length + ' claims=' + (v.details || []).length);
    const confs = [...det.matchAll(/conf-num">([0-9.]+)</g)].map(m => parseFloat(m[1]));
    check('confidence values are real (0-1, from API)',
      confs.length > 0 && confs.every(c => c > 0 && c <= 1),
      JSON.stringify(confs));
    const apiConfs = (v.details || []).map(d => d.confidence).filter(c => c != null);
    check('UI confidences match API confidences',
      JSON.stringify(confs) === JSON.stringify(apiConfs.map(c => parseFloat(c.toFixed(2)))),
      'ui=' + JSON.stringify(confs) + ' api=' + JSON.stringify(apiConfs));
    if (gate) {
      check('gate answerability rendered', /Gate: answerable/.test(strip(dl)), strip(dl).slice(0, 300));
      check('gate route rendered', /Gate: retrieval route/.test(strip(dl)), strip(dl).slice(0, 300));
      check('gate complexity rendered', /Gate: complexity/.test(strip(dl)), strip(dl).slice(0, 300));
    }
    check('no marker bleed in rendered claims',
      !det.includes('[Source:') && !(v.details || []).some(d => (d.citation?.claim || '').includes(']')),
      det.slice(0, 200));
    check('no "p.N/A" rendered', !det.includes('p.N/A'), det.slice(0, 250));
  } else {
    check('refusal scored', els['verify-score-num'].textContent === '—' || v.is_refusal,
      els['verify-score-num'].textContent);
    check('refusal explains itself', /refused/i.test(strip(det)), strip(det).slice(0, 150));
    check('engine badge honest (none, not jev)',
      !dl.includes('>jev<'), dl.slice(0, 200));
    check('no confidence bars on refusal', !det.includes('conf-bar'), det.slice(0, 150));
  }

  // answer rendering (markdown leak check)
  const ansHtml = renderAnswer(p.answer || '', p.citations || [], !!v.is_refusal);
  check('answer renders no raw ** markdown', !ansHtml.includes('**'), ansHtml.slice(0, 300));
  check('answer escapes html', !/<script/i.test(ansHtml));
}

console.log('\n== helper unit tests ==');
// Real pages must still render; only genuinely-absent pages must be suppressed.
check('hasPage("3") true', hasPage('3') === true);
check('hasPage("12") true', hasPage('12') === true);
check('hasPage("N/A") false', hasPage('N/A') === false);
check('hasPage("n/a") false', hasPage('n/a') === false);
check('hasPage("NA") false', hasPage('NA') === false);
check('hasPage("") false', hasPage('') === false);
check('hasPage(null) false', hasPage(null) === false);
check('hasPage(undefined) false', hasPage(undefined) === false);
check('hasPage(" 7 ") true (trimmed)', hasPage(' 7 ') === true);
check('fmtPage("3") => p.3', fmtPage('3') === 'p.3', fmtPage('3'));
check('fmtPage("N/A") => empty', fmtPage('N/A') === '', JSON.stringify(fmtPage('N/A')));
check('pageSuffix("3") => , p.3', pageSuffix('3') === ', p.3', pageSuffix('3'));
check('pageSuffix("N/A") => empty', pageSuffix('N/A') === '', JSON.stringify(pageSuffix('N/A')));

// Synthetic payload with REAL page numbers must still show them.
els['decision-layer'] = mkEl('decision-layer');
els['verify-details'] = mkEl('verify-details');
renderVerification({
  total_citations: 1, verified: 1, accuracy: 1, is_refusal: false,
  engine: 'llm',
  details: [{ citation: { source: 'report.pdf', page: '14', claim: 'A real claim' },
              supported: true, source_text: '', confidence: null }],
}, [{ source: 'report.pdf', page: '14', claim: 'A real claim' }], null);
check('real page number IS rendered', els['verify-details'].innerHTML.includes('p.14'),
      els['verify-details'].innerHTML.slice(0, 200));
check('real page has separator', els['verify-details'].innerHTML.includes('report.pdf · p.14'),
      els['verify-details'].innerHTML.slice(0, 200));

const realPageAnswer = renderAnswer('See page fourteen [Source: report.pdf, Page 14].',
  [{ source: 'report.pdf', page: '14', claim: '' }], false);
check('answer keeps real page', realPageAnswer.includes('p.14'), realPageAnswer);
check('answer replaces marker', !realPageAnswer.includes('[Source:'), realPageAnswer);

// Markdown handling
check('bold rendered', renderInlineMarkdown('contact **billing@x.com** now')
      === 'contact <strong>billing@x.com</strong> now', renderInlineMarkdown('contact **billing@x.com** now'));
check('inline code rendered', renderInlineMarkdown('run `npm i`')
      === 'run <code>npm i</code>');
check('no bold left unrendered', !renderInlineMarkdown('a **b** c').includes('**'));
check('html stays escaped before markdown', renderInlineMarkdown(esc('<script>x</script> **b**'))
      .includes('&lt;script&gt;') === true, renderInlineMarkdown(esc('<script>x</script> **b**')));
check('single asterisks untouched', renderInlineMarkdown('2 * 3 = 6') === '2 * 3 = 6');

console.log('\n' + pass + ' passed, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
