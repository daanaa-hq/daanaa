import { useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { searchVolunteerEvents, type VolunteerEvent, type EventType } from '../data/api'

const US_STATES = [
  ['AL','Alabama'],['AK','Alaska'],['AZ','Arizona'],['AR','Arkansas'],['CA','California'],
  ['CO','Colorado'],['CT','Connecticut'],['DE','Delaware'],['FL','Florida'],['GA','Georgia'],
  ['HI','Hawaii'],['ID','Idaho'],['IL','Illinois'],['IN','Indiana'],['IA','Iowa'],
  ['KS','Kansas'],['KY','Kentucky'],['LA','Louisiana'],['ME','Maine'],['MD','Maryland'],
  ['MA','Massachusetts'],['MI','Michigan'],['MN','Minnesota'],['MS','Mississippi'],['MO','Missouri'],
  ['MT','Montana'],['NE','Nebraska'],['NV','Nevada'],['NH','New Hampshire'],['NJ','New Jersey'],
  ['NM','New Mexico'],['NY','New York'],['NC','North Carolina'],['ND','North Dakota'],['OH','Ohio'],
  ['OK','Oklahoma'],['OR','Oregon'],['PA','Pennsylvania'],['RI','Rhode Island'],['SC','South Carolina'],
  ['SD','South Dakota'],['TN','Tennessee'],['TX','Texas'],['UT','Utah'],['VT','Vermont'],
  ['VA','Virginia'],['WA','Washington'],['WV','West Virginia'],['WI','Wisconsin'],['WY','Wyoming'],
  ['DC','Washington DC'],
]

function formatDate(d: string) {
  const [y, m, day] = d.split('-')
  return new Date(Number(y), Number(m) - 1, Number(day)).toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
  })
}

function formatTime(t: string | null) {
  if (!t) return ''
  const [h, min] = t.split(':').map(Number)
  const ampm = h >= 12 ? 'pm' : 'am'
  const hour = h % 12 || 12
  return `${hour}:${String(min).padStart(2, '0')} ${ampm}`
}

const EVENT_TYPE_LABELS: Record<string, string> = {
  volunteer:  'Volunteer',
  community:  'Community',
  fundraiser: 'Fundraiser',
  networking: 'Networking',
}
const EVENT_TYPE_COLORS: Record<string, string> = {
  volunteer:  'bg-green-50 text-green-700',
  community:  'bg-soft-gold/10 text-soft-gold',
  fundraiser: 'bg-blue-50 text-blue-600',
  networking: 'bg-purple-50 text-purple-600',
}

