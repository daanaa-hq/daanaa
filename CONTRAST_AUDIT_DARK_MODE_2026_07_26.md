# Contrast Audit — Dark Mode Visibility Issues (2026-07-26)

## 🔴 Critical Findings: Unreadable Text in Dark Mode

Testing all color combinations on dark navy background (#0A1628).

### DARK MODE FAILURES (Deep Navy bg)

| Color | Used For | Ratio | Status | Issue |
|-------|----------|-------|--------|-------|
| **Merit Navy** (#0D1C36) | ??? | 1.07:1 | ✗ FAIL | **Nearly invisible** |
| **Civic Teal** (#1A4A4A) | ??? | 1.83:1 | ✗ FAIL | **Nearly invisible** |
| **Cool Grey** (#37 65 81) | Secondary text? | 1.76:1 | ✗ FAIL | **Nearly invisible** |
| **Teal Light** (#2D7070) | ??? | 3.16:1 | ✗ FAIL | Below WCAG AA |
| **Deep Gold** (#8B7340) | ??? | 3.99:1 | ✗ FAIL | Below WCAG AA |

### DARK MODE PASSES (for reference)

| Color | Ratio | Status |
|-------|-------|--------|
| Warm Cream (primary text) | 16.01:1 | ✓ PASS |
| Merit Gold (accent) | 7.93:1 | ✓ PASS |
| Soft Gold | 8.10:1 | ✓ PASS |
| Muted Cream | 11.39:1 | ✓ PASS |
| Success Green | 10.40:1 | ✓ PASS |
| Alert Amber | 8.44:1 | ✓ PASS |

---

## 📍 Where Are These Used?

Need to search frontend code for:
1. `text-cool-grey` or `.cool-grey` — secondary text?
2. `text-civic-teal` or `.civic-teal` — used where?
3. `text-teal-light` or `.teal-light` — badges? accents?
4. `text-merit-navy` or `.merit-navy` — used where? (1.07:1 is nearly invisible!)
5. `text-deep-gold` or `.deep-gold` — alt gold text?

---

## Light Mode (✅ Fixed)

| Scenario | Old Ratio | New Ratio | Status |
|----------|-----------|-----------|--------|
| Light gold on light bg | 4.40:1 | 7.50:1 | ✓ Fixed |

---

## Next Steps

1. **Search** for usage of failing colors in component/page files
2. **Replace** with readable alternatives (Warm Cream, Muted Cream, or lighter shades)
3. **Test** on real pages to verify visibility
4. **Commit** fixes

**Impact:** Any text using these colors is currently unreadable in dark mode.
