#!/usr/bin/env python3
"""
Daily quality measurement: track accuracy, validity, and trends.
"""
import sqlite3
from datetime import date
from typing import Dict, Any, Optional
import json


class QualityMeasurement:
    """Measure enrichment quality and log metrics for improvement."""

    def __init__(self, db_con: sqlite3.Connection):
        self.db = db_con

    def measure_daily_quality(
        self,
        run_date: str,
        tag_corrections: Optional[Dict[str, str]] = None,
        website_validations: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Dict[str, float]]:
        tag_corrections = tag_corrections or {}
        website_validations = website_validations or {}

        results = {}

        if tag_corrections:
            all_accuracy = self._calculate_tag_accuracy(run_date, tag_corrections)
            results.setdefault('All', {})['cause_tag_accuracy'] = all_accuracy

            self._log_metric(
                date=run_date,
                metric_type='cause_tag_accuracy',
                value=all_accuracy,
                cohort='All',
                prompt_version='v1.0',
                notes=f'Measured from {len(tag_corrections)} corrections'
            )

        if website_validations:
            validity = self._calculate_website_validity(run_date, website_validations)
            results.setdefault('All', {})['website_validity'] = validity

            self._log_metric(
                date=run_date,
                metric_type='website_validity',
                value=validity,
                cohort='All',
                prompt_version='v1.0',
                notes=f'Measured from {len(website_validations)} validations'
            )

        return results

    def _calculate_tag_accuracy(
        self,
        run_date: str,
        corrections: Dict[str, str]
    ) -> float:
        cursor = self.db.cursor()

        ein_placeholders = ','.join('?' * len(corrections))
        cursor.execute(
            f"""SELECT org_ein, generated_value FROM enrichment_run
               WHERE run_date = ? AND enrichment_type = 'cause_tags'
               AND org_ein IN ({ein_placeholders})""",
            [run_date] + list(corrections.keys())
        )
        generated = {row[0]: row[1] for row in cursor.fetchall()}

        if not generated:
            return 0.0

        accuracies = []
        for ein, corrected_tags in corrections.items():
            if ein not in generated:
                continue

            gen_tags = set(generated[ein].lower().split(','))
            corr_tags = set(corrected_tags.lower().split(','))

            overlap = len(gen_tags & corr_tags)
            total = len(gen_tags)
            accuracy = overlap / total if total > 0 else 0.0
            accuracies.append(accuracy)

        return sum(accuracies) / len(accuracies) if accuracies else 0.0

    def _calculate_website_validity(
        self,
        run_date: str,
        validations: Dict[str, bool]
    ) -> float:
        if not validations:
            return 0.0

        valid_count = sum(1 for is_valid in validations.values() if is_valid)
        return valid_count / len(validations)

    def _log_metric(
        self,
        date: str,
        metric_type: str,
        value: float,
        cohort: str = 'All',
        prompt_version: str = 'v1.0',
        notes: Optional[str] = None
    ) -> None:
        cursor = self.db.cursor()

        try:
            cursor.execute(
                """INSERT INTO quality_log
                   (date, metric_type, value, cohort, prompt_version, notes)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (date, metric_type, value, cohort, prompt_version, notes)
            )
            self.db.commit()
        except sqlite3.IntegrityError:
            cursor.execute(
                """UPDATE quality_log SET value = ?, notes = ?
                   WHERE date = ? AND metric_type = ? AND cohort = ? AND prompt_version = ?""",
                (value, notes, date, metric_type, cohort, prompt_version)
            )
            self.db.commit()

    def get_quality_trend(
        self,
        metric_type: str,
        cohort: str = 'All',
        days: int = 7
    ) -> list[Dict[str, Any]]:
        cursor = self.db.cursor()
        cursor.execute(
            """SELECT date, value, prompt_version FROM quality_log
               WHERE metric_type = ? AND cohort = ?
               ORDER BY date DESC LIMIT ?""",
            (metric_type, cohort, days)
        )
        return [
            {'date': row[0], 'value': row[1], 'prompt_version': row[2]}
            for row in cursor.fetchall()
        ]
