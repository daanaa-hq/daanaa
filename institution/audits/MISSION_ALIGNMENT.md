# Mission Alignment Review

Date: 2026-07-13

## Mission Frame

Founder-provided mission shorthand: Make Giving Easy.  
Institutional mission in `institution/PURPOSE.md`: strengthen mission-driven organizations so they can create lasting benefit through responsible stewardship, transparency, wisdom, and continuous learning.

These are compatible. "Make Giving Easy" is the public and product expression. The purpose document gives the deeper institutional boundary: Daanaa exists to strengthen organizations and stewardship, not to maximize transactions.

## Alignment By Subsystem

| Subsystem | Mission Contribution | Burdens Or Risks | Current Evidence |
|---|---|---|---|
| Public directory | Helps donors and communities find active 501(c)(3)s, including smaller organizations. | Search/sort can become perceived ranking. | `frontend/src/pages/Directory.tsx`, `daanaa_api.py`, `scripts/droplet_api.py`, methodology pages. |
| Peer Financial Context | Adds context without claiming impact or worth. | Percentiles and health labels can still feel like verdicts. | `frontend/src/pages/Methodology2.tsx`, `frontend/src/components/V5Context.tsx`, scorer tests/docs. |
| Claim/profile tools | Let nonprofits correct and enhance their presence. | Burden if verification or editor is confusing; risk if AI draft is undisclosed. | claim endpoints, concierge endpoint, tests, charter. |
| Concierge | Reduces small-org administrative burden. | Must disclose AI/public-data draft and avoid pressure. | `daanaa_api.py` disclosure docstring, board resolution, failing tests needing schema alignment. |
| Giving Wallet | Helps people remember, plan, and record giving without Daanaa holding funds. | Donation logs become sensitive; privacy docs must be exact. | `WalletContext.tsx`, wallet APIs, privacy policy. |
| Volunteer tools | Converts generosity into participation. | Contact/age/preference data must be minimized. | volunteer components and endpoints. |
| Impact Network/Guild | Can reduce nonprofit operating costs and build capacity. | Vendor relationships create independence and endorsement risks. | `VENDOR-POLICY.md`, vendor pages/endpoints. |
| Research dashboard | Shares public-interest knowledge from public records. | Claims need freshness and source clarity. | `ResearchDashboard`, `research-snapshot.json`, research components. |
| Visibility overlay | Helps search engines and AI find Daanaa as a resource. | Static pages must avoid overclaiming or appearing as rankings. | `visibility/README.md`, generated overlay samples. |
| Institutional memory | Helps Daanaa survive beyond the founder. | Hidden local memory still needs migration/backporting. | `SUCCESSION.md`, `institution/`, `.gstack/`, `.claude/`. |

## Current Strengths

- Clear refusal to take custody or cut of donations.
- Strong public framing of context rather than verdict.
- Strong commitment to free core discovery.
- Explicit separation of public record, published derivation, and entrusted data.
- Existing tests for search reliability, privacy controls, donation-field exposure, and concierge semantics.
- Visibility work is mission-aligned when it points to public records and methodology rather than hype.

## Mission Risks

- Public promises may outrun controls, especially around Tier 2 firewall enforcement.
- Donation-adjacent features need a single boundary policy so wallet logs, donation links, and tax-letter concepts do not blur into fundraising.
- Financial sustainability language needs careful separation between free core participation and optional paid capacity services.
- Scored/sorted surfaces must keep reinforcing that context is not organizational worth.

## Recommendation

Use the Vision draft to make the mission simple: Daanaa makes giving easier by making trustworthy discovery easier, and it strengthens nonprofits by reducing administrative burden and transferring capacity. Use the Constitution to protect the boundaries that make that mission trustworthy.

