# Daanaa: 40-Minute Podcast Episode Outline

**Episode Title:** "The Invisible 97%: How One Founder Built a Directory for the Nonprofits America Doesn't Know"

**Guest:** Akbar Khowaja, Founder of Daanaa

**Host:** [Your Name]

**Format:** Conversational interview, 40 minutes total

---

## SEGMENT 1: The Founding Story (8 minutes)

### Host Questions
1. "Akbar, you're a procurement and supply chain executive — not a nonprofit veteran, not a tech founder. Walk me through how you ended up building this."
2. "The Ismaili Civic Leadership Program with Rice was a capstone project. Tell us what you were trying to do and what happened when you looked for nonprofits to advise."
3. "You walked into a Microcenter one day. What was that moment like? Were you prepared for what you were about to do?"
4. "You learned Linux for the first time. Built a server with your kids. What was that experience like for you — and for them?"

### Key Talking Points
- Procurement background: grading vendors, using matrices — natural foundation for peer-group financial comparison
- **Ismaili Civic Leadership Program context:** civic engagement, Rice University partnership, finding small nonprofits for the capstone became the founder insight
- **The frustration:** "If a trained data professional with weeks couldn't find small nonprofits, what about a donor with ten minutes?"
- **First principles:** took the same matrix logic he uses in procurement (revenue bands, peer groups, reserve health) and applied it to nonprofits
- **Family involvement:** built the server with kids, weeks of learning Linux / Claude / open tools, family's support critical

### Pull Quote
> "If a trained data professional with weeks to spend couldn't find small nonprofits, a donor with ten minutes certainly couldn't. That was the moment."

---

## SEGMENT 2: The Problem (5 minutes)

### Host Questions
1. "1.8 million nonprofits in America. Fewer than 50,000 are household names. For a donor, what does that invisibility actually mean?"
2. "Charity Navigator, GiveWell, Candid all exist. What can't they do that Daanaa is trying to do?"
3. "You mention privacy as a huge issue. How is giving history different from, say, search history?"

### Key Talking Points
- **The invisible 97%:** most effective work is small, local, specialized, and unsearchable by the general public
- **Existing platforms' limits:** cover only hundreds of orgs (GiveWell); rely on opaque algorithms; center mission judgment when small orgs' real story is financial stability
- **Independence problem:** rating platforms are nonprofits themselves, creating conflicts with their own donors
- **Privacy collapse:** "Your giving history is more personal than your search history. It reveals your values, your communities, your financial capacity. Yet every platform tracks and sells it."

### Pull Quote
> "The nonprofit sector is radically opaque. Fewer than 50,000 are household names. The other 97%? Invisible. And the existing tools can't find them because they're not famous."

---

## SEGMENT 3: How Daanaa Works (8 minutes)

### Host Questions
1. "Walk us through what it feels like to use Daanaa — from search to giving. What's the user experience?"
2. "The peer scoring system is interesting. Explain why you'd never compare a small clinic to a hospital."
3. "You call it a 'hand-off' platform. Money never touches Daanaa. Why was that a founding principle?"
4. "The wallet is on the user's phone, not your servers. Why? Doesn't that limit what you can build?"

### Key Talking Points
- **Search:** keyword (FTS5) + semantic (neural embeddings) — users find orgs by meaning, not just exact name match
- **Peer scoring is everything:** revenue band × NTEE subcategory × region. A $200K food bank in Texas is scored only against other $150K–$250K food banks in the South. Never against the Red Cross.
- **The "invisible 97%" philosophy:** $200K org with 12 months of reserve is in excellent health *for its scale* — that's the meaningful signal, not "67 out of 100"
- **Hand-off design:** all donations route to org's own giving page (Donorbox, Stripe, PayPal, or EIN-based routers). Daanaa never touches money. Protects both the donor and Daanaa from regulation.
- **Private wallet:** localStorage only, no server storage of giving history. "The left hand does not know what the right hand gives."
- **Trade-off:** no cross-device sync, no personalization, no data-mining. That's by design.

### Pull Quote
> "A small nonprofit should never be compared to a large one as if they were playing the same game. Every score is computed within a peer group. A $200K community arts nonprofit is ranked only against other similar orgs in its region, not against the Metropolitan Museum of Art."

---

## SEGMENT 4: The Stewardship Commitment (5 minutes)

### Host Questions
1. "You started a for-profit LLC to run a civic-good platform. That's a choice. Walk us through why."
2. "You've locked Daanaa under 11 binding principles from day one. Which one matters most to you?"
3. "Principle 11 says principles can change, but only if you re-sign them. That's meta. Why that rule?"

