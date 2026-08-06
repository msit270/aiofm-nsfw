// Load N saved workflows in ONE browser session and dump each one's API graph,
// without pressing Run (so nothing mutates seeds / control_after_generate).
// Usage: node dump_api.mjs <wfName>:<outTag> [<wfName>:<outTag> ...]
import { chromium } from '/workspace/nsfw-fix/node_modules/playwright/index.mjs'
import fs from 'node:fs'

const OUT = '/tmp/claude-0/-workspace-nsfw-fix/47375d2b-87bd-4073-a1e2-67796f8c1345/scratchpad/ws1'
const jobs = process.argv.slice(2).map(a => { const [wf, tag] = a.split(':'); return { wf, tag: tag || wf } })

const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] })
const page = await (await browser.newContext({ viewport: { width: 1920, height: 1200 } })).newPage()
page.on('pageerror', e => console.log('[pageerror]', e.message))

await page.goto('http://127.0.0.1:18188', { waitUntil: 'domcontentloaded' })
await page.waitForFunction(() => window.app?.graph, null, { timeout: 120000 })
await page.waitForTimeout(8000)

for (const { wf, tag } of jobs) {
  await page.click('button[aria-label="Workflows (w)"]')
  await page.waitForTimeout(2000)
  const item = page.locator(`text=${wf}`).first()
  await item.waitFor({ timeout: 30000 })
  await item.click()
  await page.waitForTimeout(18000)
  await page.click('button[aria-label="Workflows (w)"]').catch(() => {})
  await page.waitForTimeout(1500)

  const r = await page.evaluate(async () => {
    try {
      const p = await window.app.graphToPrompt()
      return { ok: true, output: p.output }
    } catch (e) { return { ok: false, message: String(e?.message), stack: String(e?.stack).slice(0, 3000) } }
  })
  if (r.ok) {
    fs.writeFileSync(`${OUT}/${tag}-api.json`, JSON.stringify(r.output, null, 2))
    console.log(`[${wf}] OK -> ${tag}-api.json  (${Object.keys(r.output).length} nodes)`)
  } else {
    console.log(`[${wf}] THREW ${r.message}\n${r.stack}`)
  }
}
await browser.close()
