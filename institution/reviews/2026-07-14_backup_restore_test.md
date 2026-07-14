# Backup Restore Test Review - 2026-07-14

## Document Control

| Field | Value |
|---|---|
| Purpose | Record evidence for F-008 / R-004 backup restore verification. |
| Responsible role | Stewardship Systems Agent; Operations owner for recurring execution. |
| Authority level | Operational evidence record; not a provider-console audit. |
| Review trigger | Monthly restore test, backup script change, database migration, provider change, or incident. |
| Editable status | Append-only for results; corrections should preserve prior result history. |
| Dependencies | `scripts/ops/daanaa_backup.sh`, `infrastructure/backup/test_restore.sh`, `scripts/test_backup_robustness.sh`, `institution/SUCCESSION.md`, `institution/RISK_REGISTER.md`. |

## Scope

This review validates that the latest local full registry backup can be restored into a temporary SQLite database and passes integrity checks.

This review does not prove that Google Drive / `rclone` offsite storage is reachable from production, that provider credentials are valid, or that a disaster recovery restore has been performed from offsite media.

## Commands Executed

```bash
bash scripts/test_backup_robustness.sh
bash infrastructure/backup/test_restore.sh
```

Both commands initially hit the local sandbox loopback failure before execution and were rerun with explicit escalation. No production deployment, live database mutation, provider-console action, DNS change, or credential output occurred.

## Results

| Check | Result | Evidence |
|---|---|---|
| Backup robustness suite | PASS | 12 checks passed, 0 failed. |
| Latest full backup found | PASS | `full_20260712.db.gz`. |
| Restore target | PASS | Temporary restored DB at `/tmp/merit_registry_restore_test.db`; removed by script after success. |
| Decompression | PASS | Restore time 56,829 ms, below 10 minute target RTO. |
| SQLite integrity | PASS | `PRAGMA integrity_check` returned `ok`. |
| Registry sanity count | PASS | Restored DB contained 2,042,897 orgs. |
| Backup age | PASS | 44 hours at test time; weekly full snapshot freshness threshold is 216 hours. |

## Interpretation

F-008 is partially closed:

- Local full-backup restore is verified.
- Backup script robustness controls are verified by local static tests.
- Offsite restore remains unverified because this review did not pull a backup from `daanaa-backup:` or test Google Drive credentials.

## Remaining Work

1. Run a non-destructive offsite list check:

```bash
rclone listremotes
rclone lsf daanaa-backup:daanaa-backups/full --max-depth 1
rclone lsf daanaa-backup:daanaa-backups/critical --max-depth 1
```

2. Run a true offsite restore drill to `/tmp` using the newest offsite full snapshot.
3. Record the offsite result in a new dated review under `institution/reviews/`.
4. Add this restore test to the monthly operations rhythm.
5. Keep `R-004` open until offsite restore is verified.

## Stewardship Notes

- A backup is not complete until restore has been tested.
- A local restore test reduces database-corruption risk but does not remove provider, credential, or offsite-media risk.
- No secret values were printed or recorded in this review.
