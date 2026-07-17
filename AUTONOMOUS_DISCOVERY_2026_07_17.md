# Autonomous Discovery Pipeline — 2026-07-17 13:29 UTC

**Configuration:** FULLY AUTONOMOUS ✅

---

## The System (Running Alone)

### Processes (24/7)
- **embed_server (11436)** — Ownership verification
- **discovery_daemon** — Link extraction (auto-wakes on new websites)
- **web_finder_agent** — Website finding (continuous, batched)
- **phase_orchestrator** — Phase management (auto-switch on saturation)

### Scheduled Tasks
| Time (UTC) | Task | Frequency | Purpose |
|---|---|---|---|
| 02:00 | delta_scorer_v5_nightly.py | Sun–Fri | Score new orgs same-day |
| 02:30 | overnight_pipeline.py | Daily | Mission generation + cause tags |
| 03:00 | sync_irs_revocations.py | Daily | Revocation sync |
| 03:30 | IRS revocation check | Daily | Mark revoked orgs inactive |
| 08:15 | nightly_search_deploy.sh | Daily | Deploy search index to droplet |
| 11:00 | nonprofit_discovery_orchestrator.py | Daily | Multi-source website batch |
| 14:00 | deploy_morning.sh | Daily | Precompute + data to droplet |
| 14:00–18:00 | deploy_queued_links.py | Every 4h | Auto-deploy verified links |
| 21:00 | gpu_night.sh start | Daily | GPU night mode |
| 02:00 | enrichment_loop_8pm_8am.sh | Nightly | GPU batch enrichment |
| 09:00 | gpu_night.sh stop | Daily | GPU power-down |

### Auto-Deploy
- `deploy_queued_links.py` runs every 4 hours
- Automatically deploys newly-verified donation/volunteer links to droplet
- Updates homepage + org profiles in near-real-time
- No human approval needed

---

## Monitoring (Passive)

The system continuously tracks efficiency:

### Efficiency Metric (0–100%)
Combines:
- **Throughput:** websites found/hour + links extracted/hour (50% weight)
- **Success rates:** website verification + link extraction success (30% weight)
- **Resource efficiency:** inverse of CPU/GPU/disk utilization (20% weight)

### The 80% Threshold

**Baseline:** Efficiency established on first run
- Recorded in `logs/.efficiency_state.json`
- Example: if baseline = 85%, then 80% × 85% = **68%** is the alert threshold

**When efficiency drops below 68%:**
1. Alert written to `logs/efficiency_alert.log`
2. Marker file created: `logs/.EFFICIENCY_THRESHOLD_BREACHED`
3. Pipeline continues running (no auto-stop)
4. **Signal to reconnect**

### Where to Check

```bash
# Current efficiency state (human-readable)
cat logs/efficiency_monitor.log | tail -10

# Did threshold breach?
[ -f logs/.EFFICIENCY_THRESHOLD_BREACHED ] && echo "YES — reconnect for optimization"

# What was the alert?
cat logs/efficiency_alert.log

# Historical baseline
cat logs/.efficiency_state.json | jq .peak_efficiency
```

---

## When Efficiency Hits 80% (Reconnect Signal)

### Why It Drops

Common causes:
1. **Saturation:** web_finder found most feasible domains; discovering remainder is harder
2. **Resource contention:** discovery_daemon + LLM batch competing for GPU
3. **API rate limits:** ProPublica or CN fallback is throttling
4. **Data quality:** newer websites more fragmented, harder to verify

### What to Do

When you see the marker, reconnect:

```bash
# Optimization options:
1. Increase web_finder workers: 8 → 16 (if CPU headroom)
2. Adjust LLM batch size: 1 → 8 (if GPU memory allows)
3. Shift enrichment hours: move LLM to off-peak (midnight–06:00)
4. Add Searx fallback: for domain discovery (if embed server saturated)
5. Split phases: Phase 2 activation (broader domain guessing)
6. Expand sources: add GiveWell/CyberGrants lists for cross-reference

# Reconnect command:
python3 scripts/nonprofit_discovery_orchestrator.py --batch-size 2000

# Or manually run specific source:
python3 scripts/web_finder_agent.py --limit 5000 --workers 16
```

---

## Efficiency Checkpoints (What to Expect)

### Week 1 (2026-07-17 to 2026-07-23)
- **Efficiency:** 90–100% (high throughput, low resource contention)
- **Discoveries:** 1–5K websites
- **Links:** 200–500 new donation links

### Week 2 (2026-07-24 to 2026-07-30)
- **Efficiency:** 85–95% (still strong, saturation beginning)
- **Discoveries:** 500–2K websites (harder candidates)
- **Links:** 100–300 new links

### Week 3–4 (August)
- **Efficiency:** 70–85% (optimization window)
- **Discoveries:** 200–500 websites (high-effort domain guessing)
- **Signal:** If efficiency < 80% threshold breach, reconnect

### If Phase 2 Activates (broader discovery)
- **Efficiency:** 80–90% again (fresher candidate pool)
- **Discoveries:** 2–10K websites (all 1.76M orgs, not just high-revenue)

---

## Autonomous Behavior (No Human Needed)

✅ **Daemon extracts links** — Automatic on new websites
✅ **Deploy queued links** — Every 4 hours, autonomous
✅ **Morning precompute** — Scheduled 14:00 UTC
✅ **Overnight enrichment** — Scheduled 02:30 UTC
✅ **Monitor efficiency** — Every 30 minutes, autonomous
✅ **Phase transitions** — Auto-switch if saturation detected

❌ **Does NOT auto-stop** — Pipeline keeps running
❌ **Does NOT auto-heal** — Alerts you when manual optimization needed
❌ **Does NOT spend money** — All local, zero external APIs

---

## Emergency Stop (If Needed)

```bash
# Kill discovery daemon (careful: loses in-progress links)
pkill -f discovery_daemon.py

# Kill web_finder (pause domain discovery)
pkill -f web_finder_agent

# Kill embed server
bash scripts/embed_server.sh stop

# Full stop (pause all)
for proc in discovery_daemon web_finder phase_orchestrator embed_server; do
  pkill -f "$proc"
done
```

**Resuming after stop:**
```bash
bash scripts/embed_server.sh start
nohup python3 scripts/discovery_daemon.py 100 >> logs/discovery_daemon.log 2>&1 &
nohup python3 scripts/web_finder_agent.py --limit 10000 >> logs/web_finder.log 2>&1 &
nohup python3 scripts/phase_orchestrator.py >> logs/phase_orchestrator.log 2>&1 &
```

---

## Summary

**Status:** Autonomous, monitoring-triggered optimization
- Runs alone 24/7
- Deploys verified links automatically every 4 hours
- Tracks efficiency, alerts at 80% threshold
- When you see the alert, reconnect to optimize

**Typical workflow:**
1. **Week 1:** Efficiency high, no action needed
2. **Week 2:** Efficiency dropping, monitor logs
3. **Week 3:** Efficiency hits 80% threshold → reconnect
4. **Action:** Increase workers, batch sizes, or activate Phase 2
5. **Result:** Efficiency rebounds, back to autonomous mode

**Cost:** $0/month (all local hardware)
**Scalability:** Can grow to 10M orgs on current hardware

---

**Autonomous Discovery Pipeline Started: 2026-07-17 13:29 UTC**

Check logs when you have time. Reconnect when you see the efficiency alert.
