"""Task 2: Test fixtures for enrichment pipeline.

Verifies that mock_qwen, mock_embeddings, test_db, and sample_orgs
fixtures are available and work correctly.
"""

import sqlite3
import pytest


def test_mock_qwen_fixture(mock_qwen):
    """Verify mock_qwen fixture exists and returns callable."""
    assert callable(mock_qwen), "mock_qwen must be callable"

    # Simulate Qwen response
    response = mock_qwen("Generate cause tags for an animal shelter")
    assert isinstance(response, str), "mock_qwen must return a string"
    assert len(response) > 0, "mock_qwen response must not be empty"


def test_mock_embeddings_fixture(mock_embeddings):
    """Verify mock_embeddings fixture returns 1024-dim vectors."""
    assert callable(mock_embeddings), "mock_embeddings must be callable"

    # Generate test vector
    vector = mock_embeddings("test query")
    assert isinstance(vector, list), "mock_embeddings must return a list"
    assert len(vector) == 1024, "mock_embeddings must return 1024-dim vectors (mxbai-embed-large)"
    assert all(isinstance(x, float) for x in vector), "all dimensions must be floats"


def test_test_db_fixture(test_db):
    """Verify test_db fixture creates in-memory SQLite with enrichment schema."""
    assert isinstance(test_db, sqlite3.Connection), "test_db must be a sqlite3.Connection"

    cursor = test_db.cursor()

    # Verify enrichment_run table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='enrichment_run'")
    assert cursor.fetchone() is not None, "enrichment_run table must exist"

    # Verify quality_log table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quality_log'")
    assert cursor.fetchone() is not None, "quality_log table must exist"

    # Verify registry_enriched table exists (from base conftest schema)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='registry_enriched'")
    assert cursor.fetchone() is not None, "registry_enriched table must exist"

    # Verify indexes exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_enrichment_date_ein'")
    assert cursor.fetchone() is not None, "idx_enrichment_date_ein index must exist"


def test_sample_orgs_fixture(sample_orgs):
    """Verify sample_orgs fixture returns valid org data."""
    assert isinstance(sample_orgs, list), "sample_orgs must be a list"
    assert len(sample_orgs) >= 3, "sample_orgs must have at least 3 test orgs"

    # Check structure of first org
    org = sample_orgs[0]
    assert isinstance(org, dict), "each org must be a dict"

    required_keys = {'ein', 'organization_name', 'ntee1', 'mission', 'city', 'state'}
    assert required_keys.issubset(org.keys()), f"org must have keys: {required_keys}"

    # Verify EIN format
    assert len(org['ein']) == 9, "EIN must be 9 digits"
    assert org['ein'].isdigit(), "EIN must be all digits"
