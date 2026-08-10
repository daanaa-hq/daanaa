# Daanaa Governance Hub

**The principles, decisions, and infrastructure that make Daanaa trustworthy.**

---

## 🎯 Quick Navigation

### **For your team (start here)**
- **[QUICKSTART_24HOUR.md](../docs/QUICKSTART_24HOUR.md)** — 4 hours to working governance (copy-paste templates)
- **[DECISIONS.md](DECISIONS.md)** — Why we chose what we chose (read recent entries)
- **[LESSONS.md](LESSONS.md)** — What broke and how we fixed it

### **For teams building civic tech globally**
- **[EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)** — Should we build AI-native governance? (decision doc)
- **[IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md)** — 4-week build plan (16 hours)
- **[FRAMEWORK_SCHEMA.json](FRAMEWORK_SCHEMA.json)** — Machine-readable schema for your governance setup

### **Architecture & Design**
- **[docs/AI_NATIVE_GOVERNANCE_ARCHITECTURE.md](../docs/AI_NATIVE_GOVERNANCE_ARCHITECTURE.md)** — Complete specification
- **[docs/ARCHITECTURE_DIAGRAM.md](../docs/ARCHITECTURE_DIAGRAM.md)** — Visual flows and layers
- **[docs/AI_GOVERNANCE_FRAMEWORK.md](../docs/AI_GOVERNANCE_FRAMEWORK.md)** — Full framework guide (with regional examples)

### **Operational Files**
- **[GOVERNANCE_OPERATIONAL.md](GOVERNANCE_OPERATIONAL.md)** — How decisions are made
- **[OPEN-DECISIONS.md](OPEN-DECISIONS.md)** — Outstanding questions (waiting on founder input)
- **[audits/](audits/)** — Compliance, UX, quality audits

---

## 📖 By Role

### **Founder / Leadership**
1. Read [STEWARDSHIP.md](../STEWARDSHIP.md) — 11 binding principles (non-negotiable)
2. Read [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) — AI-native governance approval (4-week plan)
3. Check [DECISIONS.md](DECISIONS.md) — Recent decisions requiring your awareness
4. Quarterly: [OPEN-DECISIONS.md](OPEN-DECISIONS.md) — Strategic questions pending

