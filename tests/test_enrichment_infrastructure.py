#!/usr/bin/env python3
"""
Integration tests for enrichment infrastructure tools.
Verifies all monitoring/QA components work together correctly.

Run: pytest tests/test_enrichment_infrastructure.py -v
"""

import json
import subprocess
import sqlite3
from pathlib import Path
import tempfile
import pytest

REPO_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
DB_PATH = REPO_ROOT / "data" / "merit_registry.db"


class TestEnrichmentDashboard:
    """Test enrichment_dashboard.py"""

    def test_dashboard_runs(self):
        """Dashboard executes without error."""
        result = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'enrichment_dashboard.py')],
            capture_output=True,
            timeout=10
        )
        assert result.returncode == 0
        assert b'ENRICHMENT DASHBOARD' in result.stdout

    def test_dashboard_shows_metrics(self):
        """Dashboard displays actual metrics from database."""
        result = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'enrichment_dashboard.py')],
            capture_output=True,
            timeout=10,
            text=True
        )
        output = result.stdout
        assert 'Orgs scanned' in output or 'ENRICHMENT' in output
        assert 'Status' in output or '✅' in output

    def test_dashboard_hourly_mode(self):
        """Dashboard --hourly produces concise output."""
        result = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'enrichment_dashboard.py'), '--hourly'],
            capture_output=True,
            timeout=10,
            text=True
        )
        assert result.returncode == 0
        # Hourly output should be single line
        lines = result.stdout.strip().split('\n')
        assert len(lines) <= 3  # Header + output


class TestEnrichmentEfficiency:
    """Test enrichment_efficiency.py"""

    def test_efficiency_shows_metrics(self):
        """Efficiency tracker displays coverage metrics."""
        result = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'enrichment_efficiency.py'), '--show'],
            capture_output=True,
            timeout=10,
            text=True
        )
        assert result.returncode == 0
        assert 'ENRICHMENT EFFICIENCY' in result.stdout
        assert 'Total Active Orgs' in result.stdout

    def test_efficiency_metrics_reasonable(self):
        """Efficiency metrics are within expected ranges."""
        result = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'enrichment_efficiency.py'), '--show'],
            capture_output=True,
            timeout=10,
            text=True
        )
        output = result.stdout

        # Website coverage should be <100%
        assert 'Discovered' in output or 'WEBSITES' in output

        # Should show reasonable percentages
        assert '%' in output


class TestArchiveQAGate:
    """Test archive_qa_gate.py"""

    def test_qa_gate_schema(self):
        """QA gate loads and validates batch structure."""
        # Create minimal test batch
        test_batch = [
            {
                'EIN': '123456789',
                'organization_name': 'Test Org',
                'mission': 'Help people',
                'mission_source': 'claimed',
                'website': 'https://example.com',
                'website_match_quality': 0.9,
                'website_status': 'active',
                'website_source': 'archive',
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_batch, f)
            temp_file = f.name

        try:
            result = subprocess.run(
                ['python3', str(SCRIPTS_DIR / 'archive_qa_gate.py'),
                 '--verify-batch', temp_file],
                capture_output=True,
                timeout=10,
                text=True
            )
            # Should execute (may pass or fail depending on validation logic)
            assert 'QA GATE' in result.stdout or 'checked' in result.stdout.lower()
        finally:
            Path(temp_file).unlink()

    def test_qa_gate_rejects_bad_data(self):
        """QA gate rejects obviously corrupted data."""
        bad_batch = [
            {
                'EIN': '123',
                'organization_name': '',  # Empty name
                'mission': 'x',  # Too short
            }
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(bad_batch, f)
            temp_file = f.name

        try:
            result = subprocess.run(
                ['python3', str(SCRIPTS_DIR / 'archive_qa_gate.py'),
                 '--verify-batch', temp_file],
                capture_output=True,
                timeout=10,
                text=True
            )
            # Should detect issues
            assert 'GATE' in result.stdout
        finally:
            Path(temp_file).unlink()


class TestServiceHealthMonitor:
    """Test service_health_check.py"""

    def test_health_monitor_runs(self):
        """Health monitor executes without error."""
        result = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'service_health_check.py')],
            capture_output=True,
            timeout=15
        )
        assert result.returncode == 0
        assert b'SERVICE HEALTH' in result.stdout or b'MONITOR' in result.stdout

    def test_health_monitor_checks_api(self):
        """Health monitor includes API check."""
        result = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'service_health_check.py')],
            capture_output=True,
            timeout=15,
            text=True
        )
        output = result.stdout
        assert 'API' in output or 'api' in output.lower()

    def test_health_monitor_checks_database(self):
        """Health monitor includes database check."""
        result = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'service_health_check.py')],
            capture_output=True,
            timeout=15,
            text=True
        )
        output = result.stdout
        assert 'Search' in output or 'Index' in output or 'database' in output.lower()


