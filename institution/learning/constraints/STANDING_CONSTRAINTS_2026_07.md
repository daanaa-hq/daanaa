# Standing Constraints & Recurring Rules

**Authority:** Learning Directive 2026-07-12  
**Scope:** Operational, architectural, and stewardship guardrails that recur across sessions  
**Status:** Live (enforced in code, tools, and workflow)

---

## OPERATIONAL CONSTRAINTS

### C-OP-001: Never Deploy Root API to Droplet

**Rule:** The root `daanaa_api.py` (8,284 lines, ~2.2GB RAM) is home-server/testing only. Production droplet runs only `scripts/droplet_api.py` (69KB, lean).

**Why:** Droplet has 2GB RAM total. Root API requires 4GB+ to load embeddings. Hand-rsyncing it has crashed the droplet twice (INC-002, INC-003).

**How to apply:**
- Only `sync_droplet_api.sh` may write `/opt/daanaa/droplet_api.py`
- Script grepped to refuse sources with `v4_scores` or `org_embeddings`
- All manual rsync bypasses this safety check — never do it
- After any droplet_api deploy, smoke-test `/api/organizations` and `/api/search?q=food+bank` from the public URL
- If both fail, auto-rollback to `.prev` immediately

**Related incidents:** [[incident-2026-07-05-spa-fallback-outage]], [[incident-2026-07-06-root-api-shipped-again]], [[incident-2026-07-09-droplet-oom]]

---

### C-OP-002: Droplet SSH Must Use Direct IP, Never daanaa.org Hostname

**Rule:** `root@162.243.97.179` for SSH and rsync. Never `root@daanaa.org`.

**Why:** daanaa.org routes through Cloudflare, which blocks SSH (port 22 times out). The domain only works for HTTP/HTTPS.

**How to apply:**
- All deploy scripts hardcode `DROPLET_IP="162.243.97.179"`
- Any new script must use this IP
- Mistake will cause immediate command timeout → catch in script testing

---

### C-OP-003: Watchdog Must Check Real Pages, Not Just /health

**Rule:** Health checks that only verify `/health` miss 500s on real routes. Watchdog must fetch a real page and verify doctype.

**Why:** INC-001 crashed the SPA fallback (every page 500) but `/health` stayed 200. Watchdog only checked `/health`, so 11 hours of downtime went undetected.

**How to apply:**
- Watchdog checks `https://daanaa.org/` for doctype
- Re-alerts every 6h while down (not just on state change)
- Post-deploy smoke tests must hit `/api/search` or `/api/organizations`, not just `/health`

**Related:** [[incident-2026-07-05-spa-fallback-outage]]

---

### C-OP-004: All Automation Credentials Must Be Passphrase-Free

**Rule:** SSH keys for cron tasks must have no passphrase. Interactive keys can remain passphrase-protected.

**Why:** INC-001's alert script failed because cron couldn't supply the passphrase to `~/.ssh/daanaa_do`. A separate automation key solves this; interactive SSH can stay protected.

**How to apply:**
- Create separate `~/.ssh/daanaa_do_cron` (no passphrase) for all cron tasks
- Leave `~/.ssh/daanaa_do` (passphrase-protected) for interactive use
- All ops scripts repoint to `daanaa_do_cron`

**Related:** [[incident-2026-07-05-spa-fallback-outage]] (alert chain failure)

---

### C-OP-005: Search Database Schema is Authoritative

**Rule:** search.db is built ONLY by `scripts/build_search_db.py`. Schema: `org_fts` + `registry_enriched` + `zip_codes`. Old June 22 artifacts are stale; fresh build required.

**Why:** INC-002 tried to run against old search.db with outdated `org_search` schema → search returns `mode:error`. Fresh build needed.

**How to apply:**
- Never hand-edit or copy search.db from old backups
- Always rebuild: `scripts/build_search_db.py`
- Smoke test after deploy: `/api/search?q=food+bank` must return `"mode":"fts"`
- If search returns error mode, rollback immediately

**Related:** [[incident-2026-07-06-root-api-shipped-again]], [[project-droplet-search-db-contract]]

---

## ARCHITECTURAL CONSTRAINTS

### C-ARC-001: Droplet Architecture is a Hard Boundary

**Rule:** Droplet runs only: lean query API (droplet_api.py) + precomputed static files + search.db. Never embeddings, models, heavy ML, or the full analytics API.

**Why:** Droplet has 2GB RAM, shared with Linux/nginx/gunicorn. Embedding-heavy workloads belong on the home server.

