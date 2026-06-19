# Wallet Validation Quick Reference

## Import the validators

```typescript
import {
  validateSearchTerm,
  validateFilterValue,
  validateSortValue,
  validateIntentNotes,
  validateAmount,
  validateHours,
  validateEmail,
  validateGivingIntent,
  logValidationError,
} from '../utils/walletValidation'
```

## Usage Examples

### Search Input
```typescript
try {
  const validated = validateSearchTerm(userInput)
  setSearchTerm(validated)
} catch (err) {
  setError((err as Error).message)
}
```

### Filter Values
```typescript
// Returns true/false, doesn't throw
if (validateFilterValue('intent', value)) {
  setFilter(value)
} else {
  setError('Invalid filter value')
}
```

### Sort Values
```typescript
if (validateSortValue(userInput)) {
  setSortBy(userInput)
}
```

### Intent Notes
```typescript
try {
  const sanitized = validateIntentNotes(notes)
  updateIntent(ein, { ...intent, notes: sanitized })
} catch (err) {
  logValidationError('updateIntent', err as Error)
}
```

### Donation Amount
```typescript
try {
  const amount = validateAmount(userInput)
  updateIntent(ein, { ...intent, amount })
} catch (err) {
  setError('Invalid amount')
}
```

### Volunteer Hours
```typescript
try {
  const hours = validateHours(userInput)
  updateIntent(ein, { ...intent, hours })
} catch (err) {
  setError('Invalid hours')
}
```

### Email
```typescript
try {
  const email = validateEmail(userInput)
  // Use email
} catch (err) {
  setError('Invalid email address')
}
```

## Validation Boundaries

| Field | Min | Max | Type | Notes |
|-------|-----|-----|------|-------|
| Search | 1 char | 100 chars | string | Blocks XSS/ReDoS |
| Notes | 0 chars | 200 chars | string | Removes control chars |
| Amount | $1 | $999,999 | integer | No decimals |
| Hours | 0.25 | 168 | number | Can be fractional |
| Email | - | 254 chars | string | RFC 5322 format |

## Error Messages

### Safe to Show Users
All error messages are user-friendly and don't expose internals:

```
"Search term must be 100 characters or less"
"Amount must be a whole number"
"Hours must be greater than 0"
"Hours must be 168 or less (one week)"
"Notes must be 200 characters or less"
"Invalid email format"
```

### Safe Logging
Use `logValidationError()` for all validation errors:

```typescript
catch (err) {
  logValidationError('updateIntent', err as Error)
}
```

This logs: `[WalletValidation] updateIntent: <error message>`
(No PII, no internal state)

## What Gets Blocked

### XSS Attempts
- `<script>alert(1)</script>` ✗
- `<img onerror=alert(1)>` ✗
- `javascript:alert(1)` ✗
- `onerror=alert(1)` ✗

### ReDoS Patterns
- `(a+)+b` ✗
- `(a*)*b` ✗
- `(a|a)*b` ✗

### Type Coercion
- `validateAmount('100')` throws (must be number)
- `validateAmount(null)` throws
- `validateAmount(undefined)` throws
- `validateAmount([100])` throws

### Out-of-Bounds Values
- `validateAmount(0)` throws (min is 1)
- `validateAmount(-50)` throws
- `validateAmount(10.5)` throws (must be integer)
- `validateAmount(1000000)` throws (max is 999999)
- `validateHours(0)` throws (min is 0.25)
- `validateHours(169)` throws (max is 168)

## Testing Validators

See `frontend/__tests__/security/wallet-security.test.ts` for 90 tests covering:
- Valid inputs
- Invalid inputs
- Boundary cases
- XSS attempts
- ReDoS patterns
- Type coercion
- DoS prevention
- Privacy compliance

Run tests:
```bash
npm test -- __tests__/security/wallet-security.test.ts
```

## Performance

All validators are O(n) or O(1):
- Search: O(n) for pattern matching on up to 100 chars
- Filters: O(1) hash lookups
- Amount/Hours: O(1) number checks
- Email: O(n) regex on up to 254 chars

Test suite runs in ~0.3 seconds (90 tests).

## Privacy Notes

Validators never expose:
- Full org objects (only EIN logged)
- User email addresses in logs
- Donation amounts in error messages
- Internal state or database details

All logging via `logValidationError()` format:
```
[WalletValidation] <context>: <safe message>
```

## Common Patterns

### Validated Giving Intent
```typescript
const intent: GivingIntent = {
  type: 'giving',
  status: 'interested',
  amount: validateAmount(input.amount),
  notes: validateIntentNotes(input.notes),
  addedAt: Date.now(),
}
```

### Safe Filter Update
```typescript
const filters = {
  intent: validateFilterValue('intent', value) ? value : 'all',
  health: validateFilterValue('health', value) ? value : 'all',
}
```

### Safe Search Update
```typescript
try {
  const term = validateSearchTerm(input)
  setSearch(term)
  clearSearchError()
} catch {
  setSearchError('Invalid search term')
  // Don't update search term
}
```

## Related Files

- **Implementation:** `frontend/src/utils/walletValidation.ts`
- **Tests:** `frontend/__tests__/security/wallet-security.test.ts`
- **Context:** `frontend/src/contexts/WalletContext.tsx`
- **Page:** `frontend/src/pages/WalletPage.tsx`
- **Audit:** `docs/security/WALLET-SECURITY-AUDIT.md`
