# MERIT Risk Register

**Owner:** legal-lead, reviewed monthly by CEO
**Last updated:** 2026-05-19

Every risk has: description, current mitigation, tripwire metric, owner, last reviewed.
Severity scale: Critical / High / Medium / Low
Likelihood scale: High / Medium / Low

---

## CRITICAL risks (could kill the project)

### R-001: Profile claim fraud
**Severity:** Critical | **Likelihood:** High once Phase 1 begins
**Description:** Bad actor claims a nonprofit they don't represent. Redirects donors or damages org's reputation.
**Mitigation:**
- 4-layer verification (Identity / Authority / Possession / Human Review)
- All Phase 1 claims human-reviewed
- Physical mail to IRS address as strongest signal
- 30-day waiting period before activation
- Email Principal Officer when reachable
- Public pending-claim RSS feed
- 90-day post-approval challenge window
**Tripwire:** Any unverified claim flagged as fraudulent OR challenged successfully
**Owner:** nonprofit-success-lead
**Status:** Mitigations designed, deploy with Phase 1

### R-002: Data accuracy errors causing harm to a nonprofit
**Severity:** Critical | **Likelihood:** Medium
**Description:** Wrong donate link routes money to wrong place; wrong address embarrasses org; wrong badge defames.
**Mitigation:**
- IRS data displayed as-is with timestamp and source citation
- Clear public correction process
- Every datapoint shows provenance
- Self-reported corrections from verified claimants supplement, never overwrite IRS
- Donate links marked unverified until self-confirmed
- Weekly link health checker
**Tripwire:** Any formal complaint from a nonprofit about MERIT-displayed data
**Owner:** data-lead
**Status:** Schema designed for provenance; correction handler in Phase 1

### R-003: Legal action over tip jar framing
**Severity:** Critical | **Likelihood:** Low
**Description:** Texas AG, FTC, or private party claims tip jar misrepresents as charitable solicitation.
**Mitigation:**
- Tip disclosure language attorney-reviewed before launch
- Clear "this is not a tax-deductible donation" language
- Names operator (EcoMargins LLC) explicitly
- No "donate" terminology for tips
- No state-targeted advertising in Phase 0
**Tripwire:** Any inquiry from state AG or FTC; any C&D
**Owner:** legal-lead
**Status:** Drafted; pending attorney review (Gate 5)

### R-004: Security breach exposing PII
**Severity:** Critical | **Likelihood:** Medium
**Description:** Claim documents, IDs, email addresses, giving wallet entries leaked.
**Mitigation:**
- All sensitive data encrypted at rest
- 1Password Business for all credentials
- Cloudflare WAF + bot protection
- Security headers (CSP, HSTS, etc.)
- Rate limiting on all public endpoints
- Quarterly manual security review
- Vulnerability disclosure policy + security.txt
- Cyber liability insurance bound before launch
**Tripwire:** Any detected breach indicator; any unauthorized access attempt that succeeds
**Owner:** ops-lead + legal-lead
**Status:** Architecture designed; insurance pending (Gate 5)

### R-005: Burnout / founder bandwidth collapse
**Severity:** Critical | **Likelihood:** Medium
**Description:** Solo founder with full-time day job + MERIT alongside burns out. Project dies or stalls indefinitely.
**Mitigation:**
- Capped at 2–3 hrs/day per operating rhythm
- Mandatory off-days (Sat/Sun)
- Async-first; missing a session doesn't break anything
- Approval queue protects attention
- Recruit second human (contractor) by Month 9–12
- Quarterly retro includes burnout self-check
**Tripwire:** Skipped sessions > 5 in a week OR self-reported burnout signal at quarterly retro
**Owner:** strategy-lead + CEO self-monitoring
**Status:** Operating rhythm designed; ongoing discipline

---

## HIGH risks

