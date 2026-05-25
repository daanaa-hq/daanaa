#!/bin/bash
echo "=== KILLING EVERYTHING ON PORT 5000 ==="
fuser -k 5000/tcp 2>/dev/null || true
pkill -9 -f "python.*merit_api\|python.*daanaa_api" 2>/dev/null || true
pkill -9 -f "uvicorn" 2>/dev/null || true
pkill -9 -f "flask" 2>/dev/null || true
sleep 2

echo "=== VERIFY PORT IS FREE ==="
fuser 5000/tcp 2>/dev/null && echo "Port still in use!" || echo "Port 5000 is free"

echo "=== STARTING DAANAA API (gunicorn) ==="
source ~/meritgiving/venv/bin/activate
cd ~/meritgiving
[ -f .env ] && export $(grep -v '^#' .env | xargs)
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 \
  --access-logfile logs/gunicorn_access.log \
  --error-logfile logs/daanaa_api.log \
  --pid logs/merit_api.pid \
  daanaa_api:app &
API_PID=$!
echo "API PID: $API_PID (gunicorn master)"
sleep 3

echo "=== HEALTH CHECK ==="
curl -s http://localhost:5000/health | python3 -m json.tool

echo "=== STATS CHECK ==="
curl -s http://localhost:5000/api/stats | python3 -m json.tool

echo ""
echo "Done. PID saved to logs/merit_api.pid"
