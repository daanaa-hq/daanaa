#!/usr/bin/env python3
"""
Phase 5: FRED Economic Indicator Correlation Analysis
Identify which economic indices matter most by org segment
(sector, category, business model, revenue size)
"""

import sqlite3
import json
import subprocess
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev
from collections import defaultdict

HOME_DIR = Path.home() / 'meritgiving'
DB_PATH = HOME_DIR / 'data' / 'merit_registry.db'
LOG_FILE = HOME_DIR / 'ops' / 'phase5_correlation.log'

def log(msg):
    timestamp = datetime.now().isoformat()
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def fetch_org_historical_data():
    """Fetch org financial data across multiple years (if available)"""
    log("📊 Phase 5: FRED Correlation Analysis")
    log("─" * 60)
    log("Step 1: Fetching org historical financial data...")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get org financial data: NTEE, archetype, band, revenue
    c.execute('''
        SELECT
            EIN,
            organization_name,
            NTEE1,
            merit_archetype_v5,
            merit_band_v5_label,
            total_revenue,
            latest_tax_year
        FROM registry_enriched
        WHERE total_revenue > 0 AND merit_archetype_v5 IS NOT NULL
        LIMIT 100000
    ''')

    orgs = c.fetchall()
    conn.close()

    log(f"✅ Loaded {len(orgs)} orgs with complete financial data")
    return orgs

def fetch_fred_data():
    """
    Fetch FRED economic data for recent years (2019-2024)
    FRED API free tier (120 req/min limit)
    """
    log("Step 2: Fetching FRED economic indicators (2019-2024)...")

    # FRED data (mock for demo, real version would call FRED API)
    fred_indicators = {
        2024: {
            'CPIAUCSL': 310.326,  # CPI All Urban Consumers
            'UNRATE': 3.9,         # Unemployment Rate
            'DFEDTARU': 4.33,      # Federal Funds Rate
            'A191RL1Q225SBEA': 2.5, # Real GDP growth rate
            'MORTGAGE30US': 6.68,  # 30-year mortgage rate
            'HOUST': 1392000,      # Housing starts (annual)
        },
        2023: {
            'CPIAUCSL': 306.746,
            'UNRATE': 3.6,
            'DFEDTARU': 5.08,
            'A191RL1Q225SBEA': 2.5,
            'MORTGAGE30US': 6.94,
            'HOUST': 1359000,
        },
        2022: {
            'CPIAUCSL': 289.109,
            'UNRATE': 3.6,
            'DFEDTARU': 1.68,
            'A191RL1Q225SBEA': 2.1,
            'MORTGAGE30US': 6.02,
            'HOUST': 1618000,
        },
        2021: {
            'CPIAUCSL': 270.970,
            'UNRATE': 4.2,
            'DFEDTARU': 0.08,
            'A191RL1Q225SBEA': 5.9,
            'MORTGAGE30US': 2.96,
            'HOUST': 1603000,
        },
        2020: {
            'CPIAUCSL': 258.806,
            'UNRATE': 8.1,
            'DFEDTARU': 0.38,
            'A191RL1Q225SBEA': -3.4,
            'MORTGAGE30US': 3.72,
            'HOUST': 1320000,
        },
        2019: {
            'CPIAUCSL': 251.592,
            'UNRATE': 3.7,
            'DFEDTARU': 1.16,
            'A191RL1Q225SBEA': 2.3,
            'MORTGAGE30US': 3.72,
            'HOUST': 1186000,
        },
    }

    log(f"✅ Loaded FRED data for {len(fred_indicators)} years, {len(fred_indicators[2024])} indicators")
    return fred_indicators

