# Daanaa Charter Review

Status: internal review draft  
Subject: `institution/DAANAA-CHARTER.md` and published Charter language  
Prepared: 2026-07-14  
Authority: review artifact only; does not amend the adopted Charter

## Summary

The Charter is mission-aligned and unusually clear about donation custody, paid influence, data restraint, and dignity. The main risk is not moral direction. The main risk is enforceability: several public promises are broader than the currently demonstrated technical, operational, legal, and audit controls.

This review recommends narrowing ambiguous wording without weakening the Charter's substance. The strongest public promises should be retained, but only where Daanaa can explain how they are enforced, audited, and corrected.

## Line-by-Line Promise Review

| Charter promise | Current assessment | Recommendation |
|---|---|---|
| "We will never take a cut of a donation." | Aligned; supported by Terms, donation receipt 410 behavior, and absence of donation merchant flow in reviewed code. | Keep. Add a Donation Boundary Policy covering donation links, Wallet logs, return prompts, and future financial services. |
| "We will never sell anything inside Daanaa." | Spirit aligned, wording overbroad. It may conflict with optional paid capacity tools, Guild services, or future nonprofit financial infrastructure. | Narrow to "We will never sell placement, visibility, ranking, or favorable public treatment inside Daanaa." Define free core platform separately. Founder decision required. |
| "We will never use entrusted information to sell you services outside Daanaa." | Aligned as principle. Current firewall policy is strong, but code-level enforcement is not fully demonstrated by `scripts/privacy_check.sh`. | Keep principle; revise implementation claim until controls are demonstrable. |
| "This is enforced in our code." | Not fully supported by current evidence. Privacy docs cite Gate 8, but the local privacy check script reviewed only implements gates 1-4. | Do not publish as absolute until tests enforce Tier 2 firewall paths. |
| "We will never sell or share your data." | Mission-aligned but legally and operationally too absolute unless exceptions are defined for service providers, legal obligations, consented research, exports, and public records. | Revise to "We will never sell entrusted data or share it for advertising, vendor sales, or unrelated use." Add explicit governed exceptions. Legal review required. |
| "We will never charge you for the platform." | Needs definition. Free public discovery and core participation are constitutional; optional paid services are contemplated elsewhere. | Revise to distinguish free public discovery/core participation from optional paid capacity services. Founder decision required. |
| "We will never let money shape the truth." | Strongly aligned with constitutional rules and vendor policy. | Keep. Add audit control mapping from payments/relationships to search/ranking/context outputs. |
| "We will never shame organizations." | Aligned; Peer Financial Context is framed as context. | Keep. Require UX review for sorting, labels, badges, and visual hierarchy. |
| "We will never hide mistakes." | Aligned. | Keep. Define correction log scope and privacy limits before claiming every correction is public. |
| "We will never lock you in." | Aligned. | Keep. Add export formats and deletion/withdrawal controls by data tier. |
| "We will never weaken this Charter quietly." | Aligned. | Keep. Define amendment notice, review, and version history process. |
| "Quarterly audit, enforced at the code level." | Aspirational or partially documented; first complete audit evidence not found. | Publish only after first audit log and code-control matrix exist. |
| "You will get an answer from a human." | Values-aligned but may become an SLA promise. | Revise to "Material correction requests are reviewed by an accountable human." Define staffing standard before stronger promise. |

## Redline Recommendations

1. Replace "never sell anything inside Daanaa" with "never sell placement, visibility, ranking, favorable treatment, or truth inside Daanaa."
2. Replace "never charge you for the platform" with "core public discovery, public IRS information, and basic nonprofit participation remain free."
3. Replace "never sell or share your data" with "never sell entrusted data or share it for advertising, vendor sales, or unrelated commercial use; limited sharing for service providers, legal obligations, user-directed exports, consented research, or public records is governed by policy."
4. Replace "enforced at the code level" with "must be enforced by code, audit, and operational controls; controls are published as they become verifiable."
5. Replace "quarterly audit" with "quarterly stewardship review" unless an actual quarterly audit protocol, owner, and log are operational.
6. Replace "every correction is documented publicly" with "material public corrections are documented in a privacy-preserving correction record."

