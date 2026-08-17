# Droplet Connectivity Lost (2026-08-17)

## Timeline
- 23:40 — Service restarted successfully (systemctl OK)
- 23:40-23:44 — Smoke test ran, service active but not responding to HTTPS (timeout at 90s)
- 23:44 — Auto-rollback triggered
- 23:44+ — Droplet SSH completely unreachable

## What Likely Happened
After auto-rollback triggered `systemctl restart daanaa-api`, one of three scenarios:
1. **Restart loop**: Service keeps crashing and restarting, systemd reached restart limit
2. **Kernel panic**: Deployment/rollback caused system instability
3. **Network interrupt**: Droplet lost connectivity to internet/hosting provider

## Current State
- **Droplet SSH**: All IPs unreachable (connection timed out)
- **Production**: Unknown (cannot verify from here)
- **Auto-rollback**: Triggered successfully (last we saw)
- **Logs**: Cannot access (SSH down)

## How to Investigate
You'll need to check the droplet manually via hosting provider dashboard:

### DigitalOcean Console (if droplet is on DO)
1. Log in to DigitalOcean dashboard
2. Select your droplet (likely "daanaa-prod" or "daanaa-1")
3. Click "Console" to open web terminal
4. Check if system is booting, running, or in restart loop:
   ```bash
   systemctl status daanaa-api
   journalctl -u daanaa-api -n 50
   ```

### If Service is in Restart Loop
```bash
systemctl stop daanaa-api
systemctl status daanaa-api
# Edit service to disable warm_cache.sh:
sed -i 's/^ExecStartPost/#ExecStartPost/' /etc/systemd/system/daanaa-api.service
systemctl daemon-reload
systemctl start daanaa-api
```

### If Kernel/Network Issue
```bash
sudo reboot
# After reboot, test: curl https://daanaa.org/
```

## Why This Matters
- Auto-rollback would have restored the old version
- But if systemd restart loop is happening, the service won't come back up
- Droplet console is only way to diagnose from here

## Code Status (Safe)
- All commits preserved locally
- IRS backfill still in database
- No data loss (rollback would preserve database state)
- Deployment scripts ready to re-run once droplet is reachable

## Recommendations
1. **Check droplet console immediately** to see if service is in restart loop
2. **If loop detected**: Disable warm_cache.sh (sed command above)
3. **If network issue**: Reboot via hosting provider dashboard
4. **Once droplet is back**: Run `bash scripts/ops/sync_droplet_api.sh` to re-deploy

---

**Status**: Awaiting manual droplet check  
**Blocker**: SSH unreachable; cannot proceed without console access  
**Workaround**: Check droplet console via hosting provider (DigitalOcean/AWS/etc)
