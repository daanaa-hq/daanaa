# Voice Support Call Tracking & Phase Transition Rules

**Last updated:** 2026-07-12  
**Status:** Phase A (all calls human-routed)  
**Transition rule:** When call volume reaches ≥10/week, evaluate Phase B

---

## What We Track

Every inbound call to +1-747-832-2622 is logged to `support_calls` table:
- `from_phone` — caller's number (anonymized, never stored publicly)
- `call_sid` — Twilio call ID (for debugging)
- `received_at` — timestamp
- `notes` — optional notes after call (founder adds these manually)

**Columns available for future use:**
- `duration` — call length (when added to the schema)
- `transcription` — voicemail text (when Phase B adds STT)
- `resolution_category` — what the call was about (founder tags manually)

---

## Monitoring Script

Run **`scripts/monitor_voice_calls.py`** to see:
- Total calls (last 7 days)
- Unique callers
- Daily trend
- Recent calls + notes

**Quick check:**
```bash
cd ~/meritgiving && python3 scripts/monitor_voice_calls.py
```

**Automated:** Add to crontab to run daily at 8am:
```bash
0 8 * * * cd ~/meritgiving && python3 scripts/monitor_voice_calls.py >> logs/voice_support_tracking.log 2>&1
```

---

## Phase Transition Decision Rule

**Trigger:** When `calls_per_week >= 10` (approximately 1.4 calls/day average)

**At that point, review:**
1. Are the calls repetitive (high Phase B candidacy)?
2. Is founder's time becoming a constraint?
3. Which questions appear most (opportunities for AI filtering)?

**Decision:** Stay Phase A longer vs. Move to Phase B (AI + human hybrid)

---

## Call Patterns to Watch For

As volume builds, track:

- **Time of day:** When do calls cluster? (Reveals time zones served)
- **Question types:** What are the top 3–5 questions? (Targets for AI in Phase B)
- **Caller segments:** Are they all small orgs, or mix of sizes?
- **Resolution quality:** Does founder solve the problem on first call, or do callbacks happen?

Example patterns that suggest Phase B readiness:
- 60%+ of calls are FAQ-type questions ("What's program expense %?", "How do I use the Wallet?")
- Calls cluster in a 2–3 hour window (can auto-route via AI during those hours)
- Same questions from different callers (AI can handle reliably)

---

## Founder's Manual Notes

After each call, optionally add a note to `support_calls.notes`:
```bash
sqlite3 ~/meritgiving/data/merit_registry.db \
  "UPDATE support_calls SET notes='Asked about peer benchmarks' WHERE call_sid='CA...' "
```

Or just track it informally — the monitoring script picks it up.

---

## What Success Looks Like (Phase A)

- **2–3 calls/week:** Healthy signal (orgs discovering us, voices finding the number)
- **5–7 calls/week:** Strong demand (time to document common Q's)
- **10+ calls/week:** Phase B is justified (hybrid model saves founder time)
- **<1 call/week:** Number isn't discoverable yet (may need homepage promotion or wait for word-of-mouth)

---

## Next Review

Check call volume **weekly** (every Friday). At week 4, founder reviews trends and decides:
1. Stay Phase A (calls are manageable, all-human is working)
2. Move to Phase B (time to automate FAQ filtering)
3. Iterate on number promotion (calls aren't there yet)

**Scheduled review:** 2026-08-09 (4 weeks in)
