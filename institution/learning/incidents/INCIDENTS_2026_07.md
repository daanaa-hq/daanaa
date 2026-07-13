# Institutional Incidents & Root Causes

**Period:** 2026-07-05 to 2026-07-09  
**Authority:** Learning Directive 2026-07-12  
**Status:** All incidents resolved; prevention rules established

---

## INC-001: SPA Fallback Outage (2026-07-05, 11h)

**Incident:** daanaa.org returned 500 on every page 04:30–15:32 UTC.

**Root Cause:** Midnight "quick fix" commit (d56a76e) deployed root `droplet_api.py` (8,284 lines, ~2GB RAM) to droplet (961MB RAM). Process crash-looped 160x on missing Twilio dependency. The fix moved SPA fallback to end of file but dropped the final `return send_from_directory()` → every route returned None → 500.

**Why silent 11h:** Watchdog only checked `/health` (not a real page) and only alerts on state change. Alert script failed: bare python3 import under cron with no cwd context → alerts no-oped for days. Nightly deploy crons failing on SSH key passphrase issues since ~Jul 3 (undiagnosed at the time).

**Prevention Rules:**
1. **Never deploy root `droplet_api.py` to droplet.** It requires 2GB+ RAM; droplet has 961MB. Use only `scripts/droplet_api.py` (69KB, lean subset).
2. **Watchdog must check a real page, not just health.** Verify `https://daanaa.org/` for doctype; re-alert every 6h while down.
3. **All ops deploy scripts must have ERR traps + venv-python.** No bare python3 imports; use explicit error handling.
4. **Post-deploy smoke test with auto-rollback.** `sync_droplet_api.sh` now tests `/api/organizations` and reverts `.prev` on failure.
5. **SSH keys for automation must be passphrase-free.** Created separate `~/.ssh/daanaa_do_cron` for cron tasks; leave interactive keys unchanged.

**Evidence:** Commits d56a76e (failure), 949b0036a62 (fix + smoke tests), c5d6ab3c0af (SSH key fix).

**Related:** [[incident-2026-07-06-root-api-shipped-again]], [[incident-2026-07-09-droplet-oom]]

---

## INC-002: Root API Shipped Again (2026-07-06, 3.3h)

**Incident:** /directory empty, /api/search returned 500 from 13:25–16:43 UTC.

**Root Cause:** Same failure family as INC-001. Root `droplet_api.py` hand-rsynced to droplet during donation-links session, not through the safe `sync_droplet_api.sh` script. Process crashed on missing v4_scores / org_embeddings queries; droplet had only search.db.

**Why it happened:** "Structural guard beats discipline" — the INC-001 rule "never rsync root droplet_api.py" was violated within 24 hours of being written. Manual rsync bypassed safety checks.

**Prevention Rules:**
1. **Only `sync_droplet_api.sh` may write to `/opt/daanaa/droplet_api.py`.** No manual rsync; no hand-edits.
2. **Script refuses sources referencing v4_scores or org_embeddings.** Grep check before sync prevents wrong file slipping through.
3. **Smoke-test both /api/organizations and search endpoint post-deploy.** If either fails, auto-rollback to `.prev` immediately.
4. **Treat deployment completion claims as unverified until curled from public URL.** Health checks don't prove the SPA is serving real pages.

**Also fixed this incident:**
- **DB path mismatch:** nightly_search_deploy.sh was shipping to `/data/search.db` but systemd reads `/data/precompute/v1/search.db`. Fresh search.db built Jul 10, live verified.
- **S3 deploy dead path:** /opt/daanaa/data/ writes go nowhere; 3.5am cron was pushing disk to 96%. Cron retired; backup now uses Google Drive (see [[project-backup-architecture]]).
- **Droplet resized:** $8→$16/mo (2GB RAM, 70GB disk); migration took ~3h.

**Evidence:** Commits cedaf1085, 5fbed8cf6 (sync_droplet_api.sh guards), live verification Jul 10.

**Related:** [[incident-2026-07-05-spa-fallback-outage]], [[incident-2026-07-09-droplet-oom]]

---

## INC-003: Droplet OOM (2026-07-09, 1.5h)

**Incident:** Deploying full `daanaa_api.py` to droplet caused OOM crash + restart loop + manual power cycle required. Site down ~1.5h.

**Root Cause:** `daanaa_api.py` loads 537K org embeddings (~2.2GB) at startup. Droplet has exactly 2GB total RAM. Process crashed on memory exhaust, restart=always loop memory-thrashed the box, SSH died.

**Why it happened:** Same misconception as INC-001/INC-002 — root API (home-server/testing only) does not belong on droplet.

**Hard Facts:**
- Droplet spec: 2GB RAM (not 70GB RAM — the 70GB is disk/storage).
- Droplet architecture (droplet_api.py + precompute + search.db) is BY DESIGN, not a compromise.
- Full `daanaa_api.py` requires 4GB+ RAM if ever deployed; spend decision must be explicit (ask founder first per [[feedback-cost-mindfulness]]).

**Prevention Rules:**
1. **Droplet_api.py is the canonical droplet binary.** No exceptions. Verify deployments load the correct file (`scripts/droplet_api.py`, not root).
2. **search.db is built by `scripts/build_search_db.py` only.** Schema: org_fts + registry_enriched + zip_codes. Old June 22 artifacts are stale; fresh build required.
3. **Smoke test search: `/api/search?q=food+bank` must return `"mode":"fts"`.** If search.db is broken, this fails immediately.
4. **Memory is a hard constraint.** Never ship anything over 2GB (embeddings, models, caches) to the 2GB droplet without prior resizing + spend approval.

**Evidence:** Incident log (no commit, it was a crash + rollback); fresh search.db shipped Jul 10, live verified.

**Related:** [[incident-2026-07-05-spa-fallback-outage]], [[incident-2026-07-06-root-api-shipped-again]], [[project-droplet-search-db-contract]]

---

## Prevention System Summary

**The Three Rules (all from these incidents):**

1. **Structural guards beat discipline.** After INC-001, we wrote the rule. INC-002 proved it was violated within 24h by hand-rsync. Solution: only `sync_droplet_api.sh` can deploy; grep checks in the script itself.

2. **Watchdog must check real pages, not just health pings.** A 200 on /health while serving 500 on every route is silent failure.

3. **Droplet architecture is the boundary.** Embedding-heavy code (daanaa_api.py) stays on home server. Lean query API (droplet_api.py) + precompute + search.db is the production design. Never violate this.

**Escalation trigger:** If the same incident class recurs, it's a culture/training problem, not a tool problem. Escalate to founder.

---

**Confidence:** High (all root causes confirmed, fixes verified, prevention rules live in production)

**Date Extracted:** 2026-07-12  
**Next Review:** 2026-08-12 (monthly incident review)

