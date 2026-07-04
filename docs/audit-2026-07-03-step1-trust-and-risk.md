# Daanaa Audit — Step 1: Trust & Risk

**Date:** 2026-07-03 · **Method:** grounded in actual code/infra, not speculation · **Auditor:** Claude (partner review)

Covers **Security**, **Stewardship Language**, **Scoring Methodology**. Step 2 (Connectivity, UX, Search Visibility) follows after you absorb this.

---

## 🔴 THE ONE THING TO FIX TODAY

**Real API secrets are committed to git and pushed to GitHub.**

`.env.claim` is tracked in the repo and present on `origin/master` at `github.com/daanaa-hq/daanaa`. It contains real-format credentials:

| Key | Length | Format match |
|-----|--------|--------------|
| `LOB_API_KEY` | 40 | Lob live/test key |
| `TWILIO_ACCOUNT_SID` | 34 | `AC` + 32 hex = exact Twilio SID |
| `TWILIO_AUTH_TOKEN` | 32 | exact Twilio auth token |
| `CLAUDE_API_KEY` | 26 | Anthropic key (short — possibly old/partial) |
| `LOB_FROM_ADDRESS_ID` | 20 | Lob address id |

- **Committed:** 2026-06-16 (`21f6a70cc6e`), ~17 days ago
- **Exposure:** repo is **PRIVATE** — blast radius is collaborators + anyone with a leaked GitHub token, not the whole internet. That is the only reason this is not a five-alarm fire.
- **Root cause:** the pre-commit hook (`.git/hooks/pre-commit → privacy_check.sh`) was symlinked **2026-06-22** — six days *after* this file was committed. The guard existed in the repo but wasn't wired as a hook yet when the secret went in.
- **Second gap:** even today, `privacy_check.sh` GATE 6 calls `warn` (non-blocking) for secret files, not `fail`. And its filename list (`.env`, `.env.local`, `.env.*.local`, `secrets.json`) does not explicitly hard-block arbitrary `.env.*` files. A re-commit would warn, not stop.

**Remediation (needs your approval — I did not execute any of this):**
1. **Rotate all four credentials now** — Lob, Twilio (SID+token), Claude. Assume compromised. Rotation is the only real fix; scrubbing history without rotation is theater.
2. `git rm --cached .env.claim .env.email.example` and add `.env*` (broad) to `.gitignore`.
3. Scrub from history (`git filter-repo` or BFG) and force-push — coordinate since master is ahead 7 and there are active worktrees/branches.
4. Harden `privacy_check.sh`: GATE 6 should `fail` not `warn`, and match `^\.env` broadly (allow only `.env.example`).
5. Audit Twilio + Lob usage logs for the exposure window (2026-06-16 → rotation) for unexpected sends/charges — you're bootstrapped, a hijacked Twilio number bleeds money fast.

`.env.email.example` (tracked) — verify it's a real template with no live SMTP password before relaxing about it; the field names suggest placeholders but confirm.

---

## Security — what's actually SOLID (turned these stones, found them sound)

Credit where due. These were checked in code and hold up:

- **Admin auth is correct.** `require_admin_key` uses `hmac.compare_digest` (constant-time, no timing leak) and **fails closed** on empty key (`if not _ADMIN_KEY or not compare_digest(...)`). Manual checks at lines 5704/5722 use the same pattern. ✓
- **Claim flow crypto is sound.** PIN generated with `secrets.randbelow(900000)+100000` (CSPRNG, not `random`). Verify tokens are `HMAC-SHA256(secret, ein:pin)` compared with `compare_digest`. Prod fails closed if `DAANAA_CLAIM_SECRET`/`DAANAA_ADMIN_KEY` unset. ✓
- **No SQL injection found.** Every dynamic query builds the SET/WHERE clause from **whitelisted column names** (`allowed`/`_VALID_STATUSES` lists) and passes all values as `?` params. The f-strings interpolate column identifiers the code controls, never user data. FTS5 `MATCH` goes through `_sanitize_fts_query` (strips specials, wildcards each token) and is parameterized. ✓
- **Local LLM servers are not exposed.** Droplet binds only `22/80/443` publicly; `5000/5001/3000/5432/6379` are `127.0.0.1`-only. Ports `11436/11437` (llama.cpp) live on the home server, not the droplet — zero public attack surface. ✓
- **Rate limits exist on sensitive endpoints.** Claim submit `3/hour`, verify paths `5/hour`–`10/min`, feedback `5/min;20/hour`. Brute-forcing a 6-digit PIN is throttled. ✓
- **UFW is Cloudflare-aware** — 80/443 allowed from Cloudflare ranges (plus Anywhere).

