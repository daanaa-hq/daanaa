#!/usr/bin/env python3
"""
Add missing columns to registry_enriched for storing GitHub and skills.sh discovery results.
Run once to migrate the schema.
"""

import sqlite3
from pathlib import Path

DB = Path.home() / 'meritgiving' / 'data' / 'merit_registry.db'

def add_columns():
    """Add github_repo and skills_sh_profile columns if they don't exist."""
    conn = sqlite3.connect(str(DB))
    cursor = conn.cursor()

    # Get existing columns
    cursor.execute("PRAGMA table_info(registry_enriched)")
    existing_cols = [row[1] for row in cursor.fetchall()]

    added = False

    # Add github_repo column
    if 'github_repo' not in existing_cols:
        try:
            cursor.execute("""
                ALTER TABLE registry_enriched
                ADD COLUMN github_repo TEXT
            """)
            print("✅ Added github_repo column")
            added = True
        except Exception as e:
            print(f"⚠️  Could not add github_repo: {e}")

    # Add skills_sh_profile column
    if 'skills_sh_profile' not in existing_cols:
        try:
            cursor.execute("""
                ALTER TABLE registry_enriched
                ADD COLUMN skills_sh_profile TEXT
            """)
            print("✅ Added skills_sh_profile column")
            added = True
        except Exception as e:
            print(f"⚠️  Could not add skills_sh_profile: {e}")

    # Add donate_button_text column (for storing button label)
    if 'donate_button_text' not in existing_cols:
        try:
            cursor.execute("""
                ALTER TABLE registry_enriched
                ADD COLUMN donate_button_text TEXT
            """)
            print("✅ Added donate_button_text column")
            added = True
        except Exception as e:
            print(f"⚠️  Could not add donate_button_text: {e}")

    if added:
        conn.commit()
        print("✅ Schema migration complete")
    else:
        print("ℹ️  No columns needed to be added (already exist)")

    conn.close()

if __name__ == '__main__':
    add_columns()
