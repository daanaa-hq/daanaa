# IT Security & Cybersecurity Stakeholder Primer
## Board Meeting July 22, 2026

**Your Role:** Data security, infrastructure security, incident response, and compliance with regulatory requirements (GDPR, CCPA, COPPA, etc.).

**Time to read:** 5 minutes | **Decisions:** 4 key (11, 12, 13, 15) + cost estimates

---

## Your Critical Decisions

### Decision 13: Data Retention & Privacy Policy ⚠️ **VOTE NEEDED**

**Question:** Permanent, 7-year, 1-year, or hybrid PII + aggregates?

**Your IT security angle:** Data minimization, breach exposure, and incident response.

| Option | Data at Risk | Breach Exposure | Incident Response | Security Benefit |
|--------|---|---|---|---|
| **Permanent** | Very high (all records forever) | ❌ Highest | Worst (years of exposure) | None |
| **7-Year** | Medium (7 years only) | ✅ Good | Good (delete after violation) | Good |
| **1-Year** | Low (1 year only) | ✅ Best | Best (fast deletion post-incident) | Best |
| **Hybrid (PII 7yr, agg ∞)** | Medium (PII only) | ✅ Good | Good (PII deleted) | Good |

**IT Security Flags:**

**Permanent retention = increased breach risk:**
- Larger database = larger attack surface
- Longer data retention = longer exposure if breached
- More data = higher regulatory fines (GDPR: €20M or 4% revenue, whichever higher)

**7-year retention (recommended):**
- Balances legal requirement (IRS 7-year), regulatory compliance (GDPR/CCPA right to deletion), and incident response
- If breach occurs, we can delete PII immediately post-incident (reduces fine exposure)
- Hybrid (7-year PII + indefinite aggregates) adds security benefit: aggregates have no PII, so no privacy risk even if breach occurs

**Recommendation:** Option D (Hybrid: 7-year PII, indefinite aggregates). Minimizes data at risk, improves incident response, regulatory-compliant.

---

### Decision 12: Volunteer Verification ⚠️ **VOTE NEEDED**

**Question:** Self-attestation, school-mediated, third-party ID, or hybrid?

**Your IT security angle:** Fraud prevention, identity verification, and data flow security.

| Option | Fraud Prevention | Data Flow Security | Identity Spoofing Risk |
|--------|---|---|---|
| **Self-attestation** | ❌ None (anyone can claim age) | Low (no data shared) | ✅ High (easy to fake) |
| **School-mediated** | ✅ Good (school verifies) | ⚠️ Medium (FERPA-protected) | ✅ Low (school trusts verification) |
| **Third-party ID** | ✅ Best (ID verified) | ❌ High (PII to vendor) | ❌ Lowest (ID checked) |
| **Hybrid** | ✅ Best (school primary) | ⚠️ Medium | ✅ Low |

**IT Security Flags:**

**Self-attestation (risky):**
- No identity verification = easy fraud (fake students submit fake hours)
- Decision 3 (fraud detection) tries to flag fraud post-hoc, but reactive
- Self-attestation + no verification = fraud detection workload increases

**School-mediated (recommended):**
- Schools already verify students (FERPA-compliant)
- We don't receive PII, just "Jane is a 9th grader" (yes/no)
- Fraud risk drops dramatically (school verification is strong signal)

**Third-party ID (avoid):**
- Vendor receives student ID or photo (COPPA/GDPR/CCPA risk)
- Data breach at vendor = student PII exposed
- Better fraud detection, but data security trade-off

**Hybrid (best):**
- School verification primary (FERPA-safe, strong fraud signal)
- Third-party fallback only for non-school students (homeschooled, independent)
- Limits third-party PII data to small subset

**Recommendation:** Option D (Hybrid: school primary, third-party fallback). Strong fraud prevention + minimal third-party data.

---

### Decision 11: Volunteer Liability Structure ⚠️ **VOTE NEEDED**

**Question:** Who is liable if volunteer causes damage? Nonprofit, Daanaa, or shared?

**Your IT security angle:** Incident disclosure, breach notification, and insurance coordination.

