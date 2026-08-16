#!/bin/bash
# Verify hidden gems feature status

echo "═══════════════════════════════════════════════════════════════════"
echo "  Hidden Gems Feature Status Check"
echo "═══════════════════════════════════════════════════════════════════"
echo ""

status=0

# 1. Check home server registry has gems
echo "[1/7] Home server database — is_hidden_gem column"
GEM_COUNT=$(sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched WHERE is_hidden_gem=1 AND deductibility=1 AND org_status='active'")
if [ -n "$GEM_COUNT" ] && [ "$GEM_COUNT" -gt 0 ]; then
    echo "  ✓ Found $GEM_COUNT gems in registry_enriched"
else
    echo "  ✗ No gems found (check database)"
    status=1
fi
echo ""

# 2. Check precompute script exists
echo "[2/7] Precompute script"
if [ -f scripts/precompute_hidden_gems.py ]; then
    echo "  ✓ scripts/precompute_hidden_gems.py exists"
else
    echo "  ✗ scripts/precompute_hidden_gems.py missing"
    status=1
fi
echo ""

# 3. Check precomputed files
echo "[3/7] Precomputed gem files"
GEM_PAGES=$(find precompute_output/browse/hidden_gems -name 'ALL_*.json.gz' 2>/dev/null | wc -l)
if [ "$GEM_PAGES" -gt 0 ]; then
    echo "  ✓ Found $GEM_PAGES gem pages in precompute_output"
    # Check the most recent
    LATEST=$(ls -t precompute_output/browse/hidden_gems/ALL_1.json.gz 2>/dev/null)
    if [ -f "$LATEST" ]; then
        echo "    Last generated: $(date -r "$LATEST" '+%Y-%m-%d %H:%M:%S')"
    fi
else
    echo "  ⚠ No precomputed gem files found (run: python3 scripts/precompute_hidden_gems.py)"
    status=1
fi
echo ""

# 4. Check weekly cron
echo "[4/7] Weekly cron schedule"
if crontab -l 2>/dev/null | grep -q "precompute_hidden_gems"; then
    echo "  ✓ Weekly cron job configured"
    echo "    $(crontab -l 2>/dev/null | grep precompute_hidden_gems | head -1)"
else
    echo "  ⚠ Weekly cron not found"
fi
echo ""

# 5. Check droplet API supports gems
echo "[5/7] Backend API (droplet_api.py)"
if grep -q "gems_only" scripts/droplet_api.py; then
    echo "  ✓ droplet_api.py has hidden gems logic"
else
    echo "  ⚠ droplet_api.py may not have gems support"
fi
echo ""

# 6. Check frontend Directory component
echo "[6/7] Frontend Directory component"
if grep -q "hiddenGem\|hidden_gem" frontend/src/pages/Directory.tsx; then
    echo "  ✓ Directory.tsx has hidden gems UI"
    if grep -q "Hidden gems" frontend/src/pages/Directory.tsx; then
        echo "    - Hidden gems toggle: yes"
    fi
    if grep -q "See all 1.8M" frontend/src/pages/Directory.tsx; then
        echo "    - See all button: yes"
    fi
else
    echo "  ⚠ Directory.tsx may not have gems support"
fi
echo ""

# 7. Check API parameters
echo "[7/7] API parameter support"
if grep -q "hidden_gem" frontend/src/data/api.ts; then
    echo "  ✓ API params include hidden_gem"
else
    echo "  ⚠ API missing hidden_gem parameter"
fi
echo ""

echo "═══════════════════════════════════════════════════════════════════"
if [ $status -eq 0 ]; then
    echo "  ✓ Hidden gems feature appears complete!"
else
    echo "  ⚠ Some items need attention"
fi
echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Deployment checklist
echo "Pre-deployment checklist:"
echo ""
echo "  Before deploying to the droplet:"
echo "    □ Run 'scripts/deploy_hidden_gems.sh' to patch search.db"
echo "    □ Verify with: curl 'https://daanaa.org/api/organizations?hidden_gem=1&page=1'"
echo ""
echo "  Monitor in production:"
echo "    □ Check droplet /var/log/gunicorn/error.log for gem-file errors"
echo "    □ Confirm directory landing serves gems (not by revenue)"
echo "    □ Weekly: verify precompute cron ran"
echo ""

exit $status
