# Privacy Gates — 8 Automated Barriers

**Every commit must pass all 8 gates.** These are not guidelines — they are code-enforced structural protections on Stewardship Principle #2 (Privacy is core).

Exit code 0 = commit approved. Non-zero = commit blocked.

See `privacy_check.sh` in the project root for implementation.

---

## Gate 1: Token Pattern Detection

**Blocks:** API keys, AWS credentials, OAuth tokens, encryption keys, secrets

**Implementation:**
```bash
# Detects patterns like:
# AWS_ACCESS_KEY_ID=AKIA...
# api_key: "sk-..."
# password="..."
# Bearer token literal
```

**Evidence:** Commit 59f87cf9691 log shows `✓ Gate 1: PASS`

**What triggers it:**
- `AKIA*` strings (AWS keys)
- `sk-*` in code (OpenAI API format)
- `password=`, `secret=`, `token=` in code
- Base64-encoded credential patterns
- Private key blocks (BEGIN RSA PRIVATE KEY)

**Examples of BLOCKED commits:**
```bash
# ❌ BLOCKED: Literal API key in code
const apiKey = "sk-proj-1a2b3c4d5e6f..."

# ✅ PASS: API key from environment
const apiKey = process.env.OPENAI_API_KEY
```

---

## Gate 2: Log Leakage Detection

**Blocks:** Personal data in log files, error messages, or output

**Implementation:**
```bash
# Detects patterns like:
# User email in logs
# Phone numbers printed
# SSN or taxpayer ID
# Donor name or transaction data
```

**Evidence:** Commit 59f87cf9691 log shows `✓ Gate 2: PASS`

**What triggers it:**
- Email addresses in log strings (except generic patterns)
- Donor information in error messages
- User PII in debug output
- Credit card patterns (even if redacted)
- Social security number patterns

**Examples of BLOCKED commits:**
```bash
# ❌ BLOCKED: Donor email in error message
logger.error(`Donation from ${donorEmail} failed`)

# ✅ PASS: Aggregated, anonymized logging
logger.error(`Donation processing failed (attempt ${attemptNum})`)
```

---

## Gate 3: Env Var Fallback Detection

**Blocks:** Hardcoded default values that could expose secrets

**Implementation:**
```bash
# Detects patterns like:
# if (process.env.API_KEY || "default_key")
# config = { token: process.env.TOKEN || "fallback" }
```

**Evidence:** Commit 59f87cf9691 log shows `✓ Gate 3: PASS`

**What triggers it:**
- `|| "hardcoded_secret"` after env var access
- `.get('SECRET', 'default_password')`
- Default values that look like credentials
- Fallback strings that are actual keys (not generic placeholders like "N/A")

**Examples of BLOCKED commits:**
```bash
# ❌ BLOCKED: Real key as fallback
const token = process.env.AUTH_TOKEN || "abc123defg"

# ✅ PASS: Env-only, no fallback
const token = process.env.AUTH_TOKEN
if (!token) throw new Error('AUTH_TOKEN not set')
```

---

## Gate 4: Exfiltration & Injection Vector Detection

**Blocks:** Unusual data flows that could leak private data outside the system

**Implementation:**
```bash
# Detects patterns like:
# Sending user data to external services
# Building SQL/NoSQL queries from user input
# Writing Tier 0 data to public-facing APIs
# Exporting donor info to third parties
```

**Evidence:** Commit 59f87cf9691 log shows `✓ Gate 4: PASS`

**What triggers it:**
- Tier 0 (private) data passed to external APIs without anonymization
- User email/name in external HTTP requests
- Database queries built from unsanitized user input
- Sensitive data written to public buckets
- PII exported to analytics services without filtering

**Examples of BLOCKED commits:**
```bash
# ❌ BLOCKED: Sending donor name to tracking service
fetch('https://analytics.service.com/track', {
  body: JSON.stringify({ donor: walletData.donor_name })
})

# ✅ PASS: Anonymous event tracking only
fetch('https://analytics.service.com/track', {
  body: JSON.stringify({ event: 'donation_initiated', count: 1 })
})
```

