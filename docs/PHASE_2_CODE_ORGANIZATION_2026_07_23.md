# Phase 2: Code Organization & Endpoint Classification

**Date:** 2026-07-23  
**Status:** LAUNCHING  
**Goal:** Organize 167 missing endpoints into native/proxy categories, implement compliance-first audit logging, fix proxy routing bug.

---

## Executive Summary

Phase 1 verified droplet capacity: 35% CPU, 35% RAM headroom with Qwen3-30B-A3B MoE. Phase 2 organizes the 212-endpoint platform by compute cost:

- **~40 native endpoints** (high-value, low-latency): read-only catalog + ML inference (missions, embeddings, cause-tags)
- **~120 proxy endpoints** (business logic, external): volunteer workflow, claims, email, admin, discovery
- **~50 legacy/compatibility endpoints** (v4 tiers, deprecated): kept for backwards compatibility

### Key Deliverables

1. **Endpoint classification matrix** — every endpoint categorized by compute cost + routing
2. **Proxy route setup** — 60 critical routes for interest→email→claim workflow
3. **Audit logging schema** — compliance-first, event-type + timestamp + user_auth + EIN (NO PII)
4. **Database schema review** — volunteer_hours_events, volunteer_contexts, audit_log
5. **Deployment checklist** — smoke tests, rollback strategy, monitoring

---

## Part 1: Endpoint Classification (Reference Matrix)

### Category A: Native Endpoints (Droplet, Fast Path)

**Read-Only Catalog + Caching**

| Endpoint | Method | Latency | Comment |
|----------|--------|---------|---------|
| `GET /` | GET | <50ms | SPA fallback |
| `GET /health` | GET | <10ms | Droplet health |
| `GET /api/stats` | GET | <50ms | Cached aggregates |
| `GET /api/stats/sectors` | GET | <50ms | Cached by sector |
| `GET /api/organizations` | GET | <100ms | Paginated, indexed |
| `GET /api/organizations/<ein>` | GET | <50ms | Org lookup (cache) |
| `GET /api/organizations/<ein>/summary` | GET | <50ms | Summary view |
| `GET /api/search` | GET | <50ms | FTS5 search (cached) |
| `GET /api/search/fuzzy` | GET | <100ms | Fuzzy search, cached |
| `GET /api/ntee` | GET | <50ms | NTEE codes (cached) |
| `GET /api/ntee/<code>` | GET | <50ms | NTEE detail |
| `GET /api/ntee/<code>/peers` | GET | <100ms | Peer group (cached) |
| `GET /api/guides` | GET | <100ms | Static guides (cached) |
| `GET /api/guides/<id>` | GET | <50ms | Guide detail |
| `GET /api/methodology` | GET | <100ms | Methodology doc |
| `GET /api/sector-health` | GET | <50ms | Sector health index |
| `GET /api/sector-health/<sector>` | GET | <50ms | Sector detail |
| `GET /api/cause-tags` | GET | <100ms | All cause tags |
| `GET /api/cause-tags/<id>` | GET | <50ms | Tag detail |
| `GET /api/hidden-gems` | GET | <100ms | Weekly rotation (cached) |
| `GET /api/organizations/<ein>/giving` | GET | <100ms | Giving context (cached) |

**ML Inference (Qwen3 Native)**

| Endpoint | Method | Latency | Model | Comment |
|----------|--------|---------|-------|---------|
| `POST /api/missions` | POST | <100ms | Qwen3-30B-A3B | Generate mission |
| `POST /api/missions/batch` | POST | <500ms | Qwen3-30B-A3B | Batch mission gen |
| `GET /api/organizations/<ein>/mission` | GET | <50ms | Cached | Stored mission |
| `POST /api/embeddings/query` | POST | <50ms | mxbai-embed-large | Query embedding |
| `POST /api/embeddings/org/<ein>` | POST | <50ms | mxbai-embed-large | Org embedding |
| `POST /api/cause-tags/suggest` | POST | <100ms | Mistral-7B | Suggest tags |

**Static/Precomputed Assets**

| Endpoint | Method | Latency | Source | Comment |
|----------|--------|---------|--------|---------|
| `GET /api/research` | GET | <50ms | precompute/ | Research snapshot |
| `GET /api/research/methodology` | GET | <50ms | precompute/ | Methodology snapshot |
| `GET /api/homepage-content` | GET | <50ms | precompute/ | Homepage data |
| `GET /api/homepage-content/featured` | GET | <50ms | precompute/ | Featured orgs |

