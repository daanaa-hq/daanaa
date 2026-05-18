"""
Link Health Agent
-----------------
Verifies nonprofit website URLs and detects direct donation platform links.
Pure Python — zero LLM cost, zero API cost.

Runs weekly. Skips orgs checked in the last 6 days.
Prioritises orgs with recent link_feedback reports first.
"""

import sys, datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent))
from check_link_health import classify, ensure_columns
from agents.base import BaseAgent


class LinkHealthAgent(BaseAgent):
    name = "link_health"

    def execute(self, limit=None, workers=24, force=False):
        db = self.db()
        ensure_columns(db)

        # Prioritise orgs flagged by donors via link_feedback, then oldest checks
        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=6)).isoformat()
        rows = db.execute("""
            SELECT r.EIN, r.website
            FROM registry_enriched r
            WHERE r.website IS NOT NULL AND TRIM(r.website) != ''
              AND (? OR r.website_checked_at IS NULL OR r.website_checked_at < ?)
            ORDER BY
              -- bump orgs with donor feedback to top
              (SELECT COUNT(*) FROM link_feedback lf
               WHERE lf.EIN = r.EIN AND lf.created_at > date('now', '-30 days')) DESC,
              r.website_checked_at ASC NULLS FIRST
        """, (1 if force else 0, cutoff)).fetchall()

        if limit:
            rows = rows[:limit]

        total = len(rows)
        if total == 0:
            self.log.info("All links checked recently — nothing to do")
            self.log_job(notes="all current")
            return {"processed": 0, "updated": 0}

        self.log.info(f"Checking {total:,} links  (workers={workers})")

        now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
        counts = {"ok": 0, "dead": 0, "offsite": 0, "parked": 0}
        donate_found = 0
        updates, done = [], 0

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(classify, w): ein for ein, w in rows}
            for fut in as_completed(futs):
                ein = futs[fut]
                try:
                    status, final_dom, donate_url, donate_platform = fut.result()
                except Exception:
                    status, final_dom, donate_url, donate_platform = "dead", "", None, None
                counts[status] += 1
                if donate_url:
                    donate_found += 1
                updates.append((status, now, final_dom, donate_url, donate_platform, ein))
                done += 1
                if len(updates) >= 500:
                    self._flush(db, updates)
                    updates.clear()
                if done % 500 == 0 or done == total:
                    self.log.info(
                        f"  {done}/{total}  ok={counts['ok']} dead={counts['dead']} "
                        f"offsite={counts['offsite']} parked={counts['parked']} "
                        f"donate={donate_found}"
                    )

        if updates:
            self._flush(db, updates)

        notes = (f"ok={counts['ok']} dead={counts['dead']} "
                 f"offsite={counts['offsite']} parked={counts['parked']} "
                 f"donate_urls={donate_found}")
        self.log_job(processed=total, updated=total, notes=notes)
        return {"processed": total, **counts, "donate_found": donate_found}

    def _flush(self, db, updates):
        db.executemany("""
            UPDATE registry_enriched
            SET website_status=?, website_checked_at=?, website_final_domain=?,
                donate_url=?, donate_platform=?
            WHERE EIN=?
        """, updates)
        db.commit()
