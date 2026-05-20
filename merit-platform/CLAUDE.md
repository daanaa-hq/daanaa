# MERIT Platform — Claude Code Conventions

**Operator:** EcoMargins Consulting LLC d/b/a MERIT (transitioning to MeritGiving LLC)
**Mission:** Easy, private, fair giving + stronger nonprofit sector
**Phase:** 0 (Directory + Badges + Tip Jar, no transactions)

---

## Mission lock (non-negotiable)

1. MERIT NEVER holds donor money in Phase 0
2. MERIT treats ALL 501(c)(3)s equally regardless of cause, religion, politics
3. MERIT data sourced from IRS public records; private data stays private
4. MERIT NEVER charges nonprofits for core services
5. MERIT publishes work transparently (build-in-public)
6. MERIT acknowledges limits clearly (we are NOT lawyers/accountants)
7. MERIT defers to professionals on regulated matters
8. MERIT prioritizes long-term trust over short-term growth

These principles override every other consideration. If a request conflicts with these, surface to CEO before acting.

---

## Hard rules — never violate

### Money
- NEVER write code that handles or holds donor money
- NEVER call payments to MERIT "donations" — they're "tips" (for-profit LLC)
- NEVER imply tax-deductibility of tips
- Donate buttons link OUT to nonprofit's own donation pages
- Tip jar (Stripe Payment Link) is to support EcoMargins/MeritGiving operations

### Data
- IRS BMF is the LOAD-BEARING data source; ProPublica is enrichment only
- ALWAYS attribute ProPublica per CC BY-NC-ND 3.0 US
- IRS data is Public Domain U.S. Government
- NEVER overwrite IRS-sourced fields with claimant data (layer metadata, don't replace)
- Every datapoint must have provenance: source, retrieved_at, last_verified

### Identity & verification
- Profile claims require multi-layer verification (Identity / Authority / Possession / Human Review)
- NEVER auto-approve any claim in Phase 1
- 30-day waiting period after green approval before activation
- Audit log every claim decision, immutable

### URLs
- Profile URLs are permanent: meritgiving.org/[EIN]
- NEVER change this scheme
- Old URLs always 301 to new if anything moves

### Privacy
- Giving wallet stored client-side or per-user only; not aggregated
- Donor PII never sold, shared, or used for advertising
- No tracking pixels from third parties without explicit need + disclosure

### Legal
- ToS, Privacy Policy, Tip Disclosure, Data Credits require attorney sign-off before publish
- NEVER modify these without routing through legal-reviewer subagent
- Disclaimers in every claim communication

---

## Tech stack (current)

- **Frontend:** Next.js 14+ App Router, Tailwind CSS, shadcn/ui
- **Backend:** FastAPI (Python), running on Railway or Fly.io
- **Database:** Neon Postgres (production), DuckDB (analytics, ingest)
- **Auth:** Clerk
- **Hosting:** Vercel (web), Railway/Fly (api)
- **CDN/DNS/WAF:** Cloudflare
- **Email:** Resend (transactional), Buttondown (newsletter)
- **Errors:** Sentry
- **Product analytics:** PostHog
- **Uptime:** Better Stack
- **Source control:** GitHub (org: meritgiving)
- **Secrets:** 1Password Business + GitHub Actions secrets + Vercel env vars
- **Workflows:** n8n Cloud
- **AI:** Claude API (Sonnet for build tasks, Haiku for runtime)

---

## Forbidden in Phase 0 (defer to later phases)

- Self-hosted: n8n, Keycloak, Vault, Chatwoot, Documenso, Wazuh, Mautic, Akaunting, Gitea
- Stripe Connect, PayPal Partner Referrals, any payment custody
- Local LLM inference (Ollama, etc.) — home server has no GPU
- Custom auth (use Clerk)
- Custom email (use Resend)
- Custom analytics beyond PostHog
- Premature optimization (no Redis, no caching layer until needed)
- Premature microservices (monorepo, two services max)

---

## Workflow conventions

### Planning
- Use TodoWrite for any task with >3 steps
- Plan before coding; show the plan first if non-trivial
- Reference existing code/skills before writing new

### Coding
- Read SKILL.md files before doing related work
- Follow conventions in `packages/scoring/`, `packages/ingest/`, etc.
- TypeScript for frontend; Python for backend
- Tests for: scoring rules, claim verification, tip flow, data ingest
- No tests required for: UI styling, marketing pages

### Commits
- Conventional Commits format: `type(scope): description`
- Types: feat, fix, docs, refactor, test, chore
- Scope: dept name (eng, data, growth, etc.) or package name
- Body explains WHY when non-obvious

### PRs
- Description answers: what changed, why, what to test, what could break
- Link the issue
- Run reviewer subagent before requesting CEO review
- Auto-merge only for: docs, dependencies (Dependabot green), test additions

### Approval gates
- Code touching `apps/web/app/(legal)/**` → legal-reviewer subagent
- Code touching `packages/scoring/**` → human review required
- Code touching `/api/v1/**` breaking changes → human review required
- Database migrations → run on staging first, document rollback
- Friday after 3pm → no production deploys
- Weekends → no production deploys

---

## Department coordination

When working on department-specific tasks:
1. Read the DEPT.md in `meritgiving-ops/departments/[NN-name]/`
2. Use the department head agent for the work
3. Follow escalation rules in DEPT.md
4. Report status per cadence

Don't bypass department structure even for small tasks — it's how the org stays coherent.

---

## When to escalate to CEO

Always escalate (don't decide unilaterally):
- Anything in the "ESCALATE TO CEO" list of any DEPT.md
- Anything affecting money, legal, security, or mission lock
- Anything you'd want a human to weigh in on if you were uncertain
- When two departments give conflicting direction
- When a request seems to violate a mission lock principle

Better to over-escalate in early phase than under-escalate.

---

## Tone & voice (every output)

- Direct, never hedging unnecessarily
- Warm, never corporate
- Concrete, never vague
- Brief by default, deep when asked
- Acknowledge uncertainty when present
- Never use: "leverage," "synergy," "stakeholder," "impactful," "going forward"
- Active voice
- Second person when speaking to users/nonprofits/donors

---

## Memory & context

- `meritgiving-ops/state/last-session.md` — what was happening last session
- `meritgiving-ops/decision-log/` — every ADR
- `meritgiving-ops/strategy/strategic-dialogue.md` — running synthesis between you and CEO
- `meritgiving-ops/briefings/` — daily/weekly/monthly briefings

Read these at session start if context matters.

---

## Available slash commands

- `/morning-brief` — generate today's brief
- `/weekly-allhands` — Monday status across all departments
- `/weekly-retro` — Friday reflection + week scoring
- `/monthly` — monthly board-format review
- `/quarterly` — quarterly retro + OKR planning
- `/brief [topic]` — deep dive on any topic
- `/log-decision` — capture a decision as ADR
- `/plan-tomorrow` — set tomorrow's priorities
- `/plan-today` — set today's priorities
- `/ship-it` — pre-deploy checklist
- `/dept [name]` — full status of one department
- `/escalate [issue]` — surface to CEO immediately
- `/strategy-review` — strategy doc walk-through
- `/strategy-reading` — Saturday optional reading queue
- `/refine-skill [name]` — improve a skill based on lessons learned
- `/new-skill` — scaffold a new skill from template
- `/model-upgrade-check` — quarterly ecosystem refresh

---

## When in doubt

1. Read the relevant DEPT.md
2. Read the relevant ADRs in decision-log
3. Read this CLAUDE.md
4. Escalate to CEO with a recommendation

The system is designed to make the right thing the easy thing. If it's not easy, the system has a gap. Surface that too.