### R-006: Competitive landscape — Candid/Charity Navigator copy MERIT
**Severity:** High | **Likelihood:** Medium
**Description:** Well-funded incumbent copies the directory + badge system. MERIT loses differentiation.
**Mitigation:**
- Privacy architecture (not just policy) is hard to copy
- Mission lock in LLC operating agreement
- GPO vendor ecosystem moat (Phase 2)
- Deterministic transparent scoring (incumbents are proprietary)
- Build-in-public credibility
- Community trust from sector engagement
**Tripwire:** Public announcement from Candid or CN of free directory at scale
**Owner:** strategy-lead
**Status:** Documented in `moats.md`

### R-007: Auto-revocation handling unclear
**Severity:** High | **Likelihood:** High (ongoing)
**Description:** ~30K orgs/year auto-revoked. MERIT's policy on showing/badging revoked orgs not yet defined.
**Mitigation:**
- Define policy before Phase 0 launch: revoked orgs shown with clear status, no badges, donate link warning
- Reinstated orgs return to normal status when reinstated
- Audit trail of revocation/reinstatement events
**Tripwire:** First revoked-org dispute
**Owner:** data-lead
**Status:** Policy needs definition (Week 6)

### R-008: 501(c)(3) revocation/reinstatement timing
**Severity:** High | **Likelihood:** Medium
**Description:** IRS data shows revoked, but org has filed for reinstatement and is in good faith. MERIT's display causes harm.
**Mitigation:**
- "Status as of YYYY-MM-DD per IRS" everywhere
- Self-reported reinstatement-in-progress can be noted (verified claimant only)
- Monthly IRS BMF refresh catches most
- Manual correction path for urgent cases
**Tripwire:** First org disputes their revoked status display
**Owner:** data-lead
**Status:** Process design in Week 6

### R-009: ProPublica TOS change
**Severity:** High | **Likelihood:** Low
**Description:** ProPublica changes CC BY-NC-ND 3.0 US licensing or restricts commercial-adjacent use; MERIT loses enrichment data.
**Mitigation:**
- IRS BMF is primary; ProPublica is enrichment only
- Architecture supports running without ProPublica
- Monitor ProPublica TOS quarterly
- Maintain proper attribution to stay in good standing
**Tripwire:** ProPublica TOS change announcement
**Owner:** legal-lead + data-lead
**Status:** Architecture is resilient; monitoring in place

### R-010: Stripe/Anthropic/Cloudflare/Vercel terms shift
**Severity:** High | **Likelihood:** Low
**Description:** Any core vendor changes terms in a way that affects MERIT (e.g., Stripe restricts tip jars for LLCs).
**Mitigation:**
- Use mainstream features only (Stripe Payment Links, not custom Connect)
- Tip framing as service-tied (not pure donation) per Stripe policy
- Vendor diversification where practical (Resend + SES, Cloudflare + DigitalOcean backup)
- Quarterly TOS review
**Tripwire:** Vendor notice of relevant terms change
**Owner:** legal-lead
**Status:** Monitoring in place

### R-011: Subpoena / law enforcement request for user data
**Severity:** High | **Likelihood:** Medium
**Description:** LE requests data on a user (especially giving wallet data, which is private).
**Mitigation:**
- Documented response process (verify request, narrow scope, attorney consult)
- Annual transparency report
- Minimize data retention by design
- Warrant canary consideration
**Tripwire:** First request received
**Owner:** legal-lead
**Status:** Process documented; not yet faced

### R-012: Sector journalist/influencer publishes negative piece
**Severity:** High | **Likelihood:** Low–Medium
**Description:** Misunderstanding or genuine criticism becomes published piece, damages reputation.
**Mitigation:**
- Build relationships proactively (Phase 0 outreach to sector journalists)
- Build-in-public minimizes surprise
- Transparent operations means few "gotcha" stories possible
- Crisis comms playbook drafted
**Tripwire:** Major outlet investigating
**Owner:** growth-lead + CEO
**Status:** Crisis comms playbook needed (Gate 6)

---

## MEDIUM risks

### R-013: Search quality insufficient
**Severity:** Medium | **Likelihood:** High
**Description:** Users can't find what they want; directory feels useless.
**Mitigation:**
- Typesense or Algolia free tier for proper search
- Multi-field indexing (name, NTEE, location, programs)
- User research validates search queries
- Search analytics drives improvement
**Tripwire:** Search-related bounce rate > 50%
**Owner:** eng-lead
**Status:** Plan in roadmap (Week 14)

