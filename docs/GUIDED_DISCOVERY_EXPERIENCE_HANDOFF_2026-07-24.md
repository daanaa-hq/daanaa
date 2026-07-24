# Guided Discovery Experience

## Developer handoff

Date: 2026-07-24
Status: Product and UX specification. Local only. No deployment approved.

## Product decision

Keep `/directory` as the full search and research tool. Add `/discover` as a guided path for people who care about a cause but do not yet know which words, filters, or organizations to search for.

The guided experience should produce a short list of 20 to 25 organizations to explore. It must feel like a helpful introduction, not a ranking, contest, or donation funnel.

The first version should use existing directory filters and search APIs. Do not introduce an opaque recommendation model, user profiling, paid placement, or a new financial score.

## Home page placement

Place this immediately below the existing search bar:

**Search by name, cause, city, or ZIP code**

`[Search the directory]`

**Not sure where to begin?**

Answer a few simple questions to find a short list of organizations to explore.

`[Start guided discovery]`

Supporting text:

> Your answers help narrow the directory. Daanaa does not rank organizations or tell you where to give. Each result is a starting point for your own review.

The direct search and guided path must have equal visual dignity. Do not make the guided path look like an upsell or a correction for people who prefer search.

## Guided flow

### Step 1: purpose

Heading: **What brings you here?**

Subheading: **You can choose more than one.**

Choices:

- Give money
- Give time
- Share knowledge or skills
- Learn about organizations in a community
- Find organizations working on related problems

Store these as temporary session intent only. They should influence which fields are emphasized, not create a public or private donor profile.

### Step 2: cause

Heading: **What matters to you?**

Subheading: **Choose one or more areas. You can change this later.**

Use the existing Daanaa cause taxonomy and plain language labels. Show a manageable first group of familiar choices, with `See more causes` for the full taxonomy.

Do not imply that a cause is more important because it is displayed first. Use a neutral, stable order or a clearly labeled “popular starting points” section.

### Step 3: place

Heading: **Where would you like to look?**

Choices:

- Near me
- A city or ZIP code
- Anywhere in the United States
- A specific state

Use the existing location search and proximity behavior. Do not require precise location access. If the user chooses `Near me`, ask for browser permission only after an explicit click and explain why it is needed.

### Step 4: connection

Heading: **What kind of connection would help?**

Choices:

- A place to volunteer
- A direct giving or organization website link
- A smaller, community-rooted organization
- An organization with recent public filings
- A broad mix so I can discover something new

These are discovery preferences, not quality claims. “Smaller” must not become a hidden penalty or a reason to exclude larger organizations unless the user explicitly selects it.

### Step 5: review

Heading: **Here is a starting list to explore**

Subheading:

> We used your answers to narrow the public directory. We did not rank these organizations by worth or tell you where to give.

Show 20 to 25 organizations. Each card must include:

- Organization name
- City and state
- Plain cause label
- Whether a website, giving path, or volunteer information is available
- Data freshness or filing year where relevant
- A source or “Read the source” link when available
- A short “Why it is here” explanation tied to the user’s choices
- A clear `View organization` action

Example explanation:

> Included because you selected Houston, education, and volunteering.

Do not use `Top match`, `Best choice`, `Recommended for you`, `Financially best`, or similar language.

## Result composition

Use a transparent, deterministic shortlist builder:

1. Apply explicit cause and location filters first.
2. Apply explicit connection filters only when the underlying field exists.
3. Prefer records that satisfy more selected criteria.
4. Preserve a small discovery mix when the user selected “broad mix.”
5. Include smaller organizations when requested, without describing them as better.
6. Fill the list to 20 when possible. If fewer than 20 qualify, say so plainly and offer `Broaden the search`.
7. Never silently broaden a user’s location or cause selection.
8. Never use payment, wallet contents, private information, or undisclosed behavior to order the list.

Recommended display groups:

- **Close to what you selected**
- **A few nearby possibilities**
- **Something you may not have considered**

Only show a group if the explanation is true from available data. These are presentation groups, not quality tiers.

## Return behavior

The experience should invite healthy return visits through usefulness and fresh perspective, not pressure.

After a user views a result, offer:

- `Show another list`
- `Change my answers`
- `Browse the full directory`
- `Save this organization` only if the existing wallet flow is intentionally selected
- `Start over`

When `Show another list` is selected, preserve the user’s criteria and vary only the order or discovery mix. Do not show the same organizations repeatedly in the same session.

For future visits, do not persist answers by default. If a user is signed in and explicitly chooses to save a discovery list, explain what is saved and allow deletion. Do not infer sensitive interests from browsing behavior.

## Human and behavioral design principles

