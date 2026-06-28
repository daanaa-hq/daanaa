import { useState, useEffect, useCallback } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import {
  getEventDetail,
  signupForEvent,
  cancelEventSignup,
  type VolunteerEvent,
  type EventAttendee,
} from '../data/api'
import { API_BASE } from '../data/api'

const EVENT_TYPE_LABELS: Record<string, string> = {
  volunteer:    'Volunteer',
  community:    'Community',
  fundraiser:   'Fundraiser',
  networking:   'Networking',
}

const EVENT_TYPE_COLORS: Record<string, string> = {
  volunteer:  'bg-green-50 text-green-700',
  community:  'bg-soft-gold/10 text-soft-gold',
  fundraiser: 'bg-blue-50 text-blue-600',
  networking: 'bg-purple-50 text-purple-600',
}

const AGE_GROUP_LABELS: Record<string, string> = {
  child:  'Child (under 13)',
  teen:   'Teen (13–17)',
  adult:  'Adult (18+)',
  senior: 'Senior (65+)',
}

function formatDate(d: string) {
  const [y, m, day] = d.split('-')
  return new Date(Number(y), Number(m) - 1, Number(day)).toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric', year: 'numeric',
  })
}

function formatTime(t: string | null) {
  if (!t) return ''
  const [h, min] = t.split(':').map(Number)
  const ampm = h >= 12 ? 'pm' : 'am'
  return `${h % 12 || 12}:${String(min).padStart(2, '0')} ${ampm}`
}

function ShareBar({ event }: { event: VolunteerEvent }) {
  const [copied, setCopied] = useState(false)
  const shortUrl = event.short_id
    ? `https://daanaa.org/e/${event.short_id}`
    : `https://daanaa.org/events/${event.id}`
  const pageUrl = `https://daanaa.org/events/${event.id}`

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(shortUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // clipboard denied — fallback to selection
    }
  }

  const nativeShare = async () => {
    try {
      await navigator.share({ title: event.title, url: shortUrl })
    } catch {
      copy()
    }
  }

  const emailHref = `mailto:?subject=${encodeURIComponent(event.title)}&body=${encodeURIComponent(
    `Thought you might want to join this:\n\n${event.title}\n${shortUrl}`
  )}`

  const smsHref = `sms:?body=${encodeURIComponent(`${event.title} — ${shortUrl}`)}`

  const calUrl = `${API_BASE}/api/events/${event.id}/calendar.ics`

  return (
    <div className="flex flex-wrap gap-2 mt-4">
      {/* Native share (mobile) or copy link (desktop) */}
      {'share' in navigator ? (
        <button
          onClick={nativeShare}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-light-cream font-body text-[13px] text-deep-navy hover:bg-soft-gold/8 transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
          </svg>
          Share
        </button>
      ) : (
        <button
          onClick={copy}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-light-cream font-body text-[13px] text-deep-navy hover:bg-soft-gold/8 transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
          </svg>
          {copied ? 'Copied!' : 'Copy link'}
        </button>
      )}

      {/* Email */}
      <a
        href={emailHref}
        className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-light-cream font-body text-[13px] text-deep-navy hover:bg-soft-gold/8 transition-colors"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
          <polyline points="22,6 12,13 2,6"/>
        </svg>
        Email
      </a>

      {/* Text / SMS */}
      <a
        href={smsHref}
        className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-light-cream font-body text-[13px] text-deep-navy hover:bg-soft-gold/8 transition-colors"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        Text
      </a>

      {/* Add to calendar */}
      <a
        href={calUrl}
        className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-light-cream font-body text-[13px] text-deep-navy hover:bg-soft-gold/8 transition-colors"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        Add to calendar
      </a>

      {/* QR code (download) */}
      <a
        href={`${API_BASE}/api/events/${event.id}/qr.png`}
        download={`event-${event.id}-qr.png`}
        className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-light-cream font-body text-[13px] text-deep-navy hover:bg-soft-gold/8 transition-colors"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
          <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
        </svg>
        QR code
      </a>

      {/* Short URL display */}
      <div className="ml-auto self-center font-body text-[11px] text-muted-cream select-all">
        {shortUrl.replace('https://', '')}
      </div>
    </div>
  )
}

