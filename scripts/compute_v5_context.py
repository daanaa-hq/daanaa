#!/usr/bin/env python3
"""
Compute v5 financial context for all orgs:
- Archetype (Donation-Funded, Fee-for-Service, Endowment-Funded, Membership, Mutual-Benefit)
- Health signal (HEALTHY, STABLE, CAUTION based on months_of_reserve)
- Peer group (archetype + revenue band)
- Peer count (size of peer cell)
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

DB_PATH = Path.home() / "meritgiving" / "data" / "merit_registry.db"

# NTEE1 → v5 Archetype mapping (from prior analysis)
NTEE_TO_ARCHETYPE = {
    'A': 'Donation-Funded',      # Arts
    'B': 'Donation-Funded',      # Education
    'C': 'Donation-Funded',      # Environment
    'D': 'Donation-Funded',      # Animal Welfare
    'E': 'Fee-for-Service',      # Health Care
    'F': 'Donation-Funded',      # Mental Health
    'G': 'Fee-for-Service',      # Disease Research
    'H': 'Fee-for-Service',      # Medical Research
    'I': 'Donation-Funded',      # Crime & Legal
    'J': 'Fee-for-Service',      # Employment
    'K': 'Donation-Funded',      # Food & Agriculture
    'L': 'Donation-Funded',      # Housing
    'M': 'Donation-Funded',      # Public Safety
    'N': 'Donation-Funded',      # Recreation
    'O': 'Donation-Funded',      # Youth Development
    'P': 'Donation-Funded',      # Human Services
    'Q': 'Donation-Funded',      # International
    'R': 'Donation-Funded',      # Civil Rights
    'S': 'Donation-Funded',      # Community
    'T': 'Endowment-Funded',     # Philanthropy
    'U': 'Fee-for-Service',      # Science & Tech
    'V': 'Donation-Funded',      # Social Science
    'W': 'Mutual-Benefit',       # Public Benefit
    'X': 'Donation-Funded',      # Religion
    'Y': 'Mutual-Benefit',       # Mutual Benefit
    'Z': 'Donation-Funded',      # Unknown
}

# Revenue bands: based on total_revenue
def revenue_band(revenue):
    """Assign revenue band."""
    if revenue is None or revenue <= 0:
        return None
    if revenue < 150000:
        return 'Micro'
    elif revenue < 700000:
        return 'Professional'
    else:
        return 'Established'

def health_signal(months_of_reserve):
    """Assign health signal based on months of reserve."""
    if months_of_reserve is None:
        return None
    if months_of_reserve >= 12:
        return 'HEALTHY'
    elif months_of_reserve >= 6:
        return 'STABLE'
    else:
        return 'CAUTION'

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def main():
    log("=== COMPUTE V5 CONTEXT ===")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Count orgs to process
    total = cur.execute("SELECT COUNT(*) FROM registry_enriched WHERE NTEE1 IS NOT NULL").fetchone()[0]
    log(f"Orgs to process: {total:,}")

    # First pass: compute archetypes and health signals for all with NTEE1
    log("Pass 1: Computing archetype, health signal, revenue band")
    updated = 0
    peer_cells = defaultdict(lambda: {'count': 0, 'orgs': []})

    cur.execute("""
    SELECT EIN, NTEE1, total_revenue, months_of_reserve
    FROM registry_enriched
    WHERE NTEE1 IS NOT NULL
    """)

    batch = []
    for i, row in enumerate(cur.fetchall(), 1):
        ein = row['EIN']
        ntee1 = row['NTEE1']
        revenue = row['total_revenue']
        mor = row['months_of_reserve']

        archetype = NTEE_TO_ARCHETYPE.get(ntee1, 'Donation-Funded')
        band = revenue_band(revenue)
        health = health_signal(mor)

        # Peer group is archetype + revenue band
        peer_group = f"{archetype}:{band}" if band else archetype

        # Track peer group membership
        peer_cells[peer_group]['count'] += 1
        peer_cells[peer_group]['orgs'].append(ein)

        batch.append((archetype, band, health, peer_group, ein))

        if i % 50000 == 0:
            log(f"  {i:,} / {total:,} computed")

    # Second pass: update database with archetype, health, peer_group
    log("Pass 2: Updating database with v5 context")
    for ein, archetype, band, health, peer_group in [
        (ein, arch, band, health, peer_grp)
        for arch, band, health, peer_grp, ein in batch
    ]:
        conn.execute("""
        UPDATE registry_enriched
        SET merit_archetype_v5 = ?,
            merit_archetype_v5_label = ?,
            merit_band_v5_label = ?,
            merit_health_signal_v5 = ?,
            merit_peer_group_v5 = ?
        WHERE EIN = ?
        """, (
            list(NTEE_TO_ARCHETYPE.values()).index(archetype) if archetype in NTEE_TO_ARCHETYPE.values() else 0,
            archetype,
            band,
            health,
            peer_group,
            ein
        ))
        updated += 1

        if updated % 50000 == 0:
            log(f"  {updated:,} / {total:,} updated")
            conn.commit()

    conn.commit()
    log(f"Updated: {updated:,} orgs")

    # Third pass: compute peer counts for each org
    log("Pass 3: Computing peer counts")
    peer_count_updated = 0

    for peer_group, cell_data in peer_cells.items():
        peer_count = cell_data['count']
        for ein in cell_data['orgs']:
            conn.execute("""
            UPDATE registry_enriched
            SET merit_peer_count_v5 = ?
            WHERE EIN = ?
            """, (peer_count, ein))
            peer_count_updated += 1

        if peer_count_updated % 50000 == 0:
            log(f"  {peer_count_updated:,} peer counts set")
            conn.commit()

    conn.commit()
    log(f"Peer counts set: {peer_count_updated:,}")

    # Summary stats
    log("\n=== SUMMARY ===")
    by_archetype = conn.execute("""
    SELECT merit_archetype_v5_label, COUNT(*) as count
    FROM registry_enriched
    WHERE merit_archetype_v5_label IS NOT NULL
    GROUP BY merit_archetype_v5_label
    ORDER BY count DESC
    """).fetchall()

    for arch, count in by_archetype:
        log(f"  {arch}: {count:,}")

    by_health = conn.execute("""
    SELECT merit_health_signal_v5, COUNT(*) as count
    FROM registry_enriched
    WHERE merit_health_signal_v5 IS NOT NULL
    GROUP BY merit_health_signal_v5
    ORDER BY count DESC
    """).fetchall()

    log("\nHealth signals:")
    for health, count in by_health:
        log(f"  {health}: {count:,}")

    conn.close()
    log("\n✓ v5 context computation complete")

if __name__ == "__main__":
    main()
