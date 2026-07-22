# Peer Financial Context Under Incomplete Public Data

Status: research brief for academic and community review  
Prepared: 2026-07-18  
Authority: draft only; does not change production scoring

## Publication integrity

### Organizational status

Daanaa is currently a public interest initiative and a DBA of EcoMargins Consulting LLC, a for-profit entity. It is funded by the founder and operating with deliberately low overhead while the concept is tested. Daanaa does not process donations, hold donor funds, or take a percentage of gifts. This structure does not represent Daanaa as a nonprofit, tax-exempt organization, or charity-rating agency. Future structural options may be considered as the mission, resources, and community review develop.


This brief is a directed by the founder research proposal prepared with editorial
assistance. It does not report completed validation, academic findings, or a
production methodology change. Claims and proposed tests should be reviewed
against primary sources, local data definitions, nonprofit experience, and
independent methodological critique before publication.

## Abstract

Daanaa is developing a public nonprofit discovery platform that presents
financial information as peer context rather than as a universal rating. The
current context layer uses public nonprofit records, including IRS filings,
to compare operating reserve patterns among organizations with similar funding
models and revenue size.

This brief addresses a difficult boundary: many nonprofits do not have
complete, recent, or comparable public financial information. The central
claim of this brief is conservative: missing public evidence is an information
condition, not evidence of financial weakness. A public interest discovery
system should measure and disclose coverage limits rather than silently
penalize organizations that are less documented.

This is a proposed review agenda, not a validated research finding. Daanaa is
seeking independent critique from nonprofit scholars, statisticians, nonprofit
leaders, fundraisers, donors, and communities affected by the presentation.

## Questions for review

1. What minimum evidence is required before a public financial context signal
   can be calculated?
2. When should the system return no signal rather than a score or label?
3. Is financial-data availability associated with organization size, age,
   geography, cause, operating model, language, or administrative capacity?
4. How should stale, partial, conflicting, or simplified filings be treated?
5. How do donors interpret “not enough public evidence” compared with
   “financial concern”?
6. What information should nonprofits be able to correct, add voluntarily,
   withdraw, export, or annotate?
7. Which tests are necessary before a coverage expansion or methodology change?

## Current measurement boundary

The intended context signal is narrow. It is not a measure of mission quality,
community trust, program impact, leadership quality, or moral worth. It should
not be used to infer those things.

The current public explanation describes operating reserves as a relative
measure within comparable peer groups. A context signal is only defensible when
the underlying financial evidence is sufficiently recent, comparable, and
complete for the intended calculation.

The [IRS Form 990 instructions](https://www.irs.gov/instructions/i990) explain
that the return contains required information about activities, finances,
governance, and compliance, while also defining which organizations file other
returns or simplified forms. That distinction matters here: a public record can
be authoritative for what it reports without being complete enough for every
comparison.

The following conditions should be treated as evidence limitations, not
negative outcomes:

- no usable public filing;
- a filing that omits the fields required for the calculation;
- a filing outside the accepted freshness window;
- conflicting public sources that cannot be resolved;
- a peer group too small or heterogeneous for a stable comparison;
- an organization whose operating model does not fit an established peer cell.

## Proposed evidence states

| State | Meaning | Public treatment |
|---|---|---|
| Context available | Minimum evidence and peer requirements are met | Show the context signal, source, year, peer definition, and limitations |
| Partial public evidence | Some relevant information exists, but the required calculation is incomplete | Do not calculate the signal; explain what is and is not available |
| No usable public evidence | The platform cannot responsibly calculate from public records | Say that public financial context is unavailable; do not imply concern |
| Stale evidence | A usable filing exists but does not meet the freshness threshold | Show the date and withhold or qualify the signal according to the reviewed rule |
| Under review | A correction, conflict, or methodology question is unresolved | Withhold the affected output and provide a correction path |

These states should never be mapped to a hidden ranking penalty.

## Missingness and fairness analysis

Before treating coverage as a product success, Daanaa should report missingness
by at least:

- revenue band and organization size;
- organization age;
- geography and urban or rural setting;
- cause area and NTEE classification;
- funding model and operating model;
- filing type and filing year;
- whether the organization is volunteer-led or has limited staff capacity,
  where that information is responsibly available.

The analysis should test whether organizations with available context differ
systematically from organizations without it. It should not assume that the
missingness mechanism is random.

## Proposed validation work

### Coverage audit

Measure the percentage of active organizations in each evidence state and
publish the denominator, date, source coverage, and exclusions.

### Sensitivity analysis

Test whether reasonable changes to freshness windows, peer minimums, revenue
bands, or field requirements materially change which organizations receive a
signal.

### Peer stability

Test whether peer membership and percentile position remain stable when small
changes are made to classification, revenue bands, or source updates.

### Donor comprehension

Use plain-language user testing to determine whether donors understand that
“not enough public evidence” does not mean “poor financial health.”

### Nonprofit dignity and burden review

Ask smaller nonprofit leaders whether the labels, correction path, and optional
information requests are understandable, fair, and worth the effort required.

### Red-team cases

Include organizations that are:

- very small but financially sound;
- new and growing;
- fiscally sponsored or operating under an unusual structure;
- rooted in community with limited administrative capacity;
- recently affected by crisis or disaster;
- filing late or using a simplified filing;
- financially healthy but missing public fields.

## Governance boundaries

- No provided by nonprofits information should silently replace public records.
- Any provided by nonprofits information must be labeled, voluntary, controlled by
  the nonprofit, and subject to correction and withdrawal rules.
- No private or entrusted nonprofit information may be used for prospecting,
  lead scoring, marketing, consulting, or external AI services.
- No payment, partnership, sponsorship, or relationship may affect the signal,
  visibility, search treatment, or ranking.
- Academic or community reviewers may critique the method but may not decide an
  individual organization’s public outcome.
- Daanaa must publish uncertainty and limitations where they affect a donor’s
  reasonable interpretation.

## Requested academic and community contribution

Reviewers are invited to challenge:

1. the proposed evidence states;
2. the missingness and fairness analysis;
3. the minimum evidence threshold;
4. the for donors language;
5. the correction and appeal path;
6. the risks of using relative reserve context in donor discovery;
7. the claim that this approach broadens discovery rather than rewarding
   administrative polish.

The desired output is a written critique or recorded review memo. Daanaa is
not seeking validation, a logo, a public endorsement, or a favorable result.

## Decision gate

No expansion of public financial-context claims for data-dark nonprofits should
be treated as complete until this brief has been reviewed and the resulting
decisions have been documented.

The academic literature also cautions against treating reserves as a universal
target. [Calabrese's study of operating reserves](https://doi.org/10.1002/nml.21282)
examines whether reserves stabilize nonprofit spending, while [Irvin and
Furneaux's work on reserves after a black-swan event](https://doi.org/10.1177/08997640211057405)
argues that an appropriate reserve level depends on organizational conditions.
These sources support studying reserve context; they do not justify a single
for donors threshold or a moral judgment about a nonprofit.

## Related materials

- [The Daanaa Vision](https://daanaa.org/pages/daanaa-vision.html)
- [AI Governance](https://daanaa.org/pages/ai-governance.html)
- [Academic Methods Review Plan](https://daanaa.org/research)
- [Daanaa Methodology](https://daanaa.org/methodology)
- [Daanaa Stewardship Charter](https://daanaa.org/charter)