function EventCard({ event }: { event: VolunteerEvent }) {
  const timeStr = event.start_time
    ? `${formatTime(event.start_time)}${event.end_time ? ` – ${formatTime(event.end_time)}` : ''}`
    : null

  const location = event.is_virtual
    ? 'Virtual'
    : [event.location_city, event.location_state].filter(Boolean).join(', ') || null

  const typeLabel = EVENT_TYPE_LABELS[event.event_type] || 'Event'
  const typeColor = EVENT_TYPE_COLORS[event.event_type] || 'bg-light-cream text-cool-grey'

  return (
    <Link
      to={`/events/${event.id}`}
      className="bg-white rounded-2xl border border-light-cream p-5 flex flex-col gap-3 hover:border-soft-gold/40 hover:shadow-sm transition-all"
    >
      <div>
        <div className="flex items-start justify-between gap-2 mb-1">
          <div className="flex gap-1.5 flex-wrap">
            <span className={`inline-block px-2 py-0.5 rounded-full font-body text-[10px] font-semibold tracking-[0.06em] uppercase ${typeColor}`}>
              {typeLabel}
            </span>
            {event.is_virtual && (
              <span className="inline-block px-2 py-0.5 rounded-full font-body text-[10px] font-semibold tracking-[0.06em] uppercase bg-blue-50 text-blue-600">
                Virtual
              </span>
            )}
            {event.min_age && event.min_age > 0 && (
              <span className="inline-block px-2 py-0.5 rounded-full font-body text-[10px] font-semibold tracking-[0.06em] uppercase bg-orange-50 text-orange-600">
                {event.min_age}+
              </span>
            )}
          </div>
          {event.signup_count > 0 && (
            <span className="font-body text-[11px] text-cool-grey shrink-0">
              {event.signup_count} going
            </span>
          )}
        </div>
        <h3 className="font-display italic text-deep-navy text-[18px] leading-tight">{event.title}</h3>
        {event.org_name && (
          <span className="font-body text-[13px] text-deep-navy font-medium mt-0.5 block">
            {event.org_name}
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-1">
        <span className="font-body text-[13px] text-deep-navy font-medium">
          {formatDate(event.event_date)}
        </span>
        {timeStr && (
          <span className="font-body text-[13px] text-cool-grey">{timeStr}</span>
        )}
        {location && !event.is_virtual && (
          <span className="font-body text-[13px] text-cool-grey">{location}</span>
        )}
      </div>

      {(event.description || event.org_mission) && (
        <p className="font-body text-[14px] text-cool-grey leading-[1.6] line-clamp-2">
          {event.description || event.org_mission}
        </p>
      )}

      <div className="mt-auto pt-1">
        <span className="inline-flex items-center gap-1 font-body text-[13px] text-soft-gold font-semibold">
          View event
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </span>
      </div>
    </Link>
  )
}

export default function VolunteerSearch() {
  usePageMeta(
    'Volunteer Opportunities — Daanaa',
    'Find volunteer events near you. Browse opportunities from verified nonprofits by location and cause.',
  )

  const [zip, setZip]           = useState('')
  const [city, setCity]         = useState('')
  const [state, setState]       = useState('')
  const [virtual, setVirtual]   = useState(false)
  const [eventType, setEventType] = useState<EventType | ''>('')
  const [searched, setSearched] = useState(false)
  const [loading, setLoading]   = useState(false)
  const [events, setEvents]     = useState<VolunteerEvent[]>([])
  const [error, setError]       = useState(false)

  const search = useCallback(async () => {
    setLoading(true)
    setError(false)
    setSearched(true)
    try {
      const result = await searchVolunteerEvents({
        zip, city, state, virtual,
        event_type: eventType || undefined,
      })
      setEvents(result.events)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [zip, city, state, virtual, eventType])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    search()
  }

  return (
    <div className="min-h-[100dvh] bg-warm-cream pt-[72px]">
      {/* Header */}
      <div className="bg-deep-navy pt-12 pb-10">
        <div className="max-w-[900px] mx-auto px-6 md:px-12">
          <h1 className="font-display italic text-warm-cream leading-tight" style={{ fontSize: 'clamp(32px, 5vw, 52px)' }}>
            Volunteer near you
          </h1>
          <p className="font-body text-[16px] text-muted-cream mt-2 max-w-lg leading-[1.7]">
            Opportunities from nonprofits that have claimed their Daanaa page. Search by zip code or city and sign up directly with the organization.
          </p>
        </div>
      </div>

      <div className="max-w-[900px] mx-auto px-6 md:px-12 py-10">
        {/* Search form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-light-cream p-6 mb-8 flex flex-col gap-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block font-body text-[12px] font-medium text-deep-navy mb-1.5">
                Zip code
              </label>
              <input
                type="text"
                inputMode="numeric"
                maxLength={10}
                placeholder="e.g. 90210"
                value={zip}
                onChange={e => { setZip(e.target.value); setCity(''); setState('') }}
                className="w-full px-3 py-2.5 rounded-xl border border-light-cream font-body text-[14px] text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
              />
            </div>
            <div>
              <label className="block font-body text-[12px] font-medium text-deep-navy mb-1.5">
                City
              </label>
              <input
                type="text"
                placeholder="e.g. Austin"
                value={city}
                onChange={e => { setCity(e.target.value); setZip('') }}
                className="w-full px-3 py-2.5 rounded-xl border border-light-cream font-body text-[14px] text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
              />
            </div>
            <div>
              <label className="block font-body text-[12px] font-medium text-deep-navy mb-1.5">
                State
              </label>
              <select
                value={state}
                onChange={e => { setState(e.target.value); setZip('') }}
                className="w-full px-3 py-2.5 rounded-xl border border-light-cream font-body text-[14px] text-deep-navy focus:outline-none focus:border-soft-gold/60 bg-white"
              >
                <option value="">Any state</option>
                {US_STATES.map(([abbr, name]) => (
                  <option key={abbr} value={abbr}>{name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-4 flex-wrap">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={virtual}
                  onChange={e => setVirtual(e.target.checked)}
                  className="w-4 h-4 rounded border-light-cream accent-soft-gold"
                />
                <span className="font-body text-[14px] text-cool-grey">Virtual</span>
              </label>
              <select
                value={eventType}
                onChange={e => setEventType(e.target.value as EventType | '')}
                className="px-3 py-2 rounded-xl border border-light-cream font-body text-[13px] text-deep-navy bg-white focus:outline-none focus:border-soft-gold/60"
              >
                <option value="">All types</option>
                <option value="volunteer">Volunteer</option>
                <option value="community">Community</option>
                <option value="fundraiser">Fundraiser</option>
                <option value="networking">Networking</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 bg-soft-gold text-deep-navy rounded-xl font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors disabled:opacity-60"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </form>

        {/* Results */}
        {loading && (
          <div className="flex justify-center py-20">
            <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
          </div>
        )}

        {!loading && error && (
          <div className="text-center py-16">
            <p className="font-body text-[15px] text-cool-grey mb-4">Could not load events. Try again.</p>
            <button onClick={search} className="font-body text-[13px] text-soft-gold hover:underline">Retry</button>
          </div>
        )}

        {!loading && !error && searched && events.length === 0 && (
          <div className="text-center py-16">
            <p className="font-body text-[18px] text-deep-navy font-display italic mb-2">No events found</p>
            <p className="font-body text-[14px] text-cool-grey max-w-sm mx-auto leading-[1.7]">
              Try a different zip code or state. Events are added by verified nonprofits — if your local orgs aren't listed yet, they may not have claimed their page.
            </p>
            <Link
              to="/directory"
              className="mt-6 inline-block font-body text-[13px] text-soft-gold hover:text-bright-gold font-semibold"
            >
              Browse nonprofits in the directory →
            </Link>
          </div>
        )}

        {!loading && !error && !searched && (
          <div className="text-center py-12">
            <p className="font-body text-[15px] text-cool-grey">
              Enter a zip code or city above to find volunteer opportunities.
            </p>
            <p className="font-body text-[13px] text-cool-grey mt-2">
              Are you a nonprofit?{' '}
              <Link to="/for-nonprofits" className="text-soft-gold hover:text-bright-gold font-semibold">
                Claim your page
              </Link>{' '}
              to post events.
            </p>
          </div>
        )}

        {!loading && !error && events.length > 0 && (
          <>
            <p className="font-body text-[13px] text-cool-grey mb-5">
              {events.length} {events.length === 1 ? 'opportunity' : 'opportunities'} found
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {events.map(e => <EventCard key={e.id} event={e} />)}
            </div>
            <p className="mt-8 font-body text-[12px] text-muted-cream text-center leading-[1.6]">
              Are you a nonprofit?{' '}
              <Link to="/for-nonprofits" className="text-soft-gold hover:underline">Claim your page</Link>{' '}
              to post events. Your contact info is shared only with the event organizer.
            </p>
          </>
        )}
      </div>
    </div>
  )
}
