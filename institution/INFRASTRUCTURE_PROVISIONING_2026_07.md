# Infrastructure Provisioning: B-Lite Phase 1 & 2

**Authority:** DR-2026-07-12-007  
**Status:** In Progress (Week 1 start: 2026-07-12)  
**Owner:** AI Steward (Autonomous), Founder oversight  

---

## Phase 1: Launch ($100/mo) — Weeks 1–3

### Week 1: Provision & Configure (2026-07-12 to 2026-07-18)

#### PostgreSQL Managed Database ($35/mo)

**Task 1.1: Provision DigitalOcean Managed Database**
- [ ] Create DigitalOcean managed PostgreSQL instance (db-s-1vcpu-1gb, $35/mo)
- [ ] Configure:
  - Automatic backups (daily, 7-day retention)
  - High availability (automatic failover)
  - Connection pooling (pgbouncer)
  - Private network (internal DigitalOcean network only)
- [ ] Create read-only replica (for future disaster recovery testing)
- [ ] Get connection string + test connectivity from home server

**Task 1.2: Schema Setup**
- [ ] Port existing SQLite schema to Postgres (structure only)
- [ ] Enable necessary extensions: `uuid-ossp`, `pg_trgm` (for FTS)
- [ ] Create indexes for common queries (org lookups, search, filtering)
- [ ] Test schema on replica

#### Redis Managed Cache ($25/mo)

**Task 1.3: Provision DigitalOcean Managed Redis**
- [ ] Create DigitalOcean managed Redis instance (db-s-1vcpu-256mb, $25/mo)
- [ ] Configure:
  - Eviction policy: `allkeys-lru`
  - Password authentication (strong, random)
  - Private network access only
  - Automatic backups
- [ ] Get connection string; test connectivity

**Task 1.4: Cache Strategy**
- [ ] Define cache keys for common queries (org detail, search results, stats)
- [ ] Set TTLs: org data (10 min), search results (5 min), stats (1 hour)
- [ ] Test cache invalidation on data updates

#### S3 + CloudFront CDN ($20/mo)

**Task 1.5: Setup AWS S3 + CloudFront**
- [ ] Create S3 bucket: `daanaa-precompute-prod` (us-east-1)
- [ ] Configure bucket:
  - Versioning enabled
  - Server-side encryption (AES-256)
  - Public read access via CloudFront only (OAI)
  - CORS headers for browser access
- [ ] Create CloudFront distribution:
  - Origin: S3 bucket
  - Cache behavior: 1 hour for org detail pages, 24 hours for static
  - Compress: gzip + brotli
  - HTTPS only
- [ ] DNS: Point `cdn.daanaa.org` to CloudFront
- [ ] Test: Upload sample precompute, verify 200ms global latency

#### Automated Backups ($10/mo)

**Task 1.6: Backup Strategy**
- [ ] Update `daanaa_backup.sh` to backup Postgres (not SQLite)
  - `pg_dump` to S3 daily at 02:30 CST
  - Encrypt backups (gpg)
  - Verify backup size on S3
  - Maintain 30-day rolling window
- [ ] Test restore: `pg_restore` from S3 backup to test DB
- [ ] Document recovery time objective (RTO): <15 min

#### Basic Monitoring ($10/mo)

**Task 1.7: DigitalOcean Monitoring + Alerts**
- [ ] Configure DigitalOcean monitoring:
  - CPU + memory alerts (>80%)
  - Disk space alerts (>85%)
  - Database connection count alerts
  - Redis memory alerts
- [ ] Setup email/Slack alerts to founder
- [ ] Custom health check: `/api/health` returns database + cache status
- [ ] Log all monitoring decisions in DECISIONS.md

**Week 1 Summary:**
- [ ] All 5 services provisioned and tested
- [ ] Connection strings documented (encrypted, stored in `.env`)
- [ ] Backup + monitoring live
- [ ] Estimated cost confirmed: $100/mo

---

### Week 2: Data Migration (2026-07-19 to 2026-07-25)

#### Migrate SQLite → Postgres (Zero Downtime)

**Task 2.1: Blue-Green Migration**
- [ ] Export SQLite data to CSV (org profiles, FTS index)
- [ ] Import CSV into Postgres staging DB
- [ ] Verify row counts match (SQLite → Postgres)
- [ ] Run validation queries: org lookups, search, aggregate stats
- [ ] Performance test: 1000 concurrent queries to Postgres (verify latency)

**Task 2.2: Application Layer**
- [ ] Update `daanaa_api.py` connection string: SQLite → Postgres
- [ ] Update `scripts/overnight_pipeline.py`: Postgres data source
- [ ] Update `scripts/build_fts_index.py`: Use Postgres FTS (tsvector)
- [ ] Update all test fixtures to use Postgres test DB

**Task 2.3: Failover Test**
- [ ] Kill Postgres instance; verify application reconnects to replica
- [ ] Restore original instance; verify no data loss
- [ ] Document failover recovery procedure

