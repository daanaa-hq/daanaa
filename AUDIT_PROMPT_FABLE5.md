# Daanaa Audit Prompt — Fable 5

You are auditing **Daanaa** (daanaa.org), a civic nonprofit-discovery platform at `/home/akbar/meritgiving`.

**Current state (as of 2026-06-09):**
- Stack: FastAPI :5000 (daanaa_api.py), React/TypeScript/Vite :5174, DuckDB + SQLite (IRS BMF + enriched registry)
- Scale: 379,990 orgs scored (71K Tier A complete-data, 308K Tier B partial-data); FTS5 + FAISS index (60x compression)
- Data features: four-tier financial-context labels, location-aware similar orgs (NTEECC+city+tags, 9 per), local Llama embeddings (mxbai-embed-large)
- Deployment: Cloudflare Tunnel → droplet (Ryzen 9700X, R9700 32GB VRAM), static precompute files + API :5000
- Governance: Founding Stewardship Commitment (12 principles) + Privacy Invariants (7 hard constraints) + CLAUDE.md discipline

**Mission constraints (violations = CRITICAL):**
1. **No ranking by revenue/size by default.** Results must not sort or suggest by org size/revenue unless explicitly user-requested and clearly labeled.
2. **Privacy is architectural.** Giving Wallet is localStorage-only; no server-side donor tracking; no IP retention; minimal PII on disk.
3. **Public data only → Claude API.** Donor/volunteer/internal data → local Llama only. Claude API calls must be audit-safe (public IRS data only).
4. **Four-tier labels must be honest.** DATA_INCOMPLETE / VERIFIED_HEALTHY / FINANCIAL_NOTE / NOT_ASSESSED must be clearly explained to users; no silent exclusions.
5. **No paid placement.** Zero revenue from org ranking, no sponsored results, no gatekeeping by donation amount.

**Token discipline (strict):**
- NEVER read a whole file. Use `rg` or `grep` to locate patterns, then read only matching regions (max 40 lines per lookup).
- Use `ls`/`tree`/`wc -l` for structure; never `cat` entire source files.
- Each phase produces a report file in `docs/audit/` and **STOPS**. Wait for "continue" before the next phase.
- Summaries: max 15 lines. Findings: one line per issue in `FINDINGS.md`.

---

## PHASE 0: MAP (structure + routes + baseline)

**Goal:** Understand stack, API shape, frontend pages, data schema, no deep dives yet.

### Outputs
- `docs/audit/00_structure.md` (max 20 lines)

### Commands
```bash
# Stack shape
tree -L 3 -I 'node_modules|__pycache__|*.duckdb|dist' > /tmp/tree.txt

# API routes: all handlers in daanaa_api.py + merit_api.py + api/main.py
rg "@(app|router|Route)\.(get|post|put|delete)" --no-heading

# Frontend pages + components (count only)
find frontend/src -name "*.tsx" -o -name "*.ts" | wc -l

# Database schema (tables + key columns)
sqlite3 data/merit_registry.db ".tables"
sqlite3 data/merit_registry.db ".schema registry_enriched" | head -30

# Check for docs/audit/ directory
ls -la docs/ | grep audit
```

### Report format
```
# Daanaa Structure Map

## Backend Stack
- Entry point: daanaa_api.py (Flask + SQLite, :5000)
- Database: merit_registry.db (IRS BMF + enriched registry)
- Routes: [count] GET/POST endpoints
- Local inference: Llama @ :11437 (Qwen, embeddings), mxbai-embed-large

## Frontend
- Framework: React 19 + Vite + TypeScript
- Pages: [count] .tsx files
- State: CompareContext (up to 4 orgs), Wallet (localStorage)
- Key routes: /, /search, /org/:ein, /directory

## Data Schema (registry_enriched)
- Columns: [count]
- Key fields: merit_score, merit_tier, ntee1_percentile, mission, donate_url, website
- Four-tier labels: DATA_INCOMPLETE / VERIFIED_HEALTHY / FINANCIAL_NOTE / NOT_ASSESSED

## Known issues from memory
- Droplet slowness (TBD: CPU/memory/query bottleneck)
- Tier assignment logic (location: [file:line])
- Data freshness visibility (is "as of <date>" shown to users?)
```

**STOP.** Report above. Wait for "continue".

---

