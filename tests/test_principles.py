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
API     = ROOT / "daanaa_api.py"
SCRIPTS = ROOT / "scripts"
FE_SRC  = ROOT / "frontend" / "src"
LOGS    = ROOT / "logs"


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
def test_wallet_routes_require_firebase_auth():
    """Wallet sync routes (opt-in cross-device) must be gated by Firebase auth.
    Wallet data is never exposed without explicit user authentication (P2).
    No giving/donation routes may exist — those stay in localStorage only.
    """
    src = _api_src()
    wallet_routes = _grep(r"@app\.route\(['\"].*wallet.*['\"]", src)
    # Wallet routes exist for optional cross-device sync; that's allowed by P2.
    # Every handler MUST call _require_firebase_user() before touching any data.
    if wallet_routes:
        firebase_guards = len(re.findall(r"_require_firebase_user\(\)", src))
        assert firebase_guards >= len(wallet_routes), (
            f"P2 violation: {len(wallet_routes)} wallet routes but only "
            f"{firebase_guards} Firebase auth guards — some routes are unprotected"
        )
        assert "_require_firebase_user" in src, (
            "P2 violation: _require_firebase_user missing — wallet routes unprotected"
        )
    # Giving/donation routes must never exist server-side
    giving_routes = _grep(r"@app\.route\(['\"].*giving.*['\"]", src)
    assert not giving_routes, f"P2 violation: giving route on server: {giving_routes}"


@pytest.mark.principle
def test_csp_header_present():
    """Content-Security-Policy header is set in set_security_headers."""
    src = _api_src()
    assert "Content-Security-Policy" in src, (
        "P2 violation: CSP header missing from set_security_headers"
    )
    assert "script-src" in src, "P2 violation: CSP missing script-src directive"


@pytest.mark.principle
def test_plausible_initializer_is_csp_compatible():
    """Plausible initialization must run without allowing arbitrary inline scripts."""
    index = (ROOT / "frontend" / "index.html").read_text()
    initializer = ROOT / "frontend" / "public" / "plausible-init.js"
    assert '<script src="/plausible-init.js?v=2"></script>' in index
    assert "plausible.init()" not in index
    assert initializer.exists()
    assert 'plausible.init({ endpoint: "https://plausible.io/api/event" })' in initializer.read_text()




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
    # Find the reserve aggregation block (variable was renamed reserve_stats → agg
    # in the merit_api → daanaa_api migration; anchor on the SQL itself)
    block = re.search(
        r"COUNT\(CASE WHEN months_of_reserve.*?(?:healthy|fetchone\(\))",
        src, re.DOTALL
    )
    assert block, "Could not find months_of_reserve aggregation in daanaa_api.py"
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


@pytest.mark.principle
def test_browse_excludes_revoked_orgs():
    """The catalog filter must exclude IRS-revoked orgs from browse/search.

    Donations to auto-revoked orgs are not tax-deductible. Listing them as
    normal 501(c)(3)s (with tier badges) violates P3. Rows stay in
    registry_enriched untouched — this is a display filter, reversible by
    removing the clause. (Audit 2026-06-09, Phase 3 finding #1.)
    """
    src = _api_src()
    # Match the assignment whether it's a single string or a parenthesized
    # multi-line concat; allows one level of nesting for COALESCE(...) calls.
    block = re.search(
        r"_DEDUCTIBILITY_FILTER\s*=\s*(?:\((?:[^()]|\([^()]*\))*\)|\"[^\"]*\")", src
    )
    assert block, "Could not find _DEDUCTIBILITY_FILTER in daanaa_api.py"
    f = block.group()
    assert "irs_revoked" in f, (
        "P3 violation: _DEDUCTIBILITY_FILTER does not exclude irs_revoked orgs — "
        "192K+ revoked orgs would appear in browse with tier badges"
    )
    assert "org_status" in f, (
        "P3 violation: _DEDUCTIBILITY_FILTER does not exclude org_status='revoked'"
    )


# ── P2/P7 — Auth hardening (audit 2026-06-09, Phase 1 findings 1–3) ──────────

