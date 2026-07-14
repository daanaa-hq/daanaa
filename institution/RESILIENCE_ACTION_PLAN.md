# F-008/F-009 Resilience Action Plan

**Status:** Ready for execution · Awaiting second admin identification  
**Owner:** Founder (name second admin) + Daanaa steward

---

## F-008: Offsite Backup Restore Test

### Why This Matters
Production database lives in `/home/akbar/meritgiving/data/merit_registry.db` (1.7GB).
Local backup chain tested at 56.829s restore time ✓  
**Gap:** Offsite copy verification is incomplete. If home server fails + local backups are lost, can we recover from Google Drive/rclone?

### Action: Live Provider Drill

**Prerequisites:**
- Offsite backup provider is Google Drive + rclone
- Full backup file: `full_20260712.db.gz` (uploaded ~2GB)
- Restore script: `scripts/ops/daanaa_backup.sh restore`

**Procedure:**
1. Pull latest backup from Google Drive to `/tmp/restore_test.db.gz`
2. Decompress and run `sqlite3 restore_test.db ".schema"` to verify integrity
3. Count rows: `SELECT COUNT(*) FROM registry_enriched` — should be ~2.04M
4. Restore time measurement (start-to-queries-working)
5. Delete test restore; confirm remote backup still intact
6. Document restore time and any issues

**When:**
- After second admin is identified (they verify they can access Google Drive)
- Run quarterly (same cadence as STEWARDSHIP.md quarterly self-audit)

**Success Criteria:**
- Restore time < 10 minutes
- Row count matches production
- Integrity check passes
- No data corruption

---

## F-009: Provider Access Map & Succession Testing

### Current State (from audit)

**Critical systems documented:**
| System | Provider | Owner | Status |
|--------|----------|-------|--------|
| Git / Code | GitHub | Akbar | Single point of failure |
| Droplet / API | DigitalOcean | Akbar | Single point of failure |
| Domain | Namecheap | Akbar | Single point of failure |
| Backups | Google Drive + rclone | Akbar | Single point of failure |
| Firebase | Google | Akbar | Single point of failure |
| Cloudflare DNS | Cloudflare | Akbar | Single point of failure |

### Action: Add Second Admin to Critical Systems

**Once second admin is identified:**

1. **GitHub**
   - [ ] Add as organization owner
   - [ ] Enable 2FA on their account
   - [ ] Test: they can pull code, create branches, merge PRs
   - [ ] Test: they can access organization secrets

2. **DigitalOcean Droplet (162.243.97.179)**
   - [ ] Add SSH public key to `/root/.ssh/authorized_keys`
   - [ ] Test: they can SSH in as root
   - [ ] Test: they can restart gunicorn (systemctl restart daanaa_api)
   - [ ] Test: they can view logs (journalctl -u daanaa_api)

3. **Domain Registrar (daanaa.org on Namecheap)**
   - [ ] Add as secondary contact with admin access
   - [ ] Test: they can view DNS settings
   - [ ] Test: they can access renewal settings

4. **Google Drive Backups**
   - [ ] Share backup folder with second admin's account
   - [ ] Test: they can download `full_20260712.db.gz`
   - [ ] Test: they can list all backup files

5. **Firebase Console**
   - [ ] Add as secondary project owner
   - [ ] Test: they can view wallet_sync table
   - [ ] Test: they can view user authentication logs

6. **Cloudflare**
   - [ ] Add as secondary account admin
   - [ ] Test: they can view DNS records
   - [ ] Test: they can modify SSL settings

### Succession Testing Protocol

**Simulate: Akbar is unreachable for 24 hours**

1. **Hour 0–6:** Second admin attempts phone/email to Akbar (should get no response)
2. **Hour 6–12:** Second admin uses emergency procedures to access all systems
   - [ ] SSH into droplet
   - [ ] Verify gunicorn is running (systemctl status daanaa_api)
   - [ ] Check logs for errors
   - [ ] Verify homepage loads (curl http://localhost:5000/)
3. **Hour 12–24:** Document any access issues or missing credentials
4. **Post-test:** Update this document with any gaps

### Success Criteria

✅ Second admin can access all 6 systems within 30 minutes  
✅ Second admin can verify production is running  
✅ All credentials and access paths are documented  
✅ No gaps in the access chain

---

## Relationship to Other Findings

- **F-001 (GATE 8):** Firewall verified; no data exfiltration during succession
- **FD-006:** Second admin identification unlocks F-008/F-009 execution
- **STEWARDSHIP.md:** Quarterly self-audit will include "Did we test succession this quarter?" question

---

## Timeline

| Date | Milestone | Owner |
|------|-----------|-------|
| 2026-07-14 | Second admin identified | Founder |
| 2026-07-14 | Access provisioned | Steward + Second Admin |
| 2026-07-15 | Succession test complete | Second Admin |
| 2026-07-15 | F-008/F-009 marked complete | Steward |
| Q3 2026 | Quarterly succession re-test | Steward |

---

**Next step:** Founder identifies second admin; Steward provisions access and runs succession test.

