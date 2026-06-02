import { useState, useCallback } from 'react'

export type DonationStatus = 'self_documented' | 'pending_acknowledgment' | 'acknowledged'

// Gift type drives IRS substantiation rules (Pub 526 / 1771 / Form 8283).
export type DonationType = 'cash' | 'goods' | 'stock' | 'vehicle' | 'other'

export interface DonationRecord {
  id: string
  ein: string
  orgName: string
  amount: number
  date: string
  note?: string
  status: DonationStatus
  loggedAt: string
  letterRequested: boolean
  referenceCode?: string
  donorName?: string
  donorEmail?: string
  donationType?: DonationType
}

export interface VolunteerRecord {
  id: string
  ein: string
  orgName: string
  date: string
  hours: number
  description?: string
  loggedAt: string
}

export const SPLIT_THRESHOLD = 249
const DONATIONS_KEY = 'merit_wallet_donations'
const VOLUNTEER_KEY = 'merit_wallet_volunteer'

const ALPHABET = '23456789ABCDEFGHJKMNPQRSTUVWXYZ'

export function generateReferenceCode(): string {
  const year = new Date().getFullYear()
  const suffix = Array.from({ length: 4 }, () =>
    ALPHABET[Math.floor(Math.random() * ALPHABET.length)]
  ).join('')
  return `DAANAA-${year}-${suffix}`
}

function uid() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
}

function load<T>(key: string): T[] {
  try { return JSON.parse(localStorage.getItem(key) || '[]') } catch { return [] }
}

function persist<T>(key: string, data: T[]) {
  localStorage.setItem(key, JSON.stringify(data))
}

// Legacy split for DonationForm (manual log — stays under $249.99)
export function splitDonation(
  base: Omit<DonationRecord, 'id' | 'loggedAt' | 'status'>
): Omit<DonationRecord, 'id' | 'loggedAt'>[] {
  if (base.amount <= SPLIT_THRESHOLD) {
    return [{ ...base, status: 'self_documented' }]
  }
  return [
    { ...base, amount: SPLIT_THRESHOLD, status: 'self_documented' },
    { ...base, amount: parseFloat((base.amount - SPLIT_THRESHOLD).toFixed(2)), status: 'pending_acknowledgment' },
  ]
}

const BACKUP_VERSION = 1
const LAST_BACKUP_KEY = 'merit_wallet_last_backup'

export interface WalletBackup {
  app: 'daanaa'
  version: number
  exportedAt: string
  donations: DonationRecord[]
  volunteerHours: VolunteerRecord[]
}

// ── Optional client-side encryption (AES-GCM, PBKDF2). Key never leaves the device. ──
const b64 = (buf: ArrayBuffer) => btoa(String.fromCharCode(...new Uint8Array(buf)))
function unb64(s: string): Uint8Array {
  const bin = atob(s)
  const out = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i)
  return out
}

async function deriveKey(passphrase: string, salt: BufferSource): Promise<CryptoKey> {
  const base = await crypto.subtle.importKey('raw', new TextEncoder().encode(passphrase), 'PBKDF2', false, ['deriveKey'])
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt, iterations: 100000, hash: 'SHA-256' },
    base, { name: 'AES-GCM', length: 256 }, false, ['encrypt', 'decrypt']
  )
}

async function encryptPayload(plaintext: string, passphrase: string): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(16))
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const key = await deriveKey(passphrase, salt as BufferSource)
  const ct = await crypto.subtle.encrypt({ name: 'AES-GCM', iv: iv as BufferSource }, key, new TextEncoder().encode(plaintext))
  return JSON.stringify({ app: 'daanaa', encrypted: true, salt: b64(salt.buffer as ArrayBuffer), iv: b64(iv.buffer as ArrayBuffer), ct: b64(ct) })
}

async function decryptPayload(obj: { salt: string; iv: string; ct: string }, passphrase: string): Promise<string> {
  const key = await deriveKey(passphrase, unb64(obj.salt) as BufferSource)
  const pt = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: unb64(obj.iv) as BufferSource }, key, unb64(obj.ct) as BufferSource)
  return new TextDecoder().decode(pt)
}