**Task 2.4: Redis Cache Warming**
- [ ] Pre-populate cache with hot data (top 1000 orgs, common searches)
- [ ] Monitor cache hit rate (target: >90% for common queries)
- [ ] Tune eviction policy if needed

**Week 2 Summary:**
- [ ] SQLite data fully migrated to Postgres
- [ ] Failover + replica tested
- [ ] APIs working on Postgres + Redis
- [ ] Zero downtime during migration

---

### Week 3: Launch (2026-07-26 to 2026-08-01)

#### Soft Launch (Beta)

**Task 3.1: Pre-Launch Checklist**
- [ ] Smoke tests: API health, search, org detail pages, precompute serving
- [ ] Performance baseline: p50/p95/p99 latencies documented
- [ ] Uptime: 48 hours without error on production stack
- [ ] Backups: Restore from backup, verify completeness

**Task 3.2: Public Launch**
- [ ] Website goes live on daanaa.org
- [ ] Announce to advisors + early users
- [ ] Monitor: error rates, latency, database connections

**Task 3.3: Monitoring Dashboard**
- [ ] Create dashboard showing:
  - API latency (p50/p95/p99)
  - Search quality (queries/day, errors)
  - Cache hit rate
  - Database connections
  - Backup status + last successful restore
- [ ] Log all infrastructure decisions in git

**Week 3 Summary:**
- [ ] Phase 1 ($100/mo) live and stable
- [ ] All monitoring + alerting working
- [ ] Backup verified + tested
- [ ] Ready for early users

---

## Phase 2: Upgrade ($130/mo more) — Week 8+ (Conditional)

### Upgrade Trigger (Week 8 Decision Gate)

**Upgrade if ANY of:**
1. ✅ **3+ advisors publicly committed**
2. ✅ **1+ major partnership announced** (e.g., HealthyOrgs)
3. ✅ **5K+ early users with strong engagement**

**Otherwise:** Hold at Phase 1 ($100/mo) and re-evaluate at week 16.

### If Triggered: Elasticsearch ($80/mo)

**Task 4.1: Elasticsearch Provisioning**
- [ ] Provision Elastic Cloud (us-east-1, medium tier, $80/mo)
- [ ] Migrate FTS index from Postgres → Elasticsearch
- [ ] Configure:
  - Synonym expansion (synonyms.txt)
  - Typo tolerance (fuzzy matching)
  - Custom ranking (relevance scoring)
- [ ] A/B test: Postgres FTS vs. Elasticsearch; measure search quality

**Task 4.2: Application Integration**
- [ ] Update search endpoint: route to Elasticsearch
- [ ] Fallback: if Elasticsearch unavailable, fall back to Postgres FTS
- [ ] Monitor: search latency, relevance metrics

### If Triggered: Datadog ($50/mo)

**Task 4.3: Datadog Integration**
- [ ] Instrument API: APM (Application Performance Monitoring)
- [ ] Logs: centralize application + database logs
- [ ] Metrics: custom dashboards for adoption, search quality, errors
- [ ] Alerts: escalate errors, latency spikes to founder

**Task 4.4: Observability**
- [ ] Distributed tracing: see full request flow (API → DB → Cache)
- [ ] Error tracking: stack traces + reproduction steps
- [ ] Performance profiling: identify bottlenecks

**Week 8–9 Summary:**
- [ ] Phase 2 ($230/mo total) live
- [ ] Search quality improved (Elasticsearch)
- [ ] Full observability (Datadog)
- [ ] No downtime during upgrade

---

## Success Criteria

### Phase 1 (Weeks 1–3)
- ✅ All services provisioned and tested
- ✅ Data migrated (zero downtime)
- ✅ Monitoring + alerts live
- ✅ Backup verified + restorable
- ✅ 99.9% uptime SLA met
- ✅ <100ms p95 latency on search/org pages

### Phase 2 (Weeks 8–9, conditional)
- ✅ Elasticsearch indexed, A/B tested
- ✅ Datadog integrated, dashboards live
- ✅ No performance regression
- ✅ Search quality improved (fuzzy + ranking)

---

## Cost Summary

| Phase | Timeline | Services | Monthly Cost | Status |
|---|---|---|---|---|
| **Phase 1** | Weeks 1–3 | Postgres, Redis, S3/CDN, Backups, Monitoring | $100/mo | **EXECUTING NOW** |
| **Phase 2** | Weeks 8–9 (conditional) | Add Elasticsearch + Datadog | +$130/mo = $230/mo total | Pending week 8 trigger |

---

## Logs & Decisions

- All provisioning decisions logged in `institution/DECISION_LOG.md`
- All infrastructure tests documented in `institution/INFRASTRUCTURE_TESTING_LOG.md` (created)
- All unexpected issues captured in `institution/learning/incidents/` (if applicable)

---

**Execution starts:** 2026-07-12  
**Phase 1 complete:** 2026-08-01 (target)  
**Phase 2 decision:** Week 8 (2026-08-23)  

