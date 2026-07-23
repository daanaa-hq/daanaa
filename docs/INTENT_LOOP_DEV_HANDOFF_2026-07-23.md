# Daanaa shared intent loop: developer handoff

## Purpose

Connect giving, volunteering, learning, partnerships, claims, events, wallet
actions, and verified outcomes through one explainable workflow.

The first implementation is `intent_layer.py`. It is additive and stores only
anonymous workflow signals. It must not become a person or donor activity log.

## Contract

Each signal has:

- `kind`: `give`, `volunteer`, `learn`, `partner`, or `claim`
- `ein` or `event_id`
- `source`: the product surface that created it
- `stage`: `expressed`, `matched`, `action_started`, `verified`, `completed`, or `withdrawn`
- optional evidence describing the source, never a person's identity

The user's wallet remains separate and private. Do not add email, name, phone,
IP address, cookie, advertising identifier, or wallet contents to this table.

## Integration order

1. Event preview interest calls `record_intent(kind="volunteer", event_id=..., source="event_preview")`.
2. Existing organization interest remains aggregate and can be mapped to the same
   contract at the adapter boundary.
3. Confirmed signup transitions the event signal to `action_started`.
4. Approved volunteer hours transition the related signal to `verified` or
   `completed`.
5. Wallet saves and giving intent remain account scoped; only an explicit,
   anonymous aggregate signal may be projected to an organization dashboard.
6. Claimed nonprofits see counts and trends only, subject to a minimum threshold
   of five signals. Never expose a list of interested people.

## Automation gates

- Public source discovery may create only `unconfirmed` previews.
- AI may extract facts, but source URL, extraction date, and uncertainty remain visible.
- No automated outreach is sent. The system may prepare a draft for human review.
- No direct signup or hour verification opens until the nonprofit confirms or claims.
- Any source change creates a review task rather than silently rewriting history.

## QA acceptance

- Invalid kind, source, or target is rejected.
- No identity fields exist in `intent_signals`.
- Repeated signals do not expose individual activity.
- Summary returns counts only.
- Unconfirmed events accept interest but reject signup.
- Confirmed events accept signup and continue through the existing hour approval flow.
- `scripts/privacy_check.sh` remains green.
