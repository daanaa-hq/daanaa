/**
 * Wallet domain types
 * Represents the complete wallet data model for giving intent tracking
 */

/**
 * GivingIntent represents a donor's intention regarding a specific nonprofit
 * type: what kind of involvement (giving, volunteering, board)
 * status: whether the donor is still interested or has withdrawn
 * amount: optional $ amount if type is "giving"
 * frequency: optional frequency for giving (year, month, one-time)
 * hours: optional hours/week if type is "volunteer"
 * addedAt: timestamp when this intent was created
 * notes: optional 200-char max user notes
 */
export interface GivingIntent {
  type: 'giving' | 'volunteer' | 'board'
  status: 'interested' | 'withdrawn'
  amount?: number // in dollars, must be > 0 if present
  frequency?: 'year' | 'month' | 'one-time' // frequency for giving
  hours?: number // per week, must be > 0 if present
  addedAt: number // timestamp in milliseconds
  notes?: string // max 200 characters
}

/**
 * WalletOrg represents a nonprofit saved in the donor's wallet
 * ein: IRS EIN (must exist in registry)
 * name, mission, location, cause: org metadata
 * merit_score_v5: 0-100 financial context percentile
 * merit_health_signal_v5: HEALTHY | STABLE | CAUTION
 * is_hidden_gem: boolean flag for small high-performing orgs
 * donate_url: optional verified donation link
 * bookmarkedAt: timestamp when org was saved
 * givingIntent: optional intent (can be added/updated later)
 */
export interface WalletOrg {
  ein: string
  name: string
  mission: string
  location: string
  cause: string[]
  merit_score_v5: number
  merit_health_signal_v5: 'HEALTHY' | 'STABLE' | 'CAUTION'
  is_hidden_gem: boolean
  donate_url?: string
  bookmarkedAt: number // timestamp in milliseconds
  givingIntent?: GivingIntent
}

/**
 * Wallet represents the complete wallet state
 * version: schema version (currently 1)
 * lastUpdated: timestamp of last modification
 * orgs: array of saved nonprofits
 * syncedWithServer: whether wallet has been synced to backend (Phase 2)
 * googleEmail: user's Google account email if synced (Phase 2)
 *
 * localStorage key: "daanaa_wallet"
 * Typical size: 5-10 MB quota supports ~5K orgs at full detail
 */
export interface Wallet {
  version: 1
  lastUpdated: number
  orgs: WalletOrg[]
  syncedWithServer: boolean
  googleEmail?: string
}

/**
 * WalletContextType defines all operations available on wallet state
 */
export interface WalletContextType {
  wallet: Wallet
  addOrg: (org: WalletOrg) => void
  removeOrg: (ein: string) => void
  updateIntent: (ein: string, intent: GivingIntent) => void
  isInWallet: (ein: string) => boolean
  getIntent: (ein: string) => GivingIntent | undefined
  syncToServer: (googleEmail: string, token: string) => Promise<void>
  logoutAndClearSync: () => void
  storageError: 'quota' | null
}

/**
 * Validation constraints
 */
export const WALLET_CONSTRAINTS = {
  NOTES_MAX_LENGTH: 200,
  AMOUNT_MIN: 1,
  HOURS_MIN: 0.25,
} as const

/**
 * Type guards
 */
export function isValidGivingIntent(intent: unknown): intent is GivingIntent {
  if (typeof intent !== 'object' || intent === null) return false
  const i = intent as Record<string, unknown>
  return (
    typeof i.type === 'string' &&
    ['giving', 'volunteer', 'board'].includes(i.type) &&
    typeof i.status === 'string' &&
    ['interested', 'withdrawn'].includes(i.status) &&
    typeof i.addedAt === 'number' &&
    i.addedAt > 0 &&
    (i.amount === undefined || (typeof i.amount === 'number' && i.amount > 0)) &&
    (i.frequency === undefined || (typeof i.frequency === 'string' && ['year', 'month', 'one-time'].includes(i.frequency))) &&
    (i.hours === undefined || (typeof i.hours === 'number' && i.hours > 0)) &&
    (i.notes === undefined || (typeof i.notes === 'string' && i.notes.length <= 200))
  )
}

export function isValidWalletOrg(org: unknown): org is WalletOrg {
  if (typeof org !== 'object' || org === null) return false
  const o = org as Record<string, unknown>
  return (
    typeof o.ein === 'string' &&
    o.ein.length === 9 &&
    typeof o.name === 'string' &&
    typeof o.mission === 'string' &&
    typeof o.location === 'string' &&
    Array.isArray(o.cause) &&
    typeof o.merit_score_v5 === 'number' &&
    o.merit_score_v5 >= 0 &&
    o.merit_score_v5 <= 100 &&
    ['HEALTHY', 'STABLE', 'CAUTION'].includes(o.merit_health_signal_v5 as string) &&
    typeof o.is_hidden_gem === 'boolean' &&
    typeof o.bookmarkedAt === 'number' &&
    o.bookmarkedAt > 0 &&
    (o.donate_url === undefined || typeof o.donate_url === 'string') &&
    (o.givingIntent === undefined || isValidGivingIntent(o.givingIntent))
  )
}

export function isValidWallet(wallet: unknown): wallet is Wallet {
  if (typeof wallet !== 'object' || wallet === null) return false
  const w = wallet as Record<string, unknown>
  return (
    w.version === 1 &&
    typeof w.lastUpdated === 'number' &&
    w.lastUpdated > 0 &&
    Array.isArray(w.orgs) &&
    w.orgs.every(isValidWalletOrg) &&
    typeof w.syncedWithServer === 'boolean' &&
    (w.googleEmail === undefined || typeof w.googleEmail === 'string')
  )
}
