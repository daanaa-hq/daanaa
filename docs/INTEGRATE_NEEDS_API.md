# Integration Guide: Needs Network API

**Status:** Ready to integrate  
**Files:** `scripts/needs_api_routes.py`  
**Target:** `daanaa_api.py` (Flask app)

---

## Quick Start

### 1. Apply Database Migration

```bash
python3 ~/meritgiving/scripts/run_migration_004_needs_network.py
```

Expected output:
```
✅ MIGRATION 004 COMPLETE
Tables ready:
  - needs (live Needs published by nonprofits)
  - need_intakes (submissions + AI drafts)
  - need_approvals (approval audit trail)
  - need_freshness_log (re-confirmation tracking)
  - need_donor_interest (interest signals)
```

### 2. Import Routes into daanaa_api.py

Add to imports section (around line 15):

```python
from scripts.needs_api_routes import (
    get_needs,
    get_nonprofit_needs,
    create_need,
    confirm_need,
    record_need_interest,
    check_needs_freshness
)
```

### 3. Register Routes

Add these Flask routes to `daanaa_api.py` (after existing org routes, around line 2500):

```python
# ============================================================================
# NEEDS NETWORK API (Phase 3B)
# ============================================================================

@app.route('/api/needs', methods=['GET'])
def api_get_needs():
    """Search published Needs (donor-facing)."""
    need_type = request.args.get('need_type')  # FUNDING, VOLUNTEER
    primary_state = request.args.get('primary_state')  # NY, CA, etc.
    cause_area = request.args.get('cause_area')  # Food, Health, etc.

    result = get_needs(need_type, primary_state, cause_area)
    return jsonify(result)


@app.route('/api/nonprofits/<ein>/needs', methods=['GET'])
def api_nonprofit_needs(ein):
    """List all Needs for a nonprofit (nonprofit dashboard)."""
    status = request.args.get('status')  # Optional: filter by status

    result = get_nonprofit_needs(ein, status)
    return jsonify(result)


@app.route('/api/nonprofits/<ein>/needs', methods=['POST'])
def api_create_need(ein):
    """Create a new Need (DRAFT status)."""
    # Nonprofit auth check (implementation detail — validate ein ownership)
    # if not is_nonprofit_authorized(ein):
    #     return jsonify({'error': 'Unauthorized'}), 403

    body = request.get_json()
    result, status_code = create_need(ein, body)
    return jsonify(result), status_code


@app.route('/api/needs/<need_id>/confirm', methods=['POST'])
def api_confirm_need(need_id):
    """Nonprofit confirms a Need is still valid (Stewardship P6)."""
    body = request.get_json()
    ein = body.get('ein')

    result, status_code = confirm_need(need_id, ein)
    return jsonify(result), status_code


@app.route('/api/needs/<need_id>/interest', methods=['POST'])
def api_record_interest(need_id):
    """Record donor/volunteer interest in a Need."""
    body = request.get_json()
    interest_type = body.get('interest_type')
    org_size = body.get('org_size')

    result, status_code = record_need_interest(need_id, interest_type, org_size)
    return jsonify(result), status_code
```

### 4. Wire Freshness Check to Nightly Pipeline

Add to `overnight_pipeline.py` (around line 80, after FTS rebuild):

```python
# Check Needs for freshness (Stewardship P6)
from scripts.needs_api_routes import check_needs_freshness

logger.info("Checking Need freshness...")
freshness_result = check_needs_freshness()
logger.info(f"  Needs pending confirmation: {freshness_result['needs_pending_confirmation']}")
logger.info(f"  Needs auto-archived: {freshness_result['needs_auto_archived']}")
```

---

## API Endpoint Reference

### Public (Donor-Facing) Endpoints

#### GET /api/needs
Search published Needs.

**Query params:**
```
?need_type=FUNDING              # optional
&primary_state=NY              # optional
&cause_area=Food               # optional
```

**Response:**
```json
{
  "needs": [
    {
      "need_id": "532000161-FUNDING-2026-08-09T...",
      "ein": "532000161",
      "need_type": "FUNDING",
      "title": "Summer Camp Scholarships",
      "description": "Help us send 50 kids to camp...",
      "amount_needed": 25000,
      "deadline_date": "2026-09-30",
      "primary_state": "NY",
      "cause_area": "Youth",
      "status": "PUBLISHED",
      "published_date": "2026-08-01T...",
      "click_count": 127,
      "volunteer_interest_count": 8
    }
  ],
  "total": 1
}
```

---

### Nonprofit-Facing Endpoints

#### GET /api/nonprofits/{ein}/needs
List all Needs for a nonprofit.

**Query params:**
```
?status=PUBLISHED              # optional: DRAFT, SUBMITTED, APPROVED, PUBLISHED, ARCHIVED
```

**Response:**
```json
{
  "needs": [...],
  "total": 3
}
```

---

#### POST /api/nonprofits/{ein}/needs
Create a new Need (DRAFT status).

**Auth:** Nonprofit must own the EIN (check via nonprofit_auth header)

