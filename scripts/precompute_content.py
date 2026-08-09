#!/usr/bin/env python3
"""
Pre-compute static content pages.
Exports: homepage, methodology, sector-health, how-it-works, guides, faqs, about, legal.
Runs on home server weekly; outputs ~50MB.
"""

import sqlite3
import json
import gzip
import os
from pathlib import Path
from datetime import datetime

DB_PATH = os.environ.get("MERIT_DB_PATH", "data/merit_registry.db")
OUTPUT_DIR = os.path.join(os.environ.get("PRECOMPUTE_OUT", "precompute_output"), "content")

# Canonical public-set predicate. Single source of truth lives in
# registry_filters.py — import it so homepage stats can never drift from the
# research snapshot / data-quality gate again. (Homepage stats describe the
# nonprofits a donor can actually find and give a deductible gift to.)
from registry_filters import DEDUCTIBLE_FILTER as DEDUCTIBLE


# NTEE categories for homepage stats
CATEGORIES = [
    ('A', 'Arts, Culture & Humanities'),
    ('B', 'Educational Institutions & Related Activities'),
    ('C', 'Environmental Quality, Protection & Beautification'),
    ('D', 'Animal-Related'),
    ('E', 'Health - General and Rehabilitative'),
    ('F', 'Mental Health, Crisis Intervention'),
    ('G', 'Voluntary Health Associations & Medical Research Institutes'),
    ('H', 'Diseases, Disorders, Medical Disciplines'),
    ('I', 'Medical Specialty Hospitals, Treatment Centers'),
    ('J', 'Nursing, Custodial Care, Hospices'),
    ('K', 'Mental Health & Crisis Intervention'),
    ('L', 'Public Safety, Disaster Preparedness & Relief'),
    ('M', 'Recreation & Sports'),
    ('N', 'Youth Development'),
    ('O', 'Human Services - Multipurpose & Other'),
    ('P', 'Human Services - Multipurpose'),
    ('Q', 'International, Foreign Affairs & Related Organizations'),
    ('R', 'Civil Rights, Social Action & Advocacy'),
    ('S', 'Community Improvement & Capacity Building'),
    ('T', 'Philanthropy, Voluntarism & Grantmaking Foundations'),
    ('U', 'Science and Technology Research Institutes, Services'),
    ('V', 'Social Sciences Research Institutes, Services'),
    ('W', 'Public & Societal Benefit'),
    ('X', 'Religion-Related, Spiritual Development'),
    ('Y', 'Mutual & Membership Benefit Organizations, Other'),
    ('Z', 'Unknown'),
]

# 8 operating models (from Methodology page)
OPERATING_MODELS = [
    {
        'code': 'Direct_Service',
        'name': 'Direct Service',
        'description': 'Directly provides services to beneficiaries (e.g., shelters, clinics, schools)',
    },
    {
        'code': 'Advocacy',
        'name': 'Advocacy & Policy',
        'description': 'Works to influence policy and systemic change',
    },
    {
        'code': 'Grant_Making',
        'name': 'Grant Making',
        'description': 'Provides grants and financial support to other organizations',
    },
    {
        'code': 'Research',
        'name': 'Research & Knowledge',
        'description': 'Conducts research and generates knowledge',
    },
    {
        'code': 'Capacity_Building',
        'name': 'Capacity Building',
        'description': 'Strengthens the capabilities of other organizations and communities',
    },
    {
        'code': 'Network',
        'name': 'Network & Convening',
        'description': 'Connects organizations and stakeholders',
    },
    {
        'code': 'Social_Enterprise',
        'name': 'Social Enterprise',
        'description': 'Generates earned revenue while pursuing mission',
    },
    {
        'code': 'Infrastructure',
        'name': 'Mission Infrastructure',
        'description': 'Provides shared services and infrastructure for other nonprofits',
    },
]


