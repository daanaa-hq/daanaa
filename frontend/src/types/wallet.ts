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
  // Optional point-in-time IRS evidence captured when this gift was logged.
  // This is an observation, not a tax determination or receipt.
  irsEligibilityStatus?: 'verified' | 'unverified' | 'revoked' | 'unknown' | 'exception_possible'
  irsEligibilityRecordedAt?: string
  irsEligibilityCheckedAt?: string | null
  irsEligibilitySources?: string[]
  letterRequested?: boolean
  letterStatus?: 'pending' | 'approved' | 'generated' | 'downloaded'
  helpedDaanaa?: boolean  // one-way: once true, permanent. indicates opt-in to impact tracking
}

// Approval status of a volunteer hours entry.
//  'private'   — logged only in this wallet, never sent anywhere (the default)
//  'submitted' — sent to the nonprofit via an event QR/link, awaiting review
//  'approved'  — the nonprofit approved it (nonprofit-approved, NOT Daanaa-verified)
//  'rejected'  — the nonprofit declined it
export type VolunteerHoursStatus = 'private' | 'submitted' | 'approved' | 'rejected'

// LoggedVolunteerHours — actual hours logged by volunteer
export interface LoggedVolunteerHours {
  id: string
  hours: number
  date: string  // ISO date — always the SERVICE date (the day volunteered), never the day it was logged
  notes?: string
  helpedDaanaa?: boolean  // one-way: once true, permanent. indicates opt-in to impact tracking
  // Server linkage — present only when this entry mirrors an event submission.
  // Absent status means 'private'. For linked entries the server owns the
  // public impact record (created once, on nonprofit approval) — the wallet
  // never syncs these to /api/impact/log, or the hours would count twice.
  status?: VolunteerHoursStatus
  submissionId?: string   // volunteer_hours.id on the server (capability token)
  eventId?: number        // volunteer_events.id
  rejectionReason?: string
  statusCheckedAt?: string  // ISO timestamp of last status refresh
}

/** Link data connecting a wallet entry to its server-side event submission. */
export interface VolunteerSubmissionLink {
  submissionId: string
  eventId?: number
}

/** The normalized wallet entry. Tracks bookmarks + actual activity. */
// RecurringTemplate — a saved giving rhythm ("I give $50 here every December").
// Device-only like the rest of the wallet; due-ness is computed client-side so
// no reminder data ever reaches a server.
export interface RecurringTemplate {
  amount: number
  cadence: 'monthly' | 'quarterly' | 'yearly'
  createdAt: number
  // Cadence anchor: for yearly, the 1-12 month the gift belongs to;
  // ignored for monthly/quarterly (anchored to last gift instead).
  anchorMonth?: number
  // A due nudge the user dismissed stays quiet until the next cycle.
  snoozedUntil?: string  // ISO date (YYYY-MM-DD)
}

export interface DonorNote {
  id: string
  text: string
  addedAt: number
  authorName?: string
}

export interface WalletEntry {
  ein: string                      // 9-digit EIN
  bookmarkedAt: number
  inFunding?: boolean              // in funding/giving list (green heart)
  inVolunteering?: boolean         // in volunteering list (red heart)
  donations?: LoggedDonation[]     // actual donations
  volunteerHours?: LoggedVolunteerHours[]  // actual volunteer hours
  recurringTemplate?: RecurringTemplate    // saved giving rhythm (see above)
  donorNotes?: DonorNote[]         // supporter voice: notes on orgs they've backed
  givingIntent?: GivingIntent      // legacy: intent tracking (deprecated, kept for migration)
}

/** Days per cadence cycle, used to decide when a template is due again. */
const CADENCE_DAYS: Record<RecurringTemplate['cadence'], number> = {
  monthly: 30, quarterly: 91, yearly: 365,
}

/**
 * A template is due when a full cadence cycle has passed since the most
 * recent logged donation (or since template creation when nothing is logged
 * yet), and any snooze has lapsed. Yearly templates with an anchorMonth are
 * due only during that month.
 */
export function isTemplateDue(entry: WalletEntry, today: Date = new Date()): boolean {
  const t = entry.recurringTemplate
  if (!t) return false
  const todayIso = today.toISOString().slice(0, 10)
  if (t.snoozedUntil && todayIso < t.snoozedUntil) return false
  if (t.cadence === 'yearly' && t.anchorMonth && (today.getMonth() + 1) !== t.anchorMonth) return false
  const giftDates = (entry.donations ?? []).map(d => d.date).sort()
  const lastGift = giftDates.length ? giftDates[giftDates.length - 1] : undefined
  const sinceMs = lastGift
    ? today.getTime() - new Date(`${lastGift}T00:00:00`).getTime()
    : today.getTime() - t.createdAt
  return sinceMs >= CADENCE_DAYS[t.cadence] * 86_400_000
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
  logDonation: (ein: string, amount: number, date: string, notes?: string, helpedDaanaa?: boolean, irsSnapshot?: Pick<LoggedDonation, 'irsEligibilityStatus' | 'irsEligibilityCheckedAt' | 'irsEligibilitySources'>) => void
  logVolunteerHours: (ein: string, hours: number, date: string, notes?: string, helpedDaanaa?: boolean, link?: VolunteerSubmissionLink) => void
  getDonations: (ein: string) => LoggedDonation[] | undefined
  getVolunteerHours: (ein: string) => LoggedVolunteerHours[] | undefined
  // Refresh approval status of event-linked volunteer hours from the server
  // (submission-id capability lookup; no identity is sent or returned)
  refreshVolunteerStatuses: () => Promise<void>
  updateDonationLetterStatus: (ein: string, donationId: string, status: LoggedDonation['letterStatus']) => void
  // Recurring giving rhythm (device-only; powers "give again" nudges)
  setRecurringTemplate: (ein: string, template: RecurringTemplate) => void
  clearRecurringTemplate: (ein: string) => void
  snoozeRecurringTemplate: (ein: string, untilIsoDate: string) => void
  archiveDonationHistory: (ein: string, beforeDate: string) => void
  syncImpactLog: (entry: LoggedDonation | LoggedVolunteerHours, type: 'giving' | 'volunteer', ein: string) => Promise<void>
  // Donor voice notes (qualitative trust signals)
  addDonorNote: (ein: string, note: any) => void
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
