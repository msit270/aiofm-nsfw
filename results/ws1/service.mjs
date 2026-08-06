// Attach to an already-queued prompt: load the workflow (so the INSTARAW popup
// can find its node), service the image-filter pause, and wait for the result.
// Usage: node service.mjs <wfName> <promptId> <tag> [maxMinutes]
import { chromium } from '/workspace/nsfw-fix/node_modules/playwright/index.mjs'
import fs from 'node:fs'

const OUT = '/tmp/claude-0/-workspace-nsfw-fix/47375d2b-87bd-4073-a1e2-67796f8c1345/scratchpad/ws1'
const [WF, PID, TAG, MM] = [process.argv[2], process.argv[3], process.argv[4] || 'service', Number(process.argv[5] || 35)]
const events = []
const log = (k, t) => { const l = `[${new Date().toISOString().slice(11,19)}][${k}] ${t}`; console.log(l); events.push(l) }

const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] })
const page = await (await browser.newContext({ viewport: { width: 1920, height: 1200 } })).newPage()
page.on('pageerror', e => log('pageerror', e.message))
page.on('console', m => {
  const t = m.text()
  if (m.type() !== 'error') return
  if (/detailsElement|Failed to load resource|preloadError|already registered/.test(t)) return
  log('console.error', t.slice(0, 400))
})

await page.goto('http://127.0.0.1:18188', { waitUntil: 'domcontentloaded' })
await page.waitForFunction(() => window.app?.graph, null, { timeout: 120000 })
await page.waitForTimeout(8000)
await page.click('button[aria-label="Workflows (w)"]')
await page.waitForTimeout(2500)
await page.locator(`text=${WF}`).first().click()
await page.waitForTimeout(20000)
await page.click('button[aria-label="Workflows (w)"]').catch(() => {})
log('info', `loaded ${WF}, servicing prompt ${PID}`)

const deadline = Date.now() + MM * 60_000
let done = null, sends = 0
while (Date.now() < deadline) {
  await page.waitForTimeout(5000)
  const sent = await page.evaluate(() => {
    const p = document.querySelector('instaraw-imgae-filter-popup')
    if (!p || p.offsetParent === null) return null
    // The popup's buttons live in a sibling floating window, NOT inside the
    // custom element, so this must search the document, not `p`.
    const findSend = () => [...document.querySelectorAll('button.control')]
      .find(b => b.innerText.trim() === 'Send' && !b.disabled && b.offsetParent !== null)
    let send = findSend()
    if (!send) {
      const imgs = [...p.querySelectorAll('img')].filter(i => i.image_index !== undefined)
      if (!imgs.length) return `popup-up-no-images(picked=${p.picked?.size})`
      if (p.picked && p.picked.size === 0) p.picked.add(String(imgs[0].image_index ?? 0))
      p.render()
      send = findSend()
      if (!send) return `send-still-disabled(n=${imgs.length},picked=${p.picked?.size})`
      send.click()
      return `picked-${p.picked.size}-of-${imgs.length}-clicked-send(node=${p.node?.id})`
    }
    send.click()
    return 'clicked-send'
  })
  if (sent && (sent === 'clicked-send' || sent.startsWith('picked-'))) {
    sends++; log('filter', `serviced popup #${sends}: ${sent}`)
    await page.screenshot({ path: `${OUT}/${TAG}-filter-${sends}.png` })
  } else if (sent) log('filter', sent)

  const st = await page.evaluate(async (pid) => {
    const q = await (await fetch('/api/queue')).json()
    const h = await (await fetch('/api/history')).json()
    const e = h[pid]
    return {
      running: q.queue_running?.length ?? 0, pending: q.queue_pending?.length ?? 0,
      status: e?.status?.status_str ?? null,
      messages: e ? JSON.stringify(e.status?.messages ?? []).slice(0, 1500) : null,
      outputs: e ? Object.entries(e.outputs || {}).filter(([, v]) => v.images)
        .map(([k, v]) => [k, v.images.map(i => `${i.subfolder}/${i.filename}`)]) : null
    }
  }, PID)
  if (st.status) { done = st; log('history', JSON.stringify(st)); break }
  log('poll', `running=${st.running} pending=${st.pending}`)
}
await page.screenshot({ path: `${OUT}/${TAG}-final.png` })
log('RESULT', !done ? 'TIMED OUT' : (done.status === 'success' ? `SUCCESS outputs=${JSON.stringify(done.outputs)}` : `FAILED ${done.status} ${done.messages}`))
fs.writeFileSync(`${OUT}/${TAG}-events.log`, events.join('\n') + '\n')
await browser.close()
