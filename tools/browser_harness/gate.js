#!/usr/bin/env node
'use strict';
/**
 * gate.js — the buyer's journey, driven in a real browser, photographed at every step.
 *
 * browser_harness/run.js answers "did it work?" with an exit code. This answers it
 * with pictures: the workflow open on a full canvas, the LoRA widgets carrying the
 * owner's files, the prompt typed into the panel, the render's selector pause
 * clicked through, and the finished image on screen.
 *
 * Every claim it prints is read back out of the page after the action, never
 * assumed from the fact that the click did not throw.
 *
 * Exit codes: 0 pass · 1 the workflow failed · 2 the gate could not be carried out.
 */

const fs = require('fs');
const path = require('path');
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const { chromium } = require(path.join(REPO_ROOT, 'node_modules', 'playwright'));

const USAGE = `
gate.js — screenshot the buyer's journey through a saved ComfyUI workflow

  node tools/browser_harness/gate.js --workflow OFMTech_NSFW --tag run1 [options]

  --workflow, -w <name>   saved workflow name (no .json)
  --url <url>             default http://127.0.0.1:18188  (env COMFY_URL)
  --workflows-dir <dir>   default /workspace/ComfyUI/user/default/workflows
  --output-dir <dir>      default /workspace/ComfyUI/output
  --install <path.json>   copy this file to <workflows-dir>/<workflow>.json first
  --out <dir>             screenshot dir, default results/gate
  --tag <str>             filename prefix for this run's screenshots (required)
  --sdxl-lora <file>      value to set on node 618 (default lunaskye.safetensors)
  --zit-lora <file>       value to set on node 116 (default luna.safetensors)
  --prompt <text>         prompt to type into the RPG panel on node 483
  --face-prompt <text>    prompt to type into #106 "Face Detailer Prompt", which lives
                          inside the subgraph on host #620. Omit to leave it shipped.
  --face-prompt-file <p>  same, read from a file (avoids shell quoting)
  --face-host <id>        subgraph host carrying #106's promoted widget (default 620)
  --face-node <id>        the CLIPTextEncode inside it (default 106)
  --no-run                stop after the prompt is entered; do not press Run
  --selector-pick N       which image to click in the INSTARAW selector (default 0)
  --execute-timeout-ms N  default 5400000 (this pod queues renders behind each other)
  --viewport WxH          default 1920x1080
`;

const DEFAULT_PROMPT =
  'photorealistic full body photograph of a young woman with long dark hair standing ' +
  'on a hotel balcony at golden hour, wearing a black silk slip dress, natural skin ' +
  'texture with visible pores and freckles, shot on 85mm, shallow depth of field';

const opt = {
  url: process.env.COMFY_URL || 'http://127.0.0.1:18188',
  workflow: null,
  workflowsDir: process.env.COMFY_WORKFLOWS_DIR || '/workspace/ComfyUI/user/default/workflows',
  outputDir: process.env.COMFY_OUTPUT_DIR || '/workspace/ComfyUI/output',
  install: null,
  out: path.join(REPO_ROOT, 'results', 'gate'),
  tag: null,
  sdxlLora: 'lunaskye.safetensors',
  zitLora: 'luna.safetensors',
  prompt: DEFAULT_PROMPT,
  facePrompt: null,
  faceHost: 620,
  faceNode: 106,
  noRun: false,
  selectorPick: 0,
  executeTimeoutMs: 5400000,
  viewport: '1920x1080',
};

function die(m) { process.stderr.write(`gate: ${m}\n`); process.exit(2); }
(function parse() {
  const a = process.argv;
  for (let i = 2; i < a.length; i++) {
    const nx = () => { const v = a[++i]; if (v === undefined) die(`${a[i - 1]} needs a value`); return v; };
    switch (a[i]) {
      case '--workflow': case '-w': opt.workflow = nx(); break;
      case '--url': opt.url = nx(); break;
      case '--workflows-dir': opt.workflowsDir = nx(); break;
      case '--output-dir': opt.outputDir = nx(); break;
      case '--install': opt.install = nx(); break;
      case '--out': opt.out = nx(); break;
      case '--tag': opt.tag = nx(); break;
      case '--sdxl-lora': opt.sdxlLora = nx(); break;
      case '--zit-lora': opt.zitLora = nx(); break;
      case '--prompt': opt.prompt = nx(); break;
      case '--face-prompt': opt.facePrompt = nx(); break;
      case '--face-prompt-file': opt.facePrompt = fs.readFileSync(nx(), 'utf8').replace(/\n+$/, ''); break;
      case '--face-host': opt.faceHost = Number(nx()); break;
      case '--face-node': opt.faceNode = Number(nx()); break;
      case '--no-run': opt.noRun = true; break;
      case '--selector-pick': opt.selectorPick = Number(nx()); break;
      case '--execute-timeout-ms': opt.executeTimeoutMs = Number(nx()); break;
      case '--viewport': opt.viewport = nx(); break;
      case '--help': case '-h': process.stdout.write(USAGE); process.exit(0); break;
      default: die(`unknown option ${a[i]}\n${USAGE}`);
    }
  }
  if (!opt.workflow) die('--workflow is required');
  if (!opt.tag) die('--tag is required (it names the screenshots)');
})();

const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const logLines = [];
function log(s) { const line = String(s); logLines.push(line); process.stdout.write(line + '\n'); }
function ensureDir(d) { fs.mkdirSync(d, { recursive: true }); }

const wfName = opt.workflow.replace(/\.json$/i, '');
ensureDir(opt.out);
let shotN = 0;
const shots = [];
async function shot(page, name, note) {
  shotN += 1;
  const file = path.join(opt.out, `${opt.tag}-${String(shotN).padStart(2, '0')}-${name}.png`);
  await page.screenshot({ path: file });
  const size = fs.statSync(file).size;
  shots.push({ file, note: note || '', bytes: size });
  log(`screenshot      ${file}  (${size} B)${note ? '  — ' + note : ''}`);
  return file;
}

// ---------------------------------------------------------------------------
// in-page helpers, injected as strings
// ---------------------------------------------------------------------------