---

## Gate 5: Data Boundary Check

**Blocks:** Tier 0, Tier 1, Tier 2 data crossing entity firewalls

**Implementation:**
```bash
# Enforces:
# - Tier 0 (donor private) never touches Tier 2 (public reports)
# - Tier 1 (org private) never mixes with external data
# - EcoMargins LLC data never mixes with Daanaa platform
```

**Evidence:** Commit 59f87cf9691 log shows `✓ Gate 5: PASS`

**What triggers it:**
- Querying Tier 0 wallet data in a public API endpoint
- Mixing vendor/consulting data with platform org records
- Exposing internal EcoMargins decisions via platform API
- Tier 1 org financial data in public rankings without consent

**Examples of BLOCKED commits:**
```bash
# ❌ BLOCKED: Mixing EcoMargins revenue into Daanaa org detail
app.get('/api/org/:ein', (req, res) => {
  const org = getOrg(req.params.ein)
  const consulting_client = getConsultingClient(org.ein) // ← crosses boundary
  res.json({ ...org, revenue: consulting_client.annual_revenue })
})

# ✅ PASS: Daanaa data only
app.get('/api/org/:ein', (req, res) => {
  const org = getOrgFromPlatformDB(req.params.ein)
  res.json(org) // Platform data only
})
```

---

## Gate 6: Config File Safety

**Blocks:** Secrets in code or config files that should be in env vars only

**Implementation:**
```bash
# Detects patterns like:
# .env files committed
# config/production.json with real credentials
# .env.local pushed to git
# secrets.json in repo
```

**Evidence:** Commit 59f87cf9691 log shows `✓ Gate 6: PASS`

**What triggers it:**
- `.env*` files added/committed (should be in .gitignore)
- `secrets.json`, `credentials.json` in repo
- `config/production.*` with API keys
- Hardcoded database connection strings
- Private key files (*.pem, *.key) in git

**Examples of BLOCKED commits:**
```bash
# ❌ BLOCKED: .env added to git
.env file:
DATABASE_URL=postgres://user:password@host/db
API_KEY=sk-1234567890

# ✅ PASS: .env in .gitignore, instructions in README
.gitignore:
.env
.env.local

README.md:
# Setup: copy .env.example to .env and fill in your keys
```

---

## Gate 7: PRIVACY-INVARIANTS Compliance

**Blocks:** Changes that violate Daanaa's core privacy invariants

**Implementation:** See `institution/library/` for full Tier 0/1/2 classification

```bash
# Enforces:
# - No unencrypted PII in database backups
# - No donor email/name in API responses unless explicitly requested
# - No cross-org donor data correlation
# - No logging individual transaction amounts
```

**Evidence:** Commit 59f87cf9691 log shows `✓ Gate 7: PASS`

**What triggers it:**
- Storing unencrypted wallet data in database
- Returning donor information in list endpoints
- Correlating donors across organizations
- Tracking individual giving patterns
- Exposing user-specific data without explicit opt-in

**Examples of BLOCKED commits:**
```bash
# ❌ BLOCKED: Returning donor info in org endpoint
GET /api/org/123/donors
[
  { name: "Alice Smith", email: "alice@example.com", amount: 500 },
  { name: "Bob Johnson", email: "bob@example.com", amount: 1000 }
]

# ✅ PASS: Aggregate donor count only
GET /api/org/123/stats
{ donor_count: 42, avg_donation: 850, last_gift_date: "2026-08-05" }
```

---

## Gate 8: Tier 2 Entity Firewall

**Blocks:** Confusing Daanaa (platform) with EcoMargins (consulting business)

**Implementation:**
```bash
# Enforces:
# - No EcoMargins consulting clients in Daanaa API
# - No Daanaa platform decisions affecting EcoMargins fees
# - No data sharing between entities without explicit boundaries
# - No co-mingling of tax entities in public communication
```

