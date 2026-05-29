#!/usr/bin/env python3
"""
Daanaa Ops Dashboard — port 5001
Live dashboard: tasks (editable), pipeline, OKRs, git log, ops chat.
POST /api/task/toggle  — flip checkbox in tasks.md
POST /api/task/comment — append comment line under a task
POST /api/chat         — routes to Claude API or local Qwen (model param)
POST /api/chat/save    — persist chat transcript to meritgiving-ops/chats/

Model routing:
  auto             → Claude Sonnet 4.6 first; Qwen fallback if no API key
  claude-sonnet-46 → claude-sonnet-4-6 via Anthropic API
  claude-haiku-45  → claude-haiku-4-5-20251001 via Anthropic API
  local            → Qwen2.5-32B on port 11437 (always-free, no key needed)

API key: set ANTHROPIC_API_KEY in meritgiving/.env  (sk-ant-api03-...)
"""
import sqlite3, subprocess, pathlib, re, datetime, os, html, json, threading, hmac
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import urllib.request, urllib.error

BASE         = pathlib.Path.home() / "meritgiving"
DB           = BASE / "data/merit_registry.db"
TASKS        = BASE / "meritgiving-ops/state/tasks.md"
CHATS        = BASE / "meritgiving-ops/chats"
LOG_MISSIONS = BASE / "logs/generate_missions.log"
LOCAL_LLM    = "http://127.0.0.1:11437/v1/chat/completions"
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
_lock        = threading.Lock()

CHATS.mkdir(parents=True, exist_ok=True)

# ── load .env ─────────────────────────────────────────────────────────────────

def _load_dotenv():
    env_file = BASE / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ[k.strip()] = v.strip()  # .env always wins

_load_dotenv()

_CLAUDE_MODELS = {
    "claude-sonnet-46": "claude-sonnet-4-6",
    "claude-haiku-45":  "claude-haiku-4-5-20251001",
}

def _api_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    return key if len(key) > 20 else None

def _ops_token():
    tok = os.environ.get("OPS_TOKEN", "")
    return tok if len(tok) >= 16 else None

def _token_ok(candidate):
    """Constant-time compare against OPS_TOKEN. If no token is configured, auth is open."""
    expected = _ops_token()
    if not expected:
        return True  # no token set → dashboard runs unprotected (dev fallback)
    if not candidate:
        return False
    return hmac.compare_digest(candidate, expected)

# ── file helpers ──────────────────────────────────────────────────────────────

def tail_bytes(path, n=1400):
    try:
        with open(path, 'rb') as f:
            f.seek(0, 2); size = f.tell()
            f.seek(max(0, size - n), 0)
            return f.read().decode('utf-8', errors='replace')
    except Exception:
        return ""

def pgrep(pattern):
    out = subprocess.run(["pgrep", "-af", pattern], capture_output=True, text=True).stdout
    return pattern in out

# ── DB metrics ────────────────────────────────────────────────────────────────

def db_metrics():
    try:
        conn = sqlite3.connect(str(DB), timeout=5)
        total    = conn.execute("SELECT COUNT(*) FROM registry_enriched").fetchone()[0]
        missions = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE mission IS NOT NULL AND mission != ''").fetchone()[0]
        ai_web   = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE mission_source='ai_web'").fetchone()[0]
        donate   = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE donate_url IS NOT NULL AND donate_confidence >= 90").fetchone()[0]
        websites = conn.execute("SELECT COUNT(*) FROM registry_enriched WHERE website_status='ok'").fetchone()[0]
        q_pend   = conn.execute("SELECT COUNT(*) FROM donate_work_queue WHERE completed_at IS NULL").fetchone()[0]
        conn.close()
        return dict(total=total, missions=missions, ai_web=ai_web,
                    donate=donate, websites=websites, q_pend=q_pend)
    except Exception as e:
        return dict(error=str(e), total=1811930, missions=0, ai_web=0, donate=0, websites=0, q_pend=0)

def mission_progress():
    raw = tail_bytes(LOG_MISSIONS)
    m = re.search(r'\[\s*(\d+\.\d+)%\]\s+(\S+) written\s+(\S+) errors\s+(\S+)/sec\s+ETA (\S+)', raw)
    if m:
        pct, written, errors, rate, eta = m.groups()
        try:
            return dict(pct=float(pct),
                        written=int(written.replace(",", "")),
                        errors=int(errors.replace(",", "")),
                        rate=rate, eta=eta)
        except ValueError:
            return None
    return None

