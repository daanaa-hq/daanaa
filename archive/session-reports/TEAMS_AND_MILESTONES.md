# Daanaa — Teams & Milestone Gates

One solo founder + AI agent teams. Everything is milestone-gated: a gate clears,
the next workstreams unlock. Nothing public-facing ships before its gate.
All teams operate under STEWARDSHIP.md — the Stewardship gate (Team 7) can block
any other team's output.

Last updated: 2026-06-09

---

## Operating model

```
                        ┌─────────────────────────┐
                        │   AKBAR (CEO, human)     │
                        │  signs, pays, calls,     │
                        │  approves, relationships │
                        └────────────┬─────────────┘
                                     │ approves / directs
        ┌──────────┬──────────┬──────┴─────┬───────────┬──────────┐
        ▼          ▼          ▼            ▼           ▼          ▼
   T1 Platform  T2 Legal   T3 Capital  T4 Nonprofit  T5 Partner  T6 Market
   (agents:     (agents:   (agents:    Services      ships       ing
    live)        research)  drafting)  (agents:      (agents:    (agents:
                                        gated)        drafting)   content)
        └──────────┴──────────┴────────────┴───────────┴──────────┘
                                     │ everything passes through
                                     ▼
                        T7 Stewardship & Governance
                        (audit agents, principles gate)
```

**Division of labor rule:** Agents draft, research, build, monitor, and prepare.
Akbar signs, sends, pays, calls, and approves. No agent sends external email,
spends money, or publishes without explicit approval (matches existing email
agent pattern: drafts only, no auto-send).

---

## The Gates

```
G0 MONEY PATH ──► G1 LEGAL ──► G2 GIVING LIVE ──► G3 SERVICES ──► G4 INFRA ──► G5 TEAM
(fiscal sponsor    (attorney     (Every.org +       (letters,      (processor    (first
 + grant pipeline)  memo)         revocation gate)   claims @100+)  partner)      hire)
```

### G0 — Money Path (NOW, weeks 1-4)
**Goal:** Grant eligibility + first applications out, so there is money for attorneys.
- [ ] Decide structure: fiscal sponsorship vs. own 501(c)(3) vs. LLC-only grants
      (some funders do fund LLCs with charitable purpose — Fast Forward-style tech
      accelerators, Mozilla-style open infrastructure funds; verify each)
- [ ] Akbar files DBA letter (already in hand)
- [ ] Grant pipeline built: 10-15 researched prospects, 3-5 applications drafted
- [ ] Target funder classes: nonprofit-infrastructure (Fast Forward, Echoing Green,
      Draper Richards Kaplan), civic data / AI-for-good (Patrick J. McGovern Fdn,
      Knight, Omidyar, Schmidt-class), community foundations with tech mandates.
      Agents verify current open programs before any application — no stale leads.
**Unlocks:** G1 (attorney budget ~$500-1500), T3 fully active.

### G1 — Legal Clearance (weeks 3-8, parallel where possible)
**Goal:** One attorney engagement answering FOUR questions at once (cheaper bundled):
1. Charitable solicitation: do our "Give here" CTAs require state registrations? (TODOS G1)
2. Letter service: can we automate §170(f)(8) acknowledgments AS the org's agent?
   What disclaimers/authorization does the claiming org need to grant us?
3. Entity structure: fiscal sponsorship vs nonprofit arm vs LLC — what fits the
   funding strategy from G0?
4. GPO formation requirements (just the 1-page sketch — full work deferred to G3)
**Unlocks:** G2 give paths, T4 letter service build, GPO legal pathway known.

### G2 — Giving Live (weeks 6-12)
**Goal:** Public, legally-clean give paths.
- [ ] G2 revocation filter verified end-to-end (TODOS G2 — mostly done, needs
      quarterly IRS list refresh automation)
- [ ] Every.org partnership signed (outreach draft exists: partners@daanaa.org)
- [ ] EIN-router fallback behind flag flipped on
- [ ] Partner logo strip built (only when signed — no fake trust signals)
**Unlocks:** T6 marketing push (organic), donor growth metrics, the volume story
that makes G4 processor pitches credible.

