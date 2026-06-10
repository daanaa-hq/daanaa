# PHASE 5 — Stewardship Reconciliation (principles → code) — 2026-06-09

## Verdict: governance is unusually well-enforced in code — 9 of 11 principles verified
## with concrete mechanisms. One principle (trust signals) has the Phase 3 CRITICAL gap.

## Document landscape (resolves the audit prompt's "7-doc vs 12-doc conflict")
- `STEWARDSHIP.md` (11 principles, signed, with revision + compliance logs) — canonical.
- `docs/11-STEWARDSHIP-PRINCIPLES.md` — companion enforcement doc; **identical 11 titles,
  no divergence found** (includes Code-Level Veto Gates + Monthly Audit sections).
- `PRIVACY-INVARIANTS.md` — 7 *invariants* (machine-checked). The audit prompt's
  "7-principle mission-lock" doesn't exist; "7" almost certainly refers to these.
- Conclusion: no doc conflict. The prompt premise was stale, not the repo.

## Principle → enforcement table

| # | Principle | Enforced? | Evidence (verified this audit) | Gap |
|---|---|---|---|---|
| 1 | Mission before growth | ✔ | No paid/sponsored logic anywhere (grep clean); surge-boosts are admin-oversight, not paid; default sort = merit_score not revenue | api/main.py dormant revenue sort (P1-MED) |
| 2 | Privacy is core | ✔ | See invariants table below; privacy_check.sh wired into .git/hooks/pre-commit | research-auth brute force (P1-HIGH) is adjacent |
| 3 | Trust signals evidence-based | ⚠ | FinancialContext: honest labels + confidence + data-quality flags; TrustBadge pinned to published methodology | **CRITICAL: 192,501 revoked orgs shown with tier badges, no disclosure (P3-1)** |
| 4 | Fairness to small orgs | ✔ | Peer-group percentiles (peer_cell_size), is_hidden_gem mechanic, Tier B partial-data scoring includes 308K small orgs | — |
| 5 | Don't weaponize transparency | ✔ | "Financially Strained" rendered amber (not red/shaming), with explanation + confidence, never a verdict | tone worth a copy review, not a code gap |
| 6 | Mistakes corrected quickly | ✔ | MistakeRegistry.tsx component (public registry); LESSONS.md discipline | — |
| 7 | Independence protected | n/a | No funding/partnership logic in code to audit | — |
| 8 | No donor funds | ✔ | Donate = handoff only; donate_handoffs records "NO identity, NO IP, NO amount" (:374-392); fail-closed eligibility gate | — |
| 9 | Decisions explainable | ✔ | DECISIONS.md, scoring_runs + score_snapshots tables, validate_v4_scores.py | — |
| 10 | AI is a tool | ✔ | mission_source provenance column, AiBadge.tsx labels AI content, admin oversight endpoints cite "Principle #6/#10" | — |
| 11 | Principles strengthened not weakened | ✔ | Revision Log + Compliance Log sections in STEWARDSHIP.md | — |

## Privacy invariants (machine-checked claims, re-verified live)

| Invariant | Status | Evidence |
|---|---|---|
| 1. No third-party trackers | ✔ | grep gtag/facebook/mixpanel/hotjar/posthog/sentry/segment: zero hits |
| 2. Giving data never leaves device | ✔ | Wallet localStorage-only; event types are names only (no contents) |
| 3. No visitor IP retention | ✔ | gunicorn `--access-logformat '%(t)s "%(r)s" %(s)s %(b)s %(M)sms'` omits %(h); **confirmed in live log lines** |
| 4. CSP strict | ✔ | `script-src 'self'`, no unsafe-eval, no wildcards; prod connect-src HTTPS-only |
| 5. No donor identity + giving | ✔ | donate_handoffs/event comments + schema; waitlist email-only |
| 6. Minimal labeled server PII | ✔ | waitlist + org_claims only, as documented |
| 7. Volunteer connect-don't-collect | ✔ | SupportIntent deep-link pattern; no contact list table |

## Findings
- **MED [governance-gap] daanaa_api.py:1096** — Principle 3's only code gap is the Phase 3
  CRITICAL (revoked orgs). Not double-counted; cross-reference only.
- **LOW [docs] CLAUDE.md** — says "11 principles" in one place; audit prompts circulating
  say "12-principle" and "7-principle mission-lock" — both wrong. Fix CLAUDE.md is right;
  retire stale prompt copies so future agents don't hunt for nonexistent docs.
- **INFO** — `.git/hooks/pre-commit` runs privacy_check.sh ✔ (structural enforcement is real,
  not aspirational — rare and worth preserving).
