import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { ClaimProgressBar } from '../components/ClaimProgressBar'
import ResearchDataTransparency from '../components/ResearchDataTransparency'
import DataUpdateForm from '../components/DataUpdateForm'
import {
  getOrganization, getOrgVolunteerEvents, createVolunteerEvent, updateVolunteerEvent, cancelVolunteerEvent,
  getServiceArea, putServiceArea,
  type VolunteerEvent, type ServiceAreaType, type ApiOrganization,
} from '../data/api'
import { METRO_NAMES } from '../data/msas'
import { US_STATES as US_STATES_WITH_NAMES } from '../data/locations'

const CAUSE_TAGS = [
  'Arts & Culture','Education','Environment','Health','Community Development',
  'Human Rights','Research','International Aid','Animals','Disaster Relief',
  'Youth Development','Food Security','Housing','Mental Health','Employment',
]

// This page only needs the codes (no display names) — derived from the shared
// source so state lists don't drift out of sync across pages (frontend/src/data/locations.ts).
// Matches this file's prior scope: continental US + DC, no PR/territories/military.
const US_STATES = US_STATES_WITH_NAMES
  .map(([code]) => code)
  .filter(code => code !== 'PR')

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

function MSAPicker({ values, onChange }: {
  values: string[]
  onChange: (v: string[]) => void
}) {
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return q ? METRO_NAMES.filter(m => m.toLowerCase().includes(q)) : METRO_NAMES
  }, [search])

  function toggle(name: string) {
    if (values.includes(name)) onChange(values.filter(v => v !== name))
    else if (values.length < 50) onChange([...values, name])
  }

  return (
    <div className="space-y-3">
      {values.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {values.map(v => (
            <span key={v} className="inline-flex items-center gap-1 px-2.5 py-1 bg-soft-gold/20 text-deep-navy rounded-full font-body text-caption">
              {v}
              <button type="button" onClick={() => onChange(values.filter(x => x !== v))}
                aria-label={`Remove ${v}`}
                className="text-cool-grey hover:text-deep-navy leading-none ml-0.5">×</button>
            </span>
          ))}
        </div>
      )}
      <input
        value={search} onChange={e => setSearch(e.target.value)}
        placeholder="Search metro areas… e.g. Chicago, Dallas, Phoenix"
        className="w-full px-3 py-2 border border-light-cream rounded-xl font-body text-body text-deep-navy focus:outline-none focus:border-soft-gold"
      />
      <div className="border border-light-cream rounded-xl overflow-y-auto max-h-52 divide-y divide-light-cream/60">
        {filtered.slice(0, 80).map(name => (
          <label key={name} className={`flex items-center gap-3 px-4 py-2.5 cursor-pointer hover:bg-warm-cream transition-colors ${values.includes(name) ? 'bg-soft-gold/10' : ''}`}>
            <input type="checkbox" checked={values.includes(name)} onChange={() => toggle(name)}
              className="accent-soft-gold w-4 h-4 flex-shrink-0" />
            <span className="font-body text-body text-deep-navy">{name}</span>
          </label>
        ))}
        {filtered.length > 80 && (
          <p className="px-4 py-2.5 font-body text-caption text-cool-grey">
            {filtered.length - 80} more — type to narrow the list
          </p>
        )}
      </div>
    </div>
  )
}

