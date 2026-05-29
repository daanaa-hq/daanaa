"""
Principle tests — Daanaa stewardship invariants.

These are static-analysis tests (grep / AST checks on source files) that run
without a live API. They catch regressions that would violate the Founding
Stewardship Commitment before code reaches production.

Run: pytest tests/test_principles.py -v
A failing test here BLOCKS DEPLOY.
"""
import re
import pytest
from pathlib import Path

ROOT    = Path(__file__).parent.parent
API     = ROOT / "merit_api.py"
SCRIPTS = ROOT / "scripts"
FE_SRC  = ROOT / "frontend" / "src"


def _api_src() -> str:
    return API.read_text()


def _grep(pattern: str, text: str) -> list[str]:
    return re.findall(pattern, text, re.IGNORECASE)


# ── P8 — Never touch money ────────────────────────────────────────────────────

@pytest.mark.principle
def test_no_payment_sdk():
    """No payment SDK may be imported in the API."""
    banned = ["stripe", "braintree", "paypal", "square", "plaid", "dwolla"]
    src = _api_src()
    for lib in banned:
        hits = _grep(rf"import\s+{lib}|from\s+{lib}\s", src)
        assert not hits, f"P8 violation: payment SDK '{lib}' imported in merit_api.py"


@pytest.mark.principle
def test_no_payment_routes():
    """No route accepts currency amounts, payment tokens, or processor webhooks."""
    src = _api_src()
    banned_params = ["card_token", "payment_method", "processor_token", "stripe_token",
                     "amount_cents", "charge_id", "webhook_secret"]
    for param in banned_params:
        assert param not in src, (
            f"P8 violation: payment parameter '{param}' found in merit_api.py"
        )
    # No webhook endpoint
    webhook_routes = _grep(r"@app\.route\(['\"].*webhook.*['\"]", src)
    assert not webhook_routes, f"P8 violation: webhook route found: {webhook_routes}"


# ── P2 — Donor privacy ────────────────────────────────────────────────────────

@pytest.mark.principle
def test_no_wallet_write_route():
    """No API route writes wallet/giving data — wallet is localStorage-only."""
    src = _api_src()
    wallet_routes = _grep(r"@app\.route\(['\"].*wallet.*['\"]", src)
    giving_routes = _grep(r"@app\.route\(['\"].*giving.*['\"]", src)
    assert not wallet_routes, f"P2 violation: wallet route on server: {wallet_routes}"
    assert not giving_routes, f"P2 violation: giving route on server: {giving_routes}"


@pytest.mark.principle
def test_csp_header_present():
    """Content-Security-Policy header is set in set_security_headers."""
    src = _api_src()
    assert "Content-Security-Policy" in src, (
        "P2 violation: CSP header missing from set_security_headers"
    )
    assert "script-src" in src, "P2 violation: CSP missing script-src directive"


# ── P1 / P7 — Verified paths, independence ───────────────────────────────────

@pytest.mark.principle
def test_no_google_search_fallback():
    """No frontend file routes donors to Google search for giving."""
    hits = []
    for f in FE_SRC.rglob("*.tsx"):
        text = f.read_text()
        if "google.com/search" in text and "donate" in text.lower():
            hits.append(str(f.relative_to(ROOT)))
    assert not hits, (
        f"P1 violation: Google search donate fallback found in: {hits}"
    )


@pytest.mark.principle
def test_no_paid_placement():
    """No paid_placement, sponsored, or featured field may affect org ordering."""
    src = _api_src()
    banned = ["paid_placement", "sponsored_rank", "featured_boost", "promoted"]
    for field in banned:
        assert field not in src, (
            f"P7 violation: '{field}' found in merit_api.py — "
            "this field must never influence ordering or scores"
        )


@pytest.mark.principle
def test_admin_key_constant_time():
    """Admin key comparison must use hmac.compare_digest (timing-safe)."""
    src = _api_src()
    assert "hmac.compare_digest" in src, (
        "P7 violation: admin key compare must use hmac.compare_digest"
    )
    # Must NOT use plain equality on the admin key
    plain_compare = re.findall(r'provided\s*[!=]=\s*_ADMIN_KEY', src)
    assert not plain_compare, (
        f"P7 violation: plain equality compare on _ADMIN_KEY: {plain_compare}"
    )


# ── P3 — Honest representation ────────────────────────────────────────────────

@pytest.mark.principle
def test_no_sentinel_in_stats_sql():
    """The /api/stats reserve SQL must exclude -999 sentinel values."""
    src = _api_src()
    # Find the reserve_stats query block
    block = re.search(
        r"reserve_stats\s*=\s*db\.execute\(.*?fetchone\(\)",
        src, re.DOTALL
    )
    assert block, "Could not find reserve_stats query in merit_api.py"
    query = block.group()
    # Must use BETWEEN or explicit bound, not open-ended < 0
    assert "BETWEEN" in query or "> -" in query, (
        "P3 violation: reserve_stats query may include -999 sentinel values. "
        "Use BETWEEN -120 AND 120 or equivalent bounds."
    )


@pytest.mark.principle
def test_claim_status_honest():
    """claim_start must not return 'letter_sent' when only logging locally."""
    src = _api_src()
    # Must check letter_id prefix before setting status
    assert "log:" in src, (
        "P3 violation: claim_start does not distinguish log-only from letter_sent status"
    )
    # The final return must use a variable, not a hardcoded 'letter_sent'
    bad = re.findall(r'return jsonify\(\{"status":\s*"letter_sent"', src)
    assert not bad, (
        f"P3 violation: claim_start hardcodes 'letter_sent' status — "
        "use a variable that reflects actual delivery mode"
    )


# ── P6 — Corrections path ────────────────────────────────────────────────────

@pytest.mark.principle
def test_link_feedback_route_exists():
    """A corrections/feedback endpoint must exist and write to the DB."""
    src = _api_src()
    assert "/api/link-feedback" in src, (
        "P6 violation: corrections endpoint /api/link-feedback not found in merit_api.py"
    )
    assert "INSERT INTO link_feedback" in src, (
        "P6 violation: link-feedback route does not persist to DB"
    )


# ── P9 — Reconstructability ──────────────────────────────────────────────────

@pytest.mark.principle
def test_org_claims_auto_created():
    """org_claims table must be created at module load, not hand-applied."""
    src = _api_src()
    assert "_init_org_claims_table" in src, (
        "P9 violation: org_claims table is not auto-created at startup. "
        "A fresh clone will crash on the first claim attempt."
    )
    assert "_init_org_claims_table()" in src, (
        "P9 violation: _init_org_claims_table is defined but never called at startup"
    )


@pytest.mark.principle
def test_overnight_pipeline_db():
    """overnight_pipeline.py must target merit_registry.db, not the legacy DB."""
    pipeline = (SCRIPTS / "overnight_pipeline.py").read_text()
    assert "meritgiving.db" not in pipeline, (
        "P9 violation: overnight_pipeline.py still points at legacy meritgiving.db. "
        "Overnight enrichment writes to a dead database."
    )
    assert "merit_registry.db" in pipeline, (
        "P9 violation: overnight_pipeline.py does not reference merit_registry.db"
    )
