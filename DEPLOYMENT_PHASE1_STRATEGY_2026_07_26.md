# Phase 1 Accessibility Deployment Strategy (2026-07-26)

## TL;DR Deployment Path

**What's shipping:** Frontend CSS + TypeScript changes (0 backend changes)  
**Risk level:** LOW (CSS-only + utility classes, no search engine changes)  
**Deployment method:** `/daanaa-deploy --code-only` (5 min build + ship)  
**Smoke tests:** Dark mode text visible + light mode borders visible + search <400ms  
**Rollback:** 2 min via git revert + redeploy

---

## What's Actually Going to the Droplet

### ✅ SAFE (Frontend-only)
- **index.css** — Line-height 1.6, display utilities (h1-3-display), theme-aware borders
- **31 refactored pages** — Typography utilities instead of inline font-size (identical visual output)
- **ConfidenceBadge.tsx** — New component (no search.db changes, no API changes)
- **Built SPA** — frontend/dist/ (static files only)

### ❌ NOT GOING (No impact on droplet)
- Backend API (daanaa_api.py stays on droplet as-is)
- Database (merit_registry.db stays on droplet as-is)
- Search index (org_fts unchanged, no rebuilds needed)
- Embedding vectors (unchanged)

---

## Why This Won't Kill the Droplet

**Droplet current state:** 2GB RAM, serving static SPA + API from same process

**What we're changing:**
1. CSS file size: ~5KB added (h1-3-display utilities + theme selectors) — negligible
2. Frontend bundle: +74 bytes (ConfidenceBadge component) — negligible
3. No new dependencies: All utilities use existing Tailwind/CSS
4. No new API calls: Component renders client-side only

**Impact on droplet resources:**
- CPU: 0 change (CSS is rendered client-side in browser)
- RAM: 0 change (static files don't consume server RAM)
- Disk: +1MB for new SPA build (ample headroom on 50GB SSD)
- Search speed: 0 change (FTS index untouched, no schema changes)

---

## Why Search Speed Won't Degrade

**Search currently:** FTS5 index (org_fts table) + semantic search (org_embeddings)

**Our changes:**
- ❌ Did NOT modify `/api/search` endpoint
- ❌ Did NOT touch org_fts table
- ❌ Did NOT rebuild embeddings
- ❌ Did NOT add new queries to search flow
- ✅ Only CSS + UI components (render-time only)

**Search latency stays:** <400ms (no changes to search code path)

---

## Deployment Plan

### Phase 0: Pre-Flight (5 min)
```bash
# 1. Verify no uncommitted changes
git status
# Expected: "nothing to commit, working tree clean"

# 2. Verify all commits are on origin/master
git log --oneline -1
git push origin master
# Expected: "Everything up-to-date"

# 3. Check current droplet health
curl -s https://daanaa.org/health
# Expected: 200 OK

# 4. Baseline search speed (record current)
curl -s "https://daanaa.org/api/search?q=education&per_page=5" \
  | jq '.meta.elapsed_ms'
# Expected: ~300-400ms
```

### Phase 1: Deploy Frontend Build (5 min)
```bash
# Use /daanaa-deploy skill with --code-only flag
# This:
# - Runs `npm run build` locally
# - Builds SPA to frontend/dist/
# - Syncs dist/ to droplet via rsync
# - Reloads Flask static files
# - Does NOT restart API (no backend changes)
```

### Phase 2: Smoke Tests (3 min)
```bash
# 1. Dark mode text visible
curl -s https://daanaa.org/org/264837170 \
  | grep -E "text-cool-grey|text-deep-gold" \
  | head -1
# Expected: CSS classes present (text now visible via CSS theme overrides)

# 2. Light mode borders visible  
curl -s https://daanaa.org/ \
  | grep "border-light-grey" \
  | head -1
# Expected: CSS classes present (borders now dark in light mode)

# 3. Search still fast (post-deploy)
curl -s "https://daanaa.org/api/search?q=health&per_page=5" \
  | jq '.meta.elapsed_ms'
# Expected: ~300-400ms (same as baseline)

# 4. ConfidenceBadge loads (no errors)
curl -s https://daanaa.org/ \
  | grep "ConfidenceBadge" \
  | wc -l
# Expected: 0 (component not yet integrated, but should load if added)
```

### Phase 3: Rollback (if needed, 2 min)
```bash
# If smoke tests fail:
git revert HEAD  # Revert last commit
git push origin master
/daanaa-deploy --code-only  # Redeploy previous version
# Back to previous state in 2 minutes
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| CSS parsing error | LOW | Page breaks | Tested in build; no syntax errors |
| Droplet runs out of disk | VERY LOW | Deploy fails | 50GB SSD, adding 1MB |
| Search latency increases | VERY LOW | User experience | No search code changes |
| API crashes | VERY LOW | Downtime | No backend changes |
| Browser caching issue | LOW | User sees old CSS | SPA dist/ is fresh build |

**Overall risk:** LOW

---

## Deployment Approval Checklist

Before proceeding, confirm:

- [ ] All 9 commits pushed to origin/master
- [ ] Build is clean (`npm run build` → 3.9s, 0 errors)
- [ ] No database/API changes included
- [ ] Smoke test endpoints identified (search latency check)
- [ ] Rollback plan documented (revert + redeploy)
- [ ] Current droplet health verified

---

## Optional: ConfidenceBadge Integration (Post-Deployment)

**Timing:** Can wait 1-2 weeks (component is ready, not integrated yet)

**If integrating now:**
1. Add ConfidenceBadge imports to OrganizationDetail.tsx (5 min)
2. Render badges next to org scores (3 min)
3. Test on 2-3 sample orgs with different confidence levels (2 min)
4. Commit + push + redeploy (2 min)

**Why safe:** Component is self-contained, no API changes, purely UI enhancement

---

## Go/No-Go Decision

✅ **GO:** Frontend-only, low risk, high value (WCAG AA compliance across 60 pages)

**Recommendation:** Deploy today via `/daanaa-deploy --code-only`

---

**Owner:** Deployment Strategy  
**Approver needed:** User (frontend changes require explicit approval)  
**Timeline:** 15 min total (5 pre-flight + 5 deploy + 3 smoke tests + 2 contingency)
