# Rename Plan: "merit" → "daanaa" (2026-06-04 after 10pm)

## Objective
Rename all "merit" references to "daanaa" to align with product branding. Execute after 10pm when token budget available.

## Scope & Files

### High Priority (Core API)
1. **merit_api.py** → **daanaa_api.py**
   - Update all flask app references
   - Update import statements
   - Update route decorators

2. **Frontend config** (src/api.ts)
   - Update API base URL references
   - Update VITE_API_URL if hardcoded

3. **Database schema references** (if any hardcoded)
   - Table names should stay (registry_enriched, v4_scores, etc.)
   - Only public-facing names change

### Medium Priority (Scripts & Config)
4. **restart_api.sh** — update gunicorn references
5. **Environment variables** — update DAANAA_* references
6. **.gitignore** patterns (merit_* → daanaa_*)
7. **Startup references** in crontab or systemd

### Low Priority (Internal/Comments)
8. Code comments mentioning "merit scoring"
9. Variable names (merit_score column stays, but merit_score variable references)
10. Log file paths (/logs/merit_*.log → /logs/daanaa_*.log)

## Execution Steps

### 1. Safety Prep (Before 10pm)
```bash
# Create backup branch
git checkout -b backup-before-rename-2026-06-04
git push origin backup-before-rename-2026-06-04

# List all files to be renamed
find . -name "*merit*" -type f | grep -v ".git" | grep -v "__pycache__"
```

### 2. Core Rename (After 10pm, ~15 min)
```bash
# Main API file
mv merit_api.py daanaa_api.py

# Update all Python imports
grep -r "merit_api" --include="*.py" | sed 's/:.*//g' | sort -u | xargs -I {} sed -i 's/from merit_api/from daanaa_api/g; s/import merit_api/import daanaa_api/g' {}

# Update frontend API URLs
sed -i "s|/merit-api|/daanaa-api|g; s|merit_api|daanaa_api|g" frontend/src/api.ts

# Update shell scripts
sed -i 's/merit_api/daanaa_api/g; s/merit-api/daanaa-api/g' restart_api.sh
```

### 3. Environment Variables (~2 min)
```bash
# Update in .env, systemd, crontab
# MERIT_* → DAANAA_*
# merit_* → daanaa_*
```

### 4. Verification (~5 min)
```bash
# Test API startup
./restart_api.sh

# Test health endpoint
curl http://localhost:5000/health

# Test sample org endpoint
curl http://localhost:5000/api/organizations/320048308 | python3 -m json.tool | head -20

# Check logs for errors
tail -50 logs/daanaa_api.log
```

### 5. Commit (~2 min)
```bash
git add -A
git commit -m "refactor: rename merit → daanaa across codebase

- merit_api.py → daanaa_api.py
- Updated all imports and references
- Updated frontend API endpoint names
- Updated environment variables
- Updated restart scripts and logs
- All API endpoints verified working
- Health check passing

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

## Rollback Plan (If anything breaks)

### Quick Rollback (< 5 min)
```bash
# Kill API
pkill gunicorn

# Revert rename
git reset --hard HEAD~1

# Restart old API
./restart_api.sh

# Verify
curl http://localhost:5000/health
```

### Full Rollback (< 10 min)
```bash
# Switch to backup branch
git checkout backup-before-rename-2026-06-04

# Force push to main (if needed)
git push -f origin backup-before-rename-2026-06-04:master
```

## Testing Checklist

- [ ] API starts without errors
- [ ] Health endpoint responds: `{"db_exists": true, "status": "ok"}`
- [ ] Org detail endpoint returns v4 scores
- [ ] Frontend can fetch orgs (check browser console)
- [ ] No 404s on API routes
- [ ] Logs show no import errors
- [ ] Git history preserved

## Timeline

**Before 10pm:**
- Read this plan
- Create backup branch (git)
- Identify all files to update

**After 10pm (when tokens available):**
- Execute core rename (15 min)
- Verify API (5 min)
- Test endpoints (5 min)
- Commit (2 min)
- **Total: ~27 minutes**

**If issues:**
- Diagnose (5 min)
- Fix or rollback (5 min)
- Re-test (5 min)

## Notes

- Database table/column names stay unchanged (schema is separate from branding)
- Only public-facing "merit_api" → "daanaa_api"
- Variables like `merit_score` are data columns, keep them
- Environment variable prefix: DAANAA_* (was MERIT_*)
- Log file pattern: daanaa_api.log, daanaa_*.log (not merit_*.log)