### **Engineer / Technical Lead**
1. Read [QUICKSTART_24HOUR.md](../docs/QUICKSTART_24HOUR.md) — 4-hour setup
2. Read [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) — Week-by-week build (you're here)
3. Implement [FRAMEWORK_SCHEMA.json](FRAMEWORK_SCHEMA.json) — Machine-readable governance
4. Log [DECISIONS.md](DECISIONS.md) — Why you chose what you chose
5. Update [LESSONS.md](LESSONS.md) — When something breaks

### **AI Agent (Claude, Codex, etc.)**
1. Read [STEWARDSHIP.md](../STEWARDSHIP.md) first — Non-negotiable principles
2. Read [GOVERNANCE_OPERATIONAL.md](GOVERNANCE_OPERATIONAL.md) — Authority matrix
3. Check [institution/AUTONOMY_FRAMEWORK.md](../institution/AUTONOMY_FRAMEWORK.md) — When you can decide alone
4. Log [DECISIONS.md](DECISIONS.md) — Why you recommended what you recommended

### **Team Member (New)**
1. Read [STEWARDSHIP.md](../STEWARDSHIP.md) — Our 11 principles (10 min)
2. Skim [DECISIONS.md](DECISIONS.md) — Recent choices (5 min)
3. Do one code review together with tech lead (see gates in action)
4. Make your first commit (experience DECISIONS.md requirement)
5. Done—you're in the culture

### **Auditor / Community Member**
1. Read [STEWARDSHIP.md](../STEWARDSHIP.md) — What we promise
2. Check [DECISIONS.md](DECISIONS.md) — Do decisions honor principles?
3. Run `privacy_check.sh` — Do automated gates work?
4. Test the live site — Does it actually do what we say?
5. Report issues via [OPEN-DECISIONS.md](OPEN-DECISIONS.md)

---

## 🏗️ Current Status

### **In Production**
- ✅ 11 binding principles (STEWARDSHIP.md)
- ✅ Decision log (DECISIONS.md)
- ✅ Lessons learned (LESSONS.md)
- ✅ Autonomy framework (institution/AUTONOMY_FRAMEWORK.md)
- ✅ 1 automated privacy gate (scripts/privacy_check.sh)
- ✅ 24-hour quick-start (docs/QUICKSTART_24HOUR.md)

### **In Phase 1 (Week 1-4)**
- 🟢 FRAMEWORK.json (machine-readable schema) — Started
- 🟢 Governance quickstart templates — Started
- 🟢 SEO + discoverability — Queued for Week 2
- 🟢 Public registry — Queued for Week 3
- 🟢 Validation + launch — Queued for Week 4

### **Planning**
- 📋 Add 2-3 more automated gates
- 📋 Expand to regional compliance (GDPR, LGPD, etc.)
- 📋 Build governance as a service (other teams)

---

## 📚 Key Documents

| File | Purpose | Audience | Time |
|------|---------|----------|------|
| [STEWARDSHIP.md](../STEWARDSHIP.md) | 11 binding principles | Everyone | 10 min |
| [DECISIONS.md](DECISIONS.md) | Why we chose what we chose | Team leads, founders | 15 min |
| [LESSONS.md](LESSONS.md) | What broke + how we fixed it | Engineers, team | 10 min |
| [GOVERNANCE_OPERATIONAL.md](GOVERNANCE_OPERATIONAL.md) | Who decides what | Leadership | 10 min |
| [OPEN-DECISIONS.md](OPEN-DECISIONS.md) | Questions pending approval | Founders | 5 min |
| [QUICKSTART_24HOUR.md](../docs/QUICKSTART_24HOUR.md) | 4-hour governance setup | New teams | 30 min |
| [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) | AI-native architecture | Decision makers | 15 min |
| [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) | Build plan | Engineers | 10 min |

---

## 🔄 How We Work

### **Before Commit**
1. Does this touch a principle? → Reference in DECISIONS.md
2. Does this fail a gate? → Fix it (no bypasses)
3. Non-obvious choice? → Add entry to DECISIONS.md

### **In Code Review**
- [ ] DECISIONS.md updated (if non-obvious)
- [ ] Privacy gate passed
- [ ] Honors our principles (check against STEWARDSHIP.md)

### **In Incident**
1. Fix the bug
2. Add LESSONS.md entry (what broke + how we fixed it)
3. Update automation to catch it next time

### **Monthly**
- Skim DECISIONS.md (are we on track?)
- Check LESSONS.md (patterns emerging?)
- Ask: "Are we honoring our 11 principles?"

### **Quarterly**
- Review principles (still right for us?)
- Update GOVERNANCE_OPERATIONAL.md (if roles changed)
- Plan next improvements

---

## ❓ Questions

**"Does governance slow us down?"**  
No. It catches mistakes that would be costlier to fix later.

**"What if we violate a principle?"**  
Log it in DECISIONS.md, explain why, fix it next. That's the process.

**"How do new people learn this?"**  
Read STEWARDSHIP.md (10 min), do a code review, make a commit. They're in.

**"Can we skip the gates?"**  
No. Gates are automatic; they protect everyone, including the founder.

**"What if principles conflict?"**  
Document it in OPEN-DECISIONS.md. Real conflicts are rare and worth discussing.

---

## 🚀 Next Steps

### **This Week (Phase 1)**
1. Engineer: Build FRAMEWORK.json (2 hours)
2. Engineer: Create quickstart templates (3 hours)
3. Tech lead: Update README + links (2 hours)
4. Validate: All links work, schema valid (1 hour)

### **Next Week (Phase 2)**
1. Add SEO meta tags
2. Create governance landing page
3. Optimize for Google/Claude Search

### **Week 3 (Phase 3)**
1. Build public registry
2. Create submission flow
3. Seed with 5+ example orgs

### **Week 4 (Phase 4)**
1. Validate all systems working
2. Launch publicly
3. Announce to civic-tech community

---

## 📞 Help & Questions

- **Governance question?** → Check OPEN-DECISIONS.md, ask in GitHub issue
- **Decision question?** → Read DECISIONS.md for similar past decisions
- **Lesson question?** → Check LESSONS.md for patterns
- **Principles conflict?** → Bring to founder + team meeting

---

## 🤝 Contributing to Governance

You can improve governance by:
1. Adding entries to DECISIONS.md (why you chose what you chose)
2. Adding entries to LESSONS.md (what broke + how you fixed it)
3. Suggesting new principles (if something's missing)
4. Expanding automated gates (what else should we block?)
5. Improving compliance for your region (GDPR, LGPD, etc.)

---

**Built by:** Akbar (founder), Claude (engineering), Codex (strategy), and you  
**Governed by:** [STEWARDSHIP.md](../STEWARDSHIP.md) — 11 binding principles  
**Last updated:** August 10, 2026  
**Status:** Phase 1 (FRAMEWORK.json) in progress
