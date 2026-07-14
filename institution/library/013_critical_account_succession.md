# Critical Account Succession Plan
Library Document 013 · Version 1.0 (Action Required)
Prepared 2026-07-13

## Why This Matters (Founder Concentration Risk)

Akbar Khowaja is currently the sole admin on accounts that, if lost, would block:
- Production deployment (GitHub, Droplet SSH, domain)
- AI-powered enrichment (llama.cpp servers, model files)
- Backup and disaster recovery
- Regulatory and compliance records
- Public charter and trust communication

**Risk:** Death, medical emergency, account compromise, or lost credentials creates 
operational crisis with no recovery path.

**Mitigation:** Add a trusted second admin who can access critical systems within 72 hours.

---

## Critical Accounts Requiring Second Admin

| System | Current Owner | Risk Level | Second Admin | Status |
|--------|---------------|-----------|--------------|--------|
| GitHub | Akbar | CRITICAL | ? | ❌ NEEDED |
| Droplet SSH (162.243.97.179) | akbar | CRITICAL | ? | ❌ NEEDED |
| Domain registrar (daanaa.org) | Akbar | HIGH | ? | ❌ NEEDED |
| Firebase (wallet auth) | Akbar | HIGH | ? | ❌ NEEDED |
| Linode account | Akbar | HIGH | ? | ❌ NEEDED |

---

## Succession Criteria

Second admin should:
1. Have operational Linux/DevOps experience (can SSH, restart services)
2. Be trustworthy with founder-level access (board member, legal counsel, or advisor)
3. Have demonstrated commitment to Daanaa's mission
4. Be reachable within 72 hours (different timezone OK if communication plan exists)
5. Have understanding of Daanaa's Charter and governance principles

---

## Immediate Actions

- [ ] Identify the second admin (board decision or founder choice)
- [ ] Brief them on succession responsibilities (read STEWARDSHIP.md, this document)
- [ ] Add as GitHub organization owner (enable 2FA)
- [ ] Add SSH public key to Droplet /root/.ssh/authorized_keys
- [ ] Add as secondary contact on domain registrar
- [ ] Add as Firebase secondary project owner
- [ ] Document handoff procedures in `SUCCESSION_PROCEDURES.md`
- [ ] Test recovery (second admin verifies they can SSH/access all systems)

---

## Handoff Procedures (TBD)

If Akbar becomes unreachable:

1. **First 24 hours:** Board chair or legal counsel attempts contact
2. **24–48 hours:** Second admin gains production access via emergency procedures
3. **48–72 hours:** Second admin secures all critical systems, changes passwords, enables audit logging
4. **Day 4+:** Board decides on temporary operational continuity (redeploy if needed)

---

## Legal and Governance Notes

- Second admin is **NOT** a co-founder and does NOT inherit equity or decision authority
- Access is **emergency-only** and should remain documented and auditable
- This is **NOT** a replacement for legal succession planning (that requires a will/trust)
- Daanaa's code, brand, and mission remain in founder's control until legal entity transition

---

## Next Step

**Founder decision:** Who should be second admin? Once named, this can be implemented in < 1 day.

