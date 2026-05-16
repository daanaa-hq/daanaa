#!/usr/bin/env python3
"""
AGENT 6: BMF DOWNLOADER
Mission: Download IRS Business Master File.
"""
import os, sys, subprocess

BMF_URL = "https://www.irs.gov/pub/irs-soi/eo1.csv"
OUT = "data/irs_bmf.csv"

print("[AGENT 6] IRS Business Master File downloader")
print(f"[AGENT 6] Source: {BMF_URL}")
print(f"[AGENT 6] Output: {OUT}")

if os.path.exists(OUT):
    size = os.path.getsize(OUT) / (1024**2)
    print(f"[AGENT 6] BMF already exists ({size:.1f} MB). Skipping download.")
    print(f"[AGENT 6] To force re-download, delete {OUT}")
    sys.exit(0)

print("[AGENT 6] Downloading... (this is ~700MB, may take 5-15 minutes)")
try:
    result = subprocess.run(
        ['wget', '-q', '--show-progress', BMF_URL, '-O', OUT],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        size = os.path.getsize(OUT) / (1024**2)
        print(f"[AGENT 6] Download complete: {size:.1f} MB")
        print("[AGENT 6] Run Agent 3 (Enricher) next to merge BMF data into profiles")
    else:
        print(f"[AGENT 6] Download failed: {result.stderr}")
        print("[AGENT 6] Try manual download: wget https://www.irs.gov/pub/irs-soi/eo1.csv -O data/irs_bmf.csv")
        sys.exit(1)
except FileNotFoundError:
    print("[AGENT 6] wget not found. Install with: sudo apt-get install wget")
    sys.exit(1)