---

### Category B: Proxy Endpoints (Home Server)

**Volunteer Workflow (Critical Path)**

| Endpoint | Method | Auth | Latency | Comment |
|----------|--------|------|---------|---------|
| `POST /api/interest` | POST | Optional | <100ms | Volunteer interest signal (sendBeacon) |
| `POST /api/interest/batch` | POST | Optional | <500ms | Batch interest signals |
| `GET /api/interest/summary` | GET | Admin | <200ms | Interest summary (admin only) |
| `GET /api/volunteer-events` | GET | Public | <100ms | Upcoming events |
| `GET /api/volunteer-events/<id>` | GET | Public | <100ms | Event detail |
| `GET /api/volunteer-events/<id>/claim` | POST | Firebase | <200ms | Claim event (nonprofit) |
| `GET /api/organizations/<ein>/volunteer-events` | GET | Public | <100ms | Org's hosted events |
| `POST /api/volunteer-hours` | POST | Firebase | <200ms | Log volunteer hours |
| `GET /api/volunteer-hours/summary` | GET | Firebase | <200ms | Volunteer summary |
| `POST /api/volunteer-hours/approve` | POST | Firebase+Role | <200ms | Approve volunteer hours |
| `GET /api/volunteer-hours/pending` | GET | Firebase+Role | <200ms | Pending approvals |

**Nonprofit Portal (Profile Contexts)**

| Endpoint | Method | Auth | Latency | Comment |
|----------|--------|------|---------|---------|
| `GET /api/profile-contexts` | GET | Firebase | <200ms | List contexts |
| `POST /api/profile-contexts` | POST | Firebase | <200ms | Create context |
| `GET /api/profile-contexts/<id>` | GET | Firebase | <200ms | Context detail |
| `PUT /api/profile-contexts/<id>` | PUT | Firebase+Role | <200ms | Update context |
| `POST /api/profile-contexts/<id>/invite` | POST | Firebase+Role | <200ms | Invite member |
| `GET /api/profile-contexts/<id>/invitations` | GET | Firebase+Role | <200ms | List invites |
| `POST /api/profile-contexts/<id>/invitations/<inv_id>/accept` | POST | Firebase | <200ms | Accept invite |
| `POST /api/profile-contexts/<id>/invitations/<inv_id>/reject` | POST | Firebase | <200ms | Reject invite |
| `POST /api/profile-contexts/<id>/members/<uid>/remove` | POST | Firebase+Role | <200ms | Remove member |
| `PUT /api/profile-contexts/<id>/members/<uid>/role` | PUT | Firebase+Role | <200ms | Change role |

**Email Triggers & Notifications**

| Endpoint | Method | Auth | Latency | Comment |
|----------|--------|------|---------|---------|
| `POST /api/email/interest-notification` | POST | Internal | <200ms | Email on interest |
| `POST /api/email/claim-notification` | POST | Internal | <200ms | Email on claim |
| `POST /api/email/hours-approval-notification` | POST | Internal | <200ms | Email on approval |
| `POST /api/email/invitation` | POST | Internal | <200ms | Invite email |
| `POST /api/email/send` | POST | Internal | <500ms | Generic email send |
| `GET /api/email/templates` | GET | Internal | <100ms | Email template list |
| `GET /api/email/templates/<name>` | GET | Internal | <50ms | Template detail |

**Admin & Discovery**

| Endpoint | Method | Auth | Latency | Comment |
|----------|--------|------|---------|---------|
| `GET /api/admin/intent/summary` | GET | Admin | <200ms | Interest summary |
| `GET /api/admin/intent/by-sector` | GET | Admin | <200ms | Interest by sector |
| `GET /api/admin/intent/by-location` | GET | Admin | <200ms | Interest by location |
| `GET /api/admin/discovery/queue` | GET | Admin | <200ms | Discovery queue |
| `POST /api/admin/discovery/queue/process` | POST | Admin | <500ms | Process queue item |
| `GET /api/admin/discovery/stats` | GET | Admin | <200ms | Discovery stats |
| `PUT /api/admin/discovery/<ein>` | PUT | Admin | <200ms | Update discovery |
| `GET /api/admin/audit-log` | GET | Admin | <200ms | Audit log (filtered) |
| `GET /api/admin/audit-log/<event_id>` | GET | Admin | <100ms | Audit log detail |

