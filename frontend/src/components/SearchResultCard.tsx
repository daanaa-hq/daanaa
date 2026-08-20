import { Link } from 'react-router-dom'
import { ApiOrganization } from '../data/api'

/**
 * SearchResultCard — "Why this matches" inline on search results
 *
 * Displays org name, location, mission, then visible summary of 2–3 key facts
 * (no collapse/expand) with source badges.
 *
 * Research: Perroni et al. (salience in search results drives donations);
 * Nielsen Norman (visible > collapsed patterns).
 */

interface WhyMatchesFact {
  text: string
  source: 'From 990 filing' | 'From website' | 'From IRS data'
}

function extractWhyMatches(org: ApiOrganization): WhyMatchesFact[] {
  const facts: WhyMatchesFact[] = []

  // Skip mission — it's already shown as lead content above.
  // Only show unique facts not visible elsewhere on the card.

  // Fact 1: Geographic reach
  const serviceStates = org.service_scope?.service_states || []
  if (serviceStates.length > 0 || org.STATE) {
    const location =
      serviceStates.length > 1
        ? `Operates in ${serviceStates.join(', ')}`
        : `Based in ${org.STATE || 'Multiple states'}`
    facts.push({
      text: location,
      source: 'From 990 filing'
    })
  }

  // Fact 3: Program efficiency or reserves
  if (org.program_expense_ratio && org.program_expense_ratio >= 65) {
    facts.push({
      text: `${Math.round(org.program_expense_ratio)}% of budget to programs`,
      source: 'From IRS data'
    })
  } else if (org.months_of_reserve !== null && org.months_of_reserve >= 3) {
    facts.push({
      text: `${Math.round(org.months_of_reserve)} months of reserves`,
      source: 'From IRS data'
    })
  }

  return facts.slice(0, 3)
}

export default function SearchResultCard({
  org
}: {
  org: ApiOrganization
}) {
  const whyMatches = extractWhyMatches(org)
  const orgLink = `/org/${org.EIN}`

  return (
    <article className="border border-light-grey rounded-lg p-5 bg-white hover:shadow-md transition-shadow duration-200">
      {/* Clickable Header Area */}
      <Link to={orgLink} className="block group">
        <h3 className="font-body text-base font-semibold text-deep-navy group-hover:text-soft-gold transition-colors">
          {org.organization_name}
        </h3>
        <p className="font-body text-small text-cool-grey">
          {org.CITY && org.STATE ? `${org.CITY}, ${org.STATE}` : org.STATE || 'Location not available'}
        </p>
      </Link>

      {/* Mission snippet */}
      {org.mission && (
        <p className="font-body text-small text-cool-grey leading-relaxed mb-4 mt-3">
          {org.mission.length > 140 ? org.mission.substring(0, 140) + '…' : org.mission}
        </p>
      )}

      {/* Why This Matches Section */}
      {whyMatches.length > 0 && (
        <div className="bg-gradient-to-r from-soft-gold/8 to-transparent border-l-3 border-soft-gold px-3 py-3 rounded-sm mb-4">
          <p className="font-body text-xs font-semibold text-soft-gold uppercase tracking-wide mb-2">
            🎯 Why this matches
          </p>
          <ul className="space-y-2">
            {whyMatches.map((fact, idx) => (
              <li key={idx} className="flex gap-2 items-start">
                <span className="font-body text-small text-deep-navy flex-1">{fact.text}</span>
                <span className="inline-flex items-center gap-1 bg-soft-gold text-white px-2 py-1 rounded-sm font-body text-xs font-medium flex-shrink-0 whitespace-nowrap">
                  {fact.source}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* CTA Buttons (outside Link to prevent navigation conflicts) */}
      <div className="flex gap-3 items-center">
        <Link
          to={orgLink}
          className="flex-1 bg-soft-gold text-white px-4 py-2 rounded-md font-body text-small font-medium hover:bg-bright-gold transition-colors text-center"
        >
          Learn more
        </Link>
        <button
          onClick={(e) => {
            e.preventDefault()
            // TODO: Wire to Wallet context
          }}
          className="px-4 py-2 border border-soft-gold text-soft-gold rounded-md font-body text-small font-medium hover:bg-soft-gold/5 transition-colors"
        >
          Save
        </button>
      </div>
    </article>
  )
}
