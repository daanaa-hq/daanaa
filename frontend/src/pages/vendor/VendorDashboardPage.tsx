import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

interface VendorStats {
  avg_rating: number | null
  rating_count: number
  total_savings: number
  nonprofits_contributed: number
}

interface VendorProfile {
  vendor_id: string
  portal_status: 'pending' | 'active' | 'suspended'
  name: string
  category: string
  description: string
  tagline: string
  website: string
  contact_email: string
  contact_phone: string
  service_areas: string[]
  discount_description: string
  discount_code: string | null
  logo_url: string | null
  active: boolean
  approved_at: string | null
  created_at: string
  stats: VendorStats
}

const API = import.meta.env.VITE_API_URL || 'http://localhost:5000'

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: 'Under Review', color: 'bg-yellow-100 text-yellow-800' },
  active: { label: 'Active', color: 'bg-green-100 text-green-800' },
  suspended: { label: 'Suspended', color: 'bg-red-100 text-red-800' },
}

export default function VendorDashboardPage() {
  const { user, getIdToken, signOut, loading } = useAuth()
  const navigate = useNavigate()
  const [vendor, setVendor] = useState<VendorProfile | null>(null)
  const [fetchError, setFetchError] = useState('')
  const [editing, setEditing] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [saveOk, setSaveOk] = useState(false)
  const [saveBusy, setSaveBusy] = useState(false)
  const [form, setForm] = useState<Partial<VendorProfile>>({})

  useEffect(() => {
    if (!loading && !user) navigate('/vendor/login')
  }, [user, loading, navigate])

  useEffect(() => {
    if (!user) return
    loadVendor()
  }, [user])

  const loadVendor = async () => {
    try {
      const token = await getIdToken()
      const resp = await fetch(`${API}/api/vendor/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (resp.status === 404) {
        navigate('/for-vendors')
        return
      }
      if (!resp.ok) throw new Error('Failed to load vendor profile')
      const data = await resp.json()
      setVendor(data)
      setForm({
        name: data.name,
        description: data.description,
        tagline: data.tagline,
        website: data.website,
        contact_phone: data.contact_phone,
        discount_description: data.discount_description,
      })
    } catch (err) {
      setFetchError('Could not load your vendor profile. Try refreshing.')
    }
  }

  const handleSave = async () => {
    if (!vendor) return
    setSaveBusy(true)
    setSaveError('')
    setSaveOk(false)
    try {
      const token = await getIdToken()
      const resp = await fetch(`${API}/api/vendor/me`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(form),
      })
      if (!resp.ok) {
        const e = await resp.json()
        throw new Error(e.error || 'Save failed')
      }
      await loadVendor()
      setEditing(false)
      setSaveOk(true)
      setTimeout(() => setSaveOk(false), 3000)
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaveBusy(false)
    }
  }

  if (loading || !vendor) {
    return (
      <div className="min-h-screen bg-warm-cream flex items-center justify-center">
        <div className="text-deep-navy">
          {fetchError || 'Loading your dashboard...'}
        </div>
      </div>
    )
  }

  const st = STATUS_LABELS[vendor.portal_status] || STATUS_LABELS.pending

  return (
    <div className="min-h-screen bg-warm-cream">
      {/* Top nav */}
      <header className="bg-white border-b border-light-grey">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <a href="/" className="text-xl font-display text-deep-navy font-bold">daanaa</a>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-500">{user?.email}</span>
            <button
              onClick={() => signOut().then(() => navigate('/vendor/login'))}
              className="text-sm text-slate-500 hover:text-deep-navy"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Status banner */}
        {vendor.portal_status === 'pending' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-sm text-yellow-800">
            <strong>Your application is under review.</strong> Our team approves vendor listings
            within 2 business days. Questions? Email{' '}
            <a href="mailto:partners@daanaa.org" className="underline">partners@daanaa.org</a>.
          </div>
        )}

        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-display font-bold text-deep-navy">{vendor.name}</h1>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${st.color}`}>
                {st.label}
              </span>
            </div>
            <p className="text-sm text-slate-500 mt-1">{vendor.category}</p>
          </div>
          {vendor.active && (
            <a
              href={`/partners/${vendor.vendor_id}`}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-soft-gold hover:underline"
            >
              View public listing →
            </a>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            {
              label: 'Avg Rating',
              value: vendor.stats.avg_rating != null
                ? `${vendor.stats.avg_rating.toFixed(1)} ★`
                : '—',
            },
            { label: 'Reviews', value: vendor.stats.rating_count.toString() },
            {
              label: 'Nonprofits Served',
              value: vendor.stats.nonprofits_contributed.toString(),
            },
            {
              label: 'Total Savings',
              value: vendor.stats.total_savings > 0
                ? `$${vendor.stats.total_savings.toLocaleString()}`
                : '—',
            },
          ].map(s => (
            <div key={s.label} className="bg-white rounded-xl border border-light-grey p-4">
              <p className="text-2xl font-bold text-deep-navy">{s.value}</p>
              <p className="text-xs text-slate-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Profile card */}
        <div className="bg-white rounded-xl border border-light-grey p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-deep-navy">Your Listing</h2>
            {!editing && (
              <button
                onClick={() => setEditing(true)}
                className="text-sm text-soft-gold hover:underline"
              >
                Edit
              </button>
            )}
          </div>

          {!editing ? (
            <dl className="space-y-3 text-sm">
              {[
                { label: 'Name', value: vendor.name },
                { label: 'Tagline', value: vendor.tagline || '—' },
                { label: 'Description', value: vendor.description || '—' },
                { label: 'Website', value: vendor.website || '—' },
                { label: 'Phone', value: vendor.contact_phone || '—' },
                { label: 'Discount offer', value: vendor.discount_description || '—' },
                {
                  label: 'Service areas',
                  value: vendor.service_areas.length
                    ? vendor.service_areas.join(', ')
                    : '—',
                },
              ].map(item => (
                <div key={item.label} className="flex gap-4">
                  <dt className="w-32 text-slate-500 shrink-0">{item.label}</dt>
                  <dd className="text-deep-navy">{item.value}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <div className="space-y-4">
              {[
                { key: 'name', label: 'Name', type: 'text', maxLength: 100 },
                { key: 'tagline', label: 'Tagline (short pitch)', type: 'text', maxLength: 120 },
                { key: 'website', label: 'Website', type: 'url', maxLength: 200 },
                { key: 'contact_phone', label: 'Phone', type: 'tel', maxLength: 30 },
              ].map(f => (
                <div key={f.key}>
                  <label className="block text-xs font-medium text-slate-600 mb-1">
                    {f.label}
                  </label>
                  <input
                    type={f.type}
                    maxLength={f.maxLength}
                    value={(form as Record<string, string>)[f.key] ?? ''}
                    onChange={e =>
                      setForm(prev => ({ ...prev, [f.key]: e.target.value }))
                    }
                    className="w-full px-3 py-2 border border-light-grey rounded-lg text-sm text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold/40"
                  />
                </div>
              ))}

              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  Description
                </label>
                <textarea
                  rows={4}
                  maxLength={500}
                  value={form.description ?? ''}
                  onChange={e => setForm(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-light-grey rounded-lg text-sm text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold/40"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">
                  Discount offer for nonprofits
                </label>
                <textarea
                  rows={2}
                  maxLength={300}
                  value={form.discount_description ?? ''}
                  onChange={e =>
                    setForm(prev => ({ ...prev, discount_description: e.target.value }))
                  }
                  className="w-full px-3 py-2 border border-light-grey rounded-lg text-sm text-deep-navy focus:outline-none focus:ring-2 focus:ring-soft-gold/40"
                />
              </div>

              {saveError && <p className="text-sm text-red-600">{saveError}</p>}

              <div className="flex gap-3">
                <button
                  onClick={handleSave}
                  disabled={saveBusy}
                  className="px-4 py-2 bg-soft-gold text-white text-sm font-medium rounded-lg hover:bg-soft-gold/90 disabled:opacity-50 transition-colors"
                >
                  {saveBusy ? 'Saving...' : 'Save changes'}
                </button>
                <button
                  onClick={() => setEditing(false)}
                  className="px-4 py-2 text-slate-600 text-sm hover:text-deep-navy transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {saveOk && (
            <p className="mt-3 text-sm text-green-600">Changes saved.</p>
          )}
        </div>

        {/* Support */}
        <div className="bg-white rounded-xl border border-light-grey p-6 text-sm text-slate-600">
          <h2 className="font-semibold text-deep-navy mb-2">Need help?</h2>
          <p>
            Email{' '}
            <a href="mailto:partners@daanaa.org" className="text-soft-gold hover:underline">
              partners@daanaa.org
            </a>{' '}
            — our partnerships team reads every message and responds within 2 business days.
          </p>
        </div>
      </main>
    </div>
  )
}
