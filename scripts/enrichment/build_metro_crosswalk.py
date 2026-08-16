#!/usr/bin/env python3
"""build_metro_crosswalk.py — ZIP5 -> metro (CBSA) crosswalk from Census public data.

Why: small/suburban nonprofits list their own town (e.g. Somerville MA), so a
search for the metro ("Boston") never finds them. Stamping each org with its
Census-defined Core-Based Statistical Area makes the whole metro one matchable
unit. Pure public geography — evidence-based and explainable (Stewardship P3/P9).

Join path:  ZIP5 --(ZCTA->county relationship)--> county FIPS --(CBSA delineation)--> CBSA title

Sources (Census, free, public):
  - CBSA delineation (county components):  list1_2023.xlsx
  - ZCTA <-> county relationship:          tab20_zcta520_county20_natl.txt

Output: data/zip_to_metro.csv  (zip5, metro, type)
Cached downloads live in /tmp so reruns are cheap; pass --refresh to re-download.
"""
import argparse
import csv
import os
import sys
import urllib.request

CBSA_URL = ("https://www2.census.gov/programs-surveys/metro-micro/geographies/"
            "reference-files/2023/delineation-files/list1_2023.xlsx")
ZCTA_URL = ("https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/"
            "tab20_zcta520_county20_natl.txt")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "data", "zip_to_metro.csv")
CACHE_CBSA = "/tmp/list1_2023.xlsx"
CACHE_ZCTA = "/tmp/zcta_county.txt"


def fetch(url, dest, refresh=False):
    if os.path.exists(dest) and not refresh:
        print(f"  cached: {dest}")
        return
    print(f"  downloading {url}")
    urllib.request.urlretrieve(url, dest)
    print(f"  saved -> {dest} ({os.path.getsize(dest):,} bytes)")


def county_to_cbsa(path):
    """county GEOID (state2+county3) -> (cbsa_title, area_type)."""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb.active
    out = {}
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i < 3 or not row or not row[0]:
            continue
        title, mtype, fs, fc = row[3], row[4], row[9], row[10]
        if not (fs and fc and title):
            continue
        out[str(fs).zfill(2) + str(fc).zfill(3)] = (title, mtype)
    return out


def zip_to_county(path):
    """ZIP5 -> county GEOID, choosing the county holding the most land area."""
    best = {}  # zip -> (area, county_geoid)
    with open(path, encoding="utf-8-sig") as f:
        rd = csv.reader(f, delimiter="|")
        h = next(rd)
        zi, ci, ai = (h.index("GEOID_ZCTA5_20"),
                      h.index("GEOID_COUNTY_20"),
                      h.index("AREALAND_PART"))
        for r in rd:
            z = r[zi].strip()
            if not z:
                continue
            try:
                a = int(r[ai]) if r[ai] else 0
            except ValueError:
                a = 0
            if z not in best or a > best[z][0]:
                best[z] = (a, r[ci].strip())
    return {z: cg for z, (a, cg) in best.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download Census source files")
    args = ap.parse_args()

    print("Fetching Census sources...")
    fetch(CBSA_URL, CACHE_CBSA, args.refresh)
    fetch(ZCTA_URL, CACHE_ZCTA, args.refresh)

    c2c = county_to_cbsa(CACHE_CBSA)
    print(f"counties mapped to a CBSA: {len(c2c):,}")
    z2county = zip_to_county(CACHE_ZCTA)
    print(f"ZIPs with a primary county: {len(z2county):,}")

    z2m = {z: c2c[cg] for z, cg in z2county.items() if cg in c2c}
    print(f"ZIPs with a CBSA: {len(z2m):,}")

    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["zip5", "metro", "type"])
        for z, (title, mtype) in sorted(z2m.items()):
            w.writerow([z, title, mtype])
    print(f"wrote {OUT} ({len(z2m):,} rows)")


if __name__ == "__main__":
    sys.exit(main())
