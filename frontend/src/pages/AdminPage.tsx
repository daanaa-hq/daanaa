import { useState, useEffect, useCallback } from 'react'
import {
  getAdminWaitlist, updateWaitlistEntry, deleteWaitlistEntry,
  getOrganizations,
  type WaitlistEntry, type ApiOrganization,
} from '../data/api'
import LampMark from '../components/LampMark'
import { getTierFromOrg } from '../components/TrustBadge'

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
        <h1 className="font-display text-[22px] text-deep-navy mb-1">MERIT Admin</h1>
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
        getOrganizations({ min_merit_tier: 'Lantern', per_page: 50, sort: 'ntee1_percentile' }),
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
                  <td className="px-4 py-3 font-body text-[12px] text-cool-grey">{org.EIN}</td>
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

type Tab = 'waitlist' | 'pipeline'

export default function AdminPage() {
  const [adminKey, setAdminKey] = useState('')
  const [tab, setTab] = useState<Tab>('waitlist')
  const [invalidKey, setInvalidKey] = useState(false)

  async function handleKey(key: string) {
    try {
      await getAdminWaitlist(key, {})
      setAdminKey(key)
      setInvalidKey(false)
    } catch {
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
        <span className="font-display italic text-[18px] text-warm-cream tracking-[-0.02em]">MERIT Admin</span>
        <button
          onClick={() => setAdminKey('')}
          className="font-body text-[12px] text-muted-cream/60 hover:text-muted-cream transition-colors"
        >
          Sign out
        </button>
      </div>

      {/* Tab bar */}
      <div className="bg-white border-b border-light-grey px-6 lg:px-12 flex gap-6">
        {(['waitlist', 'pipeline'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`font-body text-[14px] py-3.5 border-b-2 transition-colors capitalize ${
              tab === t
                ? 'border-soft-gold text-deep-navy font-medium'
                : 'border-transparent text-cool-grey hover:text-deep-navy'
            }`}
          >
            {t === 'waitlist' ? 'Waitlist' : 'Nonprofit Pipeline'}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="max-w-[1200px] mx-auto px-6 lg:px-12 py-8">
        {tab === 'waitlist'  && <WaitlistTab  adminKey={adminKey} />}
        {tab === 'pipeline'  && <PipelineTab  adminKey={adminKey} />}
      </div>
    </div>
  )
}
