"""
Base class for all MERIT data agents.

LLM routing priority (cheapest first):
  1. Local Ollama  — free, uses server GPU
  2. Claude Haiku  — ~$0.001/1K tokens, fallback only
  3. Skip          — if neither available, log and continue

Never calls Sonnet or Opus from an agent. Those are for interactive sessions.
"""

import json, logging, sqlite3, datetime, urllib.request, urllib.error, os
from pathlib import Path

DB_PATH   = Path.home() / "meritgiving" / "data" / "merit_registry.db"
LOG_DIR   = Path.home() / "meritgiving" / "logs"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


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