type SignupStep = 'idle' | 'step1' | 'step2' | 'done' | 'cancelled'

function SignupForm({ event, onDone }: { event: VolunteerEvent; onDone: () => void }) {
  const [step, setStep]           = useState<SignupStep>('idle')
  const [contactName, setName]    = useState('')
  const [contactEmail, setEmail]  = useState('')
  const [attendees, setAttendees] = useState<EventAttendee[]>([])
  const [error, setError]         = useState('')
  const [bookingToken, setToken]  = useState('')
  const [cancelToken, setCancelTok] = useState<string | null>(null)

  const canSignup = event.status === 'active' && event.event_date >= new Date().toISOString().slice(0,10)

  const spotsLeft = event.capacity != null
    ? event.capacity - event.signup_count
    : null
  const full = spotsLeft !== null && spotsLeft <= 0

  const addAttendee = () => {
    setAttendees(prev => [...prev, { name: '', age_group: 'adult' }])
  }

  const updateAttendee = (i: number, field: keyof EventAttendee, value: string) => {
    setAttendees(prev => prev.map((a, idx) => idx === i ? { ...a, [field]: value } : a))
  }

  const removeAttendee = (i: number) => {
    setAttendees(prev => prev.filter((_, idx) => idx !== i))
  }

  const [submitting, setSubmitting] = useState(false)

  const submit = async () => {
    setError('')
    setSubmitting(true)
    try {
      const validAttendees = attendees.filter(a => a.name.trim())
      const result = await signupForEvent(event.id, {
        contact_name: contactName,
        contact_email: contactEmail,
        attendees: validAttendees.length ? validAttendees : undefined,
        idempotency_key: `${event.id}-${contactEmail}-${Date.now()}`,
      })
      setToken(result.booking_token)
      setStep('done')
      onDone()
    } catch (err: unknown) {
      const msg = (err as { message?: string })?.message || 'Could not complete signup. Please try again.'
      setError(msg)
      setStep('step2')
    } finally {
      setSubmitting(false)
    }
  }

  const cancelBooking = async () => {
    if (!cancelToken) return
    try {
      await cancelEventSignup(event.id, cancelToken)
      setStep('cancelled')
    } catch {
      setError('Could not cancel. Please contact events@daanaa.org.')
    }
  }

  if (!canSignup) {
    return (
      <div className="bg-light-cream rounded-2xl p-5 text-center">
        <p className="font-body text-[14px] text-cool-grey">
          {event.status === 'cancelled' ? 'This event has been cancelled.' :
           full ? 'This event is full.' : 'Signups are closed.'}
        </p>
      </div>
    )
  }

  if (step === 'done') {
    return (
      <div className="bg-white rounded-2xl border border-light-cream p-6 text-center">
        <div className="w-12 h-12 rounded-full bg-green-50 flex items-center justify-center mx-auto mb-3">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </div>
        <h3 className="font-display italic text-deep-navy text-[18px] mb-1">You're confirmed</h3>
        <p className="font-body text-[14px] text-cool-grey mb-4">
          Check your email for details and a cancellation link.
          {event.expected_hours && (
            <> This event earns up to <strong>{event.expected_hours}h</strong> for your Wallet.</>
          )}
        </p>
        <Link to="/wallet" className="font-body text-[13px] text-soft-gold hover:text-bright-gold font-semibold">
          Open Giving Wallet →
        </Link>
      </div>
    )
  }

  if (step === 'cancelled') {
    return (
      <div className="bg-light-cream rounded-2xl p-5 text-center">
        <p className="font-body text-[14px] text-cool-grey">Your signup has been cancelled.</p>
        <button onClick={() => { setStep('idle'); setName(''); setEmail(''); setAttendees([]) }}
          className="mt-3 font-body text-[13px] text-soft-gold hover:underline">
          Sign up again
        </button>
      </div>
    )
  }

  if (step === 'idle') {
    return (
      <div>
        {spotsLeft !== null && (
          <p className="font-body text-[12px] text-muted-cream mb-3">
            {spotsLeft} spot{spotsLeft !== 1 ? 's' : ''} remaining
          </p>
        )}
        <button
          onClick={() => setStep('step1')}
          className="w-full py-3 bg-soft-gold text-deep-navy rounded-xl font-body text-[15px] font-semibold hover:bg-bright-gold transition-colors"
        >
          Sign up — it's free
        </button>
        <p className="font-body text-[11px] text-muted-cream text-center mt-2">
          No account needed. Your contact info is shared only with the organizer.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-light-cream p-5 flex flex-col gap-4">
      <h3 className="font-display italic text-deep-navy text-[17px]">Sign up</h3>

      {error && (
        <div className="bg-red-50 border border-red-100 rounded-lg px-3 py-2 font-body text-[13px] text-red-700">
          {error}
        </div>
      )}

      {/* Step 1: Contact person */}
      <div className="flex flex-col gap-3">
        <div>
          <label className="block font-body text-[12px] font-medium text-deep-navy mb-1">Your name</label>
          <input
            type="text"
            autoFocus
            placeholder="First and last name"
            value={contactName}
            onChange={e => setName(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl border border-light-cream font-body text-[14px] text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
          />
        </div>
        <div>
          <label className="block font-body text-[12px] font-medium text-deep-navy mb-1">Email</label>
          <input
            type="email"
            placeholder="you@example.com"
            value={contactEmail}
            onChange={e => setEmail(e.target.value)}
            className="w-full px-3 py-2.5 rounded-xl border border-light-cream font-body text-[14px] text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
          />
          <p className="font-body text-[11px] text-muted-cream mt-1">
            Confirmation and cancellation link will be sent here.
          </p>
        </div>
      </div>

      {/* Step 2: Additional attendees */}
      {(step === 'step2' || attendees.length > 0) && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="font-body text-[13px] font-medium text-deep-navy">
              Additional attendees
            </span>
            <button
              onClick={addAttendee}
              className="font-body text-[12px] text-soft-gold hover:text-bright-gold font-semibold"
            >
              + Add person
            </button>
          </div>
          {attendees.map((a, i) => (
            <div key={i} className="flex gap-2 items-start">
              <input
                type="text"
                placeholder="Name"
                value={a.name}
                onChange={e => updateAttendee(i, 'name', e.target.value)}
                className="flex-1 px-3 py-2 rounded-xl border border-light-cream font-body text-[13px] text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
              />
              <select
                value={a.age_group}
                onChange={e => updateAttendee(i, 'age_group', e.target.value)}
                className="px-2 py-2 rounded-xl border border-light-cream font-body text-[12px] text-deep-navy bg-white focus:outline-none focus:border-soft-gold/60"
              >
                {Object.entries(AGE_GROUP_LABELS).map(([v, label]) => {
                  if (event.min_age && event.min_age >= 13 && v === 'child') return null
                  return <option key={v} value={v}>{label}</option>
                })}
              </select>
              <button
                onClick={() => removeAttendee(i)}
                className="p-2 text-muted-cream hover:text-cool-grey"
                aria-label="Remove"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Action row */}
      <div className="flex gap-2 pt-1">
        {step === 'step1' && (
          <>
            <button
              onClick={() => setStep('step2')}
              disabled={!contactName.trim() || !contactEmail.includes('@')}
              className="flex-1 py-2.5 bg-soft-gold text-deep-navy rounded-xl font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50"
            >
              {attendees.length ? `Continue (${attendees.length + 1} people)` : 'Continue'}
            </button>
            <button
              onClick={() => setStep('idle')}
              className="px-4 py-2.5 rounded-xl border border-light-cream font-body text-[13px] text-cool-grey hover:border-soft-gold/40 transition-colors"
            >
              Cancel
            </button>
          </>
        )}
        {step === 'step2' && (
          <>
            <button
              onClick={submit}
              disabled={submitting || !contactName.trim() || !contactEmail.includes('@')}
              className="flex-1 py-2.5 bg-soft-gold text-deep-navy rounded-xl font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50"
            >
              {submitting ? 'Signing up…' : `Confirm signup${attendees.length ? ` (${attendees.length + 1})` : ''}`}
            </button>
            <button
              onClick={() => setStep('step1')}
              disabled={submitting}
              className="px-4 py-2.5 rounded-xl border border-light-cream font-body text-[13px] text-cool-grey hover:border-soft-gold/40 transition-colors disabled:opacity-50"
            >
              Back
            </button>
          </>
        )}
      </div>

      <p className="font-body text-[11px] text-muted-cream text-center leading-[1.6]">
        Your name and email are shared with the organizer only.
        Daanaa does not display who attends.
      </p>
    </div>
  )
}

export default function EventDetailPage() {
  const { eventId } = useParams<{ eventId: string }>()
  const [searchParams] = useSearchParams()
  const [event, setEvent]   = useState<VolunteerEvent | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [signupCount, setSignupCount] = useState(0)
  const cancelToken = searchParams.get('cancel')

  usePageMeta(
    event ? `${event.title} — Daanaa` : 'Event — Daanaa',
    event ? (event.description?.slice(0, 160) || event.title) : 'Volunteer event on Daanaa.',
  )

  useEffect(() => {
    if (!eventId) return
    getEventDetail(Number(eventId))
      .then(e => {
        setEvent(e)
        setSignupCount(e.signup_count)
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false))
  }, [eventId])

  const handleSignupDone = useCallback(() => {
    setSignupCount(c => c + 1)
  }, [])

  if (loading) {
    return (
      <div className="min-h-[100dvh] bg-warm-cream pt-[72px] flex items-center justify-center">
        <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
      </div>
    )
  }

  if (notFound || !event) {
    return (
      <div className="min-h-[100dvh] bg-warm-cream pt-[72px] flex flex-col items-center justify-center gap-4 px-6">
        <p className="font-display italic text-deep-navy text-[24px]">Event not found</p>
        <Link to="/volunteer" className="font-body text-[14px] text-soft-gold hover:text-bright-gold font-semibold">
          Browse all events →
        </Link>
      </div>
    )
  }

  const typeLabel = EVENT_TYPE_LABELS[event.event_type] || 'Event'
  const typeColor = EVENT_TYPE_COLORS[event.event_type] || 'bg-light-cream text-cool-grey'
  const timeStr = event.start_time
    ? `${formatTime(event.start_time)}${event.end_time ? ` – ${formatTime(event.end_time)}` : ''}`
    : null
  const location = event.is_virtual
    ? 'Virtual'
    : [event.location_city, event.location_state].filter(Boolean).join(', ') || null

  return (
    <div className="min-h-[100dvh] bg-warm-cream pt-[72px]">
      {/* Hero */}
      <div className="bg-deep-navy pt-10 pb-8">
        <div className="max-w-[860px] mx-auto px-6 md:px-12">
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <span className={`inline-block px-2.5 py-0.5 rounded-full font-body text-[10px] font-semibold tracking-[0.06em] uppercase ${typeColor}`}>
              {typeLabel}
            </span>
            {event.is_virtual && (
              <span className="inline-block px-2.5 py-0.5 rounded-full font-body text-[10px] font-semibold tracking-[0.06em] uppercase bg-blue-50 text-blue-600">
                Virtual
              </span>
            )}
            {event.min_age && event.min_age > 0 && (
              <span className="inline-block px-2.5 py-0.5 rounded-full font-body text-[10px] font-semibold tracking-[0.06em] uppercase bg-orange-50 text-orange-600">
                {event.min_age}+
              </span>
            )}
          </div>
          <h1 className="font-display italic text-warm-cream leading-tight" style={{ fontSize: 'clamp(26px, 4vw, 44px)' }}>
            {event.title}
          </h1>
          {event.org_name && (
            <Link
              to={`/org/${event.ein}`}
              className="font-body text-[15px] text-soft-gold hover:text-bright-gold font-medium mt-2 block"
            >
              {event.org_name}
            </Link>
          )}

          <div className="flex flex-wrap gap-x-5 gap-y-1.5 mt-4 font-body text-[14px]">
            <span className="text-warm-cream font-medium">{formatDate(event.event_date)}</span>
            {timeStr && <span className="text-muted-cream">{timeStr}</span>}
            {location && <span className="text-muted-cream">{location}</span>}
            {event.expected_hours && (
              <span className="text-muted-cream">{event.expected_hours}h volunteer credit</span>
            )}
          </div>

          {/* Signup count — social proof of reality, not competition */}
          {signupCount > 0 && (
            <p className="font-body text-[13px] text-muted-cream mt-3">
              {signupCount} {signupCount === 1 ? 'person' : 'people'} signed up
            </p>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="max-w-[860px] mx-auto px-6 md:px-12 py-10 grid grid-cols-1 md:grid-cols-[1fr_320px] gap-8">
        {/* Left: description + share */}
        <div className="order-2 md:order-1 flex flex-col gap-8">
          {/* Description */}
          {event.description && (
            <section>
              <h2 className="font-body text-[11px] font-semibold text-cool-grey tracking-[0.08em] uppercase mb-3">
                About this event
              </h2>
              <p className="font-body text-[15px] text-deep-navy leading-[1.8] whitespace-pre-line">
                {event.description}
              </p>
            </section>
          )}

          {/* Volunteer details grid */}
          {(event.coordinator_name || event.skill_level || event.what_to_bring || event.parking_info || event.waiver_url) && (
            <section className="bg-white rounded-2xl border border-light-cream p-5 grid grid-cols-1 sm:grid-cols-2 gap-5">
              {event.coordinator_name && (
                <div>
                  <p className="font-body text-[10px] font-semibold tracking-[0.08em] text-soft-gold uppercase mb-1">
                    Your coordinator
                  </p>
                  <p className="font-body text-[14px] text-deep-navy">{event.coordinator_name}</p>
                </div>
              )}
              {event.skill_level && event.skill_level !== 'any' && (
                <div>
                  <p className="font-body text-[10px] font-semibold tracking-[0.08em] text-soft-gold uppercase mb-1">
                    Skill level
                  </p>
                  <p className="font-body text-[14px] text-deep-navy capitalize">{event.skill_level}</p>
                </div>
              )}
              {event.expected_hours && (
                <div>
                  <p className="font-body text-[10px] font-semibold tracking-[0.08em] text-soft-gold uppercase mb-1">
                    Time commitment
                  </p>
                  <p className="font-body text-[14px] text-deep-navy">{event.expected_hours} hours</p>
                </div>
              )}
              {event.what_to_bring && (
                <div className="sm:col-span-2">
                  <p className="font-body text-[10px] font-semibold tracking-[0.08em] text-soft-gold uppercase mb-1">
                    What to bring
                  </p>
                  <p className="font-body text-[14px] text-deep-navy leading-[1.6]">{event.what_to_bring}</p>
                </div>
              )}
              {event.parking_info && (
                <div className="sm:col-span-2">
                  <p className="font-body text-[10px] font-semibold tracking-[0.08em] text-soft-gold uppercase mb-1">
                    Parking and transit
                  </p>
                  <p className="font-body text-[14px] text-deep-navy leading-[1.6]">{event.parking_info}</p>
                </div>
              )}
              {event.waiver_url && (
                <div className="sm:col-span-2">
                  <p className="font-body text-[10px] font-semibold tracking-[0.08em] text-soft-gold uppercase mb-1">
                    Waiver required
                  </p>
                  <a
                    href={event.waiver_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-body text-[14px] text-soft-gold hover:text-bright-gold font-semibold"
                  >
                    Review and sign waiver →
                  </a>
                </div>
              )}
            </section>
          )}

          {/* Privacy notice — surfaces the trust signal legal asked for */}
          <section className="bg-[#F8F5F0] rounded-2xl border border-light-grey p-5">
            <p className="font-body text-[11px] font-semibold text-cool-grey tracking-[0.08em] uppercase mb-2">
              Your privacy
            </p>
            <p className="font-body text-[13px] text-cool-grey leading-[1.65]">
              When you sign up, your name and email go directly to the organizing nonprofit — Daanaa does not retain or use your contact information. Daanaa does not verify event accessibility accommodations; contact the organizer directly with any questions.
            </p>
          </section>

          {/* Share */}
          <section>
            <h2 className="font-body text-[11px] font-semibold text-cool-grey tracking-[0.08em] uppercase mb-2">
              Know someone who cares about this cause?
            </h2>
            <p className="font-body text-[13px] text-cool-grey mb-3">
              Share this event — no account needed to sign up.
            </p>
            <ShareBar event={event} />
          </section>

          {/* Org snippet */}
          {event.org_name && (
            <section className="bg-white rounded-2xl border border-light-cream p-5">
              <h2 className="font-body text-[11px] font-semibold text-cool-grey tracking-[0.08em] uppercase mb-2">
                About {event.org_name}
              </h2>
              {event.org_mission && (
                <p className="font-body text-[14px] text-deep-navy leading-[1.7] mb-3">
                  {event.org_mission}
                </p>
              )}
              <Link
                to={`/org/${event.ein}`}
                className="font-body text-[13px] text-soft-gold hover:text-bright-gold font-semibold"
              >
                View organization profile →
              </Link>
            </section>
          )}
        </div>

        {/* Right: signup panel */}
        <div className="order-1 md:order-2">
          <div className="sticky top-20 flex flex-col gap-4">
            {cancelToken ? (
              <CancelPanel eventId={event.id} token={cancelToken} />
            ) : (
              <SignupForm event={{ ...event, signup_count: signupCount }} onDone={handleSignupDone} />
            )}

            {/* QR code preview */}
            <div className="bg-white rounded-2xl border border-light-cream p-4 text-center">
              <p className="font-body text-[11px] text-muted-cream mb-2">Scan to share</p>
              <img
                src={`${API_BASE}/api/events/${event.id}/qr.png`}
                alt="QR code for this event"
                className="w-28 h-28 mx-auto"
                loading="lazy"
              />
              <a
                href={`${API_BASE}/api/events/${event.id}/qr.png`}
                download={`event-${event.id}-qr.png`}
                className="mt-2 inline-block font-body text-[11px] text-soft-gold hover:underline"
              >
                Download for flyer
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Footer nav */}
      <div className="max-w-[860px] mx-auto px-6 md:px-12 pb-12">
        <Link
          to="/volunteer"
          className="font-body text-[13px] text-soft-gold hover:text-bright-gold font-semibold"
        >
          ← Browse all events
        </Link>
      </div>
    </div>
  )
}

function CancelPanel({ eventId, token }: { eventId: number; token: string }) {
  const [state, setState] = useState<'confirm' | 'loading' | 'done' | 'error'>('confirm')
  const [error, setError] = useState('')

  const cancel = async () => {
    setState('loading')
    try {
      await cancelEventSignup(eventId, token)
      setState('done')
    } catch {
      setError('Could not cancel. Try again or email events@daanaa.org.')
      setState('error')
    }
  }

  if (state === 'done') {
    return (
      <div className="bg-light-cream rounded-2xl p-5 text-center">
        <p className="font-body text-[14px] text-cool-grey">Your signup has been cancelled.</p>
        <Link to="/volunteer" className="mt-3 inline-block font-body text-[13px] text-soft-gold hover:underline">
          Browse other events →
        </Link>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-orange-100 p-5 flex flex-col gap-3">
      <h3 className="font-display italic text-deep-navy text-[16px]">Cancel signup</h3>
      {state === 'error' && (
        <p className="font-body text-[13px] text-red-600">{error}</p>
      )}
      <p className="font-body text-[13px] text-cool-grey">
        You're about to cancel your spot at this event. This can't be undone.
      </p>
      <button
        onClick={cancel}
        disabled={state === 'loading'}
        className="py-2.5 rounded-xl bg-red-500 text-white font-body text-[14px] font-semibold hover:bg-red-600 transition-colors disabled:opacity-50"
      >
        {state === 'loading' ? 'Cancelling…' : 'Yes, cancel my signup'}
      </button>
      <Link
        to={`/events/${eventId}`}
        replace
        className="text-center font-body text-[13px] text-cool-grey hover:text-deep-navy"
      >
        Keep my spot
      </Link>
    </div>
  )
}
