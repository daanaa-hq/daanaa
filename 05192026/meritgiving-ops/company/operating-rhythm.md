# MERIT Operating Rhythm

**The system that turns 2–3 hours/day into a real organization.**

---

## Daily rhythm (you commit 2.5–3 hours)

### Morning session — 60 min (suggested 6:30–7:30 AM Central)
**Theme: Decide & Direct**

| Time | Activity | Tool |
|---|---|---|
| 0–5 min | Read `/morning-brief` | Email/Notion |
| 5–25 min | Strategic block (one priority) | Claude Code or Notion |
| 25–45 min | Approval queue (PRs, content, emails) | GitHub + `/approvals` page |
| 45–55 min | `/log-decision` any calls made | Claude Code |
| 55–60 min | Confirm lunch + night priorities | `/plan-today` |

### Lunch session — 45–60 min (suggested 12:30–1:30 PM Central)
**Theme: Connect & Build**

| Time | Activity | Tool |
|---|---|---|
| 0–10 min | Personal-touch inbox triage | Gmail |
| 10–40 min | ONE of: human conversation OR deep build | Phone/Zoom or Claude Code |
| 40–55 min | User research signals + scheduling | Airtable + Calendar |
| 55–60 min | Stand-up note for night session | `meritgiving-ops/state/last-session.md` |

### Night session — 45–60 min (suggested 9:00–10:00 PM Central)
**Theme: Ship & Reflect**

| Time | Activity | Tool |
|---|---|---|
| 0–10 min | Review what shipped today | `/ops` dashboard |
| 10–35 min | Build/ship block | Claude Code |
| 35–50 min | `/plan-tomorrow` review + adjust | Claude Code |
| 50–60 min | Weekly habit (varies by day) | See weekly table |

---

## Weekly rhythm

| Day | Morning | Lunch | Night |
|---|---|---|---|
| **Mon** | `/weekly-allhands` review | Advisor or sponsor call | Plan the week |
| **Tue** | Strategic block (deep work) | Build session | Ship deliverable |
| **Wed** | Approval queue priority | User research call | Content review |
| **Thu** | Partnership/outreach focus | Build session | Ship deliverable |
| **Fri** | Risk review + book close prep | Inbox + community | `/weekly-retro` |
| **Sat** | (Optional) `/strategy-reading` | Off | Off |
| **Sun** | (Optional, monthly) `/monthly-prep` | Off | Off |

**Total time:** ~17–21 hours/week
**Day off rule:** Sat/Sun mostly off; skip a session = system continues async

---

## Monthly rhythm (1st of each month, ~90 min)

`/monthly` slash command generates the full review packet. You walk through it.

| Section | Owner | What you do |
|---|---|---|
| P&L + runway | finance-lead | Review, approve, sign-off |
| Product metrics + roadmap | eng-lead + data-lead | Confirm priorities |
| Growth funnel | growth-lead | Approve content plan |
| Risk register | legal-lead | Review top 5 |
| Partnership pipeline | partnerships-lead | Decide on next moves |
| OKR progress | strategy-lead | Confirm on-track / pivot |
| Nonprofit Success metrics | nonprofit-success-lead | Review escalations |

**Output:** `meritgiving-ops/briefings/monthly/YYYY-MM.md` — board-format summary, sendable to advisors

---

## Quarterly rhythm (every 3 months, ~4 hours)

`/quarterly` slash command runs the retro + planning cycle.

| Activity | Time | Output |
|---|---|---|
| Previous quarter retro | 60 min | What worked, what didn't |
| Risk register full review | 30 min | Updated `risks.md` |
| OKR retro | 30 min | Scored OKRs |
| Next quarter OKRs draft | 60 min | `okrs/YYYY-QN.md` |
| Advisor circle update | 30 min | Email sent |
| Strategy adjustments | 30 min | ADRs logged |

**Gates land here.** Phase transitions, scope changes, and major decisions happen at quarterly boundaries.

---

## Annual rhythm (once/year, ~2 days)

| Activity | Output |
|---|---|
| Annual review | `meritgiving-ops/briefings/annual/YYYY.md` |
| Mission + strategy refresh | Updated `north-star.md` |
| Risk register full reset | Updated `risks.md` |
| Compensation/equity review | (When team exists) |
| Insurance renewals | Tech E&O, Cyber, BOP |
| Tax preparation | CPA engagement |
| Annual public report | Published to `meritgiving.org/impact/YYYY` |

---

## Operating principles

1. **The system protects your attention.** No notifications outside the escalation channel. Everything else is dashboard-driven.
2. **Async by default.** Claude works continuously; you check in at session times.
3. **One inbox per channel.** Don't multi-source notifications. Email triage → Gmail. Decisions → `/approvals`. Urgent → SMS.
4. **Skip-friendly.** Missing a session doesn't break the system. Worst case: queue gets longer.
5. **Compound learning.** Every decision logged. Every problem documented. Every solution becomes a skill.
6. **Sustainable pace.** 21 hours/week is real work alongside full-time employment. Don't double it.

---

## Session checklist templates

### Morning session checklist
```
[ ] Read /morning-brief
[ ] Strategic block: [today's priority]
[ ] Approval queue cleared
[ ] Decisions logged
[ ] Today's plan confirmed
```

### Lunch session checklist
```
[ ] Inbox triaged
[ ] Human connection or build session
[ ] User research updated
[ ] Stand-up note saved
```

### Night session checklist
```
[ ] /ops dashboard reviewed
[ ] Ship block complete
[ ] /plan-tomorrow reviewed
[ ] Weekly habit (Mon plan / Fri retro / etc)
```

### Monday all-hands checklist
```
[ ] Run /weekly-allhands
[ ] Review each department report
[ ] Set weekly KPI targets
[ ] Decide week's #1 priority
[ ] Schedule advisor/sponsor calls
```

### Friday retro checklist
```
[ ] Run /weekly-retro
[ ] Score the week (1–10)
[ ] Note: what worked, what didn't
[ ] Update risks if any surfaced
[ ] Send investor/advisor update if monthly
```

---

## What this rhythm protects against

- **Burnout:** Capped hours, mandatory off-days
- **Drift:** Weekly retros and monthly reviews catch divergence
- **Loss of context:** Daily briefs and decision logs preserve memory
- **Over-engineering:** Approval queue prevents Claude from going down rabbit holes
- **Loneliness of solo founder:** Built-in human connection at lunch
- **Surprises:** Risk review every Friday, monthly review every 1st
