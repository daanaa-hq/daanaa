# Information Provenance Review

Date: 2026-07-13

## Provenance Classes Found

| Class | Examples | Current Handling |
|---|---|---|
| Public record | IRS BMF, Form 990, ProPublica, NCCS, revocation data. | Generally labeled in methodology/legal/research. |
| Nonprofit-provided | Claimed mission, website, contacts, dashboard inputs. | Stored in `org_claims`; export/delete controls exist for claims. |
| Independently verified | Claim status, verified/active claims, some website/donate statuses. | Present but terminology varies. |
| Calculated context | Peer Financial Context, health signals, percentiles, revenue bands. | Methodology explains; UI still needs ongoing verdict-risk review. |
| Estimated/inferred | AI missions, cause tags, website discovery, embeddings. | Some labels exist; not uniform across all surfaces. |
| Human-authored interpretation | Vision, methodology, pages, guides. | Generally source-separated but not always status-labeled. |
| Unverified/unknown | Missing data, stale filings, incomplete profiles. | Often acknowledged; should remain visible. |

## Strengths

- Library 011 clearly separates Tier 0 public record, Tier 1 published derivation, and Tier 2 entrusted data.
- Terms and methodology explain that Daanaa is not a rating agency or auditor.
- Concierge endpoint records source, call SID, attestation version, and operator note.
- Claim export/delete endpoints distinguish entrusted data from public record.

## Gaps

- Mission/source labels are not uniformly audited across every frontend surface.
- Public charter says code enforces the entity firewall, but visible privacy gate is incomplete.
- Historical docs can confuse old donation-link or wallet assumptions with current policy.
- The same field can exist in different tiers depending on source; implementation needs durable source-level tracing for commercial use review.

## Recommendation

Adopt a provenance display standard for every user-facing claim:

Public record; nonprofit-provided; Daanaa calculated; AI-assisted; verified by Daanaa; unverified; unknown.

Every material public claim should have a visible source, freshness date, and correction path.

