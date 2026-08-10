#!/bin/bash
echo "=== KILLING EVERYTHING ON PORT 5000 / 8880 ==="
fuser -k 5000/tcp 2>/dev/null || true
fuser -k 8880/tcp 2>/dev/null || true
pkill -9 -f "python.*daanaa_api\|python.*daanaa_api" 2>/dev/null || true
pkill -9 -f "uvicorn" 2>/dev/null || true
pkill -9 -f "flask" 2>/dev/null || true
sleep 2

echo "=== VERIFY PORTS ARE FREE ==="
fuser 5000/tcp 2>/dev/null && echo "Port 5000 still in use!" || echo "Port 5000 is free"
fuser 8880/tcp 2>/dev/null && echo "Port 8880 still in use!" || echo "Port 8880 is free"

echo "=== STARTING DAANAA API (gunicorn) ==="
source ~/meritgiving/venv/bin/activate
cd ~/meritgiving
[ -f .env ] && export $(grep -v '^#' .env | xargs)
# Binds on both 5000 (internal/LAN) and 8880 (Cloudflare proxy — free plan
# supports port 8880 without an Enterprise origin rule).
# Privacy: access log omits the client IP (%(h)). We keep request method/path/
# status for ops visibility but never persist visitor IPs.
gunicorn -w 4 -b 0.0.0.0:5000 -b 0.0.0.0:8880 --timeout 120 --preload \
  --access-logfile logs/gunicorn_access.log \
  --access-logformat '%(t)s "%(r)s" %(s)s %(b)s %(M)sms' \
  --error-logfile logs/daanaa_api.log \
  --pid logs/daanaa_api.pid \
  daanaa_api:app &
API_PID=$!
echo "API PID: $API_PID (gunicorn master)"
sleep 3

echo "=== HEALTH CHECK ==="
curl -s http://localhost:5000/health | python3 -m json.tool

echo "=== STATS CHECK ==="
curl -s http://localhost:5000/api/stats | python3 -m json.tool

echo "=== WARMING CACHE (background) ==="
# Prime the response cache with the most common entry points so the first
# real visitor after a restart never pays the cold-query cost (~3.7s).
(
  for i in $(seq 1 30); do
    curl -sf -m 2 http://localhost:5000/health > /dev/null 2>&1 && break
    sleep 1
  done
  for q in "food+bank" "animal+shelter" "youth" "veterans" "education" "homeless"; do
    curl -sf -m 20 "http://localhost:5000/api/search?q=$q" -o /dev/null
  done
  curl -sf -m 20 "http://localhost:5000/api/organizations?page=1&per_page=24" -o /dev/null
  curl -sf -m 20 "http://localhost:5000/api/ntee-categories" -o /dev/null
  curl -sf -m 20 "http://localhost:5000/api/stats" -o /dev/null
) > /dev/null 2>&1 &

echo ""
echo "Done. PID saved to logs/daanaa_api.pid (cache warm-up running in background)"
