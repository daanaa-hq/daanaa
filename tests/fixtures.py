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
import hashlib
import pytest


def _stable_seed(text: str) -> int:
    """Derive a stable PRNG seed from text, independent of PYTHONHASHSEED.

    Python's built-in hash() for strings is salted per-process unless
    PYTHONHASHSEED is pinned, which breaks "same input -> same output"
    determinism across process runs (and thus across test invocations).
    SHA-256 has no such salting, so this is stable everywhere.
    """
    return int(hashlib.sha256(text.encode()).hexdigest(), 16) % (2**31)


@pytest.fixture
def mock_qwen():
    """Return a function that simulates Qwen responses for testing.

    In real use, this connects to llama-server on port 11437.
    For testing, it returns deterministic, safe responses.
    """
    def _qwen_response(prompt: str, max_tokens: int = 200) -> str:
        """Simulate Qwen response based on prompt content.

        Args:
            prompt: Input prompt. Determinism is derived from a hash of the
                prompt text itself, so identical prompts always yield the
                same response without requiring callers to pass a seed.
            max_tokens: Accepted for call-signature compatibility with the
                real Qwen client (unused for deterministic mock output).

        Returns:
            A string simulating Qwen's response (e.g., cause tags or website suggestion)
        """
        # Local PRNG seeded from a stable hash of the prompt: same prompt ->
        # same output, without touching the shared module-level random state
        # and without depending on PYTHONHASHSEED (see _stable_seed).
        rng = random.Random(_stable_seed(prompt))

        # Simulate different response types based on prompt keywords
        if "cause_tags" in prompt.lower() or "tags" in prompt.lower():
            tags = ["Community Development", "Education", "Health Services", "Arts & Culture", "Environment"]
            selected = rng.sample(tags, k=rng.randint(2, 4))
            return ', '.join(selected)

        elif "website" in prompt.lower() or "domain" in prompt.lower():
            extensions = [".org", ".com", ".net"]
            org_name = "testorg"
            ext = rng.choice(extensions)
            return f"{org_name}{ext}"

        else:
            # Generic response for other prompts
            return "Mock response from Qwen"

    return _qwen_response


@pytest.fixture
def mock_embeddings():
    """Return a function that generates test embedding vectors.

    mxbai-embed-large produces 1024-dimensional vectors.
    For testing, we generate deterministic vectors using seeded randomness.
    """
    def _single_vector(text: str) -> list:
        """Generate a deterministic 1024-dimensional vector for one text.

        Uses a local Random instance seeded from a stable hash of the text so
        identical text always produces the identical vector, without
        mutating the shared module-level random state and without depending
        on PYTHONHASHSEED (see _stable_seed).
        """
        rng = random.Random(_stable_seed(text))

        # Generate 1024 random floats in [-1, 1] range (typical for embeddings)
        # Real mxbai vectors are normalized and roughly in this range
        return [rng.uniform(-1.0, 1.0) for _ in range(1024)]

    def _embedding_response(texts: list) -> list:
        """Generate 1024-dimensional embedding vectors for a batch of texts.

        Args:
            texts: List of input strings to embed.

        Returns:
            List of vectors (each a list of 1024 floats, mxbai-embed-large
            dimensionality), one per input text, in the same order.
        """
        return [_single_vector(text) for text in texts]

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
