# Stewardship Audit (weekly, automated)

*Generated 2026-06-29 05:50 · Status: **3 ISSUE(S) — FIX BEFORE SHIPPING***

| Principle | Check | Result | Count |
|-----------|-------|--------|-------|
| P3 | scores outside 0-100 | ✅ PASS | 0 |
| P3 | low-confidence links marked verified (conf<90 but status ok) | ✅ PASS | 0 |
| P4 | hidden gems violating published definition | ❌ FAIL | 2,026 |
| P8 | revoked orgs with live donate links | ❌ FAIL | 148 |
| P9 | agent runs logged in last 7 days (expect > 0) | ❌ FAIL | 0 |

Failing checks map to STEWARDSHIP.md principles. Correct the data, then
document the fix (principle 6: mistakes corrected openly).

*Regenerate: `python3 scripts/agents/stewardship_audit.py`*
