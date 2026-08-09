#!/bin/bash
echo "=========================================="
echo "      MERITGIVING DATA STATUS CHECK"
echo "      $(date)"
echo "=========================================="

echo ""
echo "=== 1. SCREEN SESSIONS (Active Workers) ==="
screen -ls | grep -E "merit|worker" || echo "No merit/worker screens found"

echo ""
echo "=== 2. DATABASE OVERVIEW ==="
if [ -f data/merit_registry.db ]; then
    echo "DB Size: $(du -h data/merit_registry.db | cut -f1)"
    sqlite3 data/merit_registry.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
else
    echo "merit_registry.db NOT FOUND"
fi

echo ""
echo "=== 3. TABLE COUNTS ==="
sqlite3 data/merit_registry.db "
SELECT 'registry' as table_name, COUNT(*) as count FROM registry
UNION ALL
SELECT 'registry_enriched', COUNT(*) FROM registry_enriched
UNION ALL
SELECT 'irs_bmf', COUNT(*) FROM irs_bmf
UNION ALL
SELECT 'revenue_percentiles', COUNT(*) FROM revenue_percentiles;
" 2>/dev/null || echo "Could not query counts"

echo ""
echo "=== 4. DATA QUALITY SNAPSHOT ==="
sqlite3 data/merit_registry.db "
SELECT 
    'Total Orgs' as metric,
    COUNT(*) as value
FROM registry_enriched
UNION ALL
SELECT 
    'With Revenue',
    COUNT(*)
FROM registry_enriched 
WHERE total_revenue > 0
UNION ALL
SELECT 
    'With NTEE Code',
    COUNT(*)
FROM registry_enriched 
WHERE ntee_code IS NOT NULL AND ntee_code != '';
" 2>/dev/null || echo "Could not query quality metrics"

echo ""
echo "=== 5. RECENT LOG ACTIVITY (Last 20 lines) ==="
for log in logs/worker_a.log logs/worker_b.log logs/worker_c.log logs/worker_d.log logs/worker_e.log; do
    if [ -f "$log" ]; then
        echo "--- $log (last 3 lines) ---"
        tail -3 "$log" 2>/dev/null
    fi
done

echo ""
echo "=== 6. DATA FILES INVENTORY ==="
echo "-- CSV/JSON Data Files --"
find data/ -maxdepth 2 -type f \( -name "*.csv" -o -name "*.json" -o -name "*.zip" \) -exec ls -lh {} \; 2>/dev/null | awk '{print $5, $9}'

echo ""
echo "=== 7. NCCS CORE FILES ==="
for f in data/corepcf/core_2019_pz.csv data/corepcf/core_2019_pc.csv data/corepcf/core_2019_ot_pz.csv data/corepcf/core_2019_ot_pc.csv; do
    if [ -f "$f" ]; then
        lines=$(wc -l < "$f" 2>/dev/null)
        size=$(du -h "$f" 2>/dev/null | cut -f1)
        echo "$f | Lines: $lines | Size: $size"
    else
        echo "$f | MISSING"
    fi
done

echo ""
echo "=== 8. API / WEB STATUS ==="
curl -s -o /dev/null -w "Frontend localhost:5000: %{http_code}\n" http://localhost:5000 2>/dev/null || echo "Frontend localhost:5000: DOWN"
curl -s -o /dev/null -w "API localhost:8000: %{http_code}\n" http://localhost:8000 2>/dev/null || echo "API localhost:8000: DOWN"

echo ""
echo "=== 9. DISK SPACE ==="
df -h . | tail -1

echo ""
echo "=========================================="
echo "           STATUS CHECK COMPLETE"
echo "=========================================="
