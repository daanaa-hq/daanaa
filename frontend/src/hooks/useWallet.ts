import { useState, useCallback } from 'react'

export type DonationStatus = 'self_documented' | 'pending_acknowledgment' | 'acknowledged'

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
  return `MERIT-${year}-${suffix}`
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

  return {
    donations,
    volunteerHours,
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
