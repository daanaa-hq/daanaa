"""G2 / official-sources donate-eligibility gate.

These guard the money path: Daanaa must NEVER present a donate path for a
non-deductible, non-501(c)(3), or IRS-auto-revoked org. Fail closed.
"""

import sqlite3
import pytest

from daanaa_api import _donate_eligible_basic, _is_revoked


# --- basic gate (subsection + deductibility), no DB ---

def test_deductible_501c3_is_eligible():
    eligible, reason = _donate_eligible_basic(subsection="3", deductibility="1")
    assert eligible is True
    assert reason is None


def test_unknown_deductibility_501c3_is_eligible():
    # deductibility 0 (unknown) / 4 (by treaty) stay eligible — only explicit
    # non-deductible (2) is excluded.
    assert _donate_eligible_basic("3", "0")[0] is True
    assert _donate_eligible_basic("3", "4")[0] is True


def test_non_deductible_is_blocked():
    eligible, reason = _donate_eligible_basic(subsection="3", deductibility="2")
    assert eligible is False
    assert reason == "not_tax_deductible"


def test_non_501c3_is_blocked():
    # c4, c6, etc. — not a tax-deductible public charity
    eligible, reason = _donate_eligible_basic(subsection="4", deductibility="1")
    assert eligible is False
    assert reason == "not_501c3"


def test_null_subsection_is_blocked():
    # NCCS-only / unverifiable orgs fail closed
    assert _donate_eligible_basic(None, "1")[0] is False
    assert _donate_eligible_basic("", "1")[0] is False


# --- revocation gate (DB-backed) ---

@pytest.fixture
def db_with_revoked():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE revoked_eins (ein TEXT PRIMARY KEY)")
    db.execute("INSERT INTO revoked_eins (ein) VALUES ('123456789')")
    db.commit()
    return db


def test_revoked_ein_is_flagged(db_with_revoked):
    assert _is_revoked(db_with_revoked, "12-3456789") is True   # formatting stripped
    assert _is_revoked(db_with_revoked, "123456789") is True


def test_non_revoked_ein_is_clean(db_with_revoked):
    assert _is_revoked(db_with_revoked, "999888777") is False


def test_blank_ein_is_not_revoked(db_with_revoked):
    assert _is_revoked(db_with_revoked, "") is False
    assert _is_revoked(db_with_revoked, None) is False


def test_missing_table_fails_open_on_revocation_only():
    # If the revoked_eins table is absent, the revocation check must not crash —
    # it returns False (the basic deductibility gate still protects the path).
    empty = sqlite3.connect(":memory:")
    assert _is_revoked(empty, "123456789") is False
