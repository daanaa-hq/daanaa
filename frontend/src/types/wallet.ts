/**
 * Wallet domain types — v3 (actual giving/volunteer logging, not intent)
 * Wallet tracks: bookmarks, actual donations, actual volunteer hours
 */

// LoggedDonation — actual gift logged by donor
export interface LoggedDonation {
  id: string
  amount: number
  date: string  // ISO date (YYYY-MM-DD)
  notes?: string
  letterRequested?: boolean
  letterStatus?: 'pending' | 'approved' | 'generated' | 'downloaded'
  helpedDaanaa?: boolean  // one-way: once true, permanent. indicates opt-in to impact tracking
}

// LoggedVolunteerHours — actual hours logged by volunteer
export interface LoggedVolunteerHours {
  id: string
  hours: number
  date: string  // ISO date
  notes?: string
  helpedDaanaa?: boolean  // one-way: once true, permanent. indicates opt-in to impact tracking
}

/** The normalized wallet entry. Tracks bookmarks + actual activity. */
export interface WalletEntry {
  ein: string                      // 9-digit EIN
  bookmarkedAt: number
  inFunding?: boolean              // in funding/giving list (green heart)
  inVolunteering?: boolean         // in volunteering list (red heart)
  donations?: LoggedDonation[]     // actual donations
  volunteerHours?: LoggedVolunteerHours[]  // actual volunteer hours
  givingIntent?: GivingIntent      // legacy: intent tracking (deprecated, kept for migration)
}

// Legacy: GivingIntent (kept for backward compat, but no longer used)
export interface GivingIntent {
  type: 'giving' | 'volunteer'
  amount?: number
  frequency?: 'year' | 'month' | 'one-time'
  hoursPerMonth?: number
  notes?: string
  addedAt: number
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
  addToFunding: (ein: string) => void
  addToVolunteering: (ein: string) => void
  removeFromFunding: (ein: string) => void
  removeFromVolunteering: (ein: string) => void
  isInFunding: (ein: string) => boolean
  isInVolunteering: (ein: string) => boolean
  // Logging actual giving/volunteering
  logDonation: (ein: string, amount: number, date: string, notes?: string, helpedDaanaa?: boolean) => void
  logVolunteerHours: (ein: string, hours: number, date: string, notes?: string, helpedDaanaa?: boolean) => void
  getDonations: (ein: string) => LoggedDonation[] | undefined
  getVolunteerHours: (ein: string) => LoggedVolunteerHours[] | undefined
  updateDonationLetterStatus: (ein: string, donationId: string, status: LoggedDonation['letterStatus']) => void
  archiveDonationHistory: (ein: string, beforeDate: string) => void
  syncImpactLog: (entry: LoggedDonation | LoggedVolunteerHours, type: 'giving' | 'volunteer', ein: string) => Promise<void>
  // Legacy intent methods (deprecated, kept for backward compat)
  updateIntent: (ein: string, intent: GivingIntent) => void
  getIntent: (ein: string) => GivingIntent | undefined
  isInWallet: (ein: string) => boolean
  // Passphrase flow
  isUnlocked: boolean
  unlockWithPassphrase: (passphrase: string) => Promise<void>
  setupNewWallet: (passphrase: string) => Promise<void>
  lockWallet: () => void
  deleteWallet: () => Promise<void>
  // Sync state
  syncStatus: 'idle' | 'syncing' | 'error'
  // Cross-device sync (Firebase-backed)
  mergeRemoteEntries: (entries: WalletEntry[]) => void
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
  // Valid if: has ein + bookmarkedAt, optionally donations/hours
  return (
    typeof o['ein'] === 'string' && o['ein'].length === 9 &&
    typeof o['bookmarkedAt'] === 'number' && o['bookmarkedAt'] > 0
  )
}

export function isValidWallet(w: unknown): w is Wallet {
  if (typeof w !== 'object' || w === null) return false
  const obj = w as Record<string, unknown>
  return obj['version'] === 2 && Array.isArray(obj['entries']) && (obj['entries'] as unknown[]).every(isValidWalletEntry)
}

// WalletOrg: extended entry with API org data (used for display)
export type WalletOrg = WalletEntry & Record<string, unknown>

export const WALLET_CONSTRAINTS = {
  NOTES_MAX_LENGTH: 200,
  AMOUNT_MIN: 1,
  HOURS_MIN: 0.25,
} as const
