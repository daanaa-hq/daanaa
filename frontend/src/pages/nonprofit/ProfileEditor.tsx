import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { usePageMeta } from '../../hooks/usePageMeta'
import { API_BASE } from '../../data/api'
import ProfileEditModal from '../../components/nonprofit/ProfileEditModal'
import ProfileChangeHistory from '../../components/nonprofit/ProfileChangeHistory'
import HelpTooltip from '../../components/nonprofit/HelpTooltip'

interface EditableFields {
  mission: { value: string; source: string; editable: boolean; char_limit: number; char_count?: number }
  website: { value: string; source: string; editable: boolean }
  donate_url: { value: string; source: string; editable: boolean }
  programs: { value: string; source: string; editable: boolean; char_limit: number; char_count?: number }
  service_areas: { value: string; source: string; editable: boolean }
}

interface RecentEdit {
  field: string
  old_value: string
  new_value: string
  date: string
  editor: string
  reason: string
  status: string
}

interface ProfileData {
  organization: { ein: string; name: string }
  editable_fields: EditableFields
  recent_edits: RecentEdit[]
}

export default function ProfileEditor() {
  const { ein } = useParams<{ ein: string }>()
  const navigate = useNavigate()
  const { user, loading: authLoading } = useAuth()
  usePageMeta('Edit Profile | Daanaa', 'Correct and enhance your organization profile.')

  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingField, setEditingField] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null)
  const [tab, setTab] = useState<'overview' | 'history'>('overview')

  useEffect(() => {
    if (authLoading || !user) return
    if (!ein) {
      navigate('/nonprofit/my-orgs', { replace: true })
      return
    }

    fetch(`${API_BASE}/api/nonprofit/${ein}/profile/editable`)
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

  const handleEditSave = async (fieldName: string, newValue: string, reason: string): Promise<void> => {
    try {
      const res = await fetch(`${API_BASE}/api/nonprofit/${ein}/profile/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          field_name: fieldName,
          new_value: newValue,
          reason,
          nonprofit_email: user?.email || 'nonprofit@example.com'
        })
      })

      const body = await res.json()
      if (!res.ok) {
        throw new Error(body.error || 'Failed to save changes')
      }

      setSaveSuccess(body.message || 'Changes saved')
      setEditingField(null)

      // Reload profile data
      setTimeout(() => {
        window.location.reload()
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save changes')
    }
  }

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
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-700">
            <h2 className="font-display text-lg mb-2">Could not load profile</h2>
            <p className="font-body text-[14px] mb-4">{error}</p>
            <button
              onClick={() => navigate('/nonprofit/my-orgs')}
              className="px-4 py-2 bg-red-100 hover:bg-red-200 rounded-lg font-body text-[14px] font-semibold transition"
            >
              Back
            </button>
          </div>
        </div>
      </div>
    )
  }

  const sourceLabels: Record<string, string> = {
    irs: '📋 IRS Form 990',
    nonprofit_supplied: '✏️ Nonprofit-supplied',
    ai_generated: '🤖 AI-generated',
    daanaa_corrected: '✓ Corrected by Daanaa'
  }

  return (
    <div className="min-h-screen bg-warm-cream px-6 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate(`/nonprofit/overview/${ein}`)}
            className="text-soft-gold hover:text-bright-gold font-body text-[14px] font-semibold mb-4"
          >
            ← Back to Dashboard
          </button>
          <h1 className="font-display text-3xl text-deep-navy mb-1">Edit Profile</h1>
          <p className="font-body text-[14px] text-cool-grey">{profile.organization.name}</p>
        </div>

        {/* Success Message */}
        {saveSuccess && (
          <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-700 font-body text-[14px]">
            ✓ {saveSuccess}
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-light-grey">
          <button
            onClick={() => setTab('overview')}
            className={`px-4 py-3 font-body text-[14px] font-semibold border-b-2 transition ${
              tab === 'overview'
                ? 'border-deep-navy text-deep-navy'
                : 'border-transparent text-cool-grey hover:text-deep-navy'
            }`}
            aria-label="Edit profile fields"
          >
            Profile Fields
          </button>
          <button
            onClick={() => setTab('history')}
            className={`px-4 py-3 font-body text-[14px] font-semibold border-b-2 transition ${
              tab === 'history'
                ? 'border-deep-navy text-deep-navy'
                : 'border-transparent text-cool-grey hover:text-deep-navy'
            }`}
            aria-label={`View change history (${profile.recent_edits.length} edits)`}
          >
            Change History ({profile.recent_edits.length})
          </button>
        </div>

        {/* Overview Tab */}
        {tab === 'overview' && (
          <div className="space-y-6">
            {/* Mission */}
            <div className="bg-white rounded-2xl shadow-sm p-6" role="region" aria-label="Mission statement">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h2 className="font-display text-lg text-deep-navy">Mission</h2>
                    <HelpTooltip text="A clear, concise statement of what your organization does and why it matters. This is often the first thing donors read." side="right" />
                  </div>
                  <p className="font-body text-[12px] text-cool-grey">{sourceLabels[profile.editable_fields.mission.source]}</p>
                </div>
                {profile.editable_fields.mission.editable && (
                  <button
                    onClick={() => setEditingField('mission')}
                    className="px-3 py-1.5 rounded-lg bg-soft-gold text-deep-navy font-body text-[12px] font-semibold hover:bg-bright-gold transition"
                    aria-label="Edit mission statement"
                  >
                    Edit
                  </button>
                )}
              </div>
              <p className="font-body text-[14px] text-deep-navy leading-relaxed">
                {profile.editable_fields.mission.value || '(Not set)'}
              </p>
              {profile.editable_fields.mission.value && profile.editable_fields.mission.char_count && (
                <p className="font-body text-[11px] text-cool-grey mt-3">
                  {profile.editable_fields.mission.char_count} / {profile.editable_fields.mission.char_limit} characters
                </p>
              )}
            </div>

            {/* Website */}
            <div className="bg-white rounded-2xl shadow-sm p-6" role="region" aria-label="Website URL">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h2 className="font-display text-lg text-deep-navy">Website</h2>
                    <HelpTooltip text="Your main website where donors can learn more about your organization. Must start with https://" side="right" />
                  </div>
                  <p className="font-body text-[12px] text-cool-grey">{sourceLabels[profile.editable_fields.website.source]}</p>
                </div>
                {profile.editable_fields.website.editable && (
                  <button
                    onClick={() => setEditingField('website')}
                    className="px-3 py-1.5 rounded-lg bg-soft-gold text-deep-navy font-body text-[12px] font-semibold hover:bg-bright-gold transition"
                    aria-label="Edit website URL"
                  >
                    Edit
                  </button>
                )}
              </div>
              {profile.editable_fields.website.value ? (
                <a
                  href={profile.editable_fields.website.value}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-body text-[14px] text-soft-gold hover:text-bright-gold underline"
                >
                  {profile.editable_fields.website.value}
                </a>
              ) : (
                <p className="font-body text-[14px] text-cool-grey">(Not set)</p>
              )}
            </div>

            {/* Donation URL */}
            <div className="bg-white rounded-2xl shadow-sm p-6" role="region" aria-label="Donation link">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h2 className="font-display text-lg text-deep-navy">Donation Link</h2>
                    <HelpTooltip text="Where donors can give. This can be your website, a payment processor, or a fundraising platform. A working link is critical." side="right" />
                  </div>
                  <p className="font-body text-[12px] text-cool-grey">{sourceLabels[profile.editable_fields.donate_url.source]}</p>
                </div>
                {profile.editable_fields.donate_url.editable && (
                  <button
                    onClick={() => setEditingField('donate_url')}
                    className="px-3 py-1.5 rounded-lg bg-soft-gold text-deep-navy font-body text-[12px] font-semibold hover:bg-bright-gold transition"
                    aria-label="Edit donation link"
                  >
                    Edit
                  </button>
                )}
              </div>
              {profile.editable_fields.donate_url.value ? (
                <a
                  href={profile.editable_fields.donate_url.value}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-body text-[14px] text-soft-gold hover:text-bright-gold underline"
                >
                  {profile.editable_fields.donate_url.value}
                </a>
              ) : (
                <p className="font-body text-[14px] text-cool-grey">(Not set)</p>
              )}
            </div>

            {/* Programs */}
            <div className="bg-white rounded-2xl shadow-sm p-6" role="region" aria-label="Programs and services">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h2 className="font-display text-lg text-deep-navy">Programs & Services</h2>
                    <HelpTooltip text="What programs do you offer? Who do you serve? Be specific—donors want to understand the impact." side="right" />
                  </div>
                  <p className="font-body text-[12px] text-cool-grey">{sourceLabels[profile.editable_fields.programs.source]}</p>
                </div>
                {profile.editable_fields.programs.editable && (
                  <button
                    onClick={() => setEditingField('programs')}
                    className="px-3 py-1.5 rounded-lg bg-soft-gold text-deep-navy font-body text-[12px] font-semibold hover:bg-bright-gold transition"
                    aria-label="Edit programs and services"
                  >
                    Edit
                  </button>
                )}
              </div>
              <p className="font-body text-[14px] text-deep-navy leading-relaxed whitespace-pre-wrap">
                {profile.editable_fields.programs.value || '(Not set)'}
              </p>
              {profile.editable_fields.programs.value && (
                <p className="font-body text-[11px] text-cool-grey mt-3">
                  {profile.editable_fields.programs.char_count} / {profile.editable_fields.programs.char_limit} characters
                </p>
              )}
            </div>

            {/* Service Areas */}
            <div className="bg-white rounded-2xl shadow-sm p-6" role="region" aria-label="Service areas">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h2 className="font-display text-lg text-deep-navy">Service Areas</h2>
                    <HelpTooltip text="Geographic areas or communities you serve. This helps donors find organizations working in their area." side="right" />
                  </div>
                  <p className="font-body text-[12px] text-cool-grey">{sourceLabels[profile.editable_fields.service_areas.source]}</p>
                </div>
                {profile.editable_fields.service_areas.editable && (
                  <button
                    onClick={() => setEditingField('service_areas')}
                    className="px-3 py-1.5 rounded-lg bg-soft-gold text-deep-navy font-body text-[12px] font-semibold hover:bg-bright-gold transition"
                    aria-label="Edit service areas"
                  >
                    Edit
                  </button>
                )}
              </div>
              <p className="font-body text-[14px] text-deep-navy">
                {profile.editable_fields.service_areas.value || '(Not set)'}
              </p>
            </div>
          </div>
        )}

        {/* History Tab */}
        {tab === 'history' && (
          <ProfileChangeHistory ein={ein!} edits={profile.recent_edits} />
        )}
      </div>

      {/* Edit Modal */}
      {editingField && (
        <ProfileEditModal
          field={editingField}
          currentValue={profile.editable_fields[editingField as keyof EditableFields]?.value || ''}
          onSave={async (value, reason) => {
            await handleEditSave(editingField, value, reason)
          }}
          onClose={() => setEditingField(null)}
        />
      )}
    </div>
  )
}
