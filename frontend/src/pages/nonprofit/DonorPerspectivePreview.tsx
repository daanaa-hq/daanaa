import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { usePageMeta } from '../../hooks/usePageMeta'
import { API_BASE } from '../../data/api'

interface SourceInfo {
  value: string | null
  source: string
  source_label: string
  editable: boolean
}

interface ProfileSources {
  ein: string
  sources: Record<string, SourceInfo>
}

export default function DonorPerspectivePreview() {
  const { ein } = useParams<{ ein: string }>()
  const navigate = useNavigate()
  const { user, loading: authLoading } = useAuth()
  usePageMeta('Donor Preview | Daanaa', 'See your organization profile from a donor perspective.')

  const [profile, setProfile] = useState<ProfileSources | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (authLoading || !user) return
    if (!ein) {
      navigate('/nonprofit/my-orgs', { replace: true })
      return
    }

    // Load public profile sources
    fetch(`${API_BASE}/api/public/nonprofit/${ein}/profile/sources`)
      .then(async res => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(body.error || 'Failed to load profile')
        }
        return res.json()
      })
      .then(setProfile)
      .catch(err => setError(err instanceof Error ? err.message : 'Could not load profile'))
      .finally(() => setLoading(false))
  }, [ein, user, authLoading, navigate])

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-cream">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-deep-navy" />
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen bg-warm-cream px-6 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-destructive/5 border border-destructive/20 rounded-xl p-6 text-destructive">
            <h2 className="font-display text-lg mb-2">Could not load profile</h2>
            <p className="font-body text-body mb-4">{error}</p>
            <button
              onClick={() => navigate('/nonprofit/my-orgs')}
              className="px-4 py-2 bg-red-100 hover:bg-red-200 rounded-lg font-body text-body font-semibold transition"
            >
              Back
            </button>
          </div>
        </div>
      </div>
    )
  }

  const sourceIcons: Record<string, string> = {
    'irs': '📋',
    'nonprofit_supplied': '✏️',
    'ai_generated': '🤖',
    'daanaa_corrected': '✓'
  }

  return (
    <div className="min-h-screen bg-warm-cream px-6 py-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate(`/nonprofit/profile/${ein}`)}
            className="text-soft-gold hover:text-bright-gold font-body text-body font-semibold mb-4"
          >
            ← Back to Edit Profile
          </button>
          <h1 className="font-display text-3xl text-deep-navy mb-2">Donor Perspective Preview</h1>
          <p className="font-body text-body text-cool-grey">
            This is exactly how donors and volunteers see your organization on Daanaa
          </p>
        </div>

        {/* Info Box */}
        <div className="mb-8 p-4 bg-blue-50 border border-blue-200 rounded-xl">
          <p className="font-body text-small text-blue-900">
            <strong>💡 Tip:</strong> Everything shown here is public. The "Source" labels below help donors understand where information comes from.
          </p>
        </div>

        {/* Simulated Profile Card */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
          {/* Profile Header */}
          <div className="bg-gradient-to-r from-soft-gold to-bright-gold px-6 py-8">
            <h2 className="font-display text-2xl text-deep-navy">{profile.ein}</h2>
            <p className="font-body text-body text-deep-navy mt-1">EIN: {profile.ein}</p>
          </div>

          {/* Profile Content */}
          <div className="p-6 space-y-6">
            {/* Mission */}
            {profile.sources.organization_name?.value && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">{sourceIcons[profile.sources.organization_name.source] || '📌'}</span>
                  <h3 className="font-display text-lg text-deep-navy">Organization</h3>
                </div>
                <p className="font-body text-body text-cool-grey mb-1">{profile.sources.organization_name.source_label}</p>
                <p className="font-body text-body text-deep-navy">{profile.sources.organization_name.value}</p>
              </div>
            )}

            {/* Mission */}
            {profile.sources.mission?.value && (
              <div className="pt-4 border-t border-light-grey">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">{sourceIcons[profile.sources.mission.source] || '📌'}</span>
                  <h3 className="font-display text-lg text-deep-navy">Mission</h3>
                </div>
                <p className="font-body text-small text-cool-grey mb-2">{profile.sources.mission.source_label}</p>
                <p className="font-body text-body text-deep-navy leading-relaxed">
                  {profile.sources.mission.value}
                </p>
                {profile.sources.mission.editable && (
                  <button
                    onClick={() => navigate(`/nonprofit/profile/${ein}`)}
                    className="mt-3 text-soft-gold hover:text-bright-gold font-body text-small font-semibold"
                  >
                    Edit this field →
                  </button>
                )}
              </div>
            )}

            {/* Website */}
            {profile.sources.website?.value && (
              <div className="pt-4 border-t border-light-grey">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">{sourceIcons[profile.sources.website.source] || '📌'}</span>
                  <h3 className="font-display text-lg text-deep-navy">Website</h3>
                </div>
                <p className="font-body text-small text-cool-grey mb-2">{profile.sources.website.source_label}</p>
                <a
                  href={profile.sources.website.value}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-body text-body text-soft-gold hover:text-bright-gold underline break-all"
                >
                  {profile.sources.website.value}
                </a>
              </div>
            )}

            {/* Donate URL */}
            {profile.sources.donate_url?.value && (
              <div className="pt-4 border-t border-light-grey">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">{sourceIcons[profile.sources.donate_url.source] || '📌'}</span>
                  <h3 className="font-display text-lg text-deep-navy">How to Donate</h3>
                </div>
                <p className="font-body text-small text-cool-grey mb-2">{profile.sources.donate_url.source_label}</p>
                <a
                  href={profile.sources.donate_url.value}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block px-4 py-2.5 rounded-lg bg-soft-gold text-deep-navy font-body text-small font-semibold hover:bg-bright-gold transition"
                >
                  Donate Now →
                </a>
              </div>
            )}

            {/* Programs */}
            {profile.sources.programs?.value && (
              <div className="pt-4 border-t border-light-grey">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">{sourceIcons[profile.sources.programs.source] || '📌'}</span>
                  <h3 className="font-display text-lg text-deep-navy">Programs & Services</h3>
                </div>
                <p className="font-body text-small text-cool-grey mb-2">{profile.sources.programs.source_label}</p>
                <p className="font-body text-body text-deep-navy whitespace-pre-wrap">
                  {profile.sources.programs.value}
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="bg-light-grey/20 px-6 py-4 border-t border-light-grey">
            <p className="font-body text-label text-cool-grey">
              Profile data comes from IRS Form 990, nonprofit-supplied information, and Daanaa enhancement.
              <br />
              Last updated: {new Date().toLocaleDateString()}
            </p>
          </div>
        </div>

        {/* Source Legend */}
        <div className="mt-8 p-6 bg-white rounded-2xl shadow-sm">
          <h3 className="font-display text-lg text-deep-navy mb-4">Understanding Data Sources</h3>
          <div className="space-y-3">
            <div className="flex gap-3">
              <span className="text-lg min-w-fit">📋</span>
              <div>
                <p className="font-body text-small font-semibold text-deep-navy">IRS Form 990</p>
                <p className="font-body text-caption text-cool-grey">Official public records from the IRS</p>
              </div>
            </div>
            <div className="flex gap-3">
              <span className="text-lg min-w-fit">✏️</span>
              <div>
                <p className="font-body text-small font-semibold text-deep-navy">Nonprofit-supplied</p>
                <p className="font-body text-caption text-cool-grey">Information added or edited by your organization</p>
              </div>
            </div>
            <div className="flex gap-3">
              <span className="text-lg min-w-fit">🤖</span>
              <div>
                <p className="font-body text-small font-semibold text-deep-navy">AI-generated</p>
                <p className="font-body text-caption text-cool-grey">Created by Daanaa to help organize or summarize information</p>
              </div>
            </div>
            <div className="flex gap-3">
              <span className="text-lg min-w-fit">✓</span>
              <div>
                <p className="font-body text-small font-semibold text-deep-navy">Corrected</p>
                <p className="font-body text-caption text-cool-grey">Updated by Daanaa to fix errors or improve accuracy</p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
          <button
            onClick={() => navigate(`/nonprofit/profile/${ein}`)}
            className="px-6 py-3 rounded-lg bg-soft-gold text-deep-navy font-body text-body font-semibold hover:bg-bright-gold transition"
          >
            ✏️ Edit Profile
          </button>
          <button
            onClick={() => navigate(`/nonprofit/overview/${ein}`)}
            className="px-6 py-3 rounded-lg bg-deep-navy text-warm-cream font-body text-body font-semibold hover:bg-opacity-90 transition"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  )
}
