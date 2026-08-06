// WS1 browser repro / verification harness.
// Usage: node run.mjs <tag> [--wait-seconds N]
// Loads the saved workflow OFMTech_NSFW the way a buyer does (Workflows sidebar -> click),
// presses Run, and captures every frontend error surface.
import { chromium } from '/workspace/nsfw-fix/node_modules/playwright/index.mjs'
import fs from 'node:fs'

const OUT = '/tmp/claude-0/-workspace-nsfw-fix/47375d2b-87bd-4073-a1e2-67796f8c1345/scratchpad/ws1'
const URLBASE = 'http://127.0.0.1:18188'
const TAG = process.argv[2] || 'run'
const WAIT = Number((process.argv.find(a => a.startsWith('--wait=')) || '--wait=45').split('=')[1])
const WFNAME = (process.argv.find(a => a.startsWith('--wf=')) || '--wf=OFMTech_NSFW').split('=')[1]
const DUMP_API = process.argv.includes('--dump-api')

const events = []
const log = (kind, text) => { const line = `[${kind}] ${text}`; console.log(line); events.push(line) }

const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] })
const ctx = await browser.newContext({ viewport: { width: 1920, height: 1200 } })
const page = await ctx.newPage()

page.on('pageerror', e => log('pageerror', e.stack || e.message))
page.on('console', m => { if (m.type() === 'error') log('console.error', m.text()) })
page.on('requestfailed', r => log('requestfailed', `${r.method()} ${r.url()} :: ${r.failure()?.errorText}`))
page.on('request', r => { if (r.url().includes('/api/prompt') || r.url().endsWith('/prompt')) log('POST', `${r.method()} ${r.url()}`) })
page.on('response', async r => {
  if ((r.url().includes('/api/prompt') || r.url().endsWith('/prompt')) && r.request().method() === 'POST') {
    let body = ''
    try { body = (await r.text()).slice(0, 2000) } catch {}
    log('prompt-response', `status=${r.status()} body=${body}`)
  }
})

await page.goto(URLBASE, { waitUntil: 'domcontentloaded' })
await page.waitForFunction(() => window.app?.graph, null, { timeout: 120000 })
await page.waitForTimeout(8000)

// Install an unhandled-rejection hook in the page
await page.evaluate(() => {
  window.__ws1 = { rejections: [] }
  window.addEventListener('unhandledrejection', e => {
    window.__ws1.rejections.push(String(e.reason?.stack || e.reason))
  })
})

// --- open workflow via the Workflows sidebar, as a buyer would ---
await page.click('button[aria-label="Workflows (w)"]')
await page.waitForTimeout(2500)
await page.screenshot({ path: `${OUT}/${TAG}-sidebar.png` })

const item = page.locator(`text=${WFNAME}`).first()
await item.waitFor({ timeout: 30000 })
await item.click()
log('info', `clicked workflow ${WFNAME}`)
await page.waitForTimeout(20000)
await page.screenshot({ path: `${OUT}/${TAG}-loaded.png` })

const loaded = await page.evaluate(() => ({
  activeName: window.app?.extensionManager?.workflow?.activeWorkflow?.filename
    ?? window.app?.workflowManager?.activeWorkflow?.name ?? null,
  rootNodes: window.app?.graph?._nodes?.length ?? null,
  nodeIds: (window.app?.graph?._nodes ?? []).map(n => n.id),
  subgraphDefs: window.app?.graph?.subgraphs ? [...window.app.graph.subgraphs.keys()].length : null
}))
log('info', 'loaded=' + JSON.stringify(loaded))

// close sidebar so it does not cover the canvas
await page.click('button[aria-label="Workflows (w)"]').catch(() => {})
await page.waitForTimeout(1000)

// --- press Run, exactly as a buyer would ---
await page.click('button[aria-label="Run"]')
log('info', 'clicked Run')
await page.waitForTimeout(WAIT * 1000)
await page.screenshot({ path: `${OUT}/${TAG}-afterrun.png`, fullPage: false })

// scrape any toast / error dialog text
const surfaced = await page.evaluate(() => {
  const texts = []
  for (const sel of ['.p-toast', '.p-toast-message', '.p-dialog', '[role="alertdialog"]', '.comfy-error-report', '.p-toast-detail', '.p-toast-summary']) {
    for (const el of document.querySelectorAll(sel)) {
      const t = (el.innerText || '').trim()
      if (t) texts.push(`${sel} :: ${t}`)
    }
  }
  return { texts: [...new Set(texts)], rejections: window.__ws1?.rejections ?? [] }
})
for (const t of surfaced.texts) log('toast/dialog', t)
for (const r of surfaced.rejections) log('unhandledrejection', r)

// --- direct probe: run the UI->API conversion ourselves and report the exception ---
const conv = await page.evaluate(async () => {
  try {
    const p = await window.app.graphToPrompt()
    return { ok: true, nodeCount: Object.keys(p.output).length, output: p.output }
  } catch (e) {
    return { ok: false, name: e?.constructor?.name, message: String(e?.message), stack: String(e?.stack).slice(0, 4000) }
  }
})
if (conv.ok) {
  log('graphToPrompt', `OK, ${conv.nodeCount} API nodes`)
  if (DUMP_API) {
    fs.writeFileSync(`${OUT}/${TAG}-api.json`, JSON.stringify(conv.output, null, 2))
    log('graphToPrompt', `wrote ${OUT}/${TAG}-api.json`)
  }
} else {
  log('graphToPrompt', `THREW ${conv.name}: ${conv.message}`)
  log('graphToPrompt-stack', conv.stack)
}

// queue state
const q = await page.evaluate(async () => {
  const r = await fetch('/api/queue'); const j = await r.json()
  const h = await (await fetch('/api/history')).json()
  return { running: j.queue_running?.length ?? 0, pending: j.queue_pending?.length ?? 0, history: Object.keys(h).length }
})
log('queue', JSON.stringify(q))

fs.writeFileSync(`${OUT}/${TAG}-events.log`, events.join('\n') + '\n')
console.log(`\n--- wrote ${OUT}/${TAG}-events.log ---`)
await browser.close()
