
## 2026-08-11: Backup Storage Mistake

**Symptom:** Disk 100% full with 340GB of database backups on local SSD.

**Root cause:** Backups should be in S3 for durability, not taking up local storage. SSD failure would lose both data AND backups.

**Fix applied:** Deleted local backups, freed 340GB, implemented S3-first backup policy.

**Preventing rule:** "Backups live off-box (S3/cloud), never on production SSD. Local SSD = operations only."

