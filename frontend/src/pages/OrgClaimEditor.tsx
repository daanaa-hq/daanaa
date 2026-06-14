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

const COUNTRIES: { code: string; name: string }[] = [
  { code: 'AF', name: 'Afghanistan' }, { code: 'AL', name: 'Albania' },
  { code: 'DZ', name: 'Algeria' }, { code: 'AO', name: 'Angola' },
  { code: 'AR', name: 'Argentina' }, { code: 'AM', name: 'Armenia' },
  { code: 'AU', name: 'Australia' }, { code: 'AT', name: 'Austria' },
  { code: 'AZ', name: 'Azerbaijan' }, { code: 'BD', name: 'Bangladesh' },
  { code: 'BY', name: 'Belarus' }, { code: 'BE', name: 'Belgium' },
  { code: 'BZ', name: 'Belize' }, { code: 'BJ', name: 'Benin' },
  { code: 'BO', name: 'Bolivia' }, { code: 'BA', name: 'Bosnia and Herzegovina' },
  { code: 'BW', name: 'Botswana' }, { code: 'BR', name: 'Brazil' },
  { code: 'BF', name: 'Burkina Faso' }, { code: 'BI', name: 'Burundi' },
  { code: 'KH', name: 'Cambodia' }, { code: 'CM', name: 'Cameroon' },
  { code: 'CA', name: 'Canada' }, { code: 'CF', name: 'Central African Republic' },
  { code: 'TD', name: 'Chad' }, { code: 'CL', name: 'Chile' },
  { code: 'CN', name: 'China' }, { code: 'CO', name: 'Colombia' },
  { code: 'CD', name: 'Congo (DRC)' }, { code: 'CG', name: 'Congo (Republic)' },
  { code: 'CR', name: 'Costa Rica' }, { code: 'HR', name: 'Croatia' },
  { code: 'CU', name: 'Cuba' }, { code: 'CY', name: 'Cyprus' },
  { code: 'CZ', name: 'Czech Republic' }, { code: 'DK', name: 'Denmark' },
  { code: 'DJ', name: 'Djibouti' }, { code: 'DO', name: 'Dominican Republic' },
  { code: 'EC', name: 'Ecuador' }, { code: 'EG', name: 'Egypt' },
  { code: 'SV', name: 'El Salvador' }, { code: 'ER', name: 'Eritrea' },
  { code: 'ET', name: 'Ethiopia' }, { code: 'FI', name: 'Finland' },
  { code: 'FR', name: 'France' }, { code: 'GA', name: 'Gabon' },
  { code: 'GM', name: 'Gambia' }, { code: 'GE', name: 'Georgia' },
  { code: 'DE', name: 'Germany' }, { code: 'GH', name: 'Ghana' },
  { code: 'GR', name: 'Greece' }, { code: 'GT', name: 'Guatemala' },
  { code: 'GN', name: 'Guinea' }, { code: 'GW', name: 'Guinea-Bissau' },
  { code: 'HT', name: 'Haiti' }, { code: 'HN', name: 'Honduras' },
  { code: 'HU', name: 'Hungary' }, { code: 'IN', name: 'India' },
  { code: 'ID', name: 'Indonesia' }, { code: 'IR', name: 'Iran' },
  { code: 'IQ', name: 'Iraq' }, { code: 'IE', name: 'Ireland' },
  { code: 'IL', name: 'Israel' }, { code: 'IT', name: 'Italy' },
  { code: 'JM', name: 'Jamaica' }, { code: 'JP', name: 'Japan' },
  { code: 'JO', name: 'Jordan' }, { code: 'KZ', name: 'Kazakhstan' },
  { code: 'KE', name: 'Kenya' }, { code: 'KP', name: 'North Korea' },
  { code: 'KR', name: 'South Korea' }, { code: 'KW', name: 'Kuwait' },
  { code: 'KG', name: 'Kyrgyzstan' }, { code: 'LA', name: 'Laos' },
  { code: 'LB', name: 'Lebanon' }, { code: 'LR', name: 'Liberia' },
  { code: 'LY', name: 'Libya' }, { code: 'LT', name: 'Lithuania' },
  { code: 'MG', name: 'Madagascar' }, { code: 'MW', name: 'Malawi' },
  { code: 'MY', name: 'Malaysia' }, { code: 'ML', name: 'Mali' },
  { code: 'MR', name: 'Mauritania' }, { code: 'MX', name: 'Mexico' },
  { code: 'MD', name: 'Moldova' }, { code: 'MN', name: 'Mongolia' },
  { code: 'MA', name: 'Morocco' }, { code: 'MZ', name: 'Mozambique' },
  { code: 'MM', name: 'Myanmar' }, { code: 'NA', name: 'Namibia' },
  { code: 'NP', name: 'Nepal' }, { code: 'NL', name: 'Netherlands' },
  { code: 'NZ', name: 'New Zealand' }, { code: 'NI', name: 'Nicaragua' },
  { code: 'NE', name: 'Niger' }, { code: 'NG', name: 'Nigeria' },
  { code: 'NO', name: 'Norway' }, { code: 'PK', name: 'Pakistan' },
  { code: 'PA', name: 'Panama' }, { code: 'PG', name: 'Papua New Guinea' },
  { code: 'PY', name: 'Paraguay' }, { code: 'PE', name: 'Peru' },
  { code: 'PH', name: 'Philippines' }, { code: 'PL', name: 'Poland' },
  { code: 'PT', name: 'Portugal' }, { code: 'RO', name: 'Romania' },
  { code: 'RU', name: 'Russia' }, { code: 'RW', name: 'Rwanda' },
  { code: 'SA', name: 'Saudi Arabia' }, { code: 'SN', name: 'Senegal' },
  { code: 'SL', name: 'Sierra Leone' }, { code: 'SO', name: 'Somalia' },
  { code: 'ZA', name: 'South Africa' }, { code: 'SS', name: 'South Sudan' },
  { code: 'ES', name: 'Spain' }, { code: 'LK', name: 'Sri Lanka' },
  { code: 'SD', name: 'Sudan' }, { code: 'SE', name: 'Sweden' },
  { code: 'CH', name: 'Switzerland' }, { code: 'SY', name: 'Syria' },
  { code: 'TW', name: 'Taiwan' }, { code: 'TJ', name: 'Tajikistan' },
  { code: 'TZ', name: 'Tanzania' }, { code: 'TH', name: 'Thailand' },
  { code: 'TL', name: 'Timor-Leste' }, { code: 'TG', name: 'Togo' },
  { code: 'TN', name: 'Tunisia' }, { code: 'TR', name: 'Turkey' },
  { code: 'TM', name: 'Turkmenistan' }, { code: 'UG', name: 'Uganda' },
  { code: 'UA', name: 'Ukraine' }, { code: 'AE', name: 'United Arab Emirates' },
  { code: 'GB', name: 'United Kingdom' }, { code: 'US', name: 'United States' },
  { code: 'UY', name: 'Uruguay' }, { code: 'UZ', name: 'Uzbekistan' },
  { code: 'VE', name: 'Venezuela' }, { code: 'VN', name: 'Vietnam' },
  { code: 'YE', name: 'Yemen' }, { code: 'ZM', name: 'Zambia' },
  { code: 'ZW', name: 'Zimbabwe' },
]

