import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { ClaimProgressBar } from '../components/ClaimProgressBar'
import {
  getOrgVolunteerEvents, createVolunteerEvent, updateVolunteerEvent, cancelVolunteerEvent,
  getServiceArea, putServiceArea,
  type VolunteerEvent, type ServiceAreaType,
} from '../data/api'

const CAUSE_TAGS = [
  'Arts & Culture','Education','Environment','Health','Community Development',
  'Human Rights','Research','International Aid','Animals','Disaster Relief',
  'Youth Development','Food Security','Housing','Mental Health','Employment',
]

const US_STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
  'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
  'VA','WA','WV','WI','WY','DC',
]

function formatDate(d: string) {
  const [y, m, day] = d.split('-')
  return new Date(Number(y), Number(m) - 1, Number(day)).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })
}

interface EventFormData {
  title: string
  description: string
  event_date: string
  start_time: string
  end_time: string
  location_city: string
  location_state: string
  location_zip: string
  is_virtual: boolean
  signup_url: string
  contact_email: string
  capacity: string
}

const EMPTY_FORM: EventFormData = {
  title: '', description: '', event_date: '', start_time: '', end_time: '',
  location_city: '', location_state: '', location_zip: '',
  is_virtual: false, signup_url: '', contact_email: '', capacity: '',
}

