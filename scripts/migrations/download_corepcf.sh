#!/bin/bash
# MeritGiving CorePCF Downloader
# Downloads NCCS CorePCF files (pre-parsed 990 financials) for 2019-2022
# These contain: program expenses, fundraising costs, balance sheets, revenue breakdowns

set -e

OUT="$HOME/meritgiving/data/corepcf"
mkdir -p "$OUT"

cd "$OUT"

echo "=========================================="
echo "Downloading NCCS CorePCF Financial Files"
echo "=========================================="
echo ""
echo "CorePCF = Public Charity Core File"
echo "Contains pre-parsed 990 + 990EZ financial variables"
echo "NCCS already did the XML parsing for us"
echo ""

# Known URL patterns for NCCS CorePCF
# These may change — if they fail, check: https://nccs-data.urban.org/data/core/

YEARS="2019 2020 2021 2022"

for YEAR in $YEARS; do
    echo "[${YEAR}] Trying download..."

    # Primary pattern
    curl -sL "https://nccs-data.urban.org/data/core/${YEAR}/corepcf${YEAR}.csv"         -o "corepcf_${YEAR}.csv" --progress-bar 2>/dev/null &&         echo "  ✓ Downloaded corepcf_${YEAR}.csv" && continue

    # Alternate pattern (some years use different naming)
    curl -sL "https://nccs-data.urban.org/data/core/${YEAR}/corepccr${YEAR}.csv"         -o "corepcf_${YEAR}.csv" --progress-bar 2>/dev/null &&         echo "  ✓ Downloaded corepcf_${YEAR}.csv (alt name)" && continue

    # Stata format fallback (can convert with pandas)
    curl -sL "https://nccs-data.urban.org/data/core/${YEAR}/corepcf${YEAR}.dta"         -o "corepcf_${YEAR}.dta" --progress-bar 2>/dev/null &&         echo "  ⚠️  Downloaded .dta format — convert with: python3 -c 'import pandas as pd; pd.read_stata("corepcf_${YEAR}.dta").to_csv("corepcf_${YEAR}.csv", index=False)'" && continue

    echo "  ❌ Failed — check NCCS CORE Data Catalog for ${YEAR}"
done

echo ""
echo "=========================================="
echo "Download Summary"
echo "=========================================="
ls -lh *.csv *.dta 2>/dev/null || echo "  (no files downloaded)"

echo ""
echo "If downloads failed, get files manually from:"
echo "  https://nccs-data.urban.org/data/core/"
echo "Or email: nccs@urban.org"
echo ""
echo "Once downloaded, run:"
echo "  python3 $HOME/meritgiving/scripts/merge_corepcf.py"