function ServiceAreaSection({ ein, token }: { ein: string; token: string }) {
  const [areaType, setAreaType] = useState<ServiceAreaType>('regional')
  const [values, setValues]     = useState<string[]>([])
  const [loading, setLoading]   = useState(true)
  const [saving, setSaving]     = useState(false)
  const [saved, setSaved]       = useState(false)
  const [error, setError]       = useState<string | null>(null)

  useEffect(() => {
    getServiceArea(ein)
      .then(r => {
        // 'local' is legacy — treat as regional (MSA picker) with no pre-selection
        setAreaType(r.area_type && r.area_type !== 'local' ? r.area_type : 'regional')
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

  if (loading) return null

  return (
    <fieldset className="border border-light-cream rounded-xl p-5 space-y-4">
      <legend className="px-2 font-body text-small font-semibold text-cool-grey uppercase tracking-wider">
        Where you serve
      </legend>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {([
          { type: 'regional',      label: 'Metro areas' },
          { type: 'statewide',     label: 'States' },
          { type: 'nationwide',    label: 'Nationwide' },
          { type: 'international', label: 'International' },
        ] as { type: ServiceAreaType; label: string }[]).map(({ type, label }) => (
          <button
            key={type} type="button"
            onClick={() => { setAreaType(type); setValues([]) }}
            className={`px-3 py-2 rounded-xl font-body text-small border transition-colors ${
              areaType === type || (type === 'regional' && areaType === 'local')
                ? 'bg-soft-gold text-deep-navy border-soft-gold'
                : 'bg-white text-cool-grey border-light-cream hover:border-soft-gold/50'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {areaType === 'regional' && (
        <MSAPicker values={values} onChange={setValues} />
      )}

      {areaType === 'statewide' && (
        <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto">
          {US_STATES.map(s => (
            <button key={s} type="button" onClick={() => toggleValue(s)}
              className={`px-2.5 py-1 rounded-full font-body text-caption border transition-colors ${
                values.includes(s)
                  ? 'bg-soft-gold text-deep-navy border-soft-gold'
                  : 'bg-white text-cool-grey border-light-cream hover:border-soft-gold/50'
              }`}
            >{s}</button>
          ))}
        </div>
      )}

      {areaType === 'international' && (
        <div className="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto">
          {COUNTRIES.map(c => (
            <button key={c.code} type="button"
              onClick={() => (values.length < 50 || values.includes(c.code)) && toggleValue(c.code)}
              className={`px-2.5 py-1 rounded-full font-body text-caption border transition-colors ${
                values.includes(c.code)
                  ? 'bg-soft-gold text-deep-navy border-soft-gold'
                  : 'bg-white text-cool-grey border-light-cream hover:border-soft-gold/50'
              }`}
            >{c.name}</button>
          ))}
        </div>
      )}

      <div className="flex items-center gap-3">
        <button type="button" onClick={handleSave} disabled={saving}
          className="px-5 py-2 bg-soft-gold text-deep-navy font-body text-small font-semibold rounded-xl hover:bg-bright-gold disabled:opacity-40 transition-colors">
          {saving ? 'Saving…' : 'Save reach'}
        </button>
        {saved && <span className="font-body text-small text-green-600">Saved!</span>}
        {error && <span className="font-body text-small text-red-500">{error}</span>}
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
  coordinator_name: string
  skill_level: string
  what_to_bring: string
  waiver_url: string
  parking_info: string
  safetyAck: boolean
}

const EMPTY_FORM: EventFormData = {
  title: '', description: '', event_date: '', start_time: '', end_time: '',
  location_city: '', location_state: '', location_zip: '',
  is_virtual: false, signup_url: '', contact_email: '', capacity: '',
  coordinator_name: '',
  skill_level: 'any', what_to_bring: '', waiver_url: '', parking_info: '',
  safetyAck: false,
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
  const hasExistingDetails = !!(initial?.coordinator_name || initial?.what_to_bring || initial?.waiver_url || initial?.parking_info || (initial?.skill_level && initial.skill_level !== 'any'))
  const [showDetails, setShowDetails] = useState(hasExistingDetails)

  return (
    <div className="border border-soft-gold/30 rounded-xl p-5 bg-warm-cream space-y-4">
      <label className="block">
        <span className="block font-body text-caption font-medium text-deep-navy mb-1">Event title *</span>
        <input
          type="text" required maxLength={200}
          value={form.title} onChange={e => set('title', e.target.value)}
          placeholder="e.g. Community Garden Workday"
          className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
          disabled={saving}
        />
      </label>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <label className="block">
          <span className="block font-body text-caption font-medium text-deep-navy mb-1">Date *</span>
          <input
            type="date" required
            value={form.event_date} onChange={e => set('event_date', e.target.value)}
            className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy focus:outline-none focus:border-soft-gold/60"
            disabled={saving}
          />
        </label>
        <label className="block">
          <span className="block font-body text-caption font-medium text-deep-navy mb-1">Start time</span>
          <input
            type="time"
            value={form.start_time} onChange={e => set('start_time', e.target.value)}
            className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy focus:outline-none focus:border-soft-gold/60"
            disabled={saving}
          />
        </label>
        <label className="block">
          <span className="block font-body text-caption font-medium text-deep-navy mb-1">End time</span>
          <input
            type="time"
            value={form.end_time} onChange={e => set('end_time', e.target.value)}
            className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy focus:outline-none focus:border-soft-gold/60"
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
        <span className="font-body text-body text-cool-grey">This is a virtual event</span>
      </label>

      {!form.is_virtual && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <label className="block">
            <span className="block font-body text-caption font-medium text-deep-navy mb-1">City</span>
            <input
              type="text" maxLength={100}
              value={form.location_city} onChange={e => set('location_city', e.target.value)}
              placeholder="Austin"
              className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
              disabled={saving}
            />
          </label>
          <label className="block">
            <span className="block font-body text-caption font-medium text-deep-navy mb-1">State</span>
            <select
              value={form.location_state} onChange={e => set('location_state', e.target.value)}
              className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy focus:outline-none focus:border-soft-gold/60 bg-white"
              disabled={saving}
            >
              <option value="">—</option>
              {US_STATES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label className="block">
            <span className="block font-body text-caption font-medium text-deep-navy mb-1">Zip code</span>
            <input
              type="text" maxLength={10} inputMode="numeric"
              value={form.location_zip} onChange={e => set('location_zip', e.target.value)}
              placeholder="78701"
              className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
              disabled={saving}
            />
          </label>
        </div>
      )}

      <label className="block">
        <span className="block font-body text-caption font-medium text-deep-navy mb-1">Description</span>
        <textarea
          rows={3} maxLength={1000}
          value={form.description} onChange={e => set('description', e.target.value)}
          placeholder="What will volunteers do? Who is this for?"
          className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60 resize-none"
          disabled={saving}
        />
      </label>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label className="block">
          <span className="block font-body text-caption font-medium text-deep-navy mb-1">Sign-up link</span>
          <input
            type="url" maxLength={500}
            value={form.signup_url} onChange={e => set('signup_url', e.target.value)}
            placeholder="https://..."
            className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
            disabled={saving}
          />
          <p className="mt-1 font-body text-label text-cool-grey">Link to your own sign-up form</p>
        </label>
        <label className="block">
          <span className="block font-body text-caption font-medium text-deep-navy mb-1">Contact email (fallback)</span>
          <input
            type="email" maxLength={200}
            value={form.contact_email} onChange={e => set('contact_email', e.target.value)}
            placeholder="volunteer@org.org"
            className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
            disabled={saving}
          />
        </label>
      </div>

      <label className="block w-40">
        <span className="block font-body text-caption font-medium text-deep-navy mb-1">Volunteer capacity</span>
        <input
          type="number" min={1} max={9999}
          value={form.capacity} onChange={e => set('capacity', e.target.value)}
          placeholder="Unlimited"
          className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
          disabled={saving}
        />
      </label>

      <label className="block">
        <span className="block font-body text-caption font-medium text-deep-navy mb-1">Volunteer coordinator name</span>
        <input
          type="text" maxLength={100}
          value={form.coordinator_name} onChange={e => set('coordinator_name', e.target.value)}
          placeholder="e.g. Maria Chen"
          className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
          disabled={saving}
        />
        <p className="mt-1 font-body text-label text-cool-grey">Shown to volunteers so they know who to look for. You'll also receive signup emails.</p>
      </label>

      {/* Volunteer prep — collapsible; helps volunteers show up ready */}
      <div className="pt-2 border-t border-light-grey/60">
        <button
          type="button"
          onClick={() => setShowDetails(v => !v)}
          className="flex items-center gap-1.5 font-body text-caption font-semibold text-cool-grey tracking-[0.06em] uppercase hover:text-deep-navy transition-colors"
        >
          <svg
            width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
            className={`transition-transform ${showDetails ? 'rotate-90' : ''}`}
          >
            <polyline points="9 18 15 12 9 6"/>
          </svg>
          {showDetails ? 'Hide prep details' : 'Add prep details (optional)'}
        </button>
        {showDetails && (
          <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="block">
              <span className="block font-body text-caption font-medium text-deep-navy mb-1">Skill level needed</span>
              <select
                value={form.skill_level} onChange={e => set('skill_level', e.target.value)}
                className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy bg-white focus:outline-none focus:border-soft-gold/60"
                disabled={saving}
              >
                <option value="any">Anyone welcome</option>
                <option value="beginner">Beginner friendly</option>
                <option value="intermediate">Some experience helpful</option>
                <option value="skilled">Skilled volunteers only</option>
              </select>
            </label>
            <label className="block">
              <span className="block font-body text-caption font-medium text-deep-navy mb-1">Waiver URL</span>
              <input
                type="url" maxLength={500}
                value={form.waiver_url} onChange={e => set('waiver_url', e.target.value)}
                placeholder="https://..."
                className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
                disabled={saving}
              />
              <p className="mt-1 font-body text-label text-cool-grey">Link to liability waiver if required</p>
            </label>
            <label className="block">
              <span className="block font-body text-caption font-medium text-deep-navy mb-1">What to bring</span>
              <input
                type="text" maxLength={500}
                value={form.what_to_bring} onChange={e => set('what_to_bring', e.target.value)}
                placeholder="e.g. Gloves, closed-toe shoes, water bottle"
                className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
                disabled={saving}
              />
            </label>
            <label className="block">
              <span className="block font-body text-caption font-medium text-deep-navy mb-1">Parking and transit</span>
              <input
                type="text" maxLength={300}
                value={form.parking_info} onChange={e => set('parking_info', e.target.value)}
                placeholder="e.g. Free parking on Oak St, bus route 12"
                className="w-full px-3 py-2.5 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder:text-muted-cream focus:outline-none focus:border-soft-gold/60"
                disabled={saving}
              />
            </label>
          </div>
        )}
      </div>

      <label className="flex items-start gap-2.5 cursor-pointer pt-1">
        <input
          type="checkbox"
          checked={form.safetyAck}
          onChange={e => set('safetyAck', e.target.checked)}
          className="mt-0.5 accent-soft-gold shrink-0"
        />
        <span className="font-body text-caption text-cool-grey leading-[1.6]">
          Our organization is responsible for the safety of this event, including appropriate insurance and compliance with local requirements. Daanaa does not organize, supervise, or insure volunteer events.
        </span>
      </label>
      <div className="flex gap-3 pt-1">
        <button
          type="button"
          onClick={() => onSave(form)}
          disabled={saving || !form.title || !form.event_date || !form.safetyAck}
          className="px-5 py-2.5 bg-soft-gold text-deep-navy rounded-xl font-body text-body font-semibold hover:bg-bright-gold transition-colors disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save event'}
        </button>
        <button
          type="button" onClick={onCancel} disabled={saving}
          className="px-5 py-2.5 border border-light-cream text-cool-grey rounded-xl font-body text-body hover:border-soft-gold/40 transition-colors"
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
        contact_email:    data.contact_email || null,
        capacity:         data.capacity ? Number(data.capacity) : null,
        coordinator_name: data.coordinator_name || null,
        skill_level:      (data.skill_level || 'any') as 'any' | 'beginner' | 'intermediate' | 'skilled',
        what_to_bring:    data.what_to_bring || null,
        waiver_url:       data.waiver_url || null,
        parking_info:     data.parking_info || null,
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
        contact_email:    data.contact_email || null,
        capacity:         data.capacity ? Number(data.capacity) : null,
        coordinator_name: data.coordinator_name || null,
        skill_level:      (data.skill_level || 'any') as 'any' | 'beginner' | 'intermediate' | 'skilled',
        what_to_bring:    data.what_to_bring || null,
        waiver_url:       data.waiver_url || null,
        parking_info:     data.parking_info || null,
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
      cancelled: 'bg-destructive/5 text-destructive',
      expired: 'bg-light-cream text-muted-cream',
    }
    return (
      <span className={`px-2 py-0.5 rounded-full font-body text-micro font-semibold uppercase tracking-[0.06em] ${map[s] ?? ''}`}>
        {s}
      </span>
    )
  }

  return (
    <div className="border-t border-light-cream pt-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-body text-small font-medium text-deep-navy">Volunteer events</h3>
          <p className="font-body text-caption text-cool-grey mt-0.5">
            Events appear on the public volunteer search page. They expire automatically after their date.
          </p>
        </div>
        {!showForm && (
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-soft-gold/15 text-soft-gold rounded-lg font-body text-small font-semibold hover:bg-soft-gold/25 transition-colors"
          >
            + Add event
          </button>
        )}
      </div>

      {error && (
        <p className="font-body text-small text-destructive">{error}</p>
      )}

      {showForm && (
        <EventForm
          onSave={handleCreate}
          onCancel={() => setShowForm(false)}
          saving={saving}
        />
      )}

      {loading && <p className="font-body text-small text-cool-grey">Loading events...</p>}

      {!loading && events.length === 0 && !showForm && (
        <p className="font-body text-small text-cool-grey">No events yet. Add your first volunteer opportunity.</p>
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
                coordinator_name: ev.coordinator_name ?? '',
                skill_level: ev.skill_level ?? 'any', what_to_bring: ev.what_to_bring ?? '',
                waiver_url: ev.waiver_url ?? '', parking_info: ev.parking_info ?? '',
                safetyAck: true,
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
                  <span className="font-body text-caption text-cool-grey">{formatDate(ev.event_date)}</span>
                </div>
                <p className="font-body text-body-lg font-medium text-deep-navy">{ev.title}</p>
                {ev.location_city && !ev.is_virtual && (
                  <p className="font-body text-caption text-cool-grey mt-0.5">
                    {[ev.location_city, ev.location_state].filter(Boolean).join(', ')}
                  </p>
                )}
                {ev.is_virtual && (
                  <p className="font-body text-caption text-cool-grey mt-0.5">Virtual</p>
                )}
              </div>
              {ev.status !== 'expired' && ev.status !== 'cancelled' && (
                <div className="flex gap-2 shrink-0">
                  <button
                    type="button" onClick={() => setEditId(ev.id)} disabled={saving}
                    className="font-body text-caption text-soft-gold hover:text-bright-gold font-semibold"
                  >
                    Edit
                  </button>
                  <button
                    type="button" onClick={() => handleCancel(ev.id)} disabled={saving}
                    className="font-body text-caption text-cool-grey hover:text-red-500"
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
  const [websiteUrl, setWebsiteUrl] = useState('')
  const [donateUrl, setDonateUrl] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [org, setOrg] = useState<ApiOrganization | null>(null)
  const [showUpdateForm, setShowUpdateForm] = useState(false)
  const [loadingOrg, setLoadingOrg] = useState(true)

  const ein = searchParams.get('ein') || ''
  const token = searchParams.get('token') || ''

  useEffect(() => {
    if (!ein || !token) navigate('/for-nonprofits', { replace: true })
  }, [ein, token, navigate])

  useEffect(() => {
    if (!ein) return
    getOrganization(ein)
      .then(setOrg)
      .catch(() => {})
      .finally(() => setLoadingOrg(false))
  }, [ein])

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
          website_url: websiteUrl || undefined,
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
    <div className="min-h-[100dvh] bg-warm-cream pt-nav">
      <div className="max-w-[560px] mx-auto px-6 py-12">
        <ClaimProgressBar currentStep="edit" />

        {/* Data Transparency Section */}
        {!loadingOrg && org && (
          <div className="mb-8">
            <ResearchDataTransparency org={org} onUpdateClick={() => setShowUpdateForm(true)} />

            {showUpdateForm && (
              <div className="mt-6 p-6 bg-blue-50 border border-blue-200 rounded-2xl">
                <h3 className="font-display text-lead font-semibold text-deep-navy mb-4">
                  Update Your Financial Information
                </h3>
                <DataUpdateForm
                  org={org}
                  claimToken={token}
                  ein={ein}
                  onSuccess={() => setShowUpdateForm(false)}
                  onCancel={() => setShowUpdateForm(false)}
                />
              </div>
            )}
          </div>
        )}

        <div className="text-center mb-8">
          <h1 className="font-display italic text-deep-navy mb-2">
            Tell your story
          </h1>
          <p className="font-body text-body-lg text-cool-grey">All fields are optional. Add what you can. You can always come back.</p>
        </div>
        <form onSubmit={handleSave} className="bg-white rounded-2xl shadow-sm border border-light-cream p-8 space-y-6">
          {error && (
            <div className="p-4 bg-destructive/5 border border-destructive/20 rounded-xl">
              <p className="font-body text-body text-destructive">{error}</p>
            </div>
          )}
          <label className="block">
            <span className="block font-body text-small font-medium text-deep-navy mb-2">Mission statement <span className="text-cool-grey font-normal">(1–2 sentences)</span></span>
            <textarea
              value={mission} onChange={e => setMission(e.target.value.slice(0, 300))}
              placeholder="What does your organization do and who do you serve?"
              rows={3}
              className="w-full px-4 py-3 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold resize-none"
              disabled={saving}
            />
            <p className="mt-1 font-body text-label text-cool-grey">{mission.length}/300</p>
          </label>
          <label className="block">
            <span className="block font-body text-small font-medium text-deep-navy mb-2">Programs and impact <span className="text-cool-grey font-normal">(optional)</span></span>
            <textarea
              value={description} onChange={e => setDescription(e.target.value.slice(0, 500))}
              placeholder="Describe your programs, service area, or recent impact..."
              rows={4}
              className="w-full px-4 py-3 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold resize-none"
              disabled={saving}
            />
            <p className="mt-1 font-body text-label text-cool-grey">{description.length}/500</p>
          </label>
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-1">
              <div className="h-px flex-1 bg-light-cream" />
              <span className="font-body text-label font-semibold text-cool-grey uppercase tracking-wider px-2">How donors can reach you</span>
              <div className="h-px flex-1 bg-light-cream" />
            </div>
            <label className="block">
              <span className="block font-body text-small font-medium text-deep-navy mb-1">
                Official website
                <span className="ml-1.5 font-normal text-cool-grey">(optional)</span>
              </span>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                </span>
                <input
                  type="url" value={websiteUrl} onChange={e => setWebsiteUrl(e.target.value)}
                  placeholder="https://yourorg.org"
                  className="w-full pl-9 pr-4 py-3 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold"
                  disabled={saving}
                />
              </div>
              <p className="mt-1 font-body text-label text-cool-grey">Your main homepage. Donors see this as the primary link on your page.</p>
            </label>
            <label className="block">
              <span className="block font-body text-small font-medium text-deep-navy mb-1">
                Direct donation link
                <span className="ml-1.5 font-normal text-cool-grey">(optional)</span>
              </span>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                </span>
                <input
                  type="url" value={donateUrl} onChange={e => setDonateUrl(e.target.value)}
                  placeholder="https://yourorg.org/donate"
                  className="w-full pl-9 pr-4 py-3 border border-light-cream rounded-xl font-body text-body text-deep-navy placeholder-muted-cream focus:outline-none focus:ring-2 focus:ring-soft-gold"
                  disabled={saving}
                />
              </div>
              <p className="mt-1 font-body text-label text-cool-grey">The page where donors can give directly. Can be a PayPal, Stripe, or your own donation page.</p>
            </label>
          </div>
          <fieldset>
            <legend className="font-body text-small font-medium text-deep-navy mb-3">Focus areas <span className="text-cool-grey font-normal">(select all that apply)</span></legend>
            <div className="flex flex-wrap gap-2">
              {CAUSE_TAGS.map(tag => (
                <button
                  key={tag} type="button" onClick={() => toggleTag(tag)} disabled={saving}
                  className={`px-3 py-1.5 rounded-full font-body text-small border transition-colors ${
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
            className="w-full px-4 py-3 bg-soft-gold text-deep-navy font-body text-body-lg font-semibold rounded-xl hover:bg-bright-gold disabled:opacity-40 transition-colors"
          >
            {saving ? 'Saving...' : 'Save and publish'}
          </button>
        </form>
      </div>
    </div>
  )
}