**How to apply:**
- Home server handles: daanaa_api.py, embedding generation, full analytics, batch ML
- Droplet handles: query API, precompute serving, search
- Memory is a hard constraint; never ship >2GB workloads without resizing + spend approval
- Droplet resize (2GB→4GB) needs founder approval per [[feedback-cost-mindfulness]]

**Related:** [[incident-2026-07-09-droplet-oom]], [[project-droplet-deploy]]

---

## STEWARDSHIP CONSTRAINTS

### C-STW-001: Flag All Cost-Bearing Decisions Before Proceeding

**Rule:** If a fix, plan, or recommendation has a cost implication (paid service, cloud API, storage), surface it and ask before folding it into the plan.

**Why:** Backend-autonomous policy (CLAUDE.md) covers deployment mechanics, not spend. Indirect costs (e.g., resuming S3 backup storage) should be explicit decisions, not silent.

**How to apply:**
- Prefer free alternatives (local GPU, home-server inference, Google Drive backup)
- When introducing a cost, name it, estimate it, and ask before proceeding
- Example: "Installing `aws` CLI would enable S3 backup cron, but costs $X/mo storage vs. free Google Drive chain — recommend keeping current path"

**Related:** [[feedback-use-local-inference]], [[feedback-server-hardware-preference]], [[project-backup-architecture]]

---

### C-STW-002: Deliberate Pace — Check Four Gates Before Shipping

**Rule:** Before implementing any feature, verify: (1) site-wide coherence (wording, patterns, navigation), (2) mission alignment (STEWARDSHIP.md), (3) simplicity for non-technical users, (4) no legal exposure (PII, attestations, money, unbuilt claims).

**Why:** Founder's direction 2026-06-12. Speed in building costs precision in design. Features shipped without these gates create tech debt and risk.

**How to apply:**
- Draft the feature design in 2-3 lines before building (what it does, where it fits, what it deliberately avoids)
- Review against mission + STEWARDSHIP.md
- Use one coherent pattern site-wide, not local cleverness
- Related: [[feedback-copy-voice]], [[feedback-daanaa-domain-comms]]

---

### C-STW-003: Copy Voice Must Be Human, Mission-Aligned, Simple

**Rule:** Site copy avoids: dashes, hyphenated jargon, statistics words, corporate language. Reads like a human explaining a neighborhood nonprofit.

**Why:** Language shapes how users feel about the platform. Complex copy excludes non-technical users; statistics words obscure mission.

**How to apply:**
- "Financial context" not "metric"; "needs community support" not "CAUTION"
- No "robust," "comprehensive," "nuanced," "landscape," "multifaceted"
- "People" not "constituents"; "giving" not "donations" (giving = second nature, private)
- Test: would you say this phrase at the kitchen table?

**Related:** [[feedback-research-copy-voice]], [[project-giving-philosophy]]

---

## DEVELOPMENT CONSTRAINTS

### C-DEV-001: Use Local Inference, Never Cloud APIs for Batch

**Rule:** For batch ML tasks (mission generation, embeddings, verification), route through local llama.cpp/Vulkan servers (ports 11436/11437). No cloud APIs for production batches.

**Why:** Cost control (no token burn) + auditability (models run locally) + privacy (no external data flow).

**How to apply:**
- Mission generation: `scripts/generate_missions.py` → port 11437 (Qwen)
- Embeddings: port 11436 (mxbai-embed-large)
- Never use OpenAI, Anthropic, or cloud APIs for batch tasks
- Related: [[feedback-use-local-inference]], [[project-ml-pipeline]]

---

### C-DEV-002: Test Measurement Infrastructure Before Deciding

**Rule:** Build measurement infra first. Test with real data. Review. Decide. (Commit-Test-Review-Repeat cycle.)

**Why:** Without measurement, decisions are guesses. Real-data testing catches issues that benchmarks hide.

**How to apply:**
- Example: scraper work — measure concurrency/throughput FIRST (see [[project-scraper-benchmarks]]), then decide on parallelism
- Another: feature work — instrument metrics BEFORE shipping, not after
- Review measurements openly; contradictions are valuable

**Related:** [[feedback-commit-test-review-repeat]]

---

## CONSTRAINT VIOLATIONS & ESCALATION

**If the same constraint class recurs violating:** (e.g., root API shipped a third time, or a third cost-bearing decision made silently), escalate to founder. It's a culture/training problem, not a tool problem.

**Precedent:** Constraint C-OP-001 was written after INC-001, violated within 24h by INC-002 → now enforced in the script itself (grep guard).

---

**Extracted:** 2026-07-12  
**Review Frequency:** Quarterly + incident-driven updates  
**Responsible:** Institutional steward + founder (oversight)

