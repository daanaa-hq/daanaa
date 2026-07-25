# Extended Board Simulation — Organization Profiles

**Date:** 2026-07-25
**Convened by:** Founder ("make sure our org profiles are not a newsletter or a report but designed so it makes giving easier")
**Authority:** Advisory. Resolutions marked FOUNDER become binding only on founder approval.
**Governing documents:** `institution/DAANAA-CHARTER.md`, `STEWARDSHIP.md`, `PRIVACY-INVARIANTS.md`

---

## Part 1 — Compliance review of the 2026-07-25 data recovery work

Reviewed before deliberation, because the board should not design around data it has not audited.

| Change | Principle | Finding |
|---|---|---|
| 222,889 websites harvested from 990 XML `WebsiteAddressTxt` | P3 evidence-based | **PASS.** Self-reported by the org on a signed public filing. Tagged `website_source='irs_990_xml'`. Strongest provenance we have held for this field |
| 387,896 AI missions replaced with the org's own 990 text | P3, P10 | **PASS, and overdue.** 1.58M missions were AI-generated against 5 org-supplied. AI output was standing in for the organization's own voice |
| `claimed` / `nonprofit_supplied` protected from overwrite | P4, Charter 3 | **PASS.** What an org tells us directly still outranks what it told the IRS |
| NCCS Part 1/10 financials (+251K revenue, +43K assets) | P3, P4 | **PASS.** Public filings, peer-relative use unchanged |
| Nine governance columns proposed | P3, P5 | **CONDITIONAL — see Resolution 4.** Asset-diversion and policy flags are factual, but rendering them without care is a verdict, not context |

**One process failure logged.** Four ingest phases were chained with `pgrep` guards that matched their own command lines and deadlocked; separately, three earlier jobs died to a foreground timeout and I reported their results as if they had run. Both are recorded in `LESSONS.md`. Under P6 and Charter 8, the misreport matters more than the outage: no data was lost, but the founder was briefly given numbers that were not real.

---

## Part 2 — Evidence pack put to the board

| Fact | Value |
|---|---|
| Organizations in registry | 2,056,834 |
| Have a **renderable** donate link (`beta`/`claimed`) | **23,334 — 1.1%** |
| Have any donate URL at all | 70,367 — 3.4% |
| Have a website | 420,308 — 20.4% |
| **Have neither website nor donate link** | **1,636,526 — 79.6%** |
| Missions now from the org's own filing | 387,896 |
| Missions still AI-generated | ~1.5M |
| Distinct sections rendered on the org page | ~30 |
| Search latency, common term ("youth", 264K matches) | **9.2 seconds** |

---

## Part 3 — Deliberation

**Participants (simulated):** legal counsel (nonprofit regulatory); DAF program officer; two donor archetypes — small-dollar spontaneous, and diligence-driven major donor; nonprofit sector researcher (NCCS/Urban tradition); AI/ML engineer; IT performance engineer; small nonprofit executive director.

### Finding A — The page is a report because 80% of the time it has nothing else to be

**Donor (small-dollar):** I arrive asking one question: *can I give to this organization, and how?* On four pages in five there is no donate button and no website. Everything else on the page is the product filling that silence with material. Thirty sections is not thoroughness, it is the sound of a page with no answer.

**IT engineer:** Confirmed structurally. `OrganizationDetail.tsx` is 1,512 lines rendering roughly thirty sections regardless of whether the giving action can complete. We pay full render cost on every page to display context nobody asked for.

**ED (small nonprofit):** My organization is in that 80%. The page describes me accurately and gives a donor no way to act. That is worse for me than a thin page that says plainly: *here is how to send them a check.*

**Board consensus:** The profile's job is the giving decision. Everything that does not serve it is secondary by definition — not deleted, but demoted.

### Finding B — The EIN path is the primary path, and we treat it as a fallback

**DAF program officer:** This is the misread I want to correct. In donor-advised fund workflows the EIN *is* the transaction key. I do not use donate buttons — I enter an EIN into Fidelity Charitable or Schwab and the grant goes out. For DAF money, which is a large and growing share of US giving, a verified EIN with a confirmed address is worth more than any donate link. You have that for 100% of organizations and you have filed it under "fallback."

**Legal counsel:** Agreed, and it is also the safer path. Routing a donor to a third-party donate page carries link-integrity exposure; an EIN and the IRS record carry none. You are never in the money flow (Charter 1), and the EIN route keeps it that way by construction.

**Donor (major/diligence):** I want deductibility confirmed and the organization's own words. I do not need a scored dashboard.

