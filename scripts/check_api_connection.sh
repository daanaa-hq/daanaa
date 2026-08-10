#!/bin/bash
echo "=========================================="
echo "   MERIT API <> FRONTEND CONNECTION TEST"
echo "=========================================="
echo ""

# 1. Check which API is actually the Merit API
echo "--- API IDENTITY CHECK ---"
for port in 5000 8000 8001; do
  echo "Port $port:"
  curl -s http://localhost:$port/api/health 2>/dev/null | head -c 200
  echo ""
done
echo ""

# 2. Check frontend API config
echo "--- FRONTEND API CONFIG ---"
if [ -f ~/meritgiving/frontend/.env ]; then
  cat ~/meritgiving/frontend/.env
fi
if [ -f ~/meritgiving/frontend/.env.local ]; then
  cat ~/meritgiving/frontend/.env.local
fi
if [ -f ~/meritgiving/frontend/src/lib/api.ts ]; then
  echo "API base URL in code:"
  grep -n "baseURL\|VITE_API\|localhost" ~/meritgiving/frontend/src/lib/api.ts | head -20
fi
if [ -f ~/meritgiving/frontend/vite.config.ts ]; then
  echo "Vite proxy config:"
  grep -A5 -B5 "proxy" ~/meritgiving/frontend/vite.config.ts | head -30
fi
echo ""

# 3. Test actual API endpoints
echo "--- API ENDPOINT TEST (port 8001) ---"
curl -s http://localhost:8001/api/health 2>/dev/null && echo ""
curl -s "http://localhost:8001/api/organizations?limit=1" 2>/dev/null | head -c 300
echo ""
echo ""

# 4. Test from frontend perspective
echo "--- FRONTEND PROXY TEST ---"
curl -s http://localhost:3000/api/health 2>/dev/null | head -c 200
echo ""

# 5. Check duplicate screens
echo "--- SCREEN SESSIONS ---"
screen -ls | grep merit
echo ""

echo "=========================================="
