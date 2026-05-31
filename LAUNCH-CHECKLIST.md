# Daanaa — Launch Checklist & Gates

Single source of truth for what must be true before public launch. **Gates** are
hard blockers. **Build** is feature work. Check items off as they land.

Automated gate already enforced: `scripts/privacy_check.sh` runs on every commit
(pre-commit hook). See `PRIVACY-INVARIANTS.md`.

---

## GATES — must pass before public launch (hard blockers)

- [ ] **G1. Attorney review** of `meritgiving-ops/legal/daanaa-governance-charter.md`,
      AI-content liability (AI missions about named orgs), UGC moderation / Section 230
      posture, org Terms of Use, and image rights / minors. (See board sim.)
- [ ] **G2. IRS auto-revocation handling.** Check orgs against the IRS auto-revocation
      list; suppress or clearly badge donate for revoked orgs. Showing a revoked org as
      donatable is real harm + liability.
- [ ] **G3. Privacy invariants green** in CI/pre-commit (`scripts/privacy_check.sh`). ✅ enforced
- [ ] **G4. Donate-link trust gating** stays fail-closed on unverified statuses. ✅ in place
- [ ] **G5. Methodology page matches the live scorer** (0.65 revenue / 0.35 reserve). ✅ aligned
- [ ] **G6. Org Terms of Use** published (separate from donor terms): what orgs may post,
      that they warrant authorization, and a content license to display it.
- [ ] **G7. Content moderation + takedown path** live before any org-generated content
      (open space, updates, needs, photos) is accepted. Input sanitization (XSS).

## BUILD — feature work toward launch

### Shipped ✅
- [x] AI provenance/beta for missions, donate links, and cause tags (`data_badges`)
- [x] AI/scraper disclaimer (Legal page + footer)
- [x] Claimed-profile wireframe + on-page empty-state preview of claimable spaces
- [x] Wallet backup: self-text + file export/import + 90-day nudge
- [x] Privacy: IP-free access logs, `PRIVACY-INVARIANTS.md`, `privacy_check.sh`, pre-commit hook
- [x] Governance charter draft (from STEWARDSHIP)

### In progress / next
- [x] **B1. Backup file encryption** — passphrase-based AES-GCM (PBKDF2) client-side; key never leaves device
- [~] **B2. Capacitor native wrapper** — `frontend/capacitor.config.ts` + `docs/native-app-setup.md`
      ready. Remaining is FOUNDER ACTION: Apple Developer + Google Play accounts, Mac/Xcode,
      run the documented install + publish.
- [~] **B3. Volunteer flow** — `VolunteerInterest` component built (anonymous/named + age-range
      toggle, device-send, nothing stored), wired into the org profile. Full reach pending B4
      (org-provided volunteer contact/link).
- [ ] **B4. Claim-and-edit flow** — let claimed orgs actually set mission, 5 tags, ways-to-help,
      needs, updates, photo (the wireframe, made real).
- [ ] **B5. Fiscal sponsorship** field — donations routed through a sponsor with a different EIN.
- [ ] **B6. Site alignment pass** — provenance/beta consistency across all pages.

## OPS / INFRA
- [ ] Git remote set up + push (task #10)
- [ ] Native-backup story documented for users ("your giving rides your phone backup")
- [ ] Pre-launch full privacy + stewardship compliance review

---

_Last updated: 2026-05-31. Update this file as items land; it is the launch gate of record._
