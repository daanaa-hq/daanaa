"""Search reliability regression tests.

This pins the schema-drift failure class that previously showed up in
logs/daanaa_api.log as `no such column: v4.peer_cell_size`. The current
backend search path should succeed against a minimal registry schema that has
no v4_scores table at all.
"""

from __future__ import annotations

import sqlite3

import pytest

import daanaa_api


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "search_reliability.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE registry_enriched (
            EIN TEXT PRIMARY KEY,
            organization_name TEXT,
            NTEE1 TEXT,
            CITY TEXT,
            STATE TEXT,
            total_revenue REAL,
            ntee1_percentile REAL,
            peer_percentile REAL,
            peer_group TEXT,
            revenue_band TEXT,
            latest_tax_year INTEGER,
            data_source TEXT,
            merit_tier TEXT,
            merit_score REAL,
            merit_band TEXT,
            months_of_reserve REAL,
            net_assets REAL,
            is_hidden_gem INTEGER,
            cause_tags TEXT,
            mission TEXT,
            mission_source TEXT,
            website TEXT,
            irs_revoked INTEGER DEFAULT 0,
            org_status TEXT DEFAULT 'active',
            subsection TEXT DEFAULT '3',
            deductibility TEXT DEFAULT '1'
        );
        CREATE VIRTUAL TABLE org_fts USING fts5(ein, organization_name, mission);
        INSERT INTO registry_enriched (
            EIN, organization_name, NTEE1, CITY, STATE, total_revenue,
            ntee1_percentile, peer_percentile, peer_group, revenue_band,
            latest_tax_year, data_source, merit_tier, merit_score, merit_band,
            months_of_reserve, net_assets, is_hidden_gem, cause_tags, mission,
            mission_source, website, irs_revoked, org_status, subsection,
            deductibility
        ) VALUES (
            '111000111', 'Food Bank Helpers', 'K', 'Austin', 'TX', 100000,
            91, 88, 'K|Micro', 'Micro', 2023, 'unit-test', 'Torch', 88,
            'Micro', 4, 20000, 0, '[]', 'Helps families with food',
            'ai_generated', 'https://example.org', 0, 'active', '3', '1'
        );
        INSERT INTO org_fts (ein, organization_name, mission) VALUES (
            '111000111', 'Food Bank Helpers', 'Helps families with food'
        );
        """
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(daanaa_api, 'DB_PATH', str(db_path))
    monkeypatch.setattr(daanaa_api, 'LIVE_DB_PATH', str(db_path))
    monkeypatch.setattr(daanaa_api, '_fts_available', None)
    monkeypatch.setattr(daanaa_api, '_emb_loaded', False)
    monkeypatch.setattr(daanaa_api, '_emb_matrix', None)
    monkeypatch.setattr(daanaa_api, '_emb_index', {})
    monkeypatch.setattr(daanaa_api, '_emb_eins', [])
    daanaa_api.app.config['TESTING'] = True
    with daanaa_api.app.test_client() as c:
        yield c


def test_search_succeeds_without_v4_scores_table(client):
    resp = client.get('/api/search?q=food+bank')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['mode'] == 'fused'
    assert body['total'] > 0
    assert body['results']
    assert body['results'][0]['EIN'] == '111000111'
