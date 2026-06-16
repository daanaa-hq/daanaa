# Donation Links — Legal Model (CA Compliance)

**Critical distinction:** Daanaa does NOT discover or provide donation links. Nonprofits provide their own when they claim their page.

---

## The Model

### ❌ What We DON'T Do

- Crawl nonprofit websites to find donate links
- Verify or test donation links
- Route donations through Daanaa
- Store donation link data (except what org provides)
- Provide donation links for unclaimed orgs
- Act as a "charitable solicitor" under CA law

### ✅ What We DO

- Display donation links that **nonprofits provide** when they claim their profile
- Org provides link when claiming: "Our donation URL is [...]"
- Daanaa displays link as org stated it
- Org is responsible for the link
- Daanaa is a directory (showing what orgs have told us)

---

## Why This Matters (Legal)

**California charitable solicitation law:**
- If Daanaa **discovers + promotes** donate links, we become a "charitable solicitor"
- Solicitors must register in each state they solicit (CA, NY, etc.)
- Registration is expensive + complex
- Multi-state liability is huge

**Our workaround (clean):**
- Org provides their link (org is the source)
- Daanaa displays what org provided (we're a directory)
- Org is responsible for accuracy + compliance
- We're not a solicitor (we're a discovery platform)

---

## Implementation

### Claiming Flow

```
1. Org claims profile (email verification)
2. Form asks: "What's your donation link?" 
   [Text input: https://...]
3. Org provides: URL (to Every.org, Donorbox, own site, etc.)
4. Daanaa stores + displays it
5. Form confirms: "Your 'Give Now' button will link to [URL]"
6. Org completes claim
7. "Give Now" button appears on Daanaa with org's link
```

### What's Displayed

- **Claimed orgs:** "Give Now" button (links to org's provided URL)
- **Unclaimed orgs:** No donate button (prompt to claim instead)

### Data Stored

- Org EIN + provided donation URL (that's it)
- Not a full "donation link verification pipeline"
- Just: "Org said their link is this, we're showing what they said"

---

## Legal Safeguards

### In Terms of Service (When Ready)

- "Daanaa displays donation links provided by organizations. Organizations are responsible for the accuracy + legality of their links."
- "Daanaa does not verify, test, or endorse donation links."
- "If a link is incorrect or fraudulent, report it to [email]. We will contact the organization."

### On Org Claiming Page

- "Your donation link will be displayed publicly. Make sure it's correct."
- "You are responsible for this link + any compliance requirements."

### On Org Detail Page (Near Button)

- "This link was provided by [Organization Name]. Donations are processed by [their payment processor], not Daanaa."

---

## What This Means for Retention Strategy

**Good news:** The retention loop still works.

**One-click giving + wallet + claimed orgs still unlock 2–3x repeat rate.**

**The difference:**
- Orgs must claim to get a "Give Now" button
- This incentivizes claiming (powerful hook)
- Claimed = verified (trust signal)
- Claiming flow is a key G2 feature

**Result:** Claiming rate becomes a KPI.

---

## FAQ

**Q: What if an org's link breaks or changes?**
A: Org is responsible for updating it when they claim. Daanaa displays what they provide. If it breaks, donors report it → we notify org → org fixes or re-claims.

**Q: What if an org provides a scam link?**
A: Org is liable, not us. We have a report mechanism. If we get flagged, we immediately contact org + ask them to provide a correct link or we remove the button.

**Q: What about multi-state solicitation laws?**
A: Org is the solicitor (they provided the link). Daanaa is a directory (displaying public information). We're not actively soliciting donations; we're organizing information. Legal guidance recommended pre-launch, but this model is much cleaner than a "donation link discovery pipeline."

**Q: Can orgs change their link later?**
A: Only when they re-claim or update their profile. There's no "donation link API" that auto-updates.

**Q: What if we integrate Every.org?**
A: Every.org could be an **option** orgs choose (e.g., "Donate via Every.org" button). But we don't require it. Org chooses their processor.

---

## Bottom Line

**We're a directory of nonprofit information, not a donation processor or solicitor.**

Orgs provide information (including donation links). We display it. Orgs are responsible.

This keeps Daanaa clean, legally compliant, and focused on what we do: discovery + transparency.
