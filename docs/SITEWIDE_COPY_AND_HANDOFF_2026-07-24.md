# Daanaa sitewide copy and connection handoff

Date: 2026-07-24
Status: Local, reversible review only. No deployment performed.

## Purpose

This pass gives Daanaa one clearer voice across its public pages. The site should feel like a careful guide: useful to donors and volunteers, respectful of small nonprofits, open about sources and limits, and honest about what is still unconfirmed.

The central message is simple: Daanaa makes giving of money, time, and knowledge easier to understand and easier to remember. It does not judge an organization, take a cut of generosity, or replace the nonprofit's own voice.

## Voice rules for future work

- Use short, direct sentences. Prefer ordinary words over product language.
- Say “public information,” “source,” “context,” “confirm,” and “your own words.”
- Keep IRS records, nonprofit supplied information, and AI assisted summaries visibly separate.
- Treat financial context as one limited measure, never a grade, verdict, endorsement, or proxy for mission quality.
- Mark public events as unconfirmed until the organization confirms them. Link back to the source and tell volunteers to confirm details.
- Keep AI disclosure factual and quiet: explain what was prepared with AI, what source it used, and how an organization can correct or replace it.
- Avoid inflated language such as “AI powered,” “frictionless,” “seamless,” “ecosystem,” “leverage,” and “raise your flame.”
- Minimize hyphens. Use a human sentence instead of stacking labels.

## Connected user journeys

| Person | Starting point | Next useful step | Handoff that must remain visible |
|---|---|---|---|
| Donor | Home or Directory | Review an organization page, its sources, and its own links | Financial context is not a rating; donations go directly to the organization |
| Volunteer | Volunteer | Open an event, follow the source, confirm with the organizer, then express interest or register | An unconfirmed event is a lead, not a promise; hours are recorded only through the event workflow |
| Nonprofit | Organization page or For nonprofits | Claim the page, correct public details, add its own story, and manage events | Claimed information remains separate from IRS data and AI assisted summaries |
| Researcher | Research or Methodology | Read definitions, limitations, source notes, and open data references | Research materials are working papers and do not speak for every organization |

## Work completed locally

- Reworded the shared navigation and trust handoff to “How it works” and “Continue exploring Daanaa.”
- Made nonprofit page language invite organizations to add context rather than improve a score or visibility tier.
- Reframed the public financial comparison as a limited description of reserves, with explicit limits and no donor persuasion.
- Removed rank language from the nonprofit claim explanation and replaced it with peer financial context.
- Reworded volunteer event status so people can tell when a source has not been confirmed by the organization.
- Reworded the open data page so it serves people and automated tools without sounding like search engine marketing.
- Kept AI labels and source disclosures in place, while explaining them in plain language.
- Replaced repeated “seamless,” “frictionless,” and “raise your flame” language in the main public explanation pages.

## Files changed in this pass

- `frontend/src/components/Navigation.tsx`
- `frontend/src/components/TrustNav.tsx`
- `frontend/src/components/PeerContextBreakdown.tsx`
- `frontend/src/components/TierBreakdown.tsx`
- `frontend/src/pages/About.tsx`
- `frontend/src/pages/Approach.tsx`
- `frontend/src/pages/ForNonprofits.tsx`
- `frontend/src/pages/Home.tsx`
- `frontend/src/pages/Methodology2.tsx`
- `frontend/src/pages/OpenData.tsx`
- `frontend/src/pages/Principles.tsx`
- `frontend/src/pages/ResearchDashboard.tsx`
- `frontend/src/pages/VolunteerSearch.tsx`

## Developer acceptance checklist

1. Review the changed copy in the browser at `/`, `/about`, `/approach`, `/principles`, `/methodology`, `/for-nonprofits`, `/volunteer`, `/research`, and `/open-data`.
2. Confirm every financial context card includes a source and a limit, and does not imply organizational quality.
3. Confirm event cards show source, date, location, and confirmation status before a volunteer takes action.
4. Confirm the nonprofit flow links from a public page to claim, correction, own content, events, and the dashboard without dead ends.
5. Confirm AI assisted content is labeled and never presented as the nonprofit’s own words.
6. Confirm no public page asks for or exposes wallet contents, donation amounts, tax documents, or unrelated personal information.
7. Run `npm test -- --runInBand` and `npm run build` from `frontend/`.
8. Run the repository privacy check. Stage and deploy only after founder review and the team’s normal release approval.

## Known follow-up

This handoff is a content and connection pass, not a production release. The live event proxy issue previously observed on the droplet still requires the team to deploy the corrected upstream port configuration and then run production smoke tests. Do not treat local test results as production verification.

