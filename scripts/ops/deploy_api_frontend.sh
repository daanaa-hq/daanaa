#!/bin/bash
echo "=========================================="
echo "  MERIT API + FRONTEND DEPLOY"
echo "=========================================="

# 1. Kill old API
echo "--- Stopping old API ---"
pkill -f "python.*merit_api" 2>/dev/null || true
pkill -f "flask" 2>/dev/null || true
sleep 2

# 2. Build frontend
echo "--- Building frontend ---"
source ~/meritgiving/venv/bin/activate
cd ~/meritgiving/frontend && npm run build && cd ~/meritgiving

# 3. Start API in screen (serves API + built frontend)
echo "--- Starting API on :5000 ---"
screen -S merit_api -X quit 2>/dev/null || true
screen -S merit_api -d -m bash -c "cd ~/meritgiving && source venv/bin/activate && python3 merit_api.py"
sleep 3

# 4. Verify API + frontend
echo "--- API Health Check ---"
curl -s http://localhost:5000/health | python3 -m json.tool 2>/dev/null || echo "API not responding yet"

echo "--- API Stats ---"
curl -s http://localhost:5000/api/stats | python3 -m json.tool 2>/dev/null || echo "Stats endpoint down"

echo "--- SPA Fallback Check ---"
curl -s -o /dev/null -w "/:        %{http_code}\n" http://localhost:5000/
curl -s -o /dev/null -w "/directory: %{http_code}\n" http://localhost:5000/directory
curl -s -o /dev/null -w "/orgs/test: %{http_code}\n" http://localhost:5000/orgs/test

echo ""
echo "=========================================="
echo "Done. API + frontend running in screen 'merit_api'"
echo "Test links:"
echo "  http://localhost:5000/           (home)"
echo "  http://localhost:5000/directory  (directory)"
echo "  http://localhost:5000/health     (API health)"
echo "  http://localhost:5000/api/stats  (API stats)"
echo "=========================================="