export function useWallet() {
  const [donations, setDonations] = useState<DonationRecord[]>(() => load(DONATIONS_KEY))
  const [volunteerHours, setVolunteerHours] = useState<VolunteerRecord[]>(() => load(VOLUNTEER_KEY))

  // Legacy: used by DonationForm (manual log, always sub-threshold)
  const addDonation = useCallback((record: Omit<DonationRecord, 'id' | 'loggedAt' | 'status'>) => {
    const entries = splitDonation(record).map(r => ({ ...r, id: uid(), loggedAt: new Date().toISOString() }))
    setDonations(prev => { const next = [...entries, ...prev]; persist(DONATIONS_KEY, next); return next })
  }, [])

  // New: used by GivingReview — caller builds records with status already set
  const addDonationDirect = useCallback((records: Omit<DonationRecord, 'id' | 'loggedAt'>[]) => {
    const entries = records.map(r => ({ ...r, id: uid(), loggedAt: new Date().toISOString() }))
    setDonations(prev => { const next = [...entries, ...prev]; persist(DONATIONS_KEY, next); return next })
  }, [])

  const removeDonation = useCallback((id: string) => {
    setDonations(prev => { const next = prev.filter(d => d.id !== id); persist(DONATIONS_KEY, next); return next })
  }, [])

  const markAcknowledged = useCallback((id: string) => {
    setDonations(prev => {
      const next = prev.map(d => d.id === id ? { ...d, status: 'acknowledged' as DonationStatus } : d)
      persist(DONATIONS_KEY, next)
      return next
    })
  }, [])

  const addVolunteer = useCallback((record: Omit<VolunteerRecord, 'id' | 'loggedAt'>) => {
    const entry: VolunteerRecord = { ...record, id: uid(), loggedAt: new Date().toISOString() }
    setVolunteerHours(prev => { const next = [entry, ...prev]; persist(VOLUNTEER_KEY, next); return next })
  }, [])

  const removeVolunteer = useCallback((id: string) => {
    setVolunteerHours(prev => { const next = prev.filter(v => v.id !== id); persist(VOLUNTEER_KEY, next); return next })
  }, [])

  const thisYear = new Date().getFullYear().toString()

  // ── Backup: device-driven only. No server, no account, no PII leaves the device. ──

  // Download the wallet as a file the user keeps in their own Files / cloud drive.
  // If a passphrase is given, the file is encrypted client-side (we never see the key).
  const exportBackup = useCallback(async (passphrase?: string) => {
    const payload: WalletBackup = {
      app: 'daanaa',
      version: BACKUP_VERSION,
      exportedAt: new Date().toISOString(),
      donations: load(DONATIONS_KEY),
      volunteerHours: load(VOLUNTEER_KEY),
    }
    const plain = JSON.stringify(payload, null, 2)
    const out = passphrase ? await encryptPayload(plain, passphrase) : plain
    const blob = new Blob([out], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `daanaa-giving-backup-${new Date().toISOString().slice(0, 10)}${passphrase ? '.enc' : ''}.json`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
    try { localStorage.setItem(LAST_BACKUP_KEY, new Date().toISOString()) } catch { /* ignore */ }
  }, [])

  // Restore from a backup file the user picks. Replaces current wallet contents.
  // If the file is encrypted, the passphrase is required.
  const importBackup = useCallback(async (raw: string, passphrase?: string): Promise<{ ok: boolean; error?: string; needsPassphrase?: boolean }> => {
    try {
      let obj = JSON.parse(raw) as Record<string, unknown>
      if (obj.encrypted === true) {
        if (!passphrase) return { ok: false, needsPassphrase: true }
        try {
          obj = JSON.parse(await decryptPayload(obj as { salt: string; iv: string; ct: string }, passphrase))
        } catch {
          return { ok: false, error: 'Wrong password, or the file is damaged.' }
        }
      }
      const parsed = obj as unknown as WalletBackup
      if (parsed.app !== 'daanaa' || !Array.isArray(parsed.donations)) {
        return { ok: false, error: 'This does not look like a Daanaa backup file.' }
      }
      persist(DONATIONS_KEY, parsed.donations)
      persist(VOLUNTEER_KEY, parsed.volunteerHours || [])
      setDonations(parsed.donations)
      setVolunteerHours(parsed.volunteerHours || [])
      return { ok: true }
    } catch {
      return { ok: false, error: 'Could not read that file.' }
    }
  }, [])

  // A short summary the user can text to themselves (opens their own Messages app).
  const buildSummaryText = useCallback(() => {
    const yr = donations.filter(d => d.date.startsWith(thisYear))
    const total = yr.reduce((s, d) => s + d.amount, 0)
    const orgs = new Set(yr.map(d => d.ein)).size
    const lines = [
      `My Daanaa giving record (${thisYear})`,
      `Total given: $${total.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
      `Organizations supported: ${orgs}`,
      '',
      ...yr.slice(0, 12).map(d => `- ${d.orgName}: $${d.amount.toLocaleString()} (${d.date})`),
      yr.length > 12 ? `...and ${yr.length - 12} more` : '',
      '',
      'Kept on my device. daanaa.org',
    ].filter(Boolean)
    return lines.join('\n')
  }, [donations, thisYear])

  // sms: deep link — opens the user's Messages app pre-filled; they send to themselves.
  const selfTextHref = `sms:?&body=${encodeURIComponent(buildSummaryText())}`

  const lastBackupAt = (() => {
    try { return localStorage.getItem(LAST_BACKUP_KEY) } catch { return null }
  })()
  // Nudge a backup if it has been 90+ days (or never).
  const backupDueDays = lastBackupAt
    ? Math.floor((Date.now() - new Date(lastBackupAt).getTime()) / 86400000)
    : null
  const backupOverdue = donations.length > 0 && (backupDueDays === null || backupDueDays >= 90)

  return {
    donations,
    volunteerHours,
    exportBackup,
    importBackup,
    buildSummaryText,
    selfTextHref,
    lastBackupAt,
    backupOverdue,
    addDonation,
    addDonationDirect,
    removeDonation,
    markAcknowledged,
    addVolunteer,
    removeVolunteer,
    totalDonated: donations.reduce((s, d) => s + d.amount, 0),
    totalDonatedThisYear: donations.filter(d => d.date.startsWith(thisYear)).reduce((s, d) => s + d.amount, 0),
    pendingAcknowledgment: donations.filter(d => d.status === 'pending_acknowledgment'),
    pendingLetters: donations.filter(d => d.status === 'pending_acknowledgment' && !!d.referenceCode),
    orgsSupported: new Set(donations.map(d => d.ein)).size,
    uniqueEins: new Set(donations.map(d => d.ein)),
    totalHours: volunteerHours.reduce((s, v) => s + v.hours, 0),
    totalHoursThisYear: volunteerHours.filter(v => v.date.startsWith(thisYear)).reduce((s, v) => s + v.hours, 0),
    orgsServed: new Set(volunteerHours.map(v => v.ein)).size,
  }
}