def link_progress():
    logs = sorted((BASE / "logs").glob("link_workers_*.log"),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    if not logs:
        return None
    raw = tail_bytes(logs[0])
    m = re.search(r'verified=(\d+)\s+review=(\d+)\s+no_link=(\d+)\s+blocked=(\d+)\s+([\d.]+) orgs/s', raw)
    if m:
        ver, rev, no_lnk, blk, rate = m.groups()
        return dict(verified=int(ver), no_link=int(no_lnk), blocked=int(blk), rate=rate)
    return None

def git_log():
    try:
        out = subprocess.run(
            ["git", "-C", str(BASE), "log", "--oneline", "--since=48 hours ago"],
            capture_output=True, text=True
        ).stdout
        if not out.strip():
            out = subprocess.run(
                ["git", "-C", str(BASE), "log", "--oneline", "-6"],
                capture_output=True, text=True
            ).stdout
        return [html.escape(l.strip()) for l in out.strip().splitlines() if l.strip()][:8]
    except Exception:
        return []

def api_health():
    try:
        req = urllib.request.Request("http://localhost:5000/health")
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.status == 200
    except Exception:
        return False

# ── tasks.md parsing & mutation ───────────────────────────────────────────────

def read_task_lines():
    try:
        return TASKS.read_text().splitlines()
    except Exception:
        return []

def parse_tasks(lines):
    """Returns list of (section, [(done, text, line_index, comment_lines)])."""
    sections = []
    current_section = None
    current_tasks = []
    for i, line in enumerate(lines):
        if line.startswith("## "):
            if current_section is not None:
                sections.append((current_section, current_tasks))
            current_section = line[3:].strip()
            current_tasks = []
        elif line.startswith("- [x]") or line.startswith("- [ ]"):
            done = line.startswith("- [x]")
            text = line[6:].strip()
            current_tasks.append((done, text, i, []))
        elif current_tasks and line.startswith("  > "):
            # comment attached to previous task
            prev = current_tasks[-1]
            current_tasks[-1] = (prev[0], prev[1], prev[2], prev[3] + [(i, line[4:].strip())])
    if current_section is not None:
        sections.append((current_section, current_tasks))
    return sections

def toggle_task(line_index: int):
    with _lock:
        lines = read_task_lines()
        if 0 <= line_index < len(lines):
            l = lines[line_index]
            if l.startswith("- [ ]"):
                lines[line_index] = "- [x]" + l[5:]
            elif l.startswith("- [x]"):
                lines[line_index] = "- [ ]" + l[5:]
            TASKS.write_text("\n".join(lines) + "\n")
            return True
        return False

def add_comment(line_index: int, comment: str):
    with _lock:
        lines = read_task_lines()
        if 0 <= line_index < len(lines):
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            comment_line = f"  > [{now}] {comment.strip()}"
            lines.insert(line_index + 1, comment_line)
            TASKS.write_text("\n".join(lines) + "\n")
            return True
        return False

# ── local LLM chat ────────────────────────────────────────────────────────────

def build_ops_context(db, mp):
    total    = db.get("total", 1811930)
    missions = db.get("missions", 0)
    donate   = db.get("donate", 0)
    websites = db.get("websites", 0)
    q_pend   = db.get("q_pend", 0)
    mp_pct   = mp["pct"] if mp else (missions / total * 100 if total else 0)

    tasks_text = ""
    try:
        tasks_text = TASKS.read_text()[:2000]
    except Exception:
        pass

    return f"""You are the Daanaa Ops Assistant — a concise, expert AI for the Daanaa nonprofit-discovery platform.

## Current pipeline state ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})
- Missions: {missions:,} / {total:,} ({mp_pct:.1f}%) — ai_web={db.get('ai_web',0):,}
- Donate URLs: {donate:,} verified (≥90 confidence) — {q_pend:,} pending
- Live websites: {websites:,}
- Embeddings: 1,811,930 (100%) — complete

## Open task list
{tasks_text}

## About Daanaa
Civic nonprofit-discovery platform. 1.8M IRS-registered 501(c)(3) orgs. Free for donors and nonprofits.
Legal entity: EcoMargins Consulting LLC (EIN exists, Houston TX). DBA Daanaa pending.
Revenue target: EcoMargins ESG portal (Oct 2026). Credit card: $4K/$13K used, 0% APR until Mar 2027.
Gates: Gate 0 ✓ (2026-05-28), Gate 1 legal (overdue), Gate 2 Jun 16, Gate 3 Jul 14, Gate 7 launch Nov 10.
Stack: Flask/SQLite API (port 5000), React 19 + Vite frontend, local GPU (Ryzen 9700X, R9700 32GB).

Answer concisely. For code or data questions, be specific. For action items, be direct."""

# ── LLM routing ───────────────────────────────────────────────────────────────

def _call_claude(system: str, user: str, model_id: str) -> str:
    key = _api_key()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in meritgiving/.env")
    payload = json.dumps({
        "model": model_id,
        "max_tokens": 1024,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode()
    req = urllib.request.Request(
        ANTHROPIC_API,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    return data["content"][0]["text"].strip()

def _call_local(system: str, user: str) -> str:
    payload = json.dumps({
        "model": "Qwen2.5-32B-Instruct-Q4_K_M",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "max_tokens": 512,
        "temperature": 0.4,
    }).encode()
    req = urllib.request.Request(
        LOCAL_LLM,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    return data["choices"][0]["message"]["content"].strip()

def call_llm(system: str, user: str, model: str = "auto") -> tuple[str, str]:
    """Returns (reply_text, model_used_label)."""
    if model in _CLAUDE_MODELS:
        model_id = _CLAUDE_MODELS[model]
        try:
            return _call_claude(system, user, model_id), model_id
        except Exception as e:
            return f"[Claude API error: {e}]", model_id

    if model == "local":
        try:
            return _call_local(system, user), "Qwen2.5-32B (local)"
        except Exception as e:
            return f"[Local LLM error: {e}]", "local"

    # auto: Claude Sonnet 4.6 → Qwen fallback
    if _api_key():
        try:
            reply = _call_claude(system, user, "claude-sonnet-4-6")
            return reply, "claude-sonnet-4-6"
        except Exception:
            pass
    try:
        return _call_local(system, user), "Qwen2.5-32B (local)"
    except Exception as e:
        return f"[All LLMs unavailable: {e}]", "none"

def save_chat(history: list) -> str:
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    chat_file = CHATS / f"chat-{date_str}.md"
    ts = datetime.datetime.now().strftime("%H:%M")
    lines = [f"\n---\n*Saved {ts}*\n"]
    for msg in history:
        role  = msg.get("role", "?")
        text  = msg.get("content", "")
        model = msg.get("model", "")
        label = "**You**" if role == "user" else f"**Assistant** ({model})" if model else "**Assistant**"
        lines.append(f"{label}: {text}\n")
    with open(chat_file, "a") as f:
        f.write("\n".join(lines))
    return str(chat_file.relative_to(BASE))

# ── HTML render ───────────────────────────────────────────────────────────────

CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --navy:#0A1628;--navy-mid:#1A2744;--navy-card:#0F1E38;--navy-hover:#162236;
  --gold:#C9A96E;--gold-bright:#D4B87A;
  --cream:#F5F0EB;--cream-dim:rgba(245,240,235,0.55);--cream-faint:rgba(245,240,235,0.25);
  --green:#4ADE80;--red:#F87171;--amber:#FBBF24;
  --border:rgba(201,169,110,0.13);
}
html{background:var(--navy);color:var(--cream);font-family:'DM Sans',Inter,system-ui,sans-serif;font-size:14px;-webkit-font-smoothing:antialiased}
body{min-height:100vh;padding-bottom:3rem}

/* topbar */
.topbar{background:var(--navy-mid);border-bottom:1px solid var(--border);padding:.75rem 1.5rem;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.topbar-left{display:flex;align-items:center;gap:.75rem}
.wordmark{font-family:Georgia,serif;font-style:italic;font-size:1.4rem;font-weight:500;color:var(--gold)}
.topbar-sub{font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;color:var(--cream-dim)}
.topbar-right{font-size:.72rem;color:var(--cream-faint);text-align:right}

/* layout */
.wrap{max-width:1100px;margin:0 auto;padding:1.25rem}
.sec-label{font-size:.65rem;letter-spacing:.12em;text-transform:uppercase;color:var(--cream-faint);margin:1.25rem 0 .5rem .1rem}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media(max-width:680px){.grid-2{grid-template-columns:1fr}}

/* stat strip */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:.75rem;margin-bottom:1rem}
@media(max-width:680px){.stats{grid-template-columns:repeat(2,1fr)}}
.stat{background:var(--navy-card);border:1px solid var(--border);border-radius:10px;padding:.9rem 1.1rem}
.stat-val{font-family:Georgia,serif;font-size:1.7rem;font-weight:500;color:var(--gold-bright);line-height:1}
.stat-lbl{font-size:.65rem;letter-spacing:.05em;text-transform:uppercase;color:var(--cream-faint);margin-top:.3rem}

/* card */
.card{background:var(--navy-card);border:1px solid var(--border);border-radius:10px;padding:1rem 1.2rem;margin-bottom:1rem}
.card-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:.8rem}
.card-title{font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--gold)}
.badges{display:flex;gap:.4rem}
.badge{font-size:.62rem;padding:.18rem .5rem;border-radius:999px;font-weight:600}
.badge-o{background:rgba(251,191,36,.12);color:var(--amber)}
.badge-d{background:rgba(74,222,128,.1);color:var(--green)}

/* tasks */
.task-row{display:flex;align-items:flex-start;gap:.5rem;padding:.3rem 0;border-top:1px solid rgba(201,169,110,.07);font-size:.82rem;line-height:1.45;cursor:pointer;transition:background .15s;border-radius:4px}
.task-card .task-row:first-of-type{border-top:none}
.task-row:hover{background:var(--navy-hover);padding-left:.3rem}
.task-cb{width:1rem;text-align:center;flex-shrink:0;font-size:.78rem;padding-top:.05rem}
.task-body{flex:1}
.task-text{}
.task-comments{font-size:.75rem;color:var(--cream-faint);margin-top:.15rem;padding-left:.2rem}
.task-comment-line{padding:.05rem 0}
.task-done .task-text{color:var(--cream-faint);text-decoration:line-through}
.task-done .task-cb{color:var(--green)}
.task-open .task-cb{color:var(--amber)}
.add-comment-btn{font-size:.65rem;color:var(--cream-faint);background:none;border:none;cursor:pointer;padding:.1rem .3rem;border-radius:3px;opacity:.6;transition:opacity .15s}
.add-comment-btn:hover{opacity:1;color:var(--gold)}
.comment-input-row{display:flex;gap:.4rem;margin-top:.3rem;padding-left:1.5rem}
.comment-input{flex:1;background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:6px;color:var(--cream);font-size:.78rem;padding:.3rem .6rem;outline:none}
.comment-input:focus{border-color:rgba(201,169,110,.4)}
.comment-submit{background:var(--gold);color:var(--navy);border:none;border-radius:6px;padding:.3rem .7rem;font-size:.72rem;font-weight:600;cursor:pointer}
.comment-submit:hover{background:var(--gold-bright)}

/* task grid */
.task-grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media(max-width:680px){.task-grid{grid-template-columns:1fr}}

/* processes */
.proc-row{display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:.85rem}
.proc-pill{font-size:.7rem;padding:.28rem .65rem;border-radius:999px;font-weight:500}
.pill-ok{background:rgba(74,222,128,.12);color:var(--green);border:1px solid rgba(74,222,128,.2)}
.pill-off{background:rgba(248,113,113,.1);color:var(--red);border:1px solid rgba(248,113,113,.15)}

/* progress */
.prog-row{display:flex;align-items:center;gap:.75rem;margin-bottom:.5rem;flex-wrap:wrap}
.prog-lbl{font-size:.7rem;font-weight:600;color:var(--cream-dim);width:6rem;flex-shrink:0}
.prog-track{flex:1;min-width:80px;height:5px;background:rgba(255,255,255,.07);border-radius:999px;overflow:hidden}
.prog-fill{height:100%;background:linear-gradient(90deg,var(--gold),var(--gold-bright));border-radius:999px}
.prog-fill-2{background:linear-gradient(90deg,#4ADE80,#86EFAC)}
.prog-val{font-size:.68rem;color:var(--cream-faint)}

/* gates */
.gate-row{display:grid;grid-template-columns:1.4rem 4.5rem 1fr 4.5rem;gap:.5rem;align-items:center;padding:.38rem 0;border-top:1px solid rgba(201,169,110,.07);font-size:.78rem}
.gate-card .gate-row:first-of-type{border-top:none}
.gate-icon{text-align:center;font-size:.78rem}
.gate-name{font-weight:600;color:var(--cream-dim)}
.gate-label{color:var(--cream)}
.gate-eta{text-align:right;font-size:.7rem;color:var(--cream-faint)}
.gate-done .gate-icon{color:var(--green)}
.gate-done .gate-name,.gate-done .gate-label{color:var(--cream-faint);text-decoration:line-through}
.gate-open .gate-icon{color:var(--amber)}

/* commits */
.commit-row{display:flex;gap:.6rem;padding:.3rem 0;border-top:1px solid rgba(201,169,110,.07);font-size:.76rem}
.commit-card .commit-row:first-of-type{border-top:none}
.commit-sha{color:var(--gold);font-family:monospace;flex-shrink:0;font-size:.7rem}
.commit-msg{color:var(--cream-dim)}

/* chat */
.chat-area{max-height:340px;overflow-y:auto;margin-bottom:.75rem;display:flex;flex-direction:column;gap:.5rem}
.chat-bubble{padding:.6rem .85rem;border-radius:8px;font-size:.82rem;line-height:1.55;max-width:92%;white-space:pre-wrap}
.chat-user{background:rgba(201,169,110,.12);color:var(--cream);align-self:flex-end;border:1px solid rgba(201,169,110,.2)}
.chat-assistant{background:rgba(255,255,255,.05);color:var(--cream-dim);align-self:flex-start;border:1px solid rgba(255,255,255,.07)}
.chat-meta{font-size:.62rem;color:var(--cream-faint);align-self:flex-start;padding:.0rem .2rem}

/* model selector */
.model-bar{display:flex;align-items:center;gap:.35rem;margin-bottom:.6rem;flex-wrap:wrap}
.model-chip{font-size:.68rem;padding:.25rem .65rem;border-radius:999px;border:1px solid var(--border);
  color:var(--cream-faint);background:none;cursor:pointer;transition:all .15s;font-family:inherit}
.model-chip:hover{border-color:var(--gold);color:var(--gold)}
.model-chip.active{background:rgba(201,169,110,.15);border-color:var(--gold);color:var(--gold);font-weight:600}
.model-chip.needs-key{opacity:.45}
.model-chip.needs-key::after{content:" 🔑";font-size:.6rem}

.chat-row{display:flex;gap:.5rem;margin-top:.5rem}
.chat-input{flex:1;background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:8px;color:var(--cream);font-family:inherit;font-size:.84rem;padding:.55rem .85rem;outline:none;resize:none}
.chat-input:focus{border-color:rgba(201,169,110,.45);box-shadow:0 0 0 2px rgba(201,169,110,.08)}
.chat-btn{background:var(--gold);color:var(--navy);border:none;border-radius:8px;padding:0 1rem;font-size:.8rem;font-weight:600;cursor:pointer;white-space:nowrap}
.chat-btn:hover{background:var(--gold-bright)}
.chat-btn:disabled{opacity:.5;cursor:wait}
.chat-actions{display:flex;gap:.5rem;margin-top:.4rem;justify-content:flex-end}
.chat-action-btn{background:none;border:1px solid var(--border);color:var(--cream-faint);border-radius:6px;padding:.25rem .65rem;font-size:.68rem;cursor:pointer;transition:all .15s}
.chat-action-btn:hover{border-color:var(--gold);color:var(--gold)}
.chat-notice{font-size:.65rem;color:var(--cream-faint);margin-top:.35rem}
"""

JS = r"""
// ── task toggle ───────────────────────────────────────────────────────────
function toggleTask(lineIdx) {
  fetch('/api/task/toggle', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({line: lineIdx})
  }).then(r => r.json()).then(d => {
    if (d.ok) location.reload();
  });
}

// ── comment UI ────────────────────────────────────────────────────────────
function showCommentBox(lineIdx) {
  const existing = document.getElementById('cbox-' + lineIdx);
  if (existing) { existing.remove(); return; }
  const row = document.getElementById('task-' + lineIdx);
  const box = document.createElement('div');
  box.id = 'cbox-' + lineIdx;
  box.className = 'comment-input-row';
  box.innerHTML = `
    <input class="comment-input" placeholder="Add a note..." id="ci-${lineIdx}"/>
    <button class="comment-submit" onclick="submitComment(${lineIdx})">Save</button>`;
  row.after(box);
  document.getElementById('ci-' + lineIdx).focus();
}

function submitComment(lineIdx) {
  const val = document.getElementById('ci-' + lineIdx).value.trim();
  if (!val) return;
  fetch('/api/task/comment', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({line: lineIdx, comment: val})
  }).then(r => r.json()).then(d => {
    if (d.ok) location.reload();
  });
}

// ── model selection ───────────────────────────────────────────────────────
const MODELS = [
  { id:'auto',             label:'Auto',          needsKey:false },
  { id:'claude-sonnet-46', label:'Sonnet 4.6',    needsKey:true  },
  { id:'claude-haiku-45',  label:'Haiku 4.5',     needsKey:true  },
  { id:'local',            label:'Qwen (local)',  needsKey:false },
];
let activeModel  = localStorage.getItem('ops_model') || 'auto';
let apiKeyIsSet  = API_KEY_SET;  // injected from server at render time

function renderModelBar() {
  const bar = document.getElementById('model-bar');
  bar.innerHTML = MODELS.map(m => {
    const isActive   = m.id === activeModel;
    const needsKey   = m.needsKey && !apiKeyIsSet;
    return `<button class="model-chip${isActive ? ' active' : ''}${needsKey ? ' needs-key' : ''}"
      onclick="setModel('${m.id}')" title="${needsKey ? 'Needs ANTHROPIC_API_KEY in .env' : m.label}">
      ${m.label}</button>`;
  }).join('');
}

function setModel(id) {
  activeModel = id;
  localStorage.setItem('ops_model', id);
  renderModelBar();
}

// ── chat ──────────────────────────────────────────────────────────────────
const chatArea  = document.getElementById('chat-area');
const chatInput = document.getElementById('chat-input');
const chatBtn   = document.getElementById('chat-send');
let lastResponse = '';
let chatHistory  = [];  // for save

function addBubble(text, who, meta) {
  const div = document.createElement('div');
  div.className = 'chat-bubble chat-' + who;
  div.textContent = text;
  chatArea.appendChild(div);
  if (meta) {
    const m = document.createElement('div');
    m.className = 'chat-meta';
    m.textContent = meta;
    chatArea.appendChild(m);
  }
  chatArea.scrollTop = chatArea.scrollHeight;
  return div;
}

function saveChat() {
  fetch('/api/chat/save', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({history: chatHistory})
  }).then(r => r.json()).then(d => {
    if (d.path) addBubble('Saved to ' + d.path, 'assistant');
  });
}

chatBtn.addEventListener('click', sendChat);
chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
});

