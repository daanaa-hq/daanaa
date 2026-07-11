# Institutional Memory Review — 2026-07-11

## Document Control

| Field | Value |
|---|---|
| Purpose | Charter Amendment 1 commission: evaluate whether any institutional knowledge depends on one founder, one server, one vendor, one AI model, one storage format, one deployment, or one undocumented workflow or reasoning process. |
| Responsible role | Institutional steward (AI), under founder authority. |
| Authority level | Survey and recommendation only. Nothing was modified, committed, or reconfigured during this review. |
| Method | Direct inspection of every known memory store on 2026-07-11: `git status`/`git ls-files`, directory listings, the backup script read in full, `rclone listremotes`, and `institution/SUCCESSION.md` read in full. |
| Classification of this review | Historical Record, containing one Constitutional Gap and prioritized recommendations. |

**Summary verdict:** Daanaa's *operational* memory (code, decisions, lessons) is in good shape — versioned, remoted, and habitually maintained. Daanaa's *institutional* memory — the wisdom library, the charter, the constitution, this very review — currently exists on one disk, in no version control, in no backup scope. The documents that argue most eloquently for fifty-year preservation are the least preserved artifacts in the project. That is the single finding that matters most; everything else in this review is detail.

---

## 1. Inventory: Where Institutional Knowledge Actually Lives

### 1.1 The git repository + GitHub remote

- **What it holds:** all code, `STEWARDSHIP.md`, `DECISIONS.md`, `LESSONS.md`, `TODOS.md`, docs/, scripts, tests.
- **State verified:** remote `origin` = `https://github.com/daanaa-hq/daanaa.git`; local master and origin/master in sync at time of review.
- **Against the single-points list:** two physical copies (home server + GitHub) — good. One *vendor* (GitHub), but the format is git itself: open, standard, trivially re-hostable. One undocumented dependency: whether the GitHub organization has a second human with access is unknown to this review — if the founder's GitHub account is lost, is the remote recoverable? **Founder-only question.**
- **Assessment: healthy.** This is the institution's best memory substrate, which is exactly why everything constitutional should be inside it.

### 1.2 `institution/` — the wisdom library ⚠ CONSTITUTIONAL GAP

- **What it holds:** the Steward's Charter, the Stewardship Constitution (library 003), the full library (001–010), AI_GOVERNANCE, DEVELOPMENT_CONSTITUTION, RESEARCH_AGENDA, FUTURE_OF_GIVING, SUCCESSION, GOVERNANCE, DECISION_LOG, RISK_REGISTER, reviews, proposals, skills, briefs — the entire constitutional and governance layer of the institution.
- **State verified:** `git status --porcelain institution/` returns `?? institution/` — **the whole directory is untracked.** It is also outside the backup script's scope (§1.7). It exists as exactly one copy, on one disk, on one machine.
- **Against the single-points list:** fails on one server, one storage location, one deployment (of zero, really), and — because only the founder and the AI sessions that wrote it know it exists — arguably one founder too. The format itself (Markdown) is open and durable; the *storage* is the failure.
- **Assessment: this is a Constitutional Gap in Amendment 1's precise sense** — knowledge without ownership by any preservation mechanism. Library 005 states: "An institution built for future generations does not store its memory in formats owned by companies that may not exist then." The current state is worse than the failure 005 warns of: the memory is stored in no system at all beyond a filesystem. One disk failure ends the library. The smallest fix (§4, Recommendation 1) is a single git command plus one commit — but committing is a **founder decision**, both because repo-write approval rests with the founder and because tracking the library in a GitHub-hosted repo raises the question of whether the repo is private or public, and whether the founder wants the constitutional layer visible wherever the repo is visible.

### 1.3 `~/.claude/projects/-home-akbar-meritgiving/memory/` — AI session memory

- **What it holds:** ~584K of Markdown: MEMORY.md index plus ~80 topic files — incidents, project state, standing feedback/preferences, session summaries. This is the operational context that re-grounds each AI session; library 008 explicitly celebrates it ("documentation good enough to brief a machine cold is documentation good enough to brief a human successor cold").
- **Against the single-points list:** one machine, one copy, not in backup scope, and — the subtle one — one *vendor's location convention*. The content is plain Markdown (good, open format), but it lives in a path owned by one AI vendor's tooling, invisible to anyone who doesn't know that convention exists. A successor who inherited the repo would never find it. If the vendor's tooling changed its storage layout, continuity depends on migration tooling we don't control.
- **Assessment: valuable content, wrong location, zero redundancy.** The knowledge inside (incident post-mortems, standing constraints like "droplet holds nothing authoritative," deploy-path traps) is exactly the operational wisdom 008 says institutions die without. Some of it is duplicated in LESSONS.md; much is not.

### 1.4 `~/.gstack/projects/meritgiving/` — workflow tool state