function EventForm({
  initial, onSave, onCancel, saving,
}: {
  initial?: EventFormData
  onSave: (data: EventFormData) => void
  onCancel: () => void
  saving: boolean
}) {
  const [form, setForm] = useState<EventFormData>(initial ?? EMPTY_FORM)
  const set = (k: keyof EventFormData, v: string | boolean) =>
    setForm(prev => ({ ...prev, [k]: v }))

  return (
    <div className="border border-soft-gold/30 rounded-xl p-5 bg-warm-cream space-y-4">
      <label className="block">
        <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">Event title *</span>
        <input
          type="text" required maxLength={200}
          value={form.title} onChange={e => set('title', e.target.value)}
          placeholder="e.g. Community Garden Workday"
          className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-[14px] placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
          disabled={saving}
        />
      </label>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <label className="block">
          <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">Date *</span>
          <input
            type="date" required
            value={form.event_date} onChange={e => set('event_date', e.target.value)}
            className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-[14px] focus:outline-none focus:border-soft-gold/60"
            disabled={saving}
          />
        </label>
        <label className="block">
          <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">Start time</span>
          <input
            type="time"
            value={form.start_time} onChange={e => set('start_time', e.target.value)}
            className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-[14px] focus:outline-none focus:border-soft-gold/60"
            disabled={saving}
          />
        </label>
        <label className="block">
          <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">End time</span>
          <input
            type="time"
            value={form.end_time} onChange={e => set('end_time', e.target.value)}
            className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-[14px] focus:outline-none focus:border-soft-gold/60"
            disabled={saving}
          />
        </label>
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={form.is_virtual}
          onChange={e => set('is_virtual', e.target.checked)}
          className="w-4 h-4 rounded border-light-cream accent-soft-gold"
          disabled={saving}
        />
        <span className="font-body text-[14px] text-cool-grey">This is a virtual event</span>
      </label>

      {!form.is_virtual && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <label className="block">
            <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">City</span>
            <input
              type="text" maxLength={100}
              value={form.location_city} onChange={e => set('location_city', e.target.value)}
              placeholder="Austin"
              className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-[14px] placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
              disabled={saving}
            />
          </label>
          <label className="block">
            <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">State</span>
            <select
              value={form.location_state} onChange={e => set('location_state', e.target.value)}
              className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-[14px] focus:outline-none focus:border-soft-gold/60 bg-white"
              disabled={saving}
            >
              <option value="">—</option>
              {US_STATES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label className="block">
            <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">Zip code</span>
            <input
              type="text" maxLength={10} inputMode="numeric"
              value={form.location_zip} onChange={e => set('location_zip', e.target.value)}
              placeholder="78701"
              className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-[14px] placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
              disabled={saving}
            />
          </label>
        </div>
      )}

      <label className="block">
        <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">Description</span>
        <textarea
          rows={3} maxLength={1000}
          value={form.description} onChange={e => set('description', e.target.value)}
          placeholder="What will volunteers do? Who is this for?"
          className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-[14px] placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60 resize-none"
          disabled={saving}
        />
      </label>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label className="block">
          <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">Sign-up link</span>
          <input
            type="url" maxLength={500}
            value={form.signup_url} onChange={e => set('signup_url', e.target.value)}
            placeholder="https://..."
            className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-[14px] placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
            disabled={saving}
          />
          <p className="mt-1 font-body text-[11px] text-muted-cream">Link to your own sign-up form</p>
        </label>
        <label className="block">
          <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">Contact email (fallback)</span>
          <input
            type="email" maxLength={200}
            value={form.contact_email} onChange={e => set('contact_email', e.target.value)}
            placeholder="volunteer@org.org"
            className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-[14px] placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
            disabled={saving}
          />
        </label>
      </div>

      <label className="block w-40">
        <span className="block font-body text-[12px] font-medium text-deep-navy mb-1">Volunteer capacity</span>
        <input
          type="number" min={1} max={9999}
          value={form.capacity} onChange={e => set('capacity', e.target.value)}
          placeholder="Unlimited"
          className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-[14px] placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
          disabled={saving}
        />
      </label>

      <div className="flex gap-3 pt-1">
        <button
          type="button"
          onClick={() => onSave(form)}
          disabled={saving || !form.title || !form.event_date}
          className="px-5 py-2.5 bg-soft-gold text-deep-navy rounded-xl font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save event'}
        </button>
        <button
          type="button" onClick={onCancel} disabled={saving}
          className="px-5 py-2.5 border border-light-cream text-cool-grey rounded-xl font-body text-[14px] hover:border-soft-gold/40 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}

function VolunteerEventsSection({ ein, token }: { ein: string; token: string }) {
  const [events, setEvents]       = useState<VolunteerEvent[]>([])
  const [loading, setLoading]     = useState(true)
  const [showForm, setShowForm]   = useState(false)
  const [editId, setEditId]       = useState<number | null>(null)
  const [saving, setSaving]       = useState(false)
  const [error, setError]         = useState<string | null>(null)

  useEffect(() => {
    getOrgVolunteerEvents(ein, { all: true })
      .then(r => setEvents(r.events))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [ein])

  async function handleCreate(data: EventFormData) {
    setSaving(true); setError(null)
    try {
      const ev = await createVolunteerEvent(ein, token, {
        title:          data.title,
        description:    data.description || null,
        event_date:     data.event_date,
        start_time:     data.start_time || null,
        end_time:       data.end_time || null,
        location_city:  data.location_city || null,
        location_state: data.location_state || null,
        location_zip:   data.location_zip || null,
        is_virtual:     data.is_virtual,
        signup_url:     data.signup_url || null,
        contact_email:  data.contact_email || null,
        capacity:       data.capacity ? Number(data.capacity) : null,
      })
      setEvents(prev => [ev, ...prev])
      setShowForm(false)
    } catch {
      setError('Could not save event. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  async function handleUpdate(id: number, data: EventFormData) {
    setSaving(true); setError(null)
    try {
      const ev = await updateVolunteerEvent(id, token, {
        title:          data.title,
        description:    data.description || null,
        event_date:     data.event_date,
        start_time:     data.start_time || null,
        end_time:       data.end_time || null,
        location_city:  data.location_city || null,
        location_state: data.location_state || null,
        location_zip:   data.location_zip || null,
        is_virtual:     data.is_virtual,
        signup_url:     data.signup_url || null,
        contact_email:  data.contact_email || null,
        capacity:       data.capacity ? Number(data.capacity) : null,
      })
      setEvents(prev => prev.map(e => e.id === id ? ev : e))
      setEditId(null)
    } catch {
      setError('Could not update event. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  async function handleCancel(id: number) {
    if (!confirm('Cancel this event? Volunteers will no longer see it.')) return
    setSaving(true); setError(null)
    try {
      await cancelVolunteerEvent(id, token)
      setEvents(prev => prev.map(e => e.id === id ? { ...e, status: 'cancelled' } : e))
    } catch {
      setError('Could not cancel event.')
    } finally {
      setSaving(false)
    }
  }

  const statusBadge = (s: VolunteerEvent['status']) => {
    const map: Record<string, string> = {
      active: 'bg-green-50 text-green-700',
      filled: 'bg-blue-50 text-blue-700',
      cancelled: 'bg-red-50 text-red-600',
      expired: 'bg-light-cream text-muted-cream',
    }
    return (
      <span className={`px-2 py-0.5 rounded-full font-body text-[10px] font-semibold uppercase tracking-[0.06em] ${map[s] ?? ''}`}>
        {s}
      </span>
    )
  }

  return (
    <div className="border-t border-light-cream pt-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-body text-[13px] font-medium text-deep-navy">Volunteer events</h3>
          <p className="font-body text-[12px] text-muted-cream mt-0.5">
            Events appear on the public volunteer search page. They expire automatically after their date.
          </p>
        </div>
        {!showForm && (
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-soft-gold/15 text-soft-gold rounded-lg font-body text-[13px] font-semibold hover:bg-soft-gold/25 transition-colors"
          >
            + Add event
          </button>
        )}
      </div>

      {error && (
        <p className="font-body text-[13px] text-red-600">{error}</p>
      )}

      {showForm && (
        <EventForm
          onSave={handleCreate}
          onCancel={() => setShowForm(false)}
          saving={saving}
        />
      )}

      {loading && <p className="font-body text-[13px] text-muted-cream">Loading events...</p>}

      {!loading && events.length === 0 && !showForm && (
        <p className="font-body text-[13px] text-muted-cream">No events yet. Add your first volunteer opportunity.</p>
      )}

      {events.map(ev => (
        <div key={ev.id} className="border border-light-cream rounded-xl p-4">
          {editId === ev.id ? (
            <EventForm
              initial={{
                title: ev.title, description: ev.description ?? '',
                event_date: ev.event_date, start_time: ev.start_time ?? '',
                end_time: ev.end_time ?? '', location_city: ev.location_city ?? '',
                location_state: ev.location_state ?? '', location_zip: ev.location_zip ?? '',
                is_virtual: ev.is_virtual, signup_url: ev.signup_url ?? '',
                contact_email: ev.contact_email ?? '', capacity: ev.capacity ? String(ev.capacity) : '',
              }}
              onSave={data => handleUpdate(ev.id, data)}
              onCancel={() => setEditId(null)}
              saving={saving}
            />
          ) : (
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  {statusBadge(ev.status)}
                  <span className="font-body text-[12px] text-muted-cream">{formatDate(ev.event_date)}</span>
                </div>
                <p className="font-body text-[15px] font-medium text-deep-navy">{ev.title}</p>
                {ev.location_city && !ev.is_virtual && (
                  <p className="font-body text-[12px] text-cool-grey mt-0.5">
                    {[ev.location_city, ev.location_state].filter(Boolean).join(', ')}
                  </p>
                )}
                {ev.is_virtual && (
                  <p className="font-body text-[12px] text-cool-grey mt-0.5">Virtual</p>
                )}
              </div>
              {ev.status !== 'expired' && ev.status !== 'cancelled' && (
                <div className="flex gap-2 shrink-0">
                  <button
                    type="button" onClick={() => setEditId(ev.id)} disabled={saving}
                    className="font-body text-[12px] text-soft-gold hover:text-bright-gold font-semibold"
                  >
                    Edit
                  </button>
                  <button
                    type="button" onClick={() => handleCancel(ev.id)} disabled={saving}
                    className="font-body text-[12px] text-cool-grey hover:text-red-500"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default function OrgClaimEditor() {
  usePageMeta('Edit Your Page', 'Add your mission, donation link, and impact areas.')
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [mission, setMission] = useState('')
  const [description, setDescription] = useState('')
  const [donateUrl, setDonateUrl] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const ein = searchParams.get('ein') || ''
  const token = searchParams.get('token') || ''

  useEffect(() => {
    if (!ein || !token) navigate('/for-nonprofits', { replace: true })
  }, [ein, token, navigate])

  function toggleTag(tag: string) {
    setSelectedTags(prev => prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag])
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const res = await fetch('/api/claim/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ein, verification_token: token,
          custom_mission: mission,
          custom_description: description,
          cause_tags_json: JSON.stringify(selectedTags),
          donate_confirmed: donateUrl.length > 0,
          donate_url: donateUrl || undefined,
        }),
      })
      const body = await res.json()
      if (!res.ok) {
        setError(body.error || 'Could not save. Please try again.')
        setSaving(false)
        return
      }
      navigate(`/claim/success?ein=${encodeURIComponent(ein)}`)
    } catch {
      setError('Network error. Please try again.')
      setSaving(false)
    }
  }

  return (
    <div className="min-h-[100dvh] bg-warm-cream pt-[72px]">
      <div className="max-w-[560px] mx-auto px-6 py-12">
        <ClaimProgressBar currentStep="edit" />
        <div className="text-center mb-8">
          <h1 className="font-display italic text-deep-navy mb-2" style={{ fontSize: 'clamp(28px, 4vw, 40px)' }}>
            Tell your story
          </h1>
          <p className="font-body text-[15px] text-cool-grey">All fields are optional. Add what you can — you can always come back.</p>
        </div>
        <form onSubmit={handleSave} className="bg-white rounded-2xl shadow-sm border border-light-cream p-8 space-y-6">
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
              <p className="font-body text-[14px] text-red-700">{error}</p>
            </div>
          )}
          <label className="block">
            <span className="block font-body text-[13px] font-medium text-deep-navy mb-2">Mission statement <span className="text-muted-cream font-normal">(1–2 sentences)</span></span>
            <textarea
              value={mission} onChange={e => setMission(e.target.value.slice(0, 300))}
              placeholder="What does your organization do and who do you serve?"
              rows={3}
              className="w-full px-4 py-3 border border-light-cream rounded-xl font-body text-[14px] placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold resize-none"
              disabled={saving}
            />
            <p className="mt-1 font-body text-[11px] text-muted-cream">{mission.length}/300</p>
          </label>
          <label className="block">
            <span className="block font-body text-[13px] font-medium text-deep-navy mb-2">Programs and impact <span className="text-muted-cream font-normal">(optional)</span></span>
            <textarea
              value={description} onChange={e => setDescription(e.target.value.slice(0, 500))}
              placeholder="Describe your programs, service area, or recent impact..."
              rows={4}
              className="w-full px-4 py-3 border border-light-cream rounded-xl font-body text-[14px] placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold resize-none"
              disabled={saving}
            />
            <p className="mt-1 font-body text-[11px] text-muted-cream">{description.length}/500</p>
          </label>
          <label className="block">
            <span className="block font-body text-[13px] font-medium text-deep-navy mb-2">Donation link <span className="text-muted-cream font-normal">(optional)</span></span>
            <input
              type="url" value={donateUrl} onChange={e => setDonateUrl(e.target.value)}
              placeholder="https://..."
              className="w-full px-4 py-3 border border-light-cream rounded-xl font-body text-[14px] placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold"
              disabled={saving}
            />
            <p className="mt-1 font-body text-[11px] text-muted-cream">Your official page where donors can give directly.</p>
          </label>
          <fieldset>
            <legend className="font-body text-[13px] font-medium text-deep-navy mb-3">Focus areas <span className="text-muted-cream font-normal">(select all that apply)</span></legend>
            <div className="flex flex-wrap gap-2">
              {CAUSE_TAGS.map(tag => (
                <button
                  key={tag} type="button" onClick={() => toggleTag(tag)} disabled={saving}
                  className={`px-3 py-1.5 rounded-full font-body text-[13px] border transition-colors ${
                    selectedTags.includes(tag)
                      ? 'bg-soft-gold text-deep-navy border-soft-gold'
                      : 'bg-white text-cool-grey border-light-cream hover:border-soft-gold'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </fieldset>

          {ein && token && (
            <VolunteerEventsSection ein={ein} token={token} />
          )}

          <button
            type="submit" disabled={saving}
            className="w-full px-4 py-3 bg-soft-gold text-deep-navy font-body text-[15px] font-semibold rounded-xl hover:bg-bright-gold disabled:opacity-40 transition-colors"
          >
            {saving ? 'Saving...' : 'Save and publish'}
          </button>
        </form>
      </div>
    </div>
  )
}
