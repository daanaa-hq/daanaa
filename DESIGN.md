---
name: Daanaa
description: Nonprofit discovery platform with evidence-based financial context and donor-first interaction.
colors:
  deep-navy: "rgb(10 22 40)"
  warm-cream: "rgb(245 240 235)"
  soft-gold: "rgb(201 169 110)"
  bright-gold: "rgb(212 184 122)"
  pale-gold: "rgb(232 213 163)"
  deep-gold: "rgb(200 165 95)"
  muted-cream: "rgb(212 204 191)"
  light-cream: "rgb(237 232 224)"
  light-grey: "rgb(229 224 219)"
  cool-grey: "rgb(160 175 195)"
  charcoal: "rgb(30 37 48)"
  slate: "rgb(75 85 99)"
  success-green: "rgb(74 222 128)"
  alert-amber: "rgb(245 158 11)"
  destructive: "rgb(239 68 68)"
  civic-teal: "rgb(26 74 74)"
  teal-light: "rgb(45 112 112)"
  # tier-beacon/lantern/flame/ember/spark: DORMANT. The lamp-tier visibility
  # system was retired from all public copy 2026-08-08, but these tokens are
  # still defined in index.css/tailwind.config.js and still consumed by
  # frontend/src/components/TrustBadge.tsx (TIER_COLORS/TIER_INK) and
  # LampMark.tsx (currently unrouted, dead code — see 2026-08-08 correction
  # in LESSONS.md). Kept here so this doc matches the actual codebase; do not
  # delete from index.css/tailwind without first removing the TrustBadge/
  # LampMark code that reads them.
typography:
  display:
    fontFamily: "Cormorant Garamond, Georgia, serif"
    fontSize: "clamp(2rem, 5vw, 3rem)"
    fontWeight: 300
    lineHeight: 1.15
    letterSpacing: "normal"
  headline:
    fontFamily: "Cormorant Garamond, Georgia, serif"
    fontSize: "clamp(1.5rem, 4vw, 2rem)"
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: "normal"
  title:
    fontFamily: "Cormorant Garamond, Georgia, serif"
    fontSize: "20px"
    fontWeight: 400
    lineHeight: 1.3
    letterSpacing: "normal"
  body:
    fontFamily: "DM Sans, Inter, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "normal"
  label:
    fontFamily: "DM Sans, Inter, system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.05em"
rounded:
  xs: "calc(var(--radius) - 6px)"
  sm: "calc(var(--radius) - 4px)"
  md: "calc(var(--radius) - 2px)"
  lg: "var(--radius)"
  xl: "calc(var(--radius) + 4px)"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  "2xl": "48px"
  "3xl": "64px"
components:
  button-primary:
    backgroundColor: "{colors.soft-gold}"
    textColor: "{colors.deep-navy}"
    rounded: "{rounded.sm}"
    padding: "10px 16px"
  button-secondary:
    backgroundColor: "{colors.warm-cream}"
    textColor: "{colors.deep-navy}"
    rounded: "{rounded.sm}"
    padding: "10px 16px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.cool-grey}"
    rounded: "{rounded.sm}"
    padding: "10px 16px"
  card-default:
    backgroundColor: "{colors.warm-cream}"
    textColor: "{colors.deep-navy}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  input-default:
    backgroundColor: "{colors.warm-cream}"
    textColor: "{colors.charcoal}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm}"
---

# Design System: Daanaa

## Overview

**Creative North Star: "The Trustworthy Directory"**

Daanaa is built on a commitment to specificity over vibes. Every design choice serves the mission: help donors make more informed and sincere giving decisions. The visual system reflects this through precise, evidence-based copy; a warm but authoritative palette (navy + cream + gold); and semantic, never-decorative component patterns.

The typography pairing of Cormorant Garamond (editorial serif for headings) and DM Sans (humanistic sans for body) signals care and intention without pretense. The navy establishes trust and professionalism; the cream adds warmth and approachability; the gold provides intentional accent without noise.

