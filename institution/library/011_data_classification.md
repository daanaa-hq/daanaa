# DATA CLASSIFICATION AND THE ENTITY FIREWALL
Library Document 011 · Version 1.0 (Living Document)
Drafted 2026-07-13 under founder brief

## Why This Document Exists

Daanaa is operated by EcoMargins Consulting LLC, which also offers paid
consulting services under its own name, to businesses and, when asked, to
nonprofits. One company, two promises. Daanaa promises the organizations it
describes that it will never sell them anything and never take a cut of
anything. EcoMargins promises its clients honest professional work at a fair
price. Both promises are legitimate. They can only coexist if there is a
wall between what Daanaa is entrusted with and what EcoMargins may act on.

Document 005 classifies information by where it came from. This document
classifies it by what may be done with it, and by whom. Every piece of
information in our systems belongs to exactly one tier, and the tier answers
one question: may this ever be used to sell, prospect, or persuade?

## The Three Tiers

**Tier 0: Public record.** Information produced by public agencies and
public sources: the IRS Business Master File, Form 990 filings, ProPublica's
mirror of them, revocation lists, published websites. This covers the name,
EIN, address, finances, and category of every one of the 1.7 million
organizations Daanaa describes.

Tier 0 belongs to everyone. Daanaa did not create it and holds no special
claim over it. EcoMargins may analyze it, may build prospect research on it,
and may reach out to organizations identified through it, exactly as any
member of the public with a laptop could. The test for Tier 0 use is
simple: could a stranger with no relationship to Daanaa have done the same
analysis from public sources? If yes, it is fair use of public record. One
obligation travels with it: outreach built on Tier 0 data says so plainly,
so the recipient can verify that everything we know about them is public.

**Tier 1: Published derivations.** Information Daanaa computes and publishes:
peer financial context scores, percentiles, health signals, revenue bands,
archetypes, everything visible on a public organization page. Provenance
class six from Document 005, made public.

Tier 1 may be used by anyone, including EcoMargins, in the same way any
reader of daanaa.org could use it. The boundary is publication itself: if a
derivation is not on the public site, it is not Tier 1, and internal or
unpublished analytics may not quietly serve as a private commercial
advantage. What we publish for everyone, anyone may use. What we have not
published, no one may use for commerce, including us.

**Tier 2: Entrusted.** Information an organization or person gives to
Daanaa because Daanaa asked for their trust: claim contact emails and
phones, representative names and titles, custom missions and descriptions,
attestations, call notes, contact preferences, dashboard behavior, opt-ins
and opt-outs, wallet contents, waitlist emails, feedback. If someone typed
it into Daanaa, told it to Daanaa on a call, or generated it by using
Daanaa, it is Tier 2.

Tier 2 exists for exactly one purpose: operating Daanaa for the person who
entrusted it. It is never available to EcoMargins. It is never an input to
prospecting, lead scoring, marketing, or sales, for any entity, in any
direction. It never leaves for an external AI service; local inference
only, per the existing privacy invariants. It is exportable and deletable
by the person it belongs to. The claim data an organization gives Daanaa
is not a lead. It is a trust, in the oldest sense of the word.

## The Bright Line, Stated Once

The same fact can exist in two tiers, and the tier follows the source, not
the fact. An organization's email address scraped from its public website
is Tier 0. The same email address typed into a Daanaa claim form is Tier 2.
EcoMargins may contact the first. It may never derive the contact from the
second. When both exist, any commercial use must be traceable to the public
source alone, and where that tracing is doubtful, the use does not happen.

Behavioral signals are the sharpest edge of this line. That an organization
claimed its profile, viewed its dashboard five times, or read its peer
comparison is Tier 2, always. Platform behavior is never a sales signal.
An organization that engages deeply with Daanaa must never, for that
reason, hear from EcoMargins.

## The One Door

A nonprofit may ask for EcoMargins' help. That door exists, and it opens in
one direction only: the organization initiates, explicitly and in writing
or by an unambiguous opt-in control inside its own dashboard settings.
Daanaa never surfaces EcoMargins in its product: no banners, no
suggestions, no "you might benefit from consulting," no warm handoffs. An
opt-in, once given, covers one conversation, not a marketing relationship,
and can be withdrawn at any time. The absence of the opt-in is the default
and the norm.

## Enforcement

A wall that lives only in a policy document is a wish. This one is enforced
in three layers:

**In code.** Tier 2 lives today in identified tables and columns:
`org_claims` (all contact, attestation, and behavioral fields), `waitlist`,
wallet data, feedback, and call records. `scripts/privacy_check.sh` fails
any commit that references these stores from prospecting, outreach, or
EcoMargins-adjacent code paths, or that sends their contents to an external
AI service. New Tier 2 stores must be added to both this document and the
check before they ship.

**In accounting.** Daanaa and EcoMargins run as separate cost centers from
2026-07-13 forward, so that what each consumes and produces is separately
auditable, and so that a future transfer of Daanaa to its own legal entity
is a clean lift rather than surgery.

**In ritual.** Once per quarter, a written self-audit is added to the
compliance log in `STEWARDSHIP.md`, answering one question in plain
language: did any Tier 2 information influence any EcoMargins activity this
quarter? The honest answer, written down every quarter, is the cheapest
drift detector ever invented.

## Relationship to Other Governing Documents

This document elaborates Principles 2 and 7 of the Founding Stewardship
Commitment and Article III of the Stewardship Constitution. It extends,
and never weakens, `PRIVACY-INVARIANTS.md`; where the invariants are
stricter, the invariants govern. `VENDOR-POLICY.md` applies this
classification to outside vendors; this document applies it to ourselves,
which is where it is easiest to cheat and therefore where it must be
hardest.

When Daanaa becomes its own legal entity, Tier 2 data, the Daanaa brand,
and the platform code transfer with it, and this document travels as part
of the founding corpus.

## The Steward's Summary

Three questions, asked of every use of every fact:

1. Could a stranger have learned this from public sources? (Tier 0: free.)
2. Did we publish this for everyone? (Tier 1: usable as any reader could.)
3. Was this given to Daanaa in trust? (Tier 2: operate the platform for
   its owner, and nothing else, ever.)

What is cheap for us, public data, published analysis, tools, compute, we
give away. What is precious, the thin layer people entrust to us, we
protect absolutely. The entire model depends on never confusing the two.

The work continues.
