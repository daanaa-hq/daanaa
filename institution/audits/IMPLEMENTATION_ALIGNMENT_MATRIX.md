# Implementation Alignment Matrix

Date: 2026-07-13

Statuses: Enforced, Partially enforced, Documented only, Planned, Contradicted, Unknown.

| Promise / Principle | Relevant Code | Tests | Policies / Docs | Evidence | Status | Known Gap |
|---|---|---|---|---|---|---|
| No donation custody, merchant of record, or cut | `daanaa_api.py`, `scripts/droplet_api.py`, disabled receipt endpoint | `tests/test_no_public_donation_fields.py` | Charter, Terms, Stewardship | No payment processor custody flow found; receipt endpoint returns 410. | Partially enforced | Donation links/logs need single boundary policy. |
| Free public discovery | Search/browse endpoints, frontend directory | Search tests | Constitution, Charter, Terms | Directory browsing exists without account. | Enforced | Define "core tools" vs optional paid services. |
| Payment cannot influence score/ranking/visibility | Scoring/search code; vendor policy | Limited principle/search tests | Stewardship, Vendor Policy, Charter | No paid boost mechanism found in reviewed code. | Partially enforced | Needs relationship-to-outcome audit. |
| Context, not verdict | Methodology, V5 UI, Terms | Scoring/search tests | Constitution, Methodology | Strong copy and methodology. | Partially enforced | Visual hierarchy/sort labels still require review. |
| Public vs entrusted data distinction | `org_claims`, claim export/delete, library 011 | `tests/test_privacy_controls.py` | Data Classification, Privacy | Claim export/delete works in tests. | Partially enforced | Wallet and firewall controls need unification. |
| Tier 2 data not used for EcoMargins/marketing | No complete code gate found | No visible gate 8 test found | Library 011, Privacy Invariants, Charter | Policy is clear; machine check incomplete. | Documented only | Implement/test firewall gate. |
| AI disclosure for concierge | Concierge endpoint docstring | `tests/test_concierge_confirm.py` currently failing | Board resolution, library 004 | Disclosure language exists. | Partially enforced | Fix tests; add operator attestation if needed. |
| Nonprofit can export/delete entrusted claim data | `/api/claim/my-data`, `/delete` | `tests/test_privacy_controls.py` | Charter promise 9 | Tests passed in combined run before concierge failures. | Enforced for claims | Wallet/org-wide data scope needs matrix. |
| Donor privacy | Wallet local encryption/sync, privacy pages | Wallet/security tests exist, not fully run here | Stewardship, Privacy | Device-first + encrypted sync patterns. | Partially enforced | Documentation drift and backup path clarity. |
| Corrections are public and prompt | Mistake registry, feedback routes | Not fully traced here | Charter, Stewardship | Correction path exists in product docs/pages. | Partially enforced | Public correction ledger/SLA not evidenced. |
| Backup failures visible | `scripts/ops/daanaa_backup.sh` | `bash -n` | Succession, Risk Register | Script fails on missing rclone/remote/push/verification. | Partially enforced | Live offsite freshness unverified. |
| Charter changes logged and announced | Charter revision text | None found | Charter | Commitment exists. | Documented only | Amendment workflow needed. |
| Institutional memory recoverable | `institution/`, git, succession docs | Weekly review script | Succession, Current State | Strong docs. | Partially enforced | Hidden AI/gstack memory not fully migrated. |

