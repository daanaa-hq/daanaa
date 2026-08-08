# Daanaa Backup & Recovery Plan

Last verified end to end: **2026-08-08**. Re-verify quarterly (see *Restore drills*).

Four systems evolved separately and overlap. This is the single description of what
exists, what each is for, and what to do when something is lost.

---

## The insight that shapes everything

`merit_registry.db` is ~23GB, but almost none of it is irreplaceable:

| Component | Size | Recoverable how |
|---|---|---|
| `org_embeddings` | 8.77GB | recompute on the local GPU |
| `page_cache` | 3.86GB | disposable |
| v6 assignments + indexes | ~5.0GB | re-run the scorer |
| FTS, classifications | ~1.5GB | derived |
| `registry_enriched` (public IRS/ProPublica fields) | ~1.6GB | re-ingest from IRS BMF + ProPublica |
| **Human input** (`org_claims`, `volunteer_interest`, …) | **7 rows** | **nothing — irreplaceable** |
| **Crawl + GPU output** (2.06M missions, 461K websites, 68K donate links) | **~79MB compressed** | **weeks of GPU and crawl time** |

So the question is never "how do we store 23GB nightly." It is **"what costs money and
time to recreate."** That is ~79MB, plus 7 rows.

---

## The four layers

### 1. Local — fast recovery
`scripts/backup_strategy.sh` · cron 02:00 daily
- Hourly + daily `VACUUM INTO` copies to `backups/production/`
- **Not `.backup`** — that API restarts on concurrent writes and can never finish against
  a live DB (see LESSONS.md 2026-08-08). `VACUUM INTO` completes in ~198s.
- Every written file is structurally verified (`quick_check`) and row-count matched.
  A corrupt copy is deleted, never retained.
- Retention: 7 daily / 3 hourly, and it **refuses to prune unless an offsite copy is
  confirmed**. Warns below 40GB free.

### 2. Critical tables + weekly full — offsite, two providers
`scripts/ops/daanaa_backup.sh` · cron 02:30 daily
- Nightly `.dump` of `org_claims`, `org_activity`, `feedback`, `waitlist` (~1.7KB)
- **Sundays:** full DB → `s3://daanaa-backups/home-server/full/` (~12–13GB gzipped)
- Also pushed to Google Drive via rclone (`daanaa-backup:` remote)

### 3. Core enrichment export — offsite, daily
`scripts/ops/backup_core_export.sh` · cron 03:15 daily (Sundays include a restore drill)
- ~79MB of EIN → mission, website, donate_url + statuses
- Verifies the **remote** copy by SHA-256 round-trip, not just "upload returned 0"
- 30 daily + 12 monthly in `s3://daanaa-nonprofit-data/backups/core/`
- **Cost ≈ $0.06/month.** Glacier was rejected: it saves ~$0.03 and adds retrieval
  delay plus a 90-day minimum-storage charge that costs more at this size.

### 4. DigitalOcean snapshots — whole machine
Manual/periodic. Restores the droplet in minutes, but lives with the same provider as
production, so it is not independent.

---

## Recovery playbooks

**Lost a few rows / bad write** → restore from the newest local `backups/production/*.db`.
Minutes.

**Lost the database, machine intact** → newest verified local daily. Minutes.

**Lost the machine** → weekly full from `s3://daanaa-backups` or Google Drive, then replay
the daily core export for enrichment newer than that full. Hours.

**Lost machine and provider** → S3 core export (79MB) + re-ingest public IRS/ProPublica
data + recompute embeddings, v6 scores and FTS locally. Days, but nothing bought is lost.

**Droplet only** → rebuild from `scripts/ops/precompute_live.sh` output and redeploy; the
droplet holds no unique state. Proven 2026-08-08 by rebuilding it from bare.

---

## Restore drills

Weekly (automated): the Sunday core export downloads its own artifact, loads it into a
throwaway SQLite DB, and asserts row counts. Failure is loud.

Quarterly (manual, **not yet performed** — the honest gap in this plan): rebuild a working
database from the S3 core export plus re-ingested public data. The export half is drilled;
the *rebuild* half has never been exercised end to end. Until it is, layer 4 recovery is a
plausible plan rather than a proven one.

---

## Known gaps

1. **The full-rebuild path is untested.** See above. This is the weakest link.
2. **2026-08-04, 05, 06 have no backup** and never will — `.backup` never completed on
   those days. Not recoverable; recorded so the gap is not mistaken for data loss.
3. **Overlap is unresolved.** Layers 2 and 3 both carry missions and websites. That is
   redundancy, not waste, but the three systems should probably converge.

---

## Rules

- **A backup that has not been restored is a belief, not a backup.** Six 2026-08-01
  backups passed a size check while being unreadable (`file is not a database`).
- **Never let a verification pass by timing out.** Report verified / inconclusive /
  corrupt, and never silently promote the second to the first.
- **Never prune without a confirmed offsite copy.**
- **Check retention against capacity.** A policy needing 660GB on a disk with 105GB free
  is a scheduled outage.
