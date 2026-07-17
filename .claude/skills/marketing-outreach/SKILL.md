---
name: marketing-outreach
version: 1.0.0
description: Draft targeted outreach emails and LinkedIn DMs for Daanaa — funders, nonprofit partners, press, and community orgs. (Daanaa)
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
triggers:
  - draft outreach
  - write an email
  - outreach to
  - write a dm
  - contact a funder
  - reach out to
---

## When to invoke this skill

Use when asked to draft outreach messages for Daanaa. Covers:
- **Funders** — foundation program officers, DAF platforms, civic tech funders
- **Nonprofit partners** — orgs to claim their page, feature in a carousel, or join the Impact Network
- **Press** — journalists covering philanthropy, civic tech, nonprofit sector
- **Community** — LinkedIn connection requests, follow-up messages

Produces copy-paste ready drafts. Never auto-sends anything.

---

## Step 0 — Gather intent

Ask (or infer) three things:
1. **Audience** — who is this going to? (funder / nonprofit / press / community)
2. **Name / org** — specific person or org name if known
3. **Channel** — email or LinkedIn DM?
4. **Goal** — what do we want them to do? (schedule a call / claim their page / write a story / follow the page)

---

## Step 1 — Pull relevant context

```bash
# Check if there are queued outreach targets in memory or docs
ls /home/akbar/meritgiving/docs/outreach/ 2>/dev/null | head -10
cat /home/akbar/meritgiving/docs/outreach/*.md 2>/dev/null | head -100
```

Also check memory for outreach queue:
- `project_outreach_queue.md` — Leslie Chandler meeting, Candid partnership drafts

---

## Step 2 — Draft the message

Use these voice rules (from `feedback_copy_voice.md`):
- Kitchen-table test: would a real person say this out loud?
- No hyphenated jargon ("mission-driven", "impact-focused", "data-driven")
- No dashes for pauses — use real sentence structure
- Specific > general: name what Daanaa actually does, not what it "aims to" do
- Short: email under 150 words, DM under 80 words

### Funder email template pattern:
```
Subject: [Specific hook — one data point or observation]

Hi [Name],

[One sentence on why you're writing to them specifically — show you know their work.]

[One sentence on what Daanaa is — concrete, no jargon.]

[One sentence on what you're asking for — a 20-minute call, a look at the platform, a question.]

[Your name]
daanaa.org
```

### Nonprofit DM pattern:
```
Hi [Name] — I noticed [org] is on Daanaa but the page hasn't been claimed yet.

Claiming takes about 5 minutes and lets you add your mission, programs, and a direct link to your donation page. No cost, ever.

Would you like me to send you the link?
```

### Press pitch pattern:
```
Subject: [Story hook — the counterintuitive angle]

Hi [Name],

[One sentence: what the data shows that surprises people.]

[One sentence: what Daanaa is and where the data comes from.]

[One sentence: why this is a story worth writing.]

Happy to share data exports or connect you with organizations you could feature.

[Your name]
```

---

## Step 3 — Output

Present the draft clearly. Then ask:
- "Want me to adjust the tone, length, or angle?"
- "Should I save this to `docs/outreach/` for your records?"

If they want to save it:
```bash
mkdir -p /home/akbar/meritgiving/docs/outreach
# Write draft to docs/outreach/YYYY-MM-DD-[recipient].md
```

Never send anything. Never open email clients. Copy-paste only.

---

## Prospect search (LinkedIn)

When asked to "find" or "research" prospects on LinkedIn, use `linkedin_search.py`:

```bash
cd /home/akbar/meritgiving && source venv/bin/activate

# Find nonprofit leaders at a specific org
python3 scripts/linkedin/linkedin_search.py --org "Food Bank of NYC" --role "Executive Director"

# Search for funder program officers across known foundations
python3 scripts/linkedin/linkedin_search.py --funders

# Free-form keyword search
python3 scripts/linkedin/linkedin_search.py --keywords "civic tech nonprofit data philanthropy" --limit 10

# Save results for review
python3 scripts/linkedin/linkedin_search.py --funders --save docs/outreach/prospects.json
```

Note: requires `scripts/linkedin/.session/linkedin_creds.json` with `{"username": "...", "password": "..."}`.
Never auto-DM or auto-connect. Output is for manual review and targeted outreach drafts only.

---

## Queued outreach (check these first)

From memory:
- **Leslie Chandler** — meeting scheduled, follow-up email ready to send
- **Candid** — data partnership draft ready to send
- **DRK Foundation, Trust for Civic Life, Knight** — funder targets from G0 sprint
