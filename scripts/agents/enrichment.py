"""
Enrichment Agent
----------------
Keeps ProPublica financial data fresh for orgs with stale or missing records.
Pure Python + free ProPublica API — zero cost.

Runs monthly. Prioritises:
  1. Orgs with no financial data at all
  2. Orgs not enriched in 90+ days
  3. Orgs where link_feedback suggests a donor tried to give (warm leads)
"""

import json, time, datetime, urllib.request, urllib.error
from agents.base import BaseAgent

PP_BASE = "https://projects.propublica.org/nonprofits/api/v2/organizations"
RATE_LIMIT_SLEEP = 0.35   # ProPublica asks ~3 req/s; we stay conservative


def _fetch_pp(ein: str) -> dict | None:
    clean = ein.replace("-", "")
    url = f"{PP_BASE}/{clean}.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        return None


def _extract(data: dict) -> dict:
    """Pull the fields we care about from ProPublica response."""
    org = data.get("organization", {})
    filings = data.get("filings_with_data", [])
    latest = filings[0] if filings else {}
    return {
        "mission":          org.get("mission"),
        "website":          org.get("website"),
        "total_revenue":    latest.get("totrevenue"),
        "total_expenses":   latest.get("totfuncexpns"),
        "net_assets":       latest.get("totnetassetend"),
        "total_liabilities": latest.get("totliabend"),
        "employee_count":   org.get("employees"),
        "ruling_date":      org.get("ruling_date"),
        "latest_tax_year":  latest.get("tax_prd_yr"),
        "updated_at":       datetime.datetime.utcnow().isoformat(),
    }


class EnrichmentAgent(BaseAgent):
    name = "enrichment"

    def execute(self, limit=None, force=False):
        db = self.db()
        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=90)).isoformat()

        rows = db.execute("""
            SELECT EIN FROM registry_enriched
            WHERE
              (? OR updated_at IS NULL OR updated_at < ?)
              AND source != 'irs_soi_only'
            ORDER BY
              -- donor feedback = highest priority
              (SELECT COUNT(*) FROM link_feedback lf
               WHERE lf.EIN = registry_enriched.EIN) DESC,
              CASE WHEN total_revenue IS NULL THEN 0 ELSE 1 END,
              updated_at ASC NULLS FIRST
        """, (1 if force else 0, cutoff)).fetchall()

        if limit:
            rows = rows[:limit]

        total = len(rows)
        if total == 0:
            self.log.info("All orgs enriched recently — nothing to do")
            self.log_job(notes="all current")
            return {"processed": 0, "updated": 0}

        self.log.info(f"Enriching {total:,} orgs from ProPublica")
        updated, skipped, errors = 0, 0, 0

        for i, (ein,) in enumerate(rows):
            try:
                data = _fetch_pp(ein)
                time.sleep(RATE_LIMIT_SLEEP)
                if data is None:
                    skipped += 1
                    continue
                fields = _extract(data)
                # Only update non-null fields — don't overwrite good data with None
                set_parts = [f"{k}=?" for k, v in fields.items() if v is not None]
                vals = [v for v in fields.values() if v is not None]
                if set_parts:
                    db.execute(
                        f"UPDATE registry_enriched SET {', '.join(set_parts)} WHERE EIN=?",
                        vals + [ein],
                    )
                    updated += 1
            except Exception as e:
                errors += 1
                self.log.warning(f"Enrichment error {ein}: {e}")

            if (i + 1) % 200 == 0:
                db.commit()
                self.log.info(f"  {i+1}/{total}  updated={updated} skip={skipped} err={errors}")

        db.commit()
        self.log_job(processed=total, updated=updated, errors=errors,
                     notes=f"skipped={skipped}")
        return {"processed": total, "updated": updated, "skipped": skipped, "errors": errors}
