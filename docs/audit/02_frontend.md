# PHASE 2 — Frontend + UX + Accessibility (frontend/src, 146 files) — 2026-06-09

## Verdict: honest tier labeling ✔, no XSS/mixed-content, but the fetch layer has no
## timeout and fused-search errors are silently swallowed — bad combo with droplet slowness.

## What's clean (verified)
- **XSS:** single `dangerouslySetInnerHTML` at `components/ui/chart.tsx:83` — shadcn's
  standard CSS-variable injection (theme colors, not user data). No innerHTML/eval anywhere.
- **Mixed content:** zero `http://` references outside localhost/LAN dev origins.
- **Tier-label honesty (stewardship principle 3):** `FinancialContext.tsx` renders
  human-readable labels ("Data Under Verification" / "Healthy Financial Position" /
  "Financially Strained") — never raw enum codes — plus a confidence badge, explanation
  paragraph, and "Data quality flags" list. ✔ This is the honesty bar the audit was
  checking for, and it passes.
- **Search UX:** debounce implemented (`Directory.tsx:186-206`); loading states across 8+
  pages; `TrustBadge.tsx` deliberately pinned to peer_percentile to match published
  methodology (good provenance comment at :13-15).
- **Keyboard nav:** OrgCard is a native `<Link>` (focusable/enter-activates); viewport
  meta correct; Tailwind responsive classes used throughout.
- **Giving List removal:** routes properly commented out in `App.tsx:64-66`; page files
  remain as dead code (cleanup only).

## Findings

### HIGH
1. **No fetch timeout anywhere** — `data/api.ts` (394 lines, all API calls). No
   AbortController/AbortSignal.timeout on any fetch. With known droplet slowness, a slow
   :5000 leaves the UI in a loading state for the browser default (minutes). Fix: add
   `signal: AbortSignal.timeout(10_000)` in the shared fetch helper + catch → error state.

### MED
2. **Fused-search errors silently swallowed** — `pages/Directory.tsx:250,349`. The fused
   (semantic+keyword) query destructures only `{data, loading}` — error never captured —
   and `:349` hardcodes `activeError = null` in fused mode. If semantic search fails, the
   user sees an empty/idle state with no message. Fix: capture and surface the error like
   the filtered path does (error UI already exists at :796).

### LOW
3. **Accessibility density is thin** — 57 `aria-` attributes and 14 `alt=` across 146
   files. Interactive elements are mostly semantic (`<Link>`, `<button>`), which carries
   the basics, but icon-only buttons and the filter sheet warrant a proper pass. Fix:
   targeted audit of FilterSheet, CompareBar, icon buttons.
4. **Dead Giving List pages** — `pages/GivingListPage.tsx`, `GivingReview.tsx`,
   `GivingConfirmation.tsx` unreferenced since feature removal — delete or move to archive/.

## Cross-phase note
Finding 1 + 2 together explain the "site hangs blank when droplet is slow" symptom —
flagged as primary UX-resilience fix; pairs with Phase 4 (server-side cause).