---

### Category C: Legacy/Compatibility Endpoints (Soft Deprecate)

| Endpoint | Method | Status | Replacement | Notes |
|----------|--------|--------|-------------|-------|
| `GET /api/organizations/<ein>/merit-score` | GET | Deprecated | `/api/organizations/<ein>` + score in body | Use v5 score |
| `GET /api/organizations/<ein>/merit-tier` | GET | Deprecated | `/api/organizations/<ein>` + tier in body | Use v5 band |
| Various v4 sorting endpoints | GET | Deprecated | v5 endpoints | Query on v5 fields |

---

## Part 2: Proxy Route Setup (Critical Path)

### Configuration: scripts/droplet_api.py Proxy Routes

**These routes MUST proxy to home server (`http://home.local:5000`)**

```python
# Volunteer workflow (interest → email → claim)
@app.route('/api/interest', methods=['POST', 'GET'])
@app.route('/api/volunteer-events', methods=['GET'])
@app.route('/api/volunteer-events/<event_id>', methods=['GET', 'POST'])
@app.route('/api/volunteer-hours', methods=['POST', 'GET'])
@app.route('/api/volunteer-hours/approve', methods=['POST'])
@app.route('/api/volunteer-hours/pending', methods=['GET'])
@app.route('/api/organizations/<ein>/volunteer-events', methods=['GET'])

# Nonprofit portal (profile contexts)
@app.route('/api/profile-contexts', methods=['GET', 'POST'])
@app.route('/api/profile-contexts/<context_id>', methods=['GET', 'PUT', 'DELETE'])
@app.route('/api/profile-contexts/<context_id>/invite', methods=['POST'])
@app.route('/api/profile-contexts/<context_id>/invitations', methods=['GET'])
@app.route('/api/profile-contexts/<context_id>/invitations/<inv_id>/<action>', methods=['POST'])
@app.route('/api/profile-contexts/<context_id>/members/<uid>/remove', methods=['POST'])
@app.route('/api/profile-contexts/<context_id>/members/<uid>/role', methods=['PUT'])

# Email & notifications
@app.route('/api/email/<email_type>', methods=['POST'])
@app.route('/api/email/templates', methods=['GET'])
@app.route('/api/email/templates/<template_name>', methods=['GET'])

# Admin & discovery
@app.route('/api/admin/intent/<intent_type>', methods=['GET', 'POST'])
@app.route('/api/admin/discovery/<discovery_action>', methods=['GET', 'POST', 'PUT'])
@app.route('/api/admin/audit-log', methods=['GET'])
@app.route('/api/admin/audit-log/<event_id>', methods=['GET'])
```

### Proxy Implementation Pattern

```python
@app.route('/api/<path:proxy_path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_to_home(proxy_path):
    """Route expensive operations to home server."""
    
    # Verify proxy is configured
    HOME_SERVER_URL = os.environ.get('HOME_SERVER_URL', 'http://home.local:5000')
    
    # Reconstruct query string
    query_string = request.query_string.decode('utf-8') if request.query_string else ''
    target_url = f"{HOME_SERVER_URL}/api/{proxy_path}"
    if query_string:
        target_url += f"?{query_string}"
    
    # Forward headers (preserve auth, content-type)
    headers = {k: v for k, v in request.headers if k.lower() not in ['host', 'connection']}
    
    # Proxy request
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            timeout=30
        )
        return (resp.content, resp.status_code, dict(resp.headers))
    except requests.RequestException as e:
        return {'error': 'Home server unavailable', 'detail': str(e)}, 503
```

---

## Part 3: Audit Logging Schema

### Table: `audit_log` (SQLite)