// Frame a set of root-level node ids so they fill the canvas. ds.offset is in graph
// units and screen = (graph + offset) * scale, verified against the running canvas.
// INSET matters: ComfyUI's tab bar, top menu, left toolbar and image-feed strip are
// overlays floating ON TOP of the canvas, so the canvas element is larger than the
// part of it a screenshot can actually show. Framing to the raw canvas puts node
// titles underneath the menu bar.
// useCurrentGraph: frame inside whatever graph the canvas is showing (i.e. after
// entering a subgraph). Omitted / false keeps the original root-graph behaviour, so
// every pre-existing call site is byte-for-byte unchanged in effect.
const FRAME_FN = `(ids, pad, maxScale, inset, useCurrentGraph) => {
  const app = window.app, LG = window.LiteGraph;
  const g = useCurrentGraph ? app.canvas.graph : (app.rootGraph || app.graph);
  const all = g.nodes || g._nodes || [];
  const nodes = ids && ids.length ? all.filter(n => ids.includes(n.id)) : all;
  if (!nodes.length) return { err: 'no nodes' };
  const ins = Object.assign({ top: 100, bottom: 46, left: 70, right: 24 }, inset || {});
  const th = (LG && LG.NODE_TITLE_HEIGHT) || 30;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const n of nodes) {
    x0 = Math.min(x0, n.pos[0]); y0 = Math.min(y0, n.pos[1] - th);
    x1 = Math.max(x1, n.pos[0] + n.size[0]); y1 = Math.max(y1, n.pos[1] + n.size[1]);
  }
  x0 -= pad; y0 -= pad; x1 += pad; y1 += pad;
  const el = app.canvas.canvas;
  const cw = el.clientWidth, ch = el.clientHeight;
  const vw = cw - ins.left - ins.right, vh = ch - ins.top - ins.bottom;
  const scale = Math.min(vw / (x1 - x0), vh / (y1 - y0), maxScale);
  const ds = app.canvas.ds;
  ds.scale = scale;
  ds.offset[0] = -x0 + ins.left / scale + (vw / scale - (x1 - x0)) / 2;
  ds.offset[1] = -y0 + ins.top / scale + (vh / scale - (y1 - y0)) / 2;
  if (ds.computeVisibleArea) ds.computeVisibleArea(app.canvas.viewport);
  if (ds.onChanged) ds.onChanged();
  app.canvas.setDirty(true, true);
  return { scale, offset: [ds.offset[0], ds.offset[1]], box: [x0, y0, x1, y1], nodes: nodes.length, canvas: [cw, ch] };
}`;

// Collapse/expand a node the same way clicking the dot in its title bar does. Used
// only to get the huge prompt panel on #483 out of the way of the LoRA nodes'
// titles for one screenshot; it is put back immediately and nothing is saved.
const COLLAPSE_FN = `(nodeId, want) => {
  const g = window.app.rootGraph || window.app.graph;
  const n = (g.nodes || g._nodes).find(x => x.id === nodeId);
  if (!n) return { err: 'no node ' + nodeId };
  const is = !!(n.flags && n.flags.collapsed);
  if (is !== want) n.collapse();
  window.app.canvas.setDirty(true, true);
  return { collapsed: !!(n.flags && n.flags.collapsed) };
}`;

// Screen position of a widget row on a root-level node, in PAGE coordinates.
// The canvas element does not start at page y=0 (tab bar), so its bounding rect is added.
const WIDGET_POINT_FN = `(nodeId, widgetName) => {
  const app = window.app;
  const g = app.rootGraph || app.graph;
  const n = (g.nodes || g._nodes).find(x => x.id === nodeId);
  if (!n) return { err: 'node ' + nodeId + ' not found' };
  const w = (n.widgets || []).find(x => x.name === widgetName);
  if (!w) return { err: 'widget ' + widgetName + ' not found on ' + nodeId };
  if (w.y === undefined) return { err: 'widget has no drawn y yet' };
  const ds = app.canvas.ds;
  const r = app.canvas.canvas.getBoundingClientRect();
  const gx = n.pos[0] + n.size[0] * 0.5;
  const gy = n.pos[1] + w.y + 10;
  return {
    x: r.left + (gx + ds.offset[0]) * ds.scale,
    y: r.top + (gy + ds.offset[1]) * ds.scale,
    value: w.value, widgetY: w.y, scale: ds.scale,
  };
}`;

// Every node in the graph, root and inside every subgraph, with the SAME registration
// test the frontend itself uses in loadGraphData:  !(node.type in LiteGraph.registered_node_types)
const NODE_AUDIT_FN = `() => {
  const app = window.app, LG = window.LiteGraph;
  const reg = (LG && LG.registered_node_types) || {};
  const rows = [];
  const seenSub = new Set();
  const walk = (graph, where) => {
    for (const n of (graph.nodes || graph._nodes || [])) {
      const isHost = !!n.subgraph;
      rows.push({
        id: String(n.id), type: n.type, title: n.title || '', where,
        registered: (n.type in reg), isSubgraphHost: isHost,
        has_errors: !!n.has_errors, mode: n.mode,
      });
      if (isHost) {
        const key = n.subgraph.id || n.subgraph.name;
        if (!seenSub.has(key)) { seenSub.add(key); walk(n.subgraph, n.subgraph.name || String(key)); }
      }
    }
  };
  walk(app.rootGraph || app.graph, 'root');
  const dialogs = [...document.querySelectorAll('.p-dialog, [role="dialog"]')].map(d => ({
    cls: String(d.className).slice(0, 120), visible: !!d.offsetParent, text: (d.innerText || '').slice(0, 600),
  }));
  const toasts = [...document.querySelectorAll('.p-toast-message')].map(t => (t.innerText || '').slice(0, 300));
  return { rows, dialogs, toasts, registeredCount: Object.keys(reg).length, title: document.title };
}`;

// --- reaching #106, which is NOT on the root canvas -------------------------
// #106 "Face Detailer Prompt" lives inside the subgraph whose host is #620, and the
// host ships COLLAPSED (flags.collapsed true in the file, all seven hosts do). Its
// text widget is promoted onto the host as "106: text", so once the host is expanded
// the buyer can type it without entering the subgraph at all. Both surfaces are
// exercised here: type on the host, then go inside and photograph the node itself.

// The collapse box is the square at the top-left of the title bar. The frontend's own
// hit test is  isPointInCollapse(x,y) -> isInRectangle(x, y, pos[0], pos[1]-TH, TH, TH)
// (api-gz4kgzki.js), so this returns the centre of exactly that rectangle in page px.
const COLLAPSE_BOX_POINT_FN = `(nodeId) => {
  const app = window.app, LG = window.LiteGraph;
  const g = app.canvas.graph;
  const n = (g.nodes || g._nodes).find(x => x.id === nodeId);
  if (!n) return { err: 'node ' + nodeId + ' not found' };
  const TH = (LG && LG.NODE_TITLE_HEIGHT) || 30;
  const ds = app.canvas.ds, r = app.canvas.canvas.getBoundingClientRect();
  const gx = n.pos[0] + TH / 2, gy = n.pos[1] - TH / 2;
  return {
    x: r.left + (gx + ds.offset[0]) * ds.scale,
    y: r.top + (gy + ds.offset[1]) * ds.scale,
    collapsed: !!(n.flags && n.flags.collapsed),
    hitTest: typeof n.isPointInCollapse === 'function' ? n.isPointInCollapse(gx, gy) : null,
  };
}`;

// The DOM textarea behind a promoted multiline widget. It is tagged with a data
// attribute so Playwright can address the very element the buyer types into; the tag
// is harness bookkeeping and changes nothing about the graph.
const TAG_TEXT_WIDGET_FN = `(nodeId, widgetName, tag) => {
  const g = window.app.canvas.graph;
  const n = (g.nodes || g._nodes).find(x => x.id === nodeId);
  if (!n) return { err: 'node ' + nodeId + ' not found' };
  const w = (n.widgets || []).find(x => x.name === widgetName);
  if (!w) return { err: 'widget ' + JSON.stringify(widgetName) + ' not on #' + nodeId +
                        '; has: ' + JSON.stringify((n.widgets || []).map(x => x.name)) };
  if (!w.element) return { err: 'widget ' + widgetName + ' has no DOM element' };
  w.element.setAttribute('data-gate-tag', tag);
  const r = w.element.getBoundingClientRect();
  return { ok: true, widgetType: w.type, value: String(w.value),
           visible: !!w.element.offsetParent,
           rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}`;