## PHASE 1: BACKEND SECURITY + MISSION (:5000 API)

**Goal:** Hunt SQL injection, hardcoded secrets, ranking by revenue, unauthorized API exposure, Claude API boundary violations.

### Outputs
- `docs/audit/01_backend.md` (findings → FINDINGS.md)

### Validation queries

#### a) SQL Injection
```bash
# DuckDB queries must use ? placeholders, never f-strings or .format()
rg "execute\(|execute_one\(|sql\(" daanaa_api.py merit_api.py | head -20
# For each hit, check: does it use ? or db.execute(f"...")? Flag f-strings as CRITICAL.

# Alternative: unsafe LIKE patterns
rg "LIKE.*%|LIKE.*'" daanaa_api.py | head -10
```

#### b) Default ranking by revenue/size
```bash
# Hunt for ORDER BY revenue/size/asset/donation patterns
rg "ORDER BY.*revenue|ORDER BY.*size|ORDER BY.*asset|ORDER BY.*donation" daanaa_api.py merit_api.py

# Check /search route: does it default to relevance or revenue?
rg -A 10 "def.*search|@app.route.*search" daanaa_api.py
```

#### c) Hardcoded secrets
```bash
# No API keys, passwords, tokens in source
rg "api_key|API_KEY|secret|SECRET|password|PASSWORD|token.*=" --no-filename -g '!*test*' daanaa_api.py merit_api.py api/main.py | head -20
```

#### d) Input validation on API routes
```bash
# Every route param must have length/type checks (Zod or explicit guards)
rg "@app.route|@router" -A 5 daanaa_api.py | grep -E "def |args\[|request\." | head -20
```

#### e) Claude API calls: data boundary
```bash
# Find all Claude API calls; verify no donor/volunteer/internal data
rg "client\.messages|anthropic\.Anthropic" daanaa_api.py merit_api.py -A 5 | head -30
# For each call, check the prompt/context: is it public IRS data only? Flag private data as CRITICAL.
```

#### f) Connection handling
```bash
# Is DuckDB opened with read_only=True where appropriate?
rg "duckdb\.connect|sqlite3\.connect" daanaa_api.py -B 2 -A 2 | head -20
```

#### g) CORS, rate limiting, bind address
```bash
# Check app initialization
head -50 daanaa_api.py | grep -E "app = |CORS|bind|0\.0\.0\.0|127\.0\.0\.1"

# Rate limiting presence
rg "rate_limit|throttle|RateLimit" daanaa_api.py
```

#### h) Error responses leaking stack traces
```bash
# Check error handlers: do they return 500 with traceback?
rg "@app.errorhandler|@app.route.*error|try:|except" daanaa_api.py -A 3 | head -30
```

### Findings format
```
[CRITICAL|HIGH|MED|LOW] [component] file:line — [issue] — [proposed fix]

Example:
CRITICAL [sql] daanaa_api.py:142 — query uses f-string, not ? placeholders — use db.execute(query, params)
HIGH [data-boundary] merit_api.py:89 — Claude API call includes volunteer emails (private) — filter to public IRS fields only
MED [input-validation] daanaa_api.py:203 — /org/:ein accepts unbounded string, no length check — add len(ein) <= 10 guard
```

**STOP.** Write FINDINGS.md with all findings above. Report count by severity. Wait for "continue".

---

## PHASE 2: FRONTEND + UX + ACCESSIBILITY

**Goal:** XSS, mixed content, API error handling, data-freshness visibility, tier explanations, keyboard nav, mobile UX.

### Outputs
- `docs/audit/02_frontend.md` (findings → FINDINGS.md)

### Validation queries

#### a) XSS vectors
```bash
# dangerouslySetInnerHTML, innerHTML, eval, Function constructor
rg "dangerouslySetInnerHTML|innerHTML|eval\(|Function\(" frontend/src --no-heading | head -20
```

#### b) Mixed content (http:// in src/)
```bash
# All HTTP in frontend must be HTTPS
rg "http://[^localhost]" frontend/src --no-heading | head -10
```

#### c) API error handling
```bash
# Does the UI handle :5000 being slow/down gracefully, or blank-hang?
rg "fetch.*localhost.*5000|VITE_API_URL" frontend/src -A 3 | head -20
rg "\.then\(|\.catch\(|try.*fetch" frontend/src | wc -l
# If < 5 catch handlers, flag as MED.
```

