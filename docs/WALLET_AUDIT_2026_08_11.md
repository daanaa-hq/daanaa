# Wallet Privacy Story Audit (2026-08-11)

**Auditor:** Claude Code  
**Date:** 2026-08-11  
**Priority:** HIGH (P2 privacy principle, Codex finding)

---

## Summary: Contradiction Found

**PRIVACY-INVARIANTS.md says:** "Wallet data is stored server-side under the user's Google account via Firebase Auth"

**STEWARDSHIP.md says** (2026-06-27 QA correction): "Wallet remains device-first (no account required); Google sign-in is optional and enables cross-device backup only"

**Actual implementation** (WalletContext.tsx): localStorage-first with optional server sync

**Result:** PRIVACY-INVARIANTS.md is outdated by ~6 weeks

---

## Evidence: Actual Implementation

### Code Location: `frontend/src/contexts/WalletContext.tsx`

```typescript
// On mount: load from localStorage (device-first — survives page refresh with no auth)
const raw = localStorage.getItem('dw_entries')

// Save entries to localStorage on every change (device-first persistence)
localStorage.setItem('dw_entries', JSON.stringify(state.entries))

// Optional: request auth token for cross-device sync (if user signs in)
const tokenRes = await fetch(`${getApiBase()}/api/wallet/token`, {
  // This is optional; wallet works without this
})
```

**Clear:** localStorage is primary storage (device-first), no auth required for basic use

---

## Timeline: How Contradiction Occurred

| Date | Event | Source | Claim |
|------|-------|--------|-------|
| 2026-06-12 | Initial implementation note | STEWARDSHIP.md | Device-first + optional sign-in |
| 2026-06-14 | Updated implementation note | STEWARDSHIP.md | "Now requires a free Google account" |
| (Unknown) | PRIVACY-INVARIANTS.md written | PRIVACY-INVARIANTS.md | "stored server-side under Firebase Auth" |
| 2026-06-27 | **QA Correction** | STEWARDSHIP.md | "Product QA found wallet remains device-first. 2026-06-14 note overstated." |
| 2026-08-11 | **Audit** | This doc | Codex finding: docs contradict; implementation matches device-first |

**Codex:** "This is a policy mismatch at the exact place where P2 is supposed to be structural"

---

## What's True (Per QA + Code)

✅ **Wallet stores on device by default** (localStorage)  
✅ **No account required to use wallet** (can browse + bookmark without auth)  
✅ **Google sign-in is optional** (only for cross-device sync)  
✅ **Sync data is bookmarks + intent only** (never transactions, identity, or amounts)  
✅ **Wallet data never used for outreach/advertising** (structural privacy)  
✅ **Users can delete entire wallet** (locally and from sync)

---

## What Needs Fixing

**PRIVACY-INVARIANTS.md (Principle 2)** currently says:
```markdown
Wallet data... is stored server-side under the user's Google account via Firebase Auth.
```

**Should say** (to match implementation + STEWARDSHIP.md QA correction):
```markdown
Wallet data (bookmarks and giving intent) is stored on the user's device (localStorage)
by default. No account is required. Users may optionally sign in with Google to enable
cross-device wallet sync; synced data contains only bookmarks and intent, never
transactions or donor identity. Wallet data is never used for outreach, advertising,
or any secondary purpose.
```

---

## Recommendation

**Action:** Update PRIVACY-INVARIANTS.md Principle 2 to match:
1. Actual implementation (device-first localStorage)
2. STEWARDSHIP.md QA correction (2026-06-27)
3. Stewardship Principle 2 (privacy is structural, not optional auth)

**Impact:** P2 (Privacy) will move from "policy drift" to "structural enforcement"

**Risk:** None (this aligns policy with implementation, doesn't change product)
