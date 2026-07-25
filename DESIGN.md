# DESIGN.md — Daanaa Design System

**This is the single source of truth for Daanaa's visual identity and voice.**

Every design decision — copy, color, component, interaction — should be traceable back to these principles. If something doesn't align with this document, it doesn't belong on Daanaa.

---

## Core Principle: Specificity Over Vibes

Daanaa exists to help donors make more informed and sincere giving decisions. Every design choice should serve that purpose, not distract from it.

**Generic SaaS does:** "Welcome to Daanaa. Unlock the power of giving."  
**Daanaa does:** "A $40,000 food pantry gets the same care as a $40 million hospital foundation."

Specificity builds trust. Vague language erodes it.

---

## Voice: Four Non-Negotiables

### 1. Specific Over Generic
- ❌ "Discover causes you care about"
- ✅ "Browse 1.7M nonprofits indexed from IRS records"

- ❌ "Learn more"
- ✅ "Read the full methodology"

### 2. Evidence-Based Over Aspirational
- ❌ "Unlock the power of informed giving"
- ✅ "View public information with peer context, not a one-size-fits-all rating"

- ❌ "Join thousands of donors"
- ✅ "See where an organization's reserves stand relative to genuinely similar organizations"

Every claim should be provable from public IRS data or user behavior.

### 3. Respectful of All Orgs Over Praising Large Ones
- ❌ Sort by "most popular" or "highest rated"
- ✅ Sort by relevance, peer group, or financial health percentile

- ❌ "Discover high-impact nonprofits"
- ✅ "Find organizations working on causes you care about, benchmarked fairly against their peers"

Size is not a signal of impact. A community food bank serving 100 families is as dignified as a national foundation.

### 4. Transparent About What We Don't Know
- ❌ Hide uncertainty
- ✅ Acknowledge it

Example: "We show financial context from the most recent IRS filing. Nonprofit finances move fast — this data is 12-24 months old by the time it's published. For real-time spending decisions, contact the organization directly."

---

## Visual Identity

### Color Palette (CSS Custom Properties)

**Primary Colors** — Define Daanaa's warmth and trust:
- `--deep-navy-rgb: 10 22 40` — Deep, professional, trustworthy
- `--warm-cream-rgb: 245 240 235` — Inviting, human, not sterile white
- `--soft-gold-rgb: 201 169 110` — Intentional accent, not neon

**Semantic Colors** — Support meaning without shame:
- `--success-green-rgb: 74 222 128` — "Financial health is good"
- `--alert-amber-rgb: 245 158 11` — "Attention needed" (not alarm)
- `--destructive-rgb: 239 68 68` — Only for truly destructive actions

**Rationale:** The navy + cream + gold palette reflects Daanaa's identity:
- Navy: trustworthy, established, not flashy
- Cream: warm, human-centered, approachable
- Gold: intentional, not generic (avoids purple-gradient SaaS defaults)

This palette intentionally avoids the purple-indigo-gradient aesthetic that signals "AI-generated SaaS template." Daanaa is *not* that.

### Typography

**Display Font: Cormorant Garamond (serif)**
- Use for: H1, H2, page headings, section titles
- Why serif: Signals sophistication, care, intention. Serif typefaces carry editorial weight; they say "someone *designed* this, not templated it."
- Never: Use serif for body text or UI labels (readability tax)

**Body Font: DM Sans (sans-serif)**
- Use for: Body text, UI labels, buttons, form fields, navigation
- Fallback chain: DM Sans → Inter → system-ui (never default to system-ui alone)
- Why DM Sans: Warm, humanistic sans-serif. Not as generic as Inter or Open Sans. Feels designed, not auto-selected.

**Font Scale** (in `tailwind.config.js`):
```
H1: 32-48px, 1.15 line-height (display font)
H2: 24-28px, 1.2 line-height (display font)
H3: 18-20px, 1.3 line-height (display font)
Body: 16px, 1.65 line-height (body font)
Small: 14px, 1.5 line-height (labels, captions)
Tiny: 12px, 1.4 line-height (meta text only)
```

### Visual Hierarchy

**Rule: Proximity = Relationship**
- Related items sit closer together (8-16px gap)
- Distinct sections sit farther apart (32-48px gap)
- Unrelated items must be visually grouped (cards, sections, containers)

**Rule: Importance = Prominence**
- Primary action: largest, most saturated color, 44px+ touch target
- Secondary action: smaller, lower contrast, same touch target size
- Tertiary action: text link only, same color as body copy
- Destructive action: appears only with confirmation

