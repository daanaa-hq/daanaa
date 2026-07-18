# Skill: Daanaa App Feature Playbook

**Mission:** Every app feature serves one loop — find fast, give in a tap, log it, come back. Build to the Luckin bar (instant, reliable, repeat-friendly) without ever crossing the stewardship lines.

## When to invoke

Use `/app-feature` when building or changing anything in the donor-facing app experience: wallet, search, giving flows, PWA shell, notifications, offline behavior.

## The return loop (priority order — build/fix in this order)

1. **Find** — search in under a second; offline directory when it lands
2. **Give** — org's own verified donate link, or EIN + mailing address for checks. NEVER a third-party donation processor; Daanaa never touches money (P8)
3. **Log** — one-tap gift log (`logDonation`), the emotional close
4. **Rhythm** — recurring templates (`RecurringTemplate`, `isTemplateDue`) power "give again" nudges
5. **Return** — nudges, at most 1 notification/day, always snoozable

**The bar:** repeat gift = 2 taps under 10 seconds; first gift = under a minute.

## Architecture map (don't rediscover)

| Piece | Where | Notes |
|---|---|---|
| Wallet state | `frontend/src/contexts/WalletContext.tsx` | reducer + localStorage + optional encrypted sync |
| Wallet types + due logic | `frontend/src/types/wallet.ts` | `isTemplateDue` is test-locked (`__tests__/givingRhythm.test.ts`) |
| Rhythm UI | `frontend/src/components/GivingRhythm.tsx` | RhythmNudges (due strip) + RhythmControl (per-org) |
| App posture | `frontend/src/hooks/useStandalone.ts` + `Layout.tsx` | installed app hides Footer; BottomNav is the nav |
| 3-tab bottom bar | `frontend/src/components/BottomNav.tsx` | Home / Search / Wallet, `md:hidden` |
| Install nudge | `frontend/src/components/InstallPrompt.tsx` | only after first save; one dismissal is permanent |
| Offline cache | `frontend/public/sw.js` | bump CACHE_NAME on behavior change; org data network-first w/ fallback; everything else network-only |
| Donate link gating | `frontend/src/utils/actionRow.ts` | only `beta`/`claimed` donate statuses render |

## Non-negotiables (each feature checked against these)

- **Device-first privacy (P2):** wallet data, reminders, and due-ness computations stay on-device. No reminder/schedule data to any server. Google sign-in is optional backup only.
- **No pressure (P5):** nudges are warm, snoozable, and shame-free. One dismissal of an install/notification prompt is permanent. Max 1 push/day, curator-triggered.
- **Evidence-based links (P3):** donate links render only with `donate_url_status` in (`beta`,`claimed`); website fallback only `website_status === 'ok'` (or NULL-unchecked, flagged beta). When offline-cached, re-verify on next online tap.
- **No ranking by default (P4/2026-07-04):** default sort is neutral name order; score/revenue sorts are explicit opt-in.
- **Copy voice:** no dashes, no jargon, no shame framing. Terminology lint runs in `tests/test_contract_and_terminology.py`.

## Definition of done for an app feature

1. Jest test for any logic that decides WHEN to show something to a donor (nudge timing, gating) — a wrong answer either nags or forgets
2. `npm run build` clean + full jest suite green (`npx jest`)
3. Works in both postures: browser tab (full site) and standalone (slim shell)
4. Ship via `/daanaa-deploy` routing (usually `--code-only`), then live-verify behavior
5. Founder phone-check for UX changes; DECISIONS/LESSONS entries for non-obvious calls
