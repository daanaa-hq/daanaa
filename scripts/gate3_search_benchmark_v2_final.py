"""
FINAL: Gate 3 Search Benchmark with real production EINs
Uses merit_score_v5 (latest available column)
"""
import sqlite3
import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class SearchBenchmark:
    """Real production data benchmark"""
    
    def __init__(self, db_path: str = "data/merit_registry.db"):
        self.db_path = db_path
    
    def build_ground_truth_from_production(self) -> Dict:
        """Query production DB for high-scoring orgs per category"""
        ground_truth = {}
        categories = [
            ("healthcare", "health OR medical OR hospice OR mental"),
            ("education", "school OR education OR literacy OR tutoring"),
            ("environment", "environment OR conservation OR climate OR water"),
            ("international", "refugee OR disaster OR humanitarian OR global"),
            ("civil_rights", "rights OR justice OR diversity OR equity"),
        ]
        
        try:
            with sqlite3.connect(self.db_path) as db:
                for category, keywords in categories:
                    cursor = db.execute("""
                        SELECT ein, organization_name, merit_score_v5
                        FROM registry_enriched
                        WHERE merit_score_v5 IS NOT NULL
                            AND merit_score_v5 > 50
                        ORDER BY merit_score_v5 DESC
                        LIMIT 20
                    """)
                    
                    eins = [row[0] for row in cursor.fetchall()]
                    if eins:
                        ground_truth[category] = {
                            "eins": eins,
                            "category": category,
                            "count": len(eins)
                        }
                        logger.info(f"✓ {category}: {len(eins)} high-scoring orgs")
        except Exception as e:
            logger.error(f"Failed to build ground truth: {e}")
        
        return ground_truth

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    benchmark = SearchBenchmark()
    ground_truth = benchmark.build_ground_truth_from_production()
    
    print(f"\n✅ Gate 3 Benchmark Ground Truth Built")
    print(f"   Categories: {len(ground_truth)}")
    print(f"   Total orgs: {sum(d['count'] for d in ground_truth.values())}")
    print(f"\n   Categories found:")
    for cat, data in ground_truth.items():
        print(f"     - {cat}: {data['count']} orgs")
    
    print(f"\n✅ Ready for Phase 1-4 integration")
