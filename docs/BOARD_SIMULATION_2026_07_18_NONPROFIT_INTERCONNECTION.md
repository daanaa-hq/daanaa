# Board Simulation — 2026-07-18: Org Profile Edit Latency

**Trigger:** Building the "interconnected spine" for the nonprofit dashboard.
Founder's goal (2026-07-18): "org edits → donor pages same day." Investigation
found the gap is worse than same-day — there is no live-push path at all, and
the one piece of code that looks like it (`merge_claims` reading `CLAIMS_DIR`)
is dead: nothing writes to that directory. A mission or donate-link edit sits
invisible on the public page until the next full precompute deploy.

## Gate 1 — Principles Check

- **P3 (evidence-based, honestly stated):** violated today in a quiet way —
  the claim-edit UI implies "saved" without disclosing that the *public* page
  won't reflect it for hours. Nothing false is stated, but nothing true is
  disclosed either. That's a gap, not a violation, but it must close.
- **P9 (explainable):** the current dead `CLAIMS_DIR` mechanism is exactly the
  kind of undocumented architectural drift P9 exists to prevent. It looks like
  a working feature in the code and isn't.
- **P4 (small orgs deserve equal, working tools):** a small org's only lever
  to fix their own page is this edit flow. If it silently doesn't work for a
  day, that disproportionately hurts orgs with no other way to reach donors.
- No option considered here violates a principle outright — this gate
  eliminates nothing, but raises the bar: any fix must be honest about timing
  even if it can't be instant.

## Gate 2 — Data Validation

Confirmed by direct code read (not assumption):
- `daanaa_api.py:3955` `claim_profile_update` writes `custom_mission`,
  `donate_confirmed` straight to `registry_enriched` on the **live local DB**.
- `scripts/droplet_api.py:15` (module docstring) + architecture doc: the
  public droplet serves **precompute static files only**, generated from a
  DB snapshot at deploy time. It does not read `registry_enriched` live.
- `scripts/droplet_api.py:653-665` `merge_claims()` reads `CLAIMS_DIR/{ein}.json`.
  `grep -rn "CLAIMS_DIR"` across the repo shows exactly one read site and
  **zero write sites**. Confirmed dead code.
- Full deploy cadence: nightly cron 02:30, or manual (~2-4h runtime observed
  tonight). Worst case an edit is invisible for just under 24h.

## Gate 3 — Board Simulation

| Seat | Position |
|---|---|
| **Legal** | No liability exposure — nothing false is being told to donors or orgs. Recommend disclosure language be precise ("within 24 hours," not "instantly") so it's a promise we keep. |
| **Accounting/Finance** | No financial-integrity angle here; data honesty (mission/link text) isn't a financial signal. Neutral. |
| **Marketing** | Strong opinion: a nonprofit who edits their page and sees nothing change will assume Daanaa is broken or ignoring them — this is a churn risk for the exact organizations we most need engaged (the pilot). Wants the real-time fix, not just messaging. |
| **ED (nonprofit leaders)** | This is the single most concrete thing that would build trust with a skeptical small-org director: "I fixed my typo and it showed up." Ranks this above almost any other dashboard feature discussed tonight. Supports building the real fix if it can be done safely. |
| **Donor group** | Mild interest — donors benefit from accurate org pages, but don't know or care about the mechanism. Low priority from this seat alone. |
| **Stewardship chair** | Two-step call: (1) ship the honest-timing disclosure NOW — it's small, safe, and closes the P3 gap immediately. (2) Do NOT rush a live-push production-write mechanism into existence in a single unreviewed session. Precompute correctness has caused two real incidents this project (2026-06-06 corruption, 2026-06-09 disk lockup) precisely because writes to the serving layer were not sandboxed and integrity-checked. A same-session, unreviewed "quick push" of new production-write code is the exact pattern LESSONS.md warns against. Recommend: design the real fix with the same safety bar as `safe_deploy_droplet.sh` (sandboxed build, integrity check, atomic swap, rollback) as a scoped follow-up, not a rushed add-on tonight.

**Consensus:** Split on timing, not on direction. All six seats agree the
disclosure fix should ship now. Marketing and ED push for the real-time fix
immediately; Stewardship chair and the underlying incident history argue for
building it with proper sandboxing rather than rushed. No seat argues against
eventually building the real-time path.

**Confidence to proceed (disclosure fix):** 95% — small, safe, honest, no
architecture risk.
**Confidence to proceed (same-session live-push mechanism):** 40% — real
value, real risk of repeating a known incident pattern under time pressure
with no review.

## Gate 4 — Resolution

**Decided (within existing backend-autonomy rules):**
1. Ship the honest-timing disclosure in the claim/edit UI now — org sees
   "Saved. Your public page updates within 24 hours (usually sooner)."
2. Do NOT build the live-push mechanism in this session. Scope it as a
   follow-up task with an explicit design requirement: sandboxed build +
   integrity check + atomic swap + rollback, mirroring
   `safe_deploy_droplet.sh`'s existing safety bar — not a bespoke shortcut.
3. Remove (or clearly comment as dead-and-intentionally-inert) the
   `merge_claims`/`CLAIMS_DIR` code path so a future reader doesn't mistake
   it for a working feature — this is a P9 cleanliness fix, zero risk.

This does not need founder escalation — principles are clean, data is
gathered, board consensus is high on the safe half of the decision, and the
risk-avoiding half (declining to rush new production-write infra) is the
conservative, reversible choice. Logged to DECISIONS.md.
