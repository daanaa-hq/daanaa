#!/bin/bash
echo "=== KILLING EVERYTHING ON PORT 5000 ==="
# Kill by port
fuser -k 5000/tcp 2>/dev/null || true
# Kill any python processes with merit in the name
pkill -9 -f "python.*merit" 2>/dev/null || true
pkill -9 -f "uvicorn" 2>/dev/null || true
pkill -9 -f "flask" 2>/dev/null || true
sleep 2

echo "=== VERIFY PORT IS FREE ==="
fuser 5000/tcp 2>/dev/null && echo "Port still in use!" || echo "Port 5000 is free"

echo "=== STARTING NEW FLASK API ==="
source ~/meritgiving/venv/bin/activate
cd ~/meritgiving
[ -f .env ] && export $(grep -v '^#' .env | xargs)
python3 merit_api.py > logs/merit_api.log 2>&1 &
API_PID=$!
echo $API_PID > logs/merit_api.pid
echo "API PID: $API_PID"
sleep 3

echo "=== HEALTH CHECK ==="
curl -s http://localhost:5000/health | python3 -m json.tool

echo "=== STATS CHECK ==="
curl -s http://localhost:5000/api/stats | python3 -m json.tool

echo "=== ORGS CHECK ==="
curl -s "http://localhost:5000/api/organizations?per_page=2" | python3 -m json.tool

echo ""
echo "Done. PID saved to logs/merit_api.pid"