#### d) Four-tier label visibility
```bash
# Are the tier labels (DATA_INCOMPLETE, VERIFIED_HEALTHY, FINANCIAL_NOTE) explained in the UI?
# Or just shown as unexplained icons?
rg "DATA_INCOMPLETE|VERIFIED_HEALTHY|FINANCIAL_NOTE" frontend/src -B 2 -A 2 | head -30
```

#### e) Search UX: debounce, loading states
```bash
# Check for debounce on search input
rg "debounce|delay.*search|search.*timeout" frontend/src --no-heading | head -10

# Check for loading states in search results
rg "isLoading|loading state|Skeleton|Spinner" frontend/src | head -10
```

#### f) Accessibility (aria, alt text, keyboard nav)
```bash
# Count aria- attributes
rg "aria-" frontend/src | wc -l

# Count alt= on images
rg 'alt="' frontend/src | wc -l

# Check for keyboard nav on search results (tabindex, onKeyDown)
rg "onKeyDown|tabIndex|role=\"button\"" frontend/src | head -15
```

#### g) Mobile viewport
```bash
# Check viewport meta tag
grep -E "viewport|width=device" frontend/index.html

# Search responsive classes (Tailwind breakpoints)
rg "md:|sm:|lg:" frontend/src | wc -l
```

### Findings format
```
[CRITICAL|HIGH|MED|LOW] [component] file:line — [issue] — [proposed fix]

Example:
CRITICAL [xss] OrgCard.tsx:67 — dangerouslySetInnerHTML on mission text — sanitize via DOMPurify before render
MED [ux] SearchResults.tsx:45 — no tier explanation; users see "DATA_INCOMPLETE" with no tooltip — add aria-label or <Tooltip>
MED [accessibility] Search.tsx:102 — search input has no aria-describedby — add aria-describedby="search-help"
```

**STOP.** Append new findings to FINDINGS.md. Report tier-label findings separately (honesty principle). Wait for "continue".

---

## PHASE 3: DATA CREDIBILITY + FRESHNESS

**Goal:** Data ingest validation, freshness visibility, tier assignment logic, revocation handling, silent exclusions.

### Outputs
- `docs/audit/03_data.md` (findings → FINDINGS.md)

### Validation queries

#### a) BMF ingest: validation step?
```bash
# Find the BMF load script
find . -name "*bmf*" -o -name "*sync*" | grep -E "\.py|\.sh"

# Read the load script (first 50 lines)
head -50 [found script]

# Does it validate row counts, EIN format, deduplication? Or blind load?
rg "validate|check|count|hash|dedupe" [found script] | head -10
```

#### b) Data freshness: "as of <date>" shown to users?
```bash
# Check if BMF snapshot date is stored
rg "snapshot.*date|as.*of.*date|data.*date|freshness" daanaa_api.py merit_api.py frontend/src | head -20

# Is the date displayed in the UI or API response?
rg "last_updated|snapshot_date|data_as_of" daanaa_api.py -A 2 | head -15
```

#### c) Tier assignment logic
```bash
# Locate the scorer that assigns tiers
find . -name "*score*" -type f | grep -E "\.py$"

# Read the tier assignment function (location = [file:line])
rg "def.*tier|merit_tier|merit_band" [scorer file] -B 2 -A 10 | head -30
```

#### d) Revoked/delisted orgs: IRS revocation handling?
```bash
# Does the pipeline handle IRS revocations?
rg "revoke|delist|status.*revoked|irs.*status" daanaa_api.py merit_api.py scripts/ | head -15
```

#### e) Silent exclusions
```bash
# Are orgs filtered out without visibility?
rg "WHERE.*status|WHERE.*exclude|WHERE.*active|is_hidden" merit_api.py daanaa_api.py -B 1 -A 2 | head -30
```

### Findings format
```
[CRITICAL|HIGH|MED|LOW] [component] file:line — [issue] — [proposed fix]

Example:
HIGH [data-freshness] daanaa_api.py:234 — BMF snapshot date not stored or returned in API — add snapshot_date column to registry_enriched; return in GET /org/:ein
CRITICAL [tier-assignment] scripts/merit_scorer_v3_3.py:145 — tier logic not documented; orgs below score threshold silently unranked — add comments; emit a "NOT_ASSESSED" tier explicitly
MED [revocations] overnight_pipeline.py:78 — pipeline loads BMF blind; does not check for IRS revocations — add a revocation lookup step before tier assignment
```