// Read the value back from BOTH surfaces: the promoted widget on the host and the
// actual CLIPTextEncode inside the subgraph definition. Agreement is what proves the
// text landed on #106 and not merely on a host-level copy of it.
const READ_FACE_PROMPT_FN = `(hostId, innerId, widgetName) => {
  const app = window.app;
  const g = app.rootGraph || app.graph;
  const host = (g.nodes || g._nodes).find(x => x.id === hostId);
  if (!host) return { err: 'host #' + hostId + ' not found at root' };
  const promoted = (host.widgets || []).find(x => x.name === innerId + ': ' + widgetName);
  const sub = host.subgraph;
  if (!sub) return { err: '#' + hostId + ' is not a subgraph host' };
  const inner = (sub.nodes || sub._nodes || []).find(x => x.id === innerId);
  if (!inner) return { err: 'node #' + innerId + ' not inside ' + (sub.name || sub.id) };
  const iw = (inner.widgets || []).find(x => x.name === widgetName);
  return {
    subgraph_name: sub.name || null,
    promoted_widget_name: promoted ? promoted.name : null,
    promoted_value: promoted ? String(promoted.value) : null,
    inner_node_type: inner.type, inner_node_title: inner.title || null,
    inner_value: iw ? String(iw.value) : null,
    same_object: !!(promoted && iw && promoted === iw),
  };
}`;

const GRAPH_STATE_FN = `() => {
  const app = window.app, c = app.canvas, g = c.graph;
  return {
    isRoot: g === (app.rootGraph || app.graph),
    name: g.name || null,
    nodeCount: (g.nodes || g._nodes || []).length,
    breadcrumb: [...document.querySelectorAll('.subgraph-breadcrumb .p-breadcrumb-item, .p-breadcrumb-item')]
      .map(e => (e.innerText || '').trim()).filter(Boolean),
  };
}`;

// ---------------------------------------------------------------------------

let browser = null;
const failures = [];
function fail(cls, msg) { failures.push({ class: cls, message: msg }); log(`FAILURE [${cls}] ${msg}`); }

const result = {
  tag: opt.tag, workflow: wfName, url: opt.url, started: new Date().toISOString(),
  workflow_sha256: null, load_path: null, node_audit: null, loras: {}, prompt: {},
  prompt_id: null, api_graph_nodes: null, selector: {}, outputs: [], timings: {},
  page_errors: [], failures, screenshots: shots, status: null,
};

function writeResult(status) {
  result.status = status;
  result.finished = new Date().toISOString();
  const p = path.join(opt.out, `${opt.tag}-result.json`);
  fs.writeFileSync(p, JSON.stringify(result, null, 2));
  fs.writeFileSync(path.join(opt.out, `${opt.tag}-console.log`), logLines.join('\n') + '\n');
  log(`\nartifacts       ${p}`);
}

