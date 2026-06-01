# Email → Agent Routing

How inbound mail to `@daanaa.org` addresses is received, routed to a department
agent, and answered — with the autonomy limits each address requires under the
Stewardship Commitment.

Status: **design** (not yet wired). Receiving layer (Google Groups) can be created
now; the agent layer sits on top of the single inbox once Gmail API access is enabled.

---

## Architecture

All nine role addresses are **Google Groups that forward into one mailbox**:
`hello@ecomargins.com`. There is **one** AI triage agent with **one** Gmail API
credential. It does not poll nine mailboxes — it reads the single inbox and routes
each message by its `To:`/`Delivered-To:` address to the right department logic.

Replies go out **as the original address** (e.g. `orgs@daanaa.org`, not
`hello@ecomargins.com`) via **send-as aliases** configured on the inbox.

```
nonprofit emails orgs@daanaa.org
  → Group forwards to hello@ecomargins.com (To: preserved)
    → triage agent reads inbox, sees To: orgs@
      → hands off to Nonprofit Success (dept 10) logic
        → drafts/sends reply AS orgs@daanaa.org
```

"Nine agents on the team" = nine **software roles** over one inbox, mapped to the
existing `departments/` structure — not nine mailboxes (that would be ~9× the seat
cost and credentials for no real gain at this stage).

---

## Routing table

| Address | Department | Agent role | Autonomy |
|---|---|---|---|
| `hello@` | 04-operations | Front desk | **High** — AI may reply (disclosed) |
| `orgs@` | 10-nonprofit-success | Nonprofit relations | **High** — AI may reply (disclosed) |
| `partners@` | 07-people-partnerships | Partnerships | **High** — AI may reply (disclosed) |
| `contact@` | 02-data-research | Crawler/webmaster contact | **High** — AI may reply (disclosed) |
| `trust@` | 02-data-research | Data-correction intake | **Medium** — AI acknowledges + logs; a human approves any score/data change |
| `verify@` | 10-nonprofit-success | Org verification | **Low** — AI triages + requests docs; a human approves the verification |
| `privacy@` | 06-legal-compliance | Privacy / data requests | **Low** — AI triages + drafts; a human sends |
| `legal@` | 06-legal-compliance | Legal / takedowns | **Low** — AI triages + drafts; a human sends |
| `security@` | 01-product-eng | Vulnerability disclosure | **Low** — AI triages + alerts a human; a human sends |

---

## Autonomy tiers

- **High** — AI may read, draft, and send the reply itself, with the AI-disclosure
  footer (below). For routine, low-stakes correspondence.
- **Medium** — AI may auto-send a *receipt/acknowledgement* and log the request, but
  any action that changes published data (a corrected score, a fixed field) is a
  "significant decision" and requires human approval before it ships.
- **Low** — AI may read, classify, summarize, and draft, but **must not send**. A
  human reviews and sends. For anything legal, security-sensitive, identity-sensitive,
  or privacy-regulated.

Why the split: takedowns and UGC liability (open launch gates **G1/G6/G7**), vuln
disclosure, identity claims (someone asserting control of an org), and CCPA/GDPR
requests all carry real-world consequence. AI drafts make them fast; humans own the
send so the decision is accountable.

---

## AI-disclosure footer

Per the Stewardship Commitment — every AI-generated mission, tag, and donate link on
the site is labeled, so AI-sent email is too. Any **High**-tier reply the AI sends on
its own appends:

> _This reply was drafted by Daanaa's AI assistant. A human reviews anything involving
> your data, legal, or verification. Reply and a person will pick it up._

**Low**-tier replies are human-sent and do not need the footer (a human is the author),
though they may note "AI-assisted triage" if a draft was used.

---

## Technical prerequisites (the real prep, not the Group dialog)

1. **Gmail API / OAuth on `hello@ecomargins.com`** — the single credential the triage
   agent uses to read and send. This is the actual gate; no agent can touch mail
   without it.
2. **Send-as aliases** for each `@daanaa.org` address on that inbox, so replies are
   *from* the role address.
3. **SPF + DKIM (and DMARC) for daanaa.org** — without these, agent-sent mail from the
   aliases lands in spam or is rejected. Verify before any outbound.
4. **Preserve `To:`/`Delivered-To:`** — the routing key. Google Groups keep it; don't
   strip headers in any forwarding rule.
5. **Audit log** — every AI-sent message recorded (address, classification, draft vs
   sent, human approver if any) for Stewardship traceability ("decisions explainable
   and traceable").

---

## Guardrails summary

- AI never auto-sends on `legal@`, `security@`, `privacy@`, `verify@`.
- AI never auto-changes published data from `trust@` — it logs and a human approves.
- Every autonomous AI reply is disclosed as AI.
- Donor privacy: agents never link an inbound email to anyone's giving activity; the
  giving wallet is device-only and not in this system at all.
- All AI actions are logged for audit.

---

## Open items

- [ ] Enable Gmail API access on the receiving inbox
- [ ] Configure send-as aliases + SPF/DKIM/DMARC for daanaa.org
- [ ] Build the triage/route agent (read → classify by `To:` → dept handoff)
- [ ] Wire the audit log
- [ ] Human-approval queue for Low/Medium-tier sends
