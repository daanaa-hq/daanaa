# AI Memory Migration — Source Inventory

**Date Started:** 2026-07-11  
**Authority:** Founder Ruling 2026-07-11, item 2  
**Status:** Planning phase

---

## Source Store Analysis

### Primary Source: ~/.claude/projects/-home-akbar-meritgiving/memory/

**Location:** `~/.claude/projects/-home-akbar-meritgiving/memory/`

**Current state:**
- ~80 markdown files
- ~584KB total
- MEMORY.md index + ~80 topic files
- Files organized by category: incidents, projects, feedback, sessions, references

**Content categories identified:**

| Category | Files Est. | Status | Action |
|----------|-----------|--------|--------|
| Incident post-mortems | ~8 files | REVIEW | Extract root causes + prevention rules → INCIDENTS.md |
| Project status snapshots | ~30 files | REVIEW | Extract decisions + lessons → DECISIONS.md, LESSONS.md |
| Standing feedback/preferences | ~12 files | REVIEW | Extract institutional rules → STANDING_CONSTRAINTS.md |
| Architecture decisions | ~15 files | REVIEW | Extract reasoning → DECISIONS.md + link to code |
| Session summaries | ~10 files | SCAN | Extract key outcomes; discard transactional details |
| References/pointers | ~5 files | KEEP | Preserve as-is (links, external systems) |

**Estimated durable content:** 60-70% of current store (360-410KB → 220-250KB after curation)

---

## Secondary Sources

### ~/.gstack/projects/meritgiving/

**Location:** `~/.gstack/projects/meritgiving/checkpoints/`, `decisions.jsonl`, `learnings.jsonl`

**Status:** Needs inventory

**Expected content:**
- Checkpoint history (numbered, timestamped)
- Decision logs (JSONL format)
- Learning logs (JSONL format)

**Action:** Audit whether high-value decisions are already in root `DECISIONS.md`; backport missing ones.

---

### Root DECISIONS.md and LESSONS.md

**Location:** `/home/akbar/meritgiving/DECISIONS.md`, `/home/akbar/meritgiving/LESSONS.md`

**Status:** Already in git

**Action:** Cross-reference institution/ai-memory/ with these. If memory repeats what's in root, link instead of duplicate.

---

## Security Scan Checklist

Before any file enters institution/ai-memory/:

- [ ] No AWS credentials or access keys
- [ ] No Google API keys or service account JSON
- [ ] No GitHub tokens or deploy keys
- [ ] No personal email addresses (except alias@daanaa.org)
- [ ] No home server paths (or anonymized as `/home/akbar` → `$HOME`)
- [ ] No vendor-specific API tokens
- [ ] No database credentials
- [ ] No founder personal information
- [ ] No nonprofit personal data (donor names, addresses, etc.)
- [ ] No machine-specific UUIDs or hardware identifiers
- [ ] No debug output with embedded secrets
- [ ] No raw session transcripts containing above

**Tool:** `grep -r -E '(AKIA|ghp_|Bearer|api_key|password|secret|token|credential)' institution/ai-memory/` (post-migration verification)

---

## Size Budget

**Target:** 250KB max (compressed: ~40KB)

**Rationale:** Fits in standard archival media, swift to review, easy to migrate to new systems.

---

## Timeline

- **2026-07-11:** Source inventory (this file) + start manual extraction
- **2026-07-12:** Complete INCIDENTS.md + STANDING_CONSTRAINTS.md from source
- **2026-07-13:** Complete DECISIONS.md + LESSONS.md extraction
- **2026-07-14:** OPEN_QUESTIONS.md + MEMORY_MANIFEST.md
- **2026-07-15:** Security scan + final review
- **2026-07-16:** Commit to git + close migration

---

## Migration Log

Each extraction session records:
- Date and time
- Files reviewed
- Items extracted
- Items excluded (with reason)
- High-risk findings (if any)

See `migration_log.md` for session-by-session detail.
