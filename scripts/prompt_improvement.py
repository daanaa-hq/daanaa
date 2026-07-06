#!/usr/bin/env python3
"""
Autonomous prompt improvement based on quality metrics.
"""
import sqlite3
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional, Dict, Any


class PromptImprovement:
    """Automatically improve prompts based on quality trends."""

    def __init__(
        self,
        db_con: sqlite3.Connection,
        config: Dict[str, Any],
        prompt_versions_file: Optional[str] = None
    ):
        self.db = db_con
        self.config = config
        self.thresholds = config.get('thresholds', {})

        self.prompt_versions_file = Path(prompt_versions_file) if prompt_versions_file else (
            Path.home() / "meritgiving" / "data" / "enrichment" / "prompt_versions.json"
        )

        self._load_prompt_versions()
        self.improvement_reasoning = None

    def _load_prompt_versions(self) -> None:
        if self.prompt_versions_file and Path(self.prompt_versions_file).exists():
            with open(self.prompt_versions_file) as f:
                self.prompt_versions = json.load(f)
        else:
            self.prompt_versions = self.config.get('prompts', {})

    def should_improve_prompts(self) -> bool:
        cursor = self.db.cursor()
        today = str(date.today())
        cursor.execute(
            """SELECT value FROM quality_log
               WHERE date = ? AND metric_type = 'cause_tag_accuracy' AND cohort = 'All'
               ORDER BY created_at DESC LIMIT 1""",
            (today,)
        )
        row = cursor.fetchone()

        if not row:
            return False

        accuracy = row[0]
        threshold = self.thresholds.get('accuracy_target', 0.75)

        return accuracy < threshold

    def generate_improved_prompt(self) -> Optional[str]:
        if not self.should_improve_prompts():
            return None

        current_version = max(self.prompt_versions.keys(),
                             key=lambda v: float(v[1:]))

        major, minor = current_version[1:].split('.')
        new_version = f"v{major}.{int(minor) + 1}"

        cursor = self.db.cursor()
        cursor.execute(
            """SELECT cohort, value FROM quality_log
               WHERE metric_type = 'cause_tag_accuracy'
               ORDER BY date DESC LIMIT 7"""
        )
        recent_metrics = cursor.fetchall()

        self.improvement_reasoning = self._build_improvement_reasoning(recent_metrics)

        old_prompt = self.prompt_versions[current_version]
        new_prompt = self._enhance_prompt(old_prompt, recent_metrics)

        self.prompt_versions[new_version] = new_prompt

        self._save_prompt_versions()

        return new_version

    def _build_improvement_reasoning(self, metrics: list) -> str:
        if not metrics:
            return "No metrics available for improvement"

        avg_value = sum(m[1] for m in metrics) / len(metrics)

        reasoning = f"""
Prompt Improvement Reasoning (Date: {date.today()}):
- Recent accuracy (7d avg): {avg_value:.2%}
- Target accuracy: {self.thresholds.get('accuracy_target', 0.75):.0%}
- Gap: {(self.thresholds.get('accuracy_target', 0.75) - avg_value):.2%}
- Action: Enhance prompt with better context, examples, or NTEE-specific guidance
"""
        return reasoning.strip()

    def _enhance_prompt(self, old_prompt: Dict[str, str], metrics: list) -> Dict[str, str]:
        enhanced = old_prompt.copy()

        if 'cause_tags' in enhanced:
            enhanced['cause_tags'] += (
                " Focus on the primary mission area first. "
                "Be specific: instead of 'Community', try 'Community Development' or 'Community Education'."
            )

        return enhanced

    def _save_prompt_versions(self) -> None:
        self.prompt_versions_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.prompt_versions_file, 'w') as f:
            json.dump(self.prompt_versions, f, indent=2)

    def get_improvement_reasoning(self) -> Optional[str]:
        return self.improvement_reasoning