### R-014: Mobile experience poor
**Severity:** Medium | **Likelihood:** Medium
**Description:** Donors and nonprofit EDs use phones; broken mobile = no users.
**Mitigation:**
- Mobile-first design from Week 1
- Real device testing (not just emulators)
- Core Web Vitals tracked
- Mobile-specific user research
**Tripwire:** Mobile bounce rate > 70% OR mobile feedback < 7/10
**Owner:** eng-lead
**Status:** Design constraint from start

### R-015: Accessibility regression
**Severity:** Medium | **Likelihood:** Medium
**Description:** Site fails WCAG 2.1 AA; violates mission of fair access.
**Mitigation:**
- WCAG 2.1 AA from day one
- Axe DevTools + Lighthouse in CI
- Manual screen reader testing pre-launch
- Mission-aligned with serving disability communities
**Tripwire:** Failed Lighthouse a11y < 95
**Owner:** eng-lead
**Status:** CI integration needed (Week 4)

### R-016: International donor / GDPR compliance
**Severity:** Medium | **Likelihood:** Low (impact: High)
**Description:** EU/UK donors visit; data handling triggers GDPR obligations.
**Mitigation:**
- Privacy policy covers GDPR scope
- Minimal data collection by design
- Right-to-deletion implemented
- Cookie consent (Cloudflare/Vercel options)
**Tripwire:** EU regulator inquiry OR > 5% EU traffic
**Owner:** legal-lead
**Status:** Privacy policy drafted; consent flow needed

### R-017: Fiscally sponsored organizations
**Severity:** Medium | **Likelihood:** High
**Description:** Org A is fiscally sponsored by Org B. Which EIN gets the credit? Whose profile gets the donate link?
**Mitigation:**
- Policy: fiscal sponsor relationship noted on both profiles
- Self-reported in claim flow
- Donate link goes to the sponsor (legal recipient)
- Sponsored org's profile cross-references sponsor
**Tripwire:** First fiscal sponsorship dispute
**Owner:** data-lead + nonprofit-success-lead
**Status:** Policy needs definition (Phase 1)

### R-018: Donor-advised funds and complex giving vehicles
**Severity:** Medium | **Likelihood:** Medium
**Description:** Major donors use DAFs, complicating "track my giving" wallet.
**Mitigation:**
- Phase 0 wallet is simple ("I gave $X on date Y")
- No DAF integration in Phase 0/1
- Phase 2 consideration
**Tripwire:** Major donor feedback requesting DAF integration
**Owner:** strategy-lead
**Status:** Deferred to Phase 2

### R-019: Group exemptions / parent-subordinate org relationships
**Severity:** Medium | **Likelihood:** Medium
**Description:** Parent org has ruling covering many subordinates (e.g., Boy Scouts councils). IRS BMF handling varies.
**Mitigation:**
- Display parent-subordinate relationship when in BMF
- Each subordinate has own profile with link to parent
- Claim flow handles parent authority
**Tripwire:** First parent-subordinate dispute
**Owner:** data-lead
**Status:** Policy needs definition (Week 8)

### R-020: NTEE classification errors
**Severity:** Medium | **Likelihood:** High
**Description:** ~30% of NTEE codes are wrong or imprecise in IRS data.
**Mitigation:**
- NTEE confidence scoring on display
- Self-correction in claim flow
- Multiple NTEE codes per org allowed (primary + secondary)
- Public methodology document
**Tripwire:** Aggregate NTEE confidence < 0.7 mean
**Owner:** data-lead
**Status:** Confidence scorer in plan

### R-021: Cost overrun
**Severity:** Medium | **Likelihood:** Medium
**Description:** Infrastructure costs exceed plan; runway compresses.
**Mitigation:**
- Cost sentinel agent with per-service thresholds
- Daily burn tracking
- Credit programs reduce baseline
- Monthly cost vs. plan review
**Tripwire:** Monthly burn > 130% of plan
**Owner:** finance-lead
**Status:** Cost sentinel needed (Week 4)

