#!/usr/bin/env python3
"""
Manual fix for QA test account Firebase UID linking.

This script provides two approaches:
1. Automatic: Attempts to get Firebase UID from browser login
2. Manual: User provides UID directly

Run: python3 scripts/manual_fix_qa_linking.py
"""

import sqlite3
import sys
import re

def get_firebase_uid_from_user() -> str:
    """Prompt user to provide Firebase UID."""
    print("\n" + "="*70)
    print("Finding Firebase UID for test@testnonprofit.org")
    print("="*70)

    print("\nTo find the Firebase UID, follow these steps:")
    print("\n1. Go to: https://console.firebase.google.com")
    print("2. Select your Daanaa Firebase project")
    print("3. Go to: Authentication → Users")
    print("4. Find: test@testnonprofit.org")
    print("5. Click on the user row")
    print("6. Look for 'User UID' field - copy the entire UID string")
    print("\nOR, if you have the browser dev tools open during login:")
    print("1. Log in to https://daanaa.org/org/login as test@testnonprofit.org")
    print("2. Open browser DevTools (F12)")
    print("3. Go to: Application → Local Storage")
    print("4. Look for key: firebase:authUser:... → Copy the entire value")
    print("5. In the JSON, find the 'uid' field")

    while True:
        uid = input("\nEnter Firebase UID (or 'skip' to cancel): ").strip()
        if uid.lower() == 'skip':
            return None
        if len(uid) > 10 and all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' for c in uid):
            return uid
        print("❌ Invalid UID. UIDs are alphanumeric strings, usually 25-30 characters long.")

def fix_org_claims_manual(email: str, ein: str, firebase_uid: str = None):
    """Manually fix org_claims linking."""

    if not firebase_uid:
        firebase_uid = get_firebase_uid_from_user()
        if not firebase_uid:
            print("\n❌ Cancelled.")
            return False

    print(f"\n{'='*70}")
    print(f"Fixing QA Account Linking")
    print(f"{'='*70}")
    print(f"\nEmail: {email}")
    print(f"EIN: {ein}")
    print(f"Firebase UID: {firebase_uid}")

    # Connect to database
    print(f"\n1. Connecting to database...")
    try:
        db = sqlite3.connect('data/merit_registry.db')
        db.row_factory = sqlite3.Row
        cursor = db.cursor()
        print(f"   ✅ Connected to data/merit_registry.db")
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        return False

    # Check if record already exists
    print(f"\n2. Checking org_claims for EIN {ein}...")
    try:
        cursor.execute(
            'SELECT id, email, firebase_uid, claim_status FROM org_claims WHERE ein=?',
            (ein,)
        )
        existing = cursor.fetchone()

        if existing:
            print(f"   Found existing record:")
            print(f"     - Email: {existing['email']}")
            print(f"     - Firebase UID: {existing['firebase_uid']}")
            print(f"     - Status: {existing['claim_status']}")

            # Update with new firebase_uid
            print(f"\n3. Updating Firebase UID for existing record...")
            cursor.execute(
                'UPDATE org_claims SET firebase_uid=?, email=? WHERE ein=?',
                (firebase_uid, email, ein)
            )
            db.commit()
            print(f"   ✅ Updated org_claims record")
        else:
            print(f"   No existing record found for EIN {ein}")
            print(f"\n3. Creating new org_claims record...")

            # Insert new record
            try:
                cursor.execute('''
                    INSERT INTO org_claims
                    (ein, email, firebase_uid, claim_status, claim_verified_at, created_at)
                    VALUES (?, ?, ?, 'verified', datetime('now'), datetime('now'))
                ''', (ein, email, firebase_uid))
                db.commit()
                print(f"   ✅ Created org_claims record")
            except sqlite3.IntegrityError as e:
                print(f"   ⚠️  Record may already exist: {e}")
                print(f"   Attempting update instead...")
                cursor.execute(
                    'UPDATE org_claims SET firebase_uid=?, email=? WHERE ein=?',
                    (firebase_uid, email, ein)
                )
                db.commit()
                print(f"   ✅ Updated org_claims record")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        db.close()
        return False

    # Verify the link
    print(f"\n4. Verifying the link...")
    try:
        cursor.execute(
            'SELECT ein FROM org_claims WHERE ein=? AND firebase_uid=? AND claim_status IN ("active", "verified")',
            (ein, firebase_uid)
        )
        verified = cursor.fetchone()

        if verified:
            print(f"   ✅ Link verified! EIN {ein} is now linked to Firebase UID {firebase_uid}")
        else:
            print(f"   ❌ Link verification failed")
            db.close()
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        db.close()
        return False

    # Check registry record exists
    print(f"\n5. Verifying nonprofit record in registry...")
    try:
        cursor.execute(
            'SELECT ein, organization_name FROM registry_enriched WHERE ein=?',
            (ein,)
        )
        org = cursor.fetchone()

        if org:
            print(f"   ✅ Found organization: {org['organization_name']}")
        else:
            print(f"   ⚠️  Organization not found in registry (may need to be created)")
    except Exception as e:
        print(f"   ⚠️  Error checking registry: {e}")

    db.close()

    print(f"\n{'='*70}")
    print(f"✅ QA Account Linking Fixed!")
    print(f"{'='*70}")
    print(f"\nTest account {email} is now linked to EIN {ein}")
    print(f"Firebase UID: {firebase_uid}")
    print(f"\n📋 Next steps:")
    print(f"1. Go to: https://daanaa.org/org/login")
    print(f"2. Login with: test@testnonprofit.org / TestNonprofit2024!")
    print(f"3. You should now see the nonprofit dashboard")
    print(f"4. Check: volunteer hours, profile edit, all features")
    print()

    return True

if __name__ == '__main__':
    email = 'test@testnonprofit.org'
    ein = '123456789'

    # Check if UID provided as command line argument
    firebase_uid = sys.argv[1] if len(sys.argv) > 1 else None

    print(f"\n📋 QA Account Firebase UID Linking")
    print(f"Email: {email}")
    print(f"EIN: {ein}")

    if firebase_uid:
        print(f"Firebase UID (provided): {firebase_uid}")

    success = fix_org_claims_manual(email, ein, firebase_uid)
    sys.exit(0 if success else 1)
