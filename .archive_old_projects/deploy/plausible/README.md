# Plausible Analytics — self-host runbook (home box)

Privacy-respecting, cookieless analytics for daanaa.org (STEWARDSHIP P2).
Self-hosted on the home Ryzen box. Public ingest via a Cloudflare Tunnel — no
open ports, no new recurring cost. Everything below is the **finish-when-back**
checklist; the compose + secrets are already prepared.

## Already prepared (committed / on the box)
- `docker-compose.yml` — Plausible CE v2.1.4 + Postgres 16 + ClickHouse 24.12,
  Plausible bound to `127.0.0.1:8000` only (tunnel is the sole public path).
- `clickhouse/*.xml` — IPv4 bind + quiet logging.
- `plausible-conf.env` — real secrets, `chmod 600`, **gitignored** (not in the repo).
  `plausible-conf.env.example` is the committed template.

## 1. Bring up the stack
```bash
cd ~/meritgiving/deploy/plausible
docker compose --env-file plausible-conf.env up -d
docker compose ps          # wait until plausible is healthy
curl -sf http://localhost:8000/api/health && echo OK
```
Uses ~1.5–2 GB RAM (ClickHouse). Fine on the 30 GB box.

## 2. Cloudflare Tunnel → stats.daanaa.org
`cloudflared` is already installed. If not logged in: `cloudflared tunnel login`.
```bash
cloudflared tunnel create daanaa-stats
cloudflared tunnel route dns daanaa-stats stats.daanaa.org   # creates the DNS record
```
Create `~/.cloudflared/config.yml`:
```yaml
tunnel: daanaa-stats
credentials-file: /home/akbar/.cloudflared/<TUNNEL_UUID>.json
ingress:
  - hostname: stats.daanaa.org
    service: http://localhost:8000
  - service: http_status:404
```
Run it as a service so it survives reboot:
```bash
sudo cloudflared service install
sudo systemctl enable --now cloudflared
```
Verify: `curl -sI https://stats.daanaa.org/api/health` → 200.

## 3. First-run account + site
- Open https://stats.daanaa.org (registration is open on first boot).
- Create the admin account; add site **daanaa.org**.
- Then lock it down: set `DISABLE_REGISTRATION=true` in `plausible-conf.env` and
  `docker compose --env-file plausible-conf.env up -d`.

## 4. Wire the site (deploy after stats.daanaa.org is live)
Two small changes, then rebuild + deploy the frontend:

**a. `frontend/index.html`** — add before `</head>`:
```html
<script defer data-domain="daanaa.org" src="https://stats.daanaa.org/js/script.js"></script>
```

**b. `scripts/droplet_api.py`** CSP (around line 37) — add `https://stats.daanaa.org`
to BOTH `script-src` and `connect-src`. Mirror the same in `daanaa_api.py` (line ~1011)
for dev parity.

Then:
```bash
cd ~/meritgiving/frontend && npm run build
rsync -az --delete dist/ root@162.243.97.179:/opt/daanaa/frontend/dist/ -e "ssh -i ~/.ssh/daanaa_do"
rsync -az ~/meritgiving/scripts/droplet_api.py root@162.243.97.179:/opt/daanaa/droplet_api.py -e "ssh -i ~/.ssh/daanaa_do"
ssh -i ~/.ssh/daanaa_do root@162.243.97.179 'systemctl restart daanaa'
```
Confirm: load daanaa.org, then check Plausible shows a live visitor. Done.

## Rollback
`docker compose down` stops it. Remove the script tag + CSP entries and redeploy
to fully detach. No external dependencies, no cost.
