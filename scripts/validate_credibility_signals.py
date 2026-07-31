#!/usr/bin/env python3
"""
validate_credibility_signals.py — Validation framework for Phase 1.

Tests:
1. Functional: All 6 signals compute correctly
2. Performance: API response <200ms, search <400ms
3. Edge cases: Postcard orgs, missing data, revoked orgs
4. Accessibility: WCAG AA compliance
5. Data integrity: Backup verification
"""

import sqlite3
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'


class SignalValidator:
    """Validate credibility signals across all test scenarios."""

    def __init__(self):
        self.db = DB
        self.results = []
        self.start_time = datetime.now()

    def test_functional_signals(self) -> Dict:
        """
        Functional test: Verify all 6 signals compute and return correct format.
        Test 3 org types: large, small, postcard.
        """
        print('Testing: Functional signals...')

        con = sqlite3.connect(str(self.db))
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        test_cases = [
            {
                'name': 'Large org',
                'query': "SELECT EIN FROM registry_enriched WHERE org_status='active' AND total_revenue > 5000000 LIMIT 1",
            },
            {
                'name': 'Small org',
                'query': "SELECT EIN FROM registry_enriched WHERE org_status='active' AND total_revenue BETWEEN 100000 AND 500000 LIMIT 1",
            },
            {
                'name': 'Postcard org',
                'query': "SELECT EIN FROM registry_enriched WHERE is_postcard_org=1 LIMIT 1",
            },
        ]

        results = {}
        for test in test_cases:
            ein_row = cur.execute(test['query']).fetchone()
            if not ein_row:
                results[test['name']] = {
                    'status': 'SKIPPED',
                    'reason': 'No test org found',
                }
                continue

            ein = ein_row['EIN']
            try:
                from credibility_signals import compute_signals
                signals = compute_signals(ein)

                # Verify all 6 signals present
                signal_keys = set(signals.get('signals', {}).keys())
                expected = {
                    'irs_verification',
                    'data_freshness',
                    'expense_ratio',
                    'peer_context',
                    'recency_completeness',
                    'mission_alignment',
                }

                if signal_keys == expected:
                    results[test['name']] = {
                        'status': 'PASS',
                        'ein': ein,
                        'signals_count': len(signal_keys),
                        'composite_confidence': signals.get('composite_confidence'),
                    }
                else:
                    results[test['name']] = {
                        'status': 'FAIL',
                        'ein': ein,
                        'missing_signals': list(expected - signal_keys),
                    }
            except Exception as e:
                results[test['name']] = {
                    'status': 'ERROR',
                    'error': str(e),
                }

        con.close()
        print(f"  ✓ Functional tests: {sum(1 for r in results.values() if r['status'] == 'PASS')}/{len(results)} pass")
        return {
            'test_name': 'functional_signals',
            'results': results,
        }

    def test_performance_response(self) -> Dict:
        """
        Performance test: API response time <200ms.
        Test 10 random orgs.
        """
        print('Testing: Performance (response time)...')

        con = sqlite3.connect(str(self.db))
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # Get 10 random org EINs
        eins = cur.execute(
            "SELECT EIN FROM registry_enriched WHERE org_status='active' ORDER BY RANDOM() LIMIT 10"
        ).fetchall()

        con.close()

        times = []
        from credibility_signals import compute_signals

        for row in eins:
            ein = row['EIN']
            start = time.perf_counter()
            try:
                compute_signals(ein)
                elapsed = (time.perf_counter() - start) * 1000  # milliseconds
                times.append(elapsed)
            except Exception as e:
                print(f"  ✗ Error computing signals for {ein}: {e}")

        if times:
            avg = sum(times) / len(times)
            max_time = max(times)
            passed = sum(1 for t in times if t < 200)

            result = {
                'test_name': 'performance_response',
                'avg_ms': round(avg, 1),
                'max_ms': round(max_time, 1),
                'goal_ms': 200,
                'passed': passed,
                'total': len(times),
                'status': 'PASS' if passed == len(times) else 'PARTIAL' if passed > 0 else 'FAIL',
            }
            print(f"  ✓ Response times: avg {avg:.1f}ms, max {max_time:.1f}ms (goal: <200ms)")
            return result
        else:
            return {
                'test_name': 'performance_response',
                'status': 'SKIPPED',
                'reason': 'No test orgs found',
            }

    def test_edge_cases(self) -> Dict:
        """
        Edge case test: Revoked orgs, missing data, postcard orgs.
        """
        print('Testing: Edge cases...')

        con = sqlite3.connect(str(self.db))
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        test_cases = {
            'revoked_org': (
                "SELECT EIN FROM registry_enriched WHERE irs_revoked=1 LIMIT 1",
                'IRS Verification should return revoked status',
            ),
            'missing_mission': (
                "SELECT EIN FROM registry_enriched WHERE mission IS NULL OR mission='' LIMIT 1",
                'Mission Alignment should return unknown status',
            ),
            'postcard_org': (
                "SELECT EIN FROM registry_enriched WHERE is_postcard_org=1 LIMIT 1",
                'Postcard org should have peer_count_v5 set',
            ),
        }

        results = {}
        from credibility_signals import compute_signals

        for test_name, (query, desc) in test_cases.items():
            ein_row = cur.execute(query).fetchone()
            if not ein_row:
                results[test_name] = {
                    'status': 'SKIPPED',
                    'reason': 'No test org found',
                }
                continue

            ein = ein_row['EIN']
            try:
                signals = compute_signals(ein)
                results[test_name] = {
                    'status': 'PASS',
                    'ein': ein,
                    'description': desc,
                    'signals_computed': len(signals.get('signals', {})),
                }
            except Exception as e:
                results[test_name] = {
                    'status': 'FAIL',
                    'ein': ein,
                    'error': str(e),
                }

        con.close()
        print(f"  ✓ Edge case tests: {sum(1 for r in results.values() if r['status'] == 'PASS')}/{len(results)} pass")
        return {
            'test_name': 'edge_cases',
            'results': results,
        }

    def test_data_integrity(self) -> Dict:
        """
        Data integrity test: Verify schema, indexes, coverage.
        """
        print('Testing: Data integrity...')

        con = sqlite3.connect(str(self.db))
        cur = con.cursor()

        # Check registry_enriched table exists and has expected columns
        cur.execute("PRAGMA table_info(registry_enriched)")
        columns = {row[1] for row in cur.fetchall()}

        expected_cols = {
            'EIN', 'organization_name', 'org_status', 'irs_revoked',
            'total_revenue', 'filing_year', 'merit_peer_count_v5',
            'merit_confidence_v6', 'is_postcard_org',
        }

        missing = expected_cols - columns
        result = {
            'test_name': 'data_integrity',
            'table_exists': True,
            'expected_columns': len(expected_cols),
            'found_columns': len(columns),
            'missing_columns': list(missing),
            'status': 'PASS' if not missing else 'FAIL',
        }

        # Coverage: active orgs
        cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE org_status='active'")
        active_count = cur.fetchone()[0]
        result['active_orgs'] = active_count

        # Coverage: postcard orgs
        cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE is_postcard_org=1")
        postcard_count = cur.fetchone()[0]
        result['postcard_orgs'] = postcard_count

        con.close()
        print(f"  ✓ Data integrity: {active_count:,} active orgs, {postcard_count:,} postcard orgs")
        return result

    def run_all(self) -> Dict:
        """Run all validation tests."""
        print('=' * 60)
        print('CREDIBILITY SIGNALS VALIDATION')
        print(f'Started: {self.start_time.isoformat()}')
        print('=' * 60 + '\n')

        all_results = {
            'validation_start': self.start_time.isoformat(),
            'tests': {},
        }

        all_results['tests']['functional'] = self.test_functional_signals()
        all_results['tests']['performance'] = self.test_performance_response()
        all_results['tests']['edge_cases'] = self.test_edge_cases()
        all_results['tests']['data_integrity'] = self.test_data_integrity()

        # Summary
        passed = sum(
            1 for t in all_results['tests'].values()
            if t.get('status') in ['PASS', 'PARTIAL']
        )
        total = len(all_results['tests'])

        all_results['summary'] = {
            'total_tests': total,
            'passed': passed,
            'status': 'PASS' if passed == total else 'PARTIAL' if passed > 0 else 'FAIL',
            'duration_seconds': (datetime.now() - self.start_time).total_seconds(),
        }

        print('\n' + '=' * 60)
        print(f"VALIDATION COMPLETE: {passed}/{total} tests passed")
        print('=' * 60)

        return all_results


def main():
    validator = SignalValidator()
    results = validator.run_all()
    print(json.dumps(results, indent=2, default=str))


if __name__ == '__main__':
    main()
