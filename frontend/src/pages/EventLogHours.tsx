import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useWallet } from '../contexts/WalletContext'
import { API_BASE } from '../data/api'

interface EventOrg {
  ein: string
  name: string
}

interface EventInfo {
  event_id: number
  title: string
  event_date: string
  location_city: string | null
  location_state: string | null
  orgs: EventOrg[]
  task_types: string[]
}

interface OrgAllocation {
  ein: string
  checked: boolean
  hours: string
  task_type: string
}

const TASK_LABELS: Record<string, string> = {
  volunteer: 'General volunteer', marshal: 'Marshal', registration: 'Registration',
  setup: 'Setup', cleanup: 'Cleanup', hospitality: 'Hospitality',
  tech_support: 'Tech support', mentor: 'Mentor', coordinator: 'Coordinator', other: 'Other',
}

export default function EventLogHours() {
  const { shortId } = useParams<{ shortId: string }>()
  usePageMeta('Log Volunteer Hours | Daanaa', 'Log the hours you volunteered at this event.')
  const { logVolunteerHours } = useWallet()

  const [info, setInfo] = useState<EventInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [addedToWallet, setAddedToWallet] = useState<Set<string>>(new Set())
  // Server submission ids per org EIN — links each wallet record to its
  // volunteer_hours row so approval status can be reflected later.
  const [submissionByEin, setSubmissionByEin] = useState<Record<string, string>>({})

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [notes, setNotes] = useState('')
  const [allocations, setAllocations] = useState<OrgAllocation[]>([])

  useEffect(() => {
    if (!shortId) return
    fetch(`${API_BASE}/api/events/${shortId}/log-hours-info`)
      .then(async res => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(body.error || 'Event not found')
        }
        return res.json()
      })
      .then((data: EventInfo) => {
        setInfo(data)
        setAllocations(
          data.orgs.map((org, i) => ({
            ein: org.ein,
            checked: data.orgs.length === 1 || i === 0,
            hours: '',
            task_type: 'volunteer',
          }))
        )
      })
      .catch(err => setError(err instanceof Error ? err.message : 'Could not load event'))
      .finally(() => setLoading(false))
  }, [shortId])

  function updateAllocation(ein: string, patch: Partial<OrgAllocation>) {
    setAllocations(prev => prev.map(a => (a.ein === ein ? { ...a, ...patch } : a)))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!name.trim() || !email.trim()) {
      setError('Name and email are required.')
      return
    }
    const selected = allocations.filter(a => a.checked)
    if (selected.length === 0) {
      setError('Select at least one organization.')
      return
    }
    for (const a of selected) {
      const h = parseFloat(a.hours)
      if (!h || h < 0.25 || h > 24) {
        setError('Enter valid hours (0.25–24) for each selected organization.')
        return
      }
    }

    setSubmitting(true)
    try {
      const res = await fetch(`${API_BASE}/api/events/${shortId}/log-hours`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          volunteer_name: name.trim(),
          volunteer_email: email.trim(),
          orgs: selected.map(a => ({ ein: a.ein, hours: parseFloat(a.hours), task_type: a.task_type })),
          notes: notes.trim() || undefined,
        }),
      })
      const body = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(body.error || 'Failed to submit hours')
      const byEin: Record<string, string> = {}
      for (const s of body.submissions ?? []) {
        if (s.ein && s.submission_id) byEin[s.ein] = s.submission_id
      }
      setSubmissionByEin(byEin)
      setSubmitted(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit hours')
    } finally {
      setSubmitting(false)
    }
  }

  function addToWallet(ein: string, hours: number) {
    // Date is the event's SERVICE date, not today. The link marks this entry
    // "Submitted for review" and stops the wallet from creating its own
    // impact record — the server creates the one aggregate record if and when
    // the nonprofit approves.
    const submissionId = submissionByEin[ein]
    logVolunteerHours(
      ein, hours, info?.event_date ?? new Date().toISOString().slice(0, 10),
      notes.trim() || undefined, false,
      submissionId ? { submissionId, eventId: info?.event_id } : undefined,
    )
    setAddedToWallet(prev => new Set(prev).add(ein))
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-cream">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-deep-navy" />
      </div>
    )
  }

  if (error && !info) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-cream px-6">
        <div className="max-w-md text-center bg-white p-8 rounded-2xl shadow-sm">
          <h1 className="font-display text-2xl text-deep-navy mb-3">Can't find this event</h1>
          <p className="font-body text-body text-cool-grey">{error}</p>
        </div>
      </div>
    )
  }

  if (submitted) {
    const selected = allocations.filter(a => a.checked)
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-cream px-6">
        <div className="max-w-md w-full text-center bg-white p-8 rounded-2xl shadow-sm">
          <div className="text-5xl mb-4">✓</div>
          <h1 className="font-display text-2xl text-deep-navy mb-2">Thanks, {name.split(' ')[0]}!</h1>
          <p className="font-body text-body text-cool-grey mb-6">
            Your hours were submitted. The organization{selected.length > 1 ? 's' : ''} will review and approve them.
          </p>

          <div className="space-y-3 mb-6">
            {selected.map(a => {
              const org = info?.orgs.find(o => o.ein === a.ein)
              const already = addedToWallet.has(a.ein)
              return (
                <div key={a.ein} className="flex items-center justify-between gap-3 p-3 bg-light-grey/30 rounded-xl">
                  <div className="text-left">
                    <p className="font-body text-small font-semibold text-deep-navy">{org?.name}</p>
                    <p className="font-body text-caption text-cool-grey">
                      {a.hours} hours · {info?.event_date}
                      <span className="ml-1.5 inline-block px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 text-micro font-semibold align-middle">
                        Pending review
                      </span>
                    </p>
                  </div>
                  <button
                    onClick={() => addToWallet(a.ein, parseFloat(a.hours))}
                    disabled={already}
                    className="shrink-0 px-3 py-1.5 rounded-lg bg-soft-gold text-deep-navy font-body text-caption font-semibold hover:bg-bright-gold disabled:opacity-50 disabled:bg-emerald-100 disabled:text-emerald-700 transition-colors"
                  >
                    {already ? 'Added ✓' : 'Track in Wallet'}
                  </button>
                </div>
              )
            })}
          </div>

          <p className="font-body text-label text-cool-grey">
            Your Giving Wallet keeps a private record of every hour you volunteer.
            Tracked hours show as "Submitted" until the organization reviews them —
            your wallet updates automatically once they decide.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-warm-cream">
      <div className="bg-deep-navy py-8 px-6">
        <div className="max-w-[560px] mx-auto">
          <h1 className="font-display italic text-warm-cream text-headline-lg leading-tight">{info?.title}</h1>
          <p className="font-body text-muted-cream mt-2 text-body">
            {info?.event_date}
            {(info?.location_city || info?.location_state) &&
              ` · ${[info?.location_city, info?.location_state].filter(Boolean).join(', ')}`}
          </p>
        </div>
      </div>

      <div className="max-w-[560px] mx-auto px-6 py-10">
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm p-6 space-y-5">
          <h2 className="font-body text-body font-semibold text-deep-navy uppercase tracking-wide">Log your hours</h2>

          {error && <div className="p-3 bg-destructive/5 border border-destructive/20 rounded-lg text-destructive font-body text-small">{error}</div>}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block font-body text-caption font-semibold text-deep-navy mb-1">Your name</label>
              <input value={name} onChange={e => setName(e.target.value)}
                className="w-full px-3 py-2.5 border border-light-grey rounded-lg font-body text-body" required />
            </div>
            <div>
              <label className="block font-body text-caption font-semibold text-deep-navy mb-1">Your email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                className="w-full px-3 py-2.5 border border-light-grey rounded-lg font-body text-body" required />
            </div>
          </div>

          <div className="space-y-3">
            <label className="block font-body text-caption font-semibold text-deep-navy">
              {info && info.orgs.length > 1 ? 'Which organization(s) did you help?' : 'Hours'}
            </label>
            {allocations.map(a => {
              const org = info?.orgs.find(o => o.ein === a.ein)
              return (
                <div key={a.ein} className="border border-light-grey rounded-xl p-4">
                  {info && info.orgs.length > 1 && (
                    <label className="flex items-center gap-2 mb-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={a.checked}
                        onChange={e => updateAllocation(a.ein, { checked: e.target.checked })}
                        className="w-4 h-4"
                      />
                      <span className="font-body text-body font-semibold text-deep-navy">{org?.name}</span>
                    </label>
                  )}
                  {a.checked && (
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block font-body text-label text-cool-grey mb-1">Hours</label>
                        <input
                          type="number" step="0.25" min="0.25" max="24"
                          value={a.hours}
                          onChange={e => updateAllocation(a.ein, { hours: e.target.value })}
                          placeholder="4"
                          className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-body"
                        />
                      </div>
                      <div>
                        <label className="block font-body text-label text-cool-grey mb-1">Role</label>
                        <select
                          value={a.task_type}
                          onChange={e => updateAllocation(a.ein, { task_type: e.target.value })}
                          className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-body"
                        >
                          {(info?.task_types || Object.keys(TASK_LABELS)).map(t => (
                            <option key={t} value={t}>{TASK_LABELS[t] || t}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          <div>
            <label className="block font-body text-caption font-semibold text-deep-navy mb-1">Notes (optional)</label>
            <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2}
              placeholder="What did you do?"
              className="w-full px-3 py-2.5 border border-light-grey rounded-lg font-body text-body" />
          </div>

          <button type="submit" disabled={submitting}
            className="w-full py-3 rounded-xl bg-soft-gold text-deep-navy font-body text-body font-semibold hover:bg-bright-gold disabled:opacity-50 transition-colors">
            {submitting ? 'Submitting...' : 'Submit hours'}
          </button>

          <p className="font-body text-label text-cool-grey text-center">
            The organization will review your hours before they're counted. No account needed.
          </p>
        </form>
      </div>
    </div>
  )
}
