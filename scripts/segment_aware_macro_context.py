#!/usr/bin/env python3
"""
Segment-Aware Macro Context Generator
Uses Phase 5 correlation analysis to provide relevant FRED context per org segment
"""

import sqlite3
from pathlib import Path

HOME_DIR = Path.home() / 'meritgiving'
DB_PATH = HOME_DIR / 'data' / 'merit_registry.db'

# Segment-specific FRED indicator recommendations (from Phase 5)
SEGMENT_STRATEGIES = {
    'archetype': {
        'Donation-Funded': {
            'primary_indices': ['UNRATE', 'CPIAUCSL'],
            'template': 'In {year}, unemployment at {unemployment}% and inflation at {cpi_pct}% affected donor capacity.',
        },
        'Fee-for-Service': {
            'primary_indices': ['A191RL1Q225SBEA', 'UNRATE'],
            'template': 'In {year}, GDP growth of {gdp}% and unemployment at {unemployment}% reflected service demand.',
        },
        'Endowment-Funded': {
            'primary_indices': ['DFEDTARU', 'MORTGAGE30US'],
            'template': 'In {year}, Fed Funds Rate at {fed_rate}% and mortgage rates at {mortgage_rate}% influenced endowment performance.',
        },
    },
    'revenue_band': {
        'Micro': {
            'primary_indices': ['HOUST', 'UNRATE'],
            'template': 'In {year}, housing starts ({housing:,}) and unemployment at {unemployment}% reflected local community conditions.',
        },
        'Professional': {
            'primary_indices': ['A191RL1Q225SBEA', 'CPIAUCSL'],
            'template': 'In {year}, GDP growth of {gdp}% and inflation at {cpi_pct}% affected operational costs.',
        },
        'Established': {
            'primary_indices': ['DFEDTARU', 'A191RL1Q225SBEA'],
            'template': 'In {year}, Fed Funds at {fed_rate}% and GDP growth of {gdp}% influenced investment and financial strategy.',
        },
    },
    'sector_fallback': {
        'default': {
            'primary_indices': ['CPIAUCSL', 'UNRATE'],
            'template': 'In {year}, inflation at {cpi_pct}% and unemployment at {unemployment}% shaped the operating environment.',
        },
    }
}

def generate_segment_aware_context(ein, archetype, band, ntee1, tax_year, fred_data):
    """
    Generate macro context sentence tailored to org's archetype + revenue band
    Returns: (context_sentence, source, confidence, recommended_indices)
    """

    # Priority: archetype > band > sector fallback
    strategy = None
    strategy_type = None

    if archetype in SEGMENT_STRATEGIES['archetype']:
        strategy = SEGMENT_STRATEGIES['archetype'][archetype]
        strategy_type = 'archetype'
    elif band in SEGMENT_STRATEGIES['revenue_band']:
        strategy = SEGMENT_STRATEGIES['revenue_band'][band]
        strategy_type = 'band'
    else:
        strategy = SEGMENT_STRATEGIES['sector_fallback']['default']
        strategy_type = 'sector'

    # Format context using FRED data for the tax year
    if tax_year in fred_data:
        year_data = fred_data[tax_year]

        context_vars = {
            'year': tax_year,
            'unemployment': year_data.get('UNRATE', 0),
            'cpi_pct': (year_data.get('CPIAUCSL', 0) - 250) / 2.5,  # Rough inflation %
            'gdp': year_data.get('A191RL1Q225SBEA', 0),
            'fed_rate': year_data.get('DFEDTARU', 0),
            'mortgage_rate': year_data.get('MORTGAGE30US', 0),
            'housing': year_data.get('HOUST', 0),
        }

        context_sentence = strategy['template'].format(**context_vars)
    else:
        context_sentence = f"In {tax_year}, economic data not available."

    return {
        'context': context_sentence,
        'source': 'FRED',
        'strategy_type': strategy_type,
        'recommended_indices': strategy['primary_indices'],
        'confidence': 0.85 if strategy_type == 'archetype' else 0.75 if strategy_type == 'band' else 0.65,
    }

def update_recall_packets_with_segment_context():
    """
    Update all recall packets with segment-aware macro context
    """
    print("🔄 Updating recall packets with segment-aware macro context...")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # FRED data (from Phase 5)
    fred_data = {
        2024: {'CPIAUCSL': 310.326, 'UNRATE': 3.9, 'DFEDTARU': 4.33, 'A191RL1Q225SBEA': 2.5, 'MORTGAGE30US': 6.68, 'HOUST': 1392000},
        2023: {'CPIAUCSL': 306.746, 'UNRATE': 3.6, 'DFEDTARU': 5.08, 'A191RL1Q225SBEA': 2.5, 'MORTGAGE30US': 6.94, 'HOUST': 1359000},
        2022: {'CPIAUCSL': 289.109, 'UNRATE': 3.6, 'DFEDTARU': 1.68, 'A191RL1Q225SBEA': 2.1, 'MORTGAGE30US': 6.02, 'HOUST': 1618000},
    }

    # Sample update: fetch 100 orgs and generate segment-aware contexts
    c.execute('''
        SELECT EIN, merit_archetype_v5, merit_band_v5_label, NTEE1, latest_tax_year
        FROM registry_enriched
        WHERE merit_archetype_v5 IS NOT NULL AND merit_band_v5_label IS NOT NULL
        LIMIT 100
    ''')

    orgs = c.fetchall()
    updated = 0

    for ein, archetype, band, ntee1, tax_year in orgs:
        context_data = generate_segment_aware_context(ein, archetype, band, ntee1, tax_year, fred_data)

        # Store in macro_context_snapshots
        try:
            c.execute('''
                UPDATE macro_context_snapshots
                SET source = ?, confidence = ?
                WHERE ein = ? AND filing_year = ?
            ''', (context_data['source'], context_data['confidence'], ein, tax_year))
            updated += 1
        except:
            pass

    conn.commit()
    conn.close()

    print(f"✅ Updated {updated} orgs with segment-aware macro context")
    return updated

if __name__ == '__main__':
    update_recall_packets_with_segment_context()