function sendChat() {
  const msg = chatInput.value.trim();
  if (!msg) return;
  chatInput.value = '';
  chatBtn.disabled = true;
  chatBtn.textContent = '…';
  addBubble(msg, 'user');
  const thinking = addBubble('Thinking…', 'assistant');

  fetch('/api/chat', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({message: msg, model: activeModel})
  }).then(r => r.json()).then(d => {
    const reply = d.reply || d.error || '(no response)';
    thinking.textContent = reply;
    lastResponse = reply;
    chatHistory.push({role:'user', content: msg});
    chatHistory.push({role:'assistant', content: reply, model: d.model});
    // update key-set status for model chips
    if (typeof d.api_key_set !== 'undefined') {
      apiKeyIsSet = d.api_key_set;
      renderModelBar();
    }
    // show which model answered
    if (d.model) {
      const meta = thinking.nextSibling;
      if (meta && meta.className === 'chat-meta') meta.textContent = '↳ ' + d.model;
      else {
        const m = document.createElement('div');
        m.className = 'chat-meta';
        m.textContent = '↳ ' + d.model;
        thinking.after(m);
      }
    }
    chatBtn.disabled = false;
    chatBtn.textContent = 'Ask';
  }).catch(e => {
    thinking.textContent = '[error: ' + e + ']';
    chatBtn.disabled = false;
    chatBtn.textContent = 'Ask';
  });
}

