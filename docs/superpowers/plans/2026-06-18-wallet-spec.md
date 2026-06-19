# Daanaa Giving Wallet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a world-class, intuitive wallet UI where donors save nonprofits they're considering + signal giving intent, with seamless persistence across devices.

**Architecture:** 
- Device-first (localStorage) with optional cloud sync via Google OAuth
- React context manages wallet state; persistence layer handles localStorage + optional server backup
- UI prioritizes clarity: nonprofit cards show mission, cause, location, health signal; donors understand at a glance what they've saved and why
- Minimal, elegant design—no clutter, no dark patterns

**Tech Stack:** React 19, TypeScript, Tailwind CSS, localStorage, optional PostgreSQL (wallet_data table), Google OAuth

---

## File Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Wallet/
│   │   │   ├── WalletPage.tsx          (main page container)
│   │   │   ├── WalletCard.tsx          (nonprofit card in wallet)
│   │   │   ├── WalletFilters.tsx       (filter/sort controls)
│   │   │   ├── WalletEmptyState.tsx    (when wallet is empty)
│   │   │   └── IntentSignal.tsx        (giving intent selector)
│   │   ├── Shared/
│   │   │   ├── AddToWalletButton.tsx   (add nonprofit to wallet)
│   │   │   └── WalletBadge.tsx         (showing org is in wallet)
│   ├── contexts/
│   │   └── WalletContext.tsx           (state management)
│   ├── hooks/
│   │   ├── useWallet.ts                (read/write wallet data)
│   │   ├── useWalletPersistence.ts     (localStorage sync)
│   │   └── useWalletSync.ts            (optional: server sync)
│   ├── types/
│   │   └── wallet.ts                   (TypeScript types)
│   └── utils/
│       └── walletStorage.ts            (localStorage layer)
├── __tests__/
│   ├── Wallet/
│   │   ├── WalletPage.test.tsx
│   │   ├── WalletCard.test.tsx
│   │   └── IntentSignal.test.tsx
│   └── utils/
│       └── walletStorage.test.ts
```

---

## Data Structure

### Wallet Data Model

```typescript
// types/wallet.ts

export interface WalletOrg {
  ein: string;
  name: string;
  mission: string;
  location: string;
  cause: string[];
  merit_score_v5: number;
  merit_health_signal_v5: "HEALTHY" | "STABLE" | "CAUTION";
  is_hidden_gem: boolean;
  donate_url?: string;
  bookmarkedAt: number; // timestamp
  givingIntent?: GivingIntent;
}

export interface GivingIntent {
  type: "giving" | "volunteer" | "board";
  status: "interested" | "withdrawn";
  amount?: number; // in dollars, optional
  hours?: number; // per month, optional
  addedAt: number; // timestamp
  notes?: string; // max 200 chars
}

export interface Wallet {
  version: 1;
  lastUpdated: number;
  orgs: WalletOrg[];
  syncedWithServer: boolean;
  googleEmail?: string; // if logged in
}

