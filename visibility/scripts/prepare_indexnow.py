#!/usr/bin/env python3
"""Place the public IndexNow key file into overlay output folders."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEY_PATH = ROOT / "visibility" / "config" / "indexnow-key.txt"
TARGETS = [ROOT / "visibility" / "public", ROOT / "visibility" / "cloudflare-public"]


def main() -> int:
    key = KEY_PATH.read_text(encoding="utf-8").strip()
    if not key or not all(ch.isalnum() or ch in "-_" for ch in key):
        raise SystemExit("Invalid IndexNow key")
    for target in TARGETS:
        if target.exists():
            (target / f"{key}.txt").write_text(key + "\n", encoding="utf-8")
            # IndexNow keys are public by protocol (served at /<key>.txt), but
            # keep key material out of logs anyway per privacy_check.sh gate 2.
            print(f"Wrote IndexNow verification file into {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
