#!/usr/bin/env node
'use strict';
/**
 * browser_harness — drive a REAL browser against a running ComfyUI, open a saved
 * workflow the way a buyer does, press the real Run button, and fail on any
 * frontend error.
 *
 * Why this exists: every render "verified" on this project before now went through
 * a harness that POSTed an already-flattened API graph straight to /prompt. That
 * path never exercises the frontend's UI-graph -> API-graph conversion, which is
 * exactly where the shipped-graph blocker lives. A render that only passes via the
 * API is not a passing test.
 *
 * Exit codes:
 *   0  pass
 *   1  test failure (frontend error, server rejection, or execution error)
 *   2  harness/usage error (bad args, ComfyUI unreachable, workflow not found)
 */

const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const { chromium } = require(path.join(REPO_ROOT, 'node_modules', 'playwright'));

const USAGE = `
browser_harness — real-browser test for a saved ComfyUI workflow

  node tools/browser_harness/run.js --workflow <name> [options]

REQUIRED
  --workflow, -w <name>   Saved workflow name, with or without .json
                          (must exist under the ComfyUI workflows dir)

MODE  (default: full render)
  --no-execute            Submit the prompt, take the server's validation verdict,
                          then interrupt + clear the queue. Tests frontend
                          conversion AND server validation. Does not render.
  --no-submit             Intercept POST /prompt and answer it locally. NOTHING
                          reaches the server. Tests frontend conversion only.
                          Fastest possible check; use it while iterating on the graph.

WHAT COUNTS AS A FAILURE
  Any of these in the "open workflow" or "run" phase fails the test:
    pageerror, window.onerror, unhandled promise rejection,
    console message at error level, PrimeVue error toast, any modal dialog,
    non-200 from POST /prompt, node_errors in the /prompt response,
    websocket execution_error, execution_interrupted.
  Errors during page BOOT (before the workflow is opened) are reported as
  BOOT-NOISE and are NOT fatal by default, because this ComfyUI install emits
  some at every page load regardless of workflow. --strict-boot makes them fatal.

  The harness does NOT stop at the first failure. A load-phase error does not
  prevent it from pressing Run, so one run tells you about every phase. The exit
  code is non-zero if ANY failure was recorded; the summary lists them all.

PRE-FLIGHT (static, ~25 ms, no browser)
  A link-bookkeeping lint runs on the UI-format JSON before the browser starts.
  It catches the class of defect behind the shipped blocker without a GPU or a
  browser. It checks link bookkeeping only - NOT widgets_values desync - so
  "0 problems" is not "no defects", and the browser stage remains the authority.
  --preflight <file.json> Lint this file (implied by --install)
  --preflight-only        Lint and stop; never launch a browser
  --no-preflight          Skip it

OPTIONS
  --url <url>             default http://127.0.0.1:18188  (env COMFY_URL)
  --install <path.json>   Copy this file over the install target before testing,
                          i.e. repo copy -> ComfyUI/user/default/workflows/<name>.json
  --cleanup-install       Delete the installed workflow again when the run ends,
                          so test fixtures do not accumulate in the list a buyer
                          picks their workflow from
  --out <dir>             Artifact dir. Default results/browser/<ts>-<workflow>/
  --api-out <path.json>   Also write the captured API graph here (for graph_diff)
  --load-mode ui|api      "ui" (default) clicks the workflow in the Workflows
                          sidebar. "api" calls app.loadGraphData directly.
  --allow-load-fallback   If the UI path fails, retry with the api path.
                          The path actually used is printed and recorded in
                          result.json as load_path_used.
INTERACTIVE IMAGE SELECTOR
  The shipped NSFW graph pauses mid-render on #603 INSTARAW_ImageFilter and waits
  for a human to choose an image (600 s timeout, then it aborts the render). That
  pause is deliberate and is part of the buyer journey.
  --drive-selector        Do what the buyer does: wait for the selector popup,
                          click an image, press Send, then wait for the render.
                          Required for any full-render test of the NSFW graph.
  --selector-pick N       Which image to click (default 0)
  --selector-timeout-ms N default 600000, matching the node's own timeout
  --wait-for-idle-ui-ms N If a selector popup from ANOTHER client's render is
                          covering the page, wait this long for it to clear before
                          giving up (default 90000; 0 = fail immediately). Matters
                          only on a shared server: the popup is broadcast to every
                          connected browser, so a foreign paused render blocks Run.

IGNORE-LIST
  tools/browser_harness/ignore.json holds a committed list of known-benign or
  pod-specific errors, each with a written justification. Matched errors are
  downgraded to "ignored": still printed, still counted, still in result.json.
  --strict-boot           Treat boot-phase console errors as failures too
  --ignore-error <regex>  Repeatable ad-hoc rule on top of the committed list
  --no-default-ignores    Ignore nothing; show the raw truth
  --headed                Run a visible browser
  --viewport WxH          default 1920x1080
  --workflows-dir <dir>   default /workspace/ComfyUI/user/default/workflows
  --output-dir <dir>      default /workspace/ComfyUI/output
  --boot-timeout-ms N     default 90000
  --load-timeout-ms N     default 120000
  --load-settle-ms N      default 3000
  --submit-timeout-ms N   default 120000
  --execute-timeout-ms N  default 900000
  --keep-open-ms N        hold the browser open before closing (debugging)
  --quiet                 only the final RESULT line group
  --help, -h
`;

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

const DEFAULTS = {
  url: process.env.COMFY_URL || 'http://127.0.0.1:18188',
  workflow: null,
  install: null,
  workflowsDir: process.env.COMFY_WORKFLOWS_DIR || '/workspace/ComfyUI/user/default/workflows',
  outputDir: process.env.COMFY_OUTPUT_DIR || '/workspace/ComfyUI/output',
  out: null,
  apiOut: null,
  mode: 'execute', // execute | no-execute | no-submit
  loadMode: 'ui', // ui | api
  allowLoadFallback: false,
  strictBoot: false,
  ignoreError: [],
  noDefaultIgnores: false,
  preflight: null,
  preflightOnly: false,
  noPreflight: false,
  cleanupInstall: false,
  driveSelector: false,
  selectorPick: 0,
  selectorTimeoutMs: 600000,
  waitForIdleUiMs: 90000,
  headed: false,
  bootTimeoutMs: 90000,
  loadTimeoutMs: 120000,
  loadSettleMs: 3000,
  submitTimeoutMs: 120000,
  executeTimeoutMs: 900000,
  viewport: '1920x1080',
  keepOpenMs: 0,
  quiet: false,
};

function die(msg) {
  process.stderr.write(`browser_harness: ${msg}\n`);
  process.exit(2);
}

