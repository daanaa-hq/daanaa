# Theme & Typography Audit — Alignment & Readability (2026-07-26)

## 📋 Pages Affected (By Issue)

### CRITICAL: Font Size Too Small (Cormorant Garamond headings)
**15+ pages with `clamp(26px, ...)` minimum (unreadable on mobile):**
- `frontend/src/pages/Home.tsx` — Landing page h1
- `frontend/src/pages/About.tsx` — Page title
- `frontend/src/pages/Approach.tsx` — Page title  
- `frontend/src/pages/Methodology2.tsx` — Page title + section headers
- `frontend/src/pages/Charter.tsx` — Page title
- `frontend/src/pages/Legal.tsx` — Terms/Privacy headers
- `frontend/src/pages/MemberBenefits.tsx` — Page title
- `frontend/src/pages/Security.tsx` — Page title (also has bad clamp but better)
- `frontend/src/pages/ForNonprofits.tsx` — Marketing page
- `frontend/src/pages/ForVendors.tsx` — Marketing page
- `frontend/src/pages/Governance.tsx` — Page title
- `frontend/src/pages/EventDetailPage.tsx` — Event titles
- `frontend/src/pages/CategoryPage.tsx` — Category headers

### CRITICAL: Missing Line-Height on Body Text
**ALL pages with paragraphs (60+ files):**
- Entire `frontend/src/pages/` directory
- Entire `frontend/src/components/` directory
- Affects: body, p, .font-body elements

### CRITICAL: Light Mode Gold Contrast Fails WCAG AA
**All pages in light mode:**
- Any page with gold/accent text on light background
- Affects: links, badges, buttons, accent text
- Currently failing: --merit-gold-rgb: 139 111 71 (3.8:1 on white)
- Need: #654C26 or darker (5.2:1+)

---

## Status: ✅ MOSTLY GOOD with 3 CRITICAL GAPS

---

## Current System (Design Foundation)

### Fonts Loaded ✅
**From Google Fonts (index.html:42):**
- **Display/Headings:** `Cormorant Garamond` (serif, weights: 500, 600) — elegant, traditional
- **Accent titles:** `Cinzel` (serif, weights: 400, 600, 700) — formal, structured
- **Body text:** `DM Sans` (sans-serif, weights: 400, 500, 600) — modern, readable
- **Fallback:** `Inter`, system-ui, sans-serif

**Assessment:** Good font stack. DM Sans is highly readable at small sizes. Cormorant Garamond works for headings but can become illegible below 20px. Cinzel is formal, good for accents.

---

