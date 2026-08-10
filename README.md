# 💎 Daanaa

![Daanaa Logo](./frontend/public/logo.png)

**AI-Governed Nonprofit Transparency Platform & Global Governance Model**

Daanaa is a civic nonprofit-discovery platform (USA) designed to help donors make more informed giving decisions. We index 2M+ 501(c)(3) organizations, assess financial health using peer comparisons, and surface trustworthy giving paths.

**Beyond the platform:** Daanaa is also a **replicable AI governance framework for NGO/nonprofit teams globally.** The 11 binding principles, automated privacy gates, and explicit autonomy rules work for any civic-tech platform, in any country, serving any type of organization.

**What makes Daanaa different:** We built governance as infrastructure, not bureaucracy. It's team-enforced, code-automated, and transparent—not dependent on founder heroics.

---

## Quick Links

### For Users
- 🌐 [Visit daanaa.org](https://daanaa.org)
- 📖 [How we assess financial health](https://daanaa.org/methodology)
- ❓ [Frequently asked questions](https://daanaa.org/faq)

### For Contributors
- 👥 [Contributing guidelines](CONTRIBUTING.md)
- 🏛️ [Governance framework](governance/GOVERNANCE_OPERATIONAL.md) — How we work
- 📋 [Stewardship commitment](STEWARDSHIP.md) — 11 binding principles

### For Developers
- 📚 [Architecture overview](REPO_MAP.md) — Which files are live
- 🔐 [Privacy gates](institution/PRIVACY_GATES.md) — How we protect donor data
- 🤖 [AI autonomy rules](institution/AUTONOMY_FRAMEWORK.md) — When Claude decides

### For Global Teams Building Civic Tech
- 🌍 [AI Governance Framework](docs/AI_GOVERNANCE_FRAMEWORK.md) — Adapt this for your NGO/nonprofit (includes GDPR, LGPD, regional guidance)
- 👥 [Team Story](TEAM_STORY.md) — How we built this as a collaborative effort (humans + AI agents)
- 🎯 [Principles (Customizable)](STEWARDSHIP.md) — 11 core principles; adapt for your culture and context
- 🤝 [Contributing as a Team](CONTRIBUTING.md) — Team workflow, decision-making, governance

---

## The Core Mission

Help people make more informed and sincere giving decisions. That's it. Growth, visibility, revenue, and automation exist to serve this mission — never the other way around.

---

## 11 Binding Principles

Daanaa operates under a **Founding Stewardship Commitment** that applies to everyone: founders, employees, contractors, volunteers, and the AI systems operating on our behalf.

**Three non-negotiables:**
1. 🎯 **Trust signals are evidence-based** (scores, badges = real data only)
2. 🔒 **Donor privacy is structural** (no tracking, no exposure of giving activity)
3. 🛡️ **Independence is protected** (no paid placement, no partner influence)

**Eight more principles** governing transparency, corrections, fairness, dignity, and explainability. Full text: [STEWARDSHIP.md](STEWARDSHIP.md)

---

## What Sets Us Apart

### Privacy by Design
- ✅ No donor tracking or public giving activity
- ✅ 8 automated privacy gates on every commit
- ✅ Device-first Giving Wallet (optional cross-device sync)
- ✅ Never the merchant of record (hand-off model only)

### Governance-First Architecture
- ✅ 11 binding principles embedded in code
- ✅ Explicit AI autonomy framework (Claude autonomous on reversible work only)
- ✅ Founder gates on public claims, spending, data changes
- ✅ Full decision log (governance/DECISIONS.md) + lesson log (governance/LESSONS.md)

### Evidence-Based Scoring
- ✅ v6 financial context system (3 dimensions: funding model × revenue band × peer performance)
- ✅ 99.83% coverage (2.05M orgs)
- ✅ Transparent methodology with confidence margins (±5% to ±15%)
- ✅ Published peer group definitions (reproducible)

### Small Org Fairness
- ✅ Peer groups are size-adjusted (NTEE + band + region)
- ✅ Hidden gems highlight small, financially healthy orgs
- ✅ No size-based disadvantaging in scoring
- ✅ Regular fairness audits against Principle #4

---

## Technology Stack

### Backend
- **Flask + SQLite** (`daanaa_api.py`, 7,800 lines)
- **Scoring pipeline** (`scripts/daanaa_scorer.py`, v6 financial context, overnight runs)
- **FTS5 full-text search** with cosine similarity embeddings
- **Local inference** (Qwen3-30B for missions, mxbai-embed-large for org embeddings)

### Frontend
- **React 19 + TypeScript** with Vite
- **Tailwind CSS + Radix UI** (shadcn components)
- **Giving Wallet** (device-first, optional Google sync)
- **Impact tracking** (Firebase Analytics, privacy-first)

### Data
- **Primary:** `data/merit_registry.db` (2.05M orgs, v6 scores)
- **Sources:** IRS Form 990 (ProPublica), NCCS, nonprofit websites
- **Precompute:** 1.76M static JSON pages + search index
- **Backups:** S3 daily snapshots + local archives

---

## Quick Start (Development)

### API (Flask)
```bash
source ~/meritgiving/venv/bin/activate
./scripts/ops/restart_api.sh    # production: gunicorn + preload
python3 daanaa_api.py           # dev: single-process Flask
curl http://localhost:5000/health
```

### Frontend (React/Vite)
```bash
cd frontend
npm install                     # first time only
npm run dev                     # port 5173
npm run build                   # dist/ for deployment
```

### Database
```bash
# Live database
sqlite3 data/merit_registry.db "SELECT COUNT(*) FROM registry_enriched"

# Schema inspection
.schema registry_enriched
```

### Status Check
```bash
./scripts/check_api_connection.sh  # Ports, process status, health endpoints
```

---

## Project Structure

```
daanaa/
├── README.md                   ← You are here
├── REPO_MAP.md                 ← Navigation guide (canonical paths)
├── CLAUDE.md                   ← Operating agreement & autonomy rules
├── STEWARDSHIP.md              ← 11 binding principles
├── CONTRIBUTING.md             ← How to contribute
│
├── governance/                 ← Governance & operations
│   ├── GOVERNANCE_OPERATIONAL.md ← How we make decisions
│   ├── DECISIONS.md            ← Decision log (choices made and why)
│   ├── LESSONS.md              ← Lesson log (what broke and how we fixed it)
│   ├── audits/                 ← Quality, UX, compliance audits
│   └── policies/               ← Governance policies
│
├── institution/                ← Constitutional corpus
│   ├── AUTONOMY_FRAMEWORK.md   ← When Claude decides vs. founder gates
│   ├── PRIVACY_GATES.md        ← 8 automated privacy gates
│   ├── CONSTITUTION.md         ← Organizational structure
│   └── library/                ← Tier 0/1/2 data classification
│
├── daanaa_api.py               ← Backend API (Flask, 7,800 lines)
├── droplet_api.py              ← Droplet variant
├── DEPLOYMENT.md               ← Deployment procedures
│
├── data/                       ← Databases & sources
│   └── merit_registry.db       ← Live database (2.05M orgs)
│
├── frontend/                   ← React/Vite SPA
│   ├── src/
│   │   ├── pages/             ← Route components
│   │   ├── components/        ← Reusable components
│   │   ├── contexts/          ← State (Wallet, GivingList, Compare)
│   │   └── utils/             ← Helpers, API client, analytics
│   └── dist/                  ← Built SPA (deployed to droplet)
│
├── scripts/                    ← Data pipeline & operations
│   ├── daanaa_scorer.py       ← Score computation (v6, nightly)
│   ├── build_fts_index.py     ← FTS5 search index
│   ├── overnight_pipeline.py  ← Orchestrator
│   └── ops/                   ← Deployment & monitoring scripts
│
├── docs/                       ← Documentation
│   ├── architecture/           ← System design & integration
│   ├── operations/             ← Deployment, monitoring, incidents
│   ├── projects/               ← Feature-specific docs
│   └── methodology/            ← Scoring & algorithms
│
├── tests/                      ← Unit & integration tests
├── migrations/                 ← Database schema migrations
│
└── archive/                    ← Historical (read-only, organized by era)
    ├── deployment-history/     ← Past deployment docs
    ├── session-reports/        ← End-of-session summaries
    └── projects/               ← Archived projects (visibility, etc.)
```

For detailed guidance: [REPO_MAP.md](REPO_MAP.md)

---

## Key Files by Role

### If you're a **Founder** making strategic decisions:
1. [governance/GOVERNANCE_OPERATIONAL.md](governance/GOVERNANCE_OPERATIONAL.md) — How decisions are made (5 min)
2. [governance/DECISIONS.md](governance/DECISIONS.md) — What we've decided and why (scan)
3. [STEWARDSHIP.md](STEWARDSHIP.md) — Principles you signed (10 min)

### If you're a **Contributor** writing code:
1. [CONTRIBUTING.md](CONTRIBUTING.md) — Workflow and conventions
2. [REPO_MAP.md](REPO_MAP.md) — Which files are live
3. [CLAUDE.md](CLAUDE.md) — Tech stack and autonomy rules

### If you're an **AI Agent** (Claude, Codex):
1. [governance/GOVERNANCE_OPERATIONAL.md](governance/GOVERNANCE_OPERATIONAL.md) — Authority matrix (who decides what)
2. [institution/AUTONOMY_FRAMEWORK.md](institution/AUTONOMY_FRAMEWORK.md) — When you can act autonomously
3. [institution/PRIVACY_GATES.md](institution/PRIVACY_GATES.md) — What blocks commits

---

## Governance Highlights

### Public Commitments
- ✅ **Transparency:** All methodology documented and auditable
- ✅ **Corrections:** Mistakes corrected openly and quickly
- ✅ **Independence:** No partner influence on scores or visibility
- ✅ **Privacy:** Donor data never used for targeting or outreach

### Decision Making
- ✅ **Founder gates:** Public claims, spending, data changes require approval
- ✅ **AI autonomy:** Claude autonomous on reversible code; founders gate irreversible work
- ✅ **Decision log:** [governance/DECISIONS.md](governance/DECISIONS.md) records all non-obvious choices
- ✅ **Lesson log:** [governance/LESSONS.md](governance/LESSONS.md) documents what broke and how we fixed it

### Automated Enforcement
- ✅ **8 privacy gates** on every commit (tokens, logs, exfiltration, boundaries, config, invariants, entity firewall)
- ✅ **Type safety** at API boundaries (Zod, TypeScript, explicit checks)
- ✅ **Test coverage** for risky changes (privacy, scoring, money flow)

---

## October 12, 2026 Launch Status

**Phase 2 (Launch Readiness):** ✅ Complete

- ✅ v6 scoring system (99.83% coverage, 2.05M orgs)
- ✅ Methodology documentation + tax-deductibility verification
- ✅ Search optimization (FTS5, p95 latency reduced 53%)
- ✅ Analytics wiring (Firebase, privacy-first)
- ✅ Governance documentation (11 principles, 8 privacy gates)
- ✅ Repository public on GitHub
- ✅ Daanaa V6 consolidation

Target: October 12 launch with governance-first transparency.

---

## Getting Help

### Documentation
- **Navigation:** [REPO_MAP.md](REPO_MAP.md) — Where everything lives
- **Governance:** [governance/GOVERNANCE_OPERATIONAL.md](governance/GOVERNANCE_OPERATIONAL.md) — How we decide
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md) — How to help
- **Technical:** [CLAUDE.md](CLAUDE.md) — Architecture & autonomy

### Issues & Bugs
- Create a GitHub issue with reproduction steps
- Label: `bug`, `feature`, `governance`, `privacy`

### Governance Questions
- Read [institution/AUTONOMY_FRAMEWORK.md](institution/AUTONOMY_FRAMEWORK.md)
- Check [governance/DECISIONS.md](governance/DECISIONS.md) for similar past decisions
- Ask in a GitHub issue if unclear

---

## License

Daanaa is developed under the **Founding Stewardship Commitment** (see [STEWARDSHIP.md](STEWARDSHIP.md)).

The codebase is **[TBD — pending legal review]**, and the principles are binding on all contributors.

---

## Acknowledgments

**Founders:** Akbar Khowaja  
**AI Steward:** Claude (Anthropic AI Engineering)  
**Architecture & Governance:** Codex (AI Coordination)

---

**Last updated:** August 2026  
**Status:** Daanaa V6 Ready  
**Public Launch:** October 12, 2026  
**Governed by:** [STEWARDSHIP.md](STEWARDSHIP.md) (11 binding principles)

---

### Join Us

We're building a platform that trusts donors enough to tell them the truth. If you believe in governance-first technology and transparent institutions, [contribute](CONTRIBUTING.md) or [reach out](https://daanaa.org).
