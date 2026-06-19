"""
Grant discovery agent.

Queries Grants.gov for federal funding opportunities matching each verified
nonprofit's NTEE category. Sends a weekly alert email to the org rep.
Idempotent — uses grant_discovery_log to skip orgs already notified this week.

Data source: Grants.gov public API (no key required).
  POST https://apply07.grants.gov/grantsws/rest/opportunities/search/
  eligibilities="25" means non-profits / 501(c)(3) only.

Stewardship compliance:
  P1  — directly serves nonprofit mission (funding discovery)
  P3  — Grants.gov is authoritative public data; no AI inference
  P7  — no curation, algorithmic matching only
  P10 — deterministic template, no LLM generation in email

Cron: Monday 08:00 (0 8 * * 1)
"""

import sys
import json
import datetime
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.agents.base import BaseAgent
from scripts.email_service import get_email_service, grant_opportunity_email

GRANTS_GOV_URL = "https://apply07.grants.gov/grantsws/rest/opportunities/search/"

# NTEE1 single-letter → search keyword(s) for Grants.gov
NTEE1_KEYWORDS: dict[str, list[str]] = {
    "A": ["arts culture humanities", "arts nonprofit"],
    "B": ["education school", "education nonprofit"],
    "C": ["environment conservation", "environmental nonprofit"],
    "D": ["animal welfare", "animal protection"],
    "E": ["health medical", "community health"],
    "F": ["mental health behavioral", "mental health services"],
    "G": ["disease research medical", "health research"],
    "H": ["medical research", "biomedical research"],
    "I": ["crime prevention justice", "criminal justice"],
    "J": ["employment workforce", "job training"],
    "K": ["food bank agriculture", "food security nonprofit"],
    "L": ["housing homeless", "affordable housing"],
    "M": ["public safety disaster", "emergency preparedness"],
    "N": ["recreation sports", "youth recreation"],
    "O": ["youth development", "youth services nonprofit"],
    "P": ["human services social", "community services"],
    "Q": ["international development", "global humanitarian"],
    "R": ["civil rights advocacy", "civil liberties"],
    "S": ["community development", "neighborhood nonprofit"],
    "T": ["philanthropy foundation", "nonprofit capacity"],
    "U": ["science technology research", "STEM nonprofit"],
    "V": ["social science research", "policy research"],
    "W": ["public policy government", "civic engagement"],
    "X": ["religion faith community", "faith-based nonprofit"],
    "Y": ["mutual benefit cooperative", "member organization"],
    "Z": ["unknown general nonprofit", "general charitable"],
}