**Rule: Everything Earns Its Pixels**
- No decorative elements (wavy dividers, floating blobs, gradient backgrounds)
- No empty white space without purpose
- No large imagery without context or narrative
- If a section feels empty, the problem is content, not decoration

### Spacing & Layout

**Grid:** 12-column responsive grid at all breakpoints (Tailwind default)

**Breakpoints:**
- Mobile: 375px (default Tailwind sm)
- Tablet: 768px (Tailwind md)
- Desktop: 1024px (Tailwind lg)
- Wide: 1440px (Tailwind xl, optional)

**Spacing Scale (Tailwind defaults):**
- Gaps between sections: 32px, 48px, 64px
- Padding within sections: 16px, 24px, 32px
- Gaps between related items: 8px, 12px, 16px

**Touch Targets:** Minimum 44x44px for all interactive elements (buttons, links, form controls)

### Components

#### Button (ui/Button.tsx)
**Required abstraction.** No inline button styling — use the Button component.

```tsx
import { Button } from '@/components/ui/Button'

<Button variant="primary" size="md">Give Now</Button>
<Button variant="secondary" size="md">Learn More</Button>
<Button variant="outline" size="sm">Cancel</Button>
<Button variant="destructive" size="md">Delete</Button>
<Button variant="ghost" size="sm">Skip</Button>
```

**Variants:**
- `primary`: soft-gold background, deep-navy text (main actions)
- `secondary`: white border, deep-navy text (supporting actions)
- `outline`: soft-gold border, soft-gold text (tertiary actions)
- `destructive`: destructive background, white text (delete/remove)
- `ghost`: text-only, cool-grey text (low-emphasis actions)

**Sizes:** `sm` (12px, 8px height), `md` (14px, 10px height), `lg` (16px, 12px height)

**Rules:**
- All buttons use semantic tokens (no raw colors)
- All touch targets ≥44px (enforced by size classes)
- Hover state: opacity change (no color shift)
- Disabled state: opacity 50% + `cursor: not-allowed`
- Refactor inline button patterns to use this component

#### Card (ui/Card.tsx)
**Required abstraction.** No card styling outside the Card component family.

```tsx
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/Card'

<Card>
  <CardHeader>
    <CardTitle>Your Wallet</CardTitle>
  </CardHeader>
  <CardContent>
    ...
  </CardContent>
  <CardFooter>
    <Button>Continue</Button>
  </CardFooter>
</Card>
```

**Sub-components:**
- `CardHeader`: top section with title/description
- `CardTitle`: serif display heading (h3-sized)
- `CardContent`: main body content
- `CardFooter`: optional actions section

**Rules:**
- Use semantic colors (not raw Tailwind utilities)
- All cards use `shadow-card` (elevation via shadow, not borders)
- Padding: 6 (24px) on Card, adjust within sub-components
- Border-radius: uses CSS variable `var(--radius)`
- Merge duplicate card variants (AnswerCard, OrgCard, etc.) into this component

#### Heading (ui/Heading.tsx)
**Required abstraction.** All h1-h6 use the Heading component for consistent styling.

```tsx
import { Heading } from '@/components/ui/Heading'

<Heading level={1}>Browse nonprofits by impact</Heading>
<Heading level={2}>Your giving wallet</Heading>
<Heading level={3}>Peer comparison</Heading>
<Heading level={4 | 5 | 6}>Subheadings</Heading>
```

**Rules:**
- Level: 1-6, maps to H1-H6
- Responsive sizing: clamp() scales headings across viewports
- h1-h3: serif display font + italic styling (Daanaa signature)
- h4-h5: serif display font, bold, not italic
- h6: body font, uppercase, wide tracking (labels/captions)
- No manual font-size on headings
- All use deep-navy text by default (semantic, overridable via className)

#### Form Fields
**Planned abstraction.** Input, Select, Textarea need unified styling.

**Rules:**
- Label always visible (never use placeholder as label)
- Focus state: `focus:ring-2 focus:ring-soft-gold/40`
- Validation: error message near field + border-destructive
- Placeholder text: cool-grey, 65% opacity
- Input text color: charcoal (not warm-cream)
- All use semantic border colors (border-light-grey, border-soft-gold on focus)

---

## What NOT To Do (The Anti-Patterns)

### Emoji as Functional UI
- ❌ `<div className="text-5xl mb-6">✅</div>` (success checkmark)
- ❌ `<span>🎯 Financial Health</span>` (icon replacement)
- ❌ `<span>⭐ Rating</span>` (rating display)

