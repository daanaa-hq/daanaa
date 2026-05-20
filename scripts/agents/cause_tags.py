"""
Cause Tags Agent
----------------
Extracts 3–5 cause tags per org from their mission statement.

Cost strategy:
  - Local Ollama (qwen2.5:7b) handles everything — FREE
  - Claude Haiku only if Ollama is unreachable — ~$0.001/org
  - Skips orgs already tagged in last 180 days
  - Processes in batches so the GPU stays saturated
"""

import json, re, datetime
from agents.base import BaseAgent

# Prompt tuned for qwen2.5:7b — concise, JSON-only output
_PROMPT = """\
You are tagging a US nonprofit for a giving directory.

Mission: {mission}

Extract 3-5 cause tags that a donor would search for. Use plain English phrases \
(2–4 words max). Focus on what they DO, not how they do it.

Return ONLY a JSON array, no explanation.
Example: ["food security", "youth mentorship", "after-school programs"]

Tags:"""


def _parse_tags(raw: str) -> list[str]:
    """Extract a JSON array from model output, tolerating extra prose."""
    m = re.search(r'\[.*?\]', raw, re.S)
    if not m:
        return []
    try:
        tags = json.loads(m.group(0))
        return [str(t).lower().strip() for t in tags if t][:5]
    except Exception:
        return []


class CauseTagsAgent(BaseAgent):
    name = "cause_tags"
    local_model = "qwen2.5:7b"

    def execute(self, limit=None, batch_size=50, force=False):
        db = self.db()
        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=180)).isoformat()

        rows = db.execute("""
            SELECT EIN, mission, organization_name
            FROM registry_enriched
            WHERE mission IS NOT NULL AND TRIM(mission) != ''
              AND (? OR cause_tags IS NULL OR json_valid(cause_tags) = 0
                   OR updated_at < ?)
            ORDER BY
              CASE WHEN cause_tags IS NULL THEN 0 ELSE 1 END,
              updated_at ASC NULLS FIRST
        """, (1 if force else 0, cutoff)).fetchall()

        if limit:
            rows = rows[:limit]

        total = len(rows)
        if total == 0:
            self.log.info("All orgs already tagged — nothing to do")
            self.log_job(notes="all current")
            return {"processed": 0, "updated": 0}

        # Determine LLM source once
        using_ollama = self._check_ollama()
        llm_source = f"ollama:{self.local_model}" if using_ollama else "claude:haiku"
        self.log.info(
            f"Tagging {total:,} orgs  batch={batch_size}  llm={llm_source}"
        )

        updated, errors, llm_calls = 0, 0, 0
        for i in range(0, total, batch_size):
            batch = rows[i:i + batch_size]
            for row in batch:
                ein, mission = row["EIN"], row["mission"]
                if not mission or len(mission.strip()) < 20:
                    continue
                try:
                    prompt = _PROMPT.format(mission=mission[:600])
                    raw = self.llm(prompt)
                    tags = _parse_tags(raw)
                    llm_calls += 1
                    if tags:
                        db.execute(
                            "UPDATE registry_enriched SET cause_tags=? WHERE EIN=?",
                            (json.dumps(tags), ein),
                        )
                        db.commit()  # commit immediately — don't hold lock across LLM calls
                        updated += 1
                    else:
                        errors += 1
                        self.log.debug(f"No tags parsed for {ein}: {raw[:80]}")
                except Exception as e:
                    errors += 1
                    self.log.warning(f"Tag error {ein}: {e}")
            self.log.info(
                f"  {min(i+batch_size, total)}/{total}  "
                f"updated={updated} errors={errors}"
            )

        self.log_job(
            processed=total, updated=updated, errors=errors,
            llm_calls=llm_calls, llm_source=llm_source,
        )
        return {"processed": total, "updated": updated, "errors": errors,
                "llm": llm_source}
