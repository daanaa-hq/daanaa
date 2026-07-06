"""Regression test for the MacroContextCard crash: the /recall endpoint's
macro_context object omitted interest_rate_federal entirely (present in the
DB, present in the sibling get_macro_context endpoint, missing only here).
Frontend guards checked `!== null`, which is true for a missing key
(undefined), so the stat tile rendered and .toFixed() crashed the page.
100% of orgs with a macro_context_snapshots row hit this — confirmed via
1,000 real rows in the live registry (2026-07-06).
"""
import os
import sqlite3

os.environ.setdefault("DAANAA_SKIP_EMBEDDINGS", "1")

import pytest

import daanaa_api


@pytest.fixture
def client():
    daanaa_api.app.config["TESTING"] = True
    with daanaa_api.app.test_client() as c:
        yield c


@pytest.fixture
def org_with_macro_context():
    ein = "123456789"
    conn = sqlite3.connect(os.environ["DB_PATH"])
    conn.execute(
        "INSERT OR REPLACE INTO registry_enriched (EIN, organization_name, NTEE1, NTEECC, CITY, STATE) "
        "VALUES (?, 'Test Org', 'P', 'P20', 'Testville', 'CA')",
        (ein,),
    )
    conn.execute(
        "INSERT OR REPLACE INTO macro_context_snapshots "
        "(ein, filing_year, cpi_year, unemployment_rate, gdp_growth, interest_rate_federal) "
        "VALUES (?, 2023, 310.0, 3.9, 2.5, 4.25)",
        (ein,),
    )
    conn.commit()
    conn.close()
    return ein


def test_recall_macro_context_includes_interest_rate(client, org_with_macro_context):
    resp = client.get(f"/api/organizations/{org_with_macro_context}/recall")
    assert resp.status_code == 200
    macro_context = resp.get_json()["macro_context"]
    assert macro_context is not None
    assert "interest_rate_federal" in macro_context, (
        "macro_context is missing interest_rate_federal — the frontend's "
        "!== null guard passes for a missing key (undefined), then "
        "context.interest_rate_federal.toFixed(2) crashes the whole org page"
    )
    assert macro_context["interest_rate_federal"] == 4.25
