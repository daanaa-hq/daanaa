# Uptime Kuma — monitoring (home box)

Already running on the home box (`docker run ... louislam/uptime-kuma:1`),
LAN-only, persistent (`--restart unless-stopped`), $0. The compose file here is
the version-controlled equivalent (same named volume `uptime-kuma`).

Dashboard: **http://192.168.1.73:3101** (host port 3101; container 3001 was free).

## First-run setup (2 minutes, UI only — do when on the LAN)
1. Open http://192.168.1.73:3101 and create the admin account.
2. Add Monitor:
   - Type: **HTTP(s) - Keyword**
   - URL: `https://daanaa.org`
   - Keyword: `Daanaa` (verifies the page renders, not just a 200)
   - Interval: 60s
3. The monitor auto-tracks the TLS cert; enable a notification (email/Telegram)
   and set a cert-expiry warning (e.g. 14 days).
4. Optional second monitor: `https://daanaa.org/api/health` (keyword `ok`).

## Manage
- Stop: `docker stop uptime-kuma`  ·  Start: `docker start uptime-kuma`
- Data lives in the `uptime-kuma` docker volume (survives container recreation).