def save_json_gz(filename, data):
    """Save data as gzipped JSON."""
    filepath = Path(OUTPUT_DIR) / filename
    with gzip.open(filepath, 'wt', encoding='utf-8') as f:
        json.dump(data, f, separators=(',', ':'))


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] Pre-computing content pages...")

    # 1. Homepage data
    print("  Generating homepage data...")
    cursor.execute(f"""
        SELECT
            COUNT(*) as total_organizations,
            COUNT(CASE WHEN total_revenue IS NOT NULL THEN 1 END) as with_revenue,
            SUM(CASE WHEN total_revenue IS NOT NULL THEN total_revenue ELSE 0 END) as total_revenue_sum,
            AVG(CASE WHEN total_revenue IS NOT NULL THEN total_revenue ELSE NULL END) as avg_revenue
        FROM registry_enriched WHERE {DEDUCTIBLE}
    """)
    row = cursor.fetchone()
    stats = {
        'total_organizations': row['total_organizations'],
        'with_revenue': row['with_revenue'],
        'total_revenue_sum': row['total_revenue_sum'],
        'avg_revenue': row['avg_revenue'],
    }

    # Top states
    cursor.execute(f"""
        SELECT STATE, COUNT(*) as count
        FROM registry_enriched
        WHERE {DEDUCTIBLE} AND STATE IS NOT NULL
        GROUP BY STATE
        ORDER BY count DESC
        LIMIT 10
    """)
    top_states = [{'STATE': r['STATE'], 'count': r['count']} for r in cursor.fetchall()]
    stats['top_states'] = top_states

    # Category counts
    category_stats = []
    for cat_code, cat_name in CATEGORIES:
        cursor.execute(f"""
            SELECT COUNT(*) as count FROM registry_enriched WHERE {DEDUCTIBLE} AND NTEE1 = ?
        """, (cat_code,))
        count = cursor.fetchone()['count']
        category_stats.append({
            'code': cat_code,
            'name': cat_name,
            'count': count,
        })

    stats['categories'] = category_stats

    # merit_tier distribution removed 2026-08-08 (founder decision, retiring
    # lamp tiers) -- confirmed unconsumed by any frontend page before removal.

    # Reserve health
    cursor.execute(f"""
        SELECT
            COUNT(*) as total_with_reserve,
            COUNT(CASE WHEN months_of_reserve < 0 THEN 1 END) as insolvent,
            COUNT(CASE WHEN months_of_reserve >= 0 AND months_of_reserve < 3 THEN 1 END) as at_risk,
            COUNT(CASE WHEN months_of_reserve >= 3 AND months_of_reserve < 12 THEN 1 END) as minimal,
            COUNT(CASE WHEN months_of_reserve >= 12 THEN 1 END) as healthy
        FROM registry_enriched
        WHERE {DEDUCTIBLE} AND months_of_reserve IS NOT NULL
    """)
    row = cursor.fetchone()
    stats['reserve_health'] = {
        'total': row['total_with_reserve'],
        'insolvent': row['insolvent'],
        'at_risk': row['at_risk'],
        'minimal': row['minimal'],
        'healthy': row['healthy'],
    }

    stats['methodology_version'] = 'v4.0'
    stats['scores_last_updated'] = timestamp

    homepage = {
        'stats': stats,
        'featured': [],  # Will be updated manually
    }
    save_json_gz('homepage.json.gz', homepage)

    # 2. Methodology page
    print("  Generating methodology data...")
    methodology = {
        'version': 'v6.0',
        'scoring_approach': 'Peer-group financial context scoring with cause awareness',
        # Lamp tiers retired 2026-08-08 (founder decision). Replaced with the
        # v6 financial-context levels, matching Methodology2.tsx wording exactly
        # so frontend and precompute-generated content never disagree again --
        # that inconsistency was the reason this file blocked the frontend
        # deploy for the rest of the day.
        'context_levels': [
            {
                'name': 'Full Context',
                'description': 'Compared with organizations of similar type, size, and region.',
            },
            {
                'name': 'Regional Context',
                'description': 'Compared within a broader regional peer group.',
            },
            {
                'name': 'Broad Category',
                'description': 'Compared across a wider category when a closer peer group was too small to be meaningful.',
            },
            {
                'name': 'Archetype Only',
                'description': 'We can describe the kind of work, but the public record does not yet support a peer comparison.',
            },
        ],
        'operating_models': OPERATING_MODELS,
        'metrics': [
            'Financial reserves (months of runway)',
            'Revenue trends',
            'Expense management',
            'Program spending ratio',
            'Peer group comparison',
        ],
    }
    save_json_gz('methodology.json.gz', methodology)

    # 3. Sector health
    print("  Generating sector health data...")
    cursor.execute("""
        SELECT
            NTEE1, COUNT(*) as total_orgs,
            COUNT(CASE WHEN months_of_reserve IS NOT NULL THEN 1 END) as has_reserve,
            AVG(CASE WHEN months_of_reserve IS NOT NULL THEN months_of_reserve ELSE NULL END) as avg_months_reserve,
            COUNT(CASE WHEN months_of_reserve < 0 THEN 1 END) as insolvent,
            COUNT(CASE WHEN months_of_reserve >= 0 AND months_of_reserve < 3 THEN 1 END) as at_risk,
            COUNT(CASE WHEN months_of_reserve >= 3 AND months_of_reserve < 12 THEN 1 END) as minimal,
            COUNT(CASE WHEN months_of_reserve >= 12 THEN 1 END) as healthy,
            AVG(CASE WHEN program_expense_pct IS NOT NULL THEN program_expense_pct ELSE NULL END) as avg_program_pct,
            AVG(CASE WHEN total_revenue IS NOT NULL THEN total_revenue ELSE NULL END) as avg_revenue
        FROM registry_enriched
        WHERE NTEE1 IS NOT NULL AND NTEE1 != '' AND LENGTH(TRIM(NTEE1)) = 1
        GROUP BY NTEE1
    """)

    # Valid NTEE1 codes from CATEGORIES
    valid_codes = {code for code, _ in CATEGORIES}

    sectors = []
    for row in cursor.fetchall():
        code = row['NTEE1']
        # Skip junk rows with invalid codes
        if code not in valid_codes:
            continue

        at_risk_pct = 0
        if row['has_reserve'] > 0:
            at_risk_pct = (row['at_risk'] / row['has_reserve']) * 100

        sector = {
            'code': code,
            'name': dict(CATEGORIES).get(code, 'Uncategorized'),
            'total_orgs': row['total_orgs'],
            'has_reserve': row['has_reserve'],
            'avg_months_reserve': row['avg_months_reserve'],
            'insolvent': row['insolvent'],
            'at_risk': row['at_risk'],
            'minimal': row['minimal'],
            'healthy': row['healthy'],
            'at_risk_pct': at_risk_pct,
            'avg_program_pct': row['avg_program_pct'],
            'avg_revenue': row['avg_revenue'],
        }
        sectors.append(sector)

    sector_health = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'sectors': sectors
    }
    save_json_gz('sector_health.json.gz', sector_health)

    # 4. How it works
    # Lamp journey (Spark -> Blazing tier-advancement narrative) removed
    # 2026-08-08 -- same framing problem fixed on ForNonprofits.tsx: implied an
    # org could "advance" through a public ranking by filing paperwork.
    # /how-it-works redirects to /methodology (App.tsx) and no frontend page
    # currently reads this endpoint's 'journey' field, but scripts/droplet_api.py
    # still serves it directly, so the content is replaced rather than left
    # stale for anyone hitting the API path directly.
    print("  Generating how-it-works data...")
    how_it_works = {
        'steps': [
            {
                'step': 'IRS records, automatically',
                'description': 'Name, location, cause area, and tax-deductible status come from IRS data. Financial details appear once the IRS publishes them.',
            },
            {
                'step': 'Peer financial context, where the record supports it',
                'description': 'Where enough comparable organizations exist, we show how an organization compares with peers doing similar work at a similar scale.',
            },
            {
                'step': 'What an organization can add',
                'description': 'A mission description, website, donation link, and volunteer information -- the details donors most often look for.',
            },
        ],
    }
    save_json_gz('how_it_works.json.gz', how_it_works)

    # 5. Guides (static content)
    print("  Generating guides data...")
    guides = {
        'articles': [
            {
                'title': 'Finding the Right Organization for You',
                'slug': 'finding-right-org',
                'content': 'Use Daanaa to discover nonprofits aligned with your values.',
            },
            {
                'title': 'Understanding Financial Health Ratings',
                'slug': 'understanding-ratings',
                'content': 'Learn how our peer-based scoring reflects organizational stability.',
            },
            {
                'title': 'Maximizing Your Giving Impact',
                'slug': 'maximizing-impact',
                'content': 'Strategies for aligning your gifts with the nonprofits doing the work you care about.',
            },
        ],
    }
    save_json_gz('guides.json.gz', guides)

    # 6. FAQs
    print("  Generating FAQs...")
    faqs = {
        'questions': [
            {
                'q': 'How do you calculate the financial health rating?',
                'a': 'We use peer-group financial context scoring that measures reserves, revenue stability, and expense management relative to similar organizations.',
            },
            {
                'q': 'What if an organization doesn\'t have a rating?',
                'a': 'Some organizations may lack sufficient public financial data. We encourage contacting them directly to learn about their work and financial health.',
            },
            {
                'q': 'Can I give through Daanaa?',
                'a': 'No. Daanaa is a discovery tool. When you find an organization, we link you to their official website. Daanaa does not process donations or collect donor payment information.',
            },
        ],
    }
    save_json_gz('faqs.json.gz', faqs)

    # 7. About
    print("  Generating about page...")
    about = {
        'mission': 'To help donors discover trustworthy nonprofits aligned with their values.',
        'vision': 'A world where every nonprofit has equal visibility, regardless of size.',
        'team': 'Founded by donors frustrated with nonprofit discovery.',
    }
    save_json_gz('about.json.gz', about)

    # 8. Legal
    print("  Generating legal pages...")
    legal = {
        'privacy': 'We respect your privacy. No user data is shared with third parties.',
        'terms': 'Daanaa is provided as-is for informational purposes.',
        'disclosures': 'All data comes from IRS Form 990-N/990-EZ/990 filings and ProPublica.',
    }
    save_json_gz('legal.json.gz', legal)

    conn.close()

    # Summary
    print(f"\n[{datetime.now().isoformat()}] Content pre-compute complete!")
    print(f"  Output: {OUTPUT_DIR}")

    # Estimate size
    total_size = sum(f.stat().st_size for f in Path(OUTPUT_DIR).rglob('*') if f.is_file())
    print(f"  Disk usage: {total_size / 1024 / 1024:.1f} MB")


if __name__ == '__main__':
    main()
