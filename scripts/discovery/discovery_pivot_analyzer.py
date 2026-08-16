#!/usr/bin/env python3
"""
Discovery Pivot Analyzer — analyze sprint results and recommend scaling strategies.

After the 10-strategy sprint completes, this tool:
1. Ranks strategies by success rate + data quality + cost
2. Identifies complementary strategy pairs (combine for better coverage)
3. Calculates scaling roadmap (500K+ orgs)
4. Recommends API/resource requirements
5. Estimates time-to-1M-coverage
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'


class DiscoveryPivotAnalyzer:
    """Analyze strategy results and propose scaling plans."""

    def __init__(self, sprint_results_json: str):
        self.sprint_results = json.load(open(sprint_results_json))
        self.db = sqlite3.connect(str(DB_PATH), timeout=30)

    def get_coverage_baseline(self) -> Dict:
        """Current coverage stats."""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN website IS NOT NULL AND website != '' THEN 1 END) as with_website,
                COUNT(CASE WHEN website_status = 'live' THEN 1 END) as live_websites,
                COUNT(CASE WHEN donate_url IS NOT NULL THEN 1 END) as with_donate_url
            FROM registry_enriched
        """)
        total, with_website, live, donate = cursor.fetchone()
        return {
            "total_orgs": total,
            "with_website": with_website,
            "live_websites": live,
            "with_donate_url": donate,
            "website_coverage_pct": (with_website / total * 100) if total > 0 else 0,
        }

    def calculate_scaling_potential(self, strategy: str, success_rate: float) -> Dict:
        """For a given strategy and success rate, calc scaling to 2M orgs."""
        coverage = self.get_coverage_baseline()
        current_with_website = coverage["with_website"]
        total_orgs = coverage["total_orgs"]
        remaining_orgs = total_orgs - current_with_website

        # If this strategy has X% success on 150 test orgs, extrapolate to full population
        estimated_new_websites = int(remaining_orgs * (success_rate / 100))
        projected_coverage = (current_with_website + estimated_new_websites) / total_orgs * 100

        return {
            "strategy": strategy,
            "success_rate": success_rate,
            "remaining_to_discover": remaining_orgs,
            "estimated_new_websites": estimated_new_websites,
            "projected_total_websites": current_with_website + estimated_new_websites,
            "projected_coverage_pct": projected_coverage,
        }

    def recommend_orchestration(self, rankings: List[Dict]) -> Dict:
        """Recommend how to combine strategies for maximum coverage."""
        # Strategy: Run fastest strategies first (high throughput), backup with slower/higher-confidence
        sorted_by_speed = sorted(rankings, key=lambda x: x.get("avg_response_time_ms", 0))
        sorted_by_success = sorted(rankings, key=lambda x: x.get("success_rate", 0), reverse=True)

        # Complementary pairing: if A and B have low overlap, use together
        recommendations = {
            "phase_1_high_throughput": [],
            "phase_2_high_confidence": [],
            "phase_3_fallback_enrichment": [],
            "parallel_execution_strategy": "Run phases 1 and 2 in parallel with different worker pools",
        }

        # Top 2 fastest = phase 1 (high throughput)
        for strat in sorted_by_speed[:2]:
            if strat.get("success_rate", 0) > 20:  # Minimum viable success rate
                recommendations["phase_1_high_throughput"].append({
                    "strategy": strat["strategy"],
                    "reason": f"Fast ({strat['avg_response_time_ms']:.0f}ms), scalable",
                })

        # Top 2 highest accuracy = phase 2
        for strat in sorted_by_success[:2]:
            if strat["strategy"] not in [s["strategy"] for s in recommendations["phase_1_high_throughput"]]:
                recommendations["phase_2_high_confidence"].append({
                    "strategy": strat["strategy"],
                    "reason": f"High confidence ({strat['success_rate']:.1f}%)",
                })

        return recommendations

    def estimate_scaling_timeline(self, top_strategy: str, success_rate: float) -> Dict:
        """Estimate time to reach 1M orgs with a given strategy."""
        coverage = self.get_coverage_baseline()
        remaining = coverage["total_orgs"] - coverage["with_website"]

        # Assume different orgs/second throughput
        scenarios = {
            "conservative": 1.0,    # 1 org/sec = 86k orgs/day
            "moderate": 5.0,        # 5 orgs/sec = 432k orgs/day
            "aggressive": 20.0,     # 20 orgs/sec = 1.7M orgs/day
        }

        timelines = {}
        for scenario, rate in scenarios.items():
            orgs_per_day = rate * 86400
            days_to_1m = 1000000 / orgs_per_day if orgs_per_day > 0 else float('inf')
            timelines[scenario] = {
                "orgs_per_second": rate,
                "orgs_per_day": orgs_per_day,
                "days_to_1m_coverage": days_to_1m if days_to_1m != float('inf') else None,
                "estimated_cost_markers": {
                    "api_calls": int(1000000 / (success_rate / 100)),
                    "estimated_bandwidth_mb": int(1000000 * 0.5),
                }
            }

        return timelines

    def generate_pivot_plan(self) -> Dict:
        """Generate comprehensive pivot plan for next sprint."""
        coverage = self.get_coverage_baseline()
        rankings = self.sprint_results["pivot_plan"]["rankings"]

        pivot_plan = {
            "executive_summary": {
                "current_coverage": f"{coverage['website_coverage_pct']:.1f}%",
                "current_websites": coverage["with_website"],
                "total_orgs": coverage["total_orgs"],
                "remaining_to_discover": coverage["total_orgs"] - coverage["with_website"],
                "top_3_winners": self.sprint_results["pivot_plan"]["rankings"][:3],
            },
            "strategy_scaling_projections": [
                self.calculate_scaling_potential(
                    r["strategy"],
                    r["success_rate"]
                )
                for r in rankings[:5]
            ],
            "recommended_orchestration": self.recommend_orchestration(rankings),
            "scaling_timeline_estimates": self.estimate_scaling_timeline(
                rankings[0]["strategy"],
                rankings[0]["success_rate"]
            ),
            "resource_requirements": {
                "api_keys_needed": [
                    "ProPublica (free, no key)",
                    "Charity Navigator (free tier sufficient)",
                    "Archive.org (free, rate-limited)",
                    "Optional: Serper/Google Search (paid, ~$5/1000 queries)",
                ],
                "infrastructure": {
                    "worker_threads": "10-20 (parallel discovery)",
                    "bandwidth": "Moderate (mostly HEAD requests)",
                    "database_growth": "~50MB per 100K new websites (index overhead)",
                },
                "rate_limiting_considerations": {
                    "google_domains": "2s min between requests (robots.txt compliant)",
                    "archive_org": "1-2 requests/sec max",
                    "charity_navigator": "10 requests/sec (API limit)",
                    "propublica": "Batch-friendly (no strict rate limit)",
                }
            },
            "next_steps": [
                f"1. Validate top 3 winners on larger batch (1000+ orgs each)",
                f"2. Implement multi-strategy fallback orchestration",
                f"3. Deploy winners to discovery_daemon.py as new strategies",
                f"4. Run 24/7 on off-peak GPU window (10pm-6am)",
                f"5. Measure real-world success rate + data quality on live orgs",
                f"6. Pivot to highest-ROI strategy at scale",
            ],
            "generated_at": datetime.now().isoformat(),
        }

        return pivot_plan


def analyze_sprint_results(results_file: str):
    """Main entry point: analyze a sprint results file."""
    logger.info(f"Loading sprint results from {results_file}")
    analyzer = DiscoveryPivotAnalyzer(results_file)

    pivot_plan = analyzer.generate_pivot_plan()

    # Write pivot plan
    output_file = Path(results_file).parent / f"pivot_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(pivot_plan, f, indent=2)

    logger.info(f"\nPivot plan written to: {output_file}\n")
    logger.info("=" * 80)
    logger.info("PIVOT PLAN SUMMARY")
    logger.info("=" * 80)
    logger.info(json.dumps(pivot_plan["executive_summary"], indent=2))
    logger.info("\nRECOMMENDED ORCHESTRATION:")
    logger.info(json.dumps(pivot_plan["recommended_orchestration"], indent=2))
    logger.info("\nNEXT STEPS:")
    for step in pivot_plan["next_steps"]:
        logger.info(f"  {step}")

    return pivot_plan


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        analyze_sprint_results(sys.argv[1])
    else:
        print("Usage: python3 discovery_pivot_analyzer.py <sprint_results.json>")
