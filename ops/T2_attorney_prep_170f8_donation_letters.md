# T2 Attorney Prep: §170(f)(8) Donation Letter Requirements

**Purpose:** Define exact requirements for Daanaa's automated donation letter service before attorney review.  
**For:** Attorney to confirm Daanaa can legally auto-generate letters and what org disclaimers are needed.

---

## What §170(f)(8) Requires

IRS Code §170(f)(8) states that a donor claiming a tax deduction for a cash donation **>$250** must have a contemporaneous written acknowledgment (CWA) from the nonprofit.

**The letter must contain:**
1. **Amount of the donation** (or "received as a pledge, not yet paid")
2. **Description of goods/services provided** in exchange, if any (e.g., "donor attended gala valued at $50"; if none, state "no goods or services provided")
3. **Solicitation text disclaimer:** Copy of the nonprofit's actual solicitation that disclosed whether goods/services would be provided and estimated fair market value
4. **Nonprofit's EIN**
5. **Nonprofit name** (matches IRS Form 990)

**The organization that RECEIVED the donation must issue the letter** — it cannot delegate this entirely to a third party. However, the nonprofit **can use software/agents to draft**, and the **nonprofit officer signs** (or electronically authorizes) the letter.

---

## Daanaa's Model (Letter Service @ G3)

**Who does what:**
1. **Donor** gives money to Nonprofit A via Every.org / payment processor (never touches Daanaa)
2. **Nonprofit A's officer** logs into Daanaa's letter-gen tool (or receives a draft email)
3. **Daanaa system** auto-generates a CWA draft using:
   - Donation amount (from org's records or processor webhook, not Daanaa's observation)
   - Org's EIN + name (from IRS registry)
   - Org's solicitation language (org provides or we pull from website)
4. **Nonprofit officer approves/customizes/signs** (PDF or e-signature) — org is legally responsible
5. **Nonprofit emails letter to donor** (or Daanaa can mail on org's behalf if authorized in writing)

**Daanaa's legal posture:**
- You are a **software vendor providing a CWA drafting tool**, not the issuer
- The **nonprofit is the issuer** (must sign)
- Daanaa must ensure the draft contains all §170(f)(8) required elements, but the nonprofit is responsible for accuracy + signing

---

## IRS Penalties & Red Flags

**If the nonprofit ignores §170(f)(8):**
- Donor cannot claim the deduction (IRS will disallow if audited)
- Nonprofit can lose donors' trust
- Nonprofit **not directly penalized** by IRS, but donor-facing risk is high

**If Daanaa provides a CWA that's incomplete:**
- Nonprofit using it would be liable, not Daanaa (assuming clear disclaimer)
- But Daanaa could face reputational / legal risk if claimed the software handles "everything" (it doesn't — org signs)
- **Mitigation:** Clear UI language: "This draft requires your review and approval. You are responsible for the accuracy of this letter before sending to donors."

---

## Special Cases & Nuances

1. **Multi-gift aggregation:** If a donor gives $100 + $200 in same tax year, the org can issue one letter for the combined $300 (not two separate letters). Daanaa system should support this.
2. **Pledges vs cash:** Pledges are NOT subject to §170(f)(8) (only cash contributions). Daanaa should ask: "Is this a cash gift or a pledge?"
3. **Quid pro quo disclosure:** If the nonprofit runs a fundraiser dinner, the donor must be told that $50 of their $200 gift is for the dinner (Fair Market Value of goods). Daanaa should prompt: "Any goods/services provided?"
4. **Electronic signatures:** IRS allows electronic signatures on CWAs (per Rev. Proc. 98–25 and subsequent guidance). Org officer can e-sign via DocuSign, etc.
5. **Timing:** The CWA must be issued "contemporaneously" — IRS interprets this as "reasonably promptly" (generally within 90 days). Daanaa should generate the draft within 1–7 days of the donation being recorded.
6. **E-mail delivery:** IRS permits email delivery of CWAs (including PDF attachments). Mailed copies also acceptable.

---

## Daanaa's Operational Checklist (before launch @ G3)

- [ ] **Terms of Service:** Daanaa's letter-gen tool explicitly states the nonprofit is responsible for the content and accuracy of the letter before signing.
- [ ] **Org authentication:** Only org officers with verified EIN/email can access the tool. Limit to 1–2 admins per org.
- [ ] **Auto-populate:** Pre-fill with EIN, org name, donation amount (from processor webhook or org's manual entry), date. Leave "goods/services?" as a required form field.
- [ ] **Draft review screen:** Show the full CWA draft to the org before they can sign/send. Include a checkbox: "I confirm this letter is accurate per §170(f)(8) and IRS guidelines."
- [ ] **Signature method:** Support electronic signature (e.g., Docusign integration) or scanned signature uploaded by org.
- [ ] **Record keeping:** Daanaa stores a copy of the signed letter + timestamp in org's account for IRS audit trails.
- [ ] **Audit log:** Daanaa logs all draft generations, edits, and sign-offs (for compliance review if needed).
- [ ] **Webhook integration:** If Daanaa integrates with processors (Every.org, Stripe, etc.), verify donation data accuracy before auto-populating the letter.

---

## Questions for Attorney

1. **Can Daanaa auto-generate the letter without the org uploading solicitation language**, or must the org always provide/confirm the exact language that was in the solicitation?
2. **If Daanaa hosts the signed letter in the org's account**, does Daanaa have any liability if the org later claims they didn't authorize a letter, or is the electronic signature/org's account log sufficient proof?
3. **For nonprofits outside the US** (e.g., Canadian donors giving to a US 501(c)(3)), does §170(f)(8) apply? Any special language needed?
4. **If a donor asks Daanaa directly for a letter** (not the org), what should Daanaa's response be? (Should be: "Contact your nonprofit directly — we provide the tool, not the letter.")
5. **Multi-org scenario:** If one donor gives to 3 different orgs, can Daanaa provide a consolidated CWA, or does each org issue separate letters?

---

## Compliance Resources (for attorney)

- **IRS Publication 526:** Charitable Contributions (includes §170(f)(8) summary)
- **IRS Revenue Procedure 98–25:** Standards for e-signatures on charitable acknowledgments
- **IRS Form 8283:** Noncash charitable contributions (related, for goods-donated scenarios)
- **State laws:** A few states (e.g., NY, CA) have additional charitable solicitation rules; attorney should cross-check.

---

**Last updated:** 2026-06-10  
**Status:** Ready for attorney consultation  
**Next:** Provide to attorney; obtain written guidance on Daanaa's liability posture + suggested UI disclaimers.