@pytest.mark.principle
def test_no_research_passcode_machinery():
    """The research dashboard serves only aggregate public IRS data — the
    passcode/session gate was removed (2026-06-09). No passcode may reappear
    in backend or frontend source (the old one was hardcoded in both)."""
    src = _api_src()
    for token in ("daanaa2026", "RESEARCH_PASSCODE", "_check_research_auth"):
        assert token not in src, (
            f"P7 violation: research passcode machinery '{token}' reappeared in API — "
            "research data is public-aggregate; gate it only if PII is ever added"
        )
    fe_hits = [
        str(f.relative_to(ROOT))
        for f in FE_SRC.rglob("*.tsx")
        if "daanaa2026" in f.read_text() or "RESEARCH_PASSCODE" in f.read_text()
    ]
    assert not fe_hits, f"P7 violation: passcode constant in frontend: {fe_hits}"


@pytest.mark.principle
def test_claim_secret_fails_closed_in_prod():
    """In prod (DAANAA_PROD), the claim HMAC secret must never fall back to the
    dev default — forged claim-verify tokens otherwise."""
    src = _api_src()
    idx = src.find("_CLAIM_SECRET")
    assert idx != -1, "Could not find _CLAIM_SECRET"
    region = src[max(0, idx - 500):idx + 1200]
    assert "DAANAA_PROD" in region and "raise" in region, (
        "P7 violation: no prod guard on _CLAIM_SECRET — dev fallback "
        "'daanaa-dev-claim-secret' would be used in production"
    )


@pytest.mark.principle
def test_revocation_sync_updates_registry_column():
    """sync_irs_revocations.py must keep registry_enriched.irs_revoked in step
    with the revoked_eins list — the browse filter reads the COLUMN, so a list
    that updates without the column silently re-lists revoked orgs."""
    src = (SCRIPTS / "sync_irs_revocations.py").read_text()
    assert "UPDATE registry_enriched SET irs_revoked = 1" in src, (
        "P3 violation: revocation sync no longer updates the irs_revoked column"
    )
    # Shrink guard: never load a truncated IRS file over good data
    assert "0.8" in src and "RuntimeError" in src, (
        "P3 violation: revocation sync lost its file-shrink sanity gate"
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


# ── P2 — No donor PII in operational logs ─────────────────────────────────────

# Columns that would represent donor PII. The platform never stores donor
# identity or giving amounts server-side (wallet lives in localStorage), so
# log-generating scripts must never SELECT or print these.
_PII_TOKENS = [
    "donor_name", "donor_email", "donor_id",
    "gift_amount", "donation_amount", "card_", "ssn",
]
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


@pytest.mark.principle
def test_log_scripts_no_pii_columns():
    """Log-generating scripts must not query donor PII columns."""
    for script in ("morning_brief.py", "pipeline_check.py"):
        path = SCRIPTS / script
        if not path.exists():
            continue
        src = path.read_text().lower()
        for tok in _PII_TOKENS:
            assert tok not in src, (
                f"P2 violation: '{script}' references PII token '{tok}'. "
                "Operational logs must contain only aggregate, non-PII data."
            )


@pytest.mark.principle
def test_generated_logs_have_no_emails():
    """Any generated brief/status logs on disk must contain no email addresses.

    Donor email is never collected; a stray address in a log would signal a
    leak from some other surface. Allow the operator's own contact domains.
    """
    if not LOGS.exists():
        pytest.skip("no logs/ directory")
    allow_domains = ("daanaa.org", "ecomargins")
    offenders = []
    for f in list(LOGS.glob("morning_brief_*.md")) + list(LOGS.glob("pipeline_status.log")):
        try:
            text = f.read_text(errors="ignore")
        except OSError:
            continue
        for match in _EMAIL_RE.findall(text):
            if not any(d in match.lower() for d in allow_domains):
                offenders.append(f"{f.name}: {match}")
    assert not offenders, (
        f"P2 violation: email addresses found in operational logs: {offenders[:5]}"
    )