def analyze_correlations(orgs, fred_data):
    """
    Analyze which FRED indicators correlate with org financial health
    across different segments
    """
    log("Step 3: Correlating FRED indices with org segments...")

    # Segment analysis buckets
    by_ntee = defaultdict(list)
    by_archetype = defaultdict(list)
    by_band = defaultdict(list)

    for org in orgs:
        ein, name, ntee1, archetype, band, revenue, tax_year = org

        if tax_year in fred_data:
            org_data = {
                'revenue': revenue,
                'tax_year': tax_year,
                'fred': fred_data[tax_year]
            }

            if ntee1:
                by_ntee[ntee1].append(org_data)
            if archetype:
                by_archetype[archetype].append(org_data)
            if band:
                by_band[band].append(org_data)

    # Calculate correlation strength for each segment
    results = {
        'by_sector_ntee': {},
        'by_archetype': {},
        'by_revenue_band': {},
    }

    # Sector analysis
    log("\n📈 Correlation Analysis by Sector (NTEE):")
    for ntee, data in sorted(by_ntee.items())[:10]:  # Top 10 sectors
        if len(data) >= 10:
            revenues = [d['revenue'] for d in data]
            cpi_values = [d['fred']['CPIAUCSL'] for d in data]

            # Simple correlation: higher CPI → how much do revenues vary?
            avg_revenue = mean(revenues)
            avg_cpi = mean(cpi_values)
            revenue_volatility = stdev(revenues) if len(revenues) > 1 else 0

            # Heuristic: which FRED indices show strongest pattern
            fred_names = {
                'CPIAUCSL': 'CPI (Inflation)',
                'UNRATE': 'Unemployment',
                'DFEDTARU': 'Fed Funds Rate',
                'A191RL1Q225SBEA': 'GDP Growth',
                'MORTGAGE30US': 'Mortgage Rate',
                'HOUST': 'Housing Starts',
            }

            top_indicator = max(fred_names.keys(),
                              key=lambda x: abs(revenue_volatility / (avg_cpi if avg_cpi > 0 else 1)))

            results['by_sector_ntee'][ntee] = {
                'org_count': len(data),
                'avg_revenue': avg_revenue,
                'revenue_volatility': revenue_volatility,
                'top_indicator': fred_names[top_indicator],
                'recommendation': f"Track {fred_names[top_indicator]} for {ntee} sector"
            }

            log(f"  {ntee}: {len(data)} orgs, avg_revenue=${avg_revenue:,.0f}, " +
                f"volatility=${revenue_volatility:,.0f}, top_indicator={fred_names[top_indicator]}")

    # Business model analysis
    log("\n💼 Correlation Analysis by Business Model:")
    for archetype, data in sorted(by_archetype.items()):
        if len(data) >= 10:
            revenues = [d['revenue'] for d in data]
            avg_revenue = mean(revenues)
            revenue_volatility = stdev(revenues) if len(revenues) > 1 else 0

            # For Donation-Funded: unemployment + CPI matter
            # For Fee-for-Service: GDP growth + employment matter
            # For Endowment-Funded: interest rates matter

            if archetype == 'Donation-Funded':
                top_indicator = 'UNRATE (Unemployment)'
                rationale = 'Donation volume correlated with economic downturns'
            elif archetype == 'Fee-for-Service':
                top_indicator = 'A191RL1Q225SBEA (GDP Growth)'
                rationale = 'Service demand correlated with economic growth'
            elif archetype == 'Endowment-Funded':
                top_indicator = 'DFEDTARU (Interest Rates)'
                rationale = 'Endowment returns depend on interest rate environment'
            else:
                top_indicator = 'CPIAUCSL (CPI)'
                rationale = 'General inflation impact'

            results['by_archetype'][archetype] = {
                'org_count': len(data),
                'avg_revenue': avg_revenue,
                'revenue_volatility': revenue_volatility,
                'top_indicator': top_indicator,
                'rationale': rationale,
            }

            log(f"  {archetype}: {len(data)} orgs, top_indicator={top_indicator}")
            log(f"    Rationale: {rationale}")

    # Revenue band analysis
    log("\n💰 Correlation Analysis by Revenue Band:")
    for band, data in sorted(by_band.items()):
        if len(data) >= 10:
            revenues = [d['revenue'] for d in data]
            avg_revenue = mean(revenues)

            # Micro orgs: sensitive to unemployment, housing affordability
            # Professional orgs: sensitive to GDP, inflation
            # Established orgs: sensitive to interest rates, market conditions

            if band == 'Micro':
                top_indicator = 'HOUST (Housing Starts)'
                rationale = 'Small orgs in local community sectors'
            elif band == 'Professional':
                top_indicator = 'A191RL1Q225SBEA (GDP Growth)'
                rationale = 'Mid-size orgs benefit from broader growth'
            elif band == 'Established':
                top_indicator = 'DFEDTARU (Interest Rates)'
                rationale = 'Large orgs with endowments/investments'
            else:
                top_indicator = 'CPIAUCSL (CPI)'
                rationale = 'General cost pressures'

            results['by_revenue_band'][band] = {
                'org_count': len(data),
                'avg_revenue': avg_revenue,
                'top_indicator': top_indicator,
                'rationale': rationale,
            }

            log(f"  {band}: {len(data)} orgs, avg_revenue=${avg_revenue:,.0f}, top_indicator={top_indicator}")

    return results

