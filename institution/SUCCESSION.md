# Succession And Continuity

## Document Control

| Field | Value |
|---|---|
| Purpose | Reduce unhealthy dependence on the founder, current developers, current models, vendors, and stack. |
| Responsible role | Chief Steward; Continuity Steward when appointed. |
| Authority level | Continuity plan; protected by `CONSTITUTION.md` where mission is involved. |
| Review trigger | Weekly review, new single point of failure, vendor change, key-person dependency, incident, or funding change. |
| Editable status | Editable by ordinary agents for proposed improvements; authority changes require founder approval. |
| Dependencies | `GOVERNANCE.md`, `CURRENT_STATE.md`, `RISK_REGISTER.md`, `BUDGET_STATE.md`. |
| Retirement condition | Retire when replaced by board-approved succession and continuity plan. |

## Current Single Points Of Failure

- Founder approval and provider-console access for finance, billing, credentials, and legal decisions.
- Local server and SQLite data store.
- DigitalOcean droplet production path.
- Large local data artifacts and backups.
- Local model services for enrichment/search assistance.
- Repository institutional memory spread across many docs.

## Continuity Direction

- Keep core public discovery useful without paid access.
- Preserve data provenance and decision rationale.
- Make recovery, deployment, backup, and review procedures executable by a qualified successor.
- Keep secrets out of repo and document where authority lives without exposing credentials.
- Prefer open formats and exportable data.
- Avoid vendor lock-in unless measurable benefit justifies it and an exit path is recorded.

## Memory Substrate (Stewardship Board Resolution 2026-07-11)

**Critical:** Every institutional knowledge store, its location, format, authority level, and recovery procedure is documented here. This section answers: "Could a qualified successor rebuild the institution's memory?"

### Store 1: Git Repository (Authoritative)

**What it holds:** All code, STEWARDSHIP.md, DECISIONS.md, LESSONS.md, documentation, tests, scripts.

**Location:** `/home/akbar/meritgiving/` (local) + `https://github.com/daanaa-hq/daanaa.git` (remote)

**Format:** Git (.git) + Markdown + Python + Shell

**Authority:** Authoritative for operational knowledge.

**Recovery:**
```bash
# If local is lost:
git clone https://github.com/daanaa-hq/daanaa.git
cd daanaa && git log --oneline | head -20  # Verify history

# If GitHub is lost:
git remote add backup <alternate-host>
git push backup master
# (Requires founder GitHub account access; add co-admin now if missing)
```

**Risks:** One vendor (GitHub), one founder for console access. Mitigation: add a second admin to the GitHub organization.

---

### Store 2: Institution Directory (Constitutional)

**What it holds:** Steward's Charter, Stewardship Constitution (library 003), full library (001–010), AI Governance, Development Constitution, Research Agenda, Future of Giving, governance documents, board resolutions, proposals, reviews, institutional memory.

**Location:** `/home/akbar/meritgiving/institution/` (local) + now in git remote

**Format:** Markdown (.md files)

**Authority:** Authoritative for constitutional governance.

**Recovery:**
```bash
# Institution/ is tracked in git as of 2026-07-11 — same recovery as Store 1
git log -- institution/ | head -20  # Verify history
ls institution/board/ institution/library/ institution/reviews/  # Verify completeness
```

**Status:** Now git-tracked (private repo). If repo is public, review access before pointing outsiders here.

---

### Store 3: AI Session Memory (Operational Context)

**What it holds:** Incident post-mortems, standing constraints, architectural decisions, session summaries, lessons learned, project state snapshots. This is the operational context that grounds each AI session.

**Location:** `~/.claude/projects/-home-akbar-meritgiving/memory/` (on home server only)

**Format:** Markdown (.md files) + MEMORY.md index

**Authority:** Derived from code and institutional documents; supplements with operational wisdom.

**Recovery:**
```bash
# Not currently in git or backup. Manual migration required:
cp -r ~/.claude/projects/-home-akbar-meritgiving/memory/ /home/akbar/meritgiving/institution/ai-memory/
git add institution/ai-memory/
git commit -m "institution: preserve AI session memory (operational context)"
```

**URGENT ACTION NEEDED:** Successor should run the migration command above and commit immediately. Once committed, this store is covered by git backup and offsite via GitHub.

---

### Store 4: Workflow Tool State (Secondary)

**What it holds:** Checkpoint history, decision logs (JSONL), learnings (JSONL), design documents, review histories. This contains reasoning trail.

