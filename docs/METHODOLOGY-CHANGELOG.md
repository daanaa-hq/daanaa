# Daanaa Methodology Changelog

All scoring and methodology changes are logged here in chronological order.
Each entry records: what changed, why, what it affects, and who validated it.

---

## v1.0 — Baseline (pre-launch) · 2026-06-03

### Scorer in production
- Script: `scripts/merit_scorer_v3_3.py`
- Peer grouping: NTEE major code × revenue band (1D: band only in practice)
- Metrics: program_ratio (30%), sustainability_ratio (25%), reserves_ratio (25%), leverage_ratio (20%)
- Data source: `xml_extracted.json` (~27K orgs with full 990 XML)
- Universe: all orgs in registry (includes non-deductible)

### Known issues documented at v1.0
1. **Non-deductible orgs included** — 501(c)(4), (c)(5), (c)(6) orgs in peer groups distort benchmarks for cause types like employment (43% non-deductible), civic (35%), community development (39%)
2. **program_expense_pct scale** — column is 0–100 scale (percentage). Scorer must use `pep / 100.0` for ratio. Do not multiply by 100.
3. **months_of_reserve sentinel** — 45,149 orgs capped at exactly 120 months (10 years) by data pipeline. True value unknown but higher. Endowment-type causes: 67.8% of grantmaking orgs hit the cap.
4. **Peer groups not cause-aware** — a food bank and a hospital foundation in the same revenue band are peers. Statistically invalid (ANOVA F=10,822, p<1e-300 shows 4 operating model groups are separable).
5. **86,451 orgs scored on revenue percentile only** — no financial health data. Displayed identically to fully-scored orgs in UI.
6. **Unrestricted vs. restricted net assets not distinguished** — total net assets used. An org with $10M in restricted endowment and $5K unrestricted cash appears healthy.
7. **Volunteer / human capital not measured** — IRS 990 Part I has volunteer counts for ~8,500 orgs in our dataset. Not incorporated.
8. **New/early-stage orgs disadvantaged** — no age adjustment. A 1-year-old org with startup-phase financials scores low vs. established peers.

---

## PRE-LAUNCH BLOCKERS — must fix before deploy

### CRITICAL: 17,607 auto-revoked orgs showing as tax-deductible
- These orgs have `deductibility='1'` but appear in IRS auto-revocation list
- Donors could give thinking it's deductible — it is not
- Fix: cross-check registry against `revoked_eins` table; suppress score + add warning badge
- Discovered: 2026-06-03 (data scientist audit)

### Data scientist verdict on composite scoring for no-data orgs
- Peer-group median has ±31 point CI — not defensible as an estimate
- Only honest approach: **badges + provenance**, not a composite number
- Badges approved: IRS Standing, Sector (NTEE only), Verified Website, Human Mission, Revoked flag
- AI-generated missions do NOT count as "has mission" evidence
- Confirmed: 2026-06-03

### Three display tiers (not two)
- Scored (386K): real 0-100 + peer context
- Revenue-placed (115K): revenue band chip + "postcard level — financials not public"
- Visible (1.1M): badges only — IRS standing, sector, website, human mission, revoked flag

### Visibility Score design principle (confirmed 2026-06-03)
**Purely additive. No org is penalized for what they cannot afford.**
- Every org starts at 0. Points are earned by what exists — never deducted for what's missing.
- A small org without a website is not "less visible" — they just haven't earned that point yet.
- **Critical rule:** If Daanaa can provide a service on behalf of the org, the org earns credit for it.
  Daanaa doing the work = the org's capability. They shouldn't need a tech team to benefit.
- Future services Daanaa offers (letters, verification) also earn the org visibility points.

### Donation acknowledgment letters (future service — not built yet)
IRS §170(f)(8) requires a written acknowledgment for charitable contributions ≥ $250.
Small orgs often handle this manually or inconsistently. Large orgs use donor management software.

**Future Daanaa service:** When a donor gives through a Daanaa-linked payment processor,
auto-generate and deliver the IRS-compliant acknowledgment letter on behalf of the org.
- Org earns visibility points for having this service active
- Donor gets their receipt automatically
- Builds toward Daanaa as a trust layer for the sector