## Security — real gaps below the CRITICAL

| Sev | Finding | Evidence | Fix |
|-----|---------|----------|-----|
| **MEDIUM** | Droplet SSH: `PermitRootLogin yes` and port 22 open to `Anywhere` (not just your IP) | `sshd_config` + `ufw status` | Password auth is already **off** (key-only), so this is hardening not an open door. Set `PermitRootLogin prohibit-password`, restrict 22 to your IP or a bastion, or move to Cloudflare Tunnel. |
| **MEDIUM** | Claim PIN is 6 digits with 30-day expiry as a legacy fallback | `daanaa_api.py:3138,3243` | The HMAC token is primary and strong; the PIN fallback (900k space) is only rate-limited. Consider shortening expiry to 7 days and dropping the raw-PIN path once token flow is universal. |
| **LOW** | GATE 6 in `privacy_check.sh` warns instead of failing | `privacy_check.sh:231-258` | Promote to hard fail (ties to the CRITICAL root cause). |

**Not vulnerabilities** (checked, ruling out noise): localStorage wallet holds bookmarks+intent only (no PII, no tokens); Plausible is cookieless; gunicorn `--preload` CoW shares read-only vectors (no cross-worker write path); in-process cache is keyed per-namespace with no observed cross-org key collision.

---

## Stewardship Language — findings

The copy discipline is genuinely strong (Approach.tsx, Methodology2.tsx, TiersPage.tsx all repeat "not a verdict / not a rating / peer context not judgment"). The risks are at the **seams** where a good sentence meets a product behavior that says something different.

**1. MEDIUM — `merit_score DESC` is a de-facto ranking on search + browse-all.**
(Scope refined 2026-07-03 after checking the live frontend — the API-level `merit_score`
default at `daanaa_api.py:1751` is NOT the whole story.) The `/directory` **landing**
defaults to hidden gems (small orgs, `Directory.tsx:168`), which is mission-aligned. But
the sort is `merit_score DESC`, and the gems lens is dropped on **search** and **"See
all"** — where results then lead with score-100 endowment funds / foundations (verified on
prod). The comment *"callers should prefer merit_score for org discovery"* still hands a
journalist the "ranking-under-another-name" quote. Real, but scoped to search/browse-all,
not the landing. Fix is a product decision (relevance-first on search; within-band shuffle
on browse-all), not just copy. Note: the reserve-hoarding critique (an org spending 95% on
programs shows thin reserves → low percentile) compounds this on those two surfaces.

**2. MEDIUM — "Needs support" for CAUTION is defensible but fragile on the compare page.**
`V5Context.tsx:26`, `WalletCard.tsx:16` — the label + tooltip ("An invitation to give, not a judgment") is well-crafted **when the tooltip is present**. On `/compare`, one org showing "Financially healthy" (emerald) beside another showing "Needs support" (amber) reads as good-vs-bad at a glance, before anyone hovers. Amber is a caution color everywhere else on the web. Verify the supportive framing survives the side-by-side visual.

**3. MEDIUM — "Hidden gems" smuggles a quality judgment.**
"Small but high-performing" = high reserve percentile in peer cell. Calling that a "gem" is an editorial endorsement, which sits awkwardly next to "we do not endorse or recommend." Either reframe as purely factual ("small orgs with strong reserves relative to peers") or accept it's a cur: pick one and make the methodology page say so explicitly.

**4. LOW — "AI generated" label is thin.** It doesn't convey recency or that it may be wrong. On a page a donor uses to decide, add "AI-drafted from public data — may be imperfect, report errors" near the mission.

---

## Scoring Methodology — the pressure test result

This is where a smart outsider will push hardest, and I found one answer the platform **cannot currently defend well**:

**The funding archetype ignores the org's actual funding.** (Verified against the prod
scorer 2026-07-03. Original draft cited `compute_v5_context.py`, an inactive/alt script;
the live scorer is `scripts/merit_scorer_v5_0.py`, whose `get_archetype_by_ntee(ntee1)`
takes ONLY the NTEE letter — so the conclusion stands, just re-sourced.)
Archetype is a **lookup on the single NTEE major-group letter**:
- Every Arts/Education/Environment/Housing/Food/Human-Services org → "Donation-Funded"
- Every Health Care / Research / Employment org → "Fee-for-Service"
- Philanthropy (T) → "Endowment-Funded"

**ALSO FOUND (data quality):** the live DB carries **7 archetype labels from two scorer
runs with drifted names** — "Donation-Funded" (1.26M) and "Donation-Funded Programs"
(301K) are the same concept; likewise Fee-for-Service / Fee-for-Service Operators,
Endowment-Funded / Endowment-Funded Grantmakers, plus "Mutual-Benefit" (65K). Two similar
orgs can display different archetype labels depending on which scorer touched them last.
CLAUDE.md's "v5 only assigns 3 archetypes" is stale. Needs one re-score pass on a single
label scheme before this is donor-facing-clean.

The org's real 990 revenue composition is **never examined**. So:

- The journalist's hybrid-funding question ("40% donations / 40% fees / 20% endowment — which bucket?") has a blunt answer: **whatever its NTEE letter says, and nothing about its actual money enters the decision.**
- A food bank (K) running 90% on government contracts is still scored against *donation-funded* peers. A community health center (E) that's 70% grants is forced into *fee-for-service*. That mismatched peer group directly moves its percentile — and therefore its HEALTHY/STABLE/CAUTION signal.
- Nonprofit-exec question #8 ("how did you decide our archetype, can we dispute it?") currently has **no dispute path and a weak rationale**: "your NTEE code is E, so you're fee-for-service."

The docstring lists 5 archetypes (adds Membership, Mutual-Benefit) but the map only assigns 3 — matching CLAUDE.md's note that the NTEE constraint caps real assignment at 3. So the taxonomy is even coarser than it looks.

**Why it matters for you specifically:** your whole trust proposition is "evidence-based, explainable, peer-fair." A peer group defined by a 1-letter proxy instead of the org's real financials is the weakest link in that chain. It's not wrong to *start* with an NTEE proxy — it's wrong to not *say so plainly* and not offer correction. **Recommended:** (a) methodology page states outright "archetype is currently assigned from NTEE category, not from your filing's revenue mix — this is a known simplification"; (b) add a dispute/correction path (you already have the Mistake Registry — wire archetype into it); (c) roadmap: derive archetype from actual 990 revenue-source ratios where the data exists.

**Other scoring answers that DO hold up:**
- "Score is peer percentile, not quality" — true and consistently coded. A 75 = better reserves than 75% of the (same-archetype, same-band) cell. ✓
- "No org can pay to change its score" — structurally true; score is deterministic from IRS data, computed nightly, no write path from vendor/partner tables into scoring. The Terms claim is backed by architecture, not just promise. ✓
- Band cutoffs (Micro <$150K / Professional $150K–$700K / Established >$700K) exist and are applied — but I did **not** find published rationale for *why* those specific numbers. A journalist will ask; have an answer ("chosen to balance cell sizes across the registry" or whatever the real reason is) and put it on the methodology page.
- **Reserve-hoarding critique is real and unaddressed:** an org that spends 95% of revenue on programs will show thin reserves → lower percentile → possibly "Needs support." Your copy frames low reserves as "resources go straight into programs, not a judgment" — good — but the *sort* still buries that org. This is the same root issue as Stewardship #1.

---

## Step 1 priorities (do in this order)

1. **Rotate the four leaked credentials** (Lob, Twilio ×2, Claude) — today. Then scrub + gitignore + fail-closed the hook.
2. **Decide the directory default sort.** `merit_score DESC` is your biggest principle/behavior contradiction and it's one product decision to fix.
3. **Disclose the NTEE-proxy archetype** on the methodology page and add a dispute path. Cheap, and it closes the scariest journalist question.
4. Harden droplet SSH (`prohibit-password`, restrict port 22).
5. Verify CAUTION/amber framing survives the `/compare` side-by-side.

---
*Not a substitute for a professional pentest. This is an AI-assisted first pass grounded in your actual code. For the credential exposure specifically, treat rotation as mandatory regardless of anything else here.*