```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Core audit
    event_type TEXT NOT NULL,  -- 'volunteer_interest', 'claim_created', 'hours_approved', etc.
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- User context (NO PII)
    user_auth TEXT,  -- Firebase UID (hashed) or 'anonymous'
    user_role TEXT,  -- 'lead', 'support', 'member', 'viewer', 'admin'
    
    -- Organization context (EIN only, NO name)
    org_ein TEXT,
    
    -- Event context
    event_id INTEGER,
    volunteer_event_id INTEGER,
    
    -- Data (sanitized, NO sensitive fields)
    hours_submitted DECIMAL(5,2),
    hours_approved DECIMAL(5,2),
    context_id INTEGER,
    invite_token_hash TEXT,  -- Hashed for replay detection, not user identity
    
    -- Compliance
    ip_address_anonymized TEXT,  -- Last octet zeroed (e.g., "192.168.1.0")
    user_agent_category TEXT,  -- Browser/Mobile/Unknown (not full user agent)
    
    -- Status
    success BOOLEAN,
    error_code TEXT,
    
    -- Indexed for queries
    INDEX event_type_timestamp (event_type, timestamp),
    INDEX org_ein_timestamp (org_ein, timestamp),
    INDEX user_auth_timestamp (user_auth, timestamp)
);
```

### Event Types (Allowed)

```
volunteer_interest_submitted
volunteer_interest_batch_submitted
event_claimed
event_claim_rejected
hours_logged
hours_approved
hours_rejected
profile_context_created
profile_context_updated
member_invited
member_joined
member_removed
member_role_changed
email_sent
email_failed
admin_query_executed
discovery_queue_processed
```

### Implementation Pattern

```python
def log_audit(event_type, org_ein=None, user_auth=None, user_role=None, **kwargs):
    """
    Log audit event with PRIVACY-INVARIANTS compliance.
    
    - NO PII in kwargs (user name, email, IP except anonymized, donation data)
    - EIN-only org identification
    - Firebase UID or 'anonymous'
    - Sanitized IP (last octet zeroed)
    """
    import hashlib
    from datetime import datetime
    from flask import request
    
    # Anonymize IP: last octet zeroed
    client_ip = request.remote_addr or 'unknown'
    parts = client_ip.split('.')
    if len(parts) == 4:
        parts[-1] = '0'
        ip_anon = '.'.join(parts)
    else:
        ip_anon = 'unknown'
    
    # Sanitize user agent (category only)
    ua = request.user_agent.string or ''
    if 'mobile' in ua.lower():
        ua_category = 'mobile'
    elif 'mozilla' in ua.lower() or 'chrome' in ua.lower():
        ua_category = 'browser'
    else:
        ua_category = 'unknown'
    
    # Insert audit record
    db = get_db()
    db.execute('''
        INSERT INTO audit_log (
            event_type, timestamp, user_auth, user_role, org_ein,
            ip_address_anonymized, user_agent_category,
            success, error_code, ...extra fields from kwargs...
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ...)
    ''', (
        event_type, datetime.utcnow(), user_auth, user_role, org_ein,
        ip_anon, ua_category, True, None, ...
    ))
    db.commit()
```

---

## Part 4: Database Schema Review

### Tables Required

| Table | Status | Location | Comment |
|-------|--------|----------|---------|
| `registry_enriched` | ✅ Exists | merit_registry.db | Org data (v5 scores) |
| `org_fts` | ✅ Exists | merit_registry.db | FTS5 search index |
| `org_embeddings` | ✅ Exists | merit_registry.db | Vector store (mxbai) |
| `volunteer_hours_events_impact` | ✅ Exists | merit_registry.db | Volunteer events |
| `volunteer_contexts` | ⚠️ Review | merit_registry.db | Profile contexts + roles |
| `volunteer_context_members` | ⚠️ Review | merit_registry.db | Context membership |
| `volunteer_context_invitations` | ⚠️ Review | merit_registry.db | Pending invites |
| `audit_log` | 🆕 Create | merit_registry.db | Compliance audit trail |

### Volunteer Schema Validation

**Ensure NO donor data in volunteer tables:**

