import sqlite3

DB = "data/merit_registry.db"

with sqlite3.connect(DB) as conn:
    c = conn.cursor()
    
    print("=== Building Revenue Percentile Engine ===")
    
    # Create percentile table
    c.execute("DROP TABLE IF EXISTS revenue_percentiles")
    c.execute("""
        CREATE TABLE revenue_percentiles AS
        SELECT 
            EIN,
            NAME,
            scope,
            NTEE1,
            NTEECC,
            STATE,
            CITY,
            total_revenue,
            -- Percentile within NTEE1 (0-100)
            ROUND(
                100.0 * (RANK() OVER (PARTITION BY NTEE1 ORDER BY total_revenue) - 1) / 
                NULLIF(COUNT(*) OVER (PARTITION BY NTEE1) - 1, 0),
                1
            ) as ntee1_percentile,
            -- Percentile within NTEE1 + State
            ROUND(
                100.0 * (RANK() OVER (PARTITION BY NTEE1, STATE ORDER BY total_revenue) - 1) / 
                NULLIF(COUNT(*) OVER (PARTITION BY NTEE1, STATE) - 1, 0),
                1
            ) as state_ntee1_percentile,
            -- Rank within NTEE1
            RANK() OVER (PARTITION BY NTEE1 ORDER BY total_revenue DESC) as ntee1_rank,
            -- Total orgs in NTEE1 category
            COUNT(*) OVER (PARTITION BY NTEE1) as ntee1_total_orgs
        FROM nccs_core_2019
        WHERE total_revenue > 0 AND NTEE1 IS NOT NULL
    """)
    conn.commit()
    
    # Index for fast lookups
    c.execute("CREATE INDEX idx_pct_ein ON revenue_percentiles(EIN)")
    c.execute("CREATE INDEX idx_pct_ntee ON revenue_percentiles(NTEE1)")
    c.execute("CREATE INDEX idx_pct_state ON revenue_percentiles(STATE)")
    conn.commit()
    print(f"Built table: {c.execute('SELECT COUNT(*) FROM revenue_percentiles').fetchone()[0]:,} rows")
    
    # === SAMPLE OUTPUTS ===
    print("\n=== Sample: Top 10 Health (E) Orgs by Revenue ===")
    c.execute("""
        SELECT EIN, NAME, total_revenue, ntee1_percentile, ntee1_rank
        FROM revenue_percentiles
        WHERE NTEE1 = 'E'
        ORDER BY total_revenue DESC
        LIMIT 10
    """)
    for row in c.fetchall():
        print(f"  {row[0]} | {row[1][:40]:40} | ${row[2]:>15,.0f} | Pctl: {row[3]:5.1f} | Rank: {row[4]}")
    
    print("\n=== Sample: Where does a $1M Education (B) org rank? ===")
    c.execute("""
        SELECT 
            COUNT(*) as total_b_orgs,
            COUNT(CASE WHEN total_revenue < 1000000 THEN 1 END) as below_1m,
            ROUND(100.0 * COUNT(CASE WHEN total_revenue < 1000000 THEN 1 END) / COUNT(*), 1) as percentile
        FROM revenue_percentiles
        WHERE NTEE1 = 'B'
    """)
    row = c.fetchone()
    print(f"  Total B orgs: {row[0]:,}")
    print(f"  Orgs below $1M: {row[1]:,}")
    print(f"  A $1M B org is at the {row[2]:.1f}th percentile (ranks higher than {row[2]:.1f}% of peers)")
    
    print("\n=== NTEE1 Category Sizes (PC scope) ===")
    c.execute("""
        SELECT NTEE1, COUNT(*) as n, 
               MIN(total_revenue) as min_rev,
               MAX(total_revenue) as max_rev
        FROM revenue_percentiles
        WHERE scope = 'PC'
        GROUP BY NTEE1
        ORDER BY n DESC
        LIMIT 10
    """)
    for row in c.fetchall():
        print(f"  {row[0]}: {row[1]:>6,} orgs | Min: ${row[2]:>12,.0f} | Max: ${row[3]:>15,.0f}")

