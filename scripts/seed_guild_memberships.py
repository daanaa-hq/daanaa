#!/usr/bin/env python3
"""Seed guild memberships for test organizations."""
import sqlite3
from datetime import datetime

DB_PATH = '/home/akbar/meritgiving/data/merit_registry.db'

# Map of org EINs to (guild_slug, tier) assignments
# These are real nonprofits from the registry
MEMBERSHIPS = [
    ('360822808', 'salesforce-nonprofit', 'enterprise'),  # American Red Cross
    ('135630589', 'google-nonprofits', 'pro'),            # Nature Conservancy
    ('236527919', 'hubspot-for-good', 'free'),            # YMCA
    ('133921386', 'stripe-nonprofits', 'enterprise'),     # Boys & Girls Clubs
    ('943412822', 'slack-nonprofits', 'pro'),             # Room to Read
    ('522520273', 'mailchimp-for-good', 'free'),          # Girl Guides
    ('113954388', 'canva-nonprofits', 'pro'),             # World Wildlife Fund
    ('581600141', 'asana-for-good', 'free'),              # Feeding America
    ('954159012', 'constant-contact-nonprofit', 'pro'),   # Salvation Army
    ('346999490', 'adobe-nonprofits', 'enterprise'),      # Habitat for Humanity
]

def seed_memberships():
    """Insert guild membership data."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # Get guild_id for each slug
        guild_map = {}
        c.execute('SELECT guild_id, slug FROM guild')
        for guild_id, slug in c.fetchall():
            guild_map[slug] = guild_id

        # Assign orgs to guilds
        inserted = 0
        for ein, guild_slug, tier in MEMBERSHIPS:
            guild_id = guild_map.get(guild_slug)
            if not guild_id:
                print(f'⚠️  Guild {guild_slug} not found, skipping')
                continue

            try:
                c.execute(
                    'INSERT INTO guild_membership (ein, guild_id, tier) VALUES (?, ?, ?)',
                    (ein, guild_id, tier)
                )
                inserted += 1
            except sqlite3.IntegrityError:
                # Already exists
                pass

        conn.commit()
        print(f'✅ Assigned {inserted} orgs to guilds')

        # Show membership summary
        c.execute('''
            SELECT g.name, COUNT(*) as count
            FROM guild_membership gm
            JOIN guild g ON gm.guild_id = g.guild_id
            GROUP BY g.guild_id
            ORDER BY count DESC
        ''')
        for guild_name, count in c.fetchall():
            print(f'   {guild_name}: {count} members')

    finally:
        conn.close()

if __name__ == '__main__':
    seed_memberships()
    print('\n✅ Guild membership seed complete')