function parseArgs(argv) {
  const o = { ...DEFAULTS };
  const rest = [];
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    const next = () => {
      const v = argv[++i];
      if (v === undefined) die(`option ${a} needs a value`);
      return v;
    };
    switch (a) {
      case '--url': o.url = next(); break;
      case '--workflow': case '-w': o.workflow = next(); break;
      case '--install': o.install = next(); break;
      case '--workflows-dir': o.workflowsDir = next(); break;
      case '--output-dir': o.outputDir = next(); break;
      case '--out': o.out = next(); break;
      case '--api-out': o.apiOut = next(); break;
      case '--no-execute': o.mode = 'no-execute'; break;
      case '--no-submit': o.mode = 'no-submit'; break;
      case '--load-mode': o.loadMode = next(); break;
      case '--allow-load-fallback': o.allowLoadFallback = true; break;
      case '--strict-boot': o.strictBoot = true; break;
      case '--ignore-error': o.ignoreError = o.ignoreError.concat([next()]); break;
      case '--no-default-ignores': o.noDefaultIgnores = true; break;
      case '--preflight': o.preflight = next(); break;
      case '--preflight-only': o.preflightOnly = true; break;
      case '--no-preflight': o.noPreflight = true; break;
      case '--cleanup-install': o.cleanupInstall = true; break;
      case '--drive-selector': o.driveSelector = true; break;
      case '--selector-pick': o.selectorPick = Number(next()); break;
      case '--selector-timeout-ms': o.selectorTimeoutMs = Number(next()); break;
      case '--wait-for-idle-ui-ms': o.waitForIdleUiMs = Number(next()); break;
      case '--headed': o.headed = true; break;
      case '--boot-timeout-ms': o.bootTimeoutMs = Number(next()); break;
      case '--load-timeout-ms': o.loadTimeoutMs = Number(next()); break;
      case '--load-settle-ms': o.loadSettleMs = Number(next()); break;
      case '--submit-timeout-ms': o.submitTimeoutMs = Number(next()); break;
      case '--execute-timeout-ms': o.executeTimeoutMs = Number(next()); break;
      case '--viewport': o.viewport = next(); break;
      case '--keep-open-ms': o.keepOpenMs = Number(next()); break;
      case '--quiet': o.quiet = true; break;
      case '--help': case '-h': process.stdout.write(USAGE); process.exit(0); break;
      default:
        if (a.startsWith('-')) die(`unknown option ${a}\n${USAGE}`);
        rest.push(a);
    }
  }
  if (!o.workflow && rest.length) o.workflow = rest[0];
  if (!o.workflow) die(`--workflow is required\n${USAGE}`);
  if (!['ui', 'api'].includes(o.loadMode)) die('--load-mode must be ui or api');
  return o;
}

// ---------------------------------------------------------------------------
// Event recording
// ---------------------------------------------------------------------------

// Classify an error by WHERE it came from, not just how loud it is. An error in
// the frontend core, in our own pack, or with no identifiable source is a product
// signal. An error from another pack's extension URL is this pod's environment.
// OUR_PACK is the only custom_nodes directory the NSFW product ships.
const OUR_PACK = 'ComfyUI_INSTARAW';

