# Contributing to Daanaa

Welcome! Daanaa is governed by 11 binding principles and an explicit AI autonomy framework. Read this before you start.

---

## Start Here (5 min)

1. **Read [GOVERNANCE.md](GOVERNANCE.md)** — Understand how we make decisions
2. **Skim [STEWARDSHIP.md](STEWARDSHIP.md)** — Know the 11 principles
3. **Understand the autonomy rules** — See [institution/AUTONOMY_FRAMEWORK.md](institution/AUTONOMY_FRAMEWORK.md)

---

## Before You Code

### Architecture

Before building, read [REPO_MAP.md](REPO_MAP.md) to understand:
- Which files are live vs. historical
- The canonical paths (one per job type)
- What's safe to edit and what's not

### Design

If you're touching UI/UX: see [DESIGN.md](DESIGN.md) (if it exists) or [CLAUDE.md](CLAUDE.md) for design principles.

### Privacy

Every commit is checked against 8 privacy gates (see [institution/PRIVACY_GATES.md](institution/PRIVACY_GATES.md)):

```bash
bash privacy_check.sh
```

If it fails, fix the code before committing. No exceptions.

---

## Workflow

### 1. Pick a Task

All work starts with understanding the scope:
- **Bug fix?** → Start with `/investigate` (if using Claude Code skills)
- **Feature?** → Collaborate with the founder first (this is gated)
- **Refactor?** → Ensure it's reversible
- **Documentation?** → Always welcome

### 2. Create a Branch

Use a clear naming pattern:
```bash
git checkout -b claude/<task-name>
```

Examples:
- `claude/fix-search-latency`
- `claude/add-methodology-page`
- `claude/optimize-scoring-pipeline`

### 3. Code

Follow the codebase style:
- **Python:** See `daanaa_api.py` (7,800 lines, the reference)
- **React/TypeScript:** See `frontend/src/components/` (shadcn/Radix UI patterns)
- **SQL:** See `scripts/` (SQLite, parameterized queries only)

**Key rules:**
- **Types at boundaries:** Validate all external input (Zod in React, explicit checks in Flask)
- **Tests first for risky changes:** Privacy, scoring, money flow
- **No silent failures:** Always error on invalid input
- **Comments for why, not what:** Code shows what; comments show why

### 4. Commit

Write clear messages:
```bash
git commit -m "fix: search query UNION removed, -53% latency

- Old query scanned FTS5 index twice (exact + BM25)
- New query uses BM25-only ordering
- p95 latency: 896ms → 420ms (419ms measured)
- Verified on 1.75M org index
- Smoke test: homepage + search + org detail all 200 OK"
```

**Remember:** Privacy gates run automatically. If they fail, fix and retry.

### 5. Test Locally

```bash
# API smoke test
curl -s http://localhost:5000/health | jq .

# Frontend build (if touched)
cd frontend && npm run build

# If you changed database queries
sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched"

# Run any specific tests
python3 -m pytest tests/test_something.py -v
```

### 6. Push & Pull Request

```bash
git push origin claude/<task-name>
```

Create a PR with:
- **Title:** What changed (e.g., "Optimize search FTS5 query")
- **Description:** Why it matters (e.g., "Blocks Oct 1 launch; p95 was 896ms")
- **Testing:** How to verify (e.g., "curl /api/search?q=health")

### 7. Address Review

If Claude Code or Codex reviews your work:
- **Requested changes?** → Push fixes, respond to comments
- **Approved?** → Merge to master (you can click the button if authorized)

---

## Gated Changes (Need Approval)

These require explicit founder approval before execution:

### Public Claims
- Scoring methodology explanations
- Trust signals (badges, confidence labels)
- Data freshness statements
- Tax deductibility language

**What to do:** Draft the change, flag it for review, wait for approval.

### Spending
- New cloud services or API subscriptions
- Tool upgrades with cost impact
- Infrastructure changes

**What to do:** Show options (Option A recommended, Option B, Option C), wait for decision.

### Schema Changes
- New database tables
- Column additions/deletions
- Data migrations

**What to do:** Prepare migration on a test copy, show rollback plan, wait for go-ahead.

### Feature Launches
- New product surfaces
- Major behavioral changes
- User-facing design decisions

**What to do:** Align with founder on strategy before building.

---

## Privacy & Secrets

### Never in Code
- API keys, database passwords, OAuth tokens
- Donor emails, names, transaction data
- Personal identifying information
- Credit card or SSN patterns

### Always in Environment
```bash
# .env (never commit)
DATABASE_URL=postgres://...
OPENAI_API_KEY=sk-...

# Code (always use env)
const db = process.env.DATABASE_URL
const key = process.env.OPENAI_API_KEY
```

### Fail Loudly
```python
# ✅ Good
api_key = os.environ['OPENAI_API_KEY']  # Fails if not set

# ❌ Bad
api_key = os.environ.get('OPENAI_API_KEY', 'default-key')  # Risky fallback
```

