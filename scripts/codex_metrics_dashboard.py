#!/usr/bin/env python3
"""
Codex Token Metrics Dashboard

Monitors Codex token usage and pre-check effectiveness.
Generates reports on:
- Token savings vs. baseline
- Pre-check discovery rate
- Cost trends
- Governance compliance

Usage:
    python3 scripts/codex_metrics_dashboard.py [--export html|csv|json]
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any


class CodexMetricsDashboard:
    """Track and analyze Codex review metrics."""

    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.reviews_log = self.repo_root / "docs" / "ralph_codex_reviews.jsonl"
        self.metrics_file = self.repo_root / "docs" / "codex_metrics.json"
        self.reviews = []
        self.load_reviews()

    def load_reviews(self) -> None:
        """Load review log from JSONL file."""
        if self.reviews_log.exists():
            with open(self.reviews_log, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            self.reviews.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

    def get_metrics(self) -> Dict[str, Any]:
        """Calculate metrics from reviews."""
        if not self.reviews:
            return self._empty_metrics()

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "total_reviews": len(self.reviews),
            "date_range": {
                "start": self.reviews[0].get("timestamp", "unknown"),
                "end": self.reviews[-1].get("timestamp", "unknown"),
            },
        }

        # Token metrics
        tokens = [r.get("tokens_used", 0) for r in self.reviews if r.get("tokens_used")]
        metrics["tokens"] = {
            "total": sum(tokens),
            "average": sum(tokens) / len(tokens) if tokens else 0,
            "min": min(tokens) if tokens else 0,
            "max": max(tokens) if tokens else 0,
        }

        # Findings metrics
        findings = [r.get("findings_count", 0) for r in self.reviews]
        metrics["findings"] = {
            "total": sum(findings),
            "average": sum(findings) / len(findings) if findings else 0,
        }

        # By review type
        by_type = {}
        for review in self.reviews:
            rtype = review.get("review_type", "unknown")
            if rtype not in by_type:
                by_type[rtype] = {
                    "count": 0,
                    "tokens": 0,
                    "findings": 0,
                    "pre_check_findings": 0,
                    "codex_findings": 0,
                }
            by_type[rtype]["count"] += 1
            by_type[rtype]["tokens"] += review.get("tokens_used", 0)
            by_type[rtype]["findings"] += review.get("findings_count", 0)
            by_type[rtype]["pre_check_findings"] += (
                review.get("semgrep_findings", 0) + review.get("lint_errors", 0)
            )
            by_type[rtype]["codex_findings"] += review.get("codex_findings", 0)

        metrics["by_type"] = by_type

        # Pre-check effectiveness
        metrics["pre_check_effectiveness"] = self._calculate_pre_check_effectiveness()

        # Savings vs. baseline
        metrics["savings"] = self._calculate_savings_vs_baseline()

        return metrics

    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics template."""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_reviews": 0,
            "message": "No reviews logged yet",
        }

    def _calculate_pre_check_effectiveness(self) -> Dict[str, Any]:
        """Calculate % of issues caught by pre-checks."""
        total_pre_check = sum(
            r.get("semgrep_findings", 0) + r.get("lint_errors", 0)
            for r in self.reviews
        )
        total_codex = sum(r.get("codex_findings", 0) for r in self.reviews)
        total = total_pre_check + total_codex

        if total == 0:
            return {"pre_check_catch_rate": 0, "total_findings": 0}

        return {
            "pre_check_catch_rate": round((total_pre_check / total) * 100, 1),
            "codex_catch_rate": round((total_codex / total) * 100, 1),
            "pre_check_findings": total_pre_check,
            "codex_findings": total_codex,
            "total_findings": total,
        }

    def _calculate_savings_vs_baseline(self) -> Dict[str, Any]:
        """Calculate token savings vs. baseline."""
        baseline_costs = {
            "architecture": 12000,
            "security": 12000,
            "code": 8000,
            "other": 10000,
        }

        savings_by_type = {}
        total_baseline = 0
        total_actual = 0

        for rtype, stats in self.get_metrics().get("by_type", {}).items():
            baseline = baseline_costs.get(rtype, 10000)
            actual_avg = stats["tokens"] / stats["count"] if stats["count"] > 0 else 0
            savings_pct = round((1 - actual_avg / baseline) * 100, 1) if baseline > 0 else 0

            savings_by_type[rtype] = {
                "baseline_per_review": baseline,
                "actual_avg_per_review": round(actual_avg, 0),
                "savings_percent": savings_pct,
                "reviews": stats["count"],
                "total_tokens": stats["tokens"],
            }

            total_baseline += baseline * stats["count"]
            total_actual += stats["tokens"]

        total_savings_pct = round((1 - total_actual / total_baseline) * 100, 1) if total_baseline > 0 else 0

        return {
            "by_type": savings_by_type,
            "total": {
                "baseline_tokens": total_baseline,
                "actual_tokens": total_actual,
                "tokens_saved": total_baseline - total_actual,
                "savings_percent": total_savings_pct,
            },
        }

    def print_dashboard(self) -> None:
        """Print dashboard to stdout."""
        metrics = self.get_metrics()

        print("\n" + "=" * 70)
        print("CODEX TOKEN METRICS DASHBOARD")
        print("=" * 70)
        print(f"Timestamp: {metrics['timestamp']}")
        print(f"Total reviews: {metrics['total_reviews']}")

        if metrics["total_reviews"] == 0:
            print("\n⚠️  No reviews logged yet. Run Codex reviews to populate metrics.")
            print("=" * 70)
            return

        print(f"Date range: {metrics['date_range']['start']} → {metrics['date_range']['end']}")

        # Token summary
        print("\n📊 TOKEN USAGE")
        print(f"  Total:   {metrics['tokens']['total']:,} tokens")
        print(f"  Average: {metrics['tokens']['average']:.0f} tokens/review")
        print(f"  Range:   {metrics['tokens']['min']:.0f} — {metrics['tokens']['max']:.0f}")

        # Findings summary
        print("\n🔍 FINDINGS")
        print(f"  Total:   {metrics['findings']['total']} findings")
        print(f"  Average: {metrics['findings']['average']:.1f} findings/review")

        # Pre-check effectiveness
        pre_check = metrics.get("pre_check_effectiveness", {})
        if pre_check.get("total_findings", 0) > 0:
            print("\n✅ PRE-CHECK EFFECTIVENESS")
            print(f"  Pre-check caught:  {pre_check['pre_check_findings']} ({pre_check['pre_check_catch_rate']}%)")
            print(f"  Codex caught:      {pre_check['codex_findings']} ({pre_check['codex_catch_rate']}%)")

        # Savings
        print("\n💰 SAVINGS VS. BASELINE")
        by_type = metrics.get("savings", {}).get("by_type", {})
        for rtype, data in by_type.items():
            print(f"\n  {rtype.upper()}")
            print(f"    Baseline: {data['baseline_per_review']:,} tokens/review")
            print(f"    Actual:   {data['actual_avg_per_review']:,} tokens/review")
            print(f"    Savings:  {data['savings_percent']}%")
            print(f"    Reviews:  {data['reviews']} × {data['total_tokens']:,} total")

        total_savings = metrics.get("savings", {}).get("total", {})
        if total_savings.get("baseline_tokens", 0) > 0:
            print(f"\n  TOTAL IMPACT")
            print(f"    Baseline: {total_savings['baseline_tokens']:,} tokens")
            print(f"    Actual:   {total_savings['actual_tokens']:,} tokens")
            print(f"    Saved:    {total_savings['tokens_saved']:,} tokens ({total_savings['savings_percent']}%)")

            # Monthly projection
            monthly_savings = (total_savings['tokens_saved'] / max(metrics['total_reviews'], 1)) * 40  # ~40 reviews/month
            print(f"    Projected/month: {monthly_savings:,.0f} tokens saved")

        print("\n" + "=" * 70)

    def export_json(self, filepath: str) -> None:
        """Export metrics to JSON."""
        metrics = self.get_metrics()
        with open(filepath, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"✅ Exported to {filepath}")

    def export_csv(self, filepath: str) -> None:
        """Export review logs to CSV."""
        import csv

        if not self.reviews:
            print("No reviews to export")
            return

        keys = set()
        for review in self.reviews:
            keys.update(review.keys())

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(keys))
            writer.writeheader()
            for review in self.reviews:
                writer.writerow({k: review.get(k, "") for k in sorted(keys)})

        print(f"✅ Exported {len(self.reviews)} reviews to {filepath}")

    def export_html(self, filepath: str) -> None:
        """Export dashboard as HTML."""
        metrics = self.get_metrics()

        html = f"""
        <html>
        <head>
            <title>Codex Metrics Dashboard</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 40px; }}
                .dashboard {{ max-width: 900px; }}
                .metric {{ margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 8px; }}
                h1 {{ color: #333; }}
                .value {{ font-size: 24px; font-weight: bold; color: #0066cc; }}
                .label {{ color: #666; font-size: 14px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                th {{ background: #f0f0f0; padding: 8px; text-align: left; }}
                td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="dashboard">
                <h1>Codex Token Metrics Dashboard</h1>
                <p>{metrics['timestamp']}</p>

                <div class="metric">
                    <div class="label">Total Reviews</div>
                    <div class="value">{metrics.get('total_reviews', 0)}</div>
                </div>

                <div class="metric">
                    <div class="label">Average Tokens per Review</div>
                    <div class="value">{metrics.get('tokens', {}).get('average', 0):.0f}</div>
                </div>

                <div class="metric">
                    <h3>Savings vs. Baseline</h3>
                    <div class="value">{metrics.get('savings', {}).get('total', {}).get('savings_percent', 0)}%</div>
                    <p>Tokens saved: {metrics.get('savings', {}).get('total', {}).get('tokens_saved', 0):,}</p>
                </div>

                <h2>By Review Type</h2>
                <table>
                    <tr>
                        <th>Type</th>
                        <th>Count</th>
                        <th>Baseline</th>
                        <th>Actual Avg</th>
                        <th>Savings</th>
                    </tr>
        """

        for rtype, data in metrics.get("savings", {}).get("by_type", {}).items():
            html += f"""
                    <tr>
                        <td>{rtype}</td>
                        <td>{data['reviews']}</td>
                        <td>{data['baseline_per_review']:,}</td>
                        <td>{data['actual_avg_per_review']:,}</td>
                        <td>{data['savings_percent']}%</td>
                    </tr>
            """

        html += """
                </table>
            </div>
        </body>
        </html>
        """

        with open(filepath, "w") as f:
            f.write(html)
        print(f"✅ Exported to {filepath}")


def main():
    dashboard = CodexMetricsDashboard(repo_root=".")

    # Parse arguments
    if "--export" in sys.argv:
        export_idx = sys.argv.index("--export")
        if export_idx + 1 < len(sys.argv):
            export_type = sys.argv[export_idx + 1]
            filepath = f"docs/codex_metrics_export.{export_type}"

            if export_type == "json":
                dashboard.export_json(filepath)
            elif export_type == "csv":
                dashboard.export_csv(filepath)
            elif export_type == "html":
                dashboard.export_html(filepath)
            else:
                print(f"Unknown export format: {export_type}")
                sys.exit(1)
    else:
        dashboard.print_dashboard()


if __name__ == "__main__":
    main()
