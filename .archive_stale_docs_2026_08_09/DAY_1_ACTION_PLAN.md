# MERIT — Day 1 Action Plan (Parallel Execution)

**Goal:** While Claude generates the org scaffolding, you execute account signups and credit applications in parallel. EcoMargins credit card funds everything; we'll true up to MeritGiving LLC when formed.

**Time required from you:** ~3–4 hours total today, broken into sessions.

---

## Morning session (90 min) — Foundation accounts

### Hour 1: Core infrastructure

**1. GitHub Organization (15 min)**
- Go to https://github.com/organizations/new
- Choose free plan
- Org name: `meritgiving`
- Contact email: your existing meritgiving.org address
- Owner: your personal GitHub account
- Verify domain `meritgiving.org` via DNS TXT record (settings → verified domains)

**2. Vercel account (10 min)**
- Sign up at https://vercel.com with GitHub
- Link `meritgiving` GitHub org
- Start on Hobby (free). Upgrade to Pro ($20/mo) at Gate 2 when ready to ship.

**3. Cloudflare account (15 min)**
- Sign up at https://cloudflare.com
- Add `meritgiving.org` domain
- Update nameservers at your registrar to Cloudflare's
- Enable proxy on root + www (orange cloud)
- Free tier covers Phase 0

**4. Resend account (10 min)**
- Sign up at https://resend.com
- Add domain `meritgiving.org`
- Add DNS records Cloudflare-side (SPF, DKIM, DMARC, MX if needed)
- Free tier: 3K emails/mo, 100/day — fine for Phase 0

**5. Anthropic Console + Claude Code (15 min)**
- Console: https://console.anthropic.com — confirm billing on EcoMargins card
- Set monthly spend limit to $100 initially (adjust later)
- Verify Claude Code is configured with API key
- Note: Anthropic Startup Program application separately (afternoon session)

**6. PostHog account (15 min)**
- Sign up at https://posthog.com cloud (free tier 1M events/mo)
- Create project "meritgiving-production"
- Note the project API key for later

### Hour 1.5: Communication infrastructure

**7. Set up nonprofit-facing email (10 min)**
- In Google Workspace admin: create alias `nonprofits@meritgiving.org` routing to your existing inbox
- Also create: `support@`, `press@`, `legal@`, `security@`, `partners@`
- All route to one inbox for now; route to agents later

**8. Set up `security.txt` (5 min)**
- Will be deployed with site; for now just draft language:
```
Contact: mailto:security@meritgiving.org
Expires: 2027-05-19T00:00:00.000Z
Preferred-Languages: en
Canonical: https://meritgiving.org/.well-known/security.txt
Policy: https://meritgiving.org/security
```

**9. 1Password Business (10 min)**
- Sign up at https://1password.com/business
- $8/user/mo
- Create vault: "MERIT Production Secrets"
- Move every credential you just created into it
- This is now your single source of truth for keys/passwords

---

## Lunch session (60 min) — Credit applications

These take ~10 min each. Goal: submit all five today. Approvals come back over 1–4 weeks.

**Application checklist (apply with `meritgiving.org` email and MERIT positioning, NOT EcoMargins consulting):**

### 1. AWS Activate Founders — $1,000 credits
- URL: https://aws.amazon.com/activate/founders/
- Eligibility: founded ≤10 yrs ago, self-funded, not previously approved
- Use EcoMargins LLC as the entity (until MeritGiving LLC forms)
- Product description: "Civic technology platform providing public-domain IRS nonprofit data with privacy-first donor tools"
- Stage: "Pre-revenue, pre-seed, bootstrapped"

### 2. Google for Startups Cloud — Start tier — $2,000 credits, 1yr
- URL: https://cloud.google.com/startup/apply
- Eligibility: tech startup, not yet equity-funded, matching email domain
- Apply with `akbar@meritgiving.org` (or equivalent)
- Frame as: "Software product — IRS-grounded nonprofit directory platform"

### 3. Cloudflare for Startups — Tier 1 — $5,000 credits
- URL: https://www.cloudflare.com/forstartups/
- Eligibility: software/SaaS, ≤5 yrs old, valid website (meritgiving.org has Webflow site — good)
- Self-funded path

### 4. Microsoft for Startups Founders Hub — $1K unlocking to $5K
- URL: https://startups.microsoft.com/
- Eligibility: software, privately held, for-profit, NOT consultancy/agency
- **Important:** position as MERIT product, NOT EcoMargins consulting
- Bootstrapped path

