/**
 * Wallet domain types — v2 (E2E encrypted, normalized)
 * WalletEntry stores only EIN + intent. Org display data is always fetched live.
 */

// GivingIntent is unchanged from v1 — all validators in walletValidation.ts reuse.
export interface GivingIntent {
  type: 'giving' | 'volunteer' | 'board'
  amount?: number
  frequency?: 'year' | 'month' | 'one-time'
  hoursPerMonth?: number
  notes?: string  // max 200 chars
  addedAt: number
}

/** The normalized wallet entry. ~40 bytes per org. 50 orgs ≈ 2KB. */
export interface WalletEntry {
  ein: string      // 9-digit EIN
  bookmarkedAt: number
  givingIntent?: GivingIntent
}

/** The full encrypted wallet state. */
export interface Wallet {
  version: 2
  entries: WalletEntry[]
}

export interface WalletContextType {
  entries: WalletEntry[]
  addEntry: (ein: string) => void
  removeEntry: (ein: string) => void
  updateIntent: (ein: string, intent: GivingIntent) => void
  isInWallet: (ein: string) => boolean
  getIntent: (ein: string) => GivingIntent | undefined
  // Passphrase flow
  isUnlocked: boolean
  unlockWithPassphrase: (passphrase: string) => Promise<void>
  setupNewWallet: (passphrase: string) => Promise<void>
  lockWallet: () => void
  deleteWallet: () => Promise<void>
  // Sync state
  syncStatus: 'idle' | 'syncing' | 'error'
  // Download backup
  downloadBackup: () => void
  // Migration
  migrationData: WalletEntry[] | null
  applyMigration: () => void
  dismissMigration: () => void
}

/** Legacy v1 type — used only for migration detection. Do not use for new code. */
export interface LegacyWalletV1 {
  version: 1
  orgs: Array<{ ein: string; bookmarkedAt: number; givingIntent?: GivingIntent; [key: string]: unknown }>
}

export function isLegacyWalletV1(w: unknown): w is LegacyWalletV1 {
  if (typeof w !== 'object' || w === null) return false
  const obj = w as Record<string, unknown>
  return obj['version'] === 1 && Array.isArray(obj['orgs'])
}

export function isValidWalletEntry(e: unknown): e is WalletEntry {
  if (typeof e !== 'object' || e === null) return false
  const o = e as Record<string, unknown>
  return (
    typeof o['ein'] === 'string' && o['ein'].length === 9 &&
    typeof o['bookmarkedAt'] === 'number' && o['bookmarkedAt'] > 0
  )
}

export const WALLET_CONSTRAINTS = {
  NOTES_MAX_LENGTH: 200,
  AMOUNT_MIN: 1,
  HOURS_MIN: 0.25,
} as const