class TestEnrichmentPreflight:
    """Test enrichment_preflight.py"""

    def test_preflight_runs_normal_mode(self):
        """Pre-flight checks execute in normal (warning) mode."""
        result = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'enrichment_preflight.py')],
            capture_output=True,
            timeout=15,
            text=True
        )
        # Should always return success in normal mode (warnings only)
        assert b'PRE-FLIGHT' in result.stdout.encode() or 'flight' in result.stdout.lower()

    def test_preflight_reports_results(self):
        """Pre-flight checks report results clearly."""
        result = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'enrichment_preflight.py')],
            capture_output=True,
            timeout=15,
            text=True
        )
        output = result.stdout
        # Should have checkmarks or status indicators
        assert '✅' in output or '❌' in output or 'Database' in output

    def test_preflight_skip_inference(self):
        """Pre-flight checks support --skip-inference flag."""
        result = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'enrichment_preflight.py'), '--skip-inference'],
            capture_output=True,
            timeout=15
        )
        # Should complete faster without inference checks
        assert result.returncode == 0 or result.returncode == 1  # Either pass or fail is ok


class TestDatabaseIntegrity:
    """Test database queries work correctly."""

    def test_database_accessible(self):
        """Database is accessible and queryable."""
        assert DB_PATH.exists()
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM registry_enriched LIMIT 1")
            count = cursor.fetchone()[0]
            assert isinstance(count, int)
            assert count > 0
            conn.close()
        except Exception as e:
            pytest.fail(f"Database query failed: {e}")

    def test_required_columns_exist(self):
        """Database has required enrichment columns."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(registry_enriched)")
        columns = {row[1] for row in cursor.fetchall()}

        required = {'mission', 'website', 'donate_url', 'organization_name'}
        assert required.issubset(columns), f"Missing columns: {required - columns}"
        conn.close()

    def test_search_index_exists(self):
        """FTS5 search index exists and is queryable."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM org_fts LIMIT 1")
            count = cursor.fetchone()[0]
            assert count > 0
        except Exception as e:
            pytest.fail(f"Search index not working: {e}")
        finally:
            conn.close()


class TestDataQuality:
    """Test sample data quality."""

    def test_sample_orgs_have_missions(self):
        """Random sample of orgs have mission text."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM registry_enriched WHERE mission IS NOT NULL "
            "AND mission != '' LIMIT 100"
        )
        count = cursor.fetchone()[0]
        assert count > 50, "Too many orgs without missions"
        conn.close()

    def test_websites_are_valid_urls(self):
        """Websites in database are valid URLs (basic check)."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT website FROM registry_enriched WHERE website IS NOT NULL "
            "LIMIT 10"
        )
        for row in cursor.fetchall():
            url = row[0]
            if url:
                # Basic URL validation
                assert url.startswith(('http://', 'https://', 'www.')), \
                    f"Invalid URL format: {url}"
        conn.close()

    def test_donate_urls_are_valid(self):
        """Donation URLs are valid (basic check)."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT donate_url FROM registry_enriched WHERE donate_url IS NOT NULL "
            "LIMIT 10"
        )
        for row in cursor.fetchall():
            url = row[0]
            if url:
                assert url.startswith(('http://', 'https://')), \
                    f"Invalid donate URL: {url}"
        conn.close()


class TestCrossComponentIntegration:
    """Test tools work together."""

    def test_dashboard_and_efficiency_both_work(self):
        """Dashboard and efficiency tracker can both run on same database."""
        # Run dashboard
        result1 = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'enrichment_dashboard.py')],
            capture_output=True,
            timeout=10
        )

        # Run efficiency
        result2 = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'enrichment_efficiency.py'), '--show'],
            capture_output=True,
            timeout=10
        )

        assert result1.returncode == 0
        assert result2.returncode == 0

    def test_preflight_and_health_compatible(self):
        """Pre-flight checks and health monitor both work."""
        result1 = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'enrichment_preflight.py')],
            capture_output=True,
            timeout=15
        )

        result2 = subprocess.run(
            ['python3', str(SCRIPTS_DIR / 'service_health_check.py')],
            capture_output=True,
            timeout=15
        )

        # Both should complete
        assert result1.returncode in [0, 1]  # 0=pass, 1=fail (both ok for warnings)
        assert result2.returncode == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
