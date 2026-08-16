#!/usr/bin/env python3
"""Idempotent local backfill for Daanaa's additive v6 data foundation."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SOURCE = "registry_enriched_snapshot"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/merit_registry.db")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    conn = sqlite3.connect(f"file:{db_path}?mode=rw", uri=True)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        (Path(__file__).parents[1] / "migrations/010_v6_foundation.sql").read_text()
    )

    total = conn.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
    tax_year = "COALESCE(latest_tax_year, nccs_data_year, 0)"
    identity = "EIN IS NOT NULL AND TRIM(EIN) <> ''"
    valid_year = f"({tax_year} BETWEEN 1990 AND 2100)"
    eligible = f"{identity} AND {valid_year}"
    financial_values = (
        "(total_revenue IS NOT NULL OR total_expenses IS NOT NULL OR "
        "total_assets IS NOT NULL OR total_liabilities IS NOT NULL OR "
        "net_assets IS NOT NULL)"
    )
    quarantine_filter = (
        f"(NOT ({identity}) OR "
        f"({identity} AND {financial_values} AND NOT {valid_year}))"
    )
    eligible_financial = conn.execute(
        f"SELECT COUNT(*) FROM registry_enriched WHERE {eligible}"
    ).fetchone()[0]
    quarantine_count = conn.execute(
        f"SELECT COUNT(*) FROM registry_enriched WHERE {quarantine_filter}"
    ).fetchone()[0]

    if not args.apply:
        print(json.dumps({
            "mode": "dry_run",
            "source_rows": total,
            "eligible_financial_rows": eligible_financial,
            "classification_source_rows": conn.execute(
                f"SELECT COUNT(*) FROM registry_enriched WHERE {identity}"
            ).fetchone()[0],
            "quarantine_candidates": quarantine_count,
        }, indent=2))
        conn.close()
        return 0

    batch_id = "local-registry-" + datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    retrieved_at = datetime.now(timezone.utc).isoformat()

    try:
        conn.execute("BEGIN")
        conn.execute(
            f"""
            INSERT OR IGNORE INTO org_financial_years (
                ein, tax_year, filing_form, source_name, source_record_id,
                retrieved_at, record_hash, total_revenue, total_expenses,
                program_expenses, management_expenses, fundraising_expenses,
                total_assets, total_liabilities, net_assets, employees,
                months_of_reserve, data_quality_status
            )
            SELECT
                EIN, {tax_year}, subsection, ?, EIN || ':' || {tax_year},
                ?, NULL, total_revenue, total_expenses, program_expenses,
                management_expenses, fundraising_expenses, total_assets,
                total_liabilities, net_assets, employee_count,
                months_of_reserve,
                CASE WHEN total_expenses IS NOT NULL AND total_expenses > 0
                     THEN 'mapped_from_current_registry' ELSE 'partial' END
            FROM registry_enriched
            WHERE {eligible}
            """,
            (SOURCE, retrieved_at),
        )

        cursor = conn.execute(
            """
            SELECT id, ein, tax_year, total_revenue, total_expenses,
                   total_assets, net_assets
            FROM org_financial_years
            WHERE source_name = ? AND record_hash IS NULL
            """,
            (SOURCE,),
        )
        while True:
            rows = cursor.fetchmany(10000)
            if not rows:
                break
            updates = []
            for row in rows:
                material = "|".join(
                    str(row[i] if row[i] is not None else "")
                    for i in range(1, 7)
                )
                updates.append(
                    (hashlib.sha256(material.encode()).hexdigest(), row[0])
                )
            conn.executemany(
                "UPDATE org_financial_years SET record_hash=? WHERE id=?",
                updates,
            )

        classification_queries = [
            (
                "nteecc",
                "NTEECC",
                "reported",
                0,
            ),
            (
                "ntee1",
                "NTEE1",
                "reported",
                0,
            ),
            (
                "funding_archetype",
                "merit_archetype_v5",
                "limited",
                1,
            ),
        ]
        for kind, column, confidence, inferred in classification_queries:
            conn.execute(
                f"""
                INSERT OR IGNORE INTO org_classifications (
                    ein, classification_type, classification_value, source_name,
                    confidence, is_inferred
                )
                SELECT EIN, ?, TRIM({column}), ?, ?, ?
                FROM registry_enriched
                WHERE {identity} AND {column} IS NOT NULL
                  AND TRIM({column}) <> ''
                """,
                (kind, SOURCE, confidence, inferred),
            )

        conn.execute(
            f"""
            INSERT OR IGNORE INTO org_operating_context (
                ein, tax_year, employee_count, board_size,
                board_independent_count, program_expense_ratio,
                overhead_ratio, source_name, retrieved_at, confidence
            )
            SELECT EIN, {tax_year}, employee_count, board_size,
                   board_independent_count,
                   COALESCE(program_expense_ratio, program_expense_pct),
                   overhead_ratio, ?, ?, 'limited'
            FROM registry_enriched
            WHERE {eligible}
            """,
            (SOURCE, retrieved_at),
        )

        for row in conn.execute(
            f"""
            SELECT EIN, organization_name, {tax_year} AS tax_year
            FROM registry_enriched
            WHERE {quarantine_filter}
            LIMIT 10000
            """
        ):
            conn.execute(
                """
                INSERT INTO ingestion_quarantine (
                    source_name, source_record_id, record_type, raw_data,
                    validation_errors
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    SOURCE,
                    row["EIN"],
                    "registry_enriched",
                    json.dumps(dict(row), sort_keys=True),
                    "missing EIN or financial values without valid tax year",
                ),
            )

        counts = {
            "financial": conn.execute(
                "SELECT COUNT(*) FROM org_financial_years"
            ).fetchone()[0],
            "classifications": conn.execute(
                "SELECT COUNT(*) FROM org_classifications"
            ).fetchone()[0],
            "operating_context": conn.execute(
                "SELECT COUNT(*) FROM org_operating_context"
            ).fetchone()[0],
        }
        conn.execute(
            """
            INSERT OR REPLACE INTO ingestion_audit_log (
                source_name, batch_id, source_record_count, valid_records,
                quarantined_records, duplicate_records, validation_errors, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                SOURCE,
                batch_id,
                total,
                total - quarantine_count,
                quarantine_count,
                0,
                json.dumps({"quarantine_filter": quarantine_filter}),
                json.dumps({"normalized_counts": counts}),
            ),
        )
        conn.commit()
        print(json.dumps({
            "mode": "apply",
            "batch_id": batch_id,
            "source_rows": total,
            "quarantine_candidates": quarantine_count,
            **counts,
        }, indent=2))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