renderModelBar();
"""

def render_page():
    now  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    db   = db_metrics()
    mp   = mission_progress()
    lp   = link_progress()
    commits = git_log()
    api_ok  = api_health()

    total    = db.get("total", 1811930)
    missions = db.get("missions", 0)
    donate   = db.get("donate", 0)
    websites = db.get("websites", 0)
    q_pend   = db.get("q_pend", 0)
    ai_web   = db.get("ai_web", 0)
    mission_pct = missions / total * 100 if total else 0
    mp_pct  = mp["pct"] if mp else mission_pct

    # Processes
    procs = {
        "Mission gen":  pgrep("generate_missions"),
        "Donate links": pgrep("donation_link"),
        "Web crawler":  pgrep("fetch_org_websites"),
        "LLM :11437":   pgrep("11437"),
        "Flask API":    api_ok,
    }

    # Tasks
    lines = read_task_lines()
    sections = parse_tasks(lines)
    open_count = sum(1 for _, ts in sections for d, _, _, _ in ts if not d)
    done_count = sum(1 for _, ts in sections for d, _, _, _ in ts if d)

    # ── task cards ────────────────────────────────────────────────────────────
    sections_html = ""
    for section, items in sections:
        sec_open = sum(1 for d, _, _, _ in items if not d)
        sec_done = sum(1 for d, _, _, _ in items if d)
        rows = ""
        for done, text, line_idx, comments in items:
            cls  = "task-done" if done else "task-open"
            cb   = "✓" if done else "○"
            comment_html = ""
            if comments:
                comment_html = '<div class="task-comments">' + \
                    "".join(f'<div class="task-comment-line">↳ {html.escape(c)}</div>'
                            for _, c in comments) + '</div>'
            rows += f"""<div class="task-row {cls}" id="task-{line_idx}">
              <span class="task-cb" onclick="toggleTask({line_idx})" title="Toggle">{cb}</span>
              <div class="task-body">
                <span class="task-text">{html.escape(text)}</span>
                {comment_html}
                <button class="add-comment-btn" onclick="showCommentBox({line_idx})" title="Add note">+ note</button>
              </div>
            </div>\n"""
        sections_html += f"""<div class="card task-card">
          <div class="card-hd">
            <span class="card-title">{html.escape(section)}</span>
            <div class="badges">
              <span class="badge badge-o">{sec_open} open</span>
              <span class="badge badge-d">{sec_done} done</span>
            </div>
          </div>
          {rows}
        </div>"""

    # ── process pills ─────────────────────────────────────────────────────────
    proc_html = "".join(
        f'<span class="proc-pill {"pill-ok" if r else "pill-off"}">{"●" if r else "○"} {html.escape(n)}</span>'
        for n, r in procs.items()
    )

    # ── progress bars ─────────────────────────────────────────────────────────
    mp_eta = f'{mp["rate"]}/sec · ETA {mp["eta"]}' if mp else ""
    prog_html = f"""
      <div class="prog-row">
        <span class="prog-lbl">Missions</span>
        <div class="prog-track"><div class="prog-fill" style="width:{min(mp_pct,100):.1f}%"></div></div>
        <span class="prog-val">{mp_pct:.1f}% ({missions:,}/{total:,}) {mp_eta}</span>
      </div>
      <div class="prog-row">
        <span class="prog-lbl">Donate links</span>
        <div class="prog-track"><div class="prog-fill prog-fill-2" style="width:{min(donate/2500*100,100):.1f}%"></div></div>
        <span class="prog-val">{donate:,} verified · {q_pend:,} pending{(' · ' + lp['rate'] + ' orgs/s') if lp else ''}</span>
      </div>
      <div class="prog-row">
        <span class="prog-lbl">Embeddings</span>
        <div class="prog-track"><div class="prog-fill" style="width:100%"></div></div>
        <span class="prog-val">1,811,930 / 1,811,930 — complete</span>
      </div>"""

    # ── gates ─────────────────────────────────────────────────────────────────
    gates = [
        ("Gate 0", "Security + Tests",      True,  "2026-05-28"),
        ("Gate 1", "Legal Foundation",      False, "Overdue"),
        ("Gate 2", "Credits & Infra",       False, "Jun 16"),
        ("Gate 3", "Data Foundation",       False, "Jul 14"),
        ("Gate 5", "Trust Foundation",      False, "Sep 8"),
        ("Gate 7", "Public Launch",         False, "Nov 10"),
    ]
    gate_html = "".join(
        f'<div class="gate-row {"gate-done" if d else "gate-open"}">'
        f'<span class="gate-icon">{"✓" if d else "◻"}</span>'
        f'<span class="gate-name">{g}</span>'
        f'<span class="gate-label">{lbl}</span>'
        f'<span class="gate-eta">{eta}</span></div>'
        for g, lbl, d, eta in gates
    )

    # ── commits ───────────────────────────────────────────────────────────────
    commit_html = ""
    for c in commits:
        parts = c.split(" ", 1)
        sha = parts[0]; msg = parts[1] if len(parts) > 1 else ""
        commit_html += f'<div class="commit-row"><span class="commit-sha">{sha}</span><span class="commit-msg">{msg}</span></div>'
    if not commit_html:
        commit_html = '<div class="commit-row" style="opacity:.35">No commits in last 48h</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Daanaa Ops</title>
<style>{CSS}</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-left">
    <span class="wordmark">Daanaa</span>
    <span class="topbar-sub">Ops</span>
  </div>
  <div class="topbar-right">
    {now}
    <div style="font-size:.62rem;opacity:.6">auto-refresh every 60s</div>
  </div>
</div>

<div class="wrap">

  <div class="stats">
    <div class="stat"><div class="stat-val">{missions/1000:.0f}K</div><div class="stat-lbl">Missions ({mission_pct:.0f}%)</div></div>
    <div class="stat"><div class="stat-val">{donate:,}</div><div class="stat-lbl">Donate URLs</div></div>
    <div class="stat"><div class="stat-val">{websites/1000:.0f}K</div><div class="stat-lbl">Live Websites</div></div>
    <div class="stat"><div class="stat-val">{open_count}</div><div class="stat-lbl">Open Tasks</div></div>
  </div>

  <p class="sec-label">Pipeline</p>
  <div class="card">
    <div class="card-hd"><span class="card-title">Processes &amp; Progress</span></div>
    <div class="proc-row">{proc_html}</div>
    {prog_html}
  </div>

  <p class="sec-label">Tasks — {open_count} open · {done_count} done (click ○ to toggle · + note to annotate)</p>
  <div class="task-grid">{sections_html}</div>

  <p class="sec-label">Gates &amp; Commits</p>
  <div class="grid-2">
    <div class="card gate-card">
      <div class="card-hd"><span class="card-title">Milestone Gates</span></div>
      {gate_html}
    </div>
    <div class="card commit-card">
      <div class="card-hd"><span class="card-title">Recent Commits (48h)</span></div>
      {commit_html}
    </div>
  </div>

  <p class="sec-label">Ops Assistant</p>
  <div class="card">
    <div class="card-hd">
      <span class="card-title">Chat</span>
      <span style="font-size:.62rem;color:var(--cream-faint)">context-aware · ops-scoped</span>
    </div>
    <div class="model-bar" id="model-bar"></div>
    <div class="chat-area" id="chat-area">
      <div class="chat-bubble chat-assistant">Hi — I have your current pipeline metrics and task list loaded. Ask me anything.</div>
    </div>
    <div class="chat-row">
      <textarea class="chat-input" id="chat-input" rows="2" placeholder="What should I prioritize today? / Why is mission gen slow? / What's blocking Gate 2?"></textarea>
      <button class="chat-btn" id="chat-send">Ask</button>
    </div>
    <div class="chat-actions">
      <button class="chat-action-btn" onclick="saveChat()">Save chat to ops log</button>
    </div>
    <div class="chat-notice">Auto: Claude Sonnet 4.6 if API key set · falls back to Qwen local · add <code>ANTHROPIC_API_KEY=sk-ant-...</code> to <code>meritgiving/.env</code></div>
  </div>

</div>

<script>const API_KEY_SET = {'true' if _api_key() else 'false'};\n{JS}</script>
</body>
</html>"""

