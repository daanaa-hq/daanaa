# Retention Features — Quick Summary

## The Core Loop (What We Build)

```
DISCOVERY          WALLET             TRUST              REDISCOVERY        GIVING
┌──────────────┐  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Donor finds  │→ │ Bookmarks in │→  │ Sees peer    │→  │ Returns to   │→  │ One-click    │
│ org on       │  │ Wallet       │   │ financial    │   │ Daanaa,      │   │ "Give Now"   │
│ Daanaa       │  │ (device-     │   │ health       │   │ sees Wallet  │   │ button       │
│              │  │  local)      │   │ signals      │   │              │   │              │
└──────────────┘  └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
                                                                                  ↓
                                                                         ┌──────────────┐
                                                                         │ Donates via  │
                                                                         │ Every.org    │
                                                                         │ (verified    │
                                                                         │  link)       │
                                                                         └──────────────┘
                                                                                  ↓
                                                                         ┌──────────────┐
                                                                         │ Gets receipt │
                                                                         │ (trust +     │
                                                                         │  reciprocity)│
                                                                         └──────────────┘
                                                                                  ↓
                                                                         REPEAT CYCLE
```

---

## Features We Build (By Phase)

### G2 (Weeks 6–12): Core Giving Paths

| Feature | What | Why | Retention Boost |
|---------|------|-----|-----------------|
| **One-Click Giving** | "Give Now" button on Wallet cards | Eliminates decision fatigue | 2–3x repeat rate |
| **Org-Provided Links** | Org provides donate link when claiming | Org controls link (legal clean) | Incentivizes claiming |
| **Claim Flow** | Easy email verify → add link → claim | More claimed orgs = more buttons | 15–20% more claims |
| **Low-Friction Donate** | Link goes directly to org's processor | Org chooses (Every.org/Donorbox/etc.) | Extra 10% completion |

**Retention psychology:** Low friction + trust signals (claimed = verified) = repeat giving

---

### G3 (Months 3–6): Growth Features

| Feature | What | Why | Retention Boost |
|---------|------|-----|-----------------|
| **Wallet Enhancements** | Sort, analytics, optional reminder | Easier navigation + gentle nudge | +20–30% |
| **Peer Recommendations** | "Similar orgs in [cause]" | Expands portfolio | +15–20% giving |
| **Nonprofit Claiming** | Org claims profile | Builds trust (org verified) | +2x inquiry |

**Retention psychology:** Habit formation + expanded portfolio + org legitimacy

---

## What We Don't Build

| Feature | Why NOT |
|---------|---------|
| Email reminders | Causes reactance (backfires) |
| Gamification | Creates guilt (reduces giving) |
| Social proof | Creates comparison anxiety |
| Org update requirements | Burdens nonprofits |
| Public giving visibility | Violates privacy, creates pressure |

---

## Retention Impact by Feature

```
Feature                          Retention Boost     Complexity    Stewardship Risk
───────────────────────────────  ──────────────────  ────────────  ─────────────────
One-click giving                 2–3x                Low           None
Verified donate links            1.5x                Low           None
Trust signals (peer group)       1.3x                Low           None
Every.org integration            1.2x                Medium        None
Wallet enhancements              1.2x                Low           None
Peer recommendations             1.2x                Medium        Low
Opt-in reminders                 1.2x                Low           Low
Email campaigns                  1.1x                Low           HIGH ✗
Gamification                     0.8x (backfire)     Low           HIGH ✗
Social proof displays            0.9x (backfire)     Low           HIGH ✗
```

---

## The Three Critical G2 Features (First)

### 1. **One-Click Giving from Wallet**
- **Solves:** Decision fatigue, cognitive load
- **How:** "Give Now" button on Wallet cards → links to org's provided donate URL
- **Effort:** ~2 weeks (UI component + link integration)
- **Impact:** Enables repeat giving (no re-search needed) for CLAIMED orgs
- **Legal:** Org provides link (org responsible, not us)

### 2. **Org-Provided Donation Links**
- **Solves:** Trust + discovery friction + legal compliance
- **How:** When org claims profile, they provide their donate link. Daanaa displays it.
- **Effort:** Fold into claiming flow (org provides link during claim process)
- **Impact:** Removes barrier + incentivizes claiming (only claimed orgs get button)
- **Legal:** Org controls link (not us discovering/verifying)

### 3. **Org Claiming Flow (Improved)**
- **Solves:** Incentivizes orgs to claim + provide link
- **How:** Make claiming super easy: email verify → add link → done
- **Effort:** ~1 week (streamline claiming form)
- **Impact:** More claimed orgs = more "Give Now" buttons
- **Legal:** Org is responsible for their link + data

**Together:** These three features unlock 2–3x repeat giving **without** dark patterns, nonprofit burden, **or legal risk**.

---

## Product Roadmap (Visual)

```
NOW (Live)          → G2 (Weeks 6–12)     → G3 (Months 3–6)      → G4+ (Later)
───────────────────────────────────────────────────────────────────────────────
Discovery           One-click giving      Wallet analytics       Giving portfolio
Bookmarks           Verified links        Peer recommendations   Advanced analytics
Org profiles        Every.org integration Opt-in reminders       Processor partner
Financial health    Simple give flow      Nonprofit claiming     Deeper integration

RETENTION IMPACT:
Baseline            2–3x repeat           4–5x repeat            5–6x repeat
(one-time givers)   (low friction)        (habit + discovery)    (seamless)
```

---

## Why This Works (Behavioral Summary)

| Psychological Barrier | Feature That Solves It | How It Works |
|----------------------|------------------------|--------------|
| Cognitive load (forgot org) | Wallet bookmarks | Org stays visible |
| Decision fatigue | One-click giving | Pre-decided, just execute |
| Loss aversion (is org legit?) | Financial health signals | Shows peer standing + stability |
| Searching is hard | One-click from Wallet | No re-search needed |
| Trust is uncertain | Verified donate links | Tested, working link |
| No reciprocity signal | Every.org receipt | Professional acknowledgment |
| Isolated (alone in choice) | Peer recommendations | See similar orgs (context) |
| Habit formation (one-time) | Repeated easy access | Wallet = habit cue |

**Result:** Donors repeat naturally (no pressure, no tracking, no guilt)

---

## Success Looks Like

**Donor experience:**
- Discovers org on Daanaa (1st gift)
- Bookmarks it (Wallet)
- Sees it's financially healthy (trust builds)
- Months later: Returns, sees Wallet, clicks "Give Now"
- Donates in 30 seconds (one-click, verified link)
- Gets professional receipt (feels good)
- Explores related orgs (expands giving)
- Repeats (habit)

**Nonprofit experience:**
- Gets discovered (visibility)
- Gets repeat donors (from Daanaa)
- Gets verified bookmarks (signals legitimate)
- No burden (they don't post to Daanaa, don't report to us)

**Daanaa's impact:**
- Donor retention: 45%+ repeat rate (vs. 20% baseline)
- Nonprofit repeat donors: +2–3x
- Average gift portfolio: 3–4 orgs (vs. 1)
- Zero dark patterns

---

## The Philosophy

**Every feature asks: "Does this make giving easier or create pressure?"**

- Make it easier? ✅ Build it.
- Creates pressure? ❌ Don't build it.

**That's retention done right.**
