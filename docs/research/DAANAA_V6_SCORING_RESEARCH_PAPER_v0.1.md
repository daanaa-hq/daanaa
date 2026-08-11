# V6 Financial Context at Daanaa

## A public-interest approach to peer comparison, uncertainty, and smaller-nonprofit visibility

**Version:** 0.1 research draft  
**Date:** 2026-08-11  
**Status:** Internal research draft; not a final public methodology or launch approval  
**Prepared for:** Founder, Codex review, Claude implementation review, and academic/community critique

> **Publication note:** This paper describes the current V6 candidate implementation and the evidence available in the local repository. The companion explorer is now published at `/research/explorer` and displays the dated aggregate snapshot referenced in this draft. This paper does not claim that V6 is academically validated, that every displayed field is currently correct, or that V6 is superior to all other nonprofit research methods. Several implementation and documentation mismatches remain open and are reported explicitly below.

## Abstract

Daanaa is a nonprofit-discovery platform designed to help people make more informed giving decisions while preserving the dignity and independence of the organizations represented. Its V6 financial-context system is intended to show how an organization compares with relevant peers, while avoiding a universal charity rating or a judgment about mission impact.

The central design problem is incomplete public data. Larger or more administratively resourced organizations are more likely to have detailed, recent, and comparable filings. Smaller, newer, volunteer-led, rural, and unusual organizations may have less complete public financial information without being less valuable or less trustworthy. Treating missing information as poor performance would therefore risk confusing administrative visibility with organizational quality.

V6 addresses this problem through a tiered evidence model. When direct organizational data and sufficient peers are available, it presents direct peer context. When direct data is missing but a defensible peer group exists, it presents clearly labeled inferred context. When the evidence is too sparse, it reduces the precision of the output or withholds numeric comparison. This design is consistent with nonprofit finance research showing that reserve levels depend on organizational conditions, size, subsector, and volatility rather than one universal target.

The current local catalog contains 2,056,834 organizations, with V6 fields populated for 2,053,335 organizations (99.83%). The local audit reports 738,130 Tier 1 assignments, 1,260,923 Tier 2 assignments, 52,057 Tier 3 assignments, 2,225 Tier 4 assignments, and 3,499 unassigned organizations. These results are promising for broad discovery coverage, but they are not yet a final validation result: the documented methodology and stored assignments disagree on peer definitions and distributions; some Tier 1 records lack revenue; many Tier 2 records lack NTEECC; inferred metrics are not fully materialized; and the explorer only reflects the published snapshot, not a fully reconciled live method. V6 should therefore be treated as a candidate system requiring reconciliation, independent review, and user-comprehension testing before public claims are finalized.

## 1. Daanaa's mission and the role of V6

Daanaa's mission is to make nonprofit discovery and giving research easier while protecting donor privacy, nonprofit dignity, and methodological independence. Daanaa is not an attorney, CPA, auditor, investment adviser, lender, charity-rating agency, or regulated financial institution. It does not hold donor funds or allow payment to influence search treatment, visibility, or financial context.

V6 supports that mission in four ways:

1. **Context instead of verdicts.** Financial data is presented as one input into a giving decision, not as a measure of impact, moral worth, or organizational quality.
2. **Peer relevance.** A small community organization should not be compared indiscriminately with a national health system merely because both are nonprofits.
3. **Uncertainty visibility.** The system should disclose whether the information is direct, inferred, sparse, stale, or unavailable.
4. **Small-organization fairness.** Missing public data should be treated as an information condition, not silently converted into a negative ranking penalty.

The governing stewardship commitments require trust signals to be evidence-based, limitations to be visible, and small organizations to be treated with equal dignity. V6 is intended to operationalize those commitments, not to replace them.

## 2. Research questions

This paper treats V6 as a researchable system rather than a finished truth claim.

### Primary question

Can a public nonprofit-discovery platform provide useful financial context across organizations with uneven public data without turning missingness, size, geography, or administrative capacity into an unfair negative signal?

### Secondary questions