# ── HTTP handler ──────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def _request_token(self):
        """Pull a token from the ops_token cookie or X-Ops-Token header."""
        hdr = self.headers.get("X-Ops-Token")
        if hdr:
            return hdr
        raw = self.headers.get("Cookie")
        if raw:
            c = SimpleCookie(raw)
            if "ops_token" in c:
                return c["ops_token"].value
        return None

    def _authed(self):
        return _token_ok(self._request_token())

    def _deny(self):
        body = b"401 Unauthorized - append ?token=YOUR_OPS_TOKEN to the dashboard URL"
        self.send_response(401)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/health":
            self._send_json({"status": "ok"})
            return
        if path in ("/", "/dashboard"):
            # Accept token via ?token= (sets cookie) or existing cookie/header.
            qs_token = parse_qs(parsed.query).get("token", [None])[0]
            set_cookie = None
            if qs_token is not None and _token_ok(qs_token):
                set_cookie = qs_token
            elif not self._authed():
                self._deny()
                return
            body = render_page().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            if set_cookie is not None:
                self.send_header(
                    "Set-Cookie",
                    f"ops_token={set_cookie}; HttpOnly; SameSite=Strict; Path=/; Max-Age=2592000",
                )
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404); self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        if not self._authed():
            self._deny()
            return
        data = self._read_body()

        if path == "/api/task/toggle":
            ok = toggle_task(int(data.get("line", -1)))
            self._send_json({"ok": ok})

        elif path == "/api/task/comment":
            ok = add_comment(int(data.get("line", -1)), data.get("comment", ""))
            self._send_json({"ok": ok})

        elif path == "/api/chat":
            msg   = data.get("message", "").strip()
            model = data.get("model", "auto")
            if not msg:
                self._send_json({"error": "empty message"})
                return
            db_   = db_metrics()
            mp_   = mission_progress()
            sys_  = build_ops_context(db_, mp_)
            reply, model_used = call_llm(sys_, msg, model)
            self._send_json({"reply": reply, "model": model_used,
                             "api_key_set": bool(_api_key())})

        elif path == "/api/chat/save":
            history = data.get("history", [])
            saved = save_chat(history) if history else None
            self._send_json({"path": saved})

        else:
            self.send_response(404); self.end_headers()

if __name__ == "__main__":
    port = int(os.environ.get("OPS_PORT", 5001))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Daanaa Ops Dashboard → http://192.168.1.73:{port}")
    server.serve_forever()
