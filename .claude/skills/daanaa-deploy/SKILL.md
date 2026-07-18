# Skill: Daanaa Deploy Router

**Mission:** Ship the right way for the change at hand — minutes for code, hours only when data actually moved. Never repeat the 2026-07-17 confusion (a 3-line API fix waiting behind a 2-hour precompute rebuild).

## When to invoke

Use `/daanaa-deploy` when shipping ANY change to the live droplet (daanaa.org). This skill routes you to the correct deploy path and its verification steps.

## The routing table (decide FIRST, before running anything)

| What changed | Command | Duration | Notes |
|---|---|---|---|
| `scripts/droplet_api.py` only | `bash scripts/ops/sync_droplet_api.sh` | ~1 min | S3-backs old version, smoke-tests, auto-rolls-back |
| API + frontend code | `bash scripts/safe_deploy_droplet.sh --code-only` | ~5 min | API sync + SPA build/ship; reuses checked-in research-snapshot.json |
| Frontend (SPA) only | `bash scripts/safe_deploy_droplet.sh --frontend-only` | ~5 min | Regenerates research snapshot from DB snapshot |
| Data (scores, links, new orgs) | `bash scripts/safe_deploy_droplet.sh` | 2-4 h | Full precompute rebuild of 1.76M pages; runs nightly via cron anyway — prefer waiting for cron unless urgent |
| search.db only | `bash scripts/ops/nightly_search_deploy.sh` | ~15 min | Also on cron (08:15 daily) |

**Key facts that keep biting:**
- `safe_deploy_droplet.sh` (full mode) does NOT ship `droplet_api.py` — only `sync_droplet_api.sh` does (also on cron nightly 1:30am).
- Gunicorn imports `/opt/daanaa/droplet_api.py`, not `scripts/`. `sync_droplet_api.sh` handles this.
- Never run two deploys concurrently — they collide at the `dist.new → dist` swap. Check first: `pgrep -f safe_deploy_droplet`.
- The full deploy builds the SPA from the WORKING TREE, so uncommitted frontend changes ride along. Commit first.
- Never ship merit_registry.db to the droplet (2GB RAM box serves precompute + search.db only).

## Verification (every deploy, no exceptions)

A deploy that "restarted the service" is not verified (caused the 2026-07-05 outage). Verify BEHAVIOR:

```bash
# 1. Health + real pages render
for p in / /directory /org/264837170 /about; do curl -s -o /dev/null -w "$p → %{http_code}\n" "https://daanaa.org$p"; done

# 2. If the change touched a request parameter, prove the parameter WORKS
#    (route presence is not enough — the 2026-07-17 sort bug shipped through
#    a presence-only contract test). Example for sort:
curl -s "https://daanaa.org/api/organizations?sort=total_revenue&order=desc&per_page=2" | python3 -c "import json,sys; print([o['organization_name'] for o in json.load(sys.stdin)['organizations']])"
# Must differ from order=asc. Beware the edge response cache: change per_page to bust stale keys.
```

## Frontend gate

Frontend deploys need founder approval per CLAUDE.md unless the founder has granted lead for the session. Backend is autonomous but MUST pass smoke tests.

## After shipping

- Log non-obvious choices in DECISIONS.md, broke-then-fixed in LESSONS.md.
- If a param-honoring behavior was added/changed, extend `tests/test_contract_and_terminology.py` to pin it at source level.
