import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { ClaimProgressBar } from '../components/ClaimProgressBar'

const CAUSE_TAGS = [
  'Arts & Culture','Education','Environment','Health','Community Development',
  'Human Rights','Research','International Aid','Animals','Disaster Relief',
  'Youth Development','Food Security','Housing','Mental Health','Employment',
]

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
