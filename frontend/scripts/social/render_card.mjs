// Branded card / OG image renderer (Satori -> SVG -> PNG, no headless browser).
// Reusable for the "Overlooked" social posts and for OG images.
// CLI: node scripts/social/render_card.mjs '{"label":"THE OVERLOOKED","name":"Org","tier":"Torch","location":"City, ST","cause":"Youth Development"}' out.png
import fs from 'node:fs'
import satori from 'satori'
import { Resvg } from '@resvg/resvg-js'

const FONTS = [
  { name: 'Display', path: '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf', weight: 700, style: 'italic' },
  { name: 'Body',    path: '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',                 weight: 400, style: 'normal' },
  { name: 'BodyBold',path: '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',            weight: 700, style: 'normal' },
]

const NAVY = '#0A1628'
const CREAM = '#F5F0EB'
const GOLD = '#C9A96E'
const MUTED = '#A7AEBB'

const el = (type, style, children) => ({ type, props: { style, ...(children !== undefined ? { children } : {}) } })

export async function renderCardPng({ label = 'THE OVERLOOKED', name, tier = '', location = '', cause = '' }) {
  const fonts = FONTS.map(f => ({ name: f.name, data: fs.readFileSync(f.path), weight: f.weight, style: f.style }))
  const metaBits = [tier && `${tier}`, location, cause].filter(Boolean).join('   ·   ')

  const tree = el('div', {
    display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
    width: '1200px', height: '630px', backgroundColor: NAVY, padding: '72px 80px',
    fontFamily: 'Body',
  }, [
    // top: gold label
    el('div', { display: 'flex', alignItems: 'center', color: GOLD, fontSize: '26px', fontFamily: 'BodyBold', letterSpacing: '4px', textTransform: 'uppercase' }, `✦  ${label}  ·  daanaa`),
    // middle: org name (serif italic)
    el('div', { display: 'flex', color: CREAM, fontSize: '64px', fontFamily: 'Display', fontStyle: 'italic', lineHeight: 1.1, maxWidth: '1040px' }, name),
    // bottom: meta + footer
    el('div', { display: 'flex', flexDirection: 'column' }, [
      el('div', { display: 'flex', width: '120px', height: '4px', backgroundColor: GOLD, marginBottom: '24px' }),
      el('div', { display: 'flex', color: MUTED, fontSize: '30px' }, metaBits),
      el('div', { display: 'flex', justifyContent: 'space-between', marginTop: '20px', color: MUTED, fontSize: '24px' }, [
        el('div', { display: 'flex' }, 'See the overlooked. Give with heart.'),
        el('div', { display: 'flex', color: GOLD, fontFamily: 'BodyBold' }, 'daanaa.org'),
      ]),
    ]),
  ])

  const svg = await satori(tree, { width: 1200, height: 630, fonts })
  return new Resvg(svg, { fitTo: { mode: 'width', value: 1200 } }).render().asPng()
}

// CLI
if (import.meta.url === `file://${process.argv[1]}`) {
  const data = JSON.parse(process.argv[2] || '{}')
  const out = process.argv[3] || 'card.png'
  const png = await renderCardPng(data)
  fs.mkdirSync(out.split('/').slice(0, -1).join('/') || '.', { recursive: true })
  fs.writeFileSync(out, png)
  console.log(`wrote ${out} (${png.length} bytes)`)
}
