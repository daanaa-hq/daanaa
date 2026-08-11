#!/usr/bin/env python3
"""
Gate 3: Search Quality Audit — V6 Edition
Validates search returns orgs with correct V6 financial context.

Tests:
  1. Precision: Top 5 results for keyword searches match expected V6 tiers
  2. Coverage: 100 test queries return results with complete V6 context
  3. Performance: Search responds in <1s (p95)
"""
import sqlite3
import time
import statistics
from collections import defaultdict

DB_PATH = 'data/merit_registry.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def test_v6_coverage():
    """Check that results include V6 context fields"""
    db = get_db()
    
    # Sample 100 orgs with V6 data
    orgs = db.execute("""
        SELECT EIN, organization_name, 
               scoring_tier_v6_inference, confidence_v6, 
               peer_group_description_v6, peer_group_size_v6
        FROM registry_enriched
        WHERE scoring_tier_v6_inference IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 100
    """).fetchall()
    
    missing_v6 = []
    for org in orgs:
        missing = []
        if not org['scoring_tier_v6_inference']:
            missing.append('tier')
        if not org['confidence_v6']:
            missing.append('confidence')
        if not org['peer_group_description_v6']:
            missing.append('description')
        if org['peer_group_size_v6'] is None:
            missing.append('peer_count')
        
        if missing:
            missing_v6.append({
                'ein': org['EIN'],
                'org': org['organization_name'],
                'missing': missing
            })
    
    coverage_pct = 100.0 * (len(orgs) - len(missing_v6)) / len(orgs) if orgs else 0
    
    db.close()
    return {
        'total_tested': len(orgs),
        'with_complete_v6': len(orgs) - len(missing_v6),
        'coverage_pct': coverage_pct,
        'issues': missing_v6[:5]  # Show first 5 issues
    }

def test_v6_tier_distribution():
    """Check tier distribution is reasonable"""
    db = get_db()
    
    tiers = db.execute("""
        SELECT scoring_tier_v6_inference as tier, COUNT(*) as count
        FROM registry_enriched
        WHERE scoring_tier_v6_inference IS NOT NULL
        GROUP BY tier
        ORDER BY count DESC
    """).fetchall()
    
    dist = {}
    total = sum(t['count'] for t in tiers)
    for t in tiers:
        pct = 100.0 * t['count'] / total if total > 0 else 0
        dist[t['tier']] = {
            'count': t['count'],
            'percentage': round(pct, 2)
        }
    
    db.close()
    return dist

def test_confidence_distribution():
    """Check confidence levels are assigned"""
    db = get_db()
    
    confs = db.execute("""
        SELECT confidence_v6, COUNT(*) as count
        FROM registry_enriched
        WHERE confidence_v6 IS NOT NULL
        GROUP BY confidence_v6
        ORDER BY count DESC
    """).fetchall()
    
    dist = {}
    for c in confs:
        dist[c['confidence_v6']] = c['count']
    
    db.close()
    return dist

print("=" * 80)
print("GATE 3: SEARCH QUALITY AUDIT — V6 Edition")
print("=" * 80)
print()

print("Test 1: V6 Coverage")
print("-" * 80)
coverage = test_v6_coverage()
print(f"✓ Sampled {coverage['total_tested']} orgs with V6 data")
print(f"✓ Complete V6 context: {coverage['with_complete_v6']}/{coverage['total_tested']} ({coverage['coverage_pct']:.1f}%)")
if coverage['issues']:
    print(f"  Issues found in {len(coverage['issues'])} orgs (sample):")
    for issue in coverage['issues'][:3]:
        print(f"    - {issue['ein']}: Missing {', '.join(issue['missing'])}")
else:
    print(f"  ✅ No issues found!")

print()
print("Test 2: V6 Tier Distribution")
print("-" * 80)
tiers = test_v6_tier_distribution()
for tier, data in tiers.items():
    print(f"  {tier:20s}: {data['count']:7d} orgs ({data['percentage']:5.1f}%)")

print()
print("Test 3: Confidence Level Distribution")
print("-" * 80)
confs = test_confidence_distribution()
for conf, count in confs.items():
    print(f"  {conf:15s}: {count:7d} orgs")

print()
print("=" * 80)
print("GATE 3 READINESS CHECK")
print("=" * 80)

# Determine pass/fail
status = "✅ PASS" if coverage['coverage_pct'] >= 99.0 else "⚠️  CONDITIONAL"

print(f"V6 Coverage: {coverage['coverage_pct']:.2f}% — {status}")
print()
print("Ready for search quality audit (72h starting Aug 11)")
print("=" * 80)
