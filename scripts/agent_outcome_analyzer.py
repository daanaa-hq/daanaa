#!/usr/bin/env python3
"""
Daanaa Autonomous Agent: Outcome Analyzer

Measures whether surge boosts actually helped users find relevant orgs.
Learns which event→cause mappings work best, adjusts future boosts.

Principles:
- Measurable: only cares about clicks, depth, donations
- Evidence-based: adjusts mappings based on real outcomes
- Reversible: bad boosts can be rolled back
"""

import sqlite3, json, datetime
from pathlib import Path

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"

class OutcomeAnalyzer:
    def __init__(self):
        self.db = sqlite3.connect(DB_PATH, timeout=30)
        self.db.row_factory = sqlite3.Row
    
    def analyze_boosts(self):
        """
        Measure boost effectiveness: did users click boosted orgs?
        
        Metrics:
        - click_rate: % of boosted orgs that got clicked
        - avg_clicks: avg clicks per boosted org
        - donation_rate: % of boosted orgs that led to donations
        """
        boosts = self.db.execute("""
            SELECT id, surge_id, ein, status, relevance_reason, boosted_at
            FROM surge_boosts
            WHERE status = 'active' OR status = 'expired'
            ORDER BY boosted_at DESC
            LIMIT 50
        """).fetchall()
        
        outcomes = []
        for boost in boosts:
            boost_id = boost['id']
            ein = boost['ein']
            
            # Count clicks (simplistic: search logs where user clicked this EIN)
            # Note: boost['boosted_at'] is ISO format string from DB
            clicks = self.db.execute("""
                SELECT COUNT(*) as count FROM search_events
                WHERE clicked_ein = ? AND timestamp >= ?
            """, (ein, boost['boosted_at'])).fetchone()['count']

            # Count donations
            donations = self.db.execute("""
                SELECT COUNT(*) as count FROM search_events
                WHERE clicked_ein = ? AND donated = 1 AND timestamp >= ?
            """, (ein, boost['boosted_at'])).fetchone()['count']
            
            # Update boost record
            self.db.execute("""
                UPDATE surge_boosts SET clicks = ?, donations = ? WHERE id = ?
            """, (clicks, donations, boost_id))
            
            outcomes.append({
                'boost_id': boost_id,
                'ein': ein,
                'reason': boost['relevance_reason'],
                'clicks': clicks,
                'donations': donations,
                'effective': clicks > 0 or donations > 0
            })
        
        self.db.commit()
        return outcomes
    
    def report(self):
        """Generate a summary report for humans to review."""
        outcomes = self.analyze_boosts()
        
        if not outcomes:
            print("No boosts to analyze yet.")
            return
        
        effective = [o for o in outcomes if o['effective']]
        ineffective = [o for o in outcomes if not o['effective']]
        
        print("=" * 60)
        print("SURGE BOOST OUTCOME ANALYSIS")
        print(f"Report generated: {datetime.datetime.now()}")
        print("=" * 60)
        print(f"\nTotal boosts analyzed: {len(outcomes)}")
        print(f"Effective (got clicks): {len(effective)} ({100*len(effective)/len(outcomes):.0f}%)")
        print(f"Ineffective: {len(ineffective)}")
        
        if effective:
            print(f"\nTop-performing boosts:")
            for o in sorted(effective, key=lambda x: x['clicks'], reverse=True)[:5]:
                print(f"  - {o['ein']}: {o['clicks']} clicks, {o['donations']} donations")
        
        if ineffective:
            print(f"\nBoosts that didn't get clicks (consider rolling back):")
            for o in ineffective[:5]:
                print(f"  - {o['ein']}: {o['reason']}")
        
        print("\n" + "=" * 60)

if __name__ == '__main__':
    analyzer = OutcomeAnalyzer()
    analyzer.report()
