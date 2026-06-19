"""
Base class for all MERIT data agents.

LLM routing priority (cheapest first):
  1. Local Ollama  — free, uses server GPU
  2. Claude Haiku  — ~$0.001/1K tokens, fallback only
  3. Skip          — if neither available, log and continue

Never calls Sonnet or Opus from an agent. Those are for interactive sessions.

Stewardship layer (P1–P11):
  Every agent inherits stewardship_check(), log_agent_decision(), and a
  human-gate for consequential actions. Violations are logged and surfaced —
  never silently swallowed. See STEWARDSHIP.md for the 11 principles.
"""

import json, logging, sqlite3, datetime, urllib.request, urllib.error, os, hashlib
from pathlib import Path

DB_PATH   = Path.home() / "meritgiving" / "data" / "merit_registry.db"
LOG_DIR   = Path.home() / "meritgiving" / "logs"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

# Actions that must not execute without explicit human approval.
# Agents calling these with human_gate=True will raise if approval is missing.
HUMAN_GATE_ACTIONS = {
    "bulk_score_update",
    "badge_grant",
    "featured_placement",
    "claim_flag",
    "bulk_email_send",
    "vendor_approve",
    "score_override",
}


class BaseAgent:
    name: str = "base"
    # Local model for this agent — override in subclass
    local_model: str = "qwen2.5:7b"

    def __init__(self):
        LOG_DIR.mkdir(exist_ok=True)
        self.log = logging.getLogger(self.name)
        if not self.log.handlers:
            fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                                    datefmt="%Y-%m-%d %H:%M:%S")
            fh = logging.FileHandler(LOG_DIR / f"agent_{self.name}.log")
            fh.setFormatter(fmt)
            sh = logging.StreamHandler()
            sh.setFormatter(fmt)
            self.log.addHandler(fh)
            self.log.addHandler(sh)
            self.log.setLevel(logging.INFO)
        self._db: sqlite3.Connection | None = None
        self._start = datetime.datetime.utcnow()
        self._ollama_ok: bool | None = None  # cached check

    # ── Database ──────────────────────────────────────────────────────────────

    def db(self) -> sqlite3.Connection:
        if self._db is None:
            self._db = sqlite3.connect(DB_PATH, timeout=60)
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.execute("PRAGMA synchronous=NORMAL")
            self._db.row_factory = sqlite3.Row
            self._ensure_job_log()
        return self._db

    def _ensure_job_log(self):
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS agent_job_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                agent        TEXT    NOT NULL,
                started_at   TEXT    NOT NULL,
                finished_at  TEXT,
                processed    INTEGER DEFAULT 0,
                updated      INTEGER DEFAULT 0,
                errors       INTEGER DEFAULT 0,
                llm_calls    INTEGER DEFAULT 0,
                llm_source   TEXT,
                notes        TEXT
            )
        """)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS agent_decision_log (
                id                       INTEGER PRIMARY KEY AUTOINCREMENT,
                agent                    TEXT NOT NULL,
                action                   TEXT NOT NULL,
                input_hash               TEXT,
                output_summary           TEXT,
                evidence                 TEXT,
                human_approved           INTEGER DEFAULT 0,
                principle_checks_passed  INTEGER DEFAULT 1,
                principle_violations     TEXT,
                created_at               TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._db.commit()

    def log_job(self, processed=0, updated=0, errors=0,
                llm_calls=0, llm_source="", notes=""):
        self.db().execute("""
            INSERT INTO agent_job_log
              (agent, started_at, finished_at, processed, updated, errors,
               llm_calls, llm_source, notes)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (self.name, self._start.isoformat(),
              datetime.datetime.utcnow().isoformat(),
              processed, updated, errors, llm_calls, llm_source, notes))
        self.db().commit()

    def last_run(self) -> datetime.datetime | None:
        """When did this agent last complete successfully?"""
        row = self.db().execute("""
            SELECT finished_at FROM agent_job_log
            WHERE agent=? AND finished_at IS NOT NULL
            ORDER BY id DESC LIMIT 1
        """, (self.name,)).fetchone()
        if not row:
            return None
        return datetime.datetime.fromisoformat(row[0])

    def hours_since_last_run(self) -> float:
        lr = self.last_run()
        if lr is None:
            return float("inf")
        return (datetime.datetime.utcnow() - lr).total_seconds() / 3600

    # ── LLM routing ───────────────────────────────────────────────────────────

    def _check_ollama(self) -> bool:
        if self._ollama_ok is not None:
            return self._ollama_ok
        try:
            urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3)
            self._ollama_ok = True
        except Exception:
            self._ollama_ok = False
        return self._ollama_ok

    def llm(self, prompt: str, model: str | None = None) -> str:
        """Call local Ollama first; fall back to Claude Haiku if unavailable."""
        if self._check_ollama():
            return self._ollama(prompt, model or self.local_model)
        return self._haiku(prompt)

    def _ollama(self, prompt: str, model: str) -> str:
        payload = json.dumps({
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 256},
        }).encode()
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())["response"].strip()

    def _haiku(self, prompt: str) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic()
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text.strip()
        except Exception as e:
            self.log.warning(f"Claude Haiku fallback failed: {e}")
            return ""

    # ── Stewardship layer ────────────────────────────────────────────────────

    def stewardship_check(self, action: str, context: dict) -> list[str]:
        """
        Check an action + context against core stewardship principles.
        Returns a list of violation strings (empty = all clear).

        Principles checked:
          P3 — trust signals must be evidence-based
          P4 — small orgs must not be disadvantaged by scale
          P7 — paying partners cannot influence visibility/scores
          P8 — agents must never handle or route funds
        """
        violations = []

        # P3: any action that produces a trust signal needs an evidence source
        if action in ("rank_org", "score_org", "badge_org", "feature_org"):
            if not context.get("evidence_source"):
                violations.append(
                    "P3: Trust signal action requires evidence_source in context"
                )

        # P4: sorting or ranking by raw revenue disadvantages small orgs
        if action in ("search_sort", "rank_org", "list_orgs"):
            if context.get("sort_by") in ("revenue", "total_revenue", "size"):
                violations.append(
                    "P4: Sorting/ranking by revenue disadvantages small orgs — "
                    "use peer-relative score instead"
                )

        # P7: paying partner EIN cannot boost visibility
        if context.get("paying_partner_ein") and action in (
            "rank_org", "feature_org", "badge_org", "boost_visibility"
        ):
            violations.append(
                "P7: Paying partner relationship must not influence "
                "ranking, featuring, or visibility outcomes"
            )

        # P8: agents must never route or hold funds
        if action in ("process_payment", "hold_donation", "route_funds", "escrow"):
            violations.append(
                "P8: Agents must never process, hold, or route donor funds — "
                "hand off to org's own processor only"
            )

        return violations

    def log_agent_decision(
        self,
        action: str,
        input_data: object,
        output_summary: str,
        evidence: str = "",
        human_approved: bool = False,
        violations: list[str] | None = None,
    ) -> None:
        """Persist a decision record to agent_decision_log for auditability (P9)."""
        input_hash = hashlib.sha256(
            json.dumps(input_data, default=str, sort_keys=True).encode()
        ).hexdigest()[:16]
        self.db().execute(
            """INSERT INTO agent_decision_log
               (agent, action, input_hash, output_summary, evidence,
                human_approved, principle_checks_passed, principle_violations)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                self.name,
                action,
                input_hash,
                str(output_summary)[:500],
                evidence[:500] if evidence else "",
                1 if human_approved else 0,
                0 if violations else 1,
                json.dumps(violations) if violations else None,
            ),
        )
        self.db().commit()

    def llm_with_stewardship(
        self,
        prompt: str,
        action: str,
        context: dict,
        model: str | None = None,
        require_human_gate: bool = False,
    ) -> str:
        """
        llm() wrapper that runs stewardship checks before and after the call.

        - Checks context for principle violations before calling the LLM.
        - Logs the decision with evidence and any violations.
        - Raises ValueError if action is in HUMAN_GATE_ACTIONS and
          require_human_gate is True but human_approved is not in context.
        """
        violations = self.stewardship_check(action, context)
        if violations:
            for v in violations:
                self.log.warning(f"[STEWARDSHIP] {v}")

        if action in HUMAN_GATE_ACTIONS and require_human_gate:
            if not context.get("human_approved"):
                raise ValueError(
                    f"Action '{action}' requires human approval. "
                    f"Pass human_approved=True in context after review."
                )

        result = self.llm(prompt, model)

        self.log_agent_decision(
            action=action,
            input_data={"prompt_len": len(prompt), "context_keys": list(context.keys())},
            output_summary=result[:200] if result else "(empty)",
            evidence=context.get("evidence_source", ""),
            human_approved=bool(context.get("human_approved")),
            violations=violations if violations else None,
        )
        return result

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def run(self, **kwargs):
        self._start = datetime.datetime.utcnow()
        self.log.info(f"=== {self.name} starting ===")
        try:
            result = self.execute(**kwargs)
            self.log.info(f"=== {self.name} done: {result} ===")
            return result
        except Exception as e:
            self.log.error(f"Agent failed: {e}", exc_info=True)
            raise
        finally:
            if self._db:
                self._db.close()
                self._db = None

    def execute(self, **kwargs):
        raise NotImplementedError
