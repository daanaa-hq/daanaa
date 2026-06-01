# Daanaa — Launch Checklist & Gates

Single source of truth for what must be true before public launch. **Gates** are
hard blockers. **Build** is feature work. Check items off as they land.

Automated gate already enforced: `scripts/privacy_check.sh` runs on every commit
(pre-commit hook). See `PRIVACY-INVARIANTS.md`.

---

## GATES — must pass before public launch (hard blockers)

- [ ] **G1. Attorney review** of `meritgiving-ops/legal/daanaa-governance-charter.md`,
      AI-content liability (AI missions about named orgs), UGC moderation / Section 230
      posture, org Terms of Use, and image rights / minors. (See board sim.)
- [ ] **G2. IRS auto-revocation handling.** Check orgs against the IRS auto-revocation
      list; suppress or clearly badge donate for revoked orgs. Showing a revoked org as
      donatable is real harm + liability.
- [ ] **G3. Privacy invariants green** in CI/pre-commit (`scripts/privacy_check.sh`). ✅ enforced
- [ ] **G4. Donate-link trust gating** stays fail-closed on unverified statuses. ✅ in place
- [ ] **G5. Methodology page matches the live scorer** (0.65 revenue / 0.35 reserve). ✅ aligned
- [ ] **G6. Org Terms of Use** published (separate from donor terms): what orgs may post,
      that they warrant authorization, and a content license to display it.
- [ ] **G7. Content moderation + takedown path** live before any org-generated content
      (open space, updates, needs, photos) is accepted. Input sanitization (XSS).

## BUILD — feature work toward launch

### Shipped ✅
- [x] AI provenance/beta for missions, donate links, and cause tags (`data_badges`)
- [x] AI/scraper disclaimer (Legal page + footer)
- [x] Claimed-profile wireframe + on-page empty-state preview of claimable spaces
- [x] Wallet backup: self-text + passphrase-encrypted (AES-GCM/PBKDF2) export/import + 90-day nudge
- [x] Privacy: IP-free access logs, `PRIVACY-INVARIANTS.md`, `privacy_check.sh`, pre-commit hook
- [x] Governance charter draft (from STEWARDSHIP)
- [x] **Scoring trust fix** — org headline now shows the documented composite (peer_percentile),
      consistent with the methodology + score-history (was showing the stale merit_score)
- [x] **Impact tracking (privacy-safe)** — weekly `impact_snapshot.py` time-series; anonymous
      `/api/handoff` give-click counter; `docs/JOURNEY.md` milestone log (AI-labeled)
- [x] **Donor-intent signal** — anonymous "I'd give / volunteer here" on unclaimed orgs
      (`/api/interest`); the demand shows to the org in the claim editor. Org-only, never public.
- [x] **Revenue section slimmed** — no big empty card for orgs without financials
- [x] **Overnight GPU/CPU scheduling** — `gpu_night.sh` (10pm-6am, heat-safe), 14B mission model

### In progress / next
- [x] **B1. Backup file encryption** — done (passphrase AES-GCM, key never leaves device)
- [~] **B2. Capacitor native wrapper** — config + `docs/native-app-setup.md` ready. Remaining is
      FOUNDER ACTION: Apple Developer + Google Play accounts, Mac/Xcode, run the documented publish.
- [~] **B3. Volunteer flow** — `VolunteerInterest` (device-send) + the anonymous intent signal
      shipped. Full reach pending B4 (org-provided volunteer contact/link).
- [ ] **B4. Claim-and-edit flow** — claim editor exists and now shows accumulated demand; still
      to build: org sets mission, 5 tags, ways-to-help, needs, updates, photo (the wireframe made real).
- [ ] **B5. Fiscal sponsorship** field — donations routed through a sponsor with a different EIN.
- [ ] **B6. Site alignment pass** — provenance/beta consistency across all pages.
- [ ] **B7. Opt-in "donate a statistic"** wallet button (Tier-3 aggregate impact; needs a small
      invariant amendment to permit explicit opt-in aggregate).

## DATA REFRESH CADENCE (when new data lands)

Automated via cron (`crontab -l`). All times local. Edit `scripts/auto_refresh.sh`
or the crontab to change cadence.

