#!/bin/bash
echo "=========================================="
echo "  MERIT API + FRONTEND DEPLOY"
echo "=========================================="

# 1. Kill old API
echo "--- Stopping old API ---"
pkill -f "python.*merit_api" 2>/dev/null || true
pkill -f "flask" 2>/dev/null || true
sleep 2

# 2. Start new API in screen
echo "--- Starting API on :5000 ---"
source ~/meritgiving/venv/bin/activate
screen -S merit_api -X quit 2>/dev/null || true
screen -S merit_api -d -m bash -c "cd ~/meritgiving && python3 merit_api.py"
sleep 3

# 3. Verify API
echo "--- API Health Check ---"
curl -s http://localhost:5000/health | python3 -m json.tool 2>/dev/null || echo "API not responding yet"

echo "--- API Stats ---"
curl -s http://localhost:5000/api/stats | python3 -m json.tool 2>/dev/null || echo "Stats endpoint down"

echo "--- API Orgs (first page) ---"
curl -s "http://localhost:5000/api/organizations?per_page=3" | python3 -m json.tool 2>/dev/null || echo "Orgs endpoint down"

# 4. Frontend check
echo ""
echo "--- Frontend Status ---"
curl -s -o /dev/null -w "localhost:3000: %{http_code}\n" http://localhost:3000 2>/dev/null || echo "Frontend not running on :3000"

echo ""
echo "=========================================="
echo "Done. API running in screen 'merit_api'"
echo "Test links:"
echo "  http://localhost:5000/health"
echo "  http://localhost:5000/api/stats"
echo "  http://localhost:5000/api/organizations?per_page=5"
echo "=========================================="
