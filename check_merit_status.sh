#!/bin/bash
echo "=========================================="
echo "      MERITGIVING SERVER STATUS CHECK"
echo "=========================================="
echo ""

# 1. Check screen sessions
echo "--- SCREEN SESSIONS ---"
screen -ls | grep merit || echo "No merit screens found"
echo ""

# 2. Check API process (Flask/FastAPI)
echo "--- API PROCESS ---"
ps aux | grep -E "python.*app|uvicorn|flask" | grep -v grep || echo "No API process found"
echo ""

# 3. Check ports
echo "--- PORT LISTENING ---"
ss -tlnp | grep -E "5000|8000|3000|5173" || netstat -tlnp 2>/dev/null | grep -E "5000|8000|3000|5173" || echo "No relevant ports found"
echo ""

# 4. Test API health
echo "--- API HEALTH CHECK ---"
for port in 5000 8000; do
  response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/api/health 2>/dev/null || echo "000")
  if [ "$response" = "200" ]; then
    echo "localhost:$port/api/health -> OK (200)"
  else
    echo "localhost:$port/api/health -> FAIL ($response)"
  fi
done
echo ""

# 5. Test frontend
echo "--- FRONTEND CHECK ---"
for port in 3000 5173; do
  response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port 2>/dev/null || echo "000")
  if [ "$response" = "200" ] || [ "$response" = "307" ]; then
    echo "localhost:$port -> OK ($response)"
  else
    echo "localhost:$port -> FAIL ($response)"
  fi
done
echo ""

# 6. Check database
echo "--- DATABASE CHECK ---"
if [ -f data/meritgiving.db ]; then
  size=$(du -h data/meritgiving.db | cut -f1)
  rows=$(sqlite3 data/meritgiving.db "SELECT COUNT(*) FROM registry;" 2>/dev/null || echo "ERROR")
  echo "Database: $size | Registry rows: $rows"
else
  echo "Database not found at data/meritgiving.db"
fi
echo ""

# 7. Check Cloudflare tunnel (if used)
echo "--- TUNNEL STATUS ---"
ps aux | grep cloudflared | grep -v grep || echo "No cloudflared tunnel running"
echo ""

echo "=========================================="
echo "Done. If API shows FAIL, start it with:"
echo "  screen -S daanaa_api -d -m python3 merit_app.py"
echo "=========================================="