```sql
-- volunteer_contexts: EIN + org rep only
ALTER TABLE volunteer_contexts ADD COLUMN org_ein TEXT NOT NULL;
ALTER TABLE volunteer_contexts ADD COLUMN created_by_uid TEXT NOT NULL;  -- Firebase UID
ALTER TABLE volunteer_contexts ADD COLUMN context_type TEXT;  -- 'household', 'daf', 'business'
ALTER TABLE volunteer_contexts ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE volunteer_contexts ADD CONSTRAINT no_wallet_ref CHECK (wallet_id IS NULL);

-- volunteer_context_members: roles + invite status
ALTER TABLE volunteer_context_members ADD COLUMN uid TEXT NOT NULL;  -- Firebase UID
ALTER TABLE volunteer_context_members ADD COLUMN role TEXT CHECK (role IN ('lead', 'support', 'member', 'viewer'));
ALTER TABLE volunteer_context_members ADD COLUMN joined_at DATETIME;
ALTER TABLE volunteer_context_members ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- volunteer_context_invitations: 14-day expiry + token hash
ALTER TABLE volunteer_context_invitations ADD COLUMN email TEXT NOT NULL;
ALTER TABLE volunteer_context_invitations ADD COLUMN token_hash TEXT NOT NULL;  -- bcrypt hash
ALTER TABLE volunteer_context_invitations ADD COLUMN expires_at DATETIME NOT NULL;
ALTER TABLE volunteer_context_invitations ADD COLUMN accepted_at DATETIME;
ALTER TABLE volunteer_context_invitations ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE volunteer_context_invitations ADD CONSTRAINT no_wallet_ref CHECK (wallet_id IS NULL);
```

---

## Part 5: Deployment Checklist

### Pre-Deployment Verification

- [ ] All 212 endpoints classified (native vs. proxy)
- [ ] Proxy routes implemented in scripts/droplet_api.py
- [ ] Audit logging schema created + tested
- [ ] Volunteer tables reviewed + no donor data leakage
- [ ] Privacy invariants check passes
- [ ] Profile Contexts proxy routing bug fixed
- [ ] Home server (daanaa_api.py) updated with all endpoints
- [ ] Local tests pass (81+ tests)
- [ ] Frontend tests pass (215+ tests)

### Smoke Tests (Before Deploying)

```bash
# 1. Droplet native endpoints
curl -s https://daanaa.org/api/organizations/391214392 | jq '.ein' > /dev/null && echo "✓ Org lookup"
curl -s https://daanaa.org/api/search?q=food | jq '.results | length > 0' > /dev/null && echo "✓ Search"

# 2. Proxy endpoints (via home server)
curl -s -X POST https://daanaa.org/api/interest -d '{}' | jq '.status' > /dev/null && echo "✓ Interest signal"
curl -s https://daanaa.org/api/volunteer-events | jq '.[] | .id' > /dev/null && echo "✓ Events list"

# 3. Audit logging
curl -s https://daanaa.org/api/admin/audit-log | jq '.[0].event_type' > /dev/null && echo "✓ Audit log"

# 4. Profile Contexts (if enabled)
curl -s https://daanaa.org/api/profile-contexts | jq '.error' | grep -q "permission\|disabled" && echo "✓ Profile Contexts (properly gated)"

# 5. SPA fallback (non-API routes)
curl -s https://daanaa.org/organizations/391214392 | grep -q "<html" && echo "✓ SPA fallback"
```

### Rollback Strategy

```bash
# If deployment fails:
# 1. Revert scripts/droplet_api.py to last good commit
git checkout HEAD~1 scripts/droplet_api.py

# 2. Restart service
systemctl restart daanaa

# 3. Re-run smoke tests to verify rollback
./verify_smoke_tests.sh

# 4. Log incident in DECISIONS.md
```

---

## Part 6: Implementation Order

### Week 1 (This Week)

1. **Day 1-2**: Endpoint classification + proxy setup
2. **Day 2-3**: Audit logging schema + home server audit events
3. **Day 3-4**: Fix Profile Contexts proxy routing bug
4. **Day 4-5**: Deploy all endpoints to droplet + smoke test
5. **Day 5-6**: Load testing (50K req/day capacity)
6. **Day 6-7**: Documentation + board briefing

### Blockers to Resolve First

1. **Profile Contexts API returning HTML** — proxy routing bug in Flask (request.path handling)
2. **Event detail routes 404** — sync issue or service restart needed
3. **Home server availability** — must be running before proxy routes work

---

## Success Criteria

✅ **PASS**: All 212 endpoints routed correctly (native vs. proxy)  
✅ **PASS**: Proxy latency <300ms P95 (local network)  
✅ **PASS**: Audit logging captures all events (event_type + timestamp + EIN only)  
✅ **PASS**: No donor data leaks in volunteer tables  
✅ **PASS**: Smoke tests 10/10 passing  
✅ **PASS**: Load test: 50K req/day + 100 concurrent claims  

---

**Next Action**: Implement Part 1 (endpoint classification matrix) + Part 2 (proxy routes).  
**Estimated Duration**: 4-6 hours  
**Owner**: Claude Code (autonomous backend, no approval needed)
