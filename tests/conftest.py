import os, sqlite3, tempfile

# Load fixtures from fixtures.py for enrichment pipeline tests
pytest_plugins = ['tests.fixtures']

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
        street_address TEXT, cohort_context TEXT,
        program_expense_pct REAL, total_assets REAL, total_liabilities REAL,
        merit_score_v5 REAL, merit_archetype_v5 TEXT, merit_archetype_v5_label TEXT,
        merit_band_v5 TEXT, merit_band_v5_label TEXT, merit_health_signal_v5 TEXT,
        merit_peer_group_v5 TEXT, merit_peer_count_v5 INTEGER
    );
    -- Mirror the FULL production org_claims DDL (sqlite3 data/merit_registry.db
    -- '.schema org_claims'). A 4-column seed caused order-dependent failures:
    -- tests passed only when another file had already imported daanaa_api and
    -- its migrations ALTER-added the missing columns.
    CREATE TABLE IF NOT EXISTS org_claims (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        ein              TEXT NOT NULL UNIQUE,
        email            TEXT NOT NULL,
        irs_address      TEXT NOT NULL,
        pin              TEXT NOT NULL,
        pin_expires_at   TEXT NOT NULL,
        letter_sent_at   TEXT,
        lob_letter_id    TEXT,
        claim_status     TEXT DEFAULT 'pending',
        verified_at      TEXT,
        custom_mission   TEXT,
        custom_description TEXT,
        donate_confirmed INTEGER DEFAULT 0,
        processor_auth   INTEGER DEFAULT 0,
        created_at       TEXT DEFAULT CURRENT_TIMESTAMP,
        revoked_at       TEXT,
        revoke_reason    TEXT,
        phone TEXT, rep_title TEXT, attested_at TEXT, attestation_version TEXT,
        called_at TEXT, call_notes TEXT, rep_name TEXT, firebase_uid TEXT,
        contact_preference TEXT DEFAULT 'unified',
        volunteer_contact_name TEXT, volunteer_contact_email TEXT, volunteer_contact_phone TEXT,
        donor_contact_name TEXT, donor_contact_email TEXT, donor_contact_phone TEXT,
        website_url TEXT, nudge_sent_at TEXT, checkin_sent_at TEXT,
        profile_nudge_sent_at TEXT DEFAULT NULL,
        donate_url TEXT, cause_tags_json TEXT
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
    CREATE TABLE IF NOT EXISTS macro_context_snapshots (
        id INTEGER PRIMARY KEY,
        ein TEXT UNIQUE,
        filing_year INTEGER,
        cpi_year REAL,
        unemployment_rate REAL,
        gdp_growth REAL,
        interest_rate_federal REAL,
        population_change REAL,
        housing_price_index REAL,
        source TEXT DEFAULT 'fred',
        source_update_date TEXT,
        confidence TEXT DEFAULT 'high',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS knowledge_graph_entities (
        ein TEXT, entity_type TEXT, entity_value TEXT,
        confidence REAL, source TEXT
    );
    CREATE TABLE IF NOT EXISTS knowledge_graph_relationships (
        ein_from TEXT, relationship_type TEXT, ein_to TEXT, confidence REAL
    );
""")

# Run the real production migrations against the temp DB so the test schema can
# never drift from what daanaa_api._run_migrations() produces (statement-level
# tolerance mirrors its semantics: ALTERs for already-present columns are skipped).
import glob as _glob
_mig_dir = os.path.join(os.path.dirname(__file__), "..", "migrations")
for _mig in sorted(_glob.glob(os.path.join(_mig_dir, "*.sql"))):
    with open(_mig) as _f:
        for _stmt in _f.read().split(";"):
            _stmt = _stmt.strip()
            if _stmt:
                try:
                    _seed_conn.execute(_stmt)
                except sqlite3.OperationalError:
                    pass  # duplicate column/table from the base seed — fine
_seed_conn.commit()
_seed_conn.close()
