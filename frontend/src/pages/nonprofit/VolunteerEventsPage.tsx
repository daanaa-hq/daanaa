import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { usePageMeta } from '../../hooks/usePageMeta'
import { API_BASE } from '../../data/api'

interface VolunteerEvent {
  id: number
  ein: string
  title: string
  event_date: string
  location_city: string | null
  location_state: string | null
  status: string
  short_id: string | null
  signup_count: number
  co_org_eins?: string | null
}

const TASK_TYPES = ['volunteer', 'marshal', 'registration', 'setup', 'cleanup', 'hospitality', 'tech_support', 'mentor', 'coordinator', 'other']

function CreateEventForm({ ein, idToken, onCreated }: { ein: string; idToken: string; onCreated: () => void }) {
  const [title, setTitle] = useState('')
  const [eventDate, setEventDate] = useState('')
  const [city, setCity] = useState('')
  const [state, setState] = useState('')
  const [coOrgEins, setCoOrgEins] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [open, setOpen] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!title.trim() || !eventDate) {
      setError('Event name and date are required.')
      return
    }
    setSubmitting(true)
    try {
      const coEins = coOrgEins.split(',').map(s => s.replace(/\D/g, '')).filter(Boolean)
      const res = await fetch(`${API_BASE}/api/portal/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${idToken}` },
        body: JSON.stringify({
          ein,
          title: title.trim(),
          event_date: eventDate,
          location_city: city.trim() || undefined,
          location_state: state.trim().toUpperCase() || undefined,
          event_type: 'volunteer',
          co_org_eins: coEins.length ? coEins : undefined,
        }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.error || 'Failed to create event')
      }
      setTitle(''); setEventDate(''); setCity(''); setState(''); setCoOrgEins('')
      setOpen(false)
      onCreated()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create event')
    } finally {
      setSubmitting(false)
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="px-5 py-3 rounded-xl bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors"
      >
        + Create event
      </button>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-light-grey p-6 space-y-4">
      <h3 className="font-body text-[15px] font-semibold text-deep-navy">New volunteer event</h3>
      {error && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 font-body text-[13px]">{error}</div>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block font-body text-[12px] font-semibold text-deep-navy mb-1">Event name</label>
          <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Fall Golf Tournament"
            className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-[14px]" />
        </div>
        <div>
          <label className="block font-body text-[12px] font-semibold text-deep-navy mb-1">Date</label>
          <input type="date" value={eventDate} onChange={e => setEventDate(e.target.value)}
            className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-[14px]" />
        </div>
        <div>
          <label className="block font-body text-[12px] font-semibold text-deep-navy mb-1">City</label>
          <input value={city} onChange={e => setCity(e.target.value)} placeholder="Austin"
            className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-[14px]" />
        </div>
        <div>
          <label className="block font-body text-[12px] font-semibold text-deep-navy mb-1">State</label>
          <input value={state} onChange={e => setState(e.target.value)} placeholder="TX" maxLength={2}
            className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-[14px]" />
        </div>
        <div className="md:col-span-2">
          <label className="block font-body text-[12px] font-semibold text-deep-navy mb-1">
            Co-hosting nonprofits (optional, comma-separated EINs)
          </label>
          <input value={coOrgEins} onChange={e => setCoOrgEins(e.target.value)} placeholder="123456789, 987654321"
            className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-[14px]" />
          <p className="font-body text-[11px] text-cool-grey mt-1">
            Volunteers at coalition events pick their org(s) from a dropdown and log hours once.
          </p>
        </div>
      </div>
      <div className="flex gap-3">
        <button type="submit" disabled={submitting}
          className="px-5 py-2.5 rounded-xl bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold disabled:opacity-50 transition-colors">
          {submitting ? 'Creating...' : 'Create event'}
        </button>
        <button type="button" onClick={() => setOpen(false)}
          className="px-5 py-2.5 rounded-xl border border-light-grey text-deep-navy font-body text-[14px] font-medium hover:border-soft-gold/40 transition-colors">
          Cancel
        </button>
      </div>
    </form>
  )
}