---

## Testing & Validation

### Code Quality
- **Types:** No `any` at API boundaries (Flask endpoints, React props)
- **Tests:** New endpoints come with a failing test first
- **Linting:** `npm run lint` (frontend), style checks (Python)

### Performance
- **Queries:** Use `.explain()` for anything touching 1M+ rows
- **Search:** p95 latency target is <200ms (benchmark at `/scripts/performance_audit.py`)
- **Frontend:** No layout shift, smooth interactions

### Privacy
- **Gates:** Always run `bash privacy_check.sh` before committing
- **Data flow:** Trace user data — where does it go? Should it?
- **Logs:** No donor/org secrets in output

---

## Common Patterns

### Adding an API Endpoint

```python
@app.route('/api/feature', methods=['GET'])
def feature():
    # 1. Validate input
    query_param = request.args.get('q')
    if not query_param:
        return error_response(400, 'Missing required parameter: q')
    
    # 2. Query database
    results = db.query('SELECT * FROM table WHERE ...')
    
    # 3. Transform for privacy (if needed)
    # (filter out sensitive fields, aggregate, anonymize)
    
    # 4. Return response
    return json_response({
        'results': results,
        'count': len(results)
    })
```

### Updating Frontend Component

```typescript
// Always type props
interface MyComponentProps {
  org: Organization
  onSelect: (ein: string) => void
}

export function MyComponent({ org, onSelect }: MyComponentProps) {
  // Component logic
}

// Export with proper display name for testing
MyComponent.displayName = 'MyComponent'
```

### Database Migration

1. **Create migration file:** `migrations/NNN_description.sql`
2. **Write idempotent queries:** `CREATE TABLE IF NOT EXISTS ...`
3. **Test on a copy:** `sqlite3 data/merit_registry.db.backup < migrations/NNN_*.sql`
4. **Document rollback:** How to undo this if needed?
5. **Get approval:** Show to founder before running on production

---

## If Something Breaks

### Immediate
1. **Revert** — `git revert [commit]` or roll back deployment
2. **Alert** — Tell the founder/team immediately
3. **Diagnose** — Understand what happened

### Document
Add an entry to [LESSONS.md](LESSONS.md):
```markdown
### Lesson: Search UNION query doubled latency

**Symptom:** Users reported slow search (p95 = 896ms)

**Root cause:** FTS5 index was scanned twice (exact phrase + BM25), creating duplicate work

**Fix:** Removed exact-phrase pin, rely on BM25 ranking only. Confirmed p95 = 420ms.

**Preventing rule:** Always profile query plans before merging FTS5 queries
```

### Prevent
Update [DECISIONS.md](DECISIONS.md) with the lesson learned so future contributors don't repeat it.

---

## Recognition

All significant contributions are logged in:
- **[DECISIONS.md](DECISIONS.md)** — Strategic choices and trade-offs
- **[LESSONS.md](LESSONS.md)** — What broke and how we fixed it
- **Git history** — Preserved forever

You'll be credited by commit, and your reasoning will live in the codebase.

---

## Questions?

### For contributors:
- Read [REPO_MAP.md](REPO_MAP.md) for architecture questions
- Read [CLAUDE.md](CLAUDE.md) for design/automation questions
- Ask a question in a GitHub issue if stuck

### For AI agents (Claude, Codex):
- Start with [GOVERNANCE.md](GOVERNANCE.md) to understand the autonomy rules
- Check [institution/AUTONOMY_FRAMEWORK.md](institution/AUTONOMY_FRAMEWORK.md) to know what you can decide autonomously
- Run all 8 privacy gates before committing
- Sign commits with appropriate co-author line (see below)

### AI Contributors

**Daanaa explicitly welcomes AI agent contributions** under governance:

| Agent | Role | Authorization |
|---|---|---|
| **Claude Code** | Implementation, planning, architecture | Autonomous on reversible work; founder gates on public claims, spending, data changes |
| **Codex** | Code review, quality assurance, architectural analysis | Autonomous on technical reviews; recommends on gated decisions |

Both agents operate under the **Stewardship Commitment** and follow the **8 privacy gates**. Commit signatures:
```
Co-Authored-By: Claude Code <claude@daanaa.org>
Co-Authored-By: Codex <codex@daanaa.org>
Claude-Session: [session-url]
```

---

## License & Principles

Daanaa is built under the **Founding Stewardship Commitment** (see [STEWARDSHIP.md](STEWARDSHIP.md)).

By contributing, you agree to uphold the 11 binding principles, including:
- Mission before growth
- Privacy is core
- Evidence-based trust signals
- Fair treatment of small organizations
- Transparency without weaponization

This is not a typical open-source project. We prioritize stewardship over growth, and integrity over efficiency.

**Welcome aboard.**

---

**Last updated:** 2026-08-09  
**Governed by:** STEWARDSHIP.md (11 principles) + GOVERNANCE.md (decision authority)
