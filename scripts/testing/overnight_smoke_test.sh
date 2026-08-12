#!/bin/bash
# overnight_smoke_test.sh — Post-overnight-pipeline validation
# Run this after overnight_pipeline.py completes (around 2:30am or next morning)
# Verifies that all moved files were called correctly

set -e

BASE_DIR="${HOME}/meritgiving"
LOG_DIR="${BASE_DIR}/logs"
DB_DIR="${BASE_DIR}/data"

echo "=== Overnight Pipeline Smoke Test ==="
echo "Time: $(date)"
echo ""

# Test 1: Check overnight pipeline log for success
echo "Test 1: Overnight pipeline completion..."
if [ -f "${LOG_DIR}/overnight_pipeline.log" ]; then
    LAST_LINE=$(tail -1 "${LOG_DIR}/overnight_pipeline.log")
    if echo "$LAST_LINE" | grep -q "completed\|SUCCESS\|finished"; then
        echo "✅ Overnight pipeline completed successfully"
    else
        echo "⚠️  Last log line: $LAST_LINE"
    fi
else
    echo "❌ Log file not found: ${LOG_DIR}/overnight_pipeline.log"
fi

echo ""

# Test 2: Check if scoring was run
echo "Test 2: Scoring (daanaa_scorer.py)..."
if grep -q "daanaa_scorer" "${LOG_DIR}/overnight_pipeline.log" 2>/dev/null; then
    echo "✅ Scoring module was called"
else
    echo "⚠️  Scoring module not found in logs"
fi

# Test 3: Check if FTS index was rebuilt
echo "Test 3: Search index (build_fts_index.py)..."
if grep -q "build_fts_index\|search.*index" "${LOG_DIR}/overnight_pipeline.log" 2>/dev/null; then
    echo "✅ Search index rebuild was called"
else
    echo "⚠️  Search index rebuild not found in logs"
fi

# Test 4: Check if missions were generated
echo "Test 4: Missions (generate_missions.py)..."
if grep -q "generate_missions\|mission" "${LOG_DIR}/overnight_pipeline.log" 2>/dev/null; then
    echo "✅ Mission generation was called"
else
    echo "⚠️  Mission generation not found in logs"
fi

# Test 5: Check if embeddings were generated
echo "Test 5: Embeddings (build_org_embeddings.py)..."
if grep -q "embed\|embedding" "${LOG_DIR}/overnight_pipeline.log" 2>/dev/null; then
    echo "✅ Embeddings were generated"
else
    echo "⚠️  Embeddings generation not found in logs"
fi

echo ""

# Test 6: Verify database was updated (scores)
echo "Test 6: Database - Financial scores..."
if [ -f "${DB_DIR}/merit_registry.db" ]; then
    COUNT=$(sqlite3 "${DB_DIR}/merit_registry.db" \
        "SELECT COUNT(*) FROM registry_enriched WHERE merit_score_v6 > 0 LIMIT 1" 2>/dev/null || echo "0")
    if [ "$COUNT" -gt 0 ]; then
        echo "✅ Scores present in database ($COUNT orgs)"
    else
        echo "⚠️  No scores found in database"
    fi
else
    echo "❌ Database not found: ${DB_DIR}/merit_registry.db"
fi

echo ""

# Test 7: Verify FTS index was updated
echo "Test 7: Database - FTS search index..."
if [ -f "${DB_DIR}/search.db" ]; then
    COUNT=$(sqlite3 "${DB_DIR}/search.db" \
        "SELECT COUNT(*) FROM org_fts LIMIT 1" 2>/dev/null || echo "0")
    if [ "$COUNT" -gt 1000 ]; then
        echo "✅ FTS index present ($COUNT records)"
    else
        echo "⚠️  FTS index has few records ($COUNT)"
    fi
else
    echo "❌ Search database not found: ${DB_DIR}/search.db"
fi

echo ""

# Test 8: Verify API is still responding
echo "Test 8: API health check..."
if command -v curl >/dev/null 2>&1; then
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5000/health" 2>/dev/null || echo "000")
    if [ "$STATUS" = "200" ]; then
        echo "✅ API health endpoint responding (HTTP 200)"
    else
        echo "⚠️  API health returned HTTP $STATUS"
    fi
else
    echo "ℹ️  curl not available, skipping API check"
fi

echo ""
echo "=== Smoke Test Complete ==="
echo ""
echo "If all tests passed: ✅ Phase 2 is stable, proceed to Phase 3"
echo "If any tests failed: ⚠️  Check logs and troubleshoot before Phase 3"
