#!/usr/bin/env python3
"""Submit overlay URLs to IndexNow after the key file is publicly deployed."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
KEY = (ROOT / "visibility" / "config" / "indexnow-key.txt").read_text(encoding="utf-8").strip()
REPORTS = ROOT / "visibility" / "reports"
HOST = "data.daanaa.org"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"
URLS = [
    f"https://{HOST}/about-daanaa",
    f"https://{HOST}/answers/daanaa-faq",
    f"https://{HOST}/authority/identity-kit",
    f"https://{HOST}/authority/search-everywhere",
    f"https://{HOST}/open-data",
    f"https://{HOST}/sitemap-index.xml",
    f"https://{HOST}/llms.txt",
    f"https://{HOST}/dataset.json",
    f"https://{HOST}/data/orgs-manifest.json",
    f"https://{HOST}/claim-nonprofit-page",
    f"https://{HOST}/nonprofit-vendor-discounts",
    f"https://{HOST}/blog/why-small-nonprofits-disappear-in-search",
    f"https://{HOST}/blog/how-donors-can-use-public-nonprofit-data-responsibly",
    f"https://{HOST}/blog/giving-wallet-making-giving-easier-to-repeat",
    f"https://{HOST}/blog/daanaa-impact-network-giving-money-time-knowledge-support",
    f"https://{HOST}/blog/philanthropy-belongs-to-everyone",
    f"https://{HOST}/growth-pages.xml",
    f"https://{HOST}/intent-pages.xml",
    f"https://{HOST}/intent",
    f"https://{HOST}/find",
    f"https://{HOST}/intent/find-nonprofits-near-me",
    f"https://{HOST}/intent/find-a-nonprofit-by-ein",
    f"https://{HOST}/intent/how-to-find-small-nonprofits-to-support",
    f"https://{HOST}/intent/how-to-know-if-a-nonprofit-is-real",
    f"https://{HOST}/find/animal-related-nonprofits-in-texas",
    f"https://{HOST}/find/education-nonprofits-in-california",
    f"https://{HOST}/nonprofits/state",
    f"https://{HOST}/nonprofits/category",
    f"https://{HOST}/guides",
    f"https://{HOST}/guides/how-to-give-locally",
    f"https://{HOST}/guides/choose-a-nonprofit-without-hype",
    f"https://{HOST}/guides/organize-giving-for-tax-time",
    f"https://{HOST}/guides/volunteer-when-you-cannot-give-money",
    f"https://{HOST}/guides/claim-your-nonprofit-profile-guide",
]


def fetch(url: str) -> dict[str, object]:
    try:
        with urlopen(Request(url, headers={"User-Agent": "DaanaaIndexNowCheck/1.0"}), timeout=15) as resp:
            return {"url": url, "status": resp.status, "ok": 200 <= resp.status < 300}
    except HTTPError as e:
        return {"url": url, "status": e.code, "ok": False, "error": str(e)}
    except URLError as e:
        return {"url": url, "status": None, "ok": False, "error": str(e.reason)}


def post_indexnow() -> dict[str, object]:
    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": URLS,
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(ENDPOINT, data=data, headers={"Content-Type": "application/json", "User-Agent": "DaanaaIndexNow/1.0"}, method="POST")
    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read(4096).decode("utf-8", errors="replace")
            return {"status": resp.status, "ok": 200 <= resp.status < 300, "body": body}
    except HTTPError as e:
        body = e.read(4096).decode("utf-8", errors="replace") if e.fp else ""
        return {"status": e.code, "ok": False, "error": str(e), "body": body}
    except URLError as e:
        return {"status": None, "ok": False, "error": str(e.reason), "body": ""}


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    key_check = fetch(KEY_LOCATION)
    result = None
    if key_check["ok"]:
        result = post_indexnow()
    else:
        result = {"status": "skipped", "ok": False, "error": "IndexNow key file is not public yet"}
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": HOST,
        "key_location": KEY_LOCATION,
        "urls": URLS,
        "key_check": key_check,
        "indexnow_result": result,
    }
    (REPORTS / "indexnow-submission.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"key_check: {key_check.get('status')} {KEY_LOCATION}")
    print(f"indexnow: {result.get('status')}")
    print(f"Wrote {REPORTS / 'indexnow-submission.json'}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
