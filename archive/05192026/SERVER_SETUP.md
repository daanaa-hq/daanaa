# Server Folder Setup — Home Server `ecomargins`

**Where to put everything after you download `merit-build.zip` to your home server.**

Hostname: `ecomargins`
OS: Ubuntu
User: `akbar`
Existing structure: `/home/akbar/Meritgiving/venv/`

---

## Final layout after Day 1

```
/home/akbar/
├── Meritgiving/                        # YOUR EXISTING ROOT — keep
│   ├── venv/                           # existing Python env — keep
│   ├── inbox/                          # NEW — monthly IRS BMF downloads
│   │   └── (empty for now; first use 2026-06)
│   ├── data/                           # NEW — persistent data
│   │   ├── duckdb/
│   │   │   └── merit.duckdb            # (created by first ingest)
│   │   ├── badges/                     # (created by first scoring run)
│   │   └── archives/                   # (created by first archive)
│   ├── scripts/                        # NEW — ingest/scoring scripts
│   │   └── (populated by Claude later)
│   ├── backups/                        # NEW — local mirror of cloud backups
│   └── logs/                           # NEW — agent logs, cron logs
│
└── merit-build/                        # NEW — unzipped from merit-build.zip
    ├── README.md                       # start here
    ├── DAY_1_ACTION_PLAN.md            # do today
    ├── meritgiving-ops/                # → push to github.com/meritgiving/meritgiving-ops
    │   ├── benchmarks/
    │   ├── board/
    │   ├── company/
    │   ├── decision-log/
    │   ├── departments/
    │   ├── okrs/
    │   ├── runbooks/
    │   ├── state/
    │   └── strategy/
    └── merit-platform/                 # → push to github.com/meritgiving/merit-platform
        ├── .claude/
        │   ├── agents/
        │   ├── commands/
        │   ├── rules/
        │   └── skills/
        ├── .mcp.json
        ├── CLAUDE.md
        └── apps/web/app/(dashboard)/
```

## Step-by-step setup (15 min)

### 1. Create the new directories under existing Meritgiving/

```bash
cd /home/akbar/Meritgiving
mkdir -p inbox data/duckdb data/badges data/archives scripts backups logs
ls -la
```

You should see venv/ (existing) + the 6 new directories.

### 2. Unzip merit-build.zip in home directory

```bash
cd /home/akbar
# Assuming you scp'd or downloaded merit-build.zip to /home/akbar
unzip merit-build.zip
# Should create /home/akbar/merit-build/
ls merit-build/
```

You should see: README.md, DAY_1_ACTION_PLAN.md, meritgiving-ops/, merit-platform/

### 3. Read the entry points

```bash
cat /home/akbar/merit-build/README.md
cat /home/akbar/merit-build/DAY_1_ACTION_PLAN.md
```

### 4. Initialize the two GitHub repos

```bash
cd /home/akbar/merit-build/meritgiving-ops
git init
git add .
git commit -m "chore: initial commit — org scaffolding"
git branch -M main
git remote add origin git@github.com:meritgiving/meritgiving-ops.git
# Don't push yet; do this AFTER you create the GitHub org

cd /home/akbar/merit-build/merit-platform
git init
git add .
git commit -m "chore: initial commit — platform scaffolding"
git branch -M main
git remote add origin git@github.com:meritgiving/merit-platform.git
# Don't push yet either
```

After Day 1 morning session (when GitHub org `meritgiving` is created):
```bash
cd /home/akbar/merit-build/meritgiving-ops && git push -u origin main
cd /home/akbar/merit-build/merit-platform && git push -u origin main
```

### 5. Set up Claude Code on the server

If running Claude Code on the server itself:
```bash
cd /home/akbar/merit-build/merit-platform
# Claude Code reads .mcp.json and CLAUDE.md from here automatically
# Add environment variables via .envrc (direnv) or systemd unit
```

If running Claude Code on your laptop and the repo lives on the server:
- Either clone the repo to your laptop
- Or use VS Code Remote-SSH / Cursor Remote to edit on the server

### 6. Set up environment variables

Create `/home/akbar/merit-build/merit-platform/.env.local` (gitignored):
```bash
# Filled in after Day 1 account creation
ANTHROPIC_API_KEY=
GITHUB_TOKEN=
NEON_DATABASE_URL=
AIRTABLE_API_KEY=
STRIPE_SECRET_KEY=
RESEND_API_KEY=
POSTHOG_API_KEY=
CLOUDFLARE_API_TOKEN=
SENTRY_TOKEN=
NOTION_API_KEY=
```

Add to `.gitignore` (already there in proper repo init).

Mirror these into 1Password Business vault "MERIT Production Secrets" immediately.

### 7. Initial IRS BMF data placement (when ready)

When you do your first BMF refresh after launch:

```bash
mkdir /home/akbar/Meritgiving/inbox/2026-06
# Download IRS BMF files into this folder
# Then run ingest (Claude will write the script)
```

For the **immediate** May 2026 data (which you may already have):
```bash
mkdir /home/akbar/Meritgiving/inbox/2026-05
# Move your existing BMF download into here if you have it
```

## Permissions

Make sure scripts directory and logs are owned by you:
```bash
chown -R akbar:akbar /home/akbar/Meritgiving
chmod 755 /home/akbar/Meritgiving/scripts/*.sh  # when scripts exist
```

## Cron setup (later, after scripts exist)

When Claude generates the scoring scripts, you'll add a cron entry for verification:
```bash
crontab -e
# Add (don't add yet, just planning):
# 0 9 * * 2 /home/akbar/Meritgiving/scripts/check_bmf_reminder.sh
# Tuesday 9am: send reminder if 2nd Tuesday and no BMF downloaded yet
```

## What lives on home server vs. cloud

**Home server (this machine, free):**
- IRS BMF historical data
- DuckDB analytics
- Ingest scripts
- Backup mirror (secondary)
- Logs
- Development environment

**Cloud (paid or credit-funded):**
- Production web (Vercel)
- Production DB (Neon Postgres — current state only)
- Production API (Railway or Fly)
- Auth (Clerk)
- Email (Resend)
- Errors (Sentry)
- Analytics (PostHog)
- Backups primary (Cloudflare R2)

This split is intentional. Home server does what's free and local; cloud does what needs uptime.

## Health check

After setup, run this to confirm everything's right:

```bash
# Check existing
ls -la /home/akbar/Meritgiving/venv/ | head -3

# Check new
ls -la /home/akbar/Meritgiving/{inbox,data,scripts,backups,logs}

# Check merit-build
ls -la /home/akbar/merit-build/
ls /home/akbar/merit-build/meritgiving-ops/departments/ | wc -l  # should be 10
ls /home/akbar/merit-build/merit-platform/.claude/agents/workers/ | wc -l  # should be 12

# Check counts
find /home/akbar/merit-build -type f -name "*.md" | wc -l  # should be ~60
find /home/akbar/merit-build -type f | wc -l  # should be ~70
```

If those numbers look right, you're set.

## What if something doesn't unpack right

If merit-build.zip didn't extract properly:
- Re-download from this chat
- Try `unzip -l merit-build.zip` to verify contents
- If still issues, I can regenerate everything

## Next: pick up Day 1 morning session

Once folder layout is set:
1. Open `/home/akbar/merit-build/DAY_1_ACTION_PLAN.md`
2. Begin morning session: GitHub org, Vercel, Cloudflare, etc.
3. End of Day 1: push both repos to GitHub
4. Day 2: start using Claude Code with the new setup
