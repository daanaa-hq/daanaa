# Droplet Deployment Guide: Week 3 Beta

**Objective**: Deploy v5.0 beta frontend to droplet for live testing  
**Current Blocker**: Disk space (6G free, need 12G)  
**Solution**: Aggressive cleanup + skip FAISS rebuild

---

## Option 1: Quick Fix (Recommended)

Deploy with FAISS skip + minimal cleanup:

```bash
cd ~/meritgiving

# Check droplet space before deploying
ssh root@167.99.204.157 'df -h /'

# Deploy with SKIP_FAISS=1 to skip rebuilding quantized index
SKIP_FAISS=1 bash scripts/safe_deploy_droplet.sh
```

**Expected outcome**: ~5 min deployment  
**What happens**: Frontend + precomputed org/browse/content files deployed, FAISS index reused

---

## Option 2: Clean Droplet First (If needed)

If Option 1 fails due to disk space:

```bash
# SSH to droplet and clean old files
ssh root@167.99.204.157 << 'EOF'
# Check current usage
du -sh /var/www/daanaa/* 2>/dev/null | sort -rh | head -10

# Remove old deployments (keep current)
rm -rf /var/www/daanaa/old_deploy_* 2>/dev/null
rm -rf /var/www/daanaa/backup_* 2>/dev/null

# Clear temporary files
rm -rf /tmp/deploy_* 2>/dev/null
rm -rf ~/.deploy_scratch/old_* 2>/dev/null

# Check freed space
df -h /
EOF

# Then retry deployment
SKIP_FAISS=1 bash scripts/safe_deploy_droplet.sh
```

---

## Option 3: Resize Droplet (Last Resort)

If cleanup insufficient:

```bash
# In DigitalOcean console:
# 1. Power off droplet
# 2. Resize to next tier (from 4GB to 8GB+ RAM)
# 3. Power back on
# 4. Run deployment

SKIP_FAISS=1 bash scripts/safe_deploy_droplet.sh
```

---

## Deployment Checklist

- [ ] Local frontend built (`npm run build` in `frontend/`)
- [ ] V5Context component ready (frontend/src/components/V5Context.tsx)
- [ ] Feature flag hook ready (frontend/src/hooks/useFeatureFlag.ts)
- [ ] API returning v5_context (verified at localhost:5000)
- [ ] Feature flag distribution verified (1% sampling works)
- [ ] All commits pushed (git log shows latest changes)
- [ ] Disk space checked on droplet
- [ ] Deployment script ready with SKIP_FAISS=1

---

## Monitoring After Deployment

Once deployed to droplet, verify:

```bash
# Check frontend is live
curl -s https://daanaa.org/org/391214392 | grep "V5Context\|v5_context" | head -5

# Check API returns v5_context
curl -s https://daanaa.org/api/organizations/391214392 | jq '.v5_context.archetype'

# Monitor error logs
tail -f /var/log/daanaa/access.log | grep v5_context
```

---

## Rollback (If Needed)

If deployment has issues:

```bash
# Revert to previous frontend build
ssh root@167.99.204.157 << 'EOF'
cd /var/www/daanaa
# Check available backups
ls -la backup_frontend_*

# Restore previous version
rm -rf dist/
cp -r backup_frontend_20260610/ dist/
# Restart nginx
systemctl restart nginx
EOF
```

---

## Timeline

| Step | Time | Owner |
|------|------|-------|
| Check droplet disk | 5 min | - |
| Run deployment | 5–10 min | safe_deploy_droplet.sh |
| Verify API endpoint | 2 min | curl |
| Monitor for errors | 10 min | tail logs |
| **Total** | **~20 min** | |

---

## Success Criteria

After deployment:

- [ ] Frontend loads without errors
- [ ] Org detail pages load in <2s
- [ ] v5_context data appears in API responses
- [ ] 1% of users see V5Context component
- [ ] No regression in v4 functionality
- [ ] Feedback form ready to collect responses

---

## Notes

- Safe to deploy during business hours (no data loss risk)
- No downtime for v4 functionality
- Rollback available if issues occur
- Feature flag limits impact to 1% of users
