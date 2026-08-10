# Blueprint Migration Steps — Detailed Walkthrough

This document walks through the exact steps to refactor droplet_api.py into blueprints. Each step is testable and reversible.

## Pre-Migration Checklist

- [ ] Run `python3 scripts/refactor_blueprints.py --dry-run` to see the plan
- [ ] Backup: `cp droplet_api.py .backups/droplet_api.py.pre-blueprint`
- [ ] All tests passing: `pytest tests/ -v`
- [ ] Clean git status: `git status` shows no uncommitted changes in droplet_api.py

## Step 1: Create Blueprint Directory Structure

```bash
mkdir -p blueprints
touch blueprints/__init__.py
echo "# Flask blueprints for routing separation" > blueprints/__init__.py
```

**Verification:**
```bash
ls -la blueprints/
```

## Step 2: Create Frontend Blueprint

Copy the pre-written file:

```bash
cp blueprints/frontend_blueprint.py blueprints/
```

Or manually create it with content from ROUTING_FIX_PLAN.md.

**Verification:**
```bash
python3 -c "from blueprints.frontend_blueprint import frontend_bp; print('✓ frontend_bp imports')"
```

## Step 3: Extract API Routes from droplet_api.py

This is the manual part. We need to identify all `@app.route()` definitions and move them to the API blueprint.

### 3a. Count routes

```bash
grep -n "@app.route" droplet_api.py | wc -l
# Should show ~50+ routes
```

### 3b. Find the split point

Find where the SPA fallback starts:

```bash
grep -n "@app.route('/', defaults=" droplet_api.py
# Example output: 6935:@app.route('/', defaults={'path': ''})
```

Write down this line number. This is where API routes end.

### 3c. Extract API code

```bash
# Lines 1 to (SPA_LINE - 1) go into the API blueprint
# Copy from droplet_api.py up to the SPA fallback
head -n 6934 droplet_api.py > /tmp/api_routes_section.py
```

### 3d. Create api_blueprint.py

Create `blueprints/api_blueprint.py` with:

1. **Header:**
```python
"""
Daanaa API Routes (Flask Blueprint)

All /api/*, /health, and other API endpoints.
Registered FIRST in droplet_api.py.
"""

from flask import Blueprint, jsonify, request, g, abort, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3
import os
import json
# ... (import all dependencies from original droplet_api.py)

api_bp = Blueprint('api', __name__)
limiter = Limiter(key_func=get_remote_address)
```

2. **All helper functions** (copy as-is from droplet_api.py):
   - `get_db()`
   - `_load_embeddings()`
   - Cache functions
   - All utility functions
   - Example: search result processing, org formatting, etc.

3. **All route handlers** (replace `@app.route` → `@api_bp.route`):

```python
# Before
@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# After
@api_bp.route('/health')
def health():
    return jsonify({"status": "ok"})
```

**Tool to help:** Use sed to replace in the extracted section:

```bash
sed 's/@app\.route/@api_bp.route/g' /tmp/api_routes_section.py > /tmp/api_blueprint_draft.py
```

Then manually review the result and fix any issues.

### 3e. Handle decorators carefully

Some routes have `@limiter.limit()` and other decorators. Preserve them:

```python
# Keep decorator order
@api_bp.route('/api/search')
@limiter.limit("30 per minute")
def search():
    ...
```

## Step 4: Update droplet_api.py

Simplify droplet_api.py to ~150 lines:

```python
#!/usr/bin/env python3
"""
Daanaa API — Backend entry point

Uses Flask blueprints for clean routing:
  - api_blueprint.py    [all API routes, registered FIRST]
  - frontend_blueprint.py [SPA fallback, registered LAST]
"""

import os
import logging
from flask import Flask
from flask_cors import CORS

# Import blueprints
from blueprints.api_blueprint import api_bp, limiter
from blueprints.frontend_blueprint import frontend_bp

# Configure Flask app
app = Flask(__name__)
CORS(app)

# Rate limiting
limiter.init_app(app)

# Register blueprints in order: API FIRST, SPA LAST
# This ensures API routes have priority in Flask routing resolution
app.register_blueprint(api_bp)
app.register_blueprint(frontend_bp)

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return {"error": "Not found"}, 404

@app.errorhandler(500)
def server_error(e):
    return {"error": "Server error"}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

**Important:** Move any app-level middleware/configuration to the simplified droplet_api.py.

## Step 5: Add Routing Safety Tests

Copy the pre-written test file:

```bash
cp tests/test_routing.py tests/
```

## Step 6: Verify Everything Works Locally

```bash
# Test imports
python3 -c "
from droplet_api import app
from blueprints.api_blueprint import api_bp
from blueprints.frontend_blueprint import frontend_bp
print('✓ All imports successful')
"

