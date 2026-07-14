# Technical Debt By Mission Impact

Date: 2026-07-13

## Highest Mission-Impact Technical Debt

| Priority | Debt | Mission Impact | Evidence | Recommended Next Step |
|---:|---|---|---|---|
| 1 | Tier 2 firewall gate incomplete relative to public claim. | Trust and commercial independence. | `privacy_check.sh` vs charter/library 011. | Implement/test gate or revise wording. |
| 2 | Wallet data-flow documentation drift. | Donor privacy and truthful consent. | Privacy pages, invariants, wallet code. | Create single wallet data-flow spec. |
| 3 | Concierge test/schema drift. | AI-assisted nonprofit onboarding trust. | Targeted pytest failures. | Repair fixture or writer behavior. |
| 4 | Donation boundary policy missing. | Legal/stewardship clarity. | Donation links/logs/receipt-disabled paths. | Draft policy before more donation-adjacent work. |
| 5 | Historical docs lack status labels. | Institutional memory and successor safety. | `docs/`, hidden state, old snapshots. | Classify high-risk docs. |
| 6 | Production edge vs full API contract complexity. | Reliability of public discovery. | `LESSONS.md`, `scripts/droplet_api.py`, tests. | Continue contract tests for both APIs. |
| 7 | Provider-console state unknown. | Continuity and recovery. | `state.json`, `RISK_REGISTER.md`. | Founder/admin access review. |

## Do Not Treat As Ordinary Cleanup

The items above are mission debt, not aesthetic debt. They affect whether public promises are true, whether nonprofits are treated fairly, and whether Daanaa can survive beyond the current operator.

