# Daanaa Production Continuity Runbook — One Week

## Objective

Keep `https://daanaa.org` available and recoverable while the founder is away.
This runbook favors stability over feature velocity. Local work may continue,
but production changes remain separately gated.

## Production ownership

- Web edge: nginx.
- API service: `daanaa.service`.
- API process: systemd-managed Gunicorn serving the production entrypoint.
- Production database: verify the path from the systemd unit before any action;
  do not assume the local database path.
- Public smoke endpoint: `/health`.
- Core API smoke endpoint: `/api/organizations/000019818`.
- v6 API endpoint: `/api/organizations/000019818/financial-context` only after
  the route has been deliberately deployed and verified.

## Absolute production rules

Never perform these actions during unattended operation:

- `pkill gunicorn`;
- `nohup gunicorn`;
- manual duplicate Gunicorn processes;
- `git reset --hard`;
- deleting backups or data to free space;
- database migrations;
- precompute rebuilds;
- large tar/archive operations;
- changing systemd environment variables;
- deploying a file whose exact diff has not been reviewed;
- restarting the droplet merely to test a code change.

If the service is healthy, do not restart it.

## Monitoring cadence

### Every 30–60 minutes

Run read-only health checks:

```bash
date -u
uptime
free -h
df -h /
systemctl is-active nginx
systemctl is-active daanaa
curl -fsS --max-time 15 https://daanaa.org/health
curl -fsS --max-time 20 https://daanaa.org/api/organizations/000019818
```

Record the output in the daily handoff note. Do not restart for a single slow
request; take two samples five minutes apart.

### Every 4 hours

Check for resource pressure and restart loops:

```bash
systemctl show daanaa -p NRestarts -p ActiveState -p SubState
journalctl -u daanaa --since '4 hours ago' --no-pager
journalctl -u nginx --since '4 hours ago' --no-pager
ss -ltnp | grep -E ':(80|443|5000)\\b' || true
```

Escalate if any of these occur:

- root filesystem above 85%;
- available memory below 20%;
- swap usage grows continuously for two checks;
- `NRestarts` increases unexpectedly;
- port 5000 has more than one unrelated Gunicorn master;
- `/health` fails twice consecutively;
- nginx is active but the upstream API is unavailable.

### Daily

```bash
systemctl status nginx --no-pager
systemctl status daanaa --no-pager
df -h /
free -h
journalctl -p warning..alert --since '24 hours ago' --no-pager
```

Also verify that the latest known-good database backup exists and that its
integrity was previously recorded. Do not create a large backup during a high
load incident without checking available disk space first.

## Incident response

### Case A — Public site fails, SSH works

1. Check nginx status.
2. Check `curl http://127.0.0.1:5000/health`.
3. Check `systemctl status daanaa` and recent journal output.
4. If the API service is inactive and the unit is known-good, run only:

```bash
systemctl restart daanaa
sleep 10
systemctl is-active daanaa
curl -fsS --max-time 20 http://127.0.0.1:5000/health
curl -fsS --max-time 20 https://daanaa.org/health
```

5. If the restart fails, stop. Do not start Gunicorn manually. Preserve logs
   and escalate for rollback or provider console recovery.

### Case B — SSH handshake timeout

1. Do not repeatedly reconnect or issue repeated restart commands.
2. Check DigitalOcean console metrics and power state.
3. Wait for one controlled observation window.
4. Use the provider console only to inspect or gracefully power-cycle if the
   droplet is confirmed unresponsive.
5. After recovery, run the full health checklist and record the incident.

### Case C — High memory or CPU

1. Do not kill processes by pattern.
2. Capture:

```bash
free -h
ps aux --sort=-%mem | head -20
ps aux --sort=-%cpu | head -20
systemctl status daanaa --no-pager
```

3. Check for duplicate Gunicorn masters and recent OOM messages:

```bash
dmesg -T | grep -iE 'oom|out of memory|killed process' || true
journalctl -k --since '2 hours ago' --no-pager | grep -iE 'oom|killed' || true
```

4. Do not launch another API process. Escalate with the evidence.

### Case D — Disk pressure

Do not delete files broadly. First inventory exact large paths:

```bash
df -h /
du -xhd1 /opt/daanaa 2>/dev/null | sort -h
du -xhd1 /var/lib/docker 2>/dev/null | sort -h
```

Only remove an item if it is explicitly identified, recoverable, and approved.
Backups are never disposable merely because disk is tight.

## Deployment gate

No production deployment is allowed unless all items are recorded:

- exact commit and changed files;
- local compile, tests, build, and type check;
- donor-facing stewardship review;
- accessibility and browser evidence;
- DigitalOcean snapshot ID;
- verified production database backup path and integrity result;
- staged or atomic file replacement plan;
- systemd-only restart plan;
- local API smoke test;
- public homepage and core API smoke tests;
- public v6 JSON content-type test if v6 is included;
- rollback command and expected recovery time;
- explicit owner approval for that exact diff.

## Daily handoff template

```text
date_utc:
agent:
site_status: healthy | degraded | incident
health_checks:
api_checks:
memory:
disk:
restart_count:
recent_errors:
changes_made:
changes_not_made:
backup_evidence:
open_risks:
next_check:
escalation_required: yes | no
```

## Success condition for the week

The service remains reachable, no unreviewed production changes occur, health
evidence is recorded at the agreed cadence, and every local feature change ends
in a reviewable handoff rather than an unattended deployment.
