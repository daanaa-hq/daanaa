#!/usr/bin/env python3
"""Seed guild (partner) data for member benefits system."""
import sqlite3
from datetime import datetime

DB_PATH = '/home/akbar/meritgiving/data/merit_registry.db'

GUILDS = [
    {
        'name': 'Salesforce Nonprofit Cloud',
        'slug': 'salesforce-nonprofit',
        'website': 'https://www.salesforce.com/nonprofit/',
    },
    {
        'name': 'Google for Nonprofits',
        'slug': 'google-nonprofits',
        'website': 'https://www.google.com/nonprofits/',
    },
    {
        'name': 'HubSpot for Good',
        'slug': 'hubspot-for-good',
        'website': 'https://www.hubspot.com/nonprofits',
    },
    {
        'name': 'Stripe for Nonprofits',
        'slug': 'stripe-nonprofits',
        'website': 'https://stripe.com/nonprofits',
    },
    {
        'name': 'Slack for Nonprofits',
        'slug': 'slack-nonprofits',
        'website': 'https://www.slack.com/nonprofits',
    },
    {
        'name': 'Mailchimp for Good',
        'slug': 'mailchimp-for-good',
        'website': 'https://mailchimp.com/nonprofits/',
    },
    {
        'name': 'Canva for Nonprofits',
        'slug': 'canva-nonprofits',
        'website': 'https://www.canva.com/nonprofits/',
    },
    {
        'name': 'Asana for Good',
        'slug': 'asana-for-good',
        'website': 'https://asana.com/campaigns/nonprofit',
    },
    {
        'name': 'Constant Contact Nonprofit',
        'slug': 'constant-contact-nonprofit',
        'website': 'https://www.constantcontact.com/nonprofit',
    },
    {
        'name': 'Adobe for Nonprofits',
        'slug': 'adobe-nonprofits',
        'website': 'https://www.adobe.com/nonprofits.html',
    },
]

BENEFITS = {
    'free': [
        ('Free tier access', 'Community support and basic features'),
        ('Nonprofit badge', 'Display on Daanaa directory'),
    ],
    'pro': [
        ('Priority support', 'Email support within 24 hours'),
        ('Advanced analytics', 'Usage reports and insights'),
        ('Custom branding', 'White-label options for partner'),
    ],
    'enterprise': [
        ('Dedicated account manager', 'One-on-one partnership support'),
        ('Custom integrations', 'API access and webhooks'),
        ('SLA guarantee', '99.9% uptime guarantee'),
        ('Training & onboarding', 'Hands-on implementation support'),
    ],
}

def seed_guilds():
    """Insert guild, membership, and benefits data."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # Insert guilds
        for guild in GUILDS:
            c.execute(
                'INSERT INTO guild (name, slug, website) VALUES (?, ?, ?)',
                (guild['name'], guild['slug'], guild['website'])
            )
        conn.commit()
        print(f'✅ Inserted {len(GUILDS)} guilds')

        # Insert benefits for each guild
        c.execute('SELECT guild_id, name FROM guild')
        guilds = c.fetchall()

        total_benefits = 0
        for guild_id, guild_name in guilds:
            for tier, features in BENEFITS.items():
                for feature_name, description in features:
                    c.execute(
                        'INSERT INTO guild_benefits (guild_id, tier, feature_name, description) VALUES (?, ?, ?, ?)',
                        (guild_id, tier, feature_name, description)
                    )
                    total_benefits += 1

        conn.commit()
        print(f'✅ Inserted {total_benefits} benefits ({len(BENEFITS)} tiers × {len(GUILDS)} guilds)')

        # Test: Show guilds
        c.execute('SELECT count(*) FROM guild')
        guild_count = c.fetchone()[0]
        print(f'📊 Total guilds in database: {guild_count}')

        # Test: Show benefits by tier
        for tier in ['free', 'pro', 'enterprise']:
            c.execute('SELECT count(*) FROM guild_benefits WHERE tier=?', (tier,))
            count = c.fetchone()[0]
            print(f'   {tier.upper()}: {count} benefits')

    finally:
        conn.close()

if __name__ == '__main__':
    seed_guilds()
    print('\n✅ Guild seed complete')
