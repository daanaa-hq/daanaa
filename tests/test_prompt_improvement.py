"""
Task 6: Autonomous prompt improvement based on quality metrics.

Tests for PromptImprovement class:
- should_improve_prompts() returns False when accuracy is above target
- should_improve_prompts() returns True when accuracy is below target
- generate_improved_prompt() creates a new version file with enhanced content
- Improvement reasoning is captured and human-readable
"""

import json
import sqlite3
from datetime import date
from pathlib import Path
import pytest


def test_no_improvement_when_quality_is_good(test_db, enrich_config):
    """Test that should_improve_prompts() returns False when quality is above threshold."""
    from scripts.prompt_improvement import PromptImprovement

    # Insert a high accuracy metric (0.85 > target of 0.75)
    cursor = test_db.cursor()
    today = str(date.today())
    cursor.execute(
        """INSERT INTO quality_log (date, metric_type, value, cohort, prompt_version, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (today, 'cause_tag_accuracy', 0.85, 'All', 'v1.0', 'Good performance')
    )
    test_db.commit()

    # Create PromptImprovement instance
    improver = PromptImprovement(test_db, enrich_config)

    # Assert that should_improve_prompts returns exactly False
    assert improver.should_improve_prompts() is False, "Expected False when accuracy (0.85) is above threshold (0.75)"


def test_improvement_flagged_when_quality_is_low(test_db, enrich_config):
    """Test that should_improve_prompts() returns True when quality is below threshold."""
    from scripts.prompt_improvement import PromptImprovement

    # Insert a low accuracy metric (0.60 < target of 0.75)
    cursor = test_db.cursor()
    today = str(date.today())
    cursor.execute(
        """INSERT INTO quality_log (date, metric_type, value, cohort, prompt_version, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (today, 'cause_tag_accuracy', 0.60, 'All', 'v1.0', 'Below target')
    )
    test_db.commit()

    # Create PromptImprovement instance
    improver = PromptImprovement(test_db, enrich_config)

    # Assert that should_improve_prompts returns exactly True
    assert improver.should_improve_prompts() is True, "Expected True when accuracy (0.60) is below threshold (0.75)"


def test_new_prompt_version_file_is_created(test_db, enrich_config, tmp_path):
    """Test that generate_improved_prompt() creates a new version file with enhanced content."""
    from scripts.prompt_improvement import PromptImprovement

    # Insert low accuracy to trigger improvement
    cursor = test_db.cursor()
    today = str(date.today())
    cursor.execute(
        """INSERT INTO quality_log (date, metric_type, value, cohort, prompt_version, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (today, 'cause_tag_accuracy', 0.55, 'All', 'v1.0', 'Below target')
    )
    test_db.commit()

    # Use tmp_path for the prompt versions file
    prompt_file = tmp_path / "prompt_versions.json"

    # Create PromptImprovement instance with temp file path
    improver = PromptImprovement(test_db, enrich_config, str(prompt_file))

    # Generate improved prompt
    new_version = improver.generate_improved_prompt()

    # Assert that a new version was created (v1.2 since config has v1.0 and v1.1, max is v1.1)
    assert new_version == "v1.2", f"Expected new_version to be 'v1.2', got '{new_version}'"

    # Assert that the file was created
    assert prompt_file.exists(), f"Expected file to exist at {prompt_file}"

    # Read the file back and verify structure
    with open(prompt_file) as f:
        saved_prompts = json.load(f)

    # Assert v1.2 exists in the saved file
    assert "v1.2" in saved_prompts, "Expected 'v1.2' key in saved prompt versions"

    # Assert the enhanced prompt contains the expected enhancement string
    assert "cause_tags" in saved_prompts["v1.2"], "Expected 'cause_tags' key in v1.2 prompt"
    enhanced_text = saved_prompts["v1.2"]["cause_tags"]
    assert "Focus on the primary mission area first" in enhanced_text, \
        f"Expected enhancement string in cause_tags, got: {enhanced_text}"


def test_improvement_reasoning_is_captured(test_db, enrich_config, tmp_path):
    """Test that improvement reasoning is captured and human-readable."""
    from scripts.prompt_improvement import PromptImprovement

    # Insert low accuracy metrics to build a trend
    cursor = test_db.cursor()
    today = str(date.today())

    # Insert 7 days of metrics
    for i in range(7):
        metric_date = str((date.today() - __import__('datetime').timedelta(days=i)))
        cursor.execute(
            """INSERT INTO quality_log (date, metric_type, value, cohort, prompt_version, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (metric_date, 'cause_tag_accuracy', 0.58 + (i * 0.01), 'All', 'v1.0', f'Day {i}')
        )
    test_db.commit()

    # Use tmp_path for the prompt versions file
    prompt_file = tmp_path / "prompt_versions.json"

    # Create PromptImprovement instance
    improver = PromptImprovement(test_db, enrich_config, str(prompt_file))

    # Generate improved prompt (this will trigger improvement)
    new_version = improver.generate_improved_prompt()

    # Get the reasoning
    reasoning = improver.get_improvement_reasoning()

    # Assert reasoning is not None
    assert reasoning is not None, "Expected reasoning to be captured"

    # Assert reasoning contains key information
    assert "accuracy" in reasoning.lower(), f"Expected 'accuracy' in reasoning, got: {reasoning}"
    assert "0.75" in reasoning or "75%" in reasoning, f"Expected target (0.75 or 75%) in reasoning, got: {reasoning}"
    assert str(date.today()) in reasoning, f"Expected today's date in reasoning, got: {reasoning}"
