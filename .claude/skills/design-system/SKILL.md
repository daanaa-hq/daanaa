# Skill: Daanaa Design System

**Mission:** Every surface reads from one source of truth. Daanaa should feel like
trusted public infrastructure that has existed for years, not a product assembled
one page at a time.

## When to invoke

Use `/design-system` when building or changing anything visual: a new page, a new
component, a consistency pass, a theme fix, or a typography decision. Invoke it
*before* writing markup, not after.

## The single source of truth

`frontend/public/tokens.css` holds the type scale, palette, and font families. It is
served statically so **every** surface reads it, not just the React app:

| Surface | How it reads tokens |
|---|---|
| React app | `frontend/index.html` links it; Tailwind's `fontSize` references it via `var()` |
| `open-data.html` | links `/tokens.css` directly, uses `var(--text-*)` |
| Any new standalone or generated page | must link `/tokens.css` |

Tailwind declares each size as `var(--text-body, 14px)`. The px fallback means a
failure to load tokens.css degrades to the correct size rather than collapsing
every text element. Keep that pattern when adding tokens.

## Type scale

| Token | Size | Use |
|---|---|---|
| `text-micro` | 10 | legal footnotes, dense metadata |
| `text-label` | 11 | uppercase eyebrow labels, tags |
| `text-caption` | 12 | captions, breadcrumbs, secondary metadata |
| `text-small` | 13 | supporting copy, card body |
| `text-body` | 14 | default body text |
| `text-body-lg` | 15 | primary reading copy on guide pages |
| `text-lead` | 16 | intro paragraphs |
| `text-title-sm` | 18 | card titles, subsection headings |
| `text-title` | 20 | section headings |
| `text-title-lg` | 24 | page section headings |
| `text-headline` | 28 | major headings |
| `text-headline-lg` | 32 | page headings |
| `text-display` | 40 | hero numerals and display figures |

For page titles that should scale with viewport, prefer the `h1-display` /
`h2-display` / `h3-display` utilities in `src/index.css` over a fixed token.

**Never write `text-[Npx]` or `font-size: Npx`.** That is exactly how 2,038
hand-rolled sizes across 24 distinct values accumulated before the scale existed.
`design-lint` check 5 fails the build on both.

## Layout spacing

General spacing uses **Tailwind's default scale** (`p-4`, `mb-6`, `gap-5`). It does
not need custom tokens and already has 99.1% adoption. Do not "systematize" it.

Four layout tokens exist, because the nav height was a magic number copied into 37
files:

| Token | Value | Use |
|---|---|---|
| `h-nav` | 72px | the Navigation bar's own height |
| `pt-nav` | 72px | top padding so content clears the fixed nav |
| `pt-nav-lg` | 108px | nav clearance on tall hero sections |
| `scroll-mt-anchor` | 88px | scroll-margin so `#anchors` clear the nav |

Never write `pt-[72px]`, `h-[72px]`, or `scroll-mt-[88px]`. Check 6 fails on them.

Arbitrary spacing for genuine optical corrections (negative margins to align an
icon, 3px padding inside a badge) is fine and expected. The 4px scale is too coarse
for those.

## Rules

1. **Tokens over values.** No raw px for text size, no raw Tailwind palette colors
   (`bg-red-600` → `bg-destructive`). If a token is missing, add it to tokens.css
   rather than working around it.
2. **Line height stays with the element.** Tokens are size-only, so adopting one
   never changes vertical rhythm. Keep using `leading-[...]`.
3. **No decorative emoji** in UI copy. Check 3 enforces it. Emoji read as informal
   and undercut the institutional voice.
4. **Both themes, deliberately.** Check every new component in light and dark. Do
   not rely on automatic inversion.
5. **Reuse before inventing.** 54 components exist in `src/components/ui/`. Check
   there before writing a new variant.
6. **Copy voice.** No dashes, no jargon, no shame framing. Errors explain what to do
   next in plain language.

## Before shipping any visual change

```bash
cd frontend
npm run design-lint     # all 5 checks, including type scale across every surface
npm run build           # must be clean
npx jest                # 225 tests
```

Then verify in both themes and at mobile width. A change that only looks right in
one theme is not done.

## Known debt (as of 2026-07-26)

Honest list, so it stays visible rather than rediscovered:

- **Raw Tailwind colors** in `profile-contexts/PendingInvitations.tsx`,
  `profile-contexts/ContextCreator.tsx`, `DataContextNote.tsx`. Pre-existing,
  flagged by check 1.
- ~~Spacing has no scale.~~ **Corrected 2026-07-26 — this was wrong.** Measurement
  showed 6,816 of 6,879 spacing utilities (99.1%) already sit on Tailwind's
  default scale. Spacing never needed the typography treatment. The real defect
  was narrower: the nav height was a magic number copied into 37 files as
  `pt-[72px]`, so changing the nav would have slid content under the header
  everywhere. Fixed with `pt-nav` / `pt-nav-lg` / `scroll-mt-anchor` / `h-nav`
  tokens, guarded by check 6. The 17 remaining arbitrary values are single-use
  optical corrections (negative margins for icon alignment, 3–4px micro-padding)
  where the 4px scale is too coarse; forcing them onto it would make the UI
  worse. Leave them.
- **Org detail lists seven giving methods as flat links.** At the edge of
  scannable. Grouping or progressive disclosure would serve the north star
  ("make giving easy") better than seven equal-weight options.
- **Themes are 60 override blocks** in `index.css` rather than a designed pair.
  Functional, not yet intentional.

## Stewardship check

Anything that ranks orgs, shapes the ask, or nudges a user must pass
`STEWARDSHIP.md` and `PRIVACY-INVARIANTS.md`. In design terms: no dark patterns, no
pressure, no implied tracking, and small orgs presented with the same visual dignity
as large ones.
