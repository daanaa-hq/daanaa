// One-off accessibility scan: runs axe-core (WCAG 2 A/AA) against key live pages.
// Usage: node scripts/a11y_scan.mjs [baseUrl]
import { chromium } from 'playwright'
import AxeBuilder from '@axe-core/playwright'

const BASE = process.argv[2] || 'https://daanaa.org'
const PATHS = ['/', '/directory', '/org/530196605', '/how-it-works', '/research']

const browser = await chromium.launch()
const ctx = await browser.newContext()
const page = await ctx.newPage()

for (const p of PATHS) {
  const url = BASE + p
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 45000 })
    await page.waitForTimeout(1500) // let the SPA settle
    const res = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()
    const v = res.violations
    console.log(`\n=== ${p} — ${v.length} violation types ===`)
    for (const x of v) {
      console.log(`  [${x.impact}] ${x.id}: ${x.help} (${x.nodes.length} node${x.nodes.length > 1 ? 's' : ''})`)
      console.log(`      e.g. ${(x.nodes[0]?.target || []).join(' ')}`)
    }
  } catch (e) {
    console.log(`\n=== ${p} — scan error: ${e.message} ===`)
  }
}

await browser.close()