**Evidence:** Commit 59f87cf9691 log shows `✓ Gate 8: PASS`

**What triggers it:**
- Daanaa API returning EcoMargins vendor data
- Consulting revenue or client information in platform records
- Co-mingling entity liability or responsibility statements
- Using Daanaa platform to market EcoMargins services
- Sharing Daanaa donor/org data with EcoMargins consulting

**Examples of BLOCKED commits:**
```bash
# ❌ BLOCKED: Platform API returns consulting data
app.get('/api/advisors', (req, res) => {
  const advisors = db.query('SELECT * FROM consulting_clients') // ← crosses entity boundary
  res.json(advisors)
})

# ✅ PASS: Separate endpoints for separate entities
// Daanaa platform
app.get('/api/organizations/:ein', (req, res) => { ... })

// EcoMargins consulting (separate service)
app.get('https://consulting.ecomargins.com/api/clients', (req, res) => { ... })
```

---

## How to Pass All 8 Gates

### Before Committing

```bash
# Run the full check locally
bash privacy_check.sh

# If any gate fails, the script explains what's wrong
# Fix it before committing
```

### Common Fixes

| Gate | Problem | Fix |
|------|---------|-----|
| 1 | API key in code | Move to `.env`, access via `process.env` |
| 2 | Email in log | Use counter or ID instead (`donation_attempt_3`) |
| 3 | Hardcoded fallback | Remove fallback, error instead |
| 4 | Donor data to external API | Anonymize or don't send |
| 5 | Tier 0 in public endpoint | Query only Tier 2 data, separate endpoint for Tier 0 |
| 6 | `.env` file in git | Add to `.gitignore`, revert commit |
| 7 | Exposing PII | Filter response, aggregate only |
| 8 | EcoMargins data in Daanaa | Separate endpoint, separate service |

---

## Proof of Enforcement

**All commits to master branch are checked.**

Recent example:
```bash
$ git log --oneline | head -5
59f87cf9691 docs: Governance structure — AI stewardship centered
7ce26a6960a v6 backend complete, all privacy gates PASS

$ git show 59f87cf9691 | grep "privacy\|Gate"
✓ Gate 1: Token Pattern Detection — PASS
✓ Gate 2: Log Leakage Detection — PASS
✓ Gate 3: Env Var Fallback Detection — PASS
✓ Gate 4: Exfiltration & Injection Vector Detection — PASS
✓ Gate 5: Data Source Boundary Check — PASS
✓ Gate 6: Config File Safety — PASS
✓ Gate 7: PRIVACY-INVARIANTS Compliance — PASS
✓ Gate 8: Tier 2 Entity Firewall — PASS
```

---

## Why These Matter (Stewardship P2)

These gates exist because privacy is not optional. Each gate protects a different privacy risk:

- **Gates 1-3:** Prevent accidental credential leakage (security)
- **Gates 4-5:** Prevent intentional data misuse (architecture)
- **Gates 6:** Prevent repeatable mistakes (discipline)
- **Gate 7:** Enforce privacy invariants at code level (principle)
- **Gate 8:** Protect institution independence (integrity)

Together, they mean: **You can trust Daanaa with donor data because the code itself prevents abuse.**

---

## Violations & Recovery

If a commit violates a gate:

1. **Blocked:** The commit cannot reach the repo (pre-receive hook)
2. **Fixed:** Contributor fixes the code and retries
3. **Logged:** Attempt is recorded in `privacy_check.log`
4. **Reviewed:** During code review, violations are discussed

If a violation somehow reaches master (bug in script):

1. **Discovered:** LESSONS.md documents the gap
2. **Reverted:** Change is rolled back immediately
3. **Fixed:** Gate logic is corrected
4. **Audit:** All commits since last successful gate run are re-scanned

---

**Last updated:** 2026-08-09  
**Status:** Active on all branches  
**Enforcement:** Pre-commit hook + pre-receive hook  
**Stewardship:** Principle #2 (Privacy is core)