### Key Talking Points
- **For-profit structure:** "A nonprofit cannot independently rate another nonprofit without creating conflicts with its own donors. A for-profit LLC with binding principles avoids that."
- **The 11 principles:** Mission before growth. Privacy core. Evidence-based trust signals. Fairness to small orgs. No weaponized transparency. Quick corrections. Independence. No donor-fund control. Explainable decisions. AI as a tool. Principles strengthened, not weakened.
- **Most important:** Principle 8 (Daanaa never touches money) and Principle 2 (privacy by default). "These two protect both the integrity of the model and the trust of the donor."
- **Principle 11:** "The sector is full of organizations that started with integrity and drifted. I never want Daanaa to drift silently. If we ever need to change a principle, we pause, document it, and re-sign. It's a guardrail against slow corruption."

### Pull Quote
> "These aren't marketing principles. They're binding. Every one. Because the moment you treat them as optional, you've already lost the thing that made Daanaa worth building."

---

## SEGMENT 5: What's Next (5 minutes)

### Host Questions
1. "We're in beta as of June 4. What does the next phase look like?"
2. "Scores are off right now. When do they come on, and why?"
3. "You mention volunteering as Phase 3. How does that fit into the bigger vision?"
4. "What's your long-term play here? Ten years from now, what does Daanaa look like?"

### Key Talking Points
- **Beta (Phase 1, now):** search, directory, private wallet, verified donate links. Scores off (feature flag `ENABLE_SCORES=false`). Testing the core flow.
- **Phase 2 (scores on):** requires a bias audit to ensure small orgs don't systematically score lower within their peer group. Public methodology page. Corrections path live. Appeal process for orgs.
- **Phase 3 (volunteering):** deliberate second vertical for civic action. "Giving time" as seriously as "giving money." Same privacy, same principles, same hand-off model.
- **Phase 4 (native apps):** only if PWA limitations bite. Capacitor-wrap the same web codebase — no second app to maintain.
- **Long-term:** "A directory so comprehensive and trustworthy that a donor with ten minutes can find an organization they've never heard of, understand its financial stability in context, and give with confidence. And their giving history stays theirs alone."

### Pull Quote
> "The long-term vision is simple: make giving so easy and private that 'the left hand does not know what the right hand gives.' An old principle from Islamic tradition. That's the north star."

---

## SEGMENT 6: Close (4 minutes)

### Host Questions
1. "If someone's listening and thinking, 'I'd like to try this,' what should they do?"
2. "For a nonprofit listening — how do they claim their profile and get verified?"
3. "What would you want people to know about Daanaa that they might not guess?"

### Key Talking Points
- **For donors:** Visit daanaa.org. Search for a cause, a place, an org type. Read the methodology page. Save orgs to your private wallet. Give directly.
- **For nonprofits:** When you see your profile on Daanaa, claim it. Verify your mission, upload your logo, confirm your donate URL. Understand your score relative to peers (not a judgment — a mirror).
- **What might surprise people:** "Daanaa doesn't judge nonprofits. It surfaces them. I'm not here to tell you which organization does the most good — that's your choice. I'm here to make sure you *can* choose the org that feels right to you, even if it's not famous."

### Pull Quote
> "Find the nonprofit you've never heard of. Give with confidence. Keep your giving private. That's Daanaa."

---

## EPISODE FLOW & TIMING

- **Intro (2 min):** Host introduces Akbar, the founding insight, and the Ismaili program.
- **Segment 1 (8 min):** Founding story deep dive.
- **Segment 2 (5 min):** The problem and why existing tools fall short.
- **Segment 3 (8 min):** How the platform works, peer scoring, hand-off model.
- **Segment 4 (5 min):** Stewardship principles and the for-profit + principles model.
- **Segment 5 (5 min):** Roadmap (beta, Phase 2, 3, 4) and long-term vision.
- **Segment 6 (4 min):** How to get involved. Close with the founding quote.
- **Outro (2 min):** Host thanks, link to daanaa.org, subscription reminder.

---

## PRODUCTION NOTES

**Tone:** Conversational, patient. This isn't a pitch — it's a founder sharing why he built something. Let pauses breathe.

**Frequency:** Single long-form episode, not a series. Can be edited into shorter clips for social media.

**Guests to mention (optional call-outs):**
- Akbar's co-researchers at Rice / Ismaili program (if he wants to credit them)
- The AI/Anthropic partnership (since Claude is integral to the build)

**Post-episode assets:**
- Transcript (for blog)
- 3–4 short video clips (for TikTok, LinkedIn, YouTube Shorts)
- Pull quotes graphic (for Instagram, Twitter)