def _search_grants(keyword: str, rows: int = 10) -> list[dict]:
    """Query Grants.gov for posted opportunities matching keyword."""
    payload = json.dumps({
        "keyword": keyword,
        "oppStatuses": "posted",
        "eligibilities": "25",
        "rows": rows,
    }).encode("utf-8")
    req = urllib.request.Request(
        GRANTS_GOV_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("oppHits", []) or []
    except Exception:
        return []


def _normalize_grant(hit: dict) -> dict:
    """Flatten a Grants.gov oppHit into a simple dict."""
    cfda_list = hit.get("cfdaList") or []
    first_cfda = cfda_list[0] if cfda_list else ""
    cfda = first_cfda if isinstance(first_cfda, str) else first_cfda.get("programNumber", "")
    grant_id = str(hit.get("id", ""))
    number = hit.get("number", "")
    url = (
        f"https://grants.gov/search-results-detail/{grant_id}"
        if grant_id else ""
    )
    return {
        "grant_id": grant_id,
        "number": number,
        "title": hit.get("title", ""),
        "agency": hit.get("agency", hit.get("agencyCode", "")),
        "open_date": hit.get("openDate", ""),
        "close_date": hit.get("closeDate", ""),
        "cfda": cfda,
        "url": url,
    }


class GrantDiscoveryAgent(BaseAgent):
    name = "grant_discovery"
    local_model = None  # no LLM needed

    def execute(self, **kwargs):
        svc = get_email_service()
        db = self.db()

        db.execute("""
            CREATE TABLE IF NOT EXISTS grant_opportunities (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                grant_id    TEXT    NOT NULL,
                ein         TEXT    NOT NULL,
                title       TEXT    NOT NULL,
                agency      TEXT,
                open_date   TEXT,
                close_date  TEXT,
                cfda        TEXT,
                url         TEXT,
                found_at    TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(grant_id, ein)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS grant_discovery_log (
                ein         TEXT    NOT NULL,
                run_week    TEXT    NOT NULL,
                sent_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
                grants_sent INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (ein, run_week)
            )
        """)
        db.commit()

        now = datetime.datetime.utcnow()
        week_label = now.strftime("%Y-W%W")

        # All verified, unrevoked claims with an email address
        claims = db.execute("""
            SELECT c.ein, c.email, c.rep_name, r.organization_name, r.NTEE1, r.cause_tags
            FROM org_claims c
            JOIN registry_enriched r ON r.EIN = c.ein
            WHERE c.claim_status = 'verified'
              AND c.revoked_at IS NULL
              AND c.email IS NOT NULL AND c.email != ''
              AND NOT EXISTS (
                SELECT 1 FROM grant_discovery_log
                WHERE ein = c.ein AND run_week = ?
              )
        """, (week_label,)).fetchall()

        self.log.info(f"Grant discovery run {week_label}: {len(claims)} orgs to check")
        sent = skipped = errors = 0

        for claim in claims:
            ein = claim["ein"]
            email = claim["email"]
            rep_name = claim["rep_name"] or ""
            org_name = claim["organization_name"] or ein
            ntee1 = (claim["NTEE1"] or "Z").upper()[0]

            try:
                # Build search keywords: NTEE1 category + first cause tag (if any)
                keywords = list(NTEE1_KEYWORDS.get(ntee1, NTEE1_KEYWORDS["Z"]))
                cause_tags = []
                try:
                    cause_tags = json.loads(claim["cause_tags"] or "[]")
                except Exception:
                    pass
                if cause_tags:
                    keywords.insert(0, cause_tags[0].replace("-", " ").replace("_", " "))

                # Query Grants.gov with best keyword first
                raw_grants: list[dict] = []
                seen_ids: set[str] = set()
                for kw in keywords[:2]:
                    for hit in _search_grants(kw, rows=8):
                        g = _normalize_grant(hit)
                        if g["grant_id"] and g["grant_id"] not in seen_ids:
                            seen_ids.add(g["grant_id"])
                            raw_grants.append(g)

                if not raw_grants:
                    skipped += 1
                    db.execute(
                        "INSERT OR IGNORE INTO grant_discovery_log (ein, run_week, grants_sent) VALUES (?, ?, 0)",
                        (ein, week_label),
                    )
                    db.commit()
                    continue

                # Persist new opportunities (deduplicated)
                new_grants: list[dict] = []
                for g in raw_grants[:5]:
                    existing = db.execute(
                        "SELECT 1 FROM grant_opportunities WHERE grant_id=? AND ein=?",
                        (g["grant_id"], ein),
                    ).fetchone()
                    if not existing:
                        db.execute("""
                            INSERT OR IGNORE INTO grant_opportunities
                                (grant_id, ein, title, agency, open_date, close_date, cfda, url)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            g["grant_id"], ein, g["title"], g["agency"],
                            g["open_date"], g["close_date"], g["cfda"], g["url"],
                        ))
                        new_grants.append(g)
                db.commit()

                # Send email with all found grants (new or recurring — rep may have missed it)
                grants_to_send = raw_grants[:5]
                template = grant_opportunity_email(rep_name or None, org_name, grants_to_send)
                if svc.send_template(email, template):
                    db.execute(
                        "INSERT OR IGNORE INTO grant_discovery_log (ein, run_week, grants_sent) VALUES (?, ?, ?)",
                        (ein, week_label, len(grants_to_send)),
                    )
                    db.commit()
                    self.log_agent_decision(
                        "grant_discovery",
                        {"ein": ein, "week": week_label, "grants": len(grants_to_send), "new": len(new_grants)},
                        f"grant alert sent to {email}: {len(grants_to_send)} opportunities ({len(new_grants)} new)",
                        evidence=f"Grants.gov API, NTEE1={ntee1}",
                    )
                    sent += 1
                else:
                    errors += 1

            except Exception as e:
                self.log.error(f"Grant discovery error for {ein}: {e}")
                errors += 1

        self.log_job(
            processed=len(claims),
            updated=sent,
            errors=errors,
            notes=f"week={week_label} sent={sent} skipped={skipped}",
        )
        return {"week": week_label, "sent": sent, "skipped": skipped, "errors": errors}


if __name__ == "__main__":
    GrantDiscoveryAgent().run()