function ServiceAreaSection({ ein, token }: { ein: string; token: string }) {
  const [areaType, setAreaType]     = useState<ServiceAreaType>('local')
  const [values, setValues]         = useState<string[]>([])
  const [regional, setRegional]     = useState('')
  const [loading, setLoading]       = useState(true)
  const [saving, setSaving]         = useState(false)
  const [saved, setSaved]           = useState(false)
  const [error, setError]           = useState<string | null>(null)

  useEffect(() => {
    getServiceArea(ein)
      .then(r => {
        if (r.area_type) setAreaType(r.area_type)
        setValues(r.area_values ?? [])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [ein])

  async function handleSave() {
    setSaving(true); setError(null); setSaved(false)
    try {
      await putServiceArea(ein, token, areaType, values)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch {
      setError('Could not save. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  function toggleValue(v: string) {
    setValues(prev => prev.includes(v) ? prev.filter(x => x !== v) : [...prev, v])
  }

  function addRegional() {
    const t = regional.trim()
    if (!t || values.includes(t) || values.length >= 10) return
    setValues(prev => [...prev, t])
    setRegional('')
  }

  if (loading) return null

  return (
    <fieldset className="border border-light-cream rounded-xl p-5 space-y-4">
      <legend className="px-2 font-body text-[13px] font-semibold text-cool-grey uppercase tracking-wider">
        Where you serve
      </legend>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {(['local','regional','statewide','nationwide','international'] as ServiceAreaType[]).map(t => (
          <button
            key={t} type="button"
            onClick={() => { setAreaType(t); setValues([]) }}
            className={`px-3 py-2 rounded-xl font-body text-[13px] border capitalize transition-colors ${
              areaType === t
                ? 'bg-soft-gold text-deep-navy border-soft-gold'
                : 'bg-white text-cool-grey border-light-cream hover:border-soft-gold/50'
            }`}
          >
            {t === 'local' ? 'Local (my city)' :
             t === 'regional' ? 'Regional (counties)' :
             t === 'statewide' ? 'Statewide' :
             t === 'nationwide' ? 'Nationwide (US)' :
             'International'}
          </button>
        ))}
      </div>

      {areaType === 'regional' && (
        <div className="space-y-2">
          <p className="font-body text-[12px] text-cool-grey">Add counties or metro areas you serve (up to 10)</p>
          <div className="flex gap-2">
            <input
              value={regional} onChange={e => setRegional(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addRegional())}
              placeholder="e.g. Cook County, IL"
              className="flex-1 px-3 py-2 border border-light-cream rounded-xl font-body text-[14px] text-deep-navy focus:outline-none focus:border-soft-gold"
            />
            <button type="button" onClick={addRegional}
              className="px-4 py-2 bg-pale-gold/30 text-deep-navy rounded-xl font-body text-[13px] hover:bg-pale-gold/50 transition-colors">
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {values.map(v => (
              <span key={v} className="inline-flex items-center gap-1 px-2.5 py-1 bg-pale-gold/20 text-deep-navy rounded-full font-body text-[12px]">
                {v}
                <button type="button" onClick={() => setValues(p => p.filter(x => x !== v))}
                  className="text-cool-grey hover:text-deep-navy leading-none">×</button>
              </span>
            ))}
          </div>
        </div>
      )}

      {areaType === 'statewide' && (
        <div className="space-y-2">
          <p className="font-body text-[12px] text-cool-grey">Select the states you serve</p>
          <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto">
            {US_STATES.map(s => (
              <button key={s} type="button" onClick={() => toggleValue(s)}
                className={`px-2.5 py-1 rounded-full font-body text-[12px] border transition-colors ${
                  values.includes(s)
                    ? 'bg-soft-gold text-deep-navy border-soft-gold'
                    : 'bg-white text-cool-grey border-light-cream hover:border-soft-gold/50'
                }`}
              >{s}</button>
            ))}
          </div>
        </div>
      )}

      {areaType === 'international' && (
        <div className="space-y-2">
          <p className="font-body text-[12px] text-cool-grey">Select the countries you serve (up to 50)</p>
          <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto">
            {COUNTRIES.map(c => (
              <button key={c.code} type="button"
                onClick={() => (values.length < 50 || values.includes(c.code)) && toggleValue(c.code)}
                className={`px-2.5 py-1 rounded-full font-body text-[12px] border transition-colors ${
                  values.includes(c.code)
                    ? 'bg-soft-gold text-deep-navy border-soft-gold'
                    : 'bg-white text-cool-grey border-light-cream hover:border-soft-gold/50'
                }`}
              >{c.name}</button>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center gap-3">
        <button type="button" onClick={handleSave} disabled={saving}
          className="px-5 py-2 bg-soft-gold text-deep-navy font-body text-[13px] font-semibold rounded-xl hover:bg-bright-gold disabled:opacity-40 transition-colors">
          {saving ? 'Saving…' : 'Save reach'}
        </button>
        {saved && <span className="font-body text-[13px] text-green-600">Saved!</span>}
        {error && <span className="font-body text-[13px] text-red-500">{error}</span>}
      </div>
    </fieldset>
  )
}

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
            <ServiceAreaSection ein={ein} token={token} />
          )}

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
