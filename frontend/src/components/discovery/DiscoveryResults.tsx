import React from 'react'
import { ChevronRight, Redo2, Edit2, RotateCcw, Grid } from 'lucide-react'
import { Link } from 'react-router-dom'

interface Organization {
  ein: string
  organization_name: string
  city: string
  state: string
  website_status?: string
  open_to_volunteers?: boolean
  cause_tags?: string[]
  tax_prd_yr?: number
  mission?: string
}

interface DiscoveryResultsProps {
  title?: string
  subtitle?: string
  closeMatches: Organization[]
  nearbyMatches: Organization[]
  discoveryMix: Organization[]
  onShowAnother?: () => void
  onChangeAnswers?: () => void
  onStartOver?: () => void
  onBrowseDirectory?: () => void
  explanations: Record<string, string>
}

export const DiscoveryResults: React.FC<DiscoveryResultsProps> = ({
  title = 'Here is a starting list to explore',
  subtitle = 'We used your answers to narrow the public directory. We did not rank these organizations by worth or tell you where to give.',
  closeMatches,
  nearbyMatches,
  discoveryMix,
  onShowAnother,
  onChangeAnswers,
  onStartOver,
  onBrowseDirectory,
  explanations,
}) => {
  const isEmpty = closeMatches.length === 0 && nearbyMatches.length === 0 && discoveryMix.length === 0

  if (isEmpty) {
    return (
      <div className="max-w-2xl mx-auto px-4">
        <h2 className="text-3xl font-bold text-deep-navy mb-2">{title}</h2>
        <p className="text-cool-grey mb-8">{subtitle}</p>
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 mb-8">
          <p className="text-deep-navy">
            We did not find organizations matching all of those choices. Nothing is wrong.
            Try a broader place, another cause, or remove one preference.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={onChangeAnswers}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-light-grey text-deep-navy hover:bg-muted-cream transition-colors"
          >
            <Edit2 className="w-4 h-4" />
            Change my answers
          </button>
          <button
            onClick={onBrowseDirectory}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-muted-cream0 hover:bg-soft-gold text-white transition-colors"
          >
            <Grid className="w-4 h-4" />
            Browse the full directory
          </button>
        </div>
      </div>
    )
  }

  const totalResults = closeMatches.length + nearbyMatches.length + discoveryMix.length
  const showTooFew = totalResults < 20

  return (
    <div className="max-w-4xl mx-auto px-4">
      <h2 className="text-3xl font-bold text-deep-navy mb-2">{title}</h2>
      <p className="text-cool-grey mb-8">{subtitle}</p>

      {showTooFew && (
        <div className="bg-muted-cream border border-blue-200 rounded-lg p-4 mb-8 text-sm text-deep-navy">
          We found {totalResults} organizations that fit these choices. You can review these or{' '}
          <button
            onClick={onChangeAnswers}
            className="underline font-medium hover:no-underline"
          >
            broaden the search
          </button>{' '}
          for more possibilities.
        </div>
      )}

      {/* Close Matches */}
      {closeMatches.length > 0 && (
        <div className="mb-12">
          <h3 className="text-lg font-semibold text-deep-navy mb-4">
            Close to what you selected
          </h3>
          <div className="grid gap-4">
            {closeMatches.map((org) => (
              <OrganizationCard
                key={org.ein}
                org={org}
                explanation={explanations[org.ein]}
              />
            ))}
          </div>
        </div>
      )}

      {/* Nearby Matches */}
      {nearbyMatches.length > 0 && (
        <div className="mb-12">
          <h3 className="text-lg font-semibold text-deep-navy mb-4">
            A few nearby possibilities
          </h3>
          <div className="grid gap-4">
            {nearbyMatches.map((org) => (
              <OrganizationCard
                key={org.ein}
                org={org}
                explanation={explanations[org.ein]}
              />
            ))}
          </div>
        </div>
      )}

      {/* Discovery Mix */}
      {discoveryMix.length > 0 && (
        <div className="mb-12">
          <h3 className="text-lg font-semibold text-deep-navy mb-4">
            Something you may not have considered
          </h3>
          <div className="grid gap-4">
            {discoveryMix.map((org) => (
              <OrganizationCard
                key={org.ein}
                org={org}
                explanation={explanations[org.ein]}
              />
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="border-t border-light-grey pt-8 mt-12">
        <div className="flex flex-wrap gap-3">
          {onShowAnother && (
            <button
              onClick={onShowAnother}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-light-grey text-deep-navy hover:bg-muted-cream transition-colors"
            >
              <Redo2 className="w-4 h-4" />
              Show another list
            </button>
          )}
          {onChangeAnswers && (
            <button
              onClick={onChangeAnswers}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-light-grey text-deep-navy hover:bg-muted-cream transition-colors"
            >
              <Edit2 className="w-4 h-4" />
              Change my answers
            </button>
          )}
          {onStartOver && (
            <button
              onClick={onStartOver}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-light-grey text-deep-navy hover:bg-muted-cream transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              Start over
            </button>
          )}
          {onBrowseDirectory && (
            <button
              onClick={onBrowseDirectory}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-muted-cream0 hover:bg-soft-gold text-white transition-colors"
            >
              <Grid className="w-4 h-4" />
              Browse the full directory
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

const OrganizationCard: React.FC<{
  org: Organization
  explanation: string
}> = ({ org, explanation }) => {
  const badges = []
  if (org.website_status === 'ok') badges.push('Website')
  if (org.open_to_volunteers) badges.push('Volunteer')
  if (org.tax_prd_yr && org.tax_prd_yr >= 2023) badges.push('Recent filing')

  return (
    <Link
      to={`/org/${org.ein}`}
      className="block p-5 rounded-lg border border-light-grey hover:shadow-md transition-shadow bg-warm-cream"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-deep-navy mb-1 truncate">
            {org.organization_name}
          </h4>
          <p className="text-sm text-cool-grey mb-3">
            {org.city}, {org.state}
          </p>

          {/* Cause tags */}
          {org.cause_tags && org.cause_tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {org.cause_tags.slice(0, 2).map((tag) => (
                <span
                  key={tag}
                  className="text-xs px-2 py-1 rounded-full bg-muted-cream text-deep-navy"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Badges */}
          {badges.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {badges.map((badge) => (
                <span
                  key={badge}
                  className="text-xs px-2 py-1 rounded-full bg-muted-cream text-deep-navy"
                >
                  ✓ {badge}
                </span>
              ))}
            </div>
          )}

          {/* Explanation */}
          <p className="text-sm text-cool-grey">{explanation}</p>
        </div>

        <ChevronRight className="w-5 h-5 text-cool-grey flex-shrink-0 mt-1" />
      </div>
    </Link>
  )
}