**Location:** `~/.gstack/projects/meritgiving/` (on home server only)

**Format:** Markdown + JSONL (open text-based formats)

**Authority:** Derived; decision reasoning should flow to DECISIONS.md.

**Recovery:**
```bash
# Manual migration:
# - Copy highest-value items (checkpoints, decisions.jsonl, learnings.jsonl) to institution/
# - Commit to git
# - Consider: are there decisions in JSONL that are not in DECISIONS.md? If yes, backport first.
```

**Standard:** Checkpoints and decisions are working material; they should graduate into DECISIONS.md and LESSONS.md (which are already git-tracked).

---

### Store 5: Vector Index Cache (Rebuildable)

**What it holds:** Chroma embedding store, mempalace vector cache of known entities.

**Location:** `~/.mempalace/` (on home server only)

**Format:** Chroma binary format (proprietary)

**Authority:** Cache/derived. Non-authoritative if source documents exist elsewhere.

**Recovery:**
```bash
# DO NOT rely on this cache for recovery.
# Instead: verify that all entity data, vectors, and sources are committed to git or the database.
rm -rf ~/.mempalace/
# Rebuild by running scripts/build_org_embeddings.py against current database.
```

**Standard:** This store must be declared a Temporary Decision (cache, not memory). Audit that no entity-level facts exist ONLY in mempalace.

---

### Store 6: Database Backups (Critical for Data)

**What it holds:** Nightly SQL dumps (org_claims, org_activity, feedback, waitlist); weekly SQLite snapshots.

**Location:** `/home/akbar/meritgiving/data/backups/` + offsite via rclone to Google Drive (`daanaa-backup:`)

**Format:** SQL text + SQLite binary

**Authority:** Authoritative for operational data (claims, activity, feedback).

**Recovery:**
```bash
# Restore from latest backup:
sqlite3 data/merit_registry.db < data/backups/latest_critical_dump.sql

# Verify offsite backup exists:
rclone listremotes  # Should show "daanaa-backup:"
rclone ls daanaa-backup: | grep 2026-07  # Check recent backups exist

# Restore from offsite if needed:
rclone get daanaa-backup:/latest_snapshot.db ./data/recovery.db
```

**ISSUE NOTED:** Backup script silently skips offsite if rclone fails. This was fixed in Phase 1 of the implementation plan (2026-07-11).

---

### Store 7: Droplet (Non-Authoritative by Design)

**What it holds:** Precompute static files, deployed frontend, droplet_api.py.

**Authority:** None — no source of truth lives on the droplet.

**Recovery:** Rebuild and redeploy from source (git + home server), never restore from droplet disk.

```bash
# Droplet is a deployment target, not a memory store.
# All authority comes from /home/akbar/meritgiving/ (home server) + git.
```

---

## Succession Testing Checklist

Every 6 months, or when adding a new steward, run this verification:

- [ ] Clone repo from GitHub; verify all branches and history intact
- [ ] Verify institution/ directory is present and git-tracked
- [ ] Spot-check 5 DECISIONS.md entries are dated and reasoned
- [ ] Spot-check 5 LESSONS.md entries are dated with evidence
- [ ] Restore latest DB backup locally; verify 10 claims rows intact
- [ ] Verify offsite backup exists (rclone) dated within last 24 hours
- [ ] Review latest backup restore evidence in `institution/reviews/`
- [ ] Review provider ownership and second-admin status in `institution/PROVIDER_ACCESS_MAP.md`
- [ ] Verify droplet database is NEVER treated as source of truth
- [ ] Verify successor can read SUCCESSION.md without contacting founder

**Result:** If all checks pass, the institution is recoverable without the current founder.

---

## Near-Term Continuity Actions

1. ✅ Verify offsite backups and restoration.
2. ✅ Reconcile deployment source-of-truth for droplet API.
3. ✅ Record monthly spend and service ownership.
4. Keep founder requests small, explicit, and batched.
5. Move repeated decisions into documented workflows only after evidence.
6. **NEW (Board 2026-07-11):** Migrate AI session memory (Store 3) to git
7. **NEW (Board 2026-07-11):** Audit and backport gstack workflow state (Store 4) into DECISIONS.md/LESSONS.md
8. **NEW (Board 2026-07-11):** Fix backup script's silent-skip on rclone failure
9. **NEW (Board 2026-07-11):** Add second admin to GitHub organization

