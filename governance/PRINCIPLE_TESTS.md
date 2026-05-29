# Principle Tests — Daanaa

Each row maps a stewardship principle to its invariant and the test that enforces it.
A failing test blocks deploy. Run with: `pytest tests/test_principles.py -v`

| Principle | Invariant | Test |
|-----------|-----------|------|
| P1 — Verified paths only | No route routes donors to unverified giving paths; donate_url is gated on link-health | `test_no_google_search_fallback`, `test_donate_url_gated` |
| P2 — Donor privacy | Wallet writes never hit the server; CSP header blocks XSS exfiltration | `test_no_wallet_write_route`, `test_csp_header_present` |
| P3 — Honest representation | /api/stats reserve buckets exclude sentinel values (-999); claim status is honest | `test_no_sentinel_in_stats_sql`, `test_claim_status_honest` |
| P6 — Corrections path | Feedback/corrections endpoint exists and persists to DB | `test_link_feedback_route_exists` |
| P7 — Independence | Admin key compare is constant-time; no paid_placement/sponsored field affects ordering | `test_admin_key_constant_time`, `test_no_paid_placement` |
| P8 — Never touch money | No route accepts currency amount, payment token, or processor webhook; no payment SDK imported | `test_no_payment_routes`, `test_no_payment_sdk` |
| P9 — Reconstructability | org_claims table is auto-created at startup; DB schema reconstructable from code | `test_org_claims_auto_created` |

## How to add a new test

1. Identify the principle and invariant.
2. Write a pytest function in `tests/test_principles.py`.
3. Add a row to this table.
4. Mark it `@pytest.mark.principle` so it runs in the gate check.

## Running in CI / pre-deploy

```bash
pytest tests/test_principles.py -v -m principle
```

A non-zero exit code blocks the deploy.
