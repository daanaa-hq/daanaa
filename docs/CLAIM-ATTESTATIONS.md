# Claim Attestations — Versioned Record

Every claim stored in `org_claims` carries an `attestation_version` and an
`attested_at` timestamp. This file is the canonical record of what each
version's text said, so any stored claim can be traced to the exact wording
the claimant agreed to. Never edit a published version — add a new one and
bump `CLAIM_ATTESTATION_VERSION` in `daanaa_api.py`.

The claim form also shows a plain-language disclosure ("Before you sign")
above the checkboxes. Its text is versioned here alongside the attestations
because the disclosure is part of what makes the consent informed.

---

## Version 2026-06-11.v1 (current)

### Disclosure shown above the checkboxes

> **Before you sign, here is who we are and what happens with this form.**
>
> Daanaa is a free public directory of nonprofits built from IRS records. We
> are not affiliated with the IRS or any government agency. We never handle
> donations and we never charge organizations for anything.
>
> We use your phone number and email only to verify that you represent this
> organization. A member of our team calls you, confirms your role, and gives
> you a PIN that unlocks your page. Neither is shown publicly.
>
> We keep a record of this submission, including the statements you check
> below and the time you checked them, so our verification process can stand
> up to review. Claiming a page gives you control over how this organization
> appears to donors, which is why we ask you to confirm the two statements
> below before submitting.

### Attestation 1 — authority

> I am an authorized representative of {organization name} and have the
> authority to manage its public presence on third-party platforms.

### Attestation 2 — legal weight

> I understand that submitting false or misleading information is a federal
> offense under 18 U.S.C. § 1001 and may result in permanent removal from
> Daanaa and referral to relevant authorities.

### What we store per claim

| Field | Why |
|---|---|
| `email`, `phone`, `rep_title` | Contact + role for the verification call. Never public. |
| `attested_at` | Timestamp of consent. |
| `attestation_version` | Pins the exact wording above. |
| `pin`, `pin_expires_at` | Verification credential, 30-day expiry. |
| `claim_status`, `revoked_at`, `revoke_reason` | Lifecycle + 45-day re-claim cooldown after revocation. |

### Enforcement

- Both attestations are required server side (`/api/claim/start` returns 400
  without them) — the form checkboxes alone are not the gate.
- A revoked claim blocks new claims on the same EIN for 45 days.
