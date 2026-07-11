# Library Steward Review — 2026-07-11

## Document Control

| Field | Value |
|---|---|
| Purpose | First full steward review of the institutional library and framework documents against the Steward's Charter (including Amendment 1). |
| Responsible role | Institutional steward (AI), under founder authority. |
| Authority level | Review and recommendation only; not approval. No document was rewritten. |
| Review trigger | Charter Amendment 1 (Institutional Self Review) upon completion of the first library corpus. |
| Method | Each document read in full and reviewed against Amendment 1's self-review questions: does it strengthen the mission, nonprofit capacity, stewardship, institutional resilience, public trust; is it still appropriate in fifty years; could it unintentionally create dependence or centralize power; what assumptions remain unchallenged; what questions remain unanswered. Cross-checked against root `STEWARDSHIP.md` and against each other. |
| Editable status | Generated review; corrections should be appended, not silently overwritten. |
| Classification of this review | Historical Record (a dated assessment of the corpus as it stood). |

Eleven documents reviewed: library 001, 002, 003, 004, 005, 006, 008, and the four framework documents `AI_GOVERNANCE.md`, `DEVELOPMENT_CONSTITUTION.md`, `RESEARCH_AGENDA.md`, `FUTURE_OF_GIVING.md`.

Verdict summary: no document needs wholesale revision. The corpus is unusually coherent for a first generation. The significant findings are not inside individual documents but between them: an unresolved precedence order among three constitution-tier documents, one genuine internal contradiction in 004, one gap between a stated obligation and current practice in AI governance, and the fact (detailed in the companion memory review) that this entire library currently exists on one disk, untracked by version control.

---

## 001_foundation.md — Daanaa Foundation

**Classification:** Institutional Principle.
**Verdict:** Sound.

The founding statement: mission, beliefs, the three responsibilities, the definition of success. Received from the founder rather than drafted, which gives it a different standing from the rest of the library — it is the document the others elaborate.

**Against the charter questions.** Strengthens mission and stewardship directly. Fifty-year appropriate: yes — it names no technology, no vendor, no current implementation. No dependence or centralization risk in the text itself.

