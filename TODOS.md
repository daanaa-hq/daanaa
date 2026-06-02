# TODOS.md

Deferred work, written down so it's real (operating agreement: vague intentions are
lies). Each item: what, why, and enough context to pick it up cold. Priority: P1 blocks
launch, P2 soon, P3 someday.

---

## Action layer — giving (the "information without action" thesis)

### P1 — G1 attorney review (the real gate)
Public "Give here" CTAs may count as soliciting donations → charitable-solicitation
registration in ~40 states. The give-path build is a two-way door; **public launch is
gated here.** Blocked on lawyer funds (~$300–500). Until then, build behind a flag, don't
promote. Context: `meritgiving-ops/partnerships/everydotorg-brief.md`, `LAUNCH-CHECKLIST.md` G1.

### P1 — G2 IRS auto-revocation filter
Suppress / clearly badge give paths for orgs on the IRS auto-revocation list. Routing a
gift to a revoked org is real harm + liability. Must be live before any give CTA. Pair
with Every.org's verified donate-ready status data. Context: `LAUNCH-CHECKLIST.md` G2.

### P2 — EIN-router fallback give-path (behind a feature flag)
Routing policy: org's own verified donate link first → Every.org EIN deep link (zero fee)
→ PayPal Giving Fund (dormant/unbankable orgs, check by mail). Build behind a flag, not
user-visible until G1 + G2 clear. Reuses the existing `donate_url` / `donate_confidence`
pipeline. Deferred per founder's "open Every.org partnership first" choice 2026-06-01.

### P2 — Every.org partnership
Outreach drafted, ready to send from `partners@daanaa.org`
(`meritgiving-ops/partnerships/everydotorg-brief.md`). Confirm contact address, send,
secure: Charity API access, verified-status data, zero-fee + for-profit-use terms.

### P3 — PayPal Giving Fund fallback
Secondary rail for truly dormant orgs (no bank, may never enroll) — PPGF mails a check
within ~75–90 days. Lower priority; Every.org covers the reachable majority first.

---

## Trust & brand

### P2 — Partnership logos (build when the first partner signs)
**Honesty guardrail (Stewardship): a logo only renders once that partner is genuinely on
board. No logo before a signed deal — that would be a fake trust signal.**
Data-driven so it's structurally impossible to show an unconfirmed partner:
- A `frontend/src/data/partners.ts` config: `{ name, logoUrl, url, role, status: 'live' | 'pending' }`.
- A `<GivingPartners>` strip that renders ONLY `status: 'live'` entries; renders nothing
  when there are none.
- Two placements: (1) on the give path — "Routed via [logo], 100% to the nonprofit"
  (functional + often required attribution); (2) a quiet "Giving partners" strip on About
  (and maybe Home).
Trigger to build: the moment Every.org (or any partner) is confirmed. ~10-minute add then.
Do NOT build the empty component now (YAGNI — no caller yet).

---

## Ops / launch (see LAUNCH-CHECKLIST.md for the full gate list)
- P2 — Minova disclosure + written consent before any public/LinkedIn announcement (task #20).
- P3 — Cloudflare SSL Full(strict) + origin cert before heavy launch (currently Flexible for beta).
- P3 — DKIM record for daanaa.org (Google Workspace → Authenticate email).
