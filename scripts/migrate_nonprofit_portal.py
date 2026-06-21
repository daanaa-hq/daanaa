#!/usr/bin/env python3
"""Create tables for nonprofit portal (accounts, letters, credits)."""

import sqlite3
import sys

DB_PATH = 'data/merit_registry.db'

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # nonprofit_accounts: org signup/login
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nonprofit_accounts (
            id TEXT PRIMARY KEY,
            ein TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            opted_in_letters BOOLEAN DEFAULT 0,
            verified BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # nonprofit_letters: generated letters
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nonprofit_letters (
            id TEXT PRIMARY KEY,
            nonprofit_ein TEXT NOT NULL,
            donor_name TEXT NOT NULL,
            amount REAL NOT NULL,
            donation_date TEXT NOT NULL,
            letter_pdf_url TEXT,
            generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'generated',
            FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein)
        )
    ''')

    # letter_credits: $10 purchases = 100 letters
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS letter_credits (
            id TEXT PRIMARY KEY,
            nonprofit_ein TEXT NOT NULL,
            letters_remaining INTEGER DEFAULT 100,
            purchased_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT,
            FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein)
        )
    ''')

    # nonprofit_letter_requests: donation approval queue
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nonprofit_letter_requests (
            id TEXT PRIMARY KEY,
            nonprofit_ein TEXT NOT NULL,
            wallet_funding_id TEXT NOT NULL,
            donor_name TEXT NOT NULL,
            amount REAL NOT NULL,
            donation_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            approved_by TEXT,
            approved_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (nonprofit_ein) REFERENCES nonprofit_accounts(ein),
            FOREIGN KEY (wallet_funding_id) REFERENCES wallet_funding_history(id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✓ Migration complete: nonprofit portal tables created")

if __name__ == '__main__':
    migrate()
