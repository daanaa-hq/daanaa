---
name: marketing-carousel
version: 1.0.0
description: Generate and post a branded LinkedIn carousel for Daanaa. Runs the full pipeline — LLM content → PDF render → Playwright post. (Daanaa)
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
triggers:
  - post a carousel
  - linkedin carousel
  - generate carousel
  - make a carousel
---

## When to invoke this skill

Use when asked to create, generate, or post a LinkedIn carousel for Daanaa.
Handles the full pipeline: content generation via local LLM → branded PDF render → Playwright post to the Daanaa company page.

Carousel types available: `hidden_gems` | `sector_insight` | `how_it_works` | `feature_launch` | `myth_bust`

---

## Step 0 — Gather intent

Ask the user (or infer from context):
1. **Type** — which carousel type? (default: `hidden_gems`)
2. **Extra context** — any specific angle, org, sector, or data point to focus on? (optional)
3. **Post now or dry run?** — generate only, or post to LinkedIn immediately?

If all three are clear from the user's message, skip asking and proceed.

---

## Step 1 — Check prerequisites

```bash
# Confirm pipeline scripts exist
ls /home/akbar/meritgiving/scripts/linkedin/post_carousel.py
ls /home/akbar/meritgiving/scripts/linkedin/.session/state.json 2>/dev/null || echo "NO_SESSION"
```

If `NO_SESSION` is printed:
- Tell the user: "No LinkedIn session found. Run the one-time setup first:"
  ```
  ! /home/akbar/merit-pdf-env/bin/python3 scripts/linkedin/linkedin_poster.py --setup
  ```
- Stop and wait for them to complete setup before continuing.

---

## Step 2 — Generate and post

```bash
cd /home/akbar/meritgiving && source venv/bin/activate
python3 scripts/linkedin/post_carousel.py \
  --type {TYPE} \
  {--context "{CONTEXT}" if context provided} \
  {--dry-run if dry run}
```

Replace `{TYPE}` with the carousel type. Add `--context` only if the user provided specific focus. Add `--dry-run` if they want to review before posting.

---

## Step 3 — Report

Tell the user:
- Where the PDF was saved (`scripts/linkedin/output/`)
- Whether it was posted or is pending manual upload
- Suggested caption (pulled from `post_carousel.py` CAPTIONS dict for the type used)

If it was a dry run, remind them: `python3 scripts/linkedin/post_carousel.py --type {TYPE} --use-existing` to post the generated PDF without regenerating.

---

## Carousel type guide

| Type | Best for | Cadence |
|---|---|---|
| `hidden_gems` | Awareness, follower growth | Weekly |
| `sector_insight` | Credibility, data storytelling | Bi-weekly |
| `how_it_works` | New followers, platform explanation | Monthly |
| `myth_bust` | Engagement, shareability | Monthly |
| `feature_launch` | Product announcements | As needed |