**Legal/financial backing required before building.** Charitable solicitation registration,
state-by-state compliance, and processor partnership agreements needed first.
Tag: revisit when Daanaa has legal counsel and operating budget.

---

## Planned: v2.0 — Cause-Aware Peer Groups · target before launch

### What will change
- **Universe**: filtered to `deductibility = '1'` only (tax-deductible 501(c)(3) orgs)
- **Peer grouping**: 4 operating model groups × 6 revenue bands = 24 peer cells
  - Group A — Direct Service (human services, food, employment, mental health, youth, animals, crime prevention, international, recreation, religion, early childhood, legal aid, civil rights)
  - Group B — Mission Infrastructure (education, health, arts, environment, science, community development, k-12 education, health advocacy, music, theater, visual arts)
  - Group C — Asset Stewards (housing, public safety, cultural heritage, mutual aid, animal welfare, sports, higher education, disability support, economic development, food security, senior services, libraries, museums)
  - Group D — Endowment & Capital (grantmaking, conservation, historical preservation, disease research, scholarships, faith, religious, veterans, medical research)
- **Statistical basis**: ANOVA on deductible-only population validates group separability
- **Metrics adjusted per group**:
  - Direct Service: de-weight reserves (thin reserves = mission delivery, not weakness)
  - Asset Stewards: de-weight asset intensity (high ratio = physical program delivery)
  - Endowment & Capital: exclude reserve metric (sentinel-distorted); use net asset growth instead
- **program_expense_pct**: used as-is (0–100 scale) — divide by 100 before ratio math
- **months_of_reserve**: exclude sentinel (=120) from peer percentile calculations; flag as ">10yr" in UI
- **Human capital**: acknowledged in methodology page; volunteer count surfaced for orgs with data (Independent Sector rate $31.80/hr, 2023)
- **Score transparency tiers**: clearly label orgs by data quality (4-metric / revenue-only / unscored)

### Validation required before v2.0 deploy
- [ ] Full cause × band matrix reviewed for all 47 cause types
- [ ] Benchmark ranges reviewed against known sector data (Nonprofit Finance Fund, Charity Navigator)
- [ ] Sector Health page updated to reflect group taxonomy
- [ ] Methodology page updated (all 4 groups, volunteer acknowledgment, data limitations)
- [ ] How It Works page updated
- [ ] Tiers page updated (tier thresholds may shift with new peer groups)
- [ ] Score reset run on server with v2.0 scorer
- [ ] Board-level review of pre/post score distributions
- [ ] Faith/religion handling confirmed (separate treatment or disclosed limitation)

### Pages to update
- `/methodology` — major revision
- `/sector-health` — add operating model group breakdown
- `/how-it-works` — update scoring explanation
- `/tiers` — update if tier thresholds change
- `/for-nonprofits` — update score explanation for nonprofit claimants

---

## Methodology Principles (permanent)

These do not change version to version:

1. **Peer comparison only** — orgs are scored relative to true peers, never against the full sector
2. **Evidence-based only** — no signal enters the score without a documented data source
3. **Fail closed on data gaps** — missing data = no score, not an estimated score
4. **Donor privacy** — individual giving behavior never enters peer calculations
5. **Small org dignity** — metrics are chosen so a well-run $50K org can score as high as a well-run $50M org
6. **Transparent limitations** — every known data quality issue is disclosed on the methodology page
7. **Changelog required** — every methodology change is logged here before deployment
8. **Monthly sector review** — peer group benchmarks reviewed on IRS BMF release cycle (quarterly)

---

## Volunteer / Human Capital (future signal)

**Not yet in score. Acknowledged in methodology.**

Formula (Independent Sector standard):
```
human_capital_value = volunteer_count × sector_avg_hours_per_year × $31.80/hr
```

Data available now: volunteer counts for ~8,500 orgs from IRS 990 Part I (xml_extracted.json).
Missing: hours per volunteer (990 does not require this). Workaround: use Independent Sector sector-specific average hours by cause type.

Will be incorporated as a **supplemental display metric** (not part of 0–100 score) once:
- Broader 990 XML coverage achieved (currently ~27K of 1.8M orgs)
- Sector-specific hour estimates validated against NFF/Independent Sector data
- Display reviewed for donor clarity (show alongside financial score, not combined)
