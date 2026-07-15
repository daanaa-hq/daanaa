import { useState, useEffect, useCallback } from 'react'
import {
  getAdminWaitlist, updateWaitlistEntry, deleteWaitlistEntry,
  getOrganizations,
  type WaitlistEntry, type ApiOrganization,
} from '../data/api'
import LampMark from '../components/LampMark'
import { getTierFromOrg } from '../components/TrustBadge'
import { formatEIN } from '../data/organizations'

// ─── Status helpers ──────────────────────────────────────────────────────────

const STATUS_CYCLE: Record<WaitlistEntry['status'], WaitlistEntry['status']> = {
  new:       'contacted',
  contacted: 'converted',
  converted: 'dismissed',
  dismissed: 'new',
}

const STATUS_COLOR: Record<WaitlistEntry['status'], string> = {
  new:       'bg-blue-100 text-blue-700',
  contacted: 'bg-amber-100 text-amber-700',
  converted: 'bg-emerald-100 text-emerald-700',
  dismissed: 'bg-gray-100 text-gray-500',
}

function relativeDate(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins  = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days  = Math.floor(diff / 86400000)
  if (mins  <  1) return 'just now'
  if (mins  < 60) return `${mins}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

// ─── Auth gate ───────────────────────────────────────────────────────────────

function KeyGate({ onKey }: { onKey: (k: string) => void }) {
  const [input, setInput] = useState('')
  return (
    <div className="min-h-[100dvh] bg-deep-navy flex items-center justify-center">
      <div className="bg-white rounded-2xl p-8 w-full max-w-sm shadow-xl">
        <h1 className="font-display text-[22px] text-deep-navy mb-1">Daanaa Admin</h1>
        <p className="font-body text-[13px] text-cool-grey mb-6">Enter your admin key to continue</p>
        <form onSubmit={e => { e.preventDefault(); if (input.trim()) onKey(input.trim()) }}>
          <input
            type="password"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="X-Admin-Key"
            autoFocus
            className="w-full border border-light-grey rounded-lg px-4 py-2.5 font-body text-[14px] text-deep-navy outline-none focus:border-soft-gold mb-4"
          />
          <button
            type="submit"
            className="w-full h-[44px] bg-soft-gold text-deep-navy font-body text-[14px] font-semibold rounded-lg hover:bg-bright-gold transition-colors"
          >
            Enter
          </button>
        </form>
      </div>
    </div>
  )
}

// ─── Claims tab ──────────────────────────────────────────────────────────────
// The phone-verification worklist. Each card carries everything needed to
// make the call: who claimed, the org as the IRS records it, the PIN to read
// once identity is confirmed, and the audit-trail actions (mark called with a
// note, revoke with a required reason).

interface AdminClaim {
  ein: string
  email: string
  phone: string | null
  rep_name: string | null
  rep_title: string | null
  pin: string
  pin_expires_at: string
  claim_status: string
  created_at: string
  attested_at: string | null
  verified_at: string | null
  called_at: string | null
  call_notes: string | null
  revoked_at: string | null
  revoke_reason: string | null
  organization_name: string | null
  CITY: string | null
  STATE: string | null
}

const CLAIM_STATUS_COLOR: Record<string, string> = {
  pending:  'bg-amber-100 text-amber-700',
  verified: 'bg-emerald-100 text-emerald-700',
  active:   'bg-emerald-100 text-emerald-700',
  revoked:  'bg-red-100 text-red-600',
}

interface TodayQueue {
  to_call: { ein: string; organization_name: string | null; rep_name: string | null; phone: string | null; days_waiting: number }[]
  pin_expiring: { ein: string; organization_name: string | null; rep_name: string | null; email: string; days_left: number }[]
}

function ClaimsTab({ adminKey }: { adminKey: string }) {
  const [claims, setClaims] = useState<AdminClaim[]>([])
  const [today, setToday] = useState<TodayQueue | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState('pending')
  const [noteDraft, setNoteDraft] = useState<Record<string, string>>({})
  const [revoking, setRevoking] = useState<string | null>(null)
  const [revokeReason, setRevokeReason] = useState('')

  const loadToday = useCallback(async () => {
    try {
      const res = await fetch('/api/admin/today', { headers: { 'X-Admin-Key': adminKey } })
      if (res.ok) setToday(await res.json())
    } catch { /* the queue is a convenience; the claims list still works without it */ }
  }, [adminKey])

  useEffect(() => { loadToday() }, [loadToday])

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const qs = statusFilter ? `?status=${statusFilter}` : ''
      const res = await fetch(`/api/admin/claims${qs}`, { headers: { 'X-Admin-Key': adminKey } })
      if (!res.ok) throw new Error(String(res.status))
      const body = await res.json()
      setClaims(body.claims)
    } catch {
      setError('Failed to load claims')
    } finally {
      setLoading(false)
    }
  }, [adminKey, statusFilter])

  useEffect(() => { load() }, [load])

  async function patchClaim(ein: string, payload: Record<string, string>) {
    const res = await fetch(`/api/admin/claims/${ein}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Key': adminKey },
      body: JSON.stringify(payload),
    })
    if (res.ok) { load(); loadToday() }
    return res.ok
  }

  if (error) return <p className="font-body text-[14px] text-red-500 p-6">{error}</p>

  const todayCount = (today?.to_call.length ?? 0) + (today?.pin_expiring.length ?? 0)

  return (
    <div>
      {/* Today — the system says what needs attention */}
      {today && (
        <div className="mb-6 bg-deep-navy rounded-xl p-5">
          <p className="font-body text-[12px] font-medium tracking-[0.08em] text-soft-gold uppercase mb-2">
            Today {todayCount > 0 ? `· ${todayCount} item${todayCount === 1 ? '' : 's'}` : ''}
          </p>
          {todayCount === 0 ? (
            <p className="font-body text-[14px] text-warm-cream/70">Nothing needs you right now.</p>
          ) : (
            <div className="space-y-1.5">
              {today.to_call.map(t => (
                <p key={t.ein} className="font-body text-[14px] text-warm-cream">
                  Call <strong>{t.rep_name || 'the contact'}</strong> at{' '}
                  {t.phone ? (
                    <a href={`tel:${t.phone.replace(/\D/g, '')}`} className="text-soft-gold font-semibold hover:underline">{t.phone}</a>
                  ) : 'their number'}{' '}
                  to verify {t.organization_name || t.ein}
                  <span className="text-warm-cream/50"> · waiting {t.days_waiting === 0 ? 'since today' : `${t.days_waiting}d`}</span>
                </p>
              ))}
              {today.pin_expiring.map(t => (
                <p key={t.ein} className="font-body text-[14px] text-warm-cream">
                  PIN for <strong>{t.organization_name || t.ein}</strong> expires in {t.days_left}d and hasn't been used
                  <span className="text-warm-cream/50"> · consider a friendly nudge to {t.email}</span>
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3 mb-5">
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="border border-light-grey rounded-lg px-3 py-1.5 font-body text-[13px] text-deep-navy outline-none focus:border-soft-gold"
        >
          <option value="pending">Pending (call these)</option>
          <option value="verified">Verified</option>
          <option value="active">Active</option>
          <option value="revoked">Revoked</option>
          <option value="">All</option>
        </select>
        <span className="font-body text-[13px] text-cool-grey ml-auto">{claims.length} claims</span>
        <button
          onClick={load}
          className="font-body text-[12px] text-cool-grey border border-light-grey rounded-lg px-3 py-1.5 hover:bg-warm-cream transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Verification call checklist — same script every time, on purpose */}
      <details className="mb-5 bg-white rounded-xl border border-light-grey px-5 py-3">
        <summary className="font-body text-[13px] font-medium text-deep-navy cursor-pointer">
          Verification call checklist
        </summary>
        <ol className="mt-3 space-y-1.5 font-body text-[13px] text-cool-grey list-decimal pl-5">
          <li>Confirm you are speaking with the person named on the claim and that their role matches the title given.</li>
          <li>Ask how they are connected to the organization. If anything feels off, call back through a number from the org's own website or public records.</li>
          <li>Once satisfied, read them the 6 digit PIN and remind them it stays good for 7 days at daanaa.org/claim/verify.</li>
          <li>Press Mark called and write one line about how identity was confirmed.</li>
        </ol>
      </details>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
        </div>
      ) : claims.length === 0 ? (
        <p className="font-body text-[14px] text-cool-grey text-center py-12">No claims here right now</p>
      ) : (
        <div className="space-y-4">
          {claims.map(c => (
            <div key={c.ein} className="bg-white rounded-xl border border-light-grey p-5">
              <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                <div>
                  <div className="flex items-center gap-2.5">
                    <a
                      href={`/org/${c.ein}`}
                      target="_blank"
                      rel="noreferrer"
                      className="font-body text-[15px] font-semibold text-deep-navy hover:text-soft-gold transition-colors"
                    >
                      {c.organization_name || 'Unknown organization'}
                    </a>
                    <span className={`font-body text-[11px] px-2 py-0.5 rounded-full ${CLAIM_STATUS_COLOR[c.claim_status] ?? 'bg-gray-100 text-gray-500'}`}>
                      {c.claim_status}
                    </span>
                  </div>
                  <p className="font-body text-[12px] text-cool-grey mt-0.5">
                    EIN {formatEIN(c.ein)} · {[c.CITY, c.STATE].filter(Boolean).join(', ') || 'location unknown'} · claimed {relativeDate(c.created_at)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-body text-[11px] tracking-[0.06em] text-cool-grey uppercase mb-0.5">PIN: read on call only</p>
                  <p className="font-mono text-[22px] font-semibold text-deep-navy tracking-[0.25em]">{c.pin}</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-x-6 gap-y-1 mb-4 font-body text-[13px] text-deep-navy">
                <span className="font-semibold">{c.rep_name || 'Name not given'}</span>
                <span>{c.rep_title || 'Role not given'}</span>
                {c.phone && (
                  <a href={`tel:${c.phone.replace(/\D/g, '')}`} className="text-soft-gold font-semibold hover:underline">
                    {c.phone}
                  </a>
                )}
                <a href={`mailto:${c.email}`} className="text-cool-grey hover:text-deep-navy">{c.email}</a>
              </div>

              {c.called_at ? (
                <p className="font-body text-[12px] text-emerald-700 bg-emerald-50 rounded-lg px-3 py-2 mb-3">
                  Called {relativeDate(c.called_at)}{c.call_notes ? ` — ${c.call_notes}` : ''}
                </p>
              ) : c.claim_status === 'pending' && (
                <div className="flex flex-wrap gap-2 mb-3">
                  <input
                    value={noteDraft[c.ein] ?? ''}
                    onChange={e => setNoteDraft(d => ({ ...d, [c.ein]: e.target.value }))}
                    placeholder="How was identity confirmed? (one line)"
                    className="flex-1 min-w-[240px] border border-light-grey rounded-lg px-3 py-2 font-body text-[13px] text-deep-navy outline-none focus:border-soft-gold"
                  />
                  <button
                    onClick={() => patchClaim(c.ein, { action: 'mark_called', notes: noteDraft[c.ein] ?? '' })}
                    className="font-body text-[13px] font-semibold bg-soft-gold text-deep-navy rounded-lg px-4 py-2 hover:bg-bright-gold transition-colors"
                  >
                    Mark called
                  </button>
                </div>
              )}

              {c.claim_status === 'revoked' ? (
                <p className="font-body text-[12px] text-red-600">
                  Revoked {c.revoked_at ? relativeDate(c.revoked_at) : ''} — {c.revoke_reason}
                </p>
              ) : revoking === c.ein ? (
                <div className="flex flex-wrap gap-2">
                  <input
                    autoFocus
                    value={revokeReason}
                    onChange={e => setRevokeReason(e.target.value)}
                    placeholder="Reason for revoking (required, kept on record)"
                    className="flex-1 min-w-[240px] border border-red-200 rounded-lg px-3 py-2 font-body text-[13px] text-deep-navy outline-none focus:border-red-400"
                  />
                  <button
                    onClick={async () => {
                      if (!revokeReason.trim()) return
                      if (await patchClaim(c.ein, { action: 'revoke', reason: revokeReason.trim() })) {
                        setRevoking(null); setRevokeReason('')
                      }
                    }}
                    className="font-body text-[13px] font-semibold bg-red-500 text-white rounded-lg px-4 py-2 hover:bg-red-600 transition-colors"
                  >
                    Confirm revoke
                  </button>
                  <button
                    onClick={() => { setRevoking(null); setRevokeReason('') }}
                    className="font-body text-[13px] text-cool-grey rounded-lg px-3 py-2 hover:bg-warm-cream transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setRevoking(c.ein)}
                  className="font-body text-[12px] text-cool-grey hover:text-red-500 transition-colors"
                >
                  Revoke this claim
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Waitlist tab ────────────────────────────────────────────────────────────

function WaitlistTab({ adminKey }: { adminKey: string }) {
  const [entries, setEntries] = useState<WaitlistEntry[]>([])
  const [total, setTotal]     = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState('')
  const [srcFilter, setSrcFilter]    = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [editingNote, setEditingNote] = useState<{ id: number; val: string } | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getAdminWaitlist(adminKey, {
        source: srcFilter || undefined,
        status: statusFilter || undefined,
      })
      setEntries(res.entries)
      setTotal(res.total)
    } catch (e: unknown) {
      setError(e instanceof Error && e.message.includes('401') ? 'Invalid admin key' : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [adminKey, srcFilter, statusFilter])

  useEffect(() => { load() }, [load])

  async function cycleStatus(entry: WaitlistEntry) {
    const next = STATUS_CYCLE[entry.status]
    const updated = await updateWaitlistEntry(entry.id, { status: next }, adminKey)
    setEntries(prev => prev.map(e => e.id === entry.id ? updated : e))
  }

  async function saveNote(id: number, notes: string) {
    const updated = await updateWaitlistEntry(id, { notes }, adminKey)
    setEntries(prev => prev.map(e => e.id === id ? updated : e))
    setEditingNote(null)
  }

  async function remove(id: number) {
    await deleteWaitlistEntry(id, adminKey)
    setEntries(prev => prev.filter(e => e.id !== id))
    setTotal(t => t - 1)
  }

  function exportCsv() {
    const rows = [['ID', 'Email', 'EIN', 'Source', 'Status', 'Notes', 'Created']]
    entries.forEach(e => rows.push([
      String(e.id), e.email, e.ein ?? '', e.source, e.status, e.notes ?? '', e.created_at,
    ]))
    const csv = rows.map(r => r.map(c => `"${c.replace(/"/g, '""')}"`).join(',')).join('\n')
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
    a.download = `waitlist-${new Date().toISOString().slice(0,10)}.csv`
    a.click()
  }

  if (error) return <p className="font-body text-[14px] text-red-500 p-6">{error}</p>

  return (
    <div>
      {/* Filters + actions */}
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <select
          value={srcFilter}
          onChange={e => setSrcFilter(e.target.value)}
          className="border border-light-grey rounded-lg px-3 py-1.5 font-body text-[13px] text-deep-navy outline-none focus:border-soft-gold"
        >
          <option value="">All sources</option>
          <option value="newsletter">Newsletter</option>
          <option value="claiming">Claiming</option>
        </select>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="border border-light-grey rounded-lg px-3 py-1.5 font-body text-[13px] text-deep-navy outline-none focus:border-soft-gold"
        >
          <option value="">All statuses</option>
          <option value="new">New</option>
          <option value="contacted">Contacted</option>
          <option value="converted">Converted</option>
          <option value="dismissed">Dismissed</option>
        </select>
        <span className="font-body text-[13px] text-cool-grey ml-auto">{total} entries</span>
        <button
          onClick={exportCsv}
          className="font-body text-[12px] text-soft-gold border border-soft-gold/30 rounded-lg px-3 py-1.5 hover:bg-soft-gold/5 transition-colors"
        >
          Export CSV
        </button>
        <button
          onClick={load}
          className="font-body text-[12px] text-cool-grey border border-light-grey rounded-lg px-3 py-1.5 hover:bg-warm-cream transition-colors"
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
        </div>
      ) : entries.length === 0 ? (
        <p className="font-body text-[14px] text-cool-grey text-center py-12">No entries found</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-light-grey">
          <table className="w-full min-w-[700px]">
            <thead>
              <tr className="border-b border-light-grey bg-warm-cream/50">
                {['Created', 'Email', 'EIN', 'Source', 'Status', 'Notes', ''].map(h => (
                  <th key={h} className="px-4 py-3 text-left font-body text-[11px] font-medium tracking-[0.06em] text-cool-grey uppercase">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {entries.map(entry => (
                <tr key={entry.id} className="border-b border-light-grey/60 hover:bg-warm-cream/30 transition-colors">
                  <td className="px-4 py-3 font-body text-[12px] text-cool-grey whitespace-nowrap">
                    {relativeDate(entry.created_at)}
                  </td>
                  <td className="px-4 py-3 font-body text-[13px] text-deep-navy">{entry.email}</td>
                  <td className="px-4 py-3 font-body text-[12px] text-cool-grey">{entry.ein ?? '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`font-body text-[11px] px-2 py-0.5 rounded-full ${entry.source === 'claiming' ? 'bg-purple-100 text-purple-700' : 'bg-sky-100 text-sky-700'}`}>
                      {entry.source}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => cycleStatus(entry)}
                      title="Click to advance status"
                      className={`font-body text-[11px] px-2 py-0.5 rounded-full cursor-pointer transition-opacity hover:opacity-75 ${STATUS_COLOR[entry.status]}`}
                    >
                      {entry.status}
                    </button>
                  </td>
                  <td className="px-4 py-3 min-w-[160px]">
                    {editingNote?.id === entry.id ? (
                      <input
                        autoFocus
                        value={editingNote.val}
                        onChange={e => setEditingNote({ id: entry.id, val: e.target.value })}
                        onBlur={() => saveNote(entry.id, editingNote.val)}
                        onKeyDown={e => { if (e.key === 'Enter') saveNote(entry.id, editingNote.val) }}
                        className="w-full border-b border-soft-gold outline-none font-body text-[12px] text-deep-navy bg-transparent"
                      />
                    ) : (
                      <button
                        onClick={() => setEditingNote({ id: entry.id, val: entry.notes ?? '' })}
                        className="text-left font-body text-[12px] text-cool-grey hover:text-deep-navy transition-colors group flex items-center gap-1.5"
                      >
                        <span>{entry.notes || <span className="italic opacity-50">add note</span>}</span>
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0 opacity-0 group-hover:opacity-60">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="m18.5 2.5 2 2-9.5 9.5H9v-2l9.5-9.5z"/>
                        </svg>
                      </button>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => remove(entry.id)}
                      title="Delete"
                      className="text-cool-grey hover:text-red-500 transition-colors"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6"/><path d="m19 6-.867 14.142A2 2 0 0 1 16.138 22H7.862a2 2 0 0 1-1.995-1.858L5 6"/><path d="m10 11 0 6"/><path d="m14 11 0 6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
                      </svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ─── Pipeline tab ─────────────────────────────────────────────────────────────

function PipelineTab({ adminKey }: { adminKey: string }) {
  const [orgs, setOrgs]         = useState<ApiOrganization[]>([])
  const [waitlistEins, setWaitlistEins] = useState<Set<string>>(new Set())
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    async function load() {
      const [orgRes, waitlistRes] = await Promise.all([
        getOrganizations({ min_tier: 'Lantern', per_page: 50, sort: 'ntee1_percentile' }),
        getAdminWaitlist(adminKey, { source: 'claiming' }).catch(() => ({ entries: [], total: 0 })),
      ])
      setOrgs(orgRes.organizations)
      setWaitlistEins(new Set(
        waitlistRes.entries.map(e => e.ein).filter(Boolean) as string[]
      ))
      setLoading(false)
    }
    load()
  }, [adminKey])

  function formatRevenue(n: number | null): string {
    if (!n) return '—'
    if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
    if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
    if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`
    return `$${n}`
  }

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
      </div>
    )
  }

  return (
    <div>
      <p className="font-body text-[13px] text-cool-grey mb-5">
        Top 50 Beacon and Lantern organizations, outreach targets. "In Waitlist" means they submitted a claiming request.
      </p>
      <div className="overflow-x-auto rounded-xl border border-light-grey">
        <table className="w-full min-w-[600px]">
          <thead>
            <tr className="border-b border-light-grey bg-warm-cream/50">
              {['Organization', 'EIN', 'Location', 'Revenue', ''].map(h => (
                <th key={h} className="px-4 py-3 text-left font-body text-[11px] font-medium tracking-[0.06em] text-cool-grey uppercase">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {orgs.map(org => {
              const tier = getTierFromOrg(org)
              const inWaitlist = waitlistEins.has(org.EIN)
              return (
                <tr key={org.EIN} className="border-b border-light-grey/60 hover:bg-warm-cream/30 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <LampMark tier={tier} size="xs" />
                      <a
                        href={`/org/${org.EIN}`}
                        target="_blank"
                        rel="noreferrer"
                        className="font-body text-[13px] font-medium text-deep-navy hover:text-soft-gold transition-colors line-clamp-1"
                      >
                        {org.organization_name}
                      </a>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-body text-[12px] text-cool-grey">{formatEIN(org.EIN)}</td>
                  <td className="px-4 py-3 font-body text-[12px] text-cool-grey">
                    {[org.CITY, org.STATE].filter(Boolean).join(', ') || '—'}
                  </td>
                  <td className="px-4 py-3 font-body text-[12px] text-cool-grey">
                    {formatRevenue(org.total_revenue)}
                  </td>
                  <td className="px-4 py-3">
                    {inWaitlist && (
                      <span className="font-body text-[11px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
                        In Waitlist
                      </span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

type Tab = 'claims' | 'waitlist' | 'pipeline'

export default function AdminPage() {
  const [adminKey, setAdminKey] = useState('')
  const [tab, setTab] = useState<Tab>('claims')
  const [invalidKey, setInvalidKey] = useState(false)

  async function handleKey(key: string) {
    // Accept any non-empty key (API validation removed for dev)
    if (key.trim().length > 0) {
      setAdminKey(key)
      setInvalidKey(false)
    } else {
      setInvalidKey(true)
    }
  }

  if (!adminKey) {
    return (
      <>
        <KeyGate onKey={handleKey} />
        {invalidKey && (
          <p className="fixed bottom-6 left-1/2 -translate-x-1/2 font-body text-[13px] text-red-500 bg-white shadow-lg rounded-full px-4 py-2">
            Invalid key. Try again
          </p>
        )}
      </>
    )
  }

  return (
    <div className="min-h-[100dvh] bg-[#F8F6F3]">
      {/* Header */}
      <div className="bg-deep-navy px-6 lg:px-12 py-4 flex items-center justify-between">
        <span className="font-display italic text-[18px] text-warm-cream tracking-[-0.02em]">Daanaa Admin</span>
        <button
          onClick={() => setAdminKey('')}
          className="font-body text-[12px] text-muted-cream hover:text-muted-cream transition-colors"
        >
          Sign out
        </button>
      </div>

      {/* Tab bar */}
      <div className="bg-white border-b border-light-grey px-6 lg:px-12 flex gap-6">
        {(['claims', 'waitlist', 'pipeline'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`font-body text-[14px] py-3.5 border-b-2 transition-colors capitalize ${
              tab === t
                ? 'border-soft-gold text-deep-navy font-medium'
                : 'border-transparent text-cool-grey hover:text-deep-navy'
            }`}
          >
            {t === 'claims' ? 'Claims' : t === 'waitlist' ? 'Waitlist' : 'Nonprofit Pipeline'}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-8">
        {tab === 'claims'    && <ClaimsTab    adminKey={adminKey} />}
        {tab === 'waitlist'  && <WaitlistTab  adminKey={adminKey} />}
        {tab === 'pipeline'  && <PipelineTab  adminKey={adminKey} />}
      </div>
    </div>
  )
}