1. Does peer conditioning produce more interpretable context than a single registry-wide comparison?
2. Does explicit separation of direct and inferred context improve donor understanding?
3. Does the tier fallback structure expand useful discovery for smaller organizations without creating false precision?
4. How sensitive are assignments to NTEE classification, geography, revenue bands, peer minimums, filing age, and revocation status?
5. Are organizations receiving direct context systematically different from organizations receiving inferred or no context?
6. Can nonprofits understand, correct, annotate, or challenge the information presented about them without unreasonable administrative burden?

## 3. Data foundation and provenance

### 3.1 Public data sources

The intended foundation consists of public nonprofit and tax-exempt-organization records, including:

- IRS Form 990 and related public filings;
- IRS tax-exempt status and revocation information;
- ProPublica Nonprofit Explorer as an accessible aggregation and presentation of public filing data;
- National Center for Charitable Statistics (NCCS) data and sector benchmarks where licensed and appropriate;
- organization classification, geography, and other public registry fields.

The IRS explains that Form 990 and Form 990-EZ are used by tax-exempt organizations to provide information required under federal law, and that completed returns are generally available for public inspection. A filing is authoritative for what it reports, but it is not necessarily complete enough for every financial comparison. Organizations may file different forms or simplified returns, and some relevant fields may be absent or stale. [IRS Form 990 instructions](https://www.irs.gov/instructions/i990) and [IRS Form 990 resources](https://www.irs.gov/charities-non-profits/form-990-resources-and-tools).

### 3.2 Local evidence snapshot

The local V6 audit used `data/merit_registry.db` and reported:

| Measure | Observed result | Interpretation |
|---|---:|---|
| `registry_enriched` rows | 2,056,834 | Current local catalog denominator in the audit |
| Organizations with V6 assignments | 2,053,335 | 99.83% of catalog |
| Organizations without V6 assignment | 3,499 | 0.17%; audit associated these with missing/blank NTEECC |
| V6 detail fields | Tier, inference flag, peer size, description, confidence, margin | Materialized for assigned organizations |
| Active run named in project records | `v6_foundation_candidate_20260728_revised` | Must be reconciled with run metadata and source snapshot |

**Important reconciliation issue:** repository state documents also contain a different catalog denominator of 2,042,897. This paper uses 2,056,834 only when referring to the July 26 V6 local audit and labels the discrepancy as unresolved. No public coverage percentage should be published until the database path, timestamp, run, and denominator are reconciled.

## 4. What V6 is intended to calculate

V6 is a hierarchical peer-context system. It seeks the most specific peer group that is defensible given the available data, then relaxes specificity when evidence is insufficient.

### 4.1 Peer dimensions

The intended peer dimensions are:

- **NTEE classification:** a public classification of nonprofit activity;
- **geography:** state or broader region, depending on available sample size;
- **funding or operating archetype:** how the organization primarily funds or delivers its work;
- **revenue band:** a scale context that avoids comparing materially different operating sizes;
- **data availability and filing year:** whether the required metric is directly observed and how current it is.

The design principle is not “find the perfect peer.” It is “use the narrowest peer group that has enough evidence to be explainable and stable; otherwise broaden the context or withhold the numeric signal.”

### 4.2 Tier definitions

The current stored assignment names are:

| Tier | Stored label | Intended meaning | Public treatment |
|---|---|---|---|
| 1 | `1_Direct_Regional` | Direct organizational financial data with regional peer context | May show direct values and peer comparison, if all prerequisites are met |
| 2 | `2_Regional_Inferred` | Organization lacks a required direct value; context is inferred from a defensible peer group | Must say that the value describes similar organizations, not this organization |
| 3 | `3_Limited_Context` | Evidence is limited or the peer group is broader/sparser | Use cautious context; avoid false precision |
| 4 | `4_Archetype_Only` | Only broad organizational/funding context is available | Descriptive language only; no numeric peer claim |
| Unassigned | No V6 assignment | Minimum evidence or classification unavailable | Explain that public context is unavailable; do not imply concern |

An earlier project handoff describes a five-level fallback hierarchy including a national tier. The current stored local distribution uses four named tiers. That difference must be resolved in the canonical methodology before publication.

### 4.3 Direct versus inferred context

The distinction is essential:

- **Direct context:** “This organization reported X in its filing; comparable peers report Y.”
- **Inferred context:** “This organization’s required direct value is unavailable. Similar organizations in the defined peer group report a typical range of Y.”

An inferred peer statistic must never be phrased as the organization’s actual financial condition. The system should display the peer definition, number of usable peers, filing years, source types, metric availability, and uncertainty.

### 4.4 Confidence and uncertainty

The implementation maps peer evidence to human-readable confidence labels and margins. The current project documents mappings such as high/±5%, good/±7%, moderate/±10%, and archetype-only/±15%. These values should be interpreted as product uncertainty bands, not as automatically valid statistical confidence intervals. A formal statistical interpretation requires a defined estimator, sampling frame, variance model, missingness treatment, and calibration study.

The paper therefore recommends calling these **displayed uncertainty margins** until the statistical basis is formally documented and validated.

## 5. Current local results

The July 26 local V6 audit reported the following distribution:

| Tier | Organizations | Share of full catalog | Share of assigned V6 records |
|---|---:|---:|---:|
| Tier 1: Direct Regional | 738,130 | 35.9% | 36.0% |
| Tier 2: Regional Inferred | 1,260,923 | 61.3% | 61.5% |
| Tier 3: Limited Context | 52,057 | 2.5% | 2.5% |
| Tier 4: Archetype Only | 2,225 | 0.1% | 0.1% |
| Unassigned | 3,499 | 0.2% | — |
| **Total** | **2,056,834** | **100.0%** | **100.0%** |

### 5.1 Coverage chart

```text
Tier 1 Direct Regional     738,130  |██████████████                      | 35.9%
Tier 2 Regional Inferred 1,260,923  |█████████████████████████           | 61.3%
Tier 3 Limited Context      52,057  |█                                   |  2.5%
Tier 4 Archetype Only        2,225  |                                    |  0.1%
Unassigned                  3,499  |                                    |  0.2%
```

The combined Tier 1 and Tier 2 count is 1,999,053 organizations, or approximately 97.2% of the audit denominator. This is a coverage result, not an accuracy result. Broad coverage is valuable only if the labels remain honest and the underlying peer definitions are reproducible.

### 5.2 Data-contract findings

The same audit identified issues that materially affect interpretation:

- 13,991 Tier 1 records had null `total_revenue`, although Tier 1 is documented as requiring direct revenue data.
- 405,987 Tier 2 records had blank NTEECC, meaning their effective peer grouping may be broader than the documented NTEE-plus-state-plus-archetype definition.
- Stored V6 fields include tier, confidence, margin, peer size, and description, but do not consistently materialize the inferred peer median, percentile range, metric availability, or source-year summary described in the methodology.
- The frontend has been observed to hardcode `±10%` and an example reserve value rather than consistently rendering the organization-specific stored values.
- The current API detail route can return V6 fields, while the list/search response has historically not selected all V6 fields.

These are not minor editorial issues. They determine whether a donor can reproduce what “similar organizations” means and whether the interface displays the same uncertainty the database stores.

## 6. How V6 differs from related nonprofit research

### 6.1 It is not a universal reserve target

Research on nonprofit operating reserves generally studies determinants, financial resilience, spending stability, or reserve policy. For example, Calabrese examines whether operating reserves help stabilize nonprofit spending, while Irvin and Furneaux show that appropriate reserve ranges vary with size, subsector, revenue volatility, and organizational characteristics. [Calabrese, 2018](https://doi.org/10.1002/nml.21282); [Irvin & Furneaux, 2022](https://doi.org/10.1177/08997640211057405).

V6 translates that conditional logic into a donor-facing discovery interface. It does not claim that one reserve ratio is healthy for every organization. Its contribution is operational and communicative: make the comparison group and uncertainty visible at the point where people research organizations.

### 6.2 It is not a conventional charity rating

A conventional rating often compresses many signals into one score, badge, or rank. V6 is designed to preserve several distinctions:

- direct data versus inferred data;
- narrow versus broad peer groups;
- available versus missing public evidence;
- financial context versus mission impact;
- stronger versus weaker evidence.

This does not automatically make V6 better. It makes V6 potentially more transparent for the specific question of financial context, provided the implementation actually preserves these distinctions.

### 6.3 It is not a nonprofit capacity assessment

Validated nonprofit-capacity instruments measure broader domains such as financial management, adaptive capacity, and board leadership. The Northwestern Network for Nonprofit and Social Impact describes an instrument covering eight organizational-health domains. [NNSI Nonprofit Capacity Instrument](https://nnsi.northwestern.edu/nonprofit-capacity-instrument/).

V6 is narrower. It uses public data to support discovery and questions for further research; it does not claim to assess leadership, impact, culture, community trust, or adaptive capacity.

### 6.4 It treats missingness as a research variable

The most important difference is conceptual. V6 is designed around the possibility that public financial-data availability is related to size, age, geography, subsector, staffing, filing burden, and administrative capacity. Missingness should therefore be measured and disclosed rather than silently used as a negative outcome.

That position is consistent with the IRS filing structure: organizations do not all submit the same form or the same level of financial detail. A public-data platform must distinguish “the organization is financially weak” from “the public record is insufficient for this calculation.”

## 7. Why the design may improve smaller-nonprofit visibility

Smaller organizations can be disadvantaged by systems that reward data richness, polished websites, large peer samples, or scale. V6 attempts to reduce that disadvantage through five design choices:

1. **Peer comparison by context, not registry-wide scale.** A small organization is not automatically compared with the largest institutions.
2. **Inferred context instead of silent exclusion.** When direct data is missing but a defensible peer group exists, the organization can receive useful context labeled as inferred.
3. **A safe no-signal state.** If evidence is too sparse, V6 should withhold numeric claims instead of guessing or treating missingness as failure.
4. **Peer minimums.** A minimum peer threshold reduces the risk that one or two organizations define a public benchmark.
5. **Correction and nonprofit agency.** Organizations should have a way to report errors, add clearly labeled information voluntarily, and understand how public records are used.

This is a fairness-oriented design hypothesis, not a demonstrated causal effect. Coverage expansion alone does not prove improved visibility. It could still create harm if inferred context is misunderstood, if small organizations are grouped too broadly, or if “Archetype Only” becomes a de facto penalty.

### Small-organization evaluation plan

Daanaa should report V6 coverage and outcomes by:

- revenue band;
- organization age;
- state and rural/urban proxy where responsibly available;
- NTEE category;
- filing type and filing year;
- inferred/direct/unassigned state;
- presence of a usable website or other administrative-capacity proxy.

The key test is not “how many small organizations received a tier?” It is whether smaller organizations receive useful, accurately labeled context without lower search visibility, harsher language, or greater correction burden.

## 8. Mission alignment and stewardship safeguards

| Mission or stewardship principle | V6 alignment | Required safeguard |
|---|---|---|
| Make giving research easier | Gives donors a structured starting point for questions | Keep explanations plain and avoid false precision |
| Evidence-based trust | Uses public filings and explicit peer definitions | Show sources, tax years, peer counts, and data gaps |
| Dignity for small organizations | Does not equate missing data with poor performance | Never map missingness to a negative rank or penalty |
| Donor privacy | Uses aggregate public data for the context layer | Do not expose donor activity or use it in scoring |
| Independence | No payment-based visibility or score changes | Audit for sponsorship, partnership, and monetization influence |
| Correctability | Public data and outputs can be challenged | Maintain a visible correction and appeal path |
| Explainability | Tier and inference labels can be documented | Make displayed values match stored values |

## 9. What V6 does not measure

V6 should not be interpreted as measuring:

- mission effectiveness or program impact;
- community trust, cultural competence, or lived experience;
- leadership quality or staff wellbeing;
- donor satisfaction;
- legal compliance beyond the specific public status fields shown;
- future survival or probability of failure;
- whether an organization deserves a donation;
- whether a reserve level is morally or financially “good” in isolation.

Financial context is historical, incomplete, and shaped by organizational strategy. A low reserve may reflect growth, restricted funds, disaster response, or a different operating model. A high reserve may reflect a prudent strategy, restricted assets, or timing—not necessarily better service.

## 10. Threats to validity and open risks

### Construct validity

Operating reserves are not the same as organizational effectiveness. The construct is narrower than “financial health” and should be named accordingly.

### Measurement validity

The current implementation must document exactly how reserves, peer medians, bands, and margins are calculated. A displayed margin is not a statistical confidence interval unless its estimator and calibration are specified.

### Missing-not-at-random risk

Organizations with richer filings may differ systematically from organizations with simplified or missing filings. The system must not treat the observed sample as representative without analysis.

### Geographic and classification bias

Dense states and common NTEE categories may produce larger peer groups than rural or unusual organizations. Broader fallback tiers may therefore be distributed unevenly.

### Reproducibility risk

The repository currently contains more than one V6 description and materially different assignment artifacts. The canonical run, source snapshot, code version, peer key, and exclusions must be recorded together.

### Interface risk

If the database says ±5% but the interface displays ±10%, the public product is not showing the documented method. UI/API contract tests are required.

## 11. Required validation before public publication

1. **Canonical specification:** reconcile the four-tier stored model with the five-tier documentation and choose one version.
2. **Reproducibility:** record code commit, source hashes, database snapshot, run ID, peer-key definition, thresholds, and exclusions.
3. **Coverage audit:** publish denominators and coverage by size, geography, cause, filing type, and age.
4. **Peer stability analysis:** perturb peer minimums, geography, classifications, and revenue bands; measure assignment changes.
5. **Missingness analysis:** test whether direct/inferred/unassigned status correlates with size, age, geography, or administrative proxies.
6. **UI/API contract tests:** verify that stored tier, confidence, margin, peer size, and source-year information reach the public page unchanged.
7. **Comprehension study:** test whether donors understand direct versus inferred context and “no usable public evidence.”
8. **Nonprofit review:** ask smaller nonprofit leaders whether labels are dignified, actionable, and correctable.
9. **Adversarial cases:** include new organizations, rural organizations, fiscally sponsored organizations, religious organizations, disaster-response organizations, and organizations with simplified filings.
10. **Independent critique:** invite nonprofit finance researchers, statisticians, nonprofit leaders, and affected communities to challenge the method.

## 12. Charts and the explorer

The companion explorer uses charts only from the static snapshot already published in the repository. The paper should keep the same rule: recommended figures remain valid only after the denominator and canonical run are reconciled.

### Figure 1 — Evidence-state coverage

Stacked bar of direct, inferred, limited, archetype-only, and unassigned organizations, with denominator and date.

### Figure 2 — Coverage by revenue band

For each band, show direct, inferred, limited, and no usable public context. This is the most important small-organization fairness chart.

### Figure 3 — Coverage by geography and NTEE category

Show peer-group availability and median peer size by state and cause category. Include uncertainty and suppress or aggregate small cells.

### Figure 4 — Sensitivity to peer minimum

Plot how many organizations receive each tier when the minimum peer threshold changes from 5 to 10 to 15 to 25.

### Figure 5 — Reproducibility and UI parity

Compare database values with API values and rendered values for a stratified sample. Any mismatch is a failed contract test, not a chartable success.

## 13. Proposed research hypotheses and success metrics

| Hypothesis | Test | Success measure |
|---|---|---|
| H1: Peer context is more understandable than a universal rating | Randomized comprehension test | Users correctly distinguish context from impact/rating |
| H2: Explicit inference labels reduce overinterpretation | Compare labeled and unlabeled explanations | Lower rate of mistaken “this is the organization’s actual value” responses |
| H3: V6 expands useful coverage for small organizations without penalty | Stratified coverage and visibility audit | More small organizations receive useful context without lower search treatment |
| H4: Peer fallback remains stable under reasonable parameter changes | Sensitivity analysis | Assignment changes are explainable and bounded |
| H5: Correction tools improve accuracy without burdening nonprofits | Correction-flow study | Faster resolution, low completion burden, no pay-to-correct pathway |

Negative results should be treated as successful research findings if they reveal that the model is not ready or that a display causes misunderstanding.

## 14. Conclusion

V6 is best understood as a transparency-oriented peer-context system, not a charity rating and not a universal financial-health score. Its strongest idea is the separation of direct evidence, inferred peer context, limited evidence, and no responsible numeric signal. That structure is potentially valuable for smaller nonprofits because it recognizes that public-data scarcity is not the same thing as organizational weakness.

The current evidence supports continued testing, not final public claims. The local catalog shows broad assignment coverage, but the model still needs a canonical specification, reproducible run metadata, missingness analysis, peer-stability tests, and UI/API parity. The next stage should be research and correction, not marketing certainty.

If Daanaa can demonstrate that donors understand the distinctions, smaller organizations are not penalized for missing data, and the displayed outputs are reproducible from public sources, V6 may provide a responsible alternative to opaque or scale-biased nonprofit comparison. Until then, its most honest public description is: **a candidate financial-context method designed to help people ask better questions while making uncertainty visible.**

## References and evidence

### Primary and methodological sources

1. [Internal V6 Peer Inference Methodology](../METHODOLOGY_V6_INFERENCE.md)
2. [Internal V6 Scoring Data Audit, July 26, 2026](../V6_SCORING_DATA_AUDIT_2026_07_26.md)
3. [Internal V6 Final Handoff Package](../V6_FINAL_HANDOFF_PACKAGE_2026_07_27.md)
4. [Internal research brief: Peer Financial Context Under Incomplete Public Data](../DAANAA_RESEARCH_PAPERS_REVIEW_PACKAGE_2026-07-18/PEER_FINANCIAL_CONTEXT_MISSING_DATA_REVIEW_v0.1.md)
5. [IRS Form 990 Instructions](https://www.irs.gov/instructions/i990)
6. [IRS Form 990 resources and tools](https://www.irs.gov/charities-non-profits/form-990-resources-and-tools)
7. [NCCS Core Files Documentation](https://nccs-public.readthedocs.io/_/downloads/en/latest/pdf/)

### Research on nonprofit reserves and capacity

8. Calabrese, T. D. (2018). [Do operating reserves stabilize spending by nonprofit organizations?](https://doi.org/10.1002/nml.21282) *Nonprofit Management & Leadership*.
9. Irvin, R. A., & Furneaux, C. W. (2022). [Surviving the Black Swan Event: How Much Reserves Should Nonprofit Organizations Hold?](https://doi.org/10.1177/08997640211057405) *Nonprofit and Voluntary Sector Quarterly*.
10. Kim, P. (2022). [Bridging the gaps between the theory and practice of nonprofit operating reserves](https://onlinelibrary.wiley.com/doi/full/10.1002/nml.21493). *Nonprofit Management & Leadership*.
11. [Northwestern Network for Nonprofit and Social Impact — Nonprofit Capacity Instrument](https://nnsi.northwestern.edu/nonprofit-capacity-instrument/).

## Appendix A — Reproducibility query template

The following is read-only pseudocode for the canonical database snapshot. It must be adapted to the final schema and run ID before publication:

```sql
SELECT COUNT(*) AS registry_rows
FROM registry_enriched;

SELECT
  scoring_tier_v6_inference,
  COUNT(*) AS organizations,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM registry_enriched), 2) AS pct_catalog
FROM registry_enriched
GROUP BY scoring_tier_v6_inference
ORDER BY scoring_tier_v6_inference;

SELECT
  COUNT(*) AS total,
  SUM(scoring_tier_v6_inference IS NOT NULL) AS v6_assigned,
  SUM(scoring_tier_v6_inference IS NULL) AS v6_unassigned
FROM registry_enriched;
```

The publication report should include the database checksum, snapshot timestamp, active run ID, source manifest, code commit, query output, and reviewer sign-off.