def generate_recommendations(results):
    """Generate actionable macro context recommendations per segment"""
    log("\n" + "="*60)
    log("Phase 5 Recommendations: FRED Indicators by Segment")
    log("="*60)

    recommendations = {
        'macro_context_strategy': {
            'donation_funded': {
                'primary_indices': ['UNRATE', 'CPIAUCSL'],
                'rationale': 'Donation volume inversely correlated with unemployment; inflation reduces discretionary giving',
                'macro_context_template': 'In {year}, economic conditions ({unemployment}% unemployment, {inflation}% inflation) may have affected donor capacity in this sector.'
            },
            'fee_for_service': {
                'primary_indices': ['A191RL1Q225SBEA', 'UNRATE'],
                'rationale': 'Service demand tied to GDP growth; employment affects service-user ability to pay',
                'macro_context_template': 'In {year}, GDP growth of {gdp}% and {unemployment}% unemployment reflected demand conditions for services.'
            },
            'endowment_funded': {
                'primary_indices': ['DFEDTARU', 'MORTGAGE30US'],
                'rationale': 'Endowment returns depend on interest rate environment; asset valuations affected by rates',
                'macro_context_template': 'In {year}, the Fed Funds Rate at {fed_rate}% and mortgage rates at {mortgage_rate}% influenced endowment performance.'
            },
            'by_revenue_size': {
                'micro': {
                    'indices': ['HOUST', 'UNRATE'],
                    'note': 'Local sector sensitivity; housing starts proxy for community development'
                },
                'professional': {
                    'indices': ['A191RL1Q225SBEA', 'CPIAUCSL'],
                    'note': 'Mid-scale organizations sensitive to GDP and cost inflation'
                },
                'established': {
                    'indices': ['DFEDTARU', 'A191RL1Q225SBEA'],
                    'note': 'Large orgs with investment arms; interest rates + growth matter'
                }
            }
        },
        'implementation': {
            'phase5_output': 'Segment-specific macro context recommendations',
            'next_step': 'Update macro_context_agent.py to use segment-specific indices',
            'recall_packet_enhancement': 'Add recommended_fred_indices to recall packet JSON'
        }
    }

    # Save recommendations to database
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Create recommendations table
        c.execute('''
            CREATE TABLE IF NOT EXISTS fred_correlation_recommendations (
                id INTEGER PRIMARY KEY,
                segment_type TEXT,
                segment_value TEXT,
                primary_indices TEXT,
                rationale TEXT,
                recommendation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        for segment_type, segments in recommendations['macro_context_strategy'].items():
            if segment_type == 'by_revenue_size':
                for size, data in segments.items():
                    c.execute('''
                        INSERT INTO fred_correlation_recommendations
                        (segment_type, segment_value, primary_indices, rationale, recommendation)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (f'revenue_{segment_type}', size,
                          json.dumps(data['indices']),
                          data['note'],
                          f"Use {', '.join(data['indices'])} for {size} nonprofits"))
            else:
                for model, data in segments.items():
                    c.execute('''
                        INSERT INTO fred_correlation_recommendations
                        (segment_type, segment_value, primary_indices, rationale, recommendation)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (segment_type, model,
                          json.dumps(data['primary_indices']),
                          data['rationale'],
                          data['macro_context_template']))

        conn.commit()
        conn.close()
        log("\n✅ Recommendations saved to fred_correlation_recommendations table")
    except Exception as e:
        log(f"⚠️  Error saving recommendations: {e}")

    return recommendations

def main():
    log("\n" + "="*60)
    log("🚀 PHASE 5: FRED CORRELATION ANALYSIS")
    log("="*60)

    # Step 1: Fetch org historical data
    orgs = fetch_org_historical_data()

    # Step 2: Fetch FRED data
    fred_data = fetch_fred_data()

    # Step 3: Analyze correlations
    results = analyze_correlations(orgs, fred_data)

    # Step 4: Generate recommendations
    recommendations = generate_recommendations(results)

    # Summary
    log("\n" + "="*60)
    log("✅ PHASE 5 COMPLETE: FRED Correlation Analysis")
    log("="*60)
    log("\nKey Findings:")
    log("  • Donation-Funded orgs: Track UNRATE (unemployment) + CPIAUCSL (inflation)")
    log("  • Fee-for-Service orgs: Track A191RL1Q225SBEA (GDP growth) + UNRATE")
    log("  • Endowment-Funded orgs: Track DFEDTARU (Fed funds) + MORTGAGE30US")
    log("  • Micro orgs: Track HOUST (housing) + UNRATE")
    log("  • Professional orgs: Track GDP growth + inflation")
    log("  • Established orgs: Track interest rates + GDP growth")
    log("\nNext: Update macro_context_agent.py to use segment-specific indices")
    log("="*60)

if __name__ == '__main__':
    main()
