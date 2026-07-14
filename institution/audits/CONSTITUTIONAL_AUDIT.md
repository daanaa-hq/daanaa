# Constitutional Audit

Date: 2026-07-13

## Executive Finding

Daanaa has a unusually strong stewardship corpus for an early institution: mission, covenant, constitution, charter, privacy invariants, decision logs, lessons, succession planning, and tests all exist. The main risk is not absence of values. The main risk is overclaiming control maturity before the code, tests, operations, and external-account governance fully prove the public promises.

## Findings

### F-001: Charter firewall promise is stronger than current machine enforcement

Severity: HIGH  
Domains: Charter, Privacy, Security, Institutional memory, Legal review needed  
Affected files: `institution/DAANAA-CHARTER.md`, `frontend/src/pages/Charter.tsx`, `institution/library/011_data_classification.md`, `PRIVACY-INVARIANTS.md`, `scripts/privacy_check.sh`  
Evidence: Charter says Tier 2 data firewall is "enforced in our code"; library 011 says `privacy_check.sh` fails forbidden Tier 2 flows; local `scripts/privacy_check.sh` implements only four checks and does not implement a visible gate 8.  
Why it matters: This is a public promise about the boundary between Daanaa and EcoMargins. If the code gate is incomplete, the statement is too absolute.  
Governing principle: Information as trust; independence from paid influence; no silent weakening.  
Recommended resolution: Either implement and test the claimed Tier 2 firewall gate or revise public wording to "being implemented and audited" until enforcement is demonstrable.  
Founder decision required: Yes, for public wording and enforcement priority.  
Confidence: High  
Evidence strength: Strong  
Safe to automate: Partially

### F-002: Privacy invariants and wallet implementation have documentation drift

Severity: HIGH  
Domains: Privacy, Documentation, Product, Engineering  
Affected files: `PRIVACY-INVARIANTS.md`, `scripts/privacy_check.sh`, `frontend/src/contexts/WalletContext.tsx`, `daanaa_api.py`, `frontend/src/pages/Privacy.tsx`, `frontend/src/pages/Terms.tsx`  
Evidence: `PRIVACY-INVARIANTS.md` describes wallet data as account-scoped in one place; `privacy_check.sh` still checks that old local wallet keys are not POSTed; frontend code supports device-first local storage plus encrypted sync; backend also has `/api/wallet/backup` storing lean entries in DynamoDB or SQLite.  
Why it matters: Donor privacy is a constitutional promise. Users and future stewards need one accurate description of where wallet data lives.  
Governing principle: Donor privacy is structural; public and entrusted information must be clear.  
Recommended resolution: Produce a single wallet data-flow record and update privacy text, invariants, and checks to match the current implementation.  
Founder decision required: No for documentation alignment; yes if the product posture changes.  
Confidence: High  
Evidence strength: Strong  
Safe to automate: Partially

### F-003: Public charter "never charge for the platform" may conflict with optional paid capacity services unless narrowed

Severity: HIGH  
Domains: Charter, Sustainability, Legal review needed, Product  
Affected files: `institution/DAANAA-CHARTER.md`, `frontend/src/pages/Charter.tsx`, `institution/CONSTITUTION.md`, `VENDOR-POLICY.md`, `docs/legal/CAF-TEMPLATE.md`, product docs  
Evidence: Constitution allows premium services that improve nonprofit operations and cannot buy favorable public treatment. Charter says "Discovery, your profile, your dashboard, your peer context, and every core tool we build for nonprofits is free." Some roadmap/docs contemplate Guild economics, credits, letters, and services.  
Why it matters: The free-platform promise is important but could accidentally forbid mission-aligned sustainability if "core tool" is not defined.  
Governing principle: Financial sustainability serves the mission; mission does not serve extraction.  
Recommended resolution: Define "core platform" and "optional paid capacity-enhancing services" in the charter controls before broad publication.  
Founder decision required: Yes.  
Confidence: High  
Evidence strength: Strong  
Safe to automate: No

### F-004: Donation custody prohibition is directionally supported, but donation-related surfaces need a unified policy

Severity: MEDIUM  
Domains: Charter, Product, Legal review needed, Privacy  
Affected files: `docs/legal/TERMS-OF-SERVICE.md`, `daanaa_api.py`, `scripts/droplet_api.py`, `frontend/src/pages/OrganizationDetail.tsx`, `tests/test_no_public_donation_fields.py`, `frontend/src/components/DonationLogger.tsx`  
Evidence: Terms say Daanaa is not merchant of record or payment intermediary. No Stripe/checkout donation custody flow was found. Wallet logging, donation return prompts, claimed donate URLs, and donation-link exposure exist or are contemplated.  
Why it matters: "Never take custody" is different from "never mention or link to donations." The institution needs one controlled policy for donation links, donation logs, tax letters, and donor self-reporting.  
Governing principle: Daanaa does not take custody, process donations, or take a cut.  
Recommended resolution: Adopt a Donation Boundary Policy mapping permitted and forbidden donation-adjacent features.  
Founder decision required: Yes.  
Confidence: Medium-high  
Evidence strength: Strong for custody; moderate for all surfaces  
Safe to automate: No

### F-005: Paid influence controls are well stated but not yet fully auditable end-to-end

