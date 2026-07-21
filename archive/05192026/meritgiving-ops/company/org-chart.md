# MERIT Organizational Chart

**Operator:** EcoMargins Consulting LLC d/b/a MERIT / MeritGiving (transitioning to MeritGiving LLC)
**Founder/CEO:** Akbar
**Mission:** Make charitable giving easy, private, and fair. Strengthen the nonprofit sector with visibility, funding access, and a vendor ecosystem.

---

## Chain of authority

```
                          AKBAR (CEO / Founder)
                                 │
                    ┌────────────┴────────────┐
                    │   Claude Code (COO)     │
                    │   Orchestrates all      │
                    │   departments async     │
                    └────────────┬────────────┘
                                 │
   ┌──────────┬──────────┬───────┴───────┬──────────┬──────────┐
   │          │          │               │          │          │
INTERNAL    PRODUCT &   GO-TO-MARKET   EXTERNAL   STRATEGIC   COMPLIANCE
OPS         DATA                       SUCCESS    LEADERSHIP  & RISK
   │          │          │               │          │          │
   │          │          │               │          │          │
 ┌─┴─┐    ┌──┴──┐    ┌──┴──┐         ┌──┴──┐    ┌──┴──┐    ┌──┴──┐
 │04 │    │01 02│    │03 07│         │ 10  │    │08 09│    │ 06  │
 │05 │    │     │    │     │         │     │    │     │    │     │
 └───┘    └─────┘    └─────┘         └─────┘    └─────┘    └─────┘
```

## The ten departments

| # | Department | Function | Department Head Agent |
|---|---|---|---|
| 1 | Product & Engineering | Build the platform | `eng-lead` |
| 2 | Data & Research | Source, score, enrich nonprofit data | `data-lead` |
| 3 | Growth & Communications | Marketing, content, community | `growth-lead` |
| 4 | Operations | Infra, inbox, incidents | `ops-lead` |
| 5 | Finance & Accounting | Books, runway, credits | `finance-lead` |
| 6 | Legal & Compliance | Filings, ToS, risk register | `legal-lead` |
| 7 | People & Partnerships | Advisors, sponsors, vendor pipeline | `partnerships-lead` |
| 8 | Intelligence | Briefs, signals, research synthesis | `intel-lead` |
| 9 | Mission & Strategy | OKRs, ADRs, board prep | `strategy-lead` |
| 10 | Nonprofit Success | Claim verification, onboarding, support | `nonprofit-success-lead` |

## Department reporting groups

**Internal Operations Group**
- Operations (04)
- Finance & Accounting (05)
- *Joint daily: infrastructure health, runway, books*

**Product & Data Group**
- Product & Engineering (01)
- Data & Research (02)
- *Joint daily: shipping velocity, data quality*

**Go-to-Market Group**
- Growth & Communications (03)
- People & Partnerships (07)
- *Joint weekly: pipeline, narrative, relationships*

**External Success Group**
- Nonprofit Success (10) — standalone, only externally-facing dept
- *Joint with all groups as needed; reports directly to COO*

**Strategic Leadership Group**
- Intelligence (08)
- Mission & Strategy (09)
- *Joint weekly: synthesis, decisions, direction*

**Compliance & Risk (cross-cutting)**
- Legal & Compliance (06) — reviews all other departments
- *Monthly: risk register, filings, legal hygiene*

## Roles in plain English

**Akbar (CEO):**
- Make all strategic decisions
- Approve everything Claude flags as needing human judgment
- Hold relationships (advisors, sponsors, nonprofits, partners)
- 2–3 hrs/day focused work

**Claude Code (COO):**
- Orchestrate all 10 departments
- Generate briefs, draft work, surface decisions
- Run async work continuously
- Maintain context across sessions

**Department Head Agents (10 of them):**
- Own KPIs for their function
- Coordinate worker agents below them
- Generate weekly reports to COO
- Escalate to CEO per defined rules

**Worker Agents (25+):**
- Execute specific recurring tasks
- Run on n8n schedules
- Have isolated context windows
- Have tool allowlists per their role

## Reporting cadence

- **Daily (morning):** Top-3 brief from each active department to CEO
- **Weekly (Monday):** Full department status reports
- **Monthly (1st):** Full P&L, KPI dashboard, risk review
- **Quarterly:** OKR retro, advisor update, strategy review

## Decision rights matrix

| Decision type | Decided by | Approver |
|---|---|---|
| Code changes < 100 LOC | Department head agent | None (auto-merge) |
| Code changes 100–500 LOC | Department head agent + reviewer | CEO if touches money/legal/data |
| Code changes > 500 LOC | Always | CEO |
| Spend < $50 | Department head | None (auto) |
| Spend $50–$500 | Finance lead | CEO |
| Spend > $500 | CEO | CEO |
| External communications (email) | Department head drafts | CEO approves |
| Public communications (blog, social) | Growth lead drafts | CEO approves |
| Legal/policy changes | Always | CEO + attorney |
| Claim verification (Phase 1) | Nonprofit success lead | CEO until 100 done, then auto for green |
| Hiring (future) | Always | CEO |

## Mission lock (encoded in agent behavior)

Every agent operates under these non-negotiable rules:

1. MERIT never holds donor money in Phase 0
2. MERIT treats all 501(c)(3)s equally regardless of cause, religion, politics
3. MERIT data is sourced from IRS public records; private data stays private
4. MERIT never charges nonprofits for core services
5. MERIT publishes its work transparently
6. MERIT acknowledges its limitations clearly
7. MERIT defers to professionals (legal, tax, accounting) on regulated matters
8. MERIT prioritizes long-term trust over short-term growth

These are hardcoded into the root `CLAUDE.md` and inherited by every agent.