## Clean Revised Charter Draft

### Daanaa Charter vNext Draft

Daanaa exists to make giving easy.

We help people discover and understand nonprofit organizations, and we help nonprofits strengthen their public presence and operating capacity.

We make these commitments:

1. We will never take custody of donations, process donations as merchant of record, or take a percentage or cut of gifts.
2. We will never sell placement, visibility, ranking, favorable treatment, or public truth inside Daanaa.
3. Core public nonprofit discovery, public IRS information, and basic nonprofit participation remain free.
4. Payment, partnership, sponsorship, consulting, vendor relationships, or future financial services will not influence public visibility, ranking, search treatment, descriptions, recommendations presented as independent, or Peer Financial Context.
5. We will distinguish public records, nonprofit-provided information, Daanaa-created enhancements, calculated context, estimates, AI-generated content, and human-authored interpretation where material.
6. We will not sell entrusted nonprofit data or donor activity.
7. We will not share entrusted data for advertising, vendor sales, or unrelated commercial use. Limited sharing for service providers, legal obligations, user-directed exports, consented research, or public records must be governed by policy.
8. We will not shame organizations. Financial context is context, not a verdict on mission worth.
9. We will disclose material AI assistance where it affects public representation, nonprofit burden, trust, or consequential interpretation.
10. We will provide meaningful paths for correction, export, deletion, withdrawal, or removal of Daanaa-created enhancements where appropriate.
11. We will preserve nonprofit autonomy and avoid hidden dependence.
12. We will document material mistakes and corrections in a privacy-preserving way.
13. We will not weaken this Charter quietly. Material changes require public version history and constitutional review.

This draft is not legal terms, a privacy policy, or a technical manual. It is a public stewardship promise. Each promise must be supported by policies, code controls, operational review, and correction paths before publication as final language.

## Promise-to-Control Matrix

| Promise | Current controls found | Status | Gap |
|---|---|---|---|
| No donation custody or cut | Terms; donation receipt 410; donate links route to nonprofit channels; no merchant-of-record donation flow found. | Partially enforced | Donation Boundary Policy needed for all donation-adjacent surfaces. |
| No paid influence on public truth | Constitution; Charter; `VENDOR-POLICY.md`; `STEWARDSHIP.md`. | Documented only / partially enforced | Need relationship-to-output audit and tests where practical. |
| Free core discovery | Constitution; Charter; frontend route; public visibility exports. | Documented only / partially enforced | Define "core platform" and optional paid services boundary. |
| Public vs entrusted data separation | Constitution; Tier 0/1/2 classification; privacy docs. | Partially enforced | Privacy check does not demonstrate claimed Tier 2 Gate 8. |
| AI disclosure | Concierge endpoint docstring; board resolution; AI principles. | Partially enforced | Test/schema drift blocks concierge test suite. |
| Context not verdict | Constitution; methodology language; stewardship docs. | Documented only / partially enforced | Directory sorting and visual hierarchy require product review. |
| Correction and deletion | Charter; privacy docs; profile claim paths. | Partially enforced | Need tier-specific export/delete/removal matrix and public correction log scope. |
| No lock-in | Charter; capacity transfer principles. | Documented only | Need export formats and operational process evidence. |
| Charter amendment control | Charter; authority docs. | Documented only | Need version history and amendment workflow. |

## Claims Not Ready for Publication as Absolute

Do not publish these as unconditional claims until controls are demonstrated:

- "The Daanaa/EcoMargins firewall is enforced at the code level."
- "The firewall is audited quarterly" unless a dated audit log and owner exist.
- "We never share your data" without governed exceptions.
- "We never charge for the platform" without defining free core access versus optional services.
- "Every correction is publicly documented" without privacy-preserving correction policy.
- "AI is always disclosed" unless disclosure scope is defined and covered by tests.

## Founder Decisions Required

1. Define "platform" for the free-platform promise.
2. Approve the boundary between free core participation and optional paid capacity services.
3. Decide whether Charter vNext should use absolute "never" language with exceptions or narrower enforceable language.
4. Approve publication timing for code-enforced firewall claims.
5. Approve correction-log visibility and privacy limits.

