import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { normalizeExternalUrl } from '../utils/externalLink'
import { API_BASE } from '../data/api'

interface Guild {
  guild_id: number
  guild_name: string
  slug: string
  website?: string
  tier: 'free' | 'pro' | 'enterprise'
  benefits: Array<{
    tier: string
    feature_name: string
    description: string
  }>
}

interface GuildSectionProps {
  ein: string
}

const TIER_COLORS: Record<string, { bg: string; text: string; badge: string }> = {
  free: { bg: 'bg-blue-50', text: 'text-blue-900', badge: 'bg-blue-100 text-blue-800' },
  pro: { bg: 'bg-purple-50', text: 'text-purple-900', badge: 'bg-purple-100 text-purple-800' },
  enterprise: { bg: 'bg-alert-amber/5', text: 'text-amber-900', badge: 'bg-amber-100 text-amber-800' },
}

export default function GuildSection({ ein }: GuildSectionProps) {
  const [guild, setGuild] = useState<Guild | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchGuild() {
      try {
        // Fixed 2026-08-21 (LESSONS.md same date): was hardcoded to
        // http://localhost:5000, broken for every real visitor -- found via
        // a Codex-assisted frontend<->backend interconnection audit.
        const res = await fetch(`${API_BASE}/api/org/${ein}/guild`)
        const data = await res.json()
        if (data.guild_id) {
          setGuild(data)
        }
      } catch {
        // Silent fail — guild not found or API error
      } finally {
        setLoading(false)
      }
    }
    fetchGuild()
  }, [ein])

  if (loading || !guild) return null

  const colors = TIER_COLORS[guild.tier] || TIER_COLORS.free

  return (
    <div className={`${colors.bg} border border-light-grey rounded-2xl p-6 mt-6`}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <h3 className={`font-display italic text-title ${colors.text}`}>
              {guild.guild_name}
            </h3>
            <span className={`${colors.badge} px-2.5 py-1 rounded-full text-caption font-semibold uppercase`}>
              {guild.tier}
            </span>
          </div>
          {guild.website && (
            <a href={normalizeExternalUrl(guild.website) || undefined} target="_blank" rel="noopener noreferrer" className="text-soft-gold hover:underline text-body">
              Visit partner →
            </a>
          )}
        </div>
        <Link to={`/partner/${guild.slug}`} className="text-soft-gold hover:underline text-small font-semibold">
          View benefits
        </Link>
      </div>

      {guild.benefits && guild.benefits.length > 0 && (
        <div className="space-y-2">
          <p className="text-caption text-cool-grey font-semibold uppercase tracking-wide mb-3">
            {guild.tier} benefits
          </p>
          {guild.benefits.map((benefit, idx) => (
            <div key={idx} className="flex gap-3 text-small">
              <span className="shrink-0 text-soft-gold">✓</span>
              <div>
                <div className={`font-semibold ${colors.text}`}>{benefit.feature_name}</div>
                {benefit.description && (
                  <div className="text-cool-grey text-caption">{benefit.description}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
