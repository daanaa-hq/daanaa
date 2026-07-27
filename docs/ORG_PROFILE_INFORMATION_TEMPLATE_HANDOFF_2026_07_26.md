# Daanaa Organization Profile Information Template

**Audience:** Product, frontend, backend, data, and QA teams  
**Status:** Founder-directed product specification; local-only handoff  
**Scope:** Public organization pages, claimed organization pages, missing-data behavior, and expandable profile sections  
**Stewardship basis:** STEWARDSHIP principles 3, 4, 5, 6, 9, and 10; Daanaa Charter commitments 7 and 8; `PRIVACY-INVARIANTS.md`

## 1. Product intention

An organization page should help a person understand who an organization is, what it does, and how they can support it. It must not turn incomplete public information into a negative judgment.

The page should make three distinctions clear:

1. What is known from public records or the organization itself.
2. What is inferred from similar organizations.
3. What Daanaa does not currently know.

The absence of information is not evidence of poor work, poor governance, or low impact.

## 2. Shared page structure

Every organization receives the same page structure. Sections become visible when supported information exists; they do not become negative empty boxes when information is missing.

### A. Identity header

Always show the strongest available identity facts:

- Official organization name
- City and state, when available
- EIN, formatted consistently
- Broad cause or NTEE category, when available
- IRS or registry status, when supported by the source
- Claimed or unclaimed status
- Last verified or updated date

The header should not show a score, rank, or quality grade. A claimed badge means the organization has control of its page. It is not an endorsement by Daanaa.

### B. Mission and purpose

Show the mission before financial context.

Each mission must carry a provenance label:

- Organization-provided
- IRS filing
- Organization website
- Public category record
- AI-assisted summary from identified public sources

If the mission is AI-assisted, provide a short “How this was prepared” disclosure and a correction path. Do not present an inferred mission as the organization’s own words.

### C. Ways to support

Use one consistent section with three possible paths:

- Give funds: link to the organization’s own giving path when verified
- Give time: volunteer link or current opportunity when available
- Give knowledge: website, contact, introduction, or learning link when available

Daanaa remains a handoff. It must not imply that money passes through Daanaa, and it must not collect donor transactions.

### D. Organization context

Show only supported information such as:

- Service area
- Programs or activities
- Population served
- Public contact information
- Volunteer opportunities
- Organization-provided updates
- Public impact information, only when sourced

Do not create impact claims from a cause tag, organization name, or generic AI inference.

### E. Financial context

Use the title **Financial context**, not “financial health,” “rating,” or “performance.”

Separate the display into two clearly labeled modes:

**Direct organization information**

> Based on this organization’s public filing or information it provided.

Show the value, filing year, source, and what the measure means.

**Peer context**

> Typical information from similar organizations. This is not a statement about this organization’s actual finances.

Show the peer definition, peer count, metric availability, source years, interval or uncertainty, and methodology link. Never show a peer median as if it belonged to the organization.

If no reliable financial context exists, say:

> Financial information was not available in the public sources reviewed. This is not a judgment about the organization.

### F. Evidence and correction

Every page should end its factual sections with:

- Sources
- Data dates
- AI disclosure where applicable
- “Suggest a correction” link
- “Is this your organization?” claim link

Corrections must not require a donor account. Organization-submitted information must be labeled separately from public data.

## 3. Three information states

The layout stays consistent, but the content density changes.

### State 1: Broad information available

Use when the page has several supported sources and current information.

Show:

- Identity and mission
- Ways to support
- Service area and programs
- Organization or public contact path
- Direct financial context when available
- Peer context only as a separate, optional explanation
- Volunteer events
- Leadership or governance information with filing year and source
- Financial history in an expandable section
- Sources, correction, claim, and AI disclosure

Do not put every available field in the first view. The first screen should answer: who are they, what do they do, and how can I help?

### State 2: Limited information

Use when the page has identity and some public information but lacks mission, contact, financial, or program detail.

Show:

- Identity facts that are verified
- Any available cause, location, website, or service area
- Available ways to support
- A compact neutral message:

> We found limited public information for this organization. That does not indicate its quality or impact. The organization can add more information when ready.

Offer two actions:

- View the public sources
- Claim or suggest a correction

Do not show empty financial cards, zero-valued metrics, empty program lists, or a weak-looking score area.

### State 3: Little or no information

Use when only a registry identity record is available.

Show a calm identity card containing:

- Official name
- EIN
- State or location, if available
- Tax or registry status, if verified
- Cause category, if available
- Source and date

Use this message:

> This page currently contains only basic public registry information. We do not have enough evidence to describe the organization’s work or finances. That is not a judgment about the organization.

Then show:

- Claim this page
- Suggest a correction
- View the official public record

Do not invent a mission, financial context, programs, leadership, impact, or contact information. Do not display a placeholder score or a row of empty cards.

## 4. Missing values and zero values

Missing, zero, false, and not applicable are different states. The frontend must not collapse them into one value.

