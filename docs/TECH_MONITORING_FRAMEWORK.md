# Tech Monitoring Framework: Stay Current, Never Drift From Principles

**Goal:** Adapt tools/repos/tech to improve execution. Never let shiny objects distract from mission.

---

## What We Monitor

### **1. Nonprofit Discovery & Index Tools**
Why: Competitive awareness + partnership opportunities

| Tool | Purpose | Watch For | Principle Check |
|------|---------|-----------|---|
| GuideStar/Candid | Nonprofit database | Features, adoption, methodology | P#3: Transparent methodology? |
| Charity Navigator | Nonprofit ratings | Rating methodology changes | P#3: Evidence-based? P#5: Non-judgmental? |
| GiveWell | Research + recommendations | Research approach, funder influence | P#1: Mission first? P#7: Independence? |
| Regional platforms | Federation members | Growth, approach, federation viability | Values alignment? |

**Cadence:** Monthly check-in

---

### **2. AI/ML Tools (Research & Content)**
Why: Speed up article drafting, data analysis, exploration

| Tool | Current Use | Watch For | Principle Check |
|------|---|---|---|
| Qwen2.5-32B (local) | Mission generation, analysis | Model updates, performance | P#10: Local inference? |
| mxbai-embed-large | Embeddings/search | New models, performance | Explainability? |
| GPT/Claude | If we ever use cloud | Cost, privacy, terms | P#2: Privacy? P#3: Transparency? |
| Academic LLMs | Research synthesis | Licensing, outputs | P#3: Citable? |

**Cadence:** Bi-weekly (tech moves fast)

---

### **3. Data & Visualization Tools**
Why: Improve article impact, tracking

| Tool | Current Use | Watch For | Principle Check |
|------|---|---|---|
| Plausible Analytics | Website tracking | Data privacy, user tracking | P#2: No tracking? P#3: Honest metrics? |
| Datasette | Data exploration | Publishing datasets | Open data capability |
| Vega-Lite | Visualizations | Accessibility, interactivity | Accessible to all users? |
| Observable | Interactive articles | Cost, capabilities | Can we make engaging explorable? |

**Cadence:** Monthly

---

### **4. Publishing & CMS**
Why: Article distribution, research visibility

| Platform | Current Use | Watch For | Principle Check |
|---|---|---|---|
| Medium | Article distribution | Algorithm, curation | P#3: Don't bury limitations? |
| Substack | Newsletter platform | Privacy, curation | P#2: Reader privacy? |
| Dev.to | Research/technical | Community, values | Community values alignment? |
| Academic preprint (arXiv, SSRN) | Research visibility | Peer review, citation | Academic credibility |

**Cadence:** Monthly

---

### **5. GitHub Repos (Open Source)**
Why: Improve our own tools, learn from others

**Repos to watch:**
- **Nonprofit data projects:** OpenGov, DataCommons, others doing nonprofit indexing
- **Discovery/search:** Elasticsearch, MeiliSearch improvements (better nonprofit search?)
- **Federation models:** Open source platforms doing federation (learn from)
- **Research infrastructure:** Platforms supporting open research
- **Privacy-first tools:** Tools that respect P#2

**Cadence:** Weekly (star/fork trending repos, read READMEs)

---

## Decision Framework: When To Adopt A New Tool

### **Test #1: Does It Serve Mission?**
- Does it help with public momentum? (articles, visibility, adoption)
- Does it help with gates? (metrics, credibility, funder awareness)
- Does it help with federation? (partner coordination, learning sharing)

If NO → Don't adopt. No matter how cool.

### **Test #2: Does It Respect Principles?**
- Privacy (P#2): Does it track user data? → If yes, only if users consent
- Transparency (P#3): Is it explainable? → If no, be clear about limitations
- Openness (P#7): Is it proprietary lock-in? → Prefer open-source
- AI (P#10): If AI-powered, is it auditable? → Local inference > cloud APIs

If conflicts with principles → Don't adopt.

### **Test #3: Can We Afford It (Time/Money)?**
- Time investment: How much to learn + maintain?
- Financial cost: Is it budget-friendly?
- Opportunity cost: What are we not doing if we invest here?

If too expensive → Don't adopt. Keep it simple.

---

## Example: Tool Evaluation

**Scenario:** New "nonprofit discovery platform" launches with AI-powered matching.

**Step 1: Mission test**
- "Does it help us discover nonprofits better?" → Maybe
- "Does it help us understand why some are invisible?" → Maybe
- "Does it serve our 2027 gates?" → Not directly
- **RESULT: Interesting, not critical**

**Step 2: Principle test**
- "How does it source data?" → Need to check (P#3)
- "Does it respect nonprofit privacy?" → Need to check (P#2)
- "Is the matching algorithm transparent?" → Need to check (P#3)
- **RESULT: Promising, but requires diligence**

**Step 3: Cost test**
- "Time to integrate?" → 40 hours
- "Cost?" → $500/month
- "Opportunity cost?" → Distracts from article writing
- **RESULT: Too expensive for marginal gain**

**FINAL DECISION:** Monitor it. Don't adopt yet. Revisit when we have more runway.

---

## GitHub Stars Framework: What We Track

**Watch (high priority):**
- ⭐ Nonprofit data projects (help index our sector?)
- ⭐ Open search tools (improve nonprofit findability?)
- ⭐ Federation/network tools (how do others structure?)
- ⭐ Privacy-first analytics (alternative to Google Analytics?)
- ⭐ Open science tools (help research infrastructure?)

**Browse (low priority):**
- General ML tools (fun but not mission-critical)
- Startup tools (good to understand what others are building)
- Academic tools (might inspire research approach)

**Ignore (not for us):**
- Growth hacking tools (P#1: mission before growth)
- Dark pattern tools (P#5: don't weaponize transparency)
- Proprietary platforms with lock-in (P#7: independence)

---

## Weekly Tech Scan (15 Minutes)

Every Friday, I:
1. **Check trending nonprofits repos** (GitHub trending page, filter by nonprofit tag)
2. **Scan AI/ML model updates** (especially open models)
3. **Review academic papers** (arXiv new papers on nonprofit discovery, giving behavior)
4. **Monitor federation patterns** (how are networks organized?)
5. **Note opportunities** (things that might help future execution)

**Report:** Quarterly summary of what's worth watching.

---

## Never Let Tools Drive Mission

**This is the core rule:** A tool is never worth adopting if it:
- Distracts from core work
- Compromises principles
- Creates technical debt
- Requires more maintenance than it saves

**Better to do core work with stone age tools than to chase shiny objects.**

The goal is not to use the latest tech. The goal is to build credibility, attract funders, and federate platforms. Tools are means to those ends, not ends themselves.

---

## What We'll Never Do

- Adopt cloud AI APIs if local inference works (P#2, P#3: transparency + privacy)
- Build tracking systems that invade user privacy (P#2)
- Use engagement-hacking techniques (P#5: don't weaponize)
- Integrate with platforms that compromise independence (P#7)
- Present AI outputs as human expertise (P#10)

**Principles > Convenience. Always.**

---

## How I Report

**Quarterly tech review:**
- What repos/tools came to our attention
- Which ones align with principles
- Which ones might help future work
- Recommendations on what to watch
- Nothing to implement unless you approve

You set the bar. I stay on top of the landscape. You decide what we adopt.
