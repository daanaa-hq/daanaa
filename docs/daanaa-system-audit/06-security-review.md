# Security Review

## Confirmed controls

- Admin actions use an `X-Admin-Key` header compared with `hmac.compare_digest` in the full backend. Evidence: [`tests/test_principles.py`](/home/akbar/meritgiving/tests/test_principles.py).
- Wallet sync routes require Firebase auth, and the repo explicitly rejects server-side donation routes. Evidence: [`tests/test_principles.py`](/home/akbar/meritgiving/tests/test_principles.py).
- The droplet API sets CSP and HSTS headers. Evidence: [`scripts/droplet_api.py`](/home/akbar/meritgiving/scripts/droplet_api.py).
- Claim flow tests enforce required attestations and protect the PIN from being echoed back in email content. Evidence: [`tests/test_claim_flow.py`](/home/akbar/meritgiving/tests/test_claim_flow.py).

## High-risk or medium-risk gaps

| Finding | Severity | Confidence | Evidence |
|---|---|---|---|
| Multiple optional external services are imported or referenced without being consistently verified as active | Medium | Strong evidence | `sentry_sdk`, `boto3`, `twilio`, Firebase references in backend/front-end |
| The repo contains both full and droplet backends, which increases the chance of security-header drift and routing drift | High | Confirmed | Full vs droplet API split, plus historical lessons in `LESSONS.md` |
| Human review requirements exist in governance, but some AI-assisted enrichment paths are not obviously gated before public display | Medium | Probable | Mission generation, tag enrichment, context assembly scripts |
| Public copy and code comments can diverge from actual behavior if not checked against live endpoints or precompute output | Medium | Strong evidence | Multiple lessons in `LESSONS.md`, `CURRENT_STATE.md` |

## Privacy review

- Donor privacy is a protected principle in stewardship docs.
- The frontend includes a local wallet context and a privacy-sensitive account model.
- Analytics are described as first-party in the governance docs, but the repo still references Plausible, so the public/runtime distinction should be checked carefully before any claim is made.

