import os, sqlite3, tempfile

# Skip the ~2GB embedding load — tests never need the vector matrix.
os.environ.setdefault("DAANAA_SKIP_EMBEDDINGS", "1")

# Use a temp file DB so tests never touch the live DB (and work even when it's locked).
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ.setdefault("DB_PATH", _tmp_db.name)
os.environ.setdefault("LIVE_DB_PATH", _tmp_db.name)

# Seed the minimal schema so endpoint tests don't crash on missing tables.
# Zero rows is fine — the tests assert that donation fields are ABSENT from
# responses; an empty list is a valid (and correct) empty response.
_seed_conn = sqlite3.connect(_tmp_db.name)
_seed_conn.executescript("""
    CREATE TABLE IF NOT EXISTS registry_enriched (
        EIN TEXT PRIMARY KEY,
        organization_name TEXT, NTEE1 TEXT, NTEECC TEXT, CITY TEXT, STATE TEXT,
        total_revenue REAL, ntee1_percentile REAL, ntee1_total_orgs INTEGER,
        source TEXT, latest_tax_year INTEGER, data_source TEXT, updated_at TEXT,
        revenue_band TEXT, peer_percentile REAL, peer_rank INTEGER,
        peer_total INTEGER, peer_group TEXT,
        merit_tier TEXT, merit_score REAL, merit_band TEXT,
        months_of_reserve REAL, net_assets REAL, total_expenses REAL,
        employee_count INTEGER, ruling_date TEXT, zipcode TEXT,
        is_hidden_gem INTEGER DEFAULT 0, cause_tags TEXT,
        website TEXT, website_status TEXT,
        mission TEXT, mission_source TEXT,
        irs_revoked INTEGER DEFAULT 0,
        org_status TEXT DEFAULT 'active',
        subsection TEXT DEFAULT '3',
        deductibility TEXT DEFAULT '1',
        donate_url TEXT, donate_platform TEXT, donate_url_status TEXT,
        donate_confidence REAL, donate_source_page TEXT,
        donate_identity_match INTEGER, donate_human_review INTEGER,
        donate_checked_at TEXT,
        street_address TEXT, cohort_context TEXT
    );
    CREATE TABLE IF NOT EXISTS org_claims (
        ein TEXT PRIMARY KEY,
        claim_status TEXT,
        verified_at TEXT,
        firebase_uid TEXT
    );
    CREATE TABLE IF NOT EXISTS wallet_sync (
        firebase_uid TEXT PRIMARY KEY,
        donations_json TEXT,
        volunteer_json TEXT,
        updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS research_lamp_tier_summary (
        merit_tier TEXT, count INTEGER, pct_of_total REAL,
        avg_revenue REAL, avg_financial_health_score REAL,
        pct_with_website REAL, avg_peer_percentile REAL, period TEXT
    );
""")
_seed_conn.close()