**Key Characteristics:**
- **Specificity over marketing vagueness** — Every copy line must be provable from data or user behavior
- **Respectful of all organizations** — Small community orgs treated with the same dignity as national foundations
- **Evidence-based trust signals** — No shame language; no unverified claims
- **Transparent about limitations** — Acknowledge gaps in data, methodology, and what users should verify directly
- **Accessible and semantic** — WCAG AA compliance is non-negotiable; all interactive elements earn their purpose

## Colors

The Daanaa palette conveys warmth, trust, and intentionality. Primary colors (navy, cream, gold) anchor the system; semantic colors (green, amber, red) support meaning without judgment.

### Primary

- **Deep Navy** (#0A1628 / `rgb(10 22 40)`): Trustworthy, established, not flashy. Primary background and text color. Never used for decorative elements.
- **Warm Cream** (#F5F0EB / `rgb(245 240 235)`): Inviting, human-centered. Card and container backgrounds. Chosen over sterile white to signal warmth and care.
- **Soft Gold** (#C9A96E / `rgb(201 169 110)`): Intentional accent. Used sparingly (≤10% of any screen). Primary button, highlight, and link color. Avoids the purple-gradient SaaS default aesthetic.

### Secondary

- **Bright Gold** (#D4B87A / `rgb(212 184 122)`): Hover/active state for primary gold elements. Lighter and more vibrant than soft gold.
- **Pale Gold** (#E8D5A3 / `rgb(232 213 163)`): Disabled or low-emphasis gold contexts. Maintains color family without distraction.
- **Deep Gold** (#C8A55F / `rgb(200 165 95)`): Deepened accent for high-contrast or dark-mode contexts.

### Tertiary

- **Civic Teal** (#1A4A4A / `rgb(26 74 74)`): Cause-specific secondary accent (e.g., environment, civic engagement). Used in badge variants and category indicators.
- **Teal Light** (#2D7070 / `rgb(45 112 112)`): Hover state for civic teal; maintains approachability.

### Neutral

- **Charcoal** (#1E2530 / `rgb(30 37 48)`): Text-heavy and technical content. Slightly warmer than pure black.
- **Slate** (#4B5563 / `rgb(75 85 99)`): Secondary text and borders. Maintains legibility without being as prominent as charcoal.
- **Cool Grey** (#A0AFC3 / `rgb(160 175 195)`): Tertiary text, disabled states, placeholder text. Always tested to 3:1 contrast minimum.
- **Light Grey** (#E5E0DB / `rgb(229 224 219)`): Subtle borders, dividers, and card shadows. Never used as background text color.
- **Muted Cream** (#D4CCBF / `rgb(212 204 191)`): Faded or secondary card backgrounds. Maintains warmth while receding from primary cream.
- **Light Cream** (#EDE8E0 / `rgb(237 232 224)`): Lightest background variant. Used for hover states on cream-background cards.

### Semantic

- **Success Green** (#4ADE80 / `rgb(74 222 128)`): Financial health is good. Peer percentile badges, positive validation messages. Never "success" as abstract concept — always tied to specific financial context.
- **Alert Amber** (#F59E0B / `rgb(245 158 11)`): Attention needed. Data is outdated, missing, or requires verification. Conveys caution, not alarm.
- **Destructive** (#EF4444 / `rgb(239 68 68)`): Truly destructive actions only (delete, revoke, irreversible state changes). Reserved for confirmation dialogs. Never used for passive warnings.

### Tier Colors (Financial Context) — DORMANT, not part of the live design language

The lamp-tier visibility system (Beacon/Torch/Candle/Spark) was retired from all
public copy 2026-08-08. These 5 colors remain defined only because
`frontend/src/components/TrustBadge.tsx` and `LampMark.tsx` (currently dead,
unrouted code — see LESSONS.md 2026-08-08) still reference them. Do not design
new UI against this palette; it is not live product language.

- **Beacon** (#B8902F / `rgb(184 144 47)`)
- **Lantern** (#C9A84C / `rgb(201 168 76)`)
- **Flame** (#D4B968 / `rgb(212 185 104)`)
- **Ember** (#D9A876 / `rgb(217 168 118)`)
- **Spark** (#E8C896 / `rgb(232 200 150)`)

### Named Rules

**The One Voice Rule:** Soft Gold (#C9A96E) is used on ≤10% of any given screen. Its rarity is the point — it should feel intentional, not defaulted.

**The No Shame Rule:** No color or copy pattern anywhere in the product may progress from "good" (green) to "bad" (red) framing. The v6 financial-context signals (Full Context/Regional Context/Broad Category/Archetype Only, and the HEALTHY/STABLE/NEED_SUPPORT health language) use neutral, supportive framing instead — every org is presented with equal dignity. (The retired tier system above followed this same rule in its own palette; the rule itself outlives that system.)

## Typography

**Display Font:** Cormorant Garamond (serif) with Georgia and generic serif fallbacks  
**Body Font:** DM Sans (sans-serif) with Inter, system-ui, and sans-serif fallbacks  
**Mono/Label:** DM Sans (same as body, with increased letter-spacing and optional uppercase)

**Character:** The serif–sans pairing conveys editorial intention. Cormorant Garamond signals sophistication and care; DM Sans (humanistic, not mechanistic) ensures body text remains warm and approachable. This intentional pairing differentiates Daanaa from SaaS templates that default to Inter or Roboto everywhere.

### Hierarchy

- **Display** (300 weight, `clamp(2rem, 5vw, 3rem)`, 1.15 line-height): Hero headlines and page-level identifiers. Serif, often italic. Reserved for one per page maximum.
- **Headline** (400 weight, `clamp(1.5rem, 4vw, 2rem)`, 1.2 line-height): Major section titles and org names. Serif, bold or regular depending on emphasis.
- **Title** (400 weight, 20px, 1.3 line-height): Card titles, subsection headings, secondary hierarchy. Serif in display contexts; body font in dense/compact UI.
- **Body** (400 weight, 14px, 1.65 line-height): Default reading copy, description text, body content. Max line length 65–75ch for readability. Use font-body class.
- **Label** (500 weight, 11px, 0.05em letter-spacing, optional uppercase): Eyebrow labels, tags, buttons, form field labels. Always visible; never hidden in placeholders.

### Named Rules

**The Serif-Is-For-Headings Rule:** Cormorant Garamond is used *only* for h1–h4 and major section headings. Never in body text or UI labels. The readability tax is too high; serif is decorative unless it's establishing hierarchy.

**The Line-Length Rule:** Body text paragraphs must not exceed 75ch. Narrow columns improve scannability and reading comfort. Test with prose-heavy pages (methodology, about, guides).

## Layout

Daanaa uses a **12-column responsive grid** (Tailwind default) with **mobile-first design**. Breakpoints are:

- **Mobile:** 375px (default, iPhone SE)
- **Tablet:** 768px (Tailwind `md`)
- **Desktop:** 1024px (Tailwind `lg`)
- **Wide:** 1440px (Tailwind `xl`, optional)

**Spacing Rhythm:**

- **Within sections (related items):** 8px, 12px, 16px gaps
- **Between sections:** 32px, 48px, 64px gaps
- **Card padding:** 24px (lg)
- **Input padding:** 8px–12px (sm–md)

**Containers:**

- Body has max-width of 1440px (desktop width), centered with margin-auto
- Pages with full-bleed sections (hero, footer) extend edge-to-edge; content inside respects padding
- Cards respect 24px padding internally and 16px–32px gaps between cards

**Touch Targets:**

All interactive elements (buttons, links, form controls, clickable areas) must be ≥44×44px. Minimum 8px gap between adjacent touch targets to prevent accidental taps.

**Density & Whitespace:**

Proximity signals relationship. Unrelated sections must have visible breathing room. If a page feels cramped, the problem is usually too much content competing for attention, not too much whitespace — add content hierarchy or separate into multiple pages rather than shrinking spacing.

### Named Rules

**The Mobile-First Rule:** Design for 375px first, then expand thoughtfully. Never just "stack desktop columns vertically" — rethink layout, typography sizing, touch targets, and hierarchy for the mobile context.

**The Proximity Rule:** Related items sit closer (8–16px). Distinct sections sit farther (32–48px). Use this spacing as a visual grammar of relationship.

## Elevation & Depth

Daanaa uses **soft shadows for depth**, not borders or tonal layering. The system is fundamentally flat (no glass morphism, no layered cards), with shadows applied only to interactive surfaces and floating containers.

### Shadow Vocabulary

- **Card Shadow** (`0 8px 30px rgba(10, 22, 40, 0.06)`): Ambient shadow on card elements at rest. Establishes light elevation without drama.
- **Card Hover** (`0 12px 40px rgba(10, 22, 40, 0.08)`): Increased shadow on hover. Subtle state change; not a dramatic lift.
- **Gold Glow** (`0 0 0 3px rgba(201, 169, 110, 0.15)`): Subtle glow around primary gold accents on hover/focus. Rarely used; reserved for high-emphasis interactions.
- **Green Glow** (`0 0 0 3px rgba(42, 107, 69, 0.20)`): Glow for success/validated states. Uses tighter chroma than gold to avoid obnoxiousness.

### Named Rules

**The Flat-By-Default Rule:** Surfaces are flat at rest. Shadows appear only as a response to interaction (hover, focus, elevation) or to establish container hierarchy (cards on white background). No decorative drop-shadows or layered blur effects.

## Shapes

**Border Radius:** Daanaa uses a **single CSS variable `--radius` (10px, or 0.625rem)**. Modifier utilities allow tighter radii for small components:

- `xl`: `--radius + 4px` = 14px (large containers, modals)
- `lg`: `--radius` = 10px (cards, buttons, inputs)
- `md`: `--radius - 2px` = 8px (chip variants, small modals)
- `sm`: `--radius - 4px` = 6px (tag corners, badge variants)
- `xs`: `--radius - 6px` = 4px (icon buttons, micro components)

**Corners:** All corners are *subtly rounded* — not sharp, not pill-shaped. The consistent radius prevents the system from feeling either sterile (square) or overly cute (pill-buttons). A radius of 10px feels intentional without asserting a brand "round" vs "square" position.

**Borders:** Borders are rare and always semantic — used for form field focus states, error boundaries, or container distinction. Never decorative. Border color follows from context (gold on focus, red on error).

**Form Language:** Buttons are rectangular with rounded corners; cards are square with rounded corners; modals are rectangular. No inconsistent shapes (circles, polygons, decorative cutouts). Consistency and simplicity earn the design's authority.

## Components

### Button

**Character:** Direct, confident, accessible. All buttons use semantic tokens; no raw utilities. Touch target ≥44×44px.

- **Primary:** Soft gold background (#C9A96E), deep navy text. Used for main actions and CTAs. Hover: bright gold (#D4B87A).
- **Secondary:** Warm cream background (#F5F0EB), deep navy text. Supporting actions and alternative paths.
- **Ghost:** Transparent background, cool grey text (#A0AFC3). Tertiary actions, low-emphasis options.
- **Destructive:** Red background (#EF4444), white text. Delete/revoke actions only, always with confirmation.
- **Sizes:** sm (12px, tight), md (14px, standard), lg (16px, spacious). All maintain 44px+ touch target.

### Card

**Character:** Unified container for related content. All cards use the Card component abstraction; no inline card styling.

- **Background:** Warm cream (#F5F0EB) by default; light cream (#EDE8E0) on hover.
- **Padding:** 24px (lg spacing token).
- **Shadow:** Card shadow by default; card-hover shadow on interactive hover.
- **Radius:** lg (10px).
- **Border:** None by default; gold border on focus or error (if interactive).
- **Sub-components:** CardHeader, CardTitle, CardContent, CardFooter. CardTitle inherits serif display font.

### Input / Form Field

**Character:** Clear, accessible, semantic. Labels always visible (never placeholder-only).

- **Background:** Warm cream (#F5F0EB).
- **Border:** Light grey (#E5E0DB) by default.
- **Padding:** 8–12px (sm–md spacing).
- **Focus:** Gold border (#C9A96E), gold ring (3px, 15% opacity), no outline shift.
- **Text color:** Charcoal (#1E2530).
- **Placeholder:** Cool grey (#A0AFC3) at 65% opacity.
- **Error:** Destructive red border (#EF4444), destructive text for error message.
- **Disabled:** 50% opacity, `cursor: not-allowed`.

### Heading

**Character:** Semantic hierarchy via the Heading component. Responsive scaling via `clamp()`.

- **h1–h3:** Serif display font (Cormorant Garamond), potentially italic for h1. Deep navy text.
- **h4–h5:** Serif display font, bold, not italic.
- **h6:** Body font (DM Sans), uppercase, wide letter-spacing (0.05em).
- **Responsive:** All use `clamp()` for fluid scaling across viewport widths.

### Navigation

**Character:** Primary navigation is top-fixed, always visible. Secondary navigation (breadcrumbs, tabs, pagination) is contextual.

- **Background:** Deep navy (#0A1628).
- **Text:** Warm cream (#F5F0EB) by default.
- **Active/Hover:** Soft gold text or underline (#C9A96E).
- **Height:** 72px (`--nav-height`).
- **Responsive:** Collapses to hamburger menu on tablet (768px and below).

### Badge / Chip

**Character:** Categorical or status indicators. Compact, scannable, never functional.

- **Shape:** Rounded corners (md or sm), small padding (4px–8px).
- **Color:** One per category (causes use generated cause palette; the v6 health signals use semantic tokens — success-green/alert-amber — never the dormant tier colors above).
- **Text:** Small font (11px label), uppercase optional.
- **Dark variant:** Used on gold/colored backgrounds for legibility.

## Do's and Don'ts

### Do:

- **Do** use semantic token names (`text-soft-gold`, `bg-success-green`) instead of raw Tailwind utilities.
- **Do** use component abstractions (Button, Card, Heading, Input) for all UI elements.
- **Do** test all interactive elements for ≥44×44px touch target and WCAG AA contrast (4.5:1 body text, 3:1 large text/UI).
- **Do** use Cormorant Garamond *only* for headings (h1–h5); never in body text.
- **Do** write specific, evidence-based copy ("Browse 1.7M nonprofits indexed from IRS records" vs. "Discover causes you care about").
- **Do** acknowledge data gaps and limitations ("This data is 12–24 months old per IRS filing timelines").
- **Do** respect all organization sizes equally — no size-based ranking or shame language.
- **Do** use proper icons (Lucide, Heroicons) instead of emoji in functional UI.
- **Do** keep gold accent use to ≤10% of any screen; if more gold is needed, the hierarchy may be unclear.

### Don't:

- **Don't** use raw Tailwind color utilities (bg-green-600, text-red-700). Use semantic tokens instead.
- **Don't** build custom button/card/heading styles. Use the component abstraction.
- **Don't** use emoji as UI iconography (❌ "🎯 Financial Health"). Use icon fonts or SVG.
- **Don't** center *all* headings, descriptions, and buttons. Left-align for scannability; center only hero sections.
- **Don't** add decorative elements (wavy dividers, floating blobs, ornamental shadows) unless the content itself is insufficient.
- **Don't** use shade.scss or custom color values. All colors come from index.css CSS variables or tailwind.config.js.
- **Don't** create new heading levels or font sizes outside the defined type scale. Use clamp() for responsive sizing within the scale.
- **Don't** hardcode hex colors in component style attributes. Always use semantic tokens or Tailwind class names.
- **Don't** ship unverified or experimental outputs as established fact. Mark uncertain guidance as "provisional" or route through review.
- **Don't** use shame language or negative framing ("Poor financial health", "Bottom-tier org"). Use neutral descriptors ("Lower peer-group percentile").