async function main() {
  // ---- install (optional) --------------------------------------------------
  const target = path.join(opt.workflowsDir, `${wfName}.json`);
  if (opt.install) {
    ensureDir(opt.workflowsDir);
    fs.copyFileSync(path.resolve(opt.install), target);
    log(`install         ${path.resolve(opt.install)} -> ${target}`);
  }
  if (!fs.existsSync(target)) die(`no saved workflow at ${target}`);
  const crypto = require('crypto');
  result.workflow_sha256 = crypto.createHash('sha256').update(fs.readFileSync(target)).digest('hex');
  log(`workflow        ${target}`);
  log(`                sha256 ${result.workflow_sha256}`);

  // ---- server reachable + object_info for the independent type check -------
  let objectInfo;
  try {
    const r = await fetch(`${opt.url}/object_info`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    objectInfo = await r.json();
  } catch (e) {
    die(`could not GET ${opt.url}/object_info: ${e.message}`);
  }
  log(`object_info     ${Object.keys(objectInfo).length} node types registered on the server`);

  const [vw, vh] = opt.viewport.split('x').map(Number);
  browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const ctx = await browser.newContext({ viewport: { width: vw, height: vh } });
  const page = await ctx.newPage();
  page.setDefaultTimeout(45000);

  const pageErrors = [];
  page.on('pageerror', e => { pageErrors.push({ when: new Date().toISOString(), text: (e.stack || e.message || '').slice(0, 800) }); });
  page.on('console', m => { if (m.type() === 'error') pageErrors.push({ when: new Date().toISOString(), text: 'console.error: ' + m.text().slice(0, 500), url: (m.location() || {}).url }); });

  const wsEvents = [];
  const wsOutputs = [];
  let execError = null, execInterrupted = false;
  page.on('websocket', ws => {
    ws.on('framereceived', ev => {
      if (typeof ev.payload !== 'string') return;
      let msg; try { msg = JSON.parse(ev.payload); } catch { return; }
      if (!msg || !msg.type) return;
      if (['progress', 'progress_state', 'crystools.monitor'].includes(msg.type)) return;
      wsEvents.push({ t: Date.now(), type: msg.type, data: msg.data });
      if (msg.type === 'executed' && msg.data && msg.data.output && msg.data.output.images) {
        for (const im of msg.data.output.images) wsOutputs.push({ ...im, node: msg.data.node });
      }
      if (msg.type === 'execution_error') execError = msg.data;
      if (msg.type === 'execution_interrupted') execInterrupted = true;
    });
  });

  let promptId = null, promptStatus = null, promptBody = null, promptResponse = null;
  page.on('response', async r => {
    if (!/\/(api\/)?prompt$/.test(new URL(r.url()).pathname) || r.request().method() !== 'POST') return;
    promptBody = r.request().postData();
    try { promptResponse = await r.json(); } catch { promptResponse = null; }
    promptStatus = r.status();
  });

  // =========================== boot ========================================
  let t0 = Date.now();
  await page.goto(`${opt.url}/`, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForSelector('canvas#graph-canvas', { timeout: 90000 });
  await page.waitForFunction(() => !!(window.app && window.app.vueAppReady), null, { timeout: 90000 });
  await sleep(2500);
  result.timings.boot_ms = Date.now() - t0;
  const bootErrCount = pageErrors.length;
  log(`boot            ${result.timings.boot_ms} ms   ${bootErrCount} console/page error(s) before any workflow was opened`);

  // ---- first-run modal ------------------------------------------------------
  // A ComfyUI that has never been opened in a browser shows the stock Templates
  // browser over everything on the very first page load (it is what writes
  // Comfy.InstalledVersion / Comfy.TutorialCompleted into user/default/
  // comfy.settings.json, so it never appears again). It covers the Workflows tab.
  // A buyer closes it; so does this. It is photographed first, because it is part
  // of the clean-install journey and a run that silently swallowed it would be
  // hiding something the buyer sees.
  const dumpDialogs = `(() => [...document.querySelectorAll('.p-dialog, [role="dialog"]')]
      .filter(d => !!d.offsetParent)
      .map(d => ({ cls: String(d.className).slice(0, 100), text: (d.innerText || '').slice(0, 400) })))()`;
  const bootDialogs = await page.evaluate(dumpDialogs);
  result.first_run_dialog = { seen: bootDialogs.length > 0, dialogs: bootDialogs };
  if (bootDialogs.length) {
    log(`first-run modal ${bootDialogs.length} dialog(s) open on the very first page load of this install:`);
    for (const d of bootDialogs) log(`                  "${d.text.split('\n').slice(0, 3).join(' / ')}"`);
    await shot(page, 'first-run-dialog', 'a fresh install opens the stock ComfyUI Templates browser over the UI; the buyer must close it');
    const closers = [
      '.p-dialog button[aria-label="Close dialog"]',
      '.p-dialog .p-dialog-close-button',
      '.p-dialog button[aria-label="Close"]',
    ];
    let closed = false;
    for (const sel of closers) {
      const l = page.locator(sel);
      if (await l.count()) { await l.first().click({ timeout: 10000 }).catch(() => {}); closed = true; break; }
    }
    if (!closed) await page.keyboard.press('Escape');
    await sleep(1500);
    const still = await page.evaluate(dumpDialogs);
    result.first_run_dialog.closed = still.length === 0;
    log(`first-run modal closed the way a buyer does; dialogs still open: ${still.length}`);
    if (still.length) { fail('dialog', `a modal dialog stayed on screen after closing it: ${still.map(d => d.text.slice(0, 120)).join(' | ')}`); }
  }

  // ============= open the workflow from the workflow list ==================
  t0 = Date.now();
  await page.click('[data-testid="side-toolbar"] button.workflows-tab-button', { timeout: 25000 });
  await page.waitForSelector('[data-testid="workflows-sidebar"]', { timeout: 25000 });
  const entry = page.locator(`[data-testid="tree-node-root/${wfName}.json"]`);
  if (!(await entry.count())) {
    const alt = page.locator('[data-testid^="tree-node-"]').filter({ hasText: wfName });
    if (!(await alt.count())) { await shot(page, 'sidebar-missing', 'workflow not in the list'); die(`"${wfName}" is not in the Workflows sidebar`); }
    await alt.first().click();
  } else {
    await entry.first().click();
  }
  await page.waitForFunction((re) => new RegExp(re).test(document.title), `^\\*?${wfName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')} - `, { timeout: 120000 });
  await page.waitForFunction(() => {
    const g = window.app && window.app.rootGraph;
    return !!(g && (g.nodes || g._nodes || []).length > 0);
  }, null, { timeout: 120000 });
  await sleep(4000);
  result.timings.load_ms = Date.now() - t0;
  result.load_path = 'workflow-list (sidebar click)';
  log(`open workflow   ${result.timings.load_ms} ms   from the Workflows sidebar   title="${await page.title()}"`);

  // close the sidebar so the canvas is unobstructed
  await page.click('[data-testid="side-toolbar"] button.workflows-tab-button').catch(() => {});
  await sleep(600);

  // ============= red-node / missing-node audit =============================
  const audit = await page.evaluate(`(${NODE_AUDIT_FN})()`);
  const hostTypes = new Set(audit.rows.filter(r => r.isSubgraphHost).map(r => r.type));
  const types = [...new Set(audit.rows.map(r => r.type))];
  const notRegistered = audit.rows.filter(r => !r.registered);
  const withErrors = audit.rows.filter(r => r.has_errors);
  const notInObjectInfo = types
    .filter(t => !hostTypes.has(t))
    .filter(t => !(t in objectInfo));
  const visibleDialogs = audit.dialogs.filter(d => d.visible);

  result.node_audit = {
    total_nodes: audit.rows.length,
    distinct_types: types.length,
    subgraph_host_types: [...hostTypes],
    frontend_registered_count: audit.registeredCount,
    not_registered_in_frontend: notRegistered,
    not_in_object_info: notInObjectInfo,
    nodes_flagged_has_errors: withErrors,
    dialogs: audit.dialogs,
    toasts: audit.toasts,
  };
  log(`node audit      ${audit.rows.length} nodes across root + every subgraph, ${types.length} distinct types`);
  log(`                frontend registered_node_types: ${audit.registeredCount}`);
  log(`                node types NOT registered in the frontend (= red nodes): ${notRegistered.length}`);
  for (const r of notRegistered) log(`                  MISSING  #${r.id} ${r.type}  (${r.where})`);
  log(`                node types absent from /object_info (excl. ${hostTypes.size} subgraph hosts): ${notInObjectInfo.length}`);
  for (const t of notInObjectInfo) log(`                  ABSENT   ${t}`);
  log(`                nodes flagged has_errors: ${withErrors.length}`);
  log(`                modal dialogs on screen: ${visibleDialogs.length}${visibleDialogs.length ? ' -> ' + JSON.stringify(visibleDialogs.map(d => d.text.slice(0, 120))) : ''}`);
  log(`                error toasts on screen: ${audit.toasts.length}${audit.toasts.length ? ' -> ' + JSON.stringify(audit.toasts) : ''}`);

  if (notRegistered.length) fail('missing-nodes', `${notRegistered.length} node(s) have a type the frontend never registered — these draw red`);
  if (visibleDialogs.length) fail('dialog', `a modal dialog is on screen after loading the workflow: ${visibleDialogs.map(d => d.text.slice(0, 200)).join(' | ')}`);
  if (audit.toasts.length) fail('toast', `error toast(s) after loading: ${audit.toasts.join(' | ')}`);

  // ============= full canvas, fitted =======================================
  // The minimap is a floating panel that covers a corner of the canvas. For a shot
  // whose whole point is "nothing on this canvas is red", nothing may be hidden.
  const minimapWas = await page.evaluate(`(async () => {
    const s = window.app.extensionManager && window.app.extensionManager.setting;
    if (!s) return null;
    const was = s.get('Comfy.Minimap.Visible');
    try { await s.set('Comfy.Minimap.Visible', false); } catch (e) { return { was, err: String(e) }; }
    return { was };
  })()`);
  log(`minimap         hidden for the canvas screenshots (was ${JSON.stringify(minimapWas && minimapWas.was)}) so it cannot cover a node`);
  await sleep(800);
  const fit = await page.evaluate(`(${FRAME_FN})(null, 60, 1.0, null)`);
  await sleep(1800);
  log(`fit view        scale=${(fit.scale || 0).toFixed(4)}  framing ${fit.nodes} root-level nodes  canvas=${fit.canvas}`);
  await shot(page, 'workflow-open-full-canvas',
    `${wfName} opened from the workflow list; ${audit.rows.length} nodes, ${notRegistered.length} red, ${visibleDialogs.length} dialogs`);

  // ============= the prompt ===============================================
  await page.evaluate(`(${FRAME_FN})([483], 20, 0.62, null)`);
  await sleep(2500);
  const ta = page.locator('.instaraw-rpg-positive-textarea').first();
  if (!(await ta.count())) {
    await shot(page, 'prompt-panel-missing', 'no positive-prompt textarea in the RPG panel');
    fail('prompt', 'the RPG panel on #483 has no .instaraw-rpg-positive-textarea to type into');
    writeResult('fail'); await browser.close(); process.exit(1);
  }
  await ta.click();
  await page.keyboard.press('Control+a');
  await page.keyboard.press('Delete');
  await page.keyboard.insertText(opt.prompt);
  // the panel commits on `change`, i.e. on blur — popup.js/reality_prompt_generator.js:7092
  await page.keyboard.press('Tab');
  await sleep(1200);
  const promptState = await page.evaluate(`(() => {
    const g = window.app.rootGraph || window.app.graph;
    const n = (g.nodes || g._nodes).find(x => x.id === 483);
    const w = (n.widgets || []).find(x => x.name === 'prompt_batch_data');
    const ta = document.querySelector('.instaraw-rpg-positive-textarea');
    let parsed = null; try { parsed = JSON.parse(w.value); } catch (e) {}
    return { widget: w.value, textarea: ta ? ta.value : null, entries: parsed ? parsed.length : null,
             firstPositive: parsed && parsed[0] ? parsed[0].positive_prompt : null };
  })()`);
  result.prompt = { typed: opt.prompt, textarea: promptState.textarea, committed: promptState.firstPositive, entries: promptState.entries };
  log(`prompt          typed into the RPG panel on #483 and committed on blur`);
  log(`                textarea now : ${JSON.stringify((promptState.textarea || '').slice(0, 90))}...`);
  log(`                node widget  : prompt_batch_data[0].positive_prompt = ${JSON.stringify((promptState.firstPositive || '').slice(0, 90))}...`);
  if (promptState.firstPositive !== opt.prompt) {
    fail('prompt', 'the prompt typed into the panel did not reach the node widget prompt_batch_data');
  }
  await shot(page, 'prompt-entered', 'the prompt typed into the panel on #483 "1 · YOUR PROMPTS & SEED"');

  // ============= LoRA stacks ==============================================
  // Real UI path: click the combo widget on the canvas, then click the file in the
  // litegraph menu that opens. The value is read back out of the graph afterwards.
  async function setLora(nodeId, widget, value, label) {
    await page.evaluate(`(${FRAME_FN})([${nodeId}], 60, 1.4, null)`);
    await sleep(900);
    const pt = await page.evaluate(`(${WIDGET_POINT_FN})(${nodeId}, ${JSON.stringify(widget)})`);
    if (pt.err) { fail('lora', `#${nodeId}: ${pt.err}`); return false; }
    await page.mouse.click(pt.x, pt.y);
    await sleep(900);
    const menu = page.locator('.litecontextmenu');
    if (!(await menu.count())) {
      await shot(page, `lora-${nodeId}-no-menu`, 'clicking the combo widget opened no menu');
      fail('lora', `#${nodeId}: clicking the ${widget} widget opened no value menu`);
      return false;
    }
    const item = page.locator('.litecontextmenu .litemenu-entry').filter({ hasText: new RegExp(`^${value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}$`) });
    if (!(await item.count())) {
      const opts = await page.locator('.litecontextmenu .litemenu-entry').allInnerTexts();
      await shot(page, `lora-${nodeId}-menu-open`, 'menu open, value not listed');
      fail('lora', `#${nodeId}: "${value}" is not offered by the widget. Offered: ${JSON.stringify(opts)}`);
      return false;
    }
    await item.first().click();
    await sleep(700);
    const readBack = await page.evaluate(`(() => {
      const g = window.app.rootGraph || window.app.graph;
      const n = (g.nodes || g._nodes).find(x => x.id === ${nodeId});
      const w = (n.widgets || []).find(x => x.name === ${JSON.stringify(widget)});
      return { value: w.value, title: n.title };
    })()`);
    log(`lora            #${nodeId} ${label}: ${widget} = ${JSON.stringify(readBack.value)}  (clicked in the widget's own menu)`);
    result.loras[nodeId] = { widget, requested: value, readBack: readBack.value, title: readBack.title };
    if (readBack.value !== value) { fail('lora', `#${nodeId} ${widget} reads ${JSON.stringify(readBack.value)} after the click, wanted ${JSON.stringify(value)}`); return false; }
    return true;
  }

  const okA = await setLora(618, 'lora_01', opt.sdxlLora, 'SDXL stack');
  const okB = await setLora(116, 'lora_01', opt.zitLora, 'Z-Image stack');

  // Both stacks in one frame, zoomed enough to read the widget rows AND the node
  // titles. The prompt panel on #483 is a DOM overlay whose element runs ~40 graph
  // units past the bottom of its own node, which lands exactly on these two nodes'
  // title bars; collapsing #483 for the duration of the screenshot is the only way
  // to photograph the titles. It is expanded again immediately and nothing is saved.
  const collapsed = await page.evaluate(`(${COLLAPSE_FN})(483, true)`);
  await sleep(900);
  await page.evaluate(`(${FRAME_FN})([618, 116], 40, 1.6, null)`);
  await sleep(1600);
  await shot(page, 'both-lora-stacks',
    `#618 lora_01=${opt.sdxlLora}  #116 lora_01=${opt.zitLora}  (both read back from the graph; #483 collapsed=${collapsed.collapsed} for this frame only)`);
  // expand it again with the node back on screen — a DOM widget only recomputes its
  // visibility when its own node is drawn, so expanding it while it is culled leaves
  // the panel blank until something else forces a draw.
  await page.evaluate(`(${FRAME_FN})([483], 20, 0.62, null)`);
  await sleep(1200);
  const restored = await page.evaluate(`(${COLLAPSE_FN})(483, false)`);
  await sleep(2000);
  const panelBack = await page.evaluate(`(() => { const e = document.querySelector('.instaraw-rpg-positive-textarea'); return { present: !!e, visible: !!(e && e.offsetParent), value: e ? e.value.slice(0,60) : null }; })()`);
  log(`panel           #483 collapsed for the LoRA frame, restored afterwards (collapsed now: ${restored.collapsed}; prompt panel visible again: ${panelBack.visible})`);
  result.prompt.panel_after_restore = panelBack;
  if (!okA || !okB) { writeResult('fail'); await browser.close(); process.exit(1); }

  // ============= the face prompt on #106 ==================================
  if (opt.facePrompt !== null) {
    const fp = { requested: opt.facePrompt, host: opt.faceHost, node: opt.faceNode };
    result.face_prompt = fp;
    const promotedName = `${opt.faceNode}: text`;

    await page.evaluate(`(${FRAME_FN})([${opt.faceHost}], 60, 1.4, null)`);
    await sleep(1800);

    // 1. the state the buyer is handed. Current files ship #620 EXPANDED (polish
    //    commit fea23a3); pre-fix files shipped it collapsed. Record which.
    const box = await page.evaluate(`(${COLLAPSE_BOX_POINT_FN})(${opt.faceHost})`);
    if (box.err) { fail('face-prompt', `#${opt.faceHost}: ${box.err}`); writeResult('fail'); await browser.close(); process.exit(1); }
    fp.host_shipped_collapsed = box.collapsed;
    log(`face prompt     #${opt.faceHost} as shipped: collapsed=${box.collapsed}`);
    await shot(page, 'face-host-as-shipped',
      `#${opt.faceHost} "5 · Face & Mouth Detail" as the workflow ships it — collapsed=${box.collapsed}`);

    // 2. expand it if needed, the way a buyer does — the collapse box in the title bar
    if (box.collapsed) {
      await page.mouse.click(box.x, box.y);
      await sleep(1500);
      const after = await page.evaluate(`(${COLLAPSE_BOX_POINT_FN})(${opt.faceHost})`);
      fp.expanded_by_clicking_collapse_box = after.collapsed === false;
      log(`face prompt     clicked the collapse box in #${opt.faceHost}'s title bar; collapsed is now ${after.collapsed}`);
      if (after.collapsed) {
        await shot(page, 'face-host-still-collapsed', 'clicking the collapse box did not expand the host');
        fail('face-prompt', `#${opt.faceHost} would not expand — #${opt.faceNode} cannot be reached through the UI`);
        writeResult('fail'); await browser.close(); process.exit(1);
      }
      await page.evaluate(`(${FRAME_FN})([${opt.faceHost}], 60, 1.4, null)`);
      await sleep(1800);
    }

    // 3. find where the buyer types. Pre-blocker-fix files promoted "106: text"
    //    onto the host; the current file promotes NOTHING on #620, so the buyer's
    //    route is INTO the subgraph. Try the promoted widget first so this gate
    //    still drives old bytes, then take the real route.
    const tag = await page.evaluate(`(${TAG_TEXT_WIDGET_FN})(${opt.faceHost}, ${JSON.stringify(promotedName)}, 'face-prompt')`);
    let typedInside = false;
    if (!tag.err) {
      fp.typed_via = 'promoted widget on the host';
      fp.shipped_value = tag.value;
      log(`face prompt     "${promotedName}" is a ${tag.widgetType} DOM widget, visible=${tag.visible}`);
      if (!tag.visible) {
        fail('face-prompt', `the "${promotedName}" textarea is not visible after expanding #${opt.faceHost}`);
        writeResult('fail'); await browser.close(); process.exit(1);
      }
      const fta = page.locator('[data-gate-tag="face-prompt"]');
      await fta.click();
      await page.keyboard.press('Control+a');
      await page.keyboard.press('Delete');
      await page.keyboard.insertText(opt.facePrompt);
      await page.keyboard.press('Tab');
      await sleep(1200);
    } else {
      typedInside = true;
      fp.typed_via = 'inside the subgraph (host promotes no widgets on current files)';
      log(`face prompt     no promoted widget on #${opt.faceHost} (${tag.err.slice(0, 90)}...)`);
      log(`face prompt     taking the buyer route: enter the subgraph and type on #${opt.faceNode} itself`);
    }

    // 4. enter the subgraph — needed to TYPE on current files, and to PHOTOGRAPH on all.
    const tbtn = await page.evaluate(`(() => {
      const app = window.app, g = app.canvas.graph;
      const n = (g.nodes || g._nodes).find(x => x.id === ${opt.faceHost});
      const b = (n.title_buttons || []).find(x => x.name === 'enter_subgraph');
      if (!b) return { err: 'no enter_subgraph title button' };
      const a = b._last_area || b._boundingRect;
      const arr = a && (a.length !== undefined ? Array.from(a) : [a.x, a.y, a.width, a.height]);
      if (!arr || !arr[2] || !arr[3]) return { err: 'title button has no drawn area yet: ' + JSON.stringify(arr) };
      const ds = app.canvas.ds, r = app.canvas.canvas.getBoundingClientRect();
      return { area: arr, visible: b.visible,
               x: r.left + (n.pos[0] + arr[0] + arr[2] / 2 + ds.offset[0]) * ds.scale,
               y: r.top  + (n.pos[1] + arr[1] + arr[3] / 2 + ds.offset[1]) * ds.scale };
    })()`);
    let enteredVia = null, entered = {};
    if (!tbtn.err) {
      await page.mouse.click(tbtn.x, tbtn.y);
      await sleep(2000);
      const s = await page.evaluate(`(${GRAPH_STATE_FN})()`);
      if (!s.isRoot) enteredVia = 'title-button click (the UI affordance)';
    }
    if (!enteredVia) {
      entered = await page.evaluate(`(() => {
        const app = window.app, g = app.rootGraph || app.graph;
        const n = (g.nodes || g._nodes).find(x => x.id === ${opt.faceHost});
        if (!n || !n.subgraph) return { err: 'no subgraph on #${opt.faceHost}' };
        app.canvas.openSubgraph(n.subgraph, n);   // the same call the title button makes
        return { ok: true };
      })()`);
      await sleep(2000);
      enteredVia = `openSubgraph() API — the title-button click did not take (${tbtn.err || 'still at root'})`;
    }
    fp.entered_via = enteredVia;
    const gs = await page.evaluate(`(${GRAPH_STATE_FN})()`);
    fp.inside_subgraph = gs;
    log(`face prompt     entered the subgraph: isRoot=${gs.isRoot}, "${gs.name}", ${gs.nodeCount} nodes, breadcrumb=${JSON.stringify(gs.breadcrumb)}`);
    if (entered.err || gs.isRoot) {
      fail('face-prompt', `could not enter the subgraph on #${opt.faceHost}: ${entered.err || 'still at root'}`);
      writeResult('fail'); await browser.close(); process.exit(1);
    }
    const f106 = await page.evaluate(`(${FRAME_FN})([${opt.faceNode}], 40, 1.0, null, true)`);
    await sleep(2500);
    log(`face prompt     framed #${opt.faceNode} inside the subgraph (scale ${(f106.scale || 0).toFixed(3)})`);

    if (typedInside) {
      // 5a. type on #106's own widget — the current graph IS the subgraph here
      const tagIn = await page.evaluate(`(${TAG_TEXT_WIDGET_FN})(${opt.faceNode}, 'text', 'face-prompt')`);
      if (tagIn.err) {
        await shot(page, 'face-widget-missing', 'no text widget on #' + opt.faceNode + ' inside the subgraph');
        fail('face-prompt', `#${opt.faceNode}: ${tagIn.err}`);
        writeResult('fail'); await browser.close(); process.exit(1);
      }
      fp.shipped_value = tagIn.value;
      log(`face prompt     #${opt.faceNode}'s own "text" widget: ${tagIn.widgetType}, visible=${tagIn.visible}, shipped value ${JSON.stringify(tagIn.value)}`);
      if (!tagIn.visible) {
        fail('face-prompt', `#${opt.faceNode}'s textarea is not visible inside the subgraph; a buyer could not click it`);
        writeResult('fail'); await browser.close(); process.exit(1);
      }
      const fta = page.locator('[data-gate-tag="face-prompt"]');
      await fta.click();
      await page.keyboard.press('Control+a');
      await page.keyboard.press('Delete');
      await page.keyboard.insertText(opt.facePrompt);
      await page.keyboard.press('Tab');
      await sleep(1200);
    }

    // 6. read back from the CLIPTextEncode itself (and the promoted widget when
    //    one exists) — a log line saying "typed" is worth nothing on its own.
    const rb = await page.evaluate(`(${READ_FACE_PROMPT_FN})(${opt.faceHost}, ${opt.faceNode}, 'text')`);
    if (rb.err) { fail('face-prompt', rb.err); writeResult('fail'); await browser.close(); process.exit(1); }
    Object.assign(fp, rb);
    log(`face prompt     read back from #${opt.faceNode} ${rb.inner_node_type} "${rb.inner_node_title}" inside "${rb.subgraph_name}":`);
    log(`                ${JSON.stringify((rb.inner_value || '').slice(0, 80))}...`);
    if (rb.promoted_value !== null) log(`face prompt     promoted widget reads: ${JSON.stringify((rb.promoted_value || '').slice(0, 80))}...`);
    if (rb.inner_value !== opt.facePrompt) {
      await shot(page, 'face-prompt-not-committed', 'typed text did not reach #' + opt.faceNode);
      fail('face-prompt', `#${opt.faceNode}.text reads ${JSON.stringify((rb.inner_value || '').slice(0, 120))} after typing, wanted the requested prompt`);
      writeResult('fail'); await browser.close(); process.exit(1);
    }
    await shot(page, 'face-prompt-on-node-106',
      `#${opt.faceNode} "${rb.inner_node_title}" inside "${gs.name}", carrying: ` +
      JSON.stringify(opt.facePrompt.length > 110 ? opt.facePrompt.slice(0, 110) + '…' : opt.facePrompt));

    // 7. back out the way a buyer does — the breadcrumb
    const crumb = page.locator('.subgraph-breadcrumb .p-breadcrumb-item, .p-breadcrumb-item').first();
    if (await crumb.count()) { await crumb.click().catch(() => {}); await sleep(1800); }
    const back = await page.evaluate(`(${GRAPH_STATE_FN})()`);
    fp.back_at_root = back.isRoot;
    log(`face prompt     back out via the breadcrumb: isRoot=${back.isRoot}`);
    if (!back.isRoot) {
      fail('face-prompt', 'could not get back to the root graph after entering the subgraph');
      writeResult('fail'); await browser.close(); process.exit(1);
    }
    // leave the canvas as it was handed over (respect the SHIPPED collapse state)
    await page.evaluate(`(${COLLAPSE_FN})(${opt.faceHost}, ${fp.host_shipped_collapsed})`);
    await sleep(800);
  } else {
    log(`face prompt     not touched — #${opt.faceNode} keeps the value the workflow ships`);
    result.face_prompt = { requested: null, note: 'left at the shipped placeholder' };
  }

  if (failures.length) { writeResult('fail'); await browser.close(); process.exit(1); }
  if (opt.noRun) {
    await page.evaluate(`(${FRAME_FN})(null, 60, 1.0, null)`);
    await sleep(1800);
    await shot(page, 'ready-to-run-not-submitted',
      'everything set — LoRAs, prompt' + (opt.facePrompt !== null ? ' and the face prompt on #' + opt.faceNode : '') +
      ' — the moment before Run. Nothing was submitted.');
    log('\n--no-run: stopping before the Run button. Nothing was submitted.');
    writeResult('pass-no-run'); await browser.close(); process.exit(0);
  }

  // ============= Run ======================================================
  await page.evaluate(`(${FRAME_FN})(null, 60, 1.0, null)`);
  await sleep(1200);
  const runBtn = page.locator('[data-testid="queue-button"] button.p-splitbutton-button');
  if (!(await runBtn.count())) { fail('run', 'Run button not found'); writeResult('fail'); await browser.close(); process.exit(1); }

  // A selector popup from ANOTHER client's paused render covers this page and eats
  // the click. Wait for it rather than dismissing it — Cancel would abort their render.
  const POPUP = 'instaraw-imgae-filter-popup.instaraw_popup';
  const foreignBlocking = async () => {
    const l = page.locator(`${POPUP}:not(.hidden)`);
    return (await l.count()) > 0 && await l.first().isVisible().catch(() => false);
  };
  const idleDeadline = Date.now() + 600000;
  if (await foreignBlocking()) log('wait            a foreign INSTARAW selector popup covers the page; waiting for it to clear');
  while (Date.now() < idleDeadline && await foreignBlocking()) await sleep(4000);
  if (await foreignBlocking()) {
    await shot(page, 'blocked-by-foreign-popup', 'another client\'s selector popup covers the page');
    fail('blocked', 'a selector popup from another client\'s render covered the page for 10 minutes; Run could not be pressed');
    writeResult('harness-error'); await browser.close(); process.exit(2);
  }

  const label = (await runBtn.first().innerText().catch(() => '')).trim();
  const tRun = Date.now();
  await runBtn.first().click({ timeout: 30000 });
  log(`press Run       the real Run button, label="${label}"`);
  const submitDeadline = Date.now() + 180000;
  while (Date.now() < submitDeadline && promptStatus === null) await sleep(300);
  await sleep(800);

  if (promptStatus === null) {
    await shot(page, 'run-no-post', 'Run pressed, no POST /prompt observed');
    fail('frontend-conversion', 'Run was pressed and no POST /prompt was made within 180 s — the frontend threw during graphToPrompt (this is the shipped-blocker signature)');
    result.page_errors = pageErrors;
    writeResult('fail'); await browser.close(); process.exit(1);
  }
  if (promptStatus !== 200) {
    await shot(page, 'run-rejected', `server refused the prompt: HTTP ${promptStatus}`);
    fail('server-validation', `POST /prompt returned HTTP ${promptStatus}: ${JSON.stringify(promptResponse).slice(0, 1500)}`);
    result.page_errors = pageErrors;
    writeResult('fail'); await browser.close(); process.exit(1);
  }
  const nodeErrors = (promptResponse && promptResponse.node_errors) || {};
  if (Object.keys(nodeErrors).length) {
    await shot(page, 'run-node-errors', 'server accepted with node_errors');
    fail('server-validation', 'node_errors: ' + JSON.stringify(nodeErrors).slice(0, 1500));
    result.page_errors = pageErrors;
    writeResult('fail'); await browser.close(); process.exit(1);
  }
  promptId = promptResponse.prompt_id;
  result.prompt_id = promptId;
  result.timings.submit_ms = Date.now() - tRun;
  try {
    const parsed = JSON.parse(promptBody);
    result.api_graph_nodes = Object.keys(parsed.prompt || {}).length;
    fs.writeFileSync(path.join(opt.out, `${opt.tag}-api_graph.json`), JSON.stringify(parsed.prompt, null, 2));
  } catch { /* keep going */ }
  log(`prompt accepted HTTP 200  prompt_id=${promptId}  api graph ${result.api_graph_nodes} nodes  (${result.timings.submit_ms} ms after the click)`);
  await shot(page, 'run-submitted', `prompt ${promptId} accepted, ${result.api_graph_nodes}-node API graph`);

  // ============= wait for the render, clicking through the selector =======
  const tExec = Date.now();
  const sel = {
    driven: false, appeared: false, images: 0, picked: null,
    send_enabled_on_open: null, send_enabled_after_click: null, send_enabled_after_reclick: null,
    auto_picked_single_image: null,
  };
  result.selector = sel;
  let history = null, lastLog = 0, queueNoted = false, selectorFailed = false;
  const deadline = Date.now() + opt.executeTimeoutMs;

  while (Date.now() < deadline) {
    if (execError || execInterrupted) break;
    let ours = false;
    try {
      const q = await (await fetch(`${opt.url}/queue`)).json();
      ours = (q.queue_running || []).some(it => it[1] === promptId);
      if (!queueNoted) {
        const ahead = (q.queue_running || []).length + (q.queue_pending || []).filter(it => it[1] !== promptId).length;
        if (!ours && ahead) { log(`  queue         waiting behind ${ahead} other render(s) already on this ComfyUI`); queueNoted = true; }
        else if (ours) queueNoted = true;
      }
    } catch { /* transient */ }

    if (ours && !sel.driven) {
      const imgs = page.locator(`${POPUP}:not(.hidden) .grid img`);
      const n = await imgs.count().catch(() => 0);
      if (n && await imgs.first().isVisible().catch(() => false)) {
        sel.appeared = true; sel.images = n;
        const idx = Math.min(Math.max(0, opt.selectorPick), n - 1);
        await shot(page, 'selector-popup', `#603 INSTARAW_ImageFilter paused the render with ${n} image(s) — the buyer must choose`);
        const send = page.locator('button.control:visible').filter({ hasText: /^Send$/ });
        if (!(await send.count())) { fail('selector', 'selector popup appeared with no visible Send button'); selectorFailed = true; break; }
        // CURRENT pack: no auto-pick — the popup opens with nothing selected and
        // Send disabled; one click selects and enables. The reclick branch below
        // only fires against OLD pack builds (which pre-picked a single image so
        // the first click DESELECTED it); keeping it lets this gate drive old
        // bytes too, and send_enabled_on_open records which behavior was seen.
        sel.send_enabled_on_open = await send.first().isEnabled();
        sel.auto_picked_single_image = (n === 1 && sel.send_enabled_on_open === true);
        await imgs.nth(idx).click();
        sel.picked = idx;
        await sleep(500);
        sel.send_enabled_after_click = await send.first().isEnabled();
        if (sel.send_enabled_on_open) {
          // it was auto-picked: the click just turned it off, so turn it back on
          await imgs.nth(idx).click();
          await sleep(500);
          sel.send_enabled_after_reclick = await send.first().isEnabled();
        }
        const enabledNow = sel.send_enabled_on_open ? sel.send_enabled_after_reclick : sel.send_enabled_after_click;
        log(`  selector      ${n} image(s); Send on open=${sel.send_enabled_on_open}, after clicking #${idx}=${sel.send_enabled_after_click}` +
            (sel.send_enabled_on_open ? `, after clicking it again=${sel.send_enabled_after_reclick}` : ''));
        await shot(page, 'selector-image-picked', `image #${idx} of ${n} selected; Send ${enabledNow ? 'enabled' : 'STILL DISABLED'}`);
        if (!enabledNow) {
          fail('selector', `image #${idx} of ${n} is selected and the Send button is still disabled — the buyer cannot proceed`);
          selectorFailed = true; break;
        }
        await send.first().click();
        sel.driven = true;
        log(`  selector      Send pressed at ${Math.round((Date.now() - tExec) / 1000)}s into the render`);
      }
    }

    try {
      const r = await fetch(`${opt.url}/history/${promptId}`);
      if (r.ok) {
        const j = await r.json();
        const h = j && j[promptId];
        if (h && h.status && (h.status.completed === true || h.status.status_str === 'success' || h.status.status_str === 'error')) { history = h; break; }
      }
    } catch { /* transient */ }

    if (Date.now() - lastLog > 60000) {
      lastLog = Date.now();
      const last = wsEvents.filter(e => e.type === 'executing').slice(-1)[0];
      log(`  ...waiting    ${Math.round((Date.now() - tExec) / 1000)}s   ours_running=${ours}  last node: ${last && last.data ? JSON.stringify(last.data.node) : 'none yet'}`);
    }
    await sleep(3000);
  }
  result.timings.execute_ms = Date.now() - tExec;

  if (execError) {
    await shot(page, 'execution-error', 'a node raised mid-render');
    fail('execution', `${execError.node_type} #${execError.node_id}: ${execError.exception_type}: ${execError.exception_message}`);
    result.page_errors = pageErrors; writeResult('fail'); await browser.close(); process.exit(1);
  }
  if (execInterrupted) { fail('execution', 'the render was interrupted'); result.page_errors = pageErrors; writeResult('fail'); await browser.close(); process.exit(1); }
  if (!history && selectorFailed) {
    // The selector failure above is the whole story; the render is still sitting on
    // #603 waiting for an answer this run will not give it. Reporting a timeout on
    // top of it would invent a second, false failure.
    log('  the render is still paused on #603 waiting for a selection this run did not make');
    result.page_errors = pageErrors; writeResult('fail'); await browser.close(); process.exit(1);
  }
  if (!history) { fail('execution-timeout', `the render did not finish within ${opt.executeTimeoutMs} ms`); result.page_errors = pageErrors; writeResult('fail'); await browser.close(); process.exit(1); }
  if (history.status && history.status.status_str === 'error') {
    fail('execution', JSON.stringify(history.status.messages).slice(0, 1500));
    result.page_errors = pageErrors; writeResult('fail'); await browser.close(); process.exit(1);
  }

  const outs = [];
  for (const [nodeId, out] of Object.entries(history.outputs || {})) {
    for (const im of (out.images || [])) {
      const base = im.type === 'output' ? opt.outputDir : path.join(path.dirname(opt.outputDir), im.type || 'output');
      const abs = path.join(base, im.subfolder || '', im.filename);
      outs.push({ ...im, node: nodeId, path: abs, exists: fs.existsSync(abs), size: fs.existsSync(abs) ? fs.statSync(abs).size : null });
    }
  }
  result.outputs = outs;
  log(`render          ${Math.round(result.timings.execute_ms / 1000)}s wall (queue included)`);
  for (const o of outs) log(`  output        ${o.exists ? 'OK  ' : 'MISS'} ${o.path}  ${o.size} B  [node ${o.node}]`);
  if (!outs.length || !outs.some(o => o.exists)) fail('output', 'the render completed but produced no image file on disk');

  // ============= the finished image on screen =============================
  await sleep(3000);
  await shot(page, 'render-complete', 'the moment the render finished, as the buyer sees it');

  // the SaveImage node carries the finished picture; frame it large
  await page.evaluate(`(${FRAME_FN})([505], 30, 1.0, null)`);
  await sleep(2500);
  await shot(page, 'final-image-on-canvas', 'the finished image on #505 "YOUR IMAGE — saved to output/Instaraw/"');

  // and the image feed / gallery, which is where a buyer looks first
  const feedImg = page.locator('.comfyui-image-feed img, [class*="image-feed"] img').first();
  if (await feedImg.count()) {
    await feedImg.scrollIntoViewIfNeeded().catch(() => {});
    await sleep(800);
    await shot(page, 'final-image-feed', 'the finished image in the ComfyUI image feed');
  }

  result.page_errors = pageErrors;
  const lateErrors = pageErrors.slice(bootErrCount);
  log(`page errors     ${bootErrCount} during boot, ${lateErrors.length} after the workflow was opened`);
  for (const e of lateErrors.slice(0, 12)) log(`                  ${e.text.split('\n')[0].slice(0, 160)}`);

  writeResult(failures.length ? 'fail' : 'pass');
  log(`\nRESULT: ${failures.length ? 'FAIL' : 'PASS'}`);
  await browser.close();
  process.exit(failures.length ? 1 : 0);
}

main().catch(async (e) => {
  log(`gate: unexpected failure: ${(e && e.stack) || e}`);
  try { writeResult('harness-error'); } catch { /* ignore */ }
  if (browser) await browser.close().catch(() => {});
  process.exit(2);
});
