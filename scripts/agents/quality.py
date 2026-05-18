"""
Quality Agent
-------------
Daily health check — flags anomalies, stale data, and donate_url rot.
Writes a brief daily report to logs/daily_report_YYYYMMDD.txt.
Uses local LLM (qwen2.5:14b) to summarise findings into plain English.
No API cost.
"""

import datetime, json
from pathlib import Path
from agents.base import BaseAgent

LOG_DIR = Path.home() / "meritgiving" / "logs"
# Slightly larger model for reasoning; still free
_SUMMARY_MODEL = "qwen2.5:14b"


class QualityAgent(BaseAgent):
    name = "quality"
    local_model = _SUMMARY_MODEL

    def execute(self):
        db = self.db()
        today = datetime.date.today().isoformat()
        findings = []

        # 1. Donate URLs that might have gone stale (link was ok, donate_url set,
        #    but no re-check in 14+ days — could be a dead campaign now)
        stale_donate = db.execute("""
            SELECT COUNT(*) FROM registry_enriched
            WHERE donate_url IS NOT NULL
              AND website_checked_at < date('now', '-14 days')
        """).fetchone()[0]
        if stale_donate:
            findings.append(f"{stale_donate:,} orgs have donate_url not re-verified in 14+ days")

        # 2. Orgs with link_feedback that still have dead website_status
        unresolved_feedback = db.execute("""
            SELECT COUNT(DISTINCT lf.EIN)
            FROM link_feedback lf
            JOIN registry_enriched r ON r.EIN = lf.EIN
            WHERE r.website_status != 'ok'
              AND lf.created_at > date('now', '-30 days')
        """).fetchone()[0]
        if unresolved_feedback:
            findings.append(
                f"{unresolved_feedback:,} orgs have recent donor feedback AND a bad website status"
            )

        # 3. Orgs with no cause_tags but have a mission (tagging backlog)
        tag_backlog = db.execute("""
            SELECT COUNT(*) FROM registry_enriched
            WHERE mission IS NOT NULL AND TRIM(mission) != ''
              AND (cause_tags IS NULL OR cause_tags = '[]')
        """).fetchone()[0]
        if tag_backlog:
            findings.append(f"{tag_backlog:,} orgs have a mission but no cause tags")

        # 4. Financial data age
        stale_financials = db.execute("""
            SELECT COUNT(*) FROM registry_enriched
            WHERE total_revenue IS NOT NULL
              AND (updated_at IS NULL OR updated_at < date('now', '-120 days'))
        """).fetchone()[0]
        if stale_financials:
            findings.append(f"{stale_financials:,} orgs have financial data older than 120 days")

        # 5. Summary stats
        stats = db.execute("""
            SELECT
              COUNT(*) total,
              SUM(CASE WHEN website_status='ok' THEN 1 ELSE 0 END) ok_links,
              SUM(CASE WHEN donate_url IS NOT NULL THEN 1 ELSE 0 END) donate_urls,
              SUM(CASE WHEN cause_tags IS NOT NULL AND cause_tags != '[]' THEN 1 ELSE 0 END) tagged
            FROM registry_enriched
        """).fetchone()

        report_lines = [
            f"MERIT Quality Report — {today}",
            "=" * 50,
            f"Total orgs:        {stats['total']:,}",
            f"Verified links:    {stats['ok_links']:,}",
            f"Direct donate URLs:{stats['donate_urls']:,}",
            f"Cause-tagged:      {stats['tagged']:,}",
            "",
            "Findings:",
        ]
        if findings:
            for f in findings:
                report_lines.append(f"  ⚠  {f}")
        else:
            report_lines.append("  ✓  No issues found")

        # Ask local LLM for a plain-English summary if available
        if findings and self._check_ollama():
            prompt = (
                "You manage a nonprofit giving directory. Summarise these data quality "
                "issues in 2-3 plain sentences a non-technical founder would understand. "
                "Be direct about what matters most:\n\n" + "\n".join(findings)
            )
            try:
                summary = self.llm(prompt, model=_SUMMARY_MODEL)
                report_lines += ["", "Summary:", summary]
            except Exception:
                pass

        report = "\n".join(report_lines)
        report_path = LOG_DIR / f"daily_report_{today}.txt"
        report_path.write_text(report)
        self.log.info(f"Report written to {report_path}")
        self.log.info(f"Findings: {len(findings)}")

        self.log_job(
            processed=stats["total"], updated=0, errors=len(findings),
            notes=json.dumps({"stale_donate": stale_donate,
                              "unresolved_feedback": unresolved_feedback,
                              "tag_backlog": tag_backlog})
        )
        print(report)
        return {"findings": len(findings), "report": str(report_path)}
