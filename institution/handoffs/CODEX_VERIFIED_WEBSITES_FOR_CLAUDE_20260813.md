# Codex Verified Website Queue For Claude

**Date:** 2026-08-13  
**Prepared by:** Codex  
**Purpose:** Provide a clean EIN → website list that Claude can use for org-page enrichment.

## Summary

Codex fixed and ran `scripts/continuous_discovery/domain_guess_engine.py` in **staging-first mode**.

What changed:
- one best candidate per EIN
- no canonical website writes by default
- candidates stored in `website_discovery_candidates`
- stronger identity checks than the original script
- org-based metrics instead of misleading domain-only success rates

Validated sample run:
- `run_id`: `domain_guess_20260813T135439Z`
- `25` orgs processed
- `198` candidate domains checked
- `7` verified candidates
- `4` needs-review candidates
- `0` canonical writes
- `0` script errors

Larger staged run launched:
- `run_id`: `domain_guess_20260813T135802Z`
- `250` org staging batch in progress at handoff time
- no canonical writes enabled

## How Codex Verified These

Each `candidate_verified` row passed all of the following:
1. DNS resolution succeeded.
2. HTTP/HTTPS request reached a live site.
3. Page text contained nonprofit-relevant signals such as mission / donate / charity / foundation / volunteer language.
4. Org identity matched the site using domain + title/description/content comparison.
5. Candidate was selected as the single best result for that EIN.

Interpretation:
- `confidence 90`: strong identity match + strong nonprofit signals
- `confidence 80`: strong identity match + moderate nonprofit signals
- `confidence 65`: acceptable verified candidate, but thinner public text signal or slightly weaker text evidence

## Verified EIN → Website List

| EIN | Organization | Website | Verification basis |
|---|---|---|---|
| `001028397` | UNITY IN THE CITY | `https://unityinthecity.org/` | Strong identity match; 3 nonprofit signals found; staged as `candidate_verified` with confidence `90`. |
| `003140260` | PILGRIM BAPTIST CHURCH | `https://pilgrimbaptistchurch.org/` | Strong identity match; 3 nonprofit signals found; staged as `candidate_verified` with confidence `90`. |
| `000260049` | CORINTH BAPTIST CHURCH | `http://corinthbaptistchurch.org/` | Strong identity match; 2 nonprofit signals found; staged as `candidate_verified` with confidence `80`. |
| `000490336` | EASTSIDE BAPTIST CHURCH | `https://eastsidebaptistchurch.com/` | Strong identity match; 2 nonprofit signals found; staged as `candidate_verified` with confidence `80`. |
| `000029215` | ST GEORGE CATHEDRAL | `https://stgeorgecathedral.org/` | Strong identity match; 1 nonprofit signal found; staged as `candidate_verified` with confidence `65`. |
| `010018605` | AMALGAMATED TRANSIT UNION | `https://atu.org/` | Strong identity match; 1 nonprofit signal found; staged as `candidate_verified` with confidence `65`. |
| `000852649` | BETHANY PRESBYTERIAN CHURCH | `https://bethanychurch.com/` | Moderate identity match; 2 nonprofit signals found; staged as `candidate_verified` with confidence `65`. |

## Needs Review (Do Not Auto-Publish)

These are plausible but should be checked before any canonical promotion:

| EIN | Organization | Candidate URL | Why review |
|---|---|---|---|
| `000360268` | IGLESIA VICTORIA | `https://www.iglesiavictoria.com/` | Strong naming fit but lower overall confidence (`45`). |
| `000841363` | AGAPE HOUSE OF PRAYER | `https://agapehouseofprayer.com/` | Strong naming fit but lower overall confidence (`45`). |
| `007764840` | TRI-COUNTY LIGHTHOUSE BAPTIST CHURCH & MINISTRIES INC | `https://www.tcec.coop/` | Weak identity match; likely false positive. |
| `001689178` | SAFE HAVEN RESIDENTIAL SERVICES INC | `https://www.safeinc.com/` | Weak identity match; generic commercial collision risk. |

## Guidance For Claude

Safe use:
- Use the `Verified EIN → Website List` as the first candidate queue for org-page website enrichment.
- Keep `Needs Review` separate.
- Do not bulk-promote `candidate_needs_review`, `candidate_rejected`, or `dns_failed` rows.

Suggested next step:
- Read from `website_discovery_candidates` where `verification_status='candidate_verified'`
- Optionally cross-check against external sources like Candid / GuideStar or ProPublica before canonical promotion
- If promoting into org pages, preserve provenance: `website_source='domain_guess'` until separately confirmed