**STOP.** Append findings. Report "data freshness to UI" finding with HIGH priority (credibility violation). Wait for "continue".

---

## PHASE 4: PERFORMANCE + DROPLET STABILITY

**Goal:** Identify why droplet is slow. CPU/memory/query bottleneck? Embedding server hang? Connection pool exhaustion?

### Outputs
- `docs/audit/04_performance.md` (with before-numbers and bottleneck root cause)

### Baseline measurement (run locally first)
```bash
# System health snapshot
free -h && nproc && df -h && top -bn 1 | head -20

# Cold and warm latency (3 runs each, local curl to bypass Tunnel)
time curl -s http://localhost:5000/api/search?q=food+bank | jq '.count'
time curl -s http://localhost:5000/api/search?q=food+bank | jq '.count'
time curl -s http://localhost:5000/api/search?q=food+bank | jq '.count'

# Check if llama-server is hanging
curl -s http://localhost:11437/v1/models | jq '.data | length'
```

### Query bottleneck analysis
```bash
# DuckDB: memory_limit / threads settings
rg "memory_limit|threads|pragma" daanaa_api.py merit_api.py | head -10

# Search query: is it using FTS5 or LIKE scan?
rg -A 20 "def.*search" daanaa_api.py | grep -E "SELECT|FROM|WHERE|LIKE" | head -15

# Run EXPLAIN on the main search query (if found above)
# sqlite3 data/merit_registry.db "EXPLAIN QUERY PLAN SELECT ... [main search query]"
```

### Embedding path
```bash
# Is llama-server called synchronously per request with no timeout?
rg "requests\.post.*11437|embedding.*timeout|llama.*server" daanaa_api.py -B 2 -A 5 | head -30
```

### Caching
```bash
# Any caching layer (Redis, in-process dict)?
rg "cache|Cache|redis|Redis" daanaa_api.py | head -10
```

### Findings format
```
[CRITICAL|HIGH|MED|LOW] [component] file:line — [issue] — [proposed fix]

Example:
HIGH [performance] daanaa_api.py:178 — search query uses LIKE scan (no FTS5), full table scans for every query — migrate to FTS5 index (org_fts table)
CRITICAL [embed-hang] merit_api.py:456 — embedding request to :11437 has no timeout; can block all Flask workers for 30s — add timeout=5, fail-open (skip semantic search on timeout)
MED [caching] daanaa_api.py:1 — no response caching; every search hits DB cold — add in-memory cache with 5-min TTL per query
```

**STOP.** Report baseline numbers (latency, CPU%, memory). Report bottleneck rank (query/embed/cache/system). Wait for "continue".

---

## PHASE 5: STEWARDSHIP RECONCILIATION

**Goal:** Verify each of the 12 principles + 7 privacy invariants is enforced in code. Highlight gaps and conflicts.

### Outputs
- `docs/audit/05_stewardship.md` (principle → enforced? where? gaps?)

### Commands
```bash
# Load the principles
head -100 STEWARDSHIP.md
head -80 PRIVACY-INVARIANTS.md

# Map each principle to code:
# 1. "No ranking by revenue/size by default" → rg "ORDER BY.*revenue|default.*sort" daanaa_api.py
# 2. "Privacy is architectural" → rg "localStorage|sessionStorage" frontend/src; rg "IP|ipv4|ipv6" daanaa_api.py
# 3. "Evidence-based labels" → rg "tier|score" daanaa_api.py; is tier explanation in code?
# 4. "No paid placement" → rg "paid|sponsor|premium|price" daanaa_api.py merit_api.py
# 5. "Never rank by revenue" → already checked in Phase 1
# 6–12. (custom searches per principle text)

# Privacy invariants:
# 1. No third-party trackers → rg "google|gtag|facebook|segment|mixpanel|hotjar|sentry" frontend/
# 2. Giving data localStorage-only → rg "wallet|donation" frontend/src | grep -v localStorage
# 3. No IP retention → grep -E "request\.remote_addr|client\.host|remote_ip" daanaa_api.py
# 4. CSP strict → grep "Content-Security-Policy" daanaa_api.py
# 5. No donor identity + giving → rg "feedback|waitlist" daanaa_api.py; check schema
# 6. Minimal PII → rg "email|phone|name" merit_api.py | grep -v public
# 7. Volunteer = connect, don't collect → rg "volunteer" daanaa_api.py; check schema
```