### G3 — Nonprofit Services Revenue (months 3-6)
**Goal:** First earned revenue from services nonprofits actually need.
- [ ] Letter automation service live (legal language from G1, claiming org
      authorizes Daanaa as acknowledgment agent, org's name on every letter)
- [ ] 100+ claimed orgs (claiming flow exists; growth via letter service hook:
      "claim your profile, get automated donation receipts")
- [ ] GPO exploration formally opens: survey claimed orgs on top 5 overspend
      categories (software, insurance, payment processing, supplies, shipping)
**Unlocks:** GPO build decision (needs member volume), pricing experiments,
T4 becomes a revenue team.

### G4 — Infrastructure Partnership (months 5-9)
**Goal:** A payments-infrastructure partner so money NEVER touches Daanaa.
Sequenced pitch ladder (volume makes each rung credible):
1. Every.org deepening (API, verified status) — already in motion at G2
2. Zeffy / Givebutter-class nonprofit processors — integration partnerships
3. **Stax-class pitch: "open a nonprofit division, we bring the demand"** —
   pitch deck needs: claimed-org count, give-path volume, letter-service adoption.
   This is the clean-slate infrastructure play; it lands on traction, not vision.
**Unlocks:** Revenue share / referral economics (stewardship-checked), GPO
payment-processing category (often nonprofits' #1 overspend).

### G5 — First Hire (when funding > $100K landed)
**Goal:** Engineer #1 or ops #1 depending on which constraint binds first.
**Unlocks:** Founder time moves to relationships and capital full-time.

---

## The Teams

### T1 — Platform & Data Engineering (LIVE today)
**Charter:** Keep the product accurate, fast, and honest. 1.97M orgs, scores, search, deploys.
**Agents running now:** nightly pipeline, IRS daily watch, surge monitor + outcome
analyzer, safe droplet deploys, FTS/embedding rebuilds.
**Agents to add:** donate-link rot checker (weekly), quarterly sector snapshot
publisher, anomaly alerts (revocation spikes, score drift) to founder.
**Human-only:** deploy approvals, methodology changes.
**KPI:** uptime, data freshness, zero trust-signal errors.

### T2 — Legal & Compliance (gate-keeper)
**Charter:** Get the four G1 questions answered; maintain compliance map after.
**Agents do now:** research memo per question (50-state solicitation overview,
§170(f)(8) requirements digest, fiscal sponsorship comparison table, GPO entity
sketch) so attorney hours are spent confirming, not educating — cuts the bill.
**Human-only:** engaging attorney, signing engagement letter, paying.
**KPI:** G1 cleared under $1,500; compliance checklist live on every give page.

### T3 — Capital & Funding
**Charter:** Grants first, earned revenue second, investment only if needed.
**Agents do now:**
- Prospect research agent: verify open programs, deadlines, eligibility (LLC vs
  fiscal sponsor), fit score per funder
- Application drafter: one master narrative (the invisible 97%, stewardship
  commitment, 537K scored orgs, methodology) adapted per funder; Akbar edits voice
- Pipeline tracker: applications out / pending / won, follow-up reminders
**Human-only:** submitting applications, funder calls, fiscal sponsor agreement.
**KPI:** 5 applications out by week 6; first dollars by month 4.

### T4 — Nonprofit Services (gated on G1)
**Charter:** Services nonprofits will adopt because they remove real pain.
**Build order:** letter automation → claiming growth loop → GPO survey → GPO.
**Agents do now (pre-gate, behind flags):** letter template engine prototype
(IRS-compliant fields: org name/EIN, gift date/amount, no-goods-or-services
clause), claiming-flow polish, GPO category research brief.
**Human-only:** pricing decisions, GPO vendor negotiations (later).
**KPI:** 100 claimed orgs; first paid letter batch; GPO survey n>50.

### T5 — Partnerships
**Charter:** Every.org → Candid → processor-class (Stax pitch lives here).
**Agents do now:** keep outreach drafts current, build the traction one-pager
that updates itself from live metrics (orgs, claims, give-path volume), prep
the Stax-class deck skeleton so it's ready the day the numbers are.
**Human-only:** sending the emails, every call, every signature.
**KPI:** Every.org signed (G2); one processor conversation started by G4.

### T6 — Marketing & Community (organic-first)
**Charter:** Earn attention with the data, never buy trust. No paid placement ever
(Stewardship #1/#7).
**Agents do now:** bi-weekly cause spotlights (live), monthly newsletter
(script exists — wire send after review), hidden-gem stories drafted from real
data, methodology explainers. All copy passes kitchen-table voice rules.
**Human-only:** publishing approval, conference talks, press conversations,
LinkedIn posting (Minova disclosure consent FIRST — TODOS #20).
**KPI:** newsletter subscribers, organic search growth, claimed-org referrals.

### T7 — Stewardship & Governance (cross-cutting veto)
**Charter:** Every team's output passes the 11 principles. Agents audit agents.
**Agents do now:** pre-publish principles check on copy, trust-signal audit
(no badge without evidence), privacy-invariant checks (already pre-commit),
agent-action log review (agent_actions table), quarterly stewardship report.
**Human-only:** principle changes, anything ambiguous.
**KPI:** zero stewardship violations shipped; every flag resolved + documented.

---

## What only Akbar can do (the weekly human list)

1. **Send:** grant applications, partnership emails (drafts will be waiting)
2. **Sign:** fiscal sponsor agreement, attorney engagement, DBA letter
3. **Pay:** attorney (~$500-1500 at G1), conference travel (later)
4. **Call:** funders, Every.org, attorney, advisors, Leslie Chandler intro
5. **Approve:** anything public, anything spending, anything touching production

Everything else — research, drafting, building, monitoring, auditing — is agent work.

---

## What agents can start THIS WEEK (no gate required)

| # | Deliverable | Team | Output |
|---|------------|------|--------|
| 1 | Funder prospect list (verified, scored, deadline-sorted) | T3 | markdown brief |
| 2 | Master grant narrative + 2 adapted drafts | T3 | drafts for editing |
| 3 | Attorney prep packet (4 research memos) | T2 | cuts attorney bill |
| 4 | Letter service prototype behind flag | T4 | demo-able |
| 5 | Traction one-pager (auto-updating from live metrics) | T5 | partnership asset |
| 6 | GPO overspend research brief | T4 | informs G3 survey |
| 7 | Donate-link rot checker agent | T1 | weekly cron |

---

## Honest notes (so future-us remembers why)

- **Stax-class pitch is a traction play, not a vision play.** Sequenced to G4
  deliberately — pitching a processor to open a division works when you bring
  demand, not a deck. Every.org first.
- **GPO is a second business.** Gated on claimed-org volume (G3) because a GPO
  with no members has no negotiating power. Survey before build.
- **Letter service must be org-authorized.** Daanaa generates AS the org's agent;
  the org's name is on the letter; we never imply we're the charity. Attorney
  confirms the authorization language at G1.
- **Funding before entity perfection.** Fiscal sponsorship gets grant eligibility
  in weeks. Don't wait on a 501(c)(3) determination letter to start applying —
  many sponsors let you apply the day the agreement is signed.
- **Marketing stays organic** because the trust model IS the brand. The data and
  the stewardship posture are the marketing.
