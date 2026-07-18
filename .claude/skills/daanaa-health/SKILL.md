# Skill: Daanaa Live Health Check

**Mission:** Answer "is everything actually working?" with evidence, not vibes. Every check here exists because its absence once hid a real production problem.

## When to invoke

Use `/daanaa-health` when the founder asks "checking in", "is the site up", "how's the daemon", "is search fast" — or at the start of any session before building on top of the system, and after any deploy.

## The checklist (run all, in order — each catches a real past incident)

### 1. Site up + pages render (not just /health)
```bash
for p in / /directory /org/264837170 /about /org/login; do
  curl -s -o /dev/null -w "$p -> %{http_code} (%{time_total}s)\n" --max-time 10 "https://daanaa.org$p"
done
```
A 200 on /health with broken pages caused the 2026-07-05 outage class. `/org/login` is the nonprofit funnel entry (dead-ended silently for weeks before 2026-07-18).

### 2. Search speed — cache-busted, isolated, common words
```bash
for term in health food children; do
  sleep 2  # isolation: rapid-fire requests queue behind 4 sync workers and fake a slowdown
  curl -s -o /dev/null -w "$term: %{time_total}s | %{http_code}\n" --max-time 15 \
    "https://daanaa.org/api/organizations?q=$term&per_page=24&_cb=$(date +%s%N)"
done
```
- **Always cache-bust** (`_cb=`): Cloudflare serves stale results for repeated URLs and will show you a fixed bug as still-broken (2026-07-18).
- **>3s for a common word is a real problem.** The 2026-07-18 bug (15-21s) was two stacked query issues: an uncapped FTS join, then SQLite flipping join order (fix: bounded-candidate CTE + CROSS JOIN — see LESSONS.md).
- If slow: reproduce ONCE, isolated, direct on the droplet before concluding anything.

### 3. No duplicate or zombie pipeline processes
```bash
ps -eo pid,etime,pcpu,cmd | grep -E "python3.*(discovery|enrich|web_finder|donation_link)" | grep -v grep
```
- Exactly ONE `discovery_daemon.py`. Watchdog cron (*/5) auto-relaunches it — after killing one intentionally, expect the watchdog's copy; don't also launch your own (dup incident 2026-07-18).
- `pgrep -f` matches its own invocation — use `pgrep -af` and read the command line before believing a match.
- Enrichment (`enrich_batch`) must NOT be running between 08:00-20:00 — if it is, its embedding server (:11436) is likely already stopped and it's erroring on every org (zombie-batch incident 2026-07-18; the loop now has a hard cutoff, but verify).
- Anything at ~100% CPU that isn't llama/scorer: investigate before it degrades live search (my own test did, 2026-07-18).

### 4. Queue truth — count by the DRAIN predicate, not a status label
```bash
bash ~/meritgiving/scripts/discovery_progress_report.sh
```
"Pending" must come from `deployed_at IS NULL` (what the deploy actually drains). A status-labeled backlog of 30K was a bookkeeping mirage on 2026-07-18. If a backlog number looks exciting or alarming, cross-check it against the drain query before reporting it to the founder.

### 5. Local API freshness (only after backend code changes)
```bash
ps -o lstart= -p $(cat ~/meritgiving/logs/daanaa_api.pid) ; git -C ~/meritgiving log -1 --format=%cd -- daanaa_api.py
```
gunicorn runs `--preload` — code changes do NOTHING until `./restart_api.sh`. If process start predates the last daanaa_api.py commit, the running API is stale (2026-07-18).

### 6. Deploy-failure messages: verify independently before reacting
A "SMOKE TEST FAILED / Rollback FAILED" from sync_droplet_api.sh can be a transient SSH blip, not an outage. Before any recovery action: curl the public site AND `md5sum` local vs `/opt/daanaa/droplet_api.py`. Matching sums + serving pages = deploy actually succeeded (false-alarm incident 2026-07-18). Never panic-redeploy on top of a fine state.

## Reporting

Lead with the verdict (healthy / degraded / broken + what), then evidence. If something's off, root-cause before fixing (route to /investigate) — and never leave a backgrounded diagnostic running (re-check §3 before ending the session).
