"""
Contract drift guard + donor-facing terminology lint.

Board decision 2026-07-17 (docs/BOARD_SIMULATION_2026_07_17_EVENING.md):

1. Contract guard — the full backend (daanaa_api.py) and the production edge
   (scripts/droplet_api.py) share a public API surface. Drift between them
   caused the 2026-07-05 outage class and the 2026-07-17 wrong-endpoint
   verification error. These tests assert the shared surface stays aligned
   at the source level (no servers needed, so they run in any environment).

2. Terminology lint — donor-facing strings must not use the
   LANGUAGE_AND_MINDSET.md avoid-list (rank/grade/failing/at-risk framing).

Run: pytest tests/test_contract_and_terminology.py -v
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
FULL_API = REPO / "daanaa_api.py"
EDGE_API = REPO / "scripts" / "droplet_api.py"
FRONTEND_SRC = REPO / "frontend" / "src"

ROUTE_RE = re.compile(r"@app\.route\(\s*['\"]([^'\"]+)['\"]")


def routes_of(path: Path) -> set[str]:
    return set(ROUTE_RE.findall(path.read_text()))


# ── Contract guard ──────────────────────────────────────────────────────────

# The donor-facing surface both backends MUST serve identically-shaped.
# Grow this list when a new shared endpoint ships; a route listed here that
# is missing from either backend is a contract break.
SHARED_SURFACE = [
    "/health",
    "/api/stats",
    "/api/organizations",
    "/api/organizations/<ein>",
    "/api/organizations/<ein>/similar",
    "/api/organizations/<ein>/financials",
]


@pytest.mark.principle
def test_shared_surface_present_in_both_backends():
    full, edge = routes_of(FULL_API), routes_of(EDGE_API)
    missing_full = [r for r in SHARED_SURFACE if r not in full]
    missing_edge = [r for r in SHARED_SURFACE if r not in edge]
    assert not missing_full, f"daanaa_api.py lost shared routes: {missing_full}"
    assert not missing_edge, f"droplet_api.py lost shared routes: {missing_edge}"


@pytest.mark.principle
def test_org_detail_route_is_organizations_not_org():
    """The 2026-07-17 verification error: /api/org/<ein> does not exist as a
    detail endpoint on either backend — the real route is /api/organizations/
    <ein>. Guard that neither backend grows a bare /api/org/<ein> lookalike
    (subroutes like /api/org/<ein>/volunteer-events are fine)."""
    for path in (FULL_API, EDGE_API):
        assert "/api/org/<ein>" not in routes_of(path), (
            f"{path.name} defines bare /api/org/<ein> — the canonical detail "
            "route is /api/organizations/<ein>; a lookalike invites drift")


@pytest.mark.principle
def test_edge_serves_no_sqlite_registry_writes():
    """The edge serves precompute; it must never write registry_enriched
    (2026-06-06 corruption class)."""
    src = EDGE_API.read_text()
    writes = re.findall(
        r"(?:UPDATE|INSERT INTO|DELETE FROM)\s+registry_enriched", src, re.I)
    # Known exception: none today. Any appearance is a review flag.
    assert not writes, (
        "droplet_api.py contains registry_enriched write statements — the "
        f"edge must stay read-only over precompute: {writes[:3]}")


# ── Terminology lint (donor-facing strings) ────────────────────────────────

# LANGUAGE_AND_MINDSET.md avoid-list, as patterns over JSX string literals.
# Matched only inside quoted strings/JSX text to avoid flagging identifiers.
AVOID = [
    (re.compile(r"top[- ]rated", re.I), "top-rated (implies contest)"),
    (re.compile(r"\bF[- ]rated\b"), "F-rated (failure framing)"),
    (re.compile(r"\bfailing (?:org|charit|nonprofit)", re.I), "failing-org framing"),
    (re.compile(r"\bat[- ]risk (?:org|charit|nonprofit)", re.I), "at-risk framing"),
    (re.compile(r"give wisely", re.I), 'give wisely (vetting frame — use "give with heart")'),
    (re.compile(r"\bwatchdog\b", re.I), "watchdog framing"),
    (re.compile(r"\bpoorly run\b", re.I), "shame framing"),
]

# Files that legitimately discuss avoided terms (methodology explains what we
# DON'T do; tests and this lint itself).
LINT_EXEMPT = {"Methodology.tsx", "Approach.tsx", "Charter.tsx", "Governance.tsx"}


@pytest.mark.principle
def test_donor_facing_copy_respects_avoid_list():
    violations = []
    for tsx in FRONTEND_SRC.rglob("*.tsx"):
        if tsx.name in LINT_EXEMPT:
            continue
        text = tsx.read_text()
        for pattern, label in AVOID:
            for m in pattern.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                violations.append(f"{tsx.relative_to(REPO)}:{line_no} — {label}")
    assert not violations, (
        "Donor-facing copy uses avoided language (LANGUAGE_AND_MINDSET.md):\n"
        + "\n".join(violations[:10]))


@pytest.mark.principle
def test_no_tier_vocabulary_returns_to_donor_directory():
    """Tiers were retired from donor-facing surfaces 2026-07-17 (founder +
    board). Guard the two highest-traffic pages against reintroduction."""
    for page in ("pages/Directory.tsx", "pages/OrganizationDetail.tsx"):
        text = (FRONTEND_SRC / page).read_text()
        assert "Any visibility" not in text, f"{page}: tier filter returned"
        assert "Fully documented" not in text, f"{page}: tier subtitle returned"