Severity: HIGH  
Domains: Charter, Commercial independence, Operations, Governance  
Affected files: `STEWARDSHIP.md`, `VENDOR-POLICY.md`, `institution/library/011_data_classification.md`, `daanaa_api.py`, `scripts/droplet_api.py`, `frontend/src/pages/VendorPolicy.tsx`  
Evidence: Policies prohibit paid influence; code sorting and scoring appear method-driven. But no complete quarterly audit artifact or automated relationship-to-outcome test was found in this audit.  
Why it matters: Paid influence is one of the highest-trust promises. It requires recurring evidence, not only policy language.  
Governing principle: Payment cannot influence public visibility, search treatment, ranking, or Peer Financial Context.  
Recommended resolution: Add quarterly self-audit template and relationship/outcome sampling procedure before claiming regular audit maturity.  
Founder decision required: No for process; yes for publication wording.  
Confidence: Medium-high  
Evidence strength: Moderate  
Safe to automate: Partially

### F-006: Concierge test failure shows schema/test drift in a governed workflow

Severity: MEDIUM  
Domains: AI governance, Information provenance, Engineering, Quality  
Affected files: `daanaa_api.py`, `tests/test_concierge_confirm.py`  
Evidence: Targeted pytest run failed 6 concierge tests because `_write_claimed_fields_to_registry` expects `org_claims.donate_url` while the fixture lacks that column.  
Why it matters: Concierge is governed by a board resolution and handles nonprofit-provided enhancements. Tests should be a reliable assurance layer.  
Governing principle: AI is infrastructure, never deception; corrections and provenance must be traceable.  
Recommended resolution: Align the fixture with current schema or make the writer column-aware.  
Founder decision required: No.  
Confidence: High  
Evidence strength: Strong  
Safe to automate: Yes, after documentation-only audit is complete.

### F-007: Legal-sounding public claims need counsel review before final publication

Severity: HIGH  
Domains: Legal review needed, Charter, Privacy, Sustainability  
Affected files: `institution/DAANAA-CHARTER.md`, `frontend/src/pages/Charter.tsx`, `frontend/src/pages/Privacy.tsx`, `frontend/src/pages/Terms.tsx`, `docs/legal/*`  
Evidence: Public pages include absolute "never" claims, deletion/export promises, privacy promises, liability language, and attorney-review-in-progress notes.  
Why it matters: Strong promises are appropriate, but legal counsel should review enforceability, exceptions, and jurisdiction-specific obligations.  
Governing principle: Do not present Daanaa as legal counsel; escalate legal decisions to humans.  
Recommended resolution: Treat publication drafts as founder/counsel review material, not final law.  
Founder decision required: Yes.  
Confidence: High  
Evidence strength: Strong  
Safe to automate: No

### F-008: Backup script now fails loudly, but offsite backup existence remains unverified from repo evidence

Severity: MEDIUM  
Domains: Succession, Operations, Security, Institutional memory  
Affected files: `scripts/ops/daanaa_backup.sh`, `institution/SUCCESSION.md`, `institution/RISK_REGISTER.md`  
Evidence: `bash -n` passes; script exits nonzero if rclone/remote/connectivity/push/verification fail. Repository does not prove current Google Drive backup freshness.  
Why it matters: A successor needs verified restore confidence, not just backup code.  
Governing principle: Institutional memory must not depend on one server.  
Recommended resolution: Run and record a non-destructive restore test with redacted evidence.  
Founder decision required: Possibly, for provider access.  
Confidence: Medium-high  
Evidence strength: Strong for script; weak for live backup state  
Safe to automate: Partially

### F-009: Founder/provider-console concentration remains a continuity risk

Severity: HIGH  
Domains: Succession, Security, Operations, Institutional memory  
Affected files: `institution/SUCCESSION.md`, `institution/RISK_REGISTER.md`, `institution/state.json`  
Evidence: Succession and risk docs identify founder-only GitHub/provider/billing/account access as unresolved or unknown.  
Why it matters: A long-lived institution cannot rely on one person for recovery, billing, legal, deploy, or domain continuity.  
Governing principle: Authority is trusteeship; memory must survive leadership transitions.  
Recommended resolution: Add second admin, provider access map, emergency contact process, and quarterly recovery checklist.  
Founder decision required: Yes.  
Confidence: Medium  
Evidence strength: Moderate  
Safe to automate: No

### F-010: Older documents contain superseded donation, wallet, and platform claims

Severity: MEDIUM  
Domains: Documentation, Institutional memory, Charter  
Affected files: `docs/`, `05192026/`, `.gstack/`, `.superpowers/`, planning docs  
Evidence: Historical docs reference donation links, wallet models, claim flows, and fundraising/payment features that do not always match current charter posture.  
Why it matters: Future stewards may accidentally revive deprecated plans if document status is unclear.  
Governing principle: Institutional memory preserves history without confusing it with current authority.  
Recommended resolution: Add status headers or index classifications for high-risk historical docs.  
Founder decision required: No.  
Confidence: High  
Evidence strength: Strong  
Safe to automate: Partially

## Overall Constitutional Verdict

Sound with open controls. The constitutional direction is coherent: free public discovery, no paid influence, donor privacy, public-vs-entrusted separation, AI disclosure, context not verdict, and sustainability in service of mission. The highest-priority work is control maturity: make the public promises demonstrably enforceable, audit recurring controls, and narrow any absolute claim that cannot be technically or operationally sustained.