| Option | We're Liable | Insurance Required | Incident Disclosure |
|--------|---|---|---|
| **Nonprofit bears all** | ❌ No | Optional | None (org handles) |
| **Shared liability** | ⚠️ Secondary | ✅ Yes (E&O) | Coordinated (we + org) |
| **Daanaa assumes** | ✅ Yes | ✅ Yes (high-limit) | Us (we're the deep pocket) |

**IT Security note:** Liability structure doesn't directly affect IT security, but affects **incident response obligations.**

- If shared liability + E&O insurance: Insurer wants incident report within 48h (drives fast response)
- If nonprofit bears all: We may not be obligated to report (slower response)
- If Daanaa assumes: We're primary defendant (fast incident response required)

**Recommendation (from IT perspective):** Shared liability (Decision 11) + E&O insurance (Decision 15). Requires incident response protocol (define within 30 days of approval).

---

### Decision 15: Insurance & Risk Management ⚠️ **VOTE NEEDED**

**Question:** Bare minimum, moderate, comprehensive, or progressive coverage?

**Your IT security angle:** Cyber insurance, breach response, and incident costs.

| Option | Cyber Liability | Breach Costs Covered | Annual Cost |
|--------|---|---|---|
| **Bare Minimum** | ❌ No | ❌ No ($0 coverage) | $2–5K |
| **Moderate** | ❌ No | ❌ No (only GL + E&O) | $10–15K |
| **Comprehensive** | ✅ Yes ($1M limit) | ✅ Yes (breach costs) | $30–50K |
| **Progressive** | ⚠️ Year 2 (Y1 none) | ⚠️ Year 2 (Y1 none) | $10–15K Y1 → $30–50K Y2 |

**IT Security Flags:**

**Cyber insurance (critical):**
- Covers data breach costs (incident response, forensics, notification, credit monitoring)
- Covers regulatory fines (GDPR, CCPA, COPPA breach fines)
- Covers business interruption (if we're offline after breach)
- Typical breach costs: $50K (forensics) + $100K+ (notification) + $1M+ (regulatory fines if large breach)

**Cyber breach cost example:**
- Incident response firm: $50–100K
- Notification (email, letter, credit monitoring): $100–500K (scales with victim count)
- Regulatory fine (GDPR 2–4%): $1M+ (if 10M+ users affected)
- Litigation: $500K–2M
- **Total: $1–3M per major breach**

**Without cyber insurance:** We absorb all costs. $1–3M breach could bankrupt a lean startup.

**Recommendation:** Option D (Progressive). Year 1: moderate (GL + E&O = $10–15K). Year 2: add cyber ($15–20K additional). Scales coverage as our data grows.

---

## Cybersecurity Action Items

### Year 1 (Pilot Phase)

**Infrastructure & Data:**
- [ ] Encrypt all data at rest (AES-256, database-level encryption)
- [ ] Encrypt all data in transit (TLS 1.3, HTTPS everywhere)
- [ ] Implement access controls (role-based, least privilege)
- [ ] Database backups: encrypted, off-site (S3), tested monthly
- [ ] API authentication: OAuth2 or equivalent (no passwords in logs)

**Privacy & Compliance:**
- [ ] Data minimization: collect only necessary fields (age, email, nonprofit EIN)
- [ ] PII removal: no student names, phone numbers, addresses in logs
- [ ] Retention policy: implement 7-year deletion (automated purge)
- [ ] GDPR/CCPA compliance: document data flows, consent mechanisms
- [ ] COPPA compliance: parental consent process for <13 (if applicable)

**Incident Response:**
- [ ] Incident response plan (document within 30 days of insurance approval)
- [ ] Breach notification process (notify affected users within 72h per GDPR)
- [ ] Forensics partner (engage incident response firm before breach)
- [ ] Communication plan (internal + external messaging)

**Cost Estimate (Year 1):**
| Item | Cost |
|------|------|
| Encryption tools (licensed) | $5–10K |
| Backup infrastructure (S3 + encyption) | $2–5K |
| GDPR/CCPA compliance audit | $10–20K |
| Incident response retainer (standby contract) | $5–10K |
| Security testing (penetration test 1x/year) | $5–15K |
| **Total Year 1** | **$27–60K** |

### Year 2 (Post-Pilot)

**Monitoring & Detection:**
- [ ] SIEM (Security Information and Event Management) for log monitoring
- [ ] WAF (Web Application Firewall) to block common attacks
- [ ] DLP (Data Loss Prevention) to prevent exfiltration
- [ ] Vulnerability scanning (automated weekly)

**Compliance & Audit:**
- [ ] Annual security audit (SOC 2 Type II readiness)
- [ ] Penetration testing (2x/year)
- [ ] Cyber insurance renewal (upgrade to comprehensive)

**Cost Estimate (Year 2 incremental):**
| Item | Cost |
|------|------|
| SIEM license | $5–15K |
| WAF + DLP (SaaS) | $3–8K |
| Vulnerability scanning | $2–5K |
| Cyber insurance (comprehensive) | $15–20K |
| **Total Year 2 incremental** | **$25–48K** |

---

## Cost Breakdown by Decision

### Year 1 Cybersecurity Budget (Pilot Phase)

| Decision | Security Requirement | Cost Impact |
|----------|---|---|
| **Decision 13 (7-yr retention)** | Automated deletion + compliance monitoring | +$10–15K |
| **Decision 12 (verification)** | Fraud detection system (data minimization) | +$5–10K (tools, not vendor data) |
| **Decision 11 (liability)** | Incident response plan + insurance coordination | +$5–10K |
| **Decision 15 (moderate insurance)** | E&O + GL (no cyber Y1) | +$10–15K |
| **Baseline (encryption, backups, GDPR)** | Necessary for all options | +$15–25K |
| **Total Year 1** | | **$45–75K** |

### Year 2 Cybersecurity Budget (Post-Pilot, if Scaling)

| Addition | Cost |
|----------|------|
| Cyber insurance (Decision 15 upgrade) | +$15–20K |
| SIEM + monitoring | +$5–15K |
| Annual compliance audits | +$10–20K |
| **Total Year 2 incremental** | **$30–55K** |

---

## IT Security Risks by Decision

| Decision | Security Risk | Mitigation |
|----------|---|---|
| **Decision 1 (account model)** | <13 accounts = higher COPPA compliance burden | School verification reduces risk |
| **Decision 6 (16+ age)** | 16+ = fewer COPPA risks | Enforcement: verify age proactively |
| **Decision 12 (school verification)** | FERPA compliance (if schools involved) | Sign DUA, limit data access, audit access logs |
| **Decision 13 (7-yr retention)** | Must implement auto-deletion | Build deletion pipeline, test quarterly |
| **Decision 15 (insurance)** | Without cyber insurance, breach costs uninsured | Upgrade to comprehensive Year 2 |

---

## Questions to Raise in Meeting

1. **Data retention (Decision 13):**
   - "Do we have budget for automated 7-year deletion pipeline? (~$5K to build)"
   - "Should we hire a compliance officer or outsource (DPO)?"

2. **Verification (Decision 12):**
   - "If third-party ID used, who vets the vendor for security? (SOC 2, GDPR compliance, etc.)"
   - "Should we limit PII flow to vendor (e.g., only age, not name)?"

3. **Insurance (Decision 15):**
   - "Can we skip cyber insurance Year 1 and add Year 2? (Risky but saves $15K)"
   - "What's our cyber insurance premium if we have 100K volunteers? (affects scalability)"

4. **Overall:**
   - "What's our security testing cadence? (1x/year? 2x/year?)"
   - "Do we have a security incident response plan drafted? (Required for board approval)"

---

## Post-Meeting Actions for You

- [ ] Draft incident response plan (30 days after approval)
- [ ] Implement data retention deletion pipeline (automated 7-year purge)
- [ ] Audit current encryption & access controls (ensure TLS, AES-256)
- [ ] Get cyber insurance quotes (include breach notification costs)
- [ ] Schedule compliance audit (GDPR/CCPA/COPPA readiness)
- [ ] Build FERPA compliance documentation (if schools involved)

---

## Security Best Practices (Beyond This Decision)

**Always follow:**
- No secrets in logs (passwords, API keys, PII)
- No student names in system logs or error messages
- No donor giving data in analytics or reports
- Encrypted backups only (test restoration monthly)
- Access logs for all data access (audit trail for compliance)
- Annual penetration testing (find vulnerabilities before attackers)

---

**Who to contact before meeting:** Chief Information Officer or security lead (for current encryption/backup state)

**Meeting prep:** Bring current security audit results, encryption inventory, backup tests, and cyber insurance quotes (3 providers).

---

## Summary: IT Security Enables Compliance

**The core insight:** All 15 board decisions have IT security implications. Strong IT security enables us to:
- Honor COPPA (verify age, delete on parental request)
- Honor GDPR/CCPA (delete PII on request, encrypt in transit)
- Honor FERPA (minimize school data collection, access controls)
- Mitigate fraud (detect anomalies, verify identity)
- Respond to incidents (forensics, breach notification)

**Without IT security investment ($45–75K Y1), compliance decisions (13, 14, 15) are unenforceable.**