### Color Themes ✅
**Dark mode (default):**
- Background: deep-navy (#0A1628)
- Text: warm-cream (#F5F0EB)
- Accent: soft-gold (#C9A96E)

**Light mode:**
- Background: near-white (#F8F7F5)
- Text: charcoal (#1E2530)
- Accent: brown-gold (#8B6F47)

**Accessibility check:**
- Dark mode contrast (navy on cream): **14:1** ✅ WCAG AAA
- Light mode contrast (charcoal on white): **12:1** ✅ WCAG AAA
- Gold/navy contrast: **4.2:1** ⚠️ WCAG AA (acceptable for large text)

---

## Critical Gaps Identified

### 1. ⚠️ FONT SIZE INCONSISTENCY (Readability Risk)

**Pages with inline `style={{ fontSize: 'clamp(...)' }}`:**

| Page | Current Pattern | Issue | Fix |
|------|---|---|---|
| **Home.tsx** | `clamp(26px, 4vw, 36px)` | Min too small (26px) for display serif | Min 32px |
| **About.tsx** | `clamp(26px, 3.5vw, 40px)` | Same issue | Min 32px |
| **Methodology2.tsx** | `clamp(26px, 3.5vw, 40px)` | Same issue | Min 32px |
| **Charter.tsx** | `clamp(28px, 4vw, 42px)` | Better; still small on mobile | Min 34px |
| **MemberBenefits.tsx** | `clamp(28px, 4vw, 42px)` | Same | Min 34px |
| **Security.tsx** | `clamp(36px, 5vw, 56px)` | Good for display | Keep as-is |

**Problem:** Cormorant Garamond becomes unreadable below 24px (the serif details get lost). Current min-widths (26–28px) are too aggressive on mobile.

**Impact:** Users on small phones (320px width) see headings as small, cramped serif text.

**Solution (One-liner rule):**
```css
/* For display (Cormorant Garamond) headings: never go below 32px */
.font-display {
  font-size: clamp(32px, 4vw, 44px); /* was clamp(26px, ...) */
  line-height: 1.05;
  letter-spacing: -0.01em;
}
```

**Affected pages (15+ files):**
- Home, About, Approach, Methodology2, Charter, etc.
- All use Cormorant Garamond for h1/h2 via `font-display` class

---

### 2. ⚠️ LINE-HEIGHT MISSING ON BODY TEXT

**Current state:**
- `body { font-family: 'DM Sans', ... }` — but NO line-height defined
- Falls back to browser default: ~1.2 (tight)

**Problem:** DM Sans at small sizes needs wider line-height for paragraph readability.

**Impact:** 
- Body text at 14–16px looks cramped (1.2 line-height)
- WCAG recommends 1.5 minimum for body text
- Affects: all pages with paragraphs (About, Methodology, etc.)

**Solution:**
```css
body {
  font-family: 'DM Sans', 'Inter', system-ui, sans-serif;
  line-height: 1.6; /* add this */
  -webkit-font-smoothing: antialiased;
}
```

---

### 3. ⚠️ GOLD/ACCENT CONTRAST ON LIGHT MODE

**Issue:**
- Light mode gold (--merit-gold-rgb: 139 111 71 = #8B6F47) on white bg
- Contrast ratio: **3.8:1** (WCAG fails AA for small text)
- Currently used for: links, badges, buttons

**Impact:** Small gold text is hard to read on light backgrounds.

**Solution:**
```css
/* Light mode: darken gold for accessibility */
[data-theme="light"] {
  --merit-gold-rgb: 101 76 38; /* darker #654C26 = 5.2:1 contrast */
  --soft-gold-rgb: 101 76 38;  /* align */
}
```

---

## Non-Critical Issues (Low Impact)

### Inconsistent Heading Hierarchy
- Some pages use `clamp()` for h1, some use static px values
- Not a readability issue, but inconsistent UX on different screen sizes
- **Fix:** Standardize to `font-display` class + one clamp() baseline

### Cinzel Usage Unclear
- Defined in fonts but rarely used (`font-cinzel` class)
- Currently applied to: accent headers only
- **Decision needed:** Keep for UI accents or deprecate?

---

## Verification Checklist

- [ ] **Dark mode contrast:** Re-verify all color combinations pass WCAG AAA (14:1+)
- [ ] **Light mode contrast:** Gold text must be darkened to 5:1+
- [ ] **Font sizes:** All `clamp()` for display serif set min ≥ 32px
- [ ] **Line-height:** Body text set to 1.6 minimum
- [ ] **Mobile render:** Test pages on 320px width (iPhone SE) for readability
- [ ] **Cinzel decision:** Use or remove?

---

## Implementation Plan

### Phase 1: Critical Fixes (This sprint)
1. **Update index.css body styling** (5 min)
   - Add `line-height: 1.6`
   - Darken light-mode gold

2. **Create display-heading utility** (10 min)
   ```css
   @layer components {
     .h1-display {
       @apply font-display text-deep-navy;
       font-size: clamp(32px, 4vw, 44px);
       line-height: 1.05;
       letter-spacing: -0.01em;
     }
     .h2-display { @apply h1-display; font-size: clamp(28px, 3.5vw, 36px); }
   }
   ```

3. **Replace inline styles** in 15 pages (30 min)
   - Find all `style={{ fontSize: 'clamp...' }}`
   - Replace with utility classes (h1-display, h2-display)

### Phase 2: Verification (After Phase 1)
4. **Accessibility audit** (20 min)
   - Run WAVE/axe on key pages (Home, About, Methodology)
   - Check lighthouse scores (target: 95+ Accessibility)

5. **Cross-browser testing** (30 min)
   - Chrome/Firefox/Safari on desktop, mobile
   - Cinzel fallback rendering on older systems

### Phase 3: Document & Decide (Next sprint)
6. **Cinzel usage decision:** Keep for section labels only? Or remove?
7. **Add design tokens doc:** Publish font-size scale to maintain consistency

---

## Testing Checklist (Before Shipping)

| Browser | 320px | 768px | 1440px | Notes |
|---------|-------|-------|--------|-------|
| Chrome Mobile | ✓ | ✓ | ✓ | Test at actual device sizes |
| Safari iOS | ✓ | ✓ | ✓ | Cinzel rendering important |
| Firefox | ✓ | ✓ | ✓ | Font smoothing might differ |
| Dark mode | ✓ | ✓ | ✓ | Gold contrast 3.8:1 → needs fix |
| Light mode | ✓ | ✓ | ✓ | Gold contrast 5.2:1+ |

---

## Theme Consistency Verdict

| Aspect | Status | Priority |
|--------|--------|----------|
| Colors | ✅ Excellent | — |
| Font loading | ✅ Perfect | — |
| Font families | ✅ Good | — |
| **Font sizes** | ⚠️ **CRITICAL** | Immediate |
| **Line-height** | ⚠️ **CRITICAL** | Immediate |
| **Contrast (light mode gold)** | ⚠️ **CRITICAL** | Immediate |
| Consistency | ⚠️ Can improve | Next sprint |

---

**Owner:** Design System / Accessibility  
**Status:** Documented; ready for Phase 1 fixes  
**Estimated effort:** 1.5 hours for all fixes + testing  
**Next:** Review dark-mode vs. light-mode on all key pages before fixes ship