**Body:**
```json
{
  "need_type": "FUNDING",
  "title": "Summer Camp Scholarships",
  "description": "Help us send 50 kids to camp",
  "amount_needed": 25000,
  "deadline_date": "2026-09-30",
  "cause_area": "Youth",
  "service_states": ["NY", "NJ", "PA"]
}
```

**Response (201 Created):**
```json
{
  "need_id": "532000161-FUNDING-2026-08-09T...",
  "ein": "532000161",
  "need_type": "FUNDING",
  "title": "Summer Camp Scholarships",
  "status": "DRAFT",
  "created_at": "2026-08-09T..."
}
```

---

#### POST /api/needs/{need_id}/confirm
Nonprofit confirms a Need is still valid.

**Auth:** Nonprofit must own the Need's EIN

**Body:**
```json
{
  "ein": "532000161"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "last_confirmed": "2026-08-09T..."
}
```

---

#### POST /api/needs/{need_id}/interest
Record donor/volunteer interest (Stewardship P2: aggregate only).

**Body:**
```json
{
  "interest_type": "VIEW",  # VIEW, SAVE, SHARE, VOLUNTEER_APPLICATION
  "org_size": "Micro"       # optional: org-level prop for analytics
}
```

**Response (200 OK):**
```json
{
  "success": true
}
```

---

## Privacy & Security Checklist

### Stewardship P2 (Privacy)
- ✅ `need_donor_interest` table stores only aggregate counts
- ✅ No PII in interest records (only `org_size` property)
- ✅ No user IDs or email addresses linked to Needs
- ✅ Responses show only aggregated `click_count` and `volunteer_interest_count`

### Auth & Validation
- ⚠️ **TODO:** Implement nonprofit ownership check for nonprofit-facing endpoints
  - Method: Validate `nonprofit_auth` header or JWT claim contains `ein`
  - Pattern: See `@app.route('/api/nonprofits/<ein>/profile')` in existing code

- ⚠️ **TODO:** Rate limiting on `/api/needs` (high-volume donor endpoint)
  - Suggest: 100 requests/minute per IP

### Data Validation (Zod-equivalent)
- ✅ `NeedType.validate()` checks required fields, types, and constraints
- ✅ `need_type` must be 'FUNDING' or 'VOLUNTEER'
- ✅ FUNDING needs require `amount_needed > 0`
- ✅ Dates validated as ISO 8601 format

---

## Testing

### Unit Test Template

```python
# tests/test_needs_api.py

import pytest
from scripts.needs_api_routes import NeedsDB

def test_create_need():
    db = NeedsDB(Path.home() / 'meritgiving' / 'data' / 'test.db')  # Use test DB
    need = db.create_need(
        ein='532000161',
        need_type='FUNDING',
        title='Test Need',
        description='Test description',
        amount_needed=5000
    )
    assert need['need_id'] is not None
    assert need['status'] == 'DRAFT'

def test_search_needs():
    db = NeedsDB(...)
    needs = db.search_needs(need_type='FUNDING', primary_state='NY')
    assert isinstance(needs, list)

def test_confirm_need():
    # Create, then confirm
    db = NeedsDB(...)
    db.create_need(...)
    success = db.confirm_need(need_id, ein)
    assert success
```

---

## Monitoring & Metrics

### Key Metrics to Track (Phase 3B)

```sql
-- Dashboard query: How many Needs have we collected?
SELECT need_type, COUNT(*) as total, 
       SUM(CASE WHEN status = 'PUBLISHED' THEN 1 ELSE 0 END) as published
FROM needs
GROUP BY need_type;

-- Dashboard query: What's the freshness status?
SELECT freshness_status, COUNT(*) as count
FROM needs
WHERE status = 'PUBLISHED'
GROUP BY freshness_status;

-- Dashboard query: Most clicked Needs (trending)
SELECT need_id, title, click_count, volunteer_interest_count
FROM needs
WHERE status = 'PUBLISHED'
ORDER BY click_count DESC
LIMIT 10;
```

---

## Rollback Plan

If issues arise, revert with:

```bash
# 1. Remove tables
sqlite3 ~/meritgiving/data/merit_registry.db "DROP TABLE IF EXISTS needs, need_intakes, need_approvals, need_freshness_log, need_donor_interest;"

# 2. Remove routes from daanaa_api.py
# (manually remove the 5 route handlers added above)

# 3. Remove import from daanaa_api.py
# (remove the needs_api_routes import)

# 4. Restart API
systemctl restart daanaa
```

---

## Next Steps

1. ✅ Database schema created (migrations/004_create_needs_network_schema.sql)
2. ✅ API routes ready (scripts/needs_api_routes.py)
3. ⏳ **INTEGRATE:** Copy route handlers into daanaa_api.py
4. ⏳ **TEST:** Run unit tests against test database
5. ⏳ **FRONTEND:** Wire nonprofit intake UI to POST /api/nonprofits/{ein}/needs
6. ⏳ **DEPLOY:** Ship with confidence

**Estimated effort to integrate:** 2-3 hours (mostly testing + frontend wiring)