### Display rules

- `NULL`, empty string, whitespace, missing JSON key, or unavailable source: do not display as a value.
- A computed zero with no evidence: treat as unknown and do not display.
- A zero explicitly reported in an official filing or claimed by the organization: it may be displayed with its source and date.
- A negative value that is genuinely reported: display it neutrally with the source and explanation; do not hide it or turn it into a warning grade.
- Empty arrays: hide the section.
- Boolean `false`: show only when the source explicitly records a meaningful negative; otherwise omit the field.
- Placeholder values such as `0`, `-1`, `999`, `unknown`, `N/A`, or `not available` must never appear as if they were real measurements.

### Required data contract

Each displayable field should carry, where applicable:

```ts
type ProfileValue<T> = {
  value: T
  source: 'irs' | 'nccs' | 'website' | 'organization' | 'daanaa_inference'
  sourceUrl?: string
  sourceDate?: string
  taxYear?: number
  confidence?: 'high' | 'good' | 'moderate'
  isInferred?: boolean
}
```

The UI should render a value only when its provenance permits display. The UI must not decide that a raw zero is meaningful without evidence from the backend.

## 5. Expandable information spaces

The public page should use expandable sections, but empty spaces should not be visible by default.

### Public page behavior

Show a collapsed section only when it contains at least one supported field. Good examples:

- Financial history
- Leadership and governance
- Programs and service area
- Volunteer opportunities
- Public records and sources
- Methodology and peer context

If a section has no data, do not show a disabled accordion or a collection of empty fields. Use one compact “Information not available yet” message only where it helps explain the page.

### Claimed page behavior

After an organization claims its page, show a private completion workspace containing the full template:

- Mission
- Short description
- Programs
- Service area
- Volunteer contact path
- Website and giving links
- Public contact information
- Impact or outcome information
- Leadership and governance information
- Corrections to public data

The workspace may show empty fields because it is an editing tool. Empty fields must remain private until the organization saves them and chooses to publish them.

Each field should say:

- Why Daanaa asks for it
- Whether it is optional
- Who can see it
- What source or verification is expected

The claim flow must not request tax documents, donor lists, wallet contents, income details, or unnecessary personal information. Authentication and verification should be handled through the existing claim controls.

### Publish controls

For each claimed field, provide:

- Save privately
- Publish to page
- Remove from page
- View public preview

Organization-provided information should be marked **Provided by the organization**. It should not be blended into IRS data or AI inference.

## 6. Recommended page order

The public page should follow this order:

1. Identity and mission
2. Give funds, time, or knowledge
3. What the organization does and whom it serves
4. Current volunteer opportunities
5. Financial context, if supported
6. Leadership and governance, if supported
7. Financial history and deeper records, collapsed by default
8. Sources, corrections, claim, and methodology

Similar organizations, donor voice, broad research, and engagement features should remain below the core profile or be excluded from print and share previews.

## 7. Language rules

Prefer:

- “Information available in public records”
- “Context from similar organizations”
- “Not reported in the sources reviewed”
- “Provided by the organization”
- “We do not know enough to say”
- “This is a starting point for learning more”

Avoid:

- “Low quality”
- “Weak organization”
- “Failed”
- “Poor transparency”
- “Little financial safety net”
- “Unverified organization” when the issue is only missing information
- “Healthy” or “unhealthy” when the evidence is peer-derived
- “Score” or “rank” in donor-facing language

## 8. Acceptance tests

### Complete profile

- Supported sections render with sources and dates.
- Inferred context is visibly separate from direct data.
- No score or rank implies organizational worth.
- Long sections can be collapsed.

### Limited profile

- The page remains useful and visually complete.
- Missing fields do not appear as zeros or empty cards.
- A neutral limitation message is shown.
- Claim and correction paths remain visible.

### Sparse profile

- Only verified identity facts appear.
- No AI-generated mission or financial claim appears without evidence.
- No placeholder score, zero metrics, or misleading badge appears.
- Official source and claim links work.

### Claimed profile

- The organization sees all optional fields in its private workspace.
- Unpublished fields are not exposed publicly.
- Published fields are labeled organization-provided.
- The organization can preview, publish, edit, and remove its additions.
- No wallet, donor, volunteer, or unrelated private information is exposed.

## 9. Recommended implementation sequence

1. Normalize backend values into explicit `unknown`, `reported_zero`, `reported_value`, `inferred_value`, and `not_applicable` states.
2. Remove frontend hardcoded financial values and derive display values only from sourced API fields.
3. Create a shared profile-section component that renders populated sections and hides empty sections.
4. Build the claimed-page completion template using the same section definitions as the public page.
5. Add preview and field-level publish controls.
6. Add tests for nulls, zeros, placeholders, inferred values, claimed values, and source labels.
7. Run privacy and stewardship checks before staging.

The governing design decision is simple: every organization receives the same dignity and the same opportunity to be understood. More data creates more detail, not more respect; less data creates more humility, not less respect.