**Why:** Emoji is decorative and casual. In product UI, it signals "hastily built" rather than "carefully designed." Use proper icons (Lucide, Heroicons) or remove.

**When emoji IS okay:** Chat messages, social features, celebratory moments (but even then, sparingly).

### Raw Tailwind Utilities for Colors
- ❌ `className="text-green-600 bg-amber-600 border-l-indigo-400"`

Use semantic tokens instead:
- ✅ `className="text-success-green bg-alert-amber border-l-soft-gold"`

**Why:** Raw utilities bypass the design system. They look scattered. They make the codebase hard to govern. They signal "I didn't know about the system" or "I chose speed over consistency."

### Generic SaaS Copy Patterns
- ❌ "Welcome to Daanaa"
- ❌ "Unlock the power of giving"
- ❌ "All-in-one nonprofit discovery"
- ❌ "Join thousands of donors discovering impact"

These phrases appear on 10,000 SaaS sites. They're invisible. Replace with Daanaa-specific copy that says what Daanaa actually does.

### Centered Everything
- ❌ Centering all headings, descriptions, and buttons in a grid

**Why:** Centered text is harder to scan. It only works for hero sections (one per page). Everywhere else, left-align for scannability.

### Decorative Elements
- ❌ Wavy SVG dividers between sections
- ❌ Floating blob shapes
- ❌ Gradient backgrounds behind text
- ❌ Ornamental shadows and glows (gold-glow should be rare, not default)

**Why:** Decoration is noise. If a section needs visual interest, the problem is content or composition, not decoration. Add decoration only after exhausting the content angle.

### Icon Circles (the SaaS Template Look)
- ❌ Icon inside a colored circle, repeated 3x in a grid

This is the most recognizable AI-generated SaaS pattern. Avoid.

### Hardcoded Hex Colors
- ❌ `style={{ color: '#7A5C2E' }}` or `className="text-[#7A5C2E]"`

Always use CSS variables or semantic Tailwind classes. Color values belong in config, not inline.

---

## Responsive Design

### Mobile-First Approach
- Design for 375px (iPhone SE) first
- Expand thoughtfully to tablet and desktop
- Don't just "stack desktop columns vertically" — rethink the layout for mobile context

### Touch Targets
- Minimum 44x44px for all clickable elements
- Spacing: 8px minimum between touch targets

### Performance as Design
- LCP < 2s (content load time affects perceived professionalism)
- CLS < 0.1 (layout shifts make the site feel buggy)
- Skeleton screens for loading states (must match actual content shape)
- Images: lazy loading, proper dimensions, WebP/AVIF format

---

## Accessibility (Non-Negotiable)

### WCAG AA Compliance
- Body text: 4.5:1 contrast ratio minimum
- Large text (18px+): 3:1 contrast ratio minimum
- UI components: 3:1 contrast ratio minimum

### Semantic HTML
- Use `<button>` for buttons (not `<div role="button">`)
- Use `<a>` for navigation (not `<span onClick>`)
- Use `<label>` for form fields (never placeholder-only)
- Use `<h1>...<h6>` for headings (in hierarchical order)

### Keyboard Navigation
- All interactive elements accessible via Tab
- `focus-visible` ring always present (never `outline: none` without replacement)
- Modals trap focus until closed

### Color Isn't Meaning
- Never use color alone to encode information (red for error, green for success)
- Always pair with text, icons, or patterns

---

## Decision Log

This section records *why* design choices were made, so future updates can change with confidence.

### Decision: Serif Display Font (Cormorant Garamond)
- **Date:** 2026-07-25
- **Why:** Differentiate from SaaS defaults (system-ui, Inter, Roboto). Serif signals editorial care and sophistication. Matches the principle-driven voice.
- **Alternative considered:** Staying with sans-serif everywhere (lower maintenance, more modern). Rejected because it made Daanaa feel generic.

### Decision: Navy + Cream + Gold Palette
- **Date:** 2026-07-25
- **Why:** Warm, trustworthy, intentional. Avoids the purple-gradient aesthetic that signals "AI-generated SaaS template."
- **Alternative considered:** Cooler blue tones (more "tech-modern"). Rejected because they felt sterile and didn't match Daanaa's warmth.

### Decision: No Emoji in Functional UI
- **Date:** 2026-07-25
- **Why:** Emoji is decorative and casual. In product UI, it signals "hastily built" rather than "carefully designed." Daanaa's value is clarity and intentionality; every pixel should reflect that.
- **Alternative considered:** Emoji as quick iconography (faster than building icon library). Rejected because speed over consistency is the opposite of Daanaa's values.

