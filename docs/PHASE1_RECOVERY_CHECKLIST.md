# Phase 1-4 Recovery Checklist (2026-08-11 Incident)

**Status:** daanaa.org is DOWN (DNS points to unreachable 167.170.26.8)  
**Action Needed:** Revert DNS to restore service, then investigate droplet  
**Blocker Fixes Status:** All safe and committed, just need proper droplet

---

## IMMEDIATE (Restore Service Now)

### Step 1: Revert DNS in Cloudflare

1. Go to: https://dash.cloudflare.com/d5639a783e4850958cbe7311414fe60/daanaa.org/dns/records
2. Find the A record for `daanaa.org` (currently shows 167.170.26.8)
3. Click Edit
4. Change content from **167.170.26.8** to **107.170.26.8**
5. Click Save
6. Wait 1-2 minutes for propagation

✅ **Expected result:** daanaa.org loads (serves pre-Phase-1-4 code from old droplet)

### Step 2: Verify Site Is Back

```bash
curl -w "HTTP %{http_code}\n" -o /dev/null https://daanaa.org/
# Should return: HTTP 200
```

---

## INVESTIGATION (Why Did New Droplet Fail?)

Once site is restored, investigate in this order:

### Check 1: Is New Droplet Even Alive?

```bash
ssh root@167.170.26.8 "uptime"
```

**If SSH works:** Droplet is running; check services next  
**If SSH times out:** Network issue or droplet is down; check DigitalOcean console

### Check 2: Are Services Running?

```bash
ssh root@167.170.26.8 "systemctl status daanaa"
# Should show: active (running)

ssh root@167.170.26.8 "curl -s http://localhost:5000/health"
# Should return: {"status":"ok",...}
```

### Check 3: Can We Reach It Directly?

```bash
curl -m 5 http://167.170.26.8/health
# Should work if service is up
```

### Check 4: Cloudflare Tunnel Status

Go to: https://dash.cloudflare.com/...
- Click "Tunnels" in left nav
- Look for Daanaa tunnel
- Status should be "Connected"
- If "Disconnected", tunnel config is broken

### Check 5: Logs

```bash
ssh root@167.170.26.8 "tail -50 /home/akbar/meritgiving/logs/daanaa_api.log"
# Look for errors near deployment time (16:48 UTC)

ssh root@167.170.26.8 "tail -50 /home/akbar/meritgiving/logs/gunicorn_access.log"
# Should show requests from Cloudflare after DNS change
```

---

## RE-DEPLOYMENT (Once Droplet Is Healthy)

Once you've verified the new droplet works:

### Step 1: Verify Blocker Fixes Are In Git

```bash
git log --oneline | head -5
# Should show:
#   9e5fbbb docs: Incident log + cleanup
#   6f7f43113ba fix: IRS eligibility status consistency
#   f1a4eef7ab0 fix: Remove Firebase Analytics
```

### Step 2: Re-Deploy to New Droplet

```bash
bash scripts/ops/sync_droplet_api.sh
# This will:
# - Backup old version to S3
# - Deploy new code
# - Restart service
# - Run smoke test
```

### Step 3: Update DNS Back to New IP

Once deployment + smoke test pass:

```bash
# Cloudflare: Change A record back to 167.170.26.8
```

### Step 4: Verify via Cloudflare

```bash
curl -w "HTTP %{http_code}\n" https://daanaa.org/health
# Should return 200 with {"status":"ok",...}
```

---

## What's Safe (Already Committed)

✅ Firebase Analytics removal (Plausible canonical, P2 compliant)  
✅ IRS status bug fix (revoked properly distinguished from unknown, P3 compliant)  
✅ Privacy gates all passing  
✅ Frontend builds clean  
✅ All commits pushed and logged in LESSONS.md  

---

## If Investigation Shows...

| Finding | Action |
|---------|--------|
| "SSH works, service running, health OK" | Re-deploy to new droplet and update DNS |
| "SSH times out, DigitalOcean shows active" | Network routing issue; check firewall/security group |
| "Service crashed, 500 errors in logs" | Check which deploy broke it; may need to roll back code diff |
| "Cloudflare tunnel disconnected" | Reconfigure tunnel; check tunnel token |
| "No requests logged after DNS change" | Cloudflare never sent traffic; tunnel/routing is broken |

---

## Recovery Done

Once daanaa.org loads with Phase 1-4 fixes (Firebase removed, IRS status fixed):

- ✅ Update DECISIONS.md with "Recovery complete" note
- ✅ Update CURRENT_STATE.md with "Phase 1-4 LIVE"
- ✅ Commit the recovery work
- ✅ Close this checklist

---

**Questions? Check:**
- `LESSONS.md` — incident analysis and preventing rules
- `docs/DROPLET_DNS_FIX_AUG10.md` — earlier DNS fix reference
- Memory: `incident_2026_08_11_dns_cloudflare` — full incident record