# Run routing tests
pytest tests/test_routing.py -v

# Manual testing
python3 droplet_api.py &
sleep 2

# Test API route
curl http://localhost:5000/health | python3 -m json.tool

# Test SPA fallback
curl http://localhost:5000/unknown-page | head -c 50

pkill -f "python3 droplet_api.py"
```

## Step 7: Deploy to Staging (Droplet)

### 7a. Backup on droplet

```bash
ssh root@162.243.97.179 "cp /opt/daanaa/droplet_api.py /opt/daanaa/droplet_api.py.pre-blueprint"
```

### 7b. Upload new files

```bash
rsync -avz blueprints/ root@162.243.97.179:/opt/daanaa/blueprints/
rsync -avz droplet_api.py root@162.243.97.179:/opt/daanaa/
```

### 7c. Restart service

```bash
ssh root@162.243.97.179 "systemctl restart daanaa && sleep 3 && systemctl status daanaa"
```

### 7d. Verify API works

```bash
# Test health endpoint
curl https://daanaa.org/health | python3 -m json.tool

# Test recall endpoint (new)
curl https://daanaa.org/api/organizations/832672211/recall | python3 -m json.tool | head -30

# Test SPA fallback
curl https://daanaa.org/directory | grep -q "<!doctype html>" && echo "✓ SPA works"
```

## Step 8: Rollback Plan (If Anything Breaks)

If the deployment breaks routing:

```bash
# On droplet
ssh root@162.243.97.179
cd /opt/daanaa
cp droplet_api.py.pre-blueprint droplet_api.py
rm -rf blueprints/
systemctl restart daanaa
```

Should be back to normal in <2 minutes.

## Step 9: Commit and Document

Once verified:

```bash
git add blueprints/ droplet_api.py tests/test_routing.py DECISIONS.md
git commit -m "refactor: Use Flask Blueprints for API/SPA routing separation

- Split droplet_api.py (8282 → 150 lines) into blueprints/
  * api_blueprint.py (all API routes, registered FIRST)
  * frontend_blueprint.py (SPA fallback, registered LAST)
- Added routing safety tests (10+ assertions)
- Guarantees API routes matched before SPA fallback
- Improves code clarity and prevents future routing bugs

Fixes recall endpoint routing issue by ensuring deterministic
route evaluation order through Flask blueprint registration."

git push
```

## Troubleshooting

### Import Error: No module named 'blueprints'

**Solution:** Ensure the parent directory is in Python path. Check:
```python
import sys
print(sys.path)  # Should include /opt/daanaa
```

### 404 on /health endpoint

**Likely cause:** The health endpoint wasn't copied to api_blueprint.py correctly.

**Debug:**
```bash
grep "def health" blueprints/api_blueprint.py
grep "@api_bp.route('/health')" blueprints/api_blueprint.py
```

### SPA fallback returning 404

**Likely cause:** `frontend_bp` not registered in droplet_api.py.

**Check:**
```python
# droplet_api.py should have:
app.register_blueprint(frontend_bp)
```

## Timeline

- **Step 1-2:** 10 minutes (setup)
- **Step 3:** 30-45 minutes (code extraction, most time spent here)
- **Step 4:** 15 minutes (simplify droplet_api.py)
- **Step 5:** 5 minutes (copy tests)
- **Step 6:** 10 minutes (local verification)
- **Step 7:** 10 minutes (deploy + verify)
- **Step 8-9:** 10 minutes (rollback plan + commit)

**Total: ~2 hours for complete migration + testing**

## Success Criteria

- [ ] `pytest tests/test_routing.py -v` — all tests pass
- [ ] `/health` returns JSON
- [ ] `/api/organizations/{ein}/recall` returns JSON (not SPA)
- [ ] `/unknown-page` returns SPA HTML
- [ ] No 500 errors in service logs
- [ ] Droplet health check: `curl https://daanaa.org/health` returns JSON
