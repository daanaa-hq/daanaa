# Infrastructure Execution Checklist

**Status:** Ready to execute  
**Blocked on:** DigitalOcean API token  
**Timeline:** Week 1 (2026-07-12 to 2026-07-18)

---

## Pre-Execution (Ready Now)

- [x] DR-2026-07-12-007 decision committed to git
- [x] INFRASTRUCTURE_PROVISIONING_2026_07.md created (full plan)
- [x] AWS credentials verified in `.env` (S3 + CloudFront)
- [x] Alert email confirmed (akbar.khowaja@gmail.com)
- [ ] DigitalOcean API token provided to `.env` (WAITING)

---

## Week 1 Execution (Starts When Token Provided)

### Task 1.1: PostgreSQL Provisioning
- [ ] Create DigitalOcean managed DB (db-s-1vcpu-1gb, $35/mo)
- [ ] Enable HA, backups, connection pooling
- [ ] Get connection string → test connectivity
- [ ] Create read-only replica
- Expected: 20 minutes

### Task 1.2: Redis Provisioning
- [ ] Create DigitalOcean managed Redis (db-s-1vcpu-256mb, $25/mo)
- [ ] Configure eviction, auth, private network
- [ ] Get connection string → test connectivity
- Expected: 15 minutes

### Task 1.3: S3 + CloudFront Setup
- [ ] Create S3 bucket (daanaa-precompute-prod)
- [ ] Configure encryption, versioning, CORS
- [ ] Create CloudFront distribution
- [ ] Point cdn.daanaa.org DNS
- [ ] Upload test file → verify <100ms latency globally
- Expected: 30 minutes

### Task 1.4: Backups + Monitoring
- [ ] Update `daanaa_backup.sh` for Postgres
- [ ] Setup DigitalOcean alerts (CPU, memory, disk, DB connections)
- [ ] Configure email alerts
- [ ] Test: trigger alert manually
- Expected: 20 minutes

### Task 1.5: Health Check Endpoint
- [ ] Create `/api/health/infrastructure` endpoint
- [ ] Returns: Postgres ✓, Redis ✓, S3 ✓, Backups ✓
- [ ] Add to monitoring dashboard
- Expected: 15 minutes

**Week 1 Total:** ~2 hours active execution, fully automated

---

## Week 2 Execution (Scheduled 2026-07-19)

### Task 2.1: SQLite → Postgres Migration
- [ ] Export SQLite data to CSV
- [ ] Import to Postgres staging
- [ ] Validate row counts
- [ ] Performance test: 1000 concurrent queries
- Expected: 3 hours

### Task 2.2: Application Layer Updates
- [ ] Update daanaa_api.py connection string
- [ ] Update overnight_pipeline.py data source
- [ ] Update test fixtures
- [ ] Verify all APIs work
- Expected: 2 hours

### Task 2.3: Failover Test
- [ ] Kill Postgres → verify reconnect to replica
- [ ] Restore → verify no data loss
- [ ] Document recovery procedure
- Expected: 1 hour

**Week 2 Total:** ~6 hours, includes testing

---

## Week 3 Execution (Scheduled 2026-07-26)

### Task 3.1: Pre-Launch Checklist
- [ ] Smoke tests (health, search, org pages, precompute)
- [ ] Performance baseline (p50/p95/p99)
- [ ] 48-hour uptime without error
- [ ] Restore from backup → verify completeness
- Expected: 2 hours

### Task 3.2: Public Launch
- [ ] daanaa.org goes live
- [ ] Announce to advisors + early users
- [ ] Monitor: errors, latency, connections
- Expected: 1 hour

### Task 3.3: Monitoring Dashboard
- [ ] Create dashboard (latency, search, cache, DB, backups)
- [ ] Log all decisions in git
- Expected: 1 hour

**Week 3 Total:** ~4 hours, then monitoring

---

## Success Criteria (End of Week 3)

- ✅ All 5 services provisioned and tested
- ✅ Data migrated (zero downtime)
- ✅ Monitoring + alerts live
- ✅ Backup verified + restorable
- ✅ 99.9% uptime SLA met
- ✅ <100ms p95 latency on search/org pages
- ✅ Cost: $100/mo confirmed

---

## Next Action (From Founder)

Provide DigitalOcean API token:

**Option A (Quick):** Reply with token  
**Option B (Secure):** Add to `.env.infrastructure`:
```bash
export DIGITALOCEAN_TOKEN="<your-token>"
```

Once provided, I execute Week 1 immediately (no further delays).

---

**Awaiting token. Ready to move fast.** 🚀