// localStorage key: "daanaa_wallet"
// Structure in localStorage:
{
  "daanaa_wallet": {
    "version": 1,
    "lastUpdated": 1718721600000,
    "orgs": [
      {
        "ein": "001234567",
        "name": "Save the World",
        "mission": "Fighting climate change through community education",
        "location": "Austin, TX",
        "cause": ["environment"],
        "merit_score_v5": 78,
        "merit_health_signal_v5": "HEALTHY",
        "is_hidden_gem": false,
        "donate_url": "https://savetheworld.org/donate",
        "bookmarkedAt": 1718721600000,
        "givingIntent": {
          "type": "giving",
          "status": "interested",
          "amount": 250,
          "addedAt": 1718721650000
        }
      },
      ...
    ],
    "syncedWithServer": false,
    "googleEmail": null
  }
}
```

### Server Backup (Optional, Phase 2)

```sql
-- wallet_data table (PostgreSQL)
CREATE TABLE wallet_data (
  id SERIAL PRIMARY KEY,
  google_email VARCHAR(255) UNIQUE NOT NULL,
  bookmarks JSONB NOT NULL DEFAULT '[]',
  giving_intents JSONB NOT NULL DEFAULT '[]',
  last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## UI/UX Design

### Screen 1: Wallet Page (Main View)

**Desktop Layout (1200px+):**

```
┌─────────────────────────────────────────────────────────────────┐
│ Daanaa                                                 [Google] [?]│
├─────────────────────────────────────────────────────────────────┤
│                         MY GIVING WALLET                         │
│                                                                   │
│ You have 5 organizations saved.  [+ Add More]                    │
│                                                                   │
│ ┌─ Sort: By Saved Date ▼  Filter: [All] [Health: Healthy] [Env]┐│
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐  │
│ │ Save the World                                     [Details]│  │
│ │ Austin, TX | Environment                                   │  │
│ │ "Fighting climate change through community education"      │  │
│ │                                                            │  │
│ │ Health: HEALTHY (78/100)  Hidden Gem: No                 │  │
│ │ Giving Intent: $250 · View Profile · [Remove] [Edit]    │  │
│ └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────────┐  │
│ │ Climate Alliance                                   [Details]│  │
│ │ Portland, OR | Environment                                 │  │
│ │ "Building climate resilience in the Pacific Northwest"     │  │
│ │                                                            │  │
│ │ Health: STABLE (62/100)  Hidden Gem: Yes                 │  │
│ │ Volunteer Intent: 5 hrs/month · View Profile · [Remove]  │  │
│ └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│ [View All] [Export List] [Share Wallet]                          │
└─────────────────────────────────────────────────────────────────┘
```

**Mobile Layout (< 600px):**

```
┌──────────────────────────┐
│ ← Wallet                 │
├──────────────────────────┤
│ MY GIVING WALLET         │
│                          │
│ 5 saved  [+ Add]         │
│                          │
│ Sort: Date ▼             │
│ Filter: All              │
│                          │
├──────────────────────────┤
│ Save the World           │
│ Austin, TX | Environment │
│                          │
│ "Fighting climate..."    │
│                          │
│ Health: HEALTHY (78)     │
│ Giving: $250             │
│                          │
│ [View] [Remove] [Edit]   │
├──────────────────────────┤
│ Climate Alliance         │
│ Portland, OR | Env       │
│ ...                      │
├──────────────────────────┤
│ [View All]               │
│ [Export]  [Share]        │
└──────────────────────────┘
```

### Screen 2: Add to Wallet (from Detail Page)

When donor is on nonprofit detail page and clicks "+ Add to Wallet":

```
┌─────────────────────────────────────────────┐
│ Save to Your Wallet                       ✕ │
├─────────────────────────────────────────────┤
│                                             │
│ Save the World                              │
│ Austin, TX | Environment                    │
│                                             │
│ ☐ Interested in Giving                      │
│   Amount (optional): $[____]                │
│                                             │
│ ☐ Interested in Volunteering                │
│   Hours/month (optional): [__] hrs          │
│                                             │
│ ☐ Interested in Board Opportunity           │
│                                             │
│ Notes (optional):                           │
│ [_________________________________]         │
│  (max 200 chars)                            │
│                                             │
│             [Save] [Cancel]                 │
│                                             │
└─────────────────────────────────────────────┘
```

### Screen 3: Edit Intent (from Wallet)

Donor clicks [Edit] on a wallet card to modify their intent:

```
┌─────────────────────────────────────────────┐
│ Edit Your Interest                        ✕ │
├─────────────────────────────────────────────┤
│                                             │
│ Save the World                              │
│                                             │
│ Current Intent: Giving                      │
│                                             │
│ ○ No longer interested (remove from wallet) │
│ ○ Change to: Volunteering                   │
│ ○ Change to: Board opportunity              │
│ ● Keep as: Giving                           │
│   Update amount: $[250]                     │
│                                             │
│ Notes: [_________________________________]  │
│                                             │
│             [Save] [Cancel]                 │
│                                             │
└─────────────────────────────────────────────┘
```

### Screen 4: Empty State

When wallet is empty:

```
┌─────────────────────────────────────────────┐
│ MY GIVING WALLET                            │
│                                             │
│ Your wallet is empty.                       │
│                                             │
│ Start exploring nonprofits to build your    │
│ giving plan. Save orgs you're interested    │
│ in, signal if you want to volunteer or      │
│ join their board, then decide how much      │
│ to give.                                    │
│                                             │
│ [← Back to Search]  [Browse Categories]    │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Feature Set

### Core Features (Must Have for Launch)

✅ **Add to Wallet**
- From detail page: "+ Add to Wallet" button
- Opens modal with intent options (giving / volunteer / board)
- Saves to localStorage immediately
- Shows confirmation: "Added to wallet ✓"

✅ **Wallet Page**
- Lists all saved nonprofits as cards
- Shows: name, location, cause, mission, health signal, score
- Shows giving intent (if set) with amount
- Sorted by date added (newest first)
- Mobile + desktop responsive

✅ **Remove from Wallet**
- [Remove] button on each card
- Confirmation: "Are you sure? This cannot be undone."
- Removes org from wallet
- Updates localStorage

✅ **Edit Intent**
- [Edit] button on each card opens edit modal
- Can change intent type or amount
- Can change notes
- Can mark as "no longer interested" (removes org)

✅ **Persistence**
- Wallet persists in localStorage across sessions
- Survives browser restart
- Device-specific (no sync until logged in)

✅ **Wallet Badge**
- Shows "💾 In Your Wallet" on detail pages for saved orgs
- Quick visual indicator that org is saved

✅ **Empty State**
- Clear message when wallet is empty
- Call-to-action: "Browse categories" or "Back to search"

### Phase 2 Features (Post-Launch)

🔄 **Server Sync (Optional)**
- "Sign in with Google" button in wallet
- Syncs wallet to server (wallet_data table)
- Enables cross-device wallet access
- Logout clears server sync

🔄 **Filters & Sort**
- Filter by: cause, health signal, hidden gems, giving intent type
- Sort by: date added, score, health signal, alphabetical

🔄 **Export Wallet**
- Export as: CSV, PDF, Email to self
- Includes: org name, EIN, mission, cause, health, website, my intent
- For sharing with partner or advisor

🔄 **Share Wallet**
- Generate shareable link (password-protected optional)
- Lets advisor/partner see your planned giving
- Read-only for others

🔄 **Batch Actions**
- Select multiple orgs
- Remove all at once
- Change intent on multiple orgs
- Export selected

---

## Interaction Flows

### Flow 1: Donor Discovers → Saves → Comes Back

```
1. Donor on search page
   ↓
2. Sees nonprofit they're interested in
   ↓
3. Clicks "+" to add to wallet (from search result or detail page)
   ↓
4. Modal opens, they select intent (giving, volunteer, board) + optional amount
   ↓
5. Click [Save] → org added to localStorage
   ↓
6. See confirmation: "Added to wallet ✓"
   ↓
7. Continue browsing OR go to wallet (/wallet)
   ↓
8. Later (same day, next week): Click wallet breadcrumb or nav
   ↓
9. See all saved orgs, review giving amounts, update intents
   ↓
10. Export wallet or share with advisor
```

### Flow 2: Donor Changes Mind

```
1. Donor in wallet, sees org they saved
   ↓
2. Clicks [Edit]
   ↓
3. Modal opens showing current intent
   ↓
4. Changes intent type OR marks "no longer interested"
   ↓
5. Updates amount if relevant
   ↓
6. Clicks [Save]
   ↓
7. Org updates in wallet, localStorage syncs
   ↓
8. If marked "no longer interested" → org removed from wallet
```

### Flow 3: Cross-Device Sync (Phase 2)

```
1. Donor saves orgs on desktop (localStorage)
   ↓
2. Goes to mobile, visits wallet
   ↓
3. Wallet empty (no sync yet)
   ↓
4. Clicks [Sign in with Google]
   ↓
5. Completes OAuth flow
   ↓
6. Wallet syncs from server → shows desktop orgs on mobile
   ↓
7. Adds org on mobile → syncs back to server
   ↓
8. Back on desktop → wallet shows all orgs (synced)
```

---

## Technical Requirements

### localStorage Strategy

**Key:** `daanaa_wallet` (single key, no versioning needed yet)

**Quota:** Typical: 5–10 MB, enough for 5K orgs at full detail  
**Fallback:** If quota exceeded, show warning "Wallet is full, please export or clear some orgs"

**Sync Strategy:**
- On page load: Read from localStorage
- On any change (add, edit, remove): Write to localStorage immediately
- On login: Fetch from server, merge with local, write to localStorage
- On logout: Keep localStorage (don't delete), just flag `syncedWithServer: false`

### API Endpoints (for optional Phase 2 sync)

```
GET /api/wallet
  Returns: Wallet object from server (requires Google auth)
  Headers: Authorization: Bearer <google_token>

POST /api/wallet/sync
  Body: { wallet: Wallet }
  Returns: { synced: true, lastSynced: timestamp }
  
DELETE /api/wallet
  Clears server wallet (requires auth)
```

### Validation Rules

1. **Adding to Wallet:**
   - EIN must exist in registry
   - Org must not already be in wallet (show: "Already in wallet")
   - Intent type must be one of: giving, volunteer, board
   - If amount: must be number > 0

2. **Editing Intent:**
   - New intent must be valid type
   - Amount (if provided): must be number > 0
   - Notes: max 200 characters
   - Cannot edit if org no longer in registry (remove org)

3. **Removing from Wallet:**
   - Confirmation modal required (prevent accidents)
   - Can be re-added immediately

4. **Persistence:**
   - Wallet must persist across page reloads
   - localStorage must stay in sync with React state
   - If localStorage corrupt: show error, clear wallet, suggest re-adding orgs

---

## Success Criteria

### Design Clarity (Must Have)

- [ ] **5-second rule:** First-time user understands what wallet is in 5 seconds (show to 3 people, confirm understanding)
- [ ] **No clutter:** Wallet card shows exactly: org name, location, cause, mission, health, intent. Nothing more.
- [ ] **Visual hierarchy:** Intent section (if present) visually distinct from org info
- [ ] **Mobile legible:** All text readable on mobile (16px+ font for body, 14px+ for secondary)
- [ ] **Empty state clear:** User knows what to do when wallet is empty

### Feature Completeness (Must Have)

- [ ] Can add org to wallet from detail page
- [ ] Can add org to wallet from search result
- [ ] Can remove org from wallet
- [ ] Can edit giving amount
- [ ] Can edit volunteer hours
- [ ] Can change intent type
- [ ] Can mark as "no longer interested"
- [ ] Wallet persists across page reloads (localStorage)
- [ ] Wallet badge shows on detail pages for saved orgs
- [ ] Empty state displays when wallet has 0 orgs

### Performance (Must Have)

- [ ] Wallet page loads in <1 second (even with 100 orgs)
- [ ] Adding/removing org is instant (no network delay)
- [ ] Mobile: page scrolls smoothly (60fps)
- [ ] No layout shift when loading wallet

### Accessibility (Must Have)

- [ ] Keyboard navigable (Tab through buttons, cards, filters)
- [ ] All buttons have aria-labels
- [ ] Color contrast meets WCAG AA
- [ ] Focus visible on all interactive elements
- [ ] Modal has proper focus trap and escape key handling

### Mobile Responsive (Must Have)

- [ ] Works on 320px screens (iPhone SE)
- [ ] Works on 768px screens (iPad)
- [ ] Works on 1200px+ (desktop)
- [ ] Touch targets are 48px+ (not 44px, but 48px for comfort)
- [ ] No horizontal scroll

### Resilience (Must Have)

- [ ] If localStorage quota exceeded: warn user, don't crash
- [ ] If org is removed from registry: show warning, offer to remove from wallet
- [ ] If localStorage corrupt: graceful recovery (show error, clear wallet)
- [ ] Network errors don't break wallet (Phase 2 sync failure = silent, retry later)

### Stretch Goals (Nice to Have, Post-Launch)

- [ ] Export wallet as PDF
- [ ] Filter by giving amount range
- [ ] Keyboard shortcuts (e.g., Cmd+S to save, Cmd+E to export)
- [ ] Wallet count badge in nav (shows # saved)
- [ ] Drag-to-reorder cards

---

## Implementation Notes

### State Management (WalletContext)

```typescript
// contexts/WalletContext.tsx
interface WalletContextType {
  wallet: Wallet;
  addOrg: (org: WalletOrg) => void;
  removeOrg: (ein: string) => void;
  updateIntent: (ein: string, intent: GivingIntent) => void;
  isInWallet: (ein: string) => boolean;
  getIntent: (ein: string) => GivingIntent | undefined;
  syncToServer: (googleEmail: string, token: string) => Promise<void>;
  logoutAndClearSync: () => void;
}
```

### localStorage Hook

```typescript
// hooks/useWalletPersistence.ts
export function useWalletPersistence() {
  // Read from localStorage on mount
  // Write to localStorage on any wallet change
  // Handle quota exceeded gracefully
  // Detect localStorage corruption, recover
}
```

### Wallet Card Component

```typescript
// components/Wallet/WalletCard.tsx
interface WalletCardProps {
  org: WalletOrg;
  onRemove: (ein: string) => void;
  onEdit: (ein: string) => void;
  onViewProfile: (ein: string) => void;
}
```

---

## Testing Strategy

### Unit Tests
- `walletStorage.test.ts`: localStorage read/write, quota handling, corruption recovery
- `WalletContext.test.tsx`: add, remove, update, sync logic
- `useWallet.test.ts`: hook behavior

### Integration Tests
- Add org from detail page → appears in wallet → persists
- Remove org → gone from wallet → gone from localStorage
- Edit intent → updates in wallet → updates in localStorage
- Login → wallet syncs from server (Phase 2)

### E2E Tests (Playwright)
- Full flow: search → detail → add to wallet → go to wallet → see org → remove
- Mobile: same flow on 375px viewport
- Empty state: new user opens wallet, sees empty state, clicks "Browse"

---

## Files to Create/Modify

**New Files:**
- `frontend/src/components/Wallet/WalletPage.tsx`
- `frontend/src/components/Wallet/WalletCard.tsx`
- `frontend/src/components/Wallet/WalletFilters.tsx`
- `frontend/src/components/Wallet/WalletEmptyState.tsx`
- `frontend/src/components/Wallet/IntentSignal.tsx`
- `frontend/src/components/Shared/AddToWalletButton.tsx`
- `frontend/src/contexts/WalletContext.tsx`
- `frontend/src/hooks/useWallet.ts`
- `frontend/src/hooks/useWalletPersistence.ts`
- `frontend/src/types/wallet.ts`
- `frontend/src/utils/walletStorage.ts`
- `frontend/__tests__/Wallet/*` (all test files)

**Modify:**
- `frontend/src/App.tsx` — add `/wallet` route
- `frontend/src/pages/OrganizationDetail.tsx` — add AddToWalletButton, WalletBadge
- `frontend/src/pages/Search.tsx` — add AddToWalletButton to search results (optional)
- `backend/app/models.py` — add wallet_data table (Phase 2)
- `backend/app/routes/wallet.py` — add wallet endpoints (Phase 2)

---

## Glossary

| Term | Definition |
|------|-----------|
| **Wallet** | Donor's collection of saved nonprofits + giving intents |
| **Intent** | The donor's interest type (giving, volunteer, board) + optional details (amount, hours) |
| **Giving Intent** | Donor signals "I might give to this org" + optional amount |
| **Volunteer Intent** | Donor signals "I'm interested in volunteering" + optional hours/month |
| **Board Intent** | Donor signals "I'm interested in board opportunity" |
| **Bookmarked** | Org is in wallet (legacy term, not used in UI but in code) |
| **Sync** | Wallet is backed up on server (Phase 2, enables cross-device) |
| **Health Signal** | HEALTHY, STABLE, or CAUTION (from merit_health_signal_v5) |
| **Hidden Gem** | Small, overlooked, high-performing org (is_hidden_gem = true) |

---

**Owner:** AI Engineer  
**Status:** Spec complete, ready for implementation  
**Next:** Choose execution approach (subagent-driven or inline)

---

*Spec created: Jun 18, 2026*  
*Goal: World-class wallet that makes donors feel confident in their giving decisions*