- **What it holds:** ~2.7M: checkpoints, `decisions.jsonl`, `learnings.jsonl`, design documents, review histories, timelines.
- **Against the single-points list:** one machine, one copy, one vendor's format (JSONL + Markdown — both open, readable without the tool), not in backup scope, and one undocumented workflow: nothing in the repo tells a successor this store exists or what the gstack toolchain is.
- **Assessment: secondary but real.** Contains reasoning history (decisions, learnings, design evolution) that Amendment 1's Decision Evolution duty says must be preserved. Lower priority than 1.2 and 1.3 because the highest-value decisions should already be flowing into DECISIONS.md — but "should" has not been audited.

### 1.5 `~/.mempalace/` — Chroma vector store

- **What it holds:** `palace/` (Chroma embedding store), `known_entities.json`, config.
- **Against the single-points list:** one machine, one binary format (Chroma's internal layout), one embedding model — re-query requires the same or a compatible embedding model, so this store fails the "one AI model" test *by construction*. Not in backup scope.
- **Assessment: treat as a rebuildable cache, and say so in writing.** A vector index derived from source documents is an *instrument*, not *memory* — provided every source document lives elsewhere. The risk is drift: if anything was ever captured *only* into mempalace (an entity note, a fact with no source file), it is memory trapped in a cache. Recommendation: declare it non-authoritative (a Temporary Decision, documented), and spot-audit that `known_entities.json` content exists in durable form elsewhere.

### 1.6 `DECISIONS.md` / `LESSONS.md` / `TODOS.md`

- **State verified:** all three tracked in git, therefore on GitHub too.
- **Assessment: the healthiest memory practice in the institution.** Open format, versioned, remoted, habitually maintained, and readable by any successor with no tooling. This is the pattern everything else should converge toward. The only weakness is inherited from 1.1: recoverability of the GitHub side rests on founder-account access.

### 1.7 Backups — `scripts/ops/daanaa_backup.sh` (read in full) + offsite

- **Actual scope, verified against the script:** nightly SQL dump of four critical DB tables (`org_claims`, `org_activity`, `feedback`, `waitlist`) with 30-day retention; weekly full SQLite snapshot (Sundays, 2 kept); offsite push via rclone to Google Drive remote `daanaa-backup:` (verified configured; today's critical dump exists on disk).
- **What the backup does NOT cover — this list is the finding:** the `institution/` directory, `~/.claude` project memory, `~/.gstack` project state, `~/.mempalace`, the git repo itself (acceptably — GitHub is the repo's offsite), any of `docs/`, and any non-database file at all. **The backup system is a database backup, not an institutional-memory backup.** Project memory's description of "home server authoritative, Google Drive offsite" is true only for four tables and a weekly DB snapshot.
- **One structural weakness in the script:** the offsite push is conditional — if `rclone` or the remote is missing, the script *silently skips* offsite and still reports "backup ok." The remote exists today; the day it breaks, no one will be told. (The institution has already lived this failure shape once: the retired S3 path that shipped to a dead location.)
- **Against the single-points list:** for DB data — two locations, adequate. For everything else in this review — the backup contributes nothing.

### 1.8 The droplet

- **What it holds:** precompute static files, deployed frontend, droplet API. Per standing architecture, nothing authoritative.
- **Assessment: correct by design and confirmed by the succession doc.** No action. Its only memory role is negative — a successor must be told *not* to treat it as a source, which SUCCESSION.md and project memory both do.

---

## 2. `SUCCESSION.md` Assessed Against the Memory Substrate

The document was read in full. It is honest and usefully current — its single-points list already names "local server and SQLite data store," "large local data artifacts and backups," and, notably, "repository institutional memory spread across many docs." Its continuity direction ("prefer open formats and exportable data," "make recovery... executable by a qualified successor") is exactly right.

**But it covers the memory substrate only partially, and the part it misses is the part this review found broken:**

- It does not mention that `institution/` — including SUCCESSION.md itself — is untracked and unbackuped. The succession plan is itself a single point of failure by its own criteria.
- It does not mention the three AI-side memory stores (1.3, 1.4, 1.5) at all. A successor executing SUCCESSION.md faithfully would never discover them, losing the incident history and standing constraints that make the system operable without its current stewards.
- It frames continuity mostly around infrastructure and authority (founder console access, droplet, vendors). Leadership succession is addressed; **memory succession is named in one line and mapped nowhere.**

Verdict: SUCCESSION.md is sound as far as it goes; it needs a "Memory Substrate" section enumerating every store in §1 with its location, format, authority level (authoritative / derived / cache), and recovery path. That amendment is small and this review provides the raw material.

---

## 3. Findings Against the Charter's Single-Points List

| Single point | Where it bites | Severity |
|---|---|---|
| One founder | GitHub-org recoverability (1.1); all provider consoles (already in SUCCESSION.md); sole knowledge that stores 1.3–1.5 exist | High, partly known |
| One server | `institution/` (sole copy), AI memory, gstack state, mempalace | **Critical for 1.2**, high for 1.3–1.4 |
| One vendor | GitHub (mitigated by git's portability); Google Drive offsite (single offsite vendor); AI-vendor path conventions (1.3) | Moderate |
| One AI model | mempalace embeddings (1.5) — acceptable only if declared a cache | Low, if documented |
| One storage format | Chroma binary (1.5); everything else is Markdown/JSONL/SQL — good | Low |
| One deployment | Droplet holds nothing authoritative — correctly avoided | None |
| One undocumented workflow/reasoning process | Existence of 1.3/1.4/1.5 documented nowhere in the repo; silent-skip behavior of offsite backup; GitHub recovery procedure | High |

---

## 4. Recommendations, Prioritized (Smallest First)

Each carries the classification Amendment 1 requires. None was executed; items 1, 3, and 6 in particular are founder decisions.

1. **Track `institution/` in git.** One `git add`, one commit, one push — the single highest-leverage preservation act available to the institution, converting its constitutional layer from one copy to two-plus-history overnight. **Classification: Operational Practice** (the act), serving an **Architecture Principle** (authoritative institutional memory lives in the repo, in open formats). **Founder decision** — repo writes are founder-gated, and the founder must decide whether the library's visibility should match the repo's visibility (if the repo is or ever becomes public). If there is any hesitation about visibility, a private `daanaa-institution` repo is the fallback; one disk is the only unacceptable option.
2. **Export AI session memory into the repo in vendor-neutral form.** The 1.3 store is already Markdown; a periodic copy (e.g., `docs/memory-export/` or `institution/memory/`) with a dated header would make the operational memory survive vendor, machine, and model changes. A small sync script keeps it honest. **Classification: Operational Practice.**
3. **Extend backup scope beyond the database.** Add `institution/`, the 1.3 memory directory, and `~/.gstack/projects/meritgiving/` to `daanaa_backup.sh` (a tar step beside the SQL dump; a few lines). Even after Recommendation 1, backups provide the third copy and cover the interval between commits. **Classification: Operational Practice.** Script change = backend code change; per this review's mandate it was not made. **Founder decision** to schedule.
4. **Make the offsite push fail loudly.** When rclone or the remote is absent, the script should report `STATUS=warn`, not silently skip. Three lines. **Classification: Operational Practice** (and a direct application of the logged lesson that unverified backup paths fail silently).
5. **Add a "Memory Substrate" section to SUCCESSION.md** enumerating every store in §1 — location, format, authoritative-or-derived, recovery path — so a successor can find all institutional memory from one document. **Classification: Operational Practice**, upgrading SUCCESSION.md toward the **Architecture Principle** in item 1.
6. **Document the GitHub recovery path.** Record (without credentials, per standing rules) who besides the founder can recover the `daanaa-hq` organization, or establish that no one can and decide whether that is acceptable. **Classification: Operational Practice. Founder-only** — no one else can answer it.
7. **Declare mempalace non-authoritative, in writing.** One paragraph in SUCCESSION.md or a README in the store: "derived cache; rebuildable from repo + memory export; nothing may live only here." Then spot-audit `known_entities.json` against durable sources once. **Classification: Temporary Decision** (the store's status may change; the declaration prevents silent drift meanwhile).
8. **Audit gstack decisions/learnings against DECISIONS.md/LESSONS.md once**, promoting anything found only in the tool store into the repo files. Thereafter rely on Recommendation 3's backup coverage. **Classification: Operational Practice.**
9. **Consider a second offsite location for the constitutional layer** (the `institution/` tree is small; even a periodic encrypted copy to a second provider or physical medium ends the single-offsite-vendor point). **Classification: Future Research** — worth costing before adopting; flag any spend to the founder per standing cost-mindfulness rules.

## 5. Findings Only the Founder Can Decide

1. Whether and where to track `institution/` (main repo vs. private repo; visibility question) — Recommendation 1.
2. Scheduling the backup-script scope change and fail-loud fix (backend change; also touches the founder's standing cost/scope awareness) — Recommendations 3–4.
3. GitHub organization recovery: whether a second trusted human should hold access, and who — Recommendation 6.
4. Whether AI memory export belongs in the repo (visibility of operational history) — Recommendation 2.
5. Whether to fund a second offsite vendor — Recommendation 9.

## 6. Closing Observation

Library 008 states that "knowledge held only in a founder's head is a debt the institution has not noticed it owes." This review's finding is the same sentence with one word changed: knowledge held only on a founder's *disk* is a debt the institution had not noticed it owes — and unlike the head, the disk version is repayable this week, mostly with tools already in place. The institution's memory practices are not weak; they are simply newer than its memory. The library outgrew its preservation in a single month. That is a good problem, briefly.

The work continues.