### 5. Anthropic Startup Program — up to $25K Claude credits, 12mo
- URL: https://www.anthropic.com/startup-program (Airtable form)
- Mention: deep Claude integration (Claude Code as primary builder), civic-tech mission
- Honest about bootstrapped stage; emphasize traction signals (existing scoring infrastructure, IRS BMF pipeline running)

**After submitting each:** log in Airtable "Credits Pipeline" table (we'll set up shortly).

---

## Evening session (60 min) — Foundation services

### 1. Database — Neon (15 min)
- Sign up at https://neon.tech
- Free tier for now; will upgrade to Pro ($19/mo) at Gate 3
- Create project "merit-production"
- Create branches: `main`, `development`, `staging`
- Save connection strings to 1Password

### 2. Auth — Clerk (15 min)
- Sign up at https://clerk.com
- Free tier (10K MAU)
- Create application "MERIT"
- Configure: email/password + Google + GitHub login
- Get publishable + secret keys; save to 1Password

### 3. Error monitoring — Sentry (10 min)
- Sign up at https://sentry.io
- Free tier first; upgrade to Team ($26/mo) when shipping
- Create org "meritgiving"
- Create projects: `merit-web`, `merit-api`

### 4. Uptime — Better Stack (10 min)
- Sign up at https://betterstack.com/better-uptime
- Free tier (10 monitors)
- Set up monitors (will configure URLs after deploy): `meritgiving.org`, `meritgiving.org/api/health`

### 5. Linear (optional, 10 min)
- Skip if you prefer GitHub Issues for now
- If using: https://linear.app — Free tier, set up "MERIT" workspace, integrate with GitHub

---

## End of Day 1 checklist

By end of today, you should have:

- [ ] GitHub `meritgiving` org created with domain verified
- [ ] Vercel, Cloudflare, Resend, PostHog accounts active
- [ ] Anthropic API access confirmed; spend cap set
- [ ] Email aliases configured (nonprofits@, support@, press@, legal@, security@, partners@)
- [ ] 1Password Business vault holding all credentials
- [ ] 5 credit applications submitted (AWS, GCP, Cloudflare, Microsoft, Anthropic)
- [ ] Neon, Clerk, Sentry, Better Stack accounts active
- [ ] All credentials in 1Password

**Total spend today:** $0 (everything on free tiers or unbilled until usage)
**Total commitment:** $8/mo (1Password) until you upgrade tiers

---

## Tomorrow (Day 2): While LLC paperwork is in motion

- Initialize the `merit-platform` repo from Claude-generated scaffolding
- Push `meritgiving-ops` repo from Claude-generated scaffolding
- Wire up first MCP servers in Claude Code
- Run first `/morning-brief` command (after I generate it)
- Begin Week 1 milestones

---

## LLC formation (background, async)

While you do the above, kick off LLC formation:

**Option A: DIY via Texas SOS (cheapest, ~$300, 1–2 weeks)**
- File Certificate of Formation (Form 205) at https://www.sos.state.tx.us
- Apply for EIN at https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online (instant)
- Draft operating agreement (with mission lock language — Claude will provide template)

**Option B: Service-assisted (faster, ~$500, 3–5 days)**
- LegalZoom, Northwest Registered Agent, or Stripe Atlas (Atlas does Delaware C-corp, not Texas LLC — skip)
- Northwest is recommended for Texas LLCs ($39 + state fees)

**Option C: Attorney-assisted (best, ~$1,500, 1–2 weeks)**
- Hire a Texas business attorney to form + advise on operating agreement
- Use this if budget allows — operating agreement quality matters

**Recommended: Option B.** Good middle ground. Operating agreement template from Claude reviewed by attorney for $200–400.

---

## What Claude is doing in parallel right now

While you execute the above, Claude is generating:

1. ✅ Day 1 action plan (you're reading it)
2. 🔄 Organizational charter (`org-chart.md`, `operating-rhythm.md`)
3. 🔄 10 department charter files
4. 🔄 25+ agent definition files (department heads + workers)
5. 🔄 Claude Code configuration (`CLAUDE.md`, `.mcp.json`, rules, commands)
6. 🔄 Risk register pre-populated with 28 risks
7. 🔄 First quarter OKRs
8. 🔄 Decision log template + first ADR
9. 🔄 Dashboard scaffolding requirements

All committed to `meritgiving-ops` repo and `merit-platform` repo as you go.