- Give the user a clear first step and visible progress, such as `2 of 4`.
- Keep each screen focused on one decision.
- Allow back, skip, edit, and start over at every point.
- Use plain language and concrete examples.
- Avoid urgency, countdowns, guilt, or emotional pressure.
- Do not celebrate a donation before the user has made one.
- Let people discover unfamiliar organizations without hiding the reason they appeared.
- Make the list useful even when the user does not sign in, donate, volunteer, or share contact information.
- Use empty states as invitations to broaden the search, never as blame.

## Exact empty and edge state copy

No results:

> We did not find organizations matching all of those choices. Nothing is wrong. Try a broader place, another cause, or remove one preference.

Fewer than 20:

> We found {count} organizations that fit these choices. You can review these or broaden the search for more possibilities.

Unconfirmed public information:

> Some information comes from public records or public organization pages and may not be current. Check the organization’s own website before making plans.

No website:

> No website was found in the public information we reviewed. The organization may still have an active presence elsewhere.

No volunteer information:

> We did not find a volunteer opportunity in the information available to Daanaa. You may wish to contact the organization directly.

## Accessibility requirements

- Every question and choice must have a visible label.
- Choice cards must work with keyboard, screen readers, and touch.
- Selected state must not depend on color alone.
- Progress must be announced to assistive technology.
- Focus must move to the new question after Continue.
- Back and Start over must preserve predictable focus.
- Do not rely on emoji alone to communicate a cause.
- Ensure the shortlist works at 375px width without horizontal scrolling.
- Respect reduced-motion preferences.

## Suggested component structure

Create:

- `frontend/src/pages/GuidedDiscovery.tsx`
- `frontend/src/components/discovery/DiscoveryProgress.tsx`
- `frontend/src/components/discovery/DiscoveryQuestion.tsx`
- `frontend/src/components/discovery/DiscoveryChoice.tsx`
- `frontend/src/components/discovery/DiscoveryResults.tsx`
- `frontend/src/components/discovery/DiscoveryWhyHere.tsx`
- `frontend/src/lib/discovery.ts`

Add a lazy route:

```tsx
const GuidedDiscovery = lazy(() => import('./pages/GuidedDiscovery'))
<Route path="/discover" element={<GuidedDiscovery />} />
```

Add the home page link beneath the main `SearchBar` and keep the directory link visible.

Use URL state where practical so a result list can be shared without including personal information. Example:

```text
/discover?cause=education,housing&place=houston-tx&intent=volunteer&mix=broad
```

Do not place email addresses, Firebase IDs, wallet data, or raw behavioral histories in the URL.

## Analytics and learning loop

Track only anonymous product events needed to improve the flow:

- discovery_started
- question_completed with question name, not free text
- result_list_shown with result count
- result_opened
- criteria_changed
- another_list_requested
- discovery_completed
- discovery_abandoned at step number

Do not log free-form answers, email addresses, IP addresses, wallet contents, donation amounts, or organization judgments. Keep analytics aggregate and apply the existing privacy threshold before showing nonprofit-facing counts.

Measure:

- Completion rate
- Time to first organization opened
- Number of organizations opened per session
- Use of Change answers and Show another list
- Zero-result rate
- Return visits to `/discover`
- Whether users reach a source or official organization link

Do not optimize only for clicks. A longer review, a source visit, or a user changing criteria may indicate a healthier discovery experience than a quick click.

## QA acceptance criteria

1. Home page shows Search the directory and Start guided discovery as separate paths.
2. A user can complete the flow without signing in or sharing contact information.
3. A user can go backward, skip optional questions, change answers, and start over.
4. The flow returns no more than 25 initial organizations and never calls them best or recommended.
5. Each result explains why it appeared using only selected criteria and available public fields.
6. Cause and location choices map correctly to existing directory filters.
7. Zero-result and fewer-than-20 states work without silent broadening.
8. Show another list changes the discovery mix without changing selected criteria.
9. Financial context is not used as a hidden ranking signal.
10. No paid placement, wallet data, private data, or contact information affects results.
11. AI is not required for the first version. If later introduced, it must explain its source, uncertainty, and role, and must not invent a reason for inclusion.
12. Keyboard, mobile, reduced-motion, and screen-reader checks pass.
13. Existing `/directory`, organization pages, wallet, and volunteer flows remain unchanged.
14. Frontend tests and build pass.

## Why this pattern fits Daanaa

Netflix’s own explanation of recommendations emphasizes rows, metadata, and interaction signals to make a large catalog easier to approach. Daanaa should borrow the manageable presentation, not the opaque personalization. Spotify’s recommendation controls offer the complementary lesson: people should be able to steer, skip, and reset what they see.

Daanaa’s version should remain explicit, source-linked, reversible, and respectful of user agency. The goal is not to keep someone scrolling. The goal is to help someone find a meaningful place to begin, understand it, and return when they are ready to explore again.

References:

- Netflix Help Center, “How Netflix’s Recommendations System Works”: https://help.netflix.com/en/node/100639
- Spotify Safety and Privacy Centre, “Understanding recommendations”: https://www.spotify.com/uk/safetyandprivacy/understanding-recommendations/plain

