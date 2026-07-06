"""Task 2: Test fixtures for enrichment pipeline.

Provides mocks for:
- Qwen LLM responses
- mxbai-embed-large embeddings (1024-dim vectors)
- In-memory SQLite database with enrichment schema
- Sample organization data for testing
"""

import sqlite3
import random
import string
import pytest


@pytest.fixture
def mock_qwen():
    """Return a function that simulates Qwen responses for testing.

    In real use, this connects to llama-server on port 11437.
    For testing, it returns deterministic, safe responses.
    """
    def _qwen_response(prompt: str, seed: int = 42) -> str:
        """Simulate Qwen response based on prompt content.

        Args:
            prompt: Input prompt (unused for deterministic output)
            seed: Random seed for reproducibility

        Returns:
            A string simulating Qwen's response (e.g., cause tags or website suggestion)
        """
        random.seed(seed)

        # Simulate different response types based on prompt keywords
        if "cause_tags" in prompt.lower() or "tags" in prompt.lower():
            tags = ["Community Development", "Education", "Health Services", "Arts & Culture", "Environment"]
            selected = random.sample(tags, k=random.randint(2, 4))
            return f"Recommended cause tags: {', '.join(selected)}. Confidence: 0.78"

        elif "website" in prompt.lower() or "domain" in prompt.lower():
            extensions = [".org", ".com", ".net"]
            org_name = "testorg"
            ext = random.choice(extensions)
            return f"Suggested domain: {org_name}{ext}. This follows nonprofit naming conventions. Confidence: 0.82"

        else:
            # Generic response for other prompts
            return f"Mock response from Qwen. Confidence: 0.75"

    return _qwen_response


@pytest.fixture
def mock_embeddings():
    """Return a function that generates test embedding vectors.

    mxbai-embed-large produces 1024-dimensional vectors.
    For testing, we generate deterministic vectors using seeded randomness.
    """
    def _embedding_response(text: str, seed: int = 42) -> list:
        """Generate a 1024-dimensional embedding vector for testing.

        Args:
            text: Input text to embed
            seed: Random seed for reproducibility (allows same text to produce same vector)

        Returns:
            List of 1024 floats (standard for mxbai-embed-large)
        """
        # Seed PRNG with text hash for determinism: same text → same vector
        hash_seed = seed + hash(text) % (2**31)
        random.seed(hash_seed)

        # Generate 1024 random floats in [-1, 1] range (typical for embeddings)
        # Real mxbai vectors are normalized and roughly in this range
        vector = [random.uniform(-1.0, 1.0) for _ in range(1024)]

        return vector

    return _embedding_response


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database with enrichment schema from Task 1.

    Includes:
    - enrichment_run table (stores tag/website generation results)
    - quality_log table (stores quality metrics)
    - Indexes for fast queries
    - Base tables from conftest (registry_enriched, org_claims, wallet_sync, etc.)

    Yields:
        sqlite3.Connection to in-memory database
    """
    con = sqlite3.connect(':memory:')
    cursor = con.cursor()

    # Base tables (from conftest.py)
    cursor.execute("""
        CREATE TABLE registry_enriched (
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
        )
    """)

    cursor.execute("""
        CREATE TABLE org_claims (
            ein TEXT PRIMARY KEY,
            claim_status TEXT,
            verified_at TEXT,
            firebase_uid TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE wallet_sync (
            firebase_uid TEXT PRIMARY KEY,
            donations_json TEXT,
            volunteer_json TEXT,
            updated_at TEXT
        )
    """)

    # Task 1 enrichment schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrichment_run (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date DATE NOT NULL,
            org_ein TEXT NOT NULL,
            enrichment_type TEXT NOT NULL CHECK(enrichment_type IN ('cause_tags', 'website')),
            generated_value TEXT NOT NULL,
            confidence_score REAL CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
            context_used TEXT,
            prompt_version TEXT NOT NULL DEFAULT 'v1.0',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(run_date, org_ein, enrichment_type)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            metric_type TEXT NOT NULL CHECK(metric_type IN ('cause_tag_accuracy', 'website_validity')),
            value REAL CHECK(value >= 0.0 AND value <= 1.0),
            cohort TEXT NOT NULL DEFAULT 'All',
            prompt_version TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, metric_type, cohort, prompt_version)
        )
    """)

    # Create indexes for fast queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_enrichment_date_ein
        ON enrichment_run(run_date, org_ein)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_quality_date_metric
        ON quality_log(date, metric_type, cohort)
    """)

    con.commit()

    yield con

    con.close()


@pytest.fixture
def sample_orgs():
    """Return sample organization data for testing.

    Provides realistic but minimal org records for integration testing.
    Each org includes EIN, name, NTEE category, mission, and location.

    Returns:
        List of dicts with org data ready to insert into test_db
    """
    return [
        {
            'ein': '611234567',
            'organization_name': 'Tech for Good Foundation',
            'ntee1': 'T',
            'nteecc': 'T20',
            'mission': 'Provides technology training to underserved communities',
            'city': 'San Francisco',
            'state': 'CA',
            'total_revenue': 450000.00,
            'ntee1_percentile': 65.0,
            'zipcode': '94102',
            'website': 'techforgood.org',
            'cause_tags': '["Technology", "Education", "Community Development"]',
            'merit_score': 72.5,
            'merit_tier': 'Torch'
        },
        {
            'ein': '621345678',
            'organization_name': 'Urban Animal Rescue',
            'ntee1': 'D',
            'nteecc': 'D31',
            'mission': 'Rescues and rehabilitates abandoned animals in urban areas',
            'city': 'Austin',
            'state': 'TX',
            'total_revenue': 125000.00,
            'ntee1_percentile': 58.0,
            'zipcode': '78701',
            'website': 'urbanrescue.org',
            'cause_tags': '["Animal Welfare", "Community Services"]',
            'merit_score': 68.0,
            'merit_tier': 'Candle'
        },
        {
            'ein': '631456789',
            'organization_name': 'Community Health Clinic Network',
            'ntee1': 'E',
            'nteecc': 'E20',
            'mission': 'Delivers affordable primary care to low-income families',
            'city': 'Chicago',
            'state': 'IL',
            'total_revenue': 2850000.00,
            'ntee1_percentile': 78.0,
            'zipcode': '60601',
            'website': 'healthclinic.org',
            'cause_tags': '["Health Services", "Community Development", "Advocacy"]',
            'merit_score': 81.5,
            'merit_tier': 'Beacon'
        },
        {
            'ein': '641567890',
            'organization_name': 'Rural Education Initiative',
            'ntee1': 'B',
            'nteecc': 'B40',
            'mission': 'Improves educational outcomes in rural communities',
            'city': 'Bozeman',
            'state': 'MT',
            'total_revenue': 185000.00,
            'ntee1_percentile': 52.0,
            'zipcode': '59715',
            'website': None,
            'cause_tags': '["Education", "Community Development"]',
            'merit_score': 64.0,
            'merit_tier': 'Spark'
        },
        {
            'ein': '651678901',
            'organization_name': 'Environmental Conservation Alliance',
            'ntee1': 'C',
            'nteecc': 'C20',
            'mission': 'Protects wetlands and wildlife habitats through advocacy',
            'city': 'Portland',
            'state': 'OR',
            'total_revenue': 320000.00,
            'ntee1_percentile': 61.0,
            'zipcode': '97204',
            'website': 'conservealliance.org',
            'cause_tags': '["Environment", "Advocacy"]',
            'merit_score': 70.5,
            'merit_tier': 'Candle'
        }
    ]
