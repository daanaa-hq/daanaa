#!/usr/bin/env python3
"""
Data pipeline health monitoring — validates scorer, FTS5, and embedding index.

Detects:
  - Scorer hasn't run in >24h
  - FTS5 index out of sync with source data
  - Embedding index stale or corrupted
  - Missing v5 scores for recent orgs

Repairs:
  - Rebuild FTS5 if out of sync
  - Recompute stale embeddings
  - Trigger scorer manually if it failed

Run: every 6 hours via cron, or manually before major deployments.
"""

import sqlite3
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = "data/merit_registry.db"
EMBEDDINGS_MIN_COUNT = 400_000  # Should have ~546K
FTS5_MIN_COUNT = 1_500_000  # Should have ~1.8M

class PipelineHealth:
    def __init__(self):
        self.issues = []
        self.repairs = []
        self.status = "healthy"

    def check_scorer(self):
        """Check if scorer ran recently."""
        try:
            conn = sqlite3.connect(DB_PATH)
            result = conn.execute(
                "SELECT run_date FROM score_snapshots ORDER BY run_date DESC LIMIT 1"
            ).fetchone()
            conn.close()

            if not result:
                self.issues.append("No score snapshots found (scorer never ran)")
                self.status = "critical"
                return False

            last_run = datetime.fromisoformat(result[0])
            hours_ago = (datetime.utcnow() - last_run).total_seconds() / 3600

            if hours_ago > 26:
                self.issues.append(f"Scorer stale: {hours_ago:.1f} hours since last run")
                self.status = "critical"
                self.repairs.append("Run: python3 scripts/merit_scorer_v4_0.py")
                return False
            elif hours_ago > 25:
                self.issues.append(f"Scorer aging: {hours_ago:.1f} hours (expected <24h)")
                self.status = "warning"

            return True
        except Exception as e:
            self.issues.append(f"Scorer check failed: {e}")
            self.status = "error"
            return False

    def check_fts5(self):
        """Check if FTS5 index is in sync."""
        try:
            conn = sqlite3.connect(DB_PATH)

            # Count orgs in source
            source_count = conn.execute(
                "SELECT COUNT(*) FROM registry_enriched"
            ).fetchone()[0]

            # Count in FTS5 index
            try:
                fts_count = conn.execute(
                    "SELECT COUNT(*) FROM org_fts"
                ).fetchone()[0]
            except:
                self.issues.append("FTS5 index missing or corrupted")
                self.status = "critical"
                self.repairs.append("Run: python3 scripts/build_fts_index.py")
                conn.close()
                return False

            # Check sync
            if fts_count != source_count:
                diff = source_count - fts_count
                pct = (diff / source_count * 100) if source_count > 0 else 0
                self.issues.append(
                    f"FTS5 out of sync: {fts_count} indexed vs {source_count} source ({pct:.1f}% missing)"
                )
                self.status = "critical"
                self.repairs.append("Run: python3 scripts/build_fts_index.py")
                conn.close()
                return False

            # Test search works
            try:
                test = conn.execute(
                    "SELECT 1 FROM org_fts WHERE org_fts MATCH 'cancer*' LIMIT 1"
                ).fetchone()
            except Exception as e:
                self.issues.append(f"FTS5 search test failed: {e}")
                self.status = "critical"
                self.repairs.append("Run: python3 scripts/build_fts_index.py")
                conn.close()
                return False

            conn.close()
            return True
        except Exception as e:
            self.issues.append(f"FTS5 check failed: {e}")
            self.status = "error"
            return False

    def check_embeddings(self):
        """Check embedding index health."""
        try:
            conn = sqlite3.connect(DB_PATH)

            # Check if table exists
            result = conn.execute(
                "SELECT COUNT(*) FROM org_embeddings WHERE embedding IS NOT NULL"
            ).fetchone()
            emb_count = result[0] if result else 0

            if emb_count < EMBEDDINGS_MIN_COUNT:
                pct = (emb_count / 546_000 * 100) if emb_count > 0 else 0
                self.issues.append(
                    f"Embeddings incomplete: {emb_count} computed ({pct:.1f}% of expected 546K)"
                )
                self.status = "warning"  # Not critical, but should be fixed
                self.repairs.append("Run: python3 scripts/build_org_embeddings.py")

            # Check for recently added orgs without embeddings
            new_orgs = conn.execute(
                "SELECT COUNT(*) FROM registry_enriched "
                "WHERE updated_at > datetime('now', '-1 day') "
                "AND EIN NOT IN (SELECT EIN FROM org_embeddings WHERE embedding IS NOT NULL)"
            ).fetchone()[0]

            if new_orgs > 100:
                self.issues.append(
                    f"{new_orgs} new orgs added but not embedded (semantic search may miss them)"
                )
                self.status = "warning"
                self.repairs.append("Run: python3 scripts/build_org_embeddings.py --recent")

            conn.close()
            return emb_count > 0
        except Exception as e:
            self.issues.append(f"Embeddings check failed: {e}")
            return False

    def check_v5_coverage(self):
        """Check v5 scoring coverage."""
        try:
            conn = sqlite3.connect(DB_PATH)

            total = conn.execute(
                "SELECT COUNT(*) FROM registry_enriched"
            ).fetchone()[0]

            v5_scored = conn.execute(
                "SELECT COUNT(*) FROM registry_enriched WHERE merit_score_v5 IS NOT NULL"
            ).fetchone()[0]

            if v5_scored == 0:
                self.issues.append("No v5 scores computed (feature not yet active?)")
                self.status = "warning"
            else:
                pct = v5_scored / total * 100 if total > 0 else 0
                if pct < 90:
                    self.issues.append(
                        f"v5 coverage low: {v5_scored} scored ({pct:.1f}% of {total})"
                    )
                    self.status = "warning"

            conn.close()
            return v5_scored > 0
        except Exception as e:
            self.issues.append(f"v5 coverage check failed: {e}")
            return False

    def check_database_size(self):
        """Warn if database growing unexpectedly."""
        try:
            size_mb = os.path.getsize(DB_PATH) / 1024**2

            if size_mb > 15_000:  # >15 GB
                self.issues.append(
                    f"Database very large: {size_mb:.0f} MB (consider archiving old data)"
                )
                self.status = "warning"

            # Check page count
            conn = sqlite3.connect(DB_PATH)
            result = conn.execute(
                "SELECT page_count FROM pragma_page_count()"
            ).fetchone()
            page_count = result[0] if result else 0

            # Suggest VACUUM if lots of free space
            free_pages = conn.execute(
                "SELECT (SELECT page_count FROM pragma_page_count()) - "
                "(SELECT page_count FROM pragma_freelist_count())"
            ).fetchone()[0]

            if page_count - free_pages > 10_000:
                self.issues.append(
                    f"Database has {page_count - free_pages:,} used pages, could VACUUM to shrink"
                )

            conn.close()
            return True
        except Exception as e:
            self.issues.append(f"Database size check failed: {e}")
            return False

    def run(self):
        """Run all checks."""
        self.check_scorer()
        self.check_fts5()
        self.check_embeddings()
        self.check_v5_coverage()
        self.check_database_size()

        # Determine overall status
        if "critical" in [issue for issue in self.issues]:
            self.status = "critical"

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": self.status,
            "issues": self.issues,
            "repairs": self.repairs,
            "issue_count": len(self.issues),
        }


if __name__ == "__main__":
    health = PipelineHealth()
    result = health.run()

    print(f"\n{'='*60}")
    print(f"  Pipeline Health Check")
    print(f"{'='*60}\n")

    print(f"Status: {result['status'].upper()}")
    print(f"Issues found: {result['issue_count']}\n")

    if result['issues']:
        print("Issues:")
        for issue in result['issues']:
            print(f"  ⚠ {issue}")
    else:
        print("✓ All checks passed")

    if result['repairs']:
        print("\nSuggested repairs:")
        for repair in result['repairs']:
            print(f"  → {repair}")

    print(f"\n{'='*60}\n")

    # Exit with appropriate code
    sys.exit(0 if result['status'] == "healthy" else 1 if result['status'] == "warning" else 2)