### Findings format
```
[CRITICAL|HIGH|MED|LOW] [principle] file:line — [gap] — [proposed fix]

Example:
CRITICAL [principle-1-no-ranking-by-size] daanaa_api.py:156 — /search default sort is by org size (assets DESC), not relevance — change ORDER BY clause to relevance, add explicit size-sort param
HIGH [principle-3-evidence-based] frontend/src:OrgCard.tsx:67 — tier badge "VERIFIED_HEALTHY" shown with no icon/tooltip; users don't know what it means — add aria-label + <Tooltip> explaining the tier logic
MED [privacy-invariant-3-no-ip-retention] daanaa_api.py:12 — access log format includes %(h) (client IP) — change to custom format omitting IP
```

**STOP.** Produce principle-gap table. Report any conflicts between stewardship principles (e.g., "mission before growth" vs "revenue model TBD"). Wait for "continue".

---

## PHASE 6: SYNTHESIS + FIX SEQUENCE

**Goal:** Produce a prioritized fix list ranked by (mission risk × user impact ÷ effort), sized for small Claude Code sessions.

### Inputs
- `FINDINGS.md` (all phases)
- `01_backend.md`, `02_frontend.md`, `03_data.md`, `04_performance.md`, `05_stewardship.md`

### Output
- `docs/audit/MASTER_REPORT.md`

### Report structure
```markdown
# Daanaa Audit Master Report — 2026-06-09

## Top 5 CRITICAL + HIGH Fixes (by mission risk × user impact ÷ effort)

1. [finding ref from FINDINGS.md:line] — [issue] — [1-2 line fix]
   - **Effort:** [<30 min | 30–60 min | 1–2 hrs | 2+ hrs]
   - **Risk if unfixed:** [mission | user trust | legal | performance]
   - **Suggested approach:** [implementation outline]

2. ... (4 more)

## Quick Wins (<30 min each)

- [finding:line] — [fix] — [file:line to edit]
- ... (all < 30 min fixes)

## Fix Sequence (for future small Claude Code sessions)

Each item references FINDINGS.md line(s). Session sizes: 30 min, 1 hr, 2 hr blocks.

### Session 1 (30 min): Tier label explanations
- FINDINGS.md:line — Add aria-label + <Tooltip> to tier badges
- FINDINGS.md:line — Add "as of <date>" data freshness text to API response + UI

### Session 2 (1 hr): Data boundary + validation
- FINDINGS.md:line — Remove private data from Claude API calls
- FINDINGS.md:line — Add EIN validation guards to /org/:ein route

### Session 3 (1–2 hrs): Performance bottleneck
- [diagnosis from Phase 4 report] — Add FTS5 to search query / reduce embedding calls / etc.

... (rest of sequence)

## Known Open Questions
- Tier assignment vs data completeness: forced thirds or natural distribution? (DECISIONS.md or stakeholder call?)
- Revenue model: when finalized, how to ensure principle-1 (mission before growth) is structurally enforced?
```

**DONE.** Master report is the output. Print top 5 + quick wins. Do NOT run any fixes yet.

---

## How to use this audit

1. **Run PHASE 0** first (structure map). Review output, ask questions.
2. **Run remaining phases sequentially** (1–5). Each phase stops and waits for "continue".
3. **Run PHASE 6** last (synthesis). Review the fix sequence.
4. **Use the fix sequence to drive future Claude Code sessions.** Each item is sized to fit one focused session. Reference FINDINGS.md line numbers so re-discovery is near-zero.

**All progress is persisted in `docs/audit/`**, so if you pause mid-audit, the next session can pick up where you left off.

---

## Current known issues (for context)

- **Droplet slowness:** Root cause TBD (CPU, query, embedding, caching). PHASE 4 will diagnose.
- **Data freshness visibility:** "Data as of <date>" not shown to users (credibility violation). HIGH priority in PHASE 3.
- **Tier label honesty:** Are the four-tier labels explained in the UI? If unexplained icons → MED finding. PHASE 2 will verify.
- **Claude API boundary:** Are any private/volunteer/donor fields being sent to Anthropic? PHASE 1 will audit.