### Decision: Component Abstraction (Button, Card, Heading)
- **Date:** 2026-07-25
- **Why:** Scattered inline styling is invisible to the design system. Component abstractions make it impossible to use raw utilities by accident; they enforce semantic tokens and consistency.
- **Alternative considered:** Leave styling inline (maximum flexibility). Rejected because flexibility without guardrails leads to sprawl and inconsistency.

---

## How to Use This Document

### For Designers
- This is your north star. Every mockup should align with these principles.
- When in doubt, ask: "Does this align with Daanaa's commitment to specificity and respect?" If no, redesign.

### For Developers
- Use semantic tokens (`text-soft-gold`, `bg-success-green`) instead of raw Tailwind utilities.
- Use component abstractions (`<Button>`, `<Card>`, `<Heading>`) instead of inline className.
- If something doesn't have a component yet, add it before using inline styles.
- When you see emoji in functional UI or raw utilities in components, refactor it. Don't ship it.

### For Product Managers
- Copy matters. Every heading, label, and button text should be specific and evidence-based.
- "Welcome to Daanaa" is not good enough. Say what Daanaa does or what the user can do here.
- If copy feels like it could fit 10 other SaaS products, rewrite it to be Daanaa-specific.

### For PMs & Designers
- Review copy together. Does it sound like the About section? If not, it needs work.
- Does the design align with the visual system? If not, it's not ready to ship.

---

## Enforcement (ESLint + Code Review)

### Automated Rules
These will be enforced by ESLint linting as soon as the rules are configured:

```bash
# Future setup:
npm install --save-dev @typescript-eslint/eslint-plugin eslint-plugin-tailwindcss

# Rules to enable:
- no-restricted-classname: Disallow raw utility patterns like bg-green-600, text-red-700, border-l-indigo-400
  → Use semantic tokens instead (bg-success-green, text-destructive, border-l-soft-gold)

- button-must-use-component: Disallow <button className="...px-4 py-2...">
  → Use <Button variant="primary" size="md">

- card-must-use-component: Disallow div+card styling patterns
  → Use <Card><CardHeader>...<CardTitle>...</CardTitle>...</CardHeader></Card>

- heading-must-use-component: Disallow <h1 className="...text-4xl...">
  → Use <Heading level={1}>
```

### Code Review Checklist
When reviewing PRs, flag:
- ❌ Raw Tailwind color utilities (bg-green-600, text-red-700, etc.)
- ❌ Inline button styling (className="px-4 py-2 rounded...") — use Button
- ❌ Inline card styling — use Card components
- ❌ Inline heading styling — use Heading
- ❌ Emoji in functional UI (except chat/social contexts)
- ❌ Generic SaaS copy ("Welcome to", "Unlock the power", etc.)

Request: Use component abstractions; if component doesn't exist yet, extract it first.

---

## Staying Intentional

**The risk:** As the product grows, design decisions scatter. Someone uses a raw utility. Someone adds emoji. Someone copies generic SaaS copy. By the time anyone notices, it's everywhere.

**The antidote:** This document + component libraries + linting rules. A shared commitment to specificity, evidence, and respect. Every designer and developer has the right — and responsibility — to call out misalignment. "This doesn't sound like Daanaa" or "This uses raw utilities instead of semantic tokens" is a *compliment*, not a critique.

**The test:** In 6 months, would someone new to Daanaa know this was designed intentionally? Or would it feel like it was built fast by an AI? If the latter, we've drifted. Time to re-read this document and refocus.

---

## Implementation Timeline

**Done (2026-07-25):**
- ✅ DESIGN.md published — voice principles + visual system codified
- ✅ Emoji removed from functional UI (17 instances)
- ✅ Semantic color tokens deployed (259 → 100 distinct colors)
- ✅ Button, Card, Heading components created (primitives in place)

**Next (by 2026-08-01):**
- [ ] Refactor 40+ inline button patterns → `<Button>` component
- [ ] Consolidate 7 card variants → unified `<Card>` component
- [ ] ESLint rules configured (no raw utilities, require components)
- [ ] Form field component abstraction

**Ongoing:**
- Code review: enforce component usage + semantic tokens
- Monitor for emoji creep, generic copy, color sprawl
- Quarterly DESIGN.md review (principles adjust as product evolves)

---

**Last updated:** 2026-07-25  
**Maintained by:** Design + Engineering  
**Questions?** Check the Decision Log above, then propose an update.
