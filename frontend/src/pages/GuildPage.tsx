import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

interface GuildData {
  guild_id: number
  name: string
  slug: string
  website?: string
  benefits: {
    free: Array<{ feature_name: string; description?: string }>
    pro: Array<{ feature_name: string; description?: string }>
    enterprise: Array<{ feature_name: string; description?: string }>
  }
  member_count: number
  members: Array<{ EIN: string; organization_name: string; city?: string; state?: string }>
}

const TIER_INFO = {
  free: { color: 'bg-blue-50 text-blue-900', label: 'Free' },
  pro: { color: 'bg-purple-50 text-purple-900', label: 'Pro' },
  enterprise: { color: 'bg-amber-50 text-amber-900', label: 'Enterprise' },
}

export default function GuildPage() {
  const { slug } = useParams<{ slug: string }>()
  const [guild, setGuild] = useState<GuildData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  usePageMeta(
    guild ? `${guild.name} | Partner Benefits — Daanaa` : 'Partner Benefits — Daanaa',
    'Explore partner benefits and member organizations'
  )

  useEffect(() => {
    async function fetchGuild() {
      try {
        const res = await fetch(`http://localhost:5000/api/guild/${slug}`)
        const data = await res.json()
        if (data.error) {
          setError(data.error)
        } else {
          setGuild(data)
        }
      } catch (err) {
        setError('Failed to load guild information')
      } finally {
        setLoading(false)
      }
    }
    fetchGuild()
  }, [slug])

  if (loading) {
    return (
      <div className="min-h-screen bg-warm-cream flex items-center justify-center">
        <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
      </div>
    )
  }

  if (error || !guild) {
    return (
      <div className="min-h-screen bg-warm-cream px-4 py-16">
        <div className="max-w-2xl mx-auto text-center">
          <h1 className="font-display italic text-deep-navy text-[28px] mb-4">Partner not found</h1>
          <p className="text-cool-grey mb-6">We couldn't find information about this partner.</p>
          <Link to="/partners" className="text-soft-gold hover:underline font-semibold">
            Back to partners →
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-warm-cream">
      {/* Header */}
      <div className="bg-white border-b border-light-grey">
        <div className="max-w-4xl mx-auto px-6 py-12">
          <h1 className="font-display italic text-deep-navy text-[32px] mb-4">{guild.name}</h1>
          {guild.website && (
            <a href={guild.website} target="_blank" rel="noopener noreferrer" className="inline-block text-soft-gold hover:underline font-semibold">
              Visit partner →
            </a>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-12">
        {/* Benefits by Tier */}
        <section className="mb-12">
          <h2 className="font-display italic text-deep-navy text-[24px] mb-8">Benefits</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Object.entries(TIER_INFO).map(([tier, info]) => (
              <div key={tier} className={`${info.color} rounded-2xl p-6 border border-light-grey`}>
                <h3 className="font-semibold text-[16px] uppercase tracking-wide mb-4">{info.label}</h3>
                <ul className="space-y-3">
                  {guild.benefits[tier as keyof typeof guild.benefits].map((benefit, idx) => (
                    <li key={idx} className="flex gap-2 text-[13px]">
                      <span className="shrink-0">✓</span>
                      <div>
                        <div className="font-semibold">{benefit.feature_name}</div>
                        {benefit.description && <div className="text-[12px] opacity-75">{benefit.description}</div>}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        {/* Member Organizations */}
        <section>
          <h2 className="font-display italic text-deep-navy text-[24px] mb-8">
            Member Organizations ({guild.member_count})
          </h2>
          {guild.members.length === 0 ? (
            <div className="bg-white rounded-2xl border border-light-grey p-8 text-center">
              <p className="text-cool-grey">No member organizations yet</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {guild.members.map((org) => (
                <Link
                  key={org.EIN}
                  to={`/org/${org.EIN}`}
                  className="bg-white rounded-lg border border-light-grey p-4 hover:border-soft-gold/40 transition-colors"
                >
                  <h3 className="font-semibold text-deep-navy mb-1 line-clamp-2">{org.organization_name}</h3>
                  {(org.city || org.state) && (
                    <p className="text-[13px] text-cool-grey">
                      {[org.city, org.state].filter(Boolean).join(', ')}
                    </p>
                  )}
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
