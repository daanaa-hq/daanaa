"""
Social Presence Agent
---------------------
Checks whether each org has a detectable presence on Twitter/X, LinkedIn,
or Facebook. Pure HEAD requests — no scraping, no APIs, no cost.

A social presence score (0–3) is a proxy signal for "this org is actively
communicating" — useful for future scoring versions and trust indicators.

Cadence: weekly (168h). Processes orgs with NULL or stale social_checked_at.
"""

import sys, datetime, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.base import BaseAgent

try:
    import urllib.request
    import urllib.parse
except ImportError:
    pass


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MERITBot/1.0; +https://meritgiving.com)",
    "Accept": "text/html",
}

_PLATFORMS = [
    # (platform_name, url_template)
    # We search for the org's slug on each platform using a known URL pattern.
    # HEAD request only — no HTML parsing, no JavaScript.
    ("twitter",   "https://twitter.com/{slug}"),
    ("linkedin",  "https://www.linkedin.com/company/{slug}"),
    ("facebook",  "https://www.facebook.com/{slug}"),
]


def _make_slug(name: str) -> str:
    """Convert org name to a URL-safe slug."""
    import re
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')[:60]
    return slug


def _check_url(url: str, timeout: int = 6) -> bool:
    """Return True only if URL resolves to an actual org page (not a login redirect)."""
    try:
        req = urllib.request.Request(url, headers=_HEADERS, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            final = resp.url or ""
            # Facebook redirects any unknown profile to /login — not a real page
            if "facebook.com/login" in final or "facebook.com/checkpoint" in final:
                return False
            # LinkedIn blocks scrapers with 999 — treated as not found
            return resp.status in (200, 301, 302, 303)
    except Exception:
        return False


def check_social(ein: str, name: str) -> tuple[int, str]:
    """Return (social_score 0-3, platforms_found csv)."""
    slug = _make_slug(name)
    found = []
    for platform, tmpl in _PLATFORMS:
        url = tmpl.format(slug=slug)
        if _check_url(url):
            found.append(platform)
        time.sleep(0.1)  # gentle rate limit per-platform per-org
    return len(found), ",".join(found)


class SocialPresenceAgent(BaseAgent):
    name = "social_presence"

    def execute(self, limit=None, workers=8, force=False):
        db = self.db()

        # Ensure columns exist
        existing = [r[1] for r in db.execute("PRAGMA table_info(registry_enriched)").fetchall()]
        if "social_score" not in existing:
            db.execute("ALTER TABLE registry_enriched ADD COLUMN social_score INTEGER")
        if "social_platforms" not in existing:
            db.execute("ALTER TABLE registry_enriched ADD COLUMN social_platforms TEXT")
        if "social_checked_at" not in existing:
            db.execute("ALTER TABLE registry_enriched ADD COLUMN social_checked_at TEXT")
        db.commit()

        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=6)).isoformat()
        rows = db.execute("""
            SELECT EIN, organization_name
            FROM registry_enriched
            WHERE organization_name IS NOT NULL AND TRIM(organization_name) != ''
              AND (? OR social_checked_at IS NULL OR social_checked_at < ?)
            ORDER BY social_checked_at ASC NULLS FIRST
        """, (1 if force else 0, cutoff)).fetchall()

        if limit:
            rows = rows[:limit]

        total = len(rows)
        if total == 0:
            self.log.info("All orgs have recent social checks — nothing to do")
            self.log_job(notes="all current")
            return {"processed": 0}

        self.log.info(f"Checking social presence for {total:,} orgs  (workers={workers})")

        now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        updates, done, found_any = [], 0, 0

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(check_social, ein, name): ein for ein, name in rows}
            for fut in as_completed(futs):
                ein = futs[fut]
                try:
                    score, platforms = fut.result()
                except Exception:
                    score, platforms = 0, ""
                if score > 0:
                    found_any += 1
                updates.append((score, platforms, now, ein))
                done += 1

                if len(updates) >= 200:
                    self._flush_social(db, updates)
                    updates.clear()
                if done % 100 == 0 or done == total:
                    self.log.info(f"  {done}/{total}  with_presence={found_any}")

        if updates:
            self._flush_social(db, updates)

        pct = found_any / total * 100 if total else 0
        self.log.info(f"=== social_presence done: {total} checked, {found_any} ({pct:.1f}%) have presence ===")
        self.log_job(notes=f"checked={total} found={found_any}")
        return {"processed": total, "with_presence": found_any}

    def _flush_social(self, db, updates):
        db.executemany("""
            UPDATE registry_enriched
            SET social_score=?, social_platforms=?, social_checked_at=?
            WHERE EIN=?
        """, updates)
        db.commit()