| When | What | Source | Why it matters |
|---|---|---|---|
| **1st of month, 1 AM** | `download_irs_soi.sh` — pulls latest IRS Statistics of Income extract | IRS SOI bulk | Authoritative annual revenue/asset figures |
| **Every Sunday, 1 AM** | `gt990_refresh` — pulls latest 990 XML index from the IRS S3 datalake | AWS S3 (IRS) | Tells us which orgs have new 990 filings to ingest |
| **Every Sunday, 2 AM** | `auto_refresh.sh` 4-stage pipeline: (1) ProPublica backfill → (2) ingest latest SOI year → (3) recompute peer groups + provisional percentiles → (4) **composite scorer** (0.65 revenue / 0.35 reserve) | ProPublica + IRS | This is THE weekly score refresh; rescore reflects the week's new data |
| **Every Sunday, 2 AM** | `backfill_stubs.py --phase 1` — fills in missing fields on partial orgs | NCCS / ProPublica | Improves coverage for data-dark small orgs |
| **Sun + every Mon-Sat, 3 AM** | `backfill_stubs.py --phase 2 --limit 300` — incremental gap-fill | same | Slow trickle, no spike |
| **Every Sunday, 3 AM** | `merit_daemon.sh` weekly orchestrator | various | Catch-all weekly housekeeping |
| **Every 2 hours** | `auto_ingest.py` — small batched ingestion of queued orgs | ProPublica cache | Keeps the queue moving without spikes |
| **Daily, 10 PM → 6 AM** | `gpu_night.sh` — mission generation on the local 14B GPU model | Local inference | Heat-safe overnight window (cron-enforced) |
| **Every Monday, 5 AM** | `impact_snapshot.py` — privacy-safe weekly impact metrics | own DB | Time-series for JOURNEY.md + future public impact page |

**To verify the schedule is actually firing:**
```bash
crontab -l | grep -viE '^(#|$|VENV=|SCRIPT=|LOGDIR=)'
tail -20 logs/impact.log         # last weekly impact snapshot
tail -20 autodev/logs/refresh.log  # last weekly refresh + rescore
```

**Manual data refresh (out of cycle):**
```bash
./scripts/auto_refresh.sh                                  # full Sunday-style refresh now
./scripts/download_irs_soi.sh && ./scripts/auto_refresh.sh # monthly SOI + refresh
```

---

## OPS / INFRA
- [x] **Git remote set up + push** — `github.com/daanaa-hq/daanaa` (private). All commits pushed 2026-06-01.
- [x] **9 daanaa.org email aliases live** — Google Groups, all forward to hello@ecomargins.com.
      Send-as aliases configured. Email triage agent (daily 7:30am cron) classifying + drafting.
- [x] **accounts@daanaa.org mailbox** — entity-owned login vault, external recovery, never AI-touched.
- [~] **DNS** — Cloudflare configured, A records point to DigitalOcean droplet (162.243.97.179).
      FOUNDER ACTION: flip both A records to Proxied (orange cloud) in Cloudflare DNS + set SSL/TLS → Flexible.
      After that: daanaa.org is live. DKIM still needed (Google Workspace Admin → Gmail → Authenticate email).
- [ ] **Minova disclosure + written consent** — before any public-facing actions
      (LinkedIn, press, daanaa.org public launch). Task #20. Requires ~$300-500 Colorado
      employment lawyer review. Civic/non-competing/personal-time facts are strongly in founder's favor.
- [ ] Native-backup story documented for users ("your giving rides your phone backup")
- [ ] Pre-launch full privacy + stewardship compliance review
- [x] Mission generation running (14B overnight + Haiku in daytime once Anthropic credits approved)
- [~] **Anthropic Startup Program** — application filed 2026-06-01. ~2 week review. Unlocks
      Haiku daytime mission generation for remaining 61K mission backlog.
- [x] **DigitalOcean droplet live** — daanaa-web, NYC2, $8/mo, 162.243.97.179. Gunicorn on port 80,
      2GB swap, UFW firewall, fail2ban, log rotation, auto security updates. Daily DB sync cron 7am.
- [x] **Beta banner** — dismissable, links to hello@daanaa.org for feedback. Ships with full app.

---

_Last updated: 2026-06-01. Manually maintained — the launch gate of record. Update
when items land. Companion docs: `docs/JOURNEY.md` (milestones), `PRIVACY-INVARIANTS.md` (enforced),
`docs/dns-setup.md` (DNS records), `meritgiving-ops/email-agent-routing.md` (email architecture),
`meritgiving-ops/credits-applications.md` (startup credits)._