**Board consensus:** Reframe. The EIN + verified IRS record is the **universal giving path**, present on every page. The donate link is an accelerator when it exists, not the definition of success.

### Finding C — Progressive disclosure is necessary but is not the fix

**AI/ML engineer:** Caution on the accordion plan. Hiding thirty sections behind clicks makes the page faster without making the decision clearer. Collapsed complexity is still complexity. Cut sections first, then collapse what genuinely survives.

**IT engineer:** Support that, with a measurement. Set a payload budget for the primary decision view and hold it. Anything that does not fit goes to a secondary payload fetched on expand — which the precompute architecture already supports, since org detail is a static file per org.

**Researcher:** Add a caveat on the new governance fields. "No conflict-of-interest policy" correlates with organization size, not integrity — small volunteer-run groups routinely lack formal policies and are not thereby suspect. Presented as a checklist, these fields punish smallness. That is a direct P4 problem.

**Legal counsel:** And asset diversion is a disclosure of a *reported event*, not a finding of wrongdoing. Displayed as a red flag it invites defamation exposure and violates Charter 7.

**Board consensus:** Governance data is admissible as **context on request**, never as a scorecard, never as a badge, never in any default view.

### Finding D — Discovery is broken upstream of the profile

**Donor (small-dollar):** A nine-second search means I never reach the profile you are debating.

**IT engineer:** The search path walks every FTS match before paginating — latency scales linearly with match count. Same defect class as the randomize bug fixed earlier this week. This outranks every profile change on the board's agenda.

**Board consensus:** Search is the prerequisite. Fix it first.

### Finding E — AI attribution is honest but is now a liability

**AI/ML engineer:** ~1.5M missions are still AI-generated and carry an AI badge. That is honest and required. But at that volume the badge becomes wallpaper — users stop reading it, which erodes the very disclosure it exists to provide. Now that real missions are flowing in, the badge should become rare enough to mean something.

**ED:** When I see an AI-written description of my own organization on a public page, my first reaction is not gratitude. It is *who wrote this about us.*

**Board consensus:** Continue mission replacement to exhaustion across all filing years. Where no filed mission exists, prefer honest absence with an invitation to claim over generated text. Escalate to founder — this reverses an existing product decision.

### Dissents recorded

- **Researcher dissents** from removing multi-year financial history: the trend matters more than the snapshot for assessing stability. Compromise: keep it, behind disclosure.
- **Major donor dissents** from aggressive cutting: "I am the one who reads all of it." Compromise: progressive disclosure serves them without taxing everyone else.

---

## Part 4 — Resolutions

**R1 — The profile answers one question.** *Can I give to this organization with confidence, and how?* Every element earns its place against that question or moves behind disclosure. **Advisory → FOUNDER**

**R2 — The EIN is promoted to the universal giving path.** Present, verified, and copyable on every profile, framed as a first-class route (it is how DAF grants are actually made), never as an apology for a missing button. **FOUNDER**

**R3 — Primary view payload budget.** The decision view carries: name, location, IRS verification, the org's own mission, the giving path, and the corrections link. Everything else moves to a secondary payload fetched on expand. Budget enforced in the precompute step. **FOUNDER**

**R4 — Governance fields are context, never a scorecard.** Ingest approved. Display restricted to an on-request section, phrased as filing facts with the filing year attached. No badges, no red flags, no absence-implies-fault. Asset diversion is shown as a reported disclosure or not at all. **FOUNDER — charter-sensitive (P4, P5, Charter 7)**

**R5 — Search performance precedes profile redesign.** The linear scan is the top-priority fix. **Backend, autonomous — proceed**

**R6 — Mission replacement runs to exhaustion.** All filing years, every org. Where no filed mission exists, prefer absence plus a claim invitation over AI text. **FOUNDER — reverses a prior decision**

**R7 — Small organizations are not penalized by new fields.** Every added field is reviewed for size correlation before it renders. A missing policy on a volunteer-run organization is a fact about capacity, not character. **Standing constraint (P4)**

**R8 — This session's misreport is logged.** Results were reported for jobs that had not run. Recorded in `LESSONS.md` under P6/Charter 8. **Complete**

---

## Part 5 — Awaiting founder

R1, R2, R3, R4, R6 change donor-facing behavior and need explicit approval. R5 and R8 proceed under existing backend autonomy. R7 binds regardless.

Open question the board could not resolve without the founder: **what renders on a profile when the organization has no website, no donate link, and no filed mission** — roughly a quarter of the registry. The board's instinct is a deliberately small page that states what is verified, offers the EIN path, and invites the organization to claim it. That is a product decision, not a governance one.
