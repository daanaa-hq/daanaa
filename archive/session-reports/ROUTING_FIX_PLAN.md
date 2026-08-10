# Long-Term Fix: Routing Architecture for API + SPA

## The Problem

**Current State:**
- `droplet_api.py` mixes ~6000 lines of API routes with the SPA fallback route
- SPA fallback route `@app.route('/<path:path>')` at line 6936 is defined AFTER all API routes
- Flask evaluates routes in registration order, but with 8282 lines of code, it's hard to verify ordering
- The recall endpoints exist but may not be routing correctly due to this mixed architecture
- No way to ensure API routes are ALWAYS matched before SPA fallback

**Why It's Fragile:**
1. Easy to accidentally add a route AFTER the SPA fallback
2. Hard to debug routing issues without reading 8000+ lines
3. No automated test ensuring API routes don't get shadowed
4. Adding new features risks breaking routing order

## The Solution: Flask Blueprints

**Architecture:**
```
droplet_api.py (main app)
├── api_blueprint.py (register FIRST)
│   ├── /health
│   ├── /api/organizations/*
│   ├── /api/wallet/*
│   └── ... (all 50+ API endpoints)
└── frontend_blueprint.py (register LAST)
    └── /<path:path> (SPA fallback)
```

**Key Property:** By registering API blueprint first, Flask will always check API routes before SPA fallback, regardless of code length.

## Implementation Plan

### Phase 1: Create API Blueprint (No Breaking Changes)

```bash
# New file: blueprints/api_blueprint.py (1500 lines)
# - Move all @app.route() to @api_bp.route()
# - Keep the same endpoint functions unchanged
# - Import in droplet_api.py and register FIRST

# New file: blueprints/frontend_blueprint.py (50 lines)
# - Move SPA fallback route here
# - Register SECOND in droplet_api.py
```

### Phase 2: Clean droplet_api.py

```python
# Before (droplet_api.py ~8282 lines)
@app.route('/health') ...
@app.route('/api/organizations/<ein>/recall') ...
# ... 6900 lines of API routes ...
@app.route('/<path:path>')  # SPA fallback (risky position!)
def serve_frontend(path): ...

# After (droplet_api.py ~200 lines)
from blueprints.api_blueprint import api_bp
from blueprints.frontend_blueprint import frontend_bp

app = Flask(__name__)
app.register_blueprint(api_bp)      # Register API FIRST
app.register_blueprint(frontend_bp)  # Register SPA LAST
```

### Phase 3: Add Routing Tests

```python
# tests/test_routing.py
def test_api_routes_before_spa():
    """Ensure /api/* routes are matched before SPA fallback."""
    assert app.get('/api/organizations/832672211/recall').status_code != 404
    assert app.get('/api/health').content_type == 'application/json'
    # SPA fallback should only catch non-API routes
    assert app.get('/unknown-page').content_type == 'text/html'
```

## Benefits

| Aspect | Current | After Fix |
|--------|---------|-----------|
| **Clarity** | Mixed 8K lines | Separated by blueprint |
| **Routing Safety** | Order-dependent | Blueprint registration order |
| **Testability** | Hard to test routing | Easy routing tests |
| **Maintainability** | Add route anywhere = risky | Add to blueprint = safe |
| **New Features** | Risk breaking routing | Guaranteed safety |
| **Debugging** | Read 8282 lines | Check blueprint registration |

## Migration Path

1. **Create blueprints/** directory
2. **Move API routes** to `api_blueprint.py` (use sed/refactor script)
3. **Move SPA route** to `frontend_blueprint.py`
4. **Update droplet_api.py** to use blueprints
5. **Add routing tests** to catch regressions
6. **Deploy** to droplet with verification
7. **Delete** old code once verified

## Files to Modify

```
droplet_api.py              [~8282 → ~150 lines]
blueprints/
├── __init__.py
├── api_blueprint.py        [~6500 lines, all API routes]
└── frontend_blueprint.py   [~50 lines, SPA fallback]
tests/
└── test_routing.py         [20-30 lines, routing safety]
CLAUDE.md                   [Add routing rules section]
DECISIONS.md                [Document decision + rationale]
```

## Timeline

- **Phase 1** (1 day): Create blueprints, migrate routes
- **Phase 2** (0.5 day): Update droplet_api.py
- **Phase 3** (0.5 day): Add tests, verify locally
- **Deployment** (0.5 day): Safe deploy to droplet with rollback

## Rollback Plan

If blueprints cause issues:
```bash
git revert <blueprint-commit>
# Back to original mixed file, takes <5 minutes
```

## Why This Matters

The current architecture is a **common Flask pitfall** that burns time on debugging mysterious routing issues. The fix is simple (1 day) and pays dividends every time we add a feature going forward.