// Every URL we can attribute an event to. Playwright's console location arrives as
// "<url>:<line>" — the trailing :N must be stripped or a $-anchored path regex in
// ignore.json can never match, and the whole ignore-list silently does nothing.
function urlCandidates(text, at) {
  const urls = [];
  if (at) {
    const s = String(at);
    urls.push(s);
    urls.push(s.replace(/:\d+$/, ''));
  }
  const inText = String(text || '').match(/https?:\/\/[^\s'")]+/g);
  if (inText) urls.push(...inText);
  return urls;
}

function classifyOrigin(text, at) {
  // Order matters. An error's stack often walks through several packs' monkey
  // patches on the way out; the frame that RAISED it is the one that attributes
  // it. For a stack in the message that is the first URL in the text; otherwise
  // it is the console location. Classifying on "any extension URL anywhere in
  // the stack" blames whichever pack happens to wrap the function.
  const inText = String(text || '').match(/https?:\/\/[^\s'")]+/g) || [];
  const loc = at ? [String(at).replace(/:\d+$/, ''), String(at)] : [];
  const ordered = inText.length ? inText.concat(loc) : loc;

  for (const u of ordered) {
    if (u.includes(`/extensions/${OUR_PACK}/`)) return { origin: 'instaraw', product: true };
    const m = u.match(/\/extensions\/([^/]+)\//);
    if (m && m[1] !== OUR_PACK) return { origin: `third-party-pack:${m[1]}`, product: false };
    if (/\/assets\//.test(u)) return { origin: 'frontend-core', product: true };
  }
  if (ordered.length) return { origin: 'comfyui-asset', product: true };
  return { origin: 'unknown', product: true };
}

class Recorder {
  // rules: [{id, match:{text?, url?}, scope, reason}] from ignore.json and --ignore-error
  constructor(rules) {
    this.phase = 'boot';
    this.events = [];
    this.seen = new Set();
    this.t0 = Date.now();
    this.rules = (rules || []).map(r => ({
      ...r,
      _text: r.match && r.match.text ? new RegExp(r.match.text) : null,
      _url: r.match && r.match.url ? new RegExp(r.match.url) : null,
    }));
  }
  setPhase(p) { this.phase = p; }

  matchRule(text, at) {
    const haystackUrls = urlCandidates(text, at);
    return this.rules.find((r) => {
      if (r._text && !r._text.test(String(text))) return false;
      if (r._url && !haystackUrls.some(u => r._url.test(u))) return false;
      return !!(r._text || r._url);
    });
  }

  add(kind, severity, text, extra) {
    // The same failure usually arrives twice (pageerror + console.error).
    // De-dup on (phase, kind, text, source-url). The URL must be in the key:
    // "Failed to load resource: ... 404" is identical text for every distinct
    // failing URL, and collapsing those would hide real 404s behind an ignored one.
    const key = `${this.phase}|${kind}|${text}|${(extra && extra.at) || ''}`;
    if (this.seen.has(key)) return;
    this.seen.add(key);
    const at = extra && extra.at;
    const { origin, product } = classifyOrigin(text, at);
    let sev = severity;
    let rule = null;
    // NEVER ignorable: the two classes that mean the product is broken.
    const unignorable = kind === 'ws.execution_error';
    if (sev === 'error' && !unignorable) {
      rule = this.matchRule(text, at);
      if (rule) sev = 'ignored';
    }
    this.events.push({
      t_ms: Date.now() - this.t0, phase: this.phase, kind, severity: sev, origin, product_signal: product, text,
      ...(rule ? { ignored_by: rule.id, ignored_reason: rule.reason, ignored_scope: rule.scope } : {}),
      ...(extra || {}),
    });
  }
  errorsIn(phases) { return this.events.filter(e => e.severity === 'error' && phases.includes(e.phase)); }
  ignoredIn(phases) { return this.events.filter(e => e.severity === 'ignored' && phases.includes(e.phase)); }
  all() { return this.events; }
}

// Runs in the page before any site script. Covers three things Playwright's own
// events do not give us reliably:
//   1. unhandled promise rejections, with the stack
//   2. PrimeVue toasts, which auto-dismiss long before any poll could see them
//   3. PrimeVue dialogs (ComfyUI's error dialog for a rejected prompt)
const INIT_SCRIPT = () => {
  window.__harness = { errors: [], ui: [] };

  window.addEventListener('unhandledrejection', (ev) => {
    const r = ev.reason;
    window.__harness.errors.push({
      kind: 'unhandledrejection',
      text: r && (r.stack || r.message) ? String(r.stack || r.message) : String(r),
    });
  });
  window.addEventListener('error', (ev) => {
    window.__harness.errors.push({
      kind: 'window.onerror',
      text: String(ev.message) + (ev.error && ev.error.stack ? '\n' + ev.error.stack : ''),
    });
  });

  const record = (el) => {
    if (!el || !el.matches) return;
    let kind = null;
    let severity = 'info';
    if (el.matches('.p-toast-message')) {
      kind = 'toast';
      const cls = String(el.className || '');
      if (cls.includes('p-toast-message-error')) severity = 'error';
      else if (cls.includes('p-toast-message-warn')) severity = 'warn';
      else if (cls.includes('p-toast-message-success')) severity = 'success';
    } else if (el.matches('.p-dialog')) {
      kind = 'dialog';
      severity = 'error';
    }
    if (!kind) return;
    window.__harness.ui.push({
      kind,
      severity,
      text: (el.innerText || el.textContent || '').trim(),
      cls: String(el.className || ''),
    });
  };

  const scan = (root) => {
    if (!(root instanceof Element)) return;
    record(root);
    if (root.querySelectorAll) root.querySelectorAll('.p-toast-message, .p-dialog').forEach(record);
  };

  const start = () => {
    scan(document.body);
    new MutationObserver((muts) => {
      for (const m of muts) for (const n of m.addedNodes) scan(n);
    }).observe(document.body, { childList: true, subtree: true });
  };
  if (document.body) start();
  else document.addEventListener('DOMContentLoaded', start);
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const ensureDir = (d) => { fs.mkdirSync(d, { recursive: true }); return d; };

function ts() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}

function isPromptPath(u) {
  try {
    const p = new URL(String(u)).pathname.replace(/\/+$/, '');
    return p === '/prompt' || p === '/api/prompt';
  } catch { return false; }
}

const fmtEvent = (e) => `[${String(e.t_ms).padStart(6)}ms][${e.phase}][${e.kind}/${e.severity}]${e.origin ? `[${e.origin}]` : ''} ${e.text}`;

// Set by main() so the top-level catch can still write artifacts on an
// unexpected harness exception instead of dying silently.
let globalFinish = null;

// ---------------------------------------------------------------------------

async function main() {
  const opt = parseArgs(process.argv);
  const wfName = opt.workflow.replace(/\.json$/i, '');
  const runId = `${ts()}-${wfName}`;
  const outDir = ensureDir(opt.out ? path.resolve(opt.out) : path.join(REPO_ROOT, 'results', 'browser', runId));
  const log = (...a) => { if (!opt.quiet) console.log(...a); };

  // ---- ignore rules: committed file + ad-hoc --ignore-error --------------------
  let ignoreRules = [];
  const ignoreFile = path.join(__dirname, 'ignore.json');
  if (!opt.noDefaultIgnores) {
    try {
      ignoreRules = (JSON.parse(fs.readFileSync(ignoreFile, 'utf8')).rules || []);
    } catch (e) {
      die(`could not read ${ignoreFile}: ${e.message}`);
    }
  }
  ignoreRules = ignoreRules.concat(opt.ignoreError.map((p, i) => ({
    id: `cli-${i}`, match: { text: p }, scope: 'cli', reason: '--ignore-error on the command line',
  })));

  // ---- all mutable run state, declared up front so finish() can always read it
  const rec = new Recorder(ignoreRules);
  const failures = [];
  const addFailure = (cls, message) => { failures.push({ class: cls, message: String(message) }); };
  const timings = {};
  const wsEvents = [];
  const wsOutputs = [];
  let stats = null;
  let browser = null;
  let page = null;
  let loadPathUsed = null;
  let apiGraphPath = null;
  let promptBody = null;
  let promptPosted = false;
  let promptStatus = null;
  let promptResponse = null;
  let execError = null;
  let execInterrupted = false;
  let cancelledByHarness = false;
  let installedAt = null;
  let selectorInfo = { driven: false, abandoned: false, appeared: false, images: 0, picked: null, sent_at_ms: null, foreignSeen: false, our_run_started_ms: null };

  // finish() is the single exit point. It never decides *whether* the run failed
  // from its argument — that comes from the accumulated `failures` list, so a
  // failure recorded in any phase counts even if a later phase succeeded.
  const finish = async (res) => {
    res = res || {};
    rec.setPhase('teardown');
    if (page) { try { await drainInPage(); } catch { /* page may be gone */ } }

    if (opt.strictBoot) {
      for (const e of rec.errorsIn(['boot'])) addFailure('boot-noise', e.text);
    }
    const failed = failures.length > 0 || res.status === 'harness-error';
    const shot = failed ? 'screenshot-fail.png' : 'screenshot-final.png';

    if (page) { try { await page.screenshot({ path: path.join(outDir, shot) }); } catch { /* ignore */ } }
    fs.writeFileSync(path.join(outDir, 'console.log'), rec.all().map(fmtEvent).join('\n') + '\n');
    fs.writeFileSync(path.join(outDir, 'ws_events.json'), JSON.stringify(wsEvents, null, 2));

    const classes = [...new Set(failures.map(f => f.class))];
    const summary = {
      run_id: runId,
      status: res.status === 'harness-error' ? 'harness-error' : (failed ? 'fail' : 'pass'),
      failure_classes: classes,
      failure_class: classes[0] || null,
      failures,
      message: res.message || (failed ? failures[0] && failures[0].message : 'ok'),
      url: opt.url,
      workflow: wfName,
      mode: opt.mode,
      load_path_used: loadPathUsed,
      comfyui_version: stats && stats.system && stats.system.comfyui_version,
      frontend_version: stats && stats.system && stats.system.required_frontend_version,
      prompt_posted: promptPosted,
      prompt_http_status: promptStatus,
      prompt_id: promptResponse && promptResponse.prompt_id,
      api_graph: apiGraphPath,
      outputs: res.outputs || [],
      timings_ms: timings,
      counts: {
        boot_errors: rec.errorsIn(['boot']).length,
        load_errors: rec.errorsIn(['load']).length,
        run_errors: rec.errorsIn(['run']).length,
        ignored: rec.ignoredIn(['boot', 'load', 'run', 'teardown']).length,
      },
      errors: rec.all().filter(e => e.severity === 'error'),
      ignored: rec.all().filter(e => e.severity === 'ignored'),
      ignore_rules_file: opt.noDefaultIgnores ? null : ignoreFile,
      selector: selectorInfo,
      artifacts_dir: outDir,
    };
    fs.writeFileSync(path.join(outDir, 'result.json'), JSON.stringify(summary, null, 2));

    if (opt.keepOpenMs) await sleep(opt.keepOpenMs);
    if (browser) { try { await browser.close(); } catch { /* ignore */ } }

    // Test fixtures should not linger in the list a buyer picks their workflow from.
    if (opt.cleanupInstall && installedAt) {
      try { fs.unlinkSync(installedAt); log(`cleanup         removed ${installedAt}`); }
      catch (e) { log(`cleanup         could not remove ${installedAt}: ${e.message}`); }
    }

    // ---- summary ----------------------------------------------------------
    log('');
    log('='.repeat(78));
    const ignored = rec.ignoredIn(['boot', 'load', 'run', 'teardown']);
    if (ignored.length) {
      log(`IGNORED — matched the ignore-list, not counted as failures: ${ignored.length}`);
      log(`  (rules: ${opt.noDefaultIgnores ? '(defaults disabled) ' : ignoreFile + ' '}— audit them, do not trust them)`);
      const byRule = {};
      for (const e of ignored) (byRule[e.ignored_by] = byRule[e.ignored_by] || []).push(e);
      for (const [id, list] of Object.entries(byRule)) {
        const r = ignoreRules.find(x => x.id === id) || {};
        log(`  * ${id}  [${r.scope || '?'}]  x${list.length}`);
        for (const e of list) log(`      [${e.phase}/${e.origin}] ${e.text.split('\n')[0].slice(0, 140)}`);
      }
      log('');
      // product-known entries are real defects we chose not to gate on. Say so every
      // run, or the ignore-list quietly becomes the place defects go to die.
      const known = ignored.filter(e => e.ignored_scope === 'product-known');
      if (known.length) {
        log(`  !! ${known.length} of the above are scope=product-known: REAL defects in what we ship,`);
        log('     ignored only so they do not make every run red. They are written up in');
        log('     notes/WS2-report.md and should be fixed, not left here.');
        log('');
      }
    }
    const prodErrs = rec.all().filter(e => e.severity === 'error' && e.product_signal);
    const envErrs = rec.all().filter(e => e.severity === 'error' && !e.product_signal);
    if (envErrs.length) {
      log(`UNIGNORED ERRORS FROM OTHER PACKS (environment, still counted): ${envErrs.length}`);
      for (const e of envErrs) log(`  [${e.phase}/${e.origin}] ${e.text.split('\n')[0].slice(0, 140)}`);
      log('');
    }
    if (prodErrs.length) {
      log(`PRODUCT-SIGNAL ERRORS (frontend core / ${OUR_PACK} / unattributable): ${prodErrs.length}`);
      for (const e of prodErrs) log(`  [${e.phase}/${e.origin}] ${e.text.split('\n')[0].slice(0, 140)}`);
      log('');
    }
    if (res.status === 'harness-error') {
      log(`RESULT: HARNESS ERROR — ${res.message}`);
      log('  The test could not be carried out. This is not a verdict on the workflow.');
    } else if (!failed) {
      log(`RESULT: PASS  (${opt.mode})`);
      if (res.passNote) for (const l of res.passNote) log(`  ${l}`);
    } else {
      log(`RESULT: FAIL — ${failures.length} failure(s) in ${classes.length} class(es): ${classes.join(', ')}`);
      let n = 0;
      for (const f of failures) {
        n++;
        log('');
        log(`  ${n}. [${f.class}]`);
        for (const l of String(f.message).split('\n')) log(`     ${l}`);
      }
    }
    log('='.repeat(78));
    log(`artifacts:      ${outDir}`);
    log(`                result.json  console.log  ws_events.json  ${shot}${apiGraphPath ? '  api_graph.json  prompt_post_body.json' : ''}`);

    if (res.status === 'harness-error') process.exit(2);
    process.exit(failed ? 1 : 0);
  };

  globalFinish = finish;

  async function drainInPage() {
    let payload;
    try {
      payload = await page.evaluate(() => {
        const h = window.__harness;
        if (!h) return { errors: [], ui: [] };
        return { errors: h.errors.splice(0), ui: h.ui.splice(0) };
      });
    } catch { return; }
    for (const e of payload.errors) rec.add(e.kind, 'error', e.text);
    for (const u of payload.ui) rec.add(u.kind, u.severity, u.text, { cls: u.cls });
  }

  // --- optional install step: repo copy -> install target -------------------
  if (opt.install) {
    const src = path.resolve(opt.install);
    if (!fs.existsSync(src)) die(`--install source not found: ${src}`);
    const dstDir = path.resolve(opt.workflowsDir);
    if (!fs.existsSync(dstDir)) die(`workflows dir not found: ${dstDir}`);
    const dst = path.join(dstDir, `${wfName}.json`);
    if (path.dirname(dst) !== dstDir) die(`refusing to install outside ${dstDir}`);
    fs.copyFileSync(src, dst);
    installedAt = dst;
    log(`installed       ${src}`);
    log(`             -> ${dst} (${fs.statSync(dst).size} bytes)`);
  }

  // --- pre-flight: static link-bookkeeping lint on the UI-format JSON -------
  // Cheap (~25 ms) and it catches the class of defect that produced this run's
  // blocker, before a browser is launched. It does NOT replace the browser stage:
  // it checks link bookkeeping only, not widgets_values desync, and "0 problems"
  // has been shown to correlate with a converting graph on exactly one file pair.
  const preflightSrc = opt.preflight || opt.install;
  if (preflightSrc && !opt.noPreflight) {
    const src = path.resolve(preflightSrc);
    const script = path.join(__dirname, '..', 'preflight', 'integrity.py');
    if (!fs.existsSync(src)) die(`--preflight source not found: ${src}`);
    const r = require('child_process').spawnSync('python3', [script, src], { encoding: 'utf8' });
    const out = ((r.stdout || '') + (r.stderr || '')).trim();
    if (r.status === 0) {
      log(`preflight       integrity.py: ${out.split('\n')[0]}`);
    } else {
      log(`preflight       integrity.py FAILED on ${src}`);
      for (const line of out.split('\n')) log(`   ${line}`);
      addFailure('preflight-integrity', out);
      if (opt.preflightOnly) return finish({});
      log('   continuing to the browser anyway so this run still reports every phase');
    }
    log('');
  }
  if (opt.preflightOnly && !preflightSrc) die('--preflight-only needs --preflight <file.json> or --install <file.json>');
  if (opt.preflightOnly) return finish({});

  // --- preflight ------------------------------------------------------------
  try {
    const r = await fetch(`${opt.url}/system_stats`);
    if (!r.ok) die(`${opt.url}/system_stats returned HTTP ${r.status}`);
    stats = await r.json();
  } catch (e) {
    die(`cannot reach ComfyUI at ${opt.url}: ${e.message}`);
  }

  let savedWorkflows = [];
  try {
    const r = await fetch(`${opt.url}/api/userdata?dir=workflows&recurse=true&split=false&full_info=true`);
    if (r.ok) savedWorkflows = (await r.json()).map(x => (typeof x === 'string' ? x : x.path));
  } catch { /* non-fatal; the UI step reports it */ }
  if (savedWorkflows.length && !savedWorkflows.includes(`${wfName}.json`)) {
    die(`workflow "${wfName}.json" is not a saved workflow on ${opt.url}. Have: ${JSON.stringify(savedWorkflows)}`);
  }

  log('browser_harness');
  log(`  url          ${opt.url}  (ComfyUI ${stats.system.comfyui_version}, frontend ${stats.system.required_frontend_version})`);
  log(`  workflow     ${wfName}`);
  log(`  mode         ${opt.mode}   load-mode ${opt.loadMode}`);
  log(`  artifacts    ${outDir}`);
  log('');

  // --- browser --------------------------------------------------------------
  const [vw, vh] = opt.viewport.split('x').map(Number);
  browser = await chromium.launch({ headless: !opt.headed, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const ctx = await browser.newContext({ viewport: { width: vw, height: vh } });
  await ctx.addInitScript(INIT_SCRIPT);
  page = await ctx.newPage();
  page.setDefaultTimeout(30000);

  page.on('console', (m) => {
    const type = m.type();
    const sev = type === 'error' ? 'error' : type === 'warning' ? 'warn' : 'info';
    const loc = m.location();
    rec.add(`console.${type}`, sev, m.text(), loc && loc.url ? { at: `${loc.url}:${loc.lineNumber}` } : undefined);
  });
  page.on('pageerror', (e) => rec.add('pageerror', 'error', e.stack || e.message));
  page.on('crash', () => rec.add('page.crash', 'error', 'the browser page crashed'));
  page.on('requestfailed', (r) => rec.add('requestfailed', 'warn', `${r.url()} ${r.failure() ? r.failure().errorText : ''}`));
  page.on('response', (r) => { if (r.status() >= 400) rec.add('http', 'warn', `HTTP ${r.status()} ${r.url()}`); });

  // websocket: the authoritative execution signal
  page.on('websocket', (ws) => {
    rec.add('websocket', 'info', `open ${ws.url()}`);
    ws.on('framereceived', (ev) => {
      if (typeof ev.payload !== 'string') return; // binary preview frames
      let msg;
      try { msg = JSON.parse(ev.payload); } catch { return; }
      if (!msg || !msg.type) return;
      if (msg.type === 'progress' || msg.type === 'progress_state' || msg.type === 'crystools.monitor') return;
      wsEvents.push(msg);
      if (msg.type === 'executed' && msg.data && msg.data.output && msg.data.output.images) {
        for (const im of msg.data.output.images) wsOutputs.push({ ...im, node: msg.data.node });
      }
      if (msg.type === 'execution_error') { execError = msg.data; rec.add('ws.execution_error', 'error', JSON.stringify(msg.data)); }
      if (msg.type === 'execution_interrupted') {
        execInterrupted = true;
        rec.add('ws.execution_interrupted', cancelledByHarness ? 'info' : 'error', JSON.stringify(msg.data));
      }
    });
    ws.on('socketerror', (e) => rec.add('websocket', 'error', `socket error: ${e}`));
  });

  // /prompt interception — this is how the API graph artifact is captured
  const fakePromptId = 'harness-no-submit-' + Math.random().toString(16).slice(2);
  await page.route((u) => isPromptPath(u), async (route) => {
    const req = route.request();
    if (req.method() !== 'POST') return route.continue();
    promptPosted = true;
    promptBody = req.postData();
    if (opt.mode === 'no-submit') {
      promptResponse = { prompt_id: fakePromptId, number: 1, node_errors: {}, _synthetic: true };
      promptStatus = 200;
      rec.add('harness', 'info', 'no-submit: POST /prompt intercepted and answered locally; nothing reached the server');
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(promptResponse) });
    }
    return route.continue();
  });

  page.on('response', async (r) => {
    if (opt.mode === 'no-submit') return;
    if (!isPromptPath(r.url()) || r.request().method() !== 'POST') return;
    let body = null;
    try { body = await r.json(); }
    catch { try { body = { _raw: await r.text() }; } catch { body = null; } }
    promptResponse = body;
    promptStatus = r.status(); // set last: the poll loop keys off this
  });

  // =========================================================================
  // PHASE 1 — boot
  // =========================================================================
  let tPhase = Date.now();
  rec.setPhase('boot');
  try {
    await page.goto(`${opt.url}/`, { waitUntil: 'domcontentloaded', timeout: opt.bootTimeoutMs });
    await page.waitForSelector('canvas#graph-canvas', { timeout: opt.bootTimeoutMs });
    await page.waitForFunction(() => !!(window.app && window.app.vueAppReady), null, { timeout: opt.bootTimeoutMs });
  } catch (e) {
    return finish({ status: 'harness-error', failureClass: 'boot', message: `ComfyUI UI did not come up: ${e.message}` });
  }
  await sleep(2000); // let deferred extension imports settle into the boot bucket
  // RUN5 personal branch: a fresh browser profile gets the first-boot Templates
  // modal, whose overlay mask blocks the sidebar click. Close any open PrimeVue
  // dialog before proceeding. Gated by env so the stock behaviour is unchanged.
  if (process.env.RUN5_DISMISS_BOOT === '1') {
    // The first-boot Templates modal can appear late on a cold tree; keep
    // dismissing until the sidebar is actually reachable (max ~25 s).
    const t0 = Date.now();
    while (Date.now() - t0 < 60000) {
      const closed = await page.evaluate(() => {
        const btn = document.querySelector('.p-dialog .p-dialog-close-button, .p-dialog [data-pc-section="closebutton"]');
        if (btn) { btn.click(); return true; }
        return false;
      }).catch(() => false);
      if (closed) { await sleep(500); continue; }
      await page.keyboard.press('Escape').catch(() => {});
      const blocked = await page.evaluate(() =>
        !!document.querySelector('.p-dialog-mask, .p-overlay-mask')).catch(() => false);
      if (!blocked) break;
      await sleep(500);
    }
  }
  await drainInPage();
  timings.boot_ms = Date.now() - tPhase;
  const bootErrors = rec.errorsIn(['boot']);
  log(`boot            ${timings.boot_ms} ms   ${bootErrors.length} pre-existing error(s) before any workflow was opened`);
  for (const e of bootErrors) log(`   BOOT-NOISE   ${e.text.split('\n')[0].slice(0, 170)}`);
  if (bootErrors.length) log('   ^ page-load defects independent of the workflow; not fatal unless --strict-boot');

  // =========================================================================
  // PHASE 2 — open the workflow the way a buyer does
  // =========================================================================
  tPhase = Date.now();
  rec.setPhase('load');
  const titleReSrc = `^\\*?${wfName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')} - `;
  let uiLoadError = null;

  if (opt.loadMode === 'ui') {
    try {
      if (process.env.RUN5_DISMISS_BOOT === '1') {
        for (let i = 0; i < 30; i++) {
          const blocked = await page.evaluate(() => {
            const btn = document.querySelector('.p-dialog .p-dialog-close-button, .p-dialog [data-pc-section="closebutton"]');
            if (btn) { btn.click(); return true; }
            return !!document.querySelector('.p-dialog-mask, .p-overlay-mask');
          }).catch(() => false);
          if (!blocked) break;
          await page.keyboard.press('Escape').catch(() => {});
          await sleep(1000);
        }
      }
      await page.click('[data-testid="side-toolbar"] button.workflows-tab-button', { timeout: 20000 });
      await page.waitForSelector('[data-testid="workflows-sidebar"]', { timeout: 20000 });
      const byKey = page.locator(`[data-testid="tree-node-root/${wfName}.json"]`);
      if (await byKey.count()) {
        await byKey.first().click();
      } else {
        const byText = page.locator('[data-testid^="tree-node-"]').filter({ hasText: wfName });
        if (!(await byText.count())) throw new Error(`no workflow named "${wfName}" in the Workflows sidebar`);
        await byText.first().click();
      }
      await page.waitForFunction((re) => new RegExp(re).test(document.title), titleReSrc, { timeout: opt.loadTimeoutMs });
      await page.waitForFunction(() => {
        const g = window.app && window.app.rootGraph;
        return !!(g && (g.nodes || g._nodes || []).length > 0);
      }, null, { timeout: opt.loadTimeoutMs });
      loadPathUsed = 'ui';
    } catch (e) {
      uiLoadError = e;
    }
  }

  if (loadPathUsed === null && (opt.loadMode === 'api' || opt.allowLoadFallback)) {
    // Fallback: fetch the saved JSON and hand it to app.loadGraphData. Skips the
    // sidebar but still goes through the real graph-configure path. NOTE: this
    // does not make the workflow "active", so the tab title stays unchanged.
    try {
      await page.evaluate(async (name) => {
        const res = await fetch(`./api/userdata/workflows%2F${encodeURIComponent(name)}.json`);
        if (!res.ok) throw new Error(`GET saved workflow: HTTP ${res.status}`);
        await window.app.loadGraphData(await res.json(), true, true);
      }, wfName);
      await page.waitForFunction(() => {
        const g = window.app && window.app.rootGraph;
        return !!(g && (g.nodes || g._nodes || []).length > 0);
      }, null, { timeout: opt.loadTimeoutMs });
      loadPathUsed = 'api-fallback';
    } catch (e) {
      return finish({
        status: 'harness-error', failureClass: 'load',
        message: `both load paths failed: ui="${uiLoadError && uiLoadError.message}" api="${e.message}"`,
      });
    }
  }
  if (loadPathUsed === null) {
    // Cannot continue: without a loaded graph there is nothing to Run.
    addFailure('workflow-load', `could not open the workflow through the UI: ${uiLoadError && uiLoadError.message}`);
    for (const e of rec.errorsIn(['load'])) addFailure('frontend-load', e.text);
    return finish({});
  }

  await sleep(opt.loadSettleMs);
  await drainInPage();
  timings.load_ms = Date.now() - tPhase;
  const graphInfo = await page.evaluate(() => {
    const g = window.app && window.app.rootGraph;
    return { rootNodeCount: ((g && (g.nodes || g._nodes)) || []).length, title: document.title };
  });
  log(`open workflow   ${timings.load_ms} ms   path=${loadPathUsed}  title="${graphInfo.title}"  root-level nodes=${graphInfo.rootNodeCount}`);

  const loadErrors = rec.errorsIn(['load']);
  if (loadErrors.length) {
    log('');
    log(`FAILURE — (a0) FRONTEND ERROR WHILE OPENING THE WORKFLOW  (${loadErrors.length})`);
    log('  A buyer sees these before touching Run. Continuing to Run anyway so this');
    log('  run reports every phase.');
    for (const e of loadErrors) {
      log('  ' + fmtEvent(e));
      addFailure('frontend-load', e.text);
    }
    log('');
  }

  // =========================================================================
  // PHASE 3 — press the real Run button
  // =========================================================================
  tPhase = Date.now();
  rec.setPhase('run');
  const runBtn = page.locator('[data-testid="queue-button"] button.p-splitbutton-button');
  if (!(await runBtn.count())) {
    return finish({ status: 'harness-error', failureClass: 'run', message: 'Run button not found: [data-testid="queue-button"] button.p-splitbutton-button' });
  }
  // The INSTARAW selector popup is a full-screen overlay (z-index 100000) driven by
  // the server-sent "instaraw-interactive-images" event, which ComfyUI broadcasts to
  // EVERY connected browser — not only the one that started the render. So a render
  // paused by someone else leaves a popup covering this fresh page and swallowing the
  // Run click. Detect that up front and say so, rather than timing out on the click.
  const blockingPopup = page.locator('instaraw-imgae-filter-popup.instaraw_popup:not(.hidden)');
  const popupBlocking = async () =>
    (await blockingPopup.count()) > 0 && (await blockingPopup.first().isVisible().catch(() => false));

  if (opt.waitForIdleUiMs > 0 && (await popupBlocking())) {
    log(`wait           a foreign INSTARAW selector popup is covering the page; waiting up to ${opt.waitForIdleUiMs} ms for it to clear`);
    const idleDeadline = Date.now() + opt.waitForIdleUiMs;
    while (Date.now() < idleDeadline && (await popupBlocking())) {
      await drainInPage();
      await sleep(3000);
    }
    if (!(await popupBlocking())) log('wait           popup cleared; continuing');
  }

  if (await popupBlocking()) {
    const imgs = await page.locator('instaraw-imgae-filter-popup.instaraw_popup .grid img').count();
    return finish({
      status: 'harness-error',
      message: [
        `an INSTARAW image-selector popup is already open on ${opt.url} and covers the whole page (${imgs} image(s)).`,
        'It belongs to a render that is ALREADY paused on this server, started by another',
        'client — the popup is broadcast to every connected browser. The Run button cannot',
        'be clicked through it. This harness will not dismiss it, because Cancel would abort',
        "somebody else's render. Resolve that render (or wait for its 600 s timeout) and re-run.",
      ].join('\n'),
    });
  }

  const runLabel = (await runBtn.first().innerText().catch(() => '')).trim();
  log(`press Run       real button, label="${runLabel}"`);
  await runBtn.first().click({ timeout: 30000 });

  const submitDeadline = Date.now() + opt.submitTimeoutMs;
  while (Date.now() < submitDeadline) {
    await drainInPage();
    if (promptStatus !== null) break;
    if (!promptPosted && rec.errorsIn(['run']).length) break; // conversion blew up before any POST
    await sleep(250);
  }
  await sleep(600);
  await drainInPage();
  timings.submit_ms = Date.now() - tPhase;

  // Persist the API graph as soon as we have it — useful even on failure.
  if (promptBody) {
    fs.writeFileSync(path.join(outDir, 'prompt_post_body.json'), promptBody);
    let parsed = null;
    try { parsed = JSON.parse(promptBody); } catch { /* keep the raw copy only */ }
    if (parsed && parsed.prompt) {
      apiGraphPath = path.join(outDir, 'api_graph.json');
      fs.writeFileSync(apiGraphPath, JSON.stringify(parsed.prompt, null, 2));
      if (opt.apiOut) {
        const dst = path.resolve(opt.apiOut);
        ensureDir(path.dirname(dst));
        fs.copyFileSync(apiGraphPath, dst);
      }
      log(`api graph       ${Object.keys(parsed.prompt).length} nodes -> ${apiGraphPath}${opt.apiOut ? `\n                copy -> ${path.resolve(opt.apiOut)}` : ''}`);
    }
  }

  const runErrors = rec.errorsIn(['run']);

  // ---- (a) frontend conversion error: nothing ever reached the server ------
  if (!promptPosted) {
    log('');
    log('FAILURE — (a) FRONTEND CONVERSION ERROR');
    log('  Run was pressed. The frontend threw while converting the UI graph to API');
    log('  format. No POST to /prompt was made — the server never saw this workflow.');
    log('  An API-only harness cannot see this class of bug.');
    log('');
    for (const e of runErrors) log('  ' + fmtEvent(e));
    addFailure('frontend-conversion', runErrors.length
      ? runErrors.map(e => e.text).join('\n---\n')
      : 'Run produced no POST /prompt and no captured error');
    return finish({});
  }

  // ---- (b) server rejected the prompt at validation ------------------------
  if (promptStatus !== null && promptStatus !== 200) {
    log('');
    log(`FAILURE — (b) SERVER-SIDE VALIDATION REJECTION (HTTP ${promptStatus})`);
    log('  The frontend converted the graph and POSTed it. ComfyUI refused it at');
    log('  validation. Graph/model/widget problem, not a frontend conversion problem.');
    log('');
    log(JSON.stringify(promptResponse, null, 2).split('\n').map(l => '    ' + l).join('\n'));
    for (const e of runErrors) log('  ' + fmtEvent(e));
    addFailure('server-validation', `HTTP ${promptStatus}\n` + JSON.stringify(promptResponse, null, 2));
    return finish({});
  }

  if (promptStatus === null) {
    addFailure('submit-timeout', `no response to POST /prompt within ${opt.submitTimeoutMs} ms`);
    for (const e of runErrors) addFailure('frontend-runtime', e.text);
    return finish({});
  }

  const promptId = promptResponse && promptResponse.prompt_id;
  const nodeErrors = (promptResponse && promptResponse.node_errors) || {};
  if (Object.keys(nodeErrors).length) {
    log('');
    log('FAILURE — (b) SERVER-SIDE VALIDATION REJECTION (node_errors on an HTTP 200)');
    log(JSON.stringify(nodeErrors, null, 2).split('\n').map(l => '    ' + l).join('\n'));
    addFailure('server-validation', 'node_errors: ' + JSON.stringify(nodeErrors, null, 2));
    return finish({});
  }
  log(`prompt accepted HTTP ${promptStatus}  prompt_id=${promptId}  (${timings.submit_ms} ms from the click)`);

  if (runErrors.length) {
    log('');
    log('FAILURE — frontend error after the prompt was accepted');
    for (const e of runErrors) { log('  ' + fmtEvent(e)); addFailure('frontend-runtime', e.text); }
  }

  // ---- short-circuit modes -------------------------------------------------
  if (opt.mode === 'no-submit') {
    return finish({
      passNote: [
        'The frontend converted the graph and produced a well-formed /prompt body.',
        'Nothing was sent to the server: server validation and execution are UNTESTED.',
      ],
    });
  }
  if (opt.mode === 'no-execute') {
    cancelledByHarness = true;
    // Cancel ONLY our own prompt. This pod is shared: `{"clear":true}` or a bare
    // /interrupt would kill another workstream's running render.
    try {
      const q = await (await fetch(`${opt.url}/queue`)).json();
      const running = (q.queue_running || []).some(it => it[1] === promptId);
      if (running) {
        await fetch(`${opt.url}/interrupt`, { method: 'POST' });
        log(`cancelled       our prompt was running -> POST /interrupt`);
      } else {
        await fetch(`${opt.url}/queue`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ delete: [promptId] }),
        });
        log(`cancelled       POST /queue {"delete":["${promptId}"]}  (only our own item; other queue entries untouched)`);
      }
    } catch (e) {
      log(`WARNING         could not cancel the queued prompt: ${e.message}`);
    }
    return finish({
      passNote: [
        'Frontend conversion OK and the server accepted the prompt at validation.',
        'The render was cancelled: execution is UNTESTED.',
      ],
    });
  }

  // =========================================================================
  // PHASE 4 — wait for the render
  // =========================================================================
  const tExec = Date.now();
  let history = null;
  const execDeadline = Date.now() + opt.executeTimeoutMs;
  let lastLog = Date.now();
  let queueNoted = false;

  // The shipped NSFW graph pauses mid-render on #603 INSTARAW_ImageFilter and waits
  // for a human to pick an image. That pause IS the buyer journey, so --drive-selector
  // does what the buyer does: click an image in the popup, then press Send. The popup
  // is the custom element <instaraw-imgae-filter-popup class="instaraw_popup"> from
  // ComfyUI_INSTARAW/js/popup.js (element name misspelled upstream — do not "fix" it,
  // this selector depends on it). Send is a button.control created in the same file.
  const POPUP = 'instaraw-imgae-filter-popup.instaraw_popup';
  const driveSelectorIfPresent = async () => {
    if (!opt.driveSelector || selectorInfo.driven || selectorInfo.abandoned) return;
    // The popup is broadcast to every connected browser, so one can appear here
    // that belongs to a render queued by somebody else. Only ever answer our own:
    // clicking Send on a foreign selector would hand another workstream's render
    // an image it did not choose.
    try {
      const q = await (await fetch(`${opt.url}/queue`)).json();
      const oursRunningNow = (q.queue_running || []).some(it => it[1] === promptId);
      if (oursRunningNow && selectorInfo.our_run_started_ms === null) selectorInfo.our_run_started_ms = Date.now();
      if (oursRunningNow
          && selectorInfo.our_run_started_ms !== null
          && Date.now() - selectorInfo.our_run_started_ms > opt.selectorTimeoutMs
          && !selectorInfo.appeared) {
        selectorInfo.abandoned = true;
        addFailure('selector', `--drive-selector was requested but no image selector popup appeared within ${opt.selectorTimeoutMs} ms of our prompt starting to run`);
        return;
      }
      if (!oursRunningNow) {
        if (!selectorInfo.foreignSeen) {
          const any = await page.locator(`${POPUP}:not(.hidden) .grid img`).count().catch(() => 0);
          if (any) {
            selectorInfo.foreignSeen = true;
            log('  selector      a selector popup is showing but OUR prompt is not the one running; leaving it alone');
          }
        }
        return;
      }
    } catch { return; }
    let imgs;
    try {
      imgs = page.locator(`${POPUP}:not(.hidden) .grid img`);
      if (!(await imgs.count())) return;
      if (!(await imgs.first().isVisible())) return;
    } catch { return; }
    selectorInfo.appeared = true;
    selectorInfo.images = await imgs.count();
    const idx = Math.min(Math.max(0, opt.selectorPick), selectorInfo.images - 1);
    log(`  selector      image selector popup appeared with ${selectorInfo.images} image(s); clicking #${idx} then Send`);
    // The Send button lives on the popup's floating window, which is appended to
    // document.body rather than inside <instaraw-imgae-filter-popup>, so this query
    // is deliberately document-wide. popup.js:122-125.
    const send = page.locator('button.control:visible').filter({ hasText: /^Send$/ });
    if (!(await send.count())) {
      selectorInfo.abandoned = true;
      addFailure('selector', 'image selector popup appeared but no visible Send button was found');
      return;
    }
    // popup.js disabled() sets the real DOM .disabled property, so this is a true
    // assertion on the buyer-visible state, not a guess.
    const enabledBefore = await send.first().isEnabled();

    await imgs.nth(idx).click();
    selectorInfo.picked = idx;
    await sleep(300); // let redraw()/render() run

    const enabledAfter = await send.first().isEnabled();
    selectorInfo.send_enabled_before_pick = enabledBefore;
    selectorInfo.send_enabled_after_pick = enabledAfter;
    log(`  selector      Send enabled before pick=${enabledBefore}, after pick=${enabledAfter}`);
    if (!enabledAfter) {
      // This is the shipped defect: with >1 image the button never enabled and the
      // buyer was stranded until the 600 s timeout sent nothing.
      selectorInfo.abandoned = true;
      addFailure('selector', `clicked image #${idx} of ${selectorInfo.images} but the Send button is still disabled — the buyer cannot proceed`);
      return;
    }
    await send.first().click();
    selectorInfo.driven = true;
    selectorInfo.sent_at_ms = Date.now() - tExec;
    log(`  selector      Send pressed at ${Math.round(selectorInfo.sent_at_ms / 1000)}s into the render`);
  };

  while (Date.now() < execDeadline) {
    await drainInPage();
    await driveSelectorIfPresent();
    if (execError || execInterrupted) break;
    if (!queueNoted) {
      try {
        const q = await (await fetch(`${opt.url}/queue`)).json();
        const running = (q.queue_running || []);
        const pending = (q.queue_pending || []);
        const oursRunning = running.some(it => it[1] === promptId);
        if (!oursRunning && (running.length || pending.length)) {
          const ahead = running.length + pending.filter(it => it[1] !== promptId).length;
          log(`  queue         our prompt is waiting behind ${ahead} other item(s) on this ComfyUI — the wait below includes that queueing time`);
          queueNoted = true;
        } else if (oursRunning) {
          queueNoted = true;
        }
      } catch { /* transient */ }
    }
    try {
      const r = await fetch(`${opt.url}/history/${promptId}`);
      if (r.ok) {
        const j = await r.json();
        const h = j && j[promptId];
        if (h && h.status && (h.status.completed === true || h.status.status_str === 'success' || h.status.status_str === 'error')) {
          history = h;
          break;
        }
      }
    } catch { /* transient */ }
    if (Date.now() - lastLog > 30000) {
      lastLog = Date.now();
      const last = wsEvents.filter(e => e.type === 'executing').slice(-1)[0];
      log(`  ...rendering  ${Math.round((Date.now() - tExec) / 1000)}s   last node: ${last && last.data ? JSON.stringify(last.data.node) : 'none yet'}`);
    }
    await sleep(2000);
  }
  timings.execute_ms = Date.now() - tExec;
  await drainInPage();

  if (execError) {
    log('');
    log('FAILURE — (c) EXECUTION ERROR MID-RENDER');
    log(`  node ${execError.node_id} (${execError.node_type}): ${execError.exception_type}: ${execError.exception_message}`);
    if (execError.traceback) log(execError.traceback.map(l => '    ' + String(l).replace(/\n$/, '')).join('\n'));
    addFailure('execution', `${execError.node_type} #${execError.node_id}: ${execError.exception_type}: ${execError.exception_message}`);
    return finish({});
  }
  if (execInterrupted) {
    addFailure('execution', 'execution was interrupted');
    return finish({});
  }
  if (!history) {
    addFailure('execution-timeout', `render did not finish within ${opt.executeTimeoutMs} ms`);
    return finish({});
  }
  if (history.status && history.status.status_str === 'error') {
    log('');
    log('FAILURE — (c) execution error reported in /history');
    log(JSON.stringify(history.status.messages, null, 2));
    addFailure('execution', JSON.stringify(history.status.messages));
    return finish({});
  }

  const histOutputs = [];
  for (const [nodeId, out] of Object.entries(history.outputs || {})) {
    for (const im of (out.images || [])) histOutputs.push({ ...im, node: nodeId });
  }
  const finalOutputs = (histOutputs.length ? histOutputs : wsOutputs).map((im) => {
    const base = im.type === 'output' ? opt.outputDir : path.join(path.dirname(opt.outputDir), im.type || 'output');
    const abs = path.join(base, im.subfolder || '', im.filename);
    const exists = fs.existsSync(abs);
    return { ...im, path: abs, exists, size: exists ? fs.statSync(abs).size : null };
  });

  const alreadyReported = new Set(failures.map(f => f.message));
  for (const e of rec.errorsIn(['run'])) {
    if (alreadyReported.has(e.text)) continue;
    log('');
    log('FAILURE — frontend error during the render');
    log('  ' + fmtEvent(e));
    addFailure('frontend-runtime', e.text);
  }

  log('');
  log(`render          ${timings.execute_ms} ms  (${Math.round(timings.execute_ms / 1000)}s)`);
  log('  output images:');
  if (!finalOutputs.length) log('    (none — the workflow produced no image output)');
  for (const o of finalOutputs) log(`    ${o.exists ? 'OK  ' : 'MISS'} ${o.path}${o.size !== null ? `  (${o.size} bytes)` : ''}  [node ${o.node}]`);
  return finish({
    outputs: finalOutputs,
    passNote: [
      'The workflow opened in a real browser, the real Run button was pressed, the',
      'frontend converted the graph, the server accepted it, the render completed,',
      'and no frontend error was raised at any point after boot.',
      `Output images: ${finalOutputs.filter(o => o.exists).length}/${finalOutputs.length} present on disk.`,
    ],
  });
}

main().catch(async (e) => {
  const msg = `unexpected harness failure: ${(e && e.stack) || e}`;
  process.stderr.write(`browser_harness: ${msg}\n`);
  if (globalFinish) {
    // Still write result.json / console.log / screenshot — a crashed run that
    // leaves no evidence is the one thing worse than a failing run.
    try { return await globalFinish({ status: 'harness-error', message: msg }); } catch { /* fall through */ }
  }
  process.exit(2);
});