### R-022: Sector report quality insufficient
**Severity:** Medium | **Likelihood:** Medium
**Description:** Quarterly sector reports don't get picked up; marketing engine sputters.
**Mitigation:**
- First report (Invisible Majority) high quality before launch
- User research drives report topics
- Distribution strategy (sector press, advisors, communities)
- Iterate based on engagement
**Tripwire:** Report read-through < 100 in first month
**Owner:** growth-lead
**Status:** First report drafting starts Week 12

### R-023: GPO vendor partnership rejection
**Severity:** Medium | **Likelihood:** Medium
**Description:** No vendors willing to partner on GPO terms; Phase 2 thesis fails.
**Mitigation:**
- Phase 2 not a 6-month goal; validate Phase 1 first
- Start vendor conversations in Phase 1 with small set
- Mission alignment over scale (small good partners > many indifferent)
- Vendor matchmaker validates demand before formalized partnerships
**Tripwire:** First three vendor outreach all rejected
**Owner:** partnerships-lead
**Status:** Phase 2 readiness, not yet active

---

## LOW risks (track but minimal)

### R-024: Trademark issue with "MERIT"
**Severity:** Low | **Likelihood:** Low
**Description:** Heavily-used word; potential confusion or claim.
**Mitigation:**
- USPTO TESS search pre-launch
- Class registration consideration (Phase 1)
- Distinctive use as "MERIT" + tagline
**Tripwire:** Demand letter received
**Owner:** legal-lead
**Status:** TESS search scheduled (Gate 1)

### R-025: Domain expiry / DNS failure
**Severity:** Low | **Likelihood:** Very Low
**Description:** meritgiving.org expires or DNS fails; site goes dark.
**Mitigation:**
- Domain registered 10 years (per memory)
- Auto-renew on
- DNS hosted at Cloudflare (free, reliable)
- 1Password tracks all renewals
**Tripwire:** Renewal notification < 90 days out
**Owner:** ops-lead
**Status:** Already in good shape

### R-026: GitHub account compromise
**Severity:** Low (with mitigations) | **Likelihood:** Low
**Description:** GitHub credentials compromised; code/secrets exposed.
**Mitigation:**
- 2FA mandatory (passkey or hardware key)
- Org-level required 2FA for collaborators
- Secrets in 1Password, never in repo
- Branch protection rules on main
- Audit log monitoring
**Tripwire:** Unusual GitHub access pattern
**Owner:** ops-lead
**Status:** 2FA enforced from Day 1

### R-027: Vendor lock-in (mostly Vercel/Cloudflare)
**Severity:** Low | **Likelihood:** Low
**Description:** Heavy reliance on Vercel for hosting creates migration cost if needed later.
**Mitigation:**
- Next.js is portable
- Database (Neon Postgres) is standard
- Cloudflare DNS is standard
- 1-day migration plan documented
**Tripwire:** Vendor term change forcing migration
**Owner:** ops-lead
**Status:** Migration plan documented post-launch

### R-028: AI model deprecation
**Severity:** Low | **Likelihood:** Medium
**Description:** Claude API model used in skills gets deprecated; workflows break.
**Mitigation:**
- Use stable model strings; track Anthropic deprecation announcements
- Skills designed to work across Claude versions
- Anthropic Startup Program relationship provides advance notice
**Tripwire:** Anthropic deprecation announcement
**Owner:** eng-lead
**Status:** Standard model upgrade discipline

---

## Risk review process

**Monthly (1st of month):**
1. Each department lead reviews their owned risks
2. Update mitigation status, tripwire status
3. Add new risks observed during month
4. CEO + legal-lead review aggregated

**Quarterly (start of quarter):**
1. Full risk register reset
2. Re-score severity and likelihood
3. Retire risks no longer applicable
4. Add risks from new phase or new initiatives

**Annual:**
1. Comprehensive risk audit
2. Insurance coverage review against risk profile
3. Major mitigation budget allocation
