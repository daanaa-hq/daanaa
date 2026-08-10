# 💎 GitHub Template: Making Daanaa Governance Forkable

**Objective:** Any team can fork this governance framework in 5 minutes and have working governance.

---

## What Goes in the Template

### 1. **Core Files (Forked as-is)**
```
template/
├── STEWARDSHIP.md (template version with XXX placeholders)
├── governance/
│   ├── DECISIONS.md (starter template)
│   ├── LESSONS.md (starter template)
│   ├── GOVERNANCE_OPERATIONAL.md (yours to customize)
│   └── FRAMEWORK_SCHEMA.json (machine-readable governance)
├── institution/
│   ├── AUTONOMY_FRAMEWORK.md (yours to customize)
│   └── PRIVACY_GATES.md (yours to customize)
├── scripts/
│   └── privacy_check.sh (ready to use as git hook)
├── .github/
│   └── pull_request_template.md (governance-aware PR template)
└── README.md (quickstart guide for forks)
```

### 2. **Customization Prompts (For Teams)**
Files include `[YOUR_ORG]`, `[YOUR_MISSION]`, `[YOUR_PRINCIPLES]` placeholders:
- Team fills in their name/mission
- Adapts 5-11 principles to their context
- Adds their team members to STEWARDSHIP.md
- Commits in 5 minutes

### 3. **What's NOT Included**
- Daanaa's specific principles (they customize theirs)
- Our DECISIONS.md history (they start fresh)
- Our specific gates (they define theirs)
- Any Daanaa branding (teams own their framework)

---

## How It Works

### Step 1: Team Forks Template
```bash
# On GitHub, click "Use this template"
# Creates team's own repo: acme-ngo/governance-framework
```

### Step 2: Customize in 30 Minutes
```bash
# Edit STEWARDSHIP.md
# - Replace [YOUR_ORG] with "ACME NGO"
# - Replace [YOUR_MISSION] with their mission
# - Adapt principles to their context

# Edit governance/GOVERNANCE_OPERATIONAL.md
# - Fill in team roles

# Commit
git add -A
git commit -m "chore: customize governance for ACME NGO"
```

### Step 3: Install Gates
```bash
cp scripts/privacy_check.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Test it
git commit --allow-empty -m "test: governance gates"
# ✅ Passed
```

### Step 4: Start Using
```bash
# Every commit triggers privacy gate
# DECISIONS.md reminds them when to log decisions
# PR template reminds them to check principles
```

**Total time: 5-30 minutes depending on customization depth.**

---

## Template File: STEWARDSHIP.md (Example)

```markdown
# [YOUR_ORG]'s Stewardship Commitment

**Mission:** [YOUR_MISSION]

We build [what you do] to help [who you help] [do what they need].

## Our Binding Principles

1. **[Principle 1 Name]** — [One sentence on why this matters for us]
   - How we implement it: [Specific rule or gate]

2. **[Principle 2 Name]** — [One sentence on why this matters for us]
   - How we implement it: [Specific rule or gate]

[... up to 15 principles]

## Who Signed
- [Founder name] — Founder
- [Team member] — Engineer
- [Team member] — Team
- [Community partner] — Community

## How We Govern
See GOVERNANCE_OPERATIONAL.md for who decides what.
See governance/DECISIONS.md for why we chose what we chose.

---

**This framework was adapted from [Daanaa Governance Framework](https://daanaa.org/governance).**

We use the same 11 principles globally to help teams build trustworthy civic tech.
```

---

## Fork Registry (Public List of Teams)

All teams that fork register here (optional but encouraged):

```json
{
  "forks": [
    {
      "organization": "ACME NGO",
      "country": "Brazil",
      "sector": "nonprofit",
      "fork_url": "https://github.com/acme-ngo/governance-framework",
      "stewardship_url": "https://github.com/acme-ngo/governance-framework/blob/main/STEWARDSHIP.md",
      "founded": "2026-08-15",
      "team_size": 8,
      "principles": 9,
      "story": "We adapted Daanaa's framework to guide our LGBTQ+ advocacy work in Brazil."
    },
    ...
  ]
}
```

**Public registry at:** `governance/FORK_REGISTRY.json`

Teams submit PRs to add themselves. We celebrate them publicly.

---

## Localization Strategy

### Tier 1 (This Month)
- [ ] Spanish (300M speakers, Latin America NGO reach)
- [ ] Portuguese (200M speakers, Brazil/Africa reach)
- [ ] French (260M speakers, Africa/EU reach)

### Tier 2 (Next Quarter)
- [ ] Arabic (400M speakers, MENA NGO reach)
- [ ] Swahili (150M speakers, East Africa reach)

### Each Translation Includes
- STEWARDSHIP.md (principles + examples)
- QUICKSTART_24HOUR.md (4-hour setup)
- One complete example GOVERNANCE_OPERATIONAL.md
- One completed team story (real case study)

---

## Adoption Badge

Teams that fork get a badge for their README:

```markdown
[![Daanaa Governance Framework](https://img.shields.io/badge/governance-daanaa-green)](https://daanaa.org/governance)
```

**Why?** 
- Credits Daanaa without dependency
- Shows team is publicly committed to governance
- Enables fork registry discovery (teams link their repos)

---

## Success Metrics (Per Template)

**This Month:**
- [ ] 1 GitHub template published
- [ ] 3 languages available
- [ ] 5 forks (real teams using it)
- [ ] Fork registry live

**By End of Q4:**
- [ ] 50+ forks
- [ ] 200+ stars
- [ ] 5+ contributed improvements (PRs back to template)
- [ ] 2 academic papers citing framework

**By End of Next Year:**
- [ ] 200+ forks
- [ ] Taught in nonprofit management courses
- [ ] Framework used on 3+ continents
- [ ] Community maintaining improvements

---

## Next Steps

1. **Create the template repository** (today)
2. **Write 3 complete localized examples** (this week)
3. **Launch fork registry** (week 2)
4. **Start academic paper** (weeks 2-3)
5. **Recruit first 5 pilot teams** (week 2)
