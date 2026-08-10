# Discovery Pipeline Startup — 2026-07-17 13:29 Central

**Status:** LIVE ✅

---

## Processes Started

| Process | PID | Started | Purpose |
|---------|-----|---------|---------|
| `embed_server.sh` | (llama-server) | 13:20 | Website ownership verification (mxbai-embed-large) |
| `discovery_daemon.py` | 163139, 2268159 | 2026-07-16 | 24/7 link extraction (listening mode) |
| `web_finder_agent.py` | 2257840 | 13:20 | Finding 10K websites (domain guessing + embedding verify) |
| `phase_orchestrator.py` | 2257841 | 13:20 | Auto-phase detection (saturation monitoring) |
| `nonprofit_discovery_orchestrator.py` | cron | 11:00 Central daily | Orchestrated multi-source batch |

---

## Infrastructure

**Embed Server (11436)**
- Model: mxbai-embed-large (639MB)
- Purpose: Website ownership verification via embedding similarity
- Headroom: Available for concurrent queries
- Health: ✅ OK

**LLM Server (11437)**
- Model: Qwen2.5-32B-Instruct-Q4_K_M (65GB)
- Purpose: Mission generation + cause tag extraction (tomorrow 02:30)
- Headroom: Available (will run nightly)
- Health: ✅ Running

**CPU (Ryzen 9700X)**
- Load: 13/32 threads (~40%)
- Headroom: 19 threads available
- Scaling: web_finder 8→16 workers possible

**Storage**
- Registry DB: 1.2GB
- 990 XMLs: 12GB
- Precompute: ~4GB
- Available: ~480GB

---

## Phase Timeline

### T+0 (Now: 13:29 Central)
- [x] Embed server started
- [x] web_finder_agent running (10K orgs, high-revenue first)
- [x] phase_orchestrator watching for saturation
- [x] discovery_daemon listening (standby)
- [x] discovery_orchestrator scheduled (11:00 Central daily)

### T+4h (17:30 Central)
- **Expected:** web_finder finds 1–5K new websites
- **Action:** discovery_daemon auto-wakes on each new website
- **Outcome:** Donation/volunteer links queued for deployment

### T+13h (02:30 Central next day)
- **Trigger:** Overnight pipeline runs
- **Actions:**
  - fetch_org_websites() — caches HTML from all 111K+ discovered sites
  - run_mission_generation() — AI extracts/generates missions
  - generate_cause_tags_batch() — categorizes orgs by cause
  - run_cohort_context() — groups by financial metrics
- **Outcome:** Missions + cause tags updated for all new websites

### T+24h (13:30 Central 2026-07-18)
- **Discovery orchestrator runs** (scheduled 11:00 Central)
- **Sources checked in order:**
  1. IRS 990 XMLs (extract_990_fields)
  2. web_finder next batch (if first hasn't saturated)
  3. Charity Navigator fallback
- **Expected total:** 150–170K websites (from 111K baseline)

### T+48h (13:30 Central 2026-07-19)
- Full synergy: every new website → missions → cause tags → donor-visible
- Metrics: website discovery growth rate, link extraction success rate

---

## Monitoring Commands

**Real-time activity:**
```bash
# Watch web_finder progress
tail -f logs/web_finder_10k_20260717.log

# Watch discovery daemon
tail -f logs/discovery_daemon.log

# Check daemon stats
sqlite3 data/merit_registry.db "
  SELECT donate_url_status, COUNT(*) 
  FROM registry_enriched 
  WHERE donate_url IS NOT NULL 
  GROUP BY donate_url_status;"

# Watch overnight pipeline (when it runs)
tail -f logs/overnight.log
```

**Daily health check:**
```bash
# Process status
ps aux | grep -E "web_finder|discovery_daemon|embed_server" | grep -v grep

# CPU/memory load
top -b -n 1 | head -5

# Disk usage
df -h /home/akbar/meritgiving

# Last discovery orchestrator run
tail -20 logs/discovery_orchestrator.log
```

---

## Success Metrics (Weekly)

| Metric | Baseline | Target (1 week) | Target (1 month) |
|--------|----------|-----------------|------------------|
| Websites | 111K | 150K | 200K |
| Donation links (live/beta) | 18.3K | 25K | 35K |
| Volunteer links | 23.2K | 30K | 40K |
| Missions (with source) | 1.93M | 1.95M | 1.97M |
| Cause tags coverage | 95.1% | 96% | 97% |

---

## Key Decision Points

**If web_finder saturates (finds <50 new domains for 5 consecutive runs):**
- phase_orchestrator auto-activates Phase 2
- Switches to broader domain guessing (not just high-revenue)

**If Charity Navigator fallback needed:**
- Activated for orgs with revenue >$1M but no donate link
- Rate-limited: 1–2 req/sec, identified UA
- Disclosed source in DB

**If GPU memory pressure (embeddings + LLM competing):**
- Split night: embeddings 18:00–22:00, LLM 23:00–06:00
- Current headroom OK for both concurrent

---

## Risk Mitigation

**If discovery_daemon crashes:**
- watchdog_discovery.sh (5-min cron) auto-restarts
- SIGSTOP/SIGCONT handling prevents frozen state
- (Fixed earlier today)

**If web_finder hits rate limit:**
- Backs off gracefully, resumes next day
- Respects robots.txt + identified UA
- Caches verification results 30 days

**If 990 XML extraction fails:**
- Non-blocking; pipeline continues
- Retried next daily orchestrator run
- Falls back to web_finder + CN

---

## Notification Checkpoints

Will report completion when:
1. **Data deploy finishes** (precompute + frontend built + homepage live)
2. **First 48h of web discovery** (website count growth visible)
3. **First overnight pipeline run** (missions + cause tags generated)
4. **Weekly metrics** (growth trajectory confirmed)

---

## Contact / Escalation

**If something breaks:**
1. Check logs: `tail -f logs/discovery_daemon.log`
2. Check processes: `ps aux | grep -E "discovery|web_finder|embed"`
3. Check hardware: `top -b -n 1`, `df -h`
4. Restart: `bash scripts/embed_server.sh start`

**Manual one-off run:**
```bash
python3 scripts/nonprofit_discovery_orchestrator.py --batch-size 500
```

---

## Philosophy

**Website discovery is the gateway.** Every new site unlocks:
- Donation links (live after daemon extraction)
- Missions (generated by overnight pipeline)
- Cause tags (extracted from missions)
- Volunteer links (from site content)
- Financial context (cohort grouping)

**Local-first, zero-cost architecture:**
- No cloud APIs (except free/rate-limited)
- All compute on Ryzen + GPU
- 60% hardware headroom for scaling

**Stewardship alignment:**
- P2 (Privacy): all data local, no external retention
- P7 (Independence): no vendor lock-in
- P1 (Mission): donors get better information

---

**PIPELINE STARTED: 2026-07-17 13:29 Central**

Next checkpoint: Deploy completion + first web_finder results.