function EventCard({ event }: { event: VolunteerEvent }) {
  const [copied, setCopied] = useState(false)
  const shortUrl = event.short_id ? `https://daanaa.org/e/${event.short_id}/log-hours` : null

  const copy = async () => {
    if (!shortUrl) return
    try {
      await navigator.clipboard.writeText(shortUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch { /* clipboard denied */ }
  }

  return (
    <div className="bg-white rounded-2xl border border-light-grey p-6">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div>
          <h3 className="font-body text-[15px] font-semibold text-deep-navy">{event.title}</h3>
          <p className="font-body text-[13px] text-cool-grey mt-0.5">
            {event.event_date}
            {(event.location_city || event.location_state) && ` · ${[event.location_city, event.location_state].filter(Boolean).join(', ')}`}
          </p>
        </div>
        <span className={`px-2.5 py-0.5 rounded-full font-body text-[11px] font-semibold border ${
          event.status === 'active' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-light-grey text-cool-grey border-light-grey'
        }`}>
          {event.status}
        </span>
      </div>

      {shortUrl && (
        <div className="flex flex-wrap items-center gap-3 mt-4 pt-4 border-t border-light-grey">
          <img
            src={`${API_BASE}/api/events/${event.id}/qr.png`}
            alt="Event QR code"
            className="w-20 h-20 rounded-lg border border-light-grey"
          />
          <div className="flex-1 min-w-0">
            <p className="font-body text-[12px] text-cool-grey mb-1">Volunteer hour-logging link</p>
            <div className="flex items-center gap-2">
              <code className="font-body text-[12px] bg-light-grey/40 px-2 py-1 rounded truncate">{shortUrl}</code>
              <button onClick={copy} className="shrink-0 px-3 py-1 rounded-lg border border-light-grey font-body text-[12px] hover:border-soft-gold/40 transition-colors">
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <p className="font-body text-[11px] text-cool-grey mt-2">
              Print the QR code at your event. Volunteers scan it, log their hours, and you approve them here afterward.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default function VolunteerEventsPage() {
  const { ein } = useParams<{ ein: string }>()
  const navigate = useNavigate()
  const { getIdToken } = useAuth()
  usePageMeta('Volunteer Events | Daanaa', 'Create events, generate QR codes, and track volunteer hours.')

  const [events, setEvents] = useState<VolunteerEvent[]>([])
  const [idToken, setIdToken] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchEvents = useCallback(async () => {
    if (!ein) return
    try {
      const token = await getIdToken()
      if (!token) {
        navigate('/nonprofit/login', { replace: true })
        return
      }
      setIdToken(token)
      const res = await fetch(`${API_BASE}/api/portal/events?ein=${encodeURIComponent(ein)}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Failed to load events')
      const data = await res.json()
      setEvents(data.events || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }, [ein, getIdToken, navigate])

  useEffect(() => { fetchEvents() }, [fetchEvents])

  if (!ein) return null

  return (
    <div className="min-h-screen bg-warm-cream">
      <div className="bg-deep-navy py-8 px-6">
        <div className="max-w-[900px] mx-auto">
          <Link to="/nonprofit/my-orgs" className="font-body text-[13px] text-muted-cream hover:text-warm-cream">← My organizations</Link>
          <h1 className="font-display italic text-warm-cream mt-3 text-[36px]">Volunteer Events</h1>
          <p className="font-body text-muted-cream mt-2 text-[15px]">
            Create an event, print the QR code, and volunteers log their own hours. You approve them afterward — no manual entry needed.
          </p>
        </div>
      </div>

      <div className="max-w-[900px] mx-auto px-6 py-10 space-y-6">
        <div className="flex justify-between items-center">
          <Link to={`/nonprofit/impact/${ein}`} className="font-body text-[13px] text-link-gold hover:underline">
            View yearly impact →
          </Link>
        </div>

        <CreateEventForm ein={ein} idToken={idToken} onCreated={fetchEvents} />

        {error && <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 font-body text-[14px]">{error}</div>}

        {loading ? (
          <p className="font-body text-cool-grey text-[14px]">Loading events...</p>
        ) : events.length === 0 ? (
          <p className="font-body text-cool-grey text-[14px]">No events yet. Create one above to get a QR code volunteers can scan to log hours.</p>
        ) : (
          <div className="space-y-4">
            {events.map(ev => <EventCard key={ev.id} event={ev} />)}
          </div>
        )}
      </div>
    </div>
  )
}
