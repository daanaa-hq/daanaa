#!/usr/bin/env python3
"""Submit/prepare search discovery signals for the visibility overlay."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "visibility" / "reports"
SITEMAP = "https://data.daanaa.org/sitemap-index.xml"
OVERLAY_SITEMAP = "https://data.daanaa.org/overlay-pages.xml"
ROBOTS = "https://data.daanaa.org/robots.txt"
AI_TXT = "https://data.daanaa.org/ai.txt"
BING_PING = "https://www.bing.com/webmaster/ping.aspx?siteMap=" + quote(SITEMAP, safe="")


def fetch(url: str, timeout: float = 15.0) -> dict[str, object]:
    req = Request(url, headers={"User-Agent": "DaanaaVisibilitySubmission/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read(4096)
            return {
                "url": url,
                "ok": 200 <= resp.status < 400,
                "status": resp.status,
                "final_url": resp.geturl(),
                "sample": body.decode("utf-8", errors="replace")[:500],
            }
    except HTTPError as e:
        sample = e.read(4096).decode("utf-8", errors="replace") if e.fp else ""
        return {"url": url, "ok": False, "status": e.code, "error": str(e), "sample": sample[:500]}
    except URLError as e:
        return {"url": url, "ok": False, "status": None, "error": str(e.reason), "sample": ""}


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    checks = {
        "robots": fetch(ROBOTS),
        "sitemap_index": fetch(SITEMAP),
        "overlay_pages_sitemap": fetch(OVERLAY_SITEMAP),
        "ai_txt": fetch(AI_TXT),
        "bing_sitemap_ping": fetch(BING_PING),
    }
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sitemap": SITEMAP,
        "overlay_pages_sitemap": OVERLAY_SITEMAP,
        "robots": ROBOTS,
        "ai_txt": AI_TXT,
        "bing_ping_url": BING_PING,
        "checks": checks,
        "google": {
            "status": "manual_or_api_auth_required",
            "note": "Google retired unauthenticated sitemap ping. Submit the sitemap in Google Search Console for data.daanaa.org and daanaa.org properties.",
        },
        "bing": {
            "status": "ping_attempted",
            "note": "For persistent reporting, also add data.daanaa.org in Bing Webmaster Tools and submit the sitemap there.",
        },
    }
    (REPORTS / "search-submission.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md = f"""# Search Submission Report

Generated: {report['generated_at']}

## Public Signals

- Sitemap index: {SITEMAP}
- Overlay page sitemap: {OVERLAY_SITEMAP}
- Robots: {ROBOTS}
- AI notes: {AI_TXT}

## Automated Checks

- Robots: {checks['robots']['status']}
- Sitemap index: {checks['sitemap_index']['status']}
- Overlay page sitemap: {checks['overlay_pages_sitemap']['status']}
- AI notes: {checks['ai_txt']['status']}
- Bing sitemap ping: {checks['bing_sitemap_ping']['status']}

## Google

Google Search Console submission still requires verified account access. The old unauthenticated sitemap ping endpoint should not be used.

Submit manually/API after verification:

```text
{SITEMAP}
```

## Bing

Bing ping was attempted at:

```text
{BING_PING}
```

Add the site in Bing Webmaster Tools for persistent reporting and submit the same sitemap there.
"""
    (REPORTS / "search-submission.md").write_text(md, encoding="utf-8")
    print(f"Wrote {REPORTS / 'search-submission.json'}")
    print(f"Wrote {REPORTS / 'search-submission.md'}")
    for name, result in checks.items():
        print(f"{name}: {result.get('status')} {result.get('final_url', result.get('url'))}")
    return 0 if checks["robots"]["ok"] and checks["sitemap_index"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
