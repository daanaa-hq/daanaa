# Daanaa Platform Governance Charter

**Status: DRAFT — requires review by qualified legal counsel before adoption.**

This Charter translates the Founding Stewardship Commitment (`STEWARDSHIP.md`) into
binding operating rules for the Daanaa platform. It is a governance instrument for how
the platform is run, not a substitute for the EcoMargins Consulting LLC Operating
Agreement (`operating-agreement-ecomargins-llc.md`), which governs the legal entity.
Where this Charter and the Operating Agreement overlap, the Operating Agreement controls
on matters of corporate law; this Charter controls on matters of platform conduct.

## Article I — Entity and Scope

1.1 Daanaa is a brand and operating name of **EcoMargins Consulting LLC**, a for-profit
limited liability company. Daanaa is not a 501(c)(3) charity, not a nonprofit, and is
not affiliated with the IRS or any government agency.

1.2 This Charter binds every person and system operating on behalf of the platform:
members, employees, contractors, volunteers, advisors, vendors, and all automation and
AI agents, consistent with `STEWARDSHIP.md`.

## Article II — Binding Principles

2.1 The eleven principles in `STEWARDSHIP.md` are incorporated by reference and are
binding operating rules, not aspirational statements.

2.2 No business objective — growth, partnership, automation efficiency, or revenue —
may override these principles (principle 1).

## Article III — Hard Prohibitions

The following are prohibited without exception. Each is a material breach of this Charter.

3.1 **No handling of donor funds.** The platform shall not receive, hold, escrow, or
process charitable gifts. All giving is a hand-off between the donor and the
organization (principle 8).

3.2 **No paid placement.** No organization may pay, or be pressured, to alter its score,
tier, ranking, visibility, or verification outcome (principles 1, 7).

3.3 **No donor surveillance or social pressure.** The platform shall not store donor
giving activity on its servers, expose personal giving publicly, or build social-
pressure or performance mechanics. Donor data minimization is mandatory (principle 2).
The enforceable specifics live in `PRIVACY-INVARIANTS.md`.

3.4 **No fabricated or unverified trust signals.** No badge, score, tag, mission text,
or link may be presented as established fact unless supported by reviewable data.
Machine-generated or auto-collected content must be labeled (for example, "beta")
(principles 3, 10).

3.5 **No silent weakening.** No principle or prohibition in this Charter may be diluted
without a documented, reasoned amendment under Article IX (principle 11).

## Article IV — Roles and Human Accountability

4.1 AI systems are tools. Accountability for any AI-assisted output remains with the
human operator who created, approved, or supervised it (principle 10).

4.2 Every significant automated output must be reviewable, challengeable, and subject to
correction. No system is treated as authoritative or beyond oversight.

## Article V — Data and Privacy Commitments

5.1 The platform operates under the invariants in `PRIVACY-INVARIANTS.md`, which are
incorporated by reference: no third-party trackers, giving data on-device only, no
persisted visitor IPs, strict CSP, no donor identity tied to giving, and minimal
labeled server PII.

5.2 The automated check `scripts/privacy_check.sh` must remain green. A failing check
blocks release.

## Article VI — Fairness to Small Organizations

6.1 Scoring compares organizations only within peer groups, never against the full
registry. Systems are reviewed for unintended bias toward scale, visibility, language,
geography, or institutional resources (principle 4).

6.2 An organization is never disadvantaged for being small, data-dark, or for not having
claimed its page. Claiming is free and never affects rank (principles 4, 7).

## Article VII — Corrections

7.1 Errors in data, logic, AI outputs, or presentation are corrected openly and
promptly. Accuracy takes priority over appearance (principle 6). A visible corrections
path is maintained on organization pages.

## Article VIII — Enforcement and Escalation

8.1 Any contributor or AI agent who believes a principle is being compromised must raise
it. Raising a good-faith concern is protected and expected (Stewardship Acknowledgment).

8.2 Suspected breaches are logged in the Compliance Log in `STEWARDSHIP.md`, reviewed by
a human operator, and resolved with a documented outcome.

## Article IX — Amendment

9.1 This Charter and the underlying principles may evolve, but only through a documented
amendment that states the change and the reasoning behind it, recorded in the Revision
Log of `STEWARDSHIP.md` (principle 11).

9.2 Material changes require explicit re-acknowledgment from active contributors before
taking effect.

## Article X — Review

10.1 This Charter is reviewed at least annually and before any public launch milestone,
and whenever the privacy invariants, scoring methodology, or revenue model materially
change.

## Adoption

| Name / Agent | Role | Date |
|---|---|---|
| Akbar Khowaja | Founder, EcoMargins Consulting LLC | _pending_ |

_This draft must be reviewed and adapted by qualified legal counsel before it is adopted
or represented as binding. It is provided as a starting point, not legal advice._
