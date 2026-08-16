#!/usr/bin/env python3
"""
Setup script for Daanaa nonprofit leader pilot invitations.

Usage:
  # Generate test invitations for specific organizations
  python3 scripts/setup_pilot_invitations.py create 12-3456789 "My Test Org"

  # List all invitations
  python3 scripts/setup_pilot_invitations.py list

  # Generate invitations from CSV file
  python3 scripts/setup_pilot_invitations.py create-batch pilot_orgs.csv
"""

import sys
import os
import sqlite3
import secrets
import uuid
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pilot_invitations_api import create_pilot_invitation, get_invitation_by_code

DB_PATH = os.environ.get('DB_PATH', 'data/merit_registry.db')


def format_ein(ein: str) -> str:
    """Format EIN to XX-XXXXXXX format."""
    ein_digits = ''.join(c for c in ein if c.isdigit())
    if len(ein_digits) != 9:
        raise ValueError(f"EIN must be 9 digits, got {len(ein_digits)}: {ein}")
    return f"{ein_digits[:2]}-{ein_digits[2:]}"


def list_invitations():
    """List all pilot invitations."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT id, ein, organization_name, status,
                   email_opened, signup_started, signup_completed, created_at
            FROM pilot_invitations
            ORDER BY created_at DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("No pilot invitations found.")
            return

        print(f"\n{'EIN':<12} {'Organization':<50} {'Status':<15} {'Opened':<8} {'Started':<8}")
        print("─" * 100)

        for row in rows:
            ein = row['ein']
            name = row['organization_name'][:48]
            status = row['status']
            opened = "✓" if row['email_opened'] else "—"
            started = "✓" if row['signup_started'] else "—"

            print(f"{ein:<12} {name:<50} {status:<15} {opened:<8} {started:<8}")

        # Summary
        total = len(rows)
        opened_count = sum(1 for row in rows if row['email_opened'])
        started_count = sum(1 for row in rows if row['signup_started'])
        completed_count = sum(1 for row in rows if row['signup_completed'])

        print("─" * 100)
        print(f"Total: {total} | Opened: {opened_count} | Started: {started_count} | Completed: {completed_count}")
        print()

    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        print("The pilot invitations table may not exist yet. Create an invitation first.")
        conn.close()


def create_single_invitation(ein: str, org_name: Optional[str] = None):
    """Create a single pilot invitation."""
    try:
        ein = format_ein(ein)
        result = create_pilot_invitation(ein, org_name or "")
        if isinstance(result, tuple):
            print(f"Error: {result[0].get('error')}")
            sys.exit(1)

        print(f"\n✓ Invitation created for {result['organization_name']}")
        print(f"  EIN: {result['ein']}")
        print(f"  Invite code: {result['invite_code']}")
        print(f"  Link: {result['invite_link']}")
        print()

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def create_batch_invitations(csv_file: str):
    """Create pilot invitations from a CSV file."""
    import csv

    if not os.path.exists(csv_file):
        print(f"Error: File not found: {csv_file}")
        sys.exit(1)

    print(f"\nReading invitations from {csv_file}...\n")

    created = 0
    errors = 0

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            ein = (row.get('ein') or '').strip()
            org_name = (row.get('organization_name') or row.get('name') or '').strip()
            email = (row.get('email') or '').strip()

            if not ein:
                print(f"  Row {i}: Skipped (no EIN)")
                continue

            try:
                ein = format_ein(ein)
                result = create_pilot_invitation(ein, org_name, email)

                if isinstance(result, tuple):
                    print(f"  Row {i}: Error — {result[0].get('error')}")
                    errors += 1
                else:
                    print(f"  Row {i}: ✓ {result['organization_name']}")
                    print(f"         Link: {result['invite_link']}")
                    created += 1

            except ValueError as e:
                print(f"  Row {i}: Error — {e}")
                errors += 1

    print(f"\n{created} invitations created, {errors} errors")
    print()


def show_help():
    """Show usage help."""
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1]

    if command == 'list':
        list_invitations()
    elif command == 'create':
        if len(sys.argv) < 3:
            print("Usage: python3 scripts/setup_pilot_invitations.py create <EIN> [organization_name]")
            sys.exit(1)
        ein = sys.argv[2]
        org_name = sys.argv[3] if len(sys.argv) > 3 else None
        create_single_invitation(ein, org_name)
    elif command == 'create-batch':
        if len(sys.argv) < 3:
            print("Usage: python3 scripts/setup_pilot_invitations.py create-batch <csv_file>")
            sys.exit(1)
        create_batch_invitations(sys.argv[2])
    elif command == 'help' or command == '--help' or command == '-h':
        show_help()
    else:
        print(f"Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