**Concerns.** None material. One observation for the record: 001 lists eleven forms of giving; nothing in the corpus yet says whether that list is illustrative or canonical. Documents downstream (006's eleven capacity dimensions) have begun to mirror its structure; if the list is illustrative, later stewards should feel free to say so.

**Open Questions it should have generated.**
- The Foundation says success is measured by whether "each generation leaves people and institutions more capable." Who performs that measurement, on what cadence, and what happens when the answer is no? The corpus never assigns this.

---

## 002_mission.md — Why Daanaa Exists

**Classification:** Institutional Principle (its opening sections on giving and on why nonprofits exist read as candidate Universal Principles, but they have not yet earned that class through the maturation process Amendment 1 defines — one generation's conviction is not yet repeated evidence).
**Verdict:** Sound.

**Against the charter questions.** The strongest hundred-year writing in the corpus. Makes the friction argument ("the generosity that was ready is never expressed") that becomes the backbone of everything else. Explicitly guards against centralization: "Daanaa does not replace the charitable sector and must never attempt to."

**Concerns.** "None of these barriers is anyone's fault" is generous and mostly true, but it is an assumption worth challenging per the charter: some barriers *are* someone's fault — tools deliberately priced for large institutions, ratings that penalize smallness by design. The document chooses charity of interpretation over diagnosis. That is a defensible tone choice for a founding text, but future research (the RESEARCH_AGENDA's "data-dark" question) may show some friction is structural and interested, and the institution should be free to say so plainly when the evidence exists.

**Open Questions it should have generated.**
- Is all friction bad? The institution deliberately *adds* friction in places (no urgency, no one-click pressure, fail-closed publishing). The corpus never distinguishes obstructive friction (fought) from protective friction (chosen). This distinction deserves a home. (Carried into draft 007.)

---

## 003_stewardship.md — The Daanaa Stewardship Constitution

**Classification:** Stewardship Principle.
**Verdict:** Sound-with-concerns. The concerns are about its position, not its content.

Thirteen articles, each defensible, all consistent in spirit with root `STEWARDSHIP.md`. Article XI's money boundary matches the repo-root principle #8 exactly. Article VIII (human dignity, "small is not lesser") matches principle #4. No article contradicts the signed commitment.

**Concern 1 — three constitutions, no precedence order.** The institution now has three constitution-tier documents: root `STEWARDSHIP.md` (eleven principles, signed, with a revision log and re-sign-off requirement), `institution/CONSTITUTION.md` (protected rules, "highest institutional authority below applicable law"), and this document (thirteen articles, "the moral and institutional operating system"). They are mutually compatible today, but nothing states which prevails when they diverge, which amendment process governs which, or whether 003 is an elaboration of `STEWARDSHIP.md` or a successor to it. Silent divergence between constitutional documents is exactly the drift 008 warns about. **This is a Constitutional Gap and an Open Question for the founder.** Two honest positions:
  - *Position A:* Root `STEWARDSHIP.md` remains supreme (it is signed and revision-logged); 003 and CONSTITUTION.md are elaborations that must trace every article to it, and say so in their headers.
  - *Position B:* 003 becomes the master constitution and `STEWARDSHIP.md` becomes its implementation covenant for contributors; this requires a formal, logged transition with re-sign-off under `STEWARDSHIP.md`'s own principle 11.
  Either works. Having neither, in writing, does not.

**Concern 2 — minimization versus preservation.** Article V: Daanaa "keeps [information] the shortest time it can." Document 005: "some information must outlive every system that holds it" and superseded data is "not deleted but archived." These are reconcilable — minimize *personal* data, preserve *institutional* record — but the boundary is never drawn, and a future steward could cite either document to justify opposite actions on the same dataset (for example, correction history that embeds a person's name). Open Question for the founder: where exactly is the line between data we minimize and record we preserve?

**Concern 3 — a live tension with the shipped product.** Article II and the "no ranking of human worth" spirit of Article VIII coexist uneasily with a directory whose default sort has, per the institution's own 2026-07-03 audit, been score-ordered. The library documents say "context, not verdict"; a default sort order is a quiet verdict. This is not a flaw in 003 — it is 003 doing its job by making the tension visible. It should be tracked to resolution rather than absorbed.

**Open Questions it should have generated.** Both concerns above, plus: what is the amendment procedure for this document specifically — who may propose, who must approve, and does the contributor re-sign-off rule apply?

---

## 004_ai_with_empathy.md — AI With Empathy

**Classification:** Operational Practice, resting on Research (the adoption-resistance synthesis). Not a principle document, and correctly does not claim to be.
**Verdict:** Sound-with-concerns — one internal contradiction that needs a founder ruling before the concierge service ships.

The opening correction ("AI does not have emotions") is exemplary charter writing: honesty before comfort, no false certainty. The five design principles are concrete and measurable.

**Concern 1 — an internal contradiction.** The Transparent principle states: "The person always knows when they are dealing with AI and when with a human." Forty lines later, describing concierge onboarding: "The AI is present but invisible; the experience is a helpful person on the phone." As written, these conflict. Two honest positions:
  - *Position A:* No conflict in substance — a human is genuinely on the phone; the AI only drafted the profile beforehand, and that drafting is disclosed (the profile is labeled AI-assisted until confirmed). "Invisible" describes the experience, not a concealment.
  - *Position B:* "Invisible" is the wrong aspiration to write down, whatever the mechanics. An institution whose constitution demands disclosure at the moment of interaction should not describe AI invisibility as a design virtue; the sentence will be read, in ten years, as permission.
  **Open Question for the founder:** does the concierge call open with an explicit sentence disclosing that the draft profile was AI-prepared? If yes, Position A holds and one sentence in 004 should be clarified. If no, the design conflicts with the document's own third principle and with AI_GOVERNANCE obligation 4.

**Concern 2 — source durability.** The research grounding is honest about its provenance (practitioner literature, reviewed July 2026), but it rests on live URLs. Per 005's own preservation rule ("formats that will open in fifty years"), cited sources should be archived locally or summarized with enough detail to survive link rot. As it stands, the evidentiary basis of a Living Document is one dead-link sweep from becoming unverifiable.

**Concern 3 — unverified metrics.** "We track, or plan to track" honestly signals that the measurable-outcomes section is partly aspiration. Fine — but per the charter, aspiration must not silently harden into claimed fact. A future revision should mark which measures are live.

**Open Questions it should have generated.** The disclosure question above; also — the champion strategy ("find the one person more comfortable with technology") is sensible, but what happens to organizations that have no champion? The document is silent on whether they are simply reached later, or reached differently.

---

## 005_information_stewardship.md — Information Stewardship

**Classification:** Stewardship Principle (an elaboration of 003 Article III, and says so).
**Verdict:** Sound.

The strongest technical-principles document in the corpus. The eight provenance classes map cleanly onto the live system (mission_source, AI-assisted badges, versioned attestations, score snapshots), which means it describes practice rather than aspiration — rare and valuable.

**Concerns.**
- "Every piece of information belongs to exactly one of eight classes" is slightly too strong: the document itself describes class transitions (AI-generated link graduating to Verified) and derived facts whose inputs span classes (a Calculated score built on Public Record inputs). The single-class rule works if it means *current* class with provenance chain retained; a one-sentence clarification in a future revision would remove the ambiguity. Minor.
- The preservation clause is the other side of the minimization tension flagged under 003 (see Concern 2 there). Not repeated here.
- Fifty-year test: passes well, with one irony noted for the record — the document declaring that memory must not live "in formats owned by companies that may not exist then" currently lives, itself, untracked on a single disk. See the companion memory review.

**Open Questions it should have generated.**
- Who arbitrates provenance-class disputes — when an organization insists a Public Record fact is wrong but the record stands? (The corrections path handles errors; it does not yet handle *disagreements with an authoritative source*.)
- What is the re-verification cadence for class 3, concretely? "Ages back toward needs re-verification" names the decay but not the clock.

---

## 006_nonprofit_first.md — A Framework for Capacity

**Classification:** Institutional Principle (the framework) containing several clearly-labeled Experiments (letter service, group purchasing, banking guidance).
**Verdict:** Sound-with-concerns.

The eleven-dimension framework is the most operationally useful document in the library, and its honesty about which services are concepts versus live is exactly right.

**Concerns.**
- **Dimension 10 (banking guidance) touches independence.** "Connect organizations with reputable options, the way a knowledgeable friend would" — the moment Daanaa names reputable financial vendors, it creates the influence surface that 003 Article XII and root principle 7 exist to protect. VENDOR-POLICY.md (2026-06-14) covers vendor relationships generally; whether it covers *referrals* — where no money changes hands but reputational endorsement does — is not established in this corpus. Open Question for the founder: may Daanaa name specific vendors at all, or only describe categories and criteria?
- **Two measurement vocabularies now exist.** 006 defines eleven capacity dimensions, each with a measure; charter Amendment 1 commissions seven capacity-transfer measures. They overlap heavily but are not the same list, and nothing maps one onto the other. Left unreconciled, the institution will report capacity two incompatible ways within a year. Addressed in the capacity-transfer proposal filed alongside this review; the reconciliation itself is a founder decision.
- **Dependence check (charter question).** The document measures capacity *added* but not capacity *retained after Daanaa steps back* — the difference between a crutch and a strengthened leg. The capacity-transfer proposal exists to close exactly this gap; 006 should eventually cite it.

**Open Questions it should have generated.** The referral question; the measurement reconciliation; and whether "administrative hours returned" can be measured honestly at all without surveying organizations — which itself costs them time.

---

## 008_institution_over_company.md — Institution Over Company

**Classification:** Institutional Principle.
**Verdict:** Sound-with-concerns — one factual overstatement.

The fixed/flexible layering, the memory-as-habit argument, and "never delegate the checking of the delegate to the delegate" are keepers; the last is a candidate Emerging Principle in its own right.

**Concerns.**
- **"None of it is theoretical: every mechanism described here already exists at Daanaa in early form."** Mostly true, but overstated on the one mechanism this document cares most about: institutional memory preservation. At the time of writing, the library containing this sentence is untracked by version control, absent from backup scope, and exists on one disk (companion memory review, same date). The sentence should survive — as soon as it is true. Until then it is the kind of confident claim Article II warns against.
- The succession test ("could the successor continue without a single conversation with the departed?") is excellent and should be run, not just stated. No document schedules it. Open Question: who runs the succession fire-drill, and how often?

**Open Questions it should have generated.** The fire-drill; also — the document praises AI-enforced documentation discipline, but does not ask what happens when the AI vendor, model, or memory format changes. (Amendment 1 asks it; the companion memory review answers what can be answered today.)

---

## AI_GOVERNANCE.md — AI Governance at Daanaa

**Classification:** Institutional Principle (a governance framework elaborating 003 Article IV).
**Verdict:** Sound-with-concerns — one gap between stated obligation and current practice.

The purpose-over-compliance framing is genuinely strong: obligations that scale with capability rather than rules that obsolesce. Fail-closed by design accurately describes the live pipelines.

**Concern — Obligation 2 as written does not match practice.** "Every AI-drafted communication, record change, or public-facing output is confirmed by a human before it touches public records." Current practice, per root `STEWARDSHIP.md` principle 10 and the live pipelines: AI-generated missions and AI-discovered donation links are *batch-reviewed* and published with AI-assisted labels *before* any per-item human confirmation; per-item confirmation happens later, if the organization claims its record. Backend deploys ship autonomously under smoke-test-plus-rollback. Two honest positions:
  - *Position A:* Obligation 2 states the standard for *communications and record changes about specific organizations*, and labeled, batch-reviewed, fail-closed publication satisfies it — the label *is* the honesty, and the obligation should be reworded to say "confirmed by a human, or explicitly labeled as awaiting confirmation."
  - *Position B:* Obligation 2 means what it says, current practice falls short, and the institution should either tighten practice or amend the document in the open — but not live with a governance document that overstates its own guarantees, which is precisely the trust-spending Article II forbids.
  **Open Question for the founder.** Either resolution is honorable; the unresolved state is not, because this is the document an auditor would read first.
- Minor: "no system runs orphaned; ownership is recorded" — with a single founder, every system has the same owner, which satisfies the letter while embodying the single-point-of-failure the charter asks about. Noted, not fixable by writing.

**Open Questions it should have generated.** The obligation-2 boundary; also — who audits the auditor? The framework assigns humans to oversee AI but never assigns anyone to periodically review whether the nine obligations are being met. (The charter's own self-review duty partially fills this; it should be cited.)

---

## DEVELOPMENT_CONSTITUTION.md — The Development Constitution

**Classification:** Engineering (constitutional-register guidance for engineering practice; deliberately below the principle layer, and says so).
**Verdict:** Sound.

The precedence order (stewardship → privacy → mission → users → elegance) is the most practically useful paragraph in the framework set. "Confidence you have not earned is a form of dishonesty, and here it is also a bug" is exact.

**Concerns.**
- "A single Flask file and a SQLite database... is a deliberate choice" — true and well-argued today, but this is a Temporary Decision wearing constitutional clothing. The charter warns: never elevate temporary decisions into constitutional guidance. The *principle* underneath (one steward should be able to hold the whole system in their head) is durable; the *instrument* (Flask, SQLite) is not. A future revision should separate them so that the eventual replacement of the instrument does not read as a constitutional breach.
- The document defines its own conflict-resolution order while `institution/CONSTITUTION.md` defines a different conflict rule ("follow the narrower stewardship protection"). They are compatible in outcome but a third precedence statement adds to the Constitutional Gap logged under 003.

**Open Questions it should have generated.** When the codebase outgrows one head — more services, more stewards — what replaces "hold the whole system in one head" as the simplicity test?

---

## RESEARCH_AGENDA.md — The Research Agenda

**Classification:** Future Research (correctly, almost by definition), governed by stated Institutional Principles.
**Verdict:** Sound.

The three commitments (ecosystem first, evidence honestly stated, privacy inviolable) are exactly the right governors, and the annual review clause keeps a twenty-year document alive. "Behavioral science of sincere giving" — studying interventions donors reflectively endorse rather than extraction — is the agenda's most original contribution and genuinely under-studied.

**Concerns.**
- Capacity check (charter question): the agenda studies the sector but only lightly commits to *transferring* research capacity to it. Commitment 1 promises open publication; dimension 9 of 006 promises citable ground. Together they nearly close the loop. A future revision could state that datasets and methods are published in forms small organizations can actually use, not only in forms scholars can.
- "1.7 million organizations" and the archetype vocabulary date the document. Acceptable in a Living Document with annual review; noted so the first annual review refreshes them.

**Open Questions it should have generated.** Who funds twenty years of research without acquiring influence over it? Article XII forbids funder influence; the agenda never says how research is paid for. This is a real question, not rhetoric — research independence usually fails at the funding step.

---

## FUTURE_OF_GIVING.md — The Future of Giving

**Classification:** Institutional Principle, containing four candidate Universal Principles (people will give; need will exist; trust is earned continuously; compassion is human) that should enter the Emerging Principle pipeline rather than being declared universal by one generation.
**Verdict:** Sound.

The refusal to predict is the document's integrity. "Point technology at friction, not at persuasion" and "point technology at the clerical, not the moral" are the two sentences most likely to still be quoted in fifty years. The closing letter earns its register.

**Concerns.**
- "The measure of success is invisibility: the technology recedes" — harmonizes with 004's concierge language and inherits the same tension flagged there: invisible infrastructure must never mean undisclosed AI. One clause distinguishing *unobtrusive* from *undisclosed* would immunize the sentence.
- The four "will not change" claims are asserted, not evidenced. For this document's genre that is acceptable — but per Amendment 1 they should be formally logged as Emerging Principles so the maturation process, not the eloquence, confers their status.

**Open Questions it should have generated.** If the institution one day faces evidence that one of its "will not change" claims is wrong — say, a future in which trust *can* be durably stored — what is the procedure for amending a document addressed to 2126?

---

## Cross-Document Findings

**Constitutional Gaps (per Amendment 1, reported for prioritization):**
1. **No precedence order among constitution-tier documents.** Root `STEWARDSHIP.md`, `institution/CONSTITUTION.md`, and library 003 coexist without a stated hierarchy or unified amendment process. Three conflict-resolution rules now exist (003's implicit supremacy, CONSTITUTION.md's "narrower protection," DEVELOPMENT_CONSTITUTION's five-step order). Compatible today; divergence would be silent. *Founder decision required.*
2. **The library itself is unpreserved.** The corpus articulating fifty-year memory obligations is untracked in git, outside backup scope, on one disk. (Full analysis and smallest-first fixes in `institution/reviews/2026-07-11_institutional_memory_review.md`.) *Founder decision required (repo tracking).*
3. **Measurement without a steward.** 001 defines generational success, 006 defines eleven measures, Amendment 1 defines seven; no document assigns who measures, reconciles, or reports. Responsibility without measurement is on the charter's own gap list.

**Open Questions for the founder (consolidated):**
- Precedence and amendment process for the three constitution-tier documents (003).
- Personal-data minimization versus institutional-record preservation: where is the line? (003/005.)
- Concierge disclosure: is AI drafting disclosed at the start of the call? (004; also touches FUTURE_OF_GIVING's "invisibility.")
- AI_GOVERNANCE Obligation 2: tighten practice or amend the obligation, in the open.
- Vendor referrals under dimension 10: names, or only categories and criteria? (006.)
- Reconcile 006's eleven dimensions with Amendment 1's seven capacity measures (proposal filed).
- The default-sort tension: does a score-ordered default directory sort constitute the ranking the principles disclaim? (Known from the 2026-07-03 audit; restated here because the library now makes the tension constitutional, not just cosmetic.)
- Research funding without research influence (RESEARCH_AGENDA).

**What the corpus does well, for the record:** consistent voice; honest labeling of aspiration versus practice in most places; genuine falsifiability in several documents; no growth language, no hype, no shame framing anywhere in eleven documents. The first generation's library is worth preserving — which is, fittingly, its most urgent open item.

The work continues.
