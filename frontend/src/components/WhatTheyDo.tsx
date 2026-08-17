import { ApiOrganization } from '../data/api'

/**
 * WhatTheyDo: Mission + Programs Section
 *
 * Shows the org's mission narrative (from IRS filing or AI-generated)
 * and their key program areas in a scannable list format.
 * Stewardship P3 (evidence-based), P9 (explainability).
 */
export default function WhatTheyDo({ org }: { org: ApiOrganization }) {
  const hasMission = !!org.mission
  const hasPrograms = org.programs?.program_descriptions && org.programs.program_descriptions.length > 0
  const hasIrsPrograms = org.irs_program_narrative && org.irs_program_narrative.length > 0

  if (!hasMission && !hasPrograms && !hasIrsPrograms) {
    return null
  }

  return (
    <section className="mb-16 py-12 md:py-16 border-b border-cool-grey/20">
      <h2 className="font-display italic text-deep-navy text-title-sm mb-6">What do they do?</h2>

      {/* Mission narrative */}
      {hasMission && (
        <div className="mb-8">
          <p className="font-body text-base leading-relaxed text-deep-navy mb-2">
            {org.mission}
          </p>
          {org.mission_source && (
            <p className="font-body text-caption text-cool-grey">
              {org.mission_source === 'ai_ntee' && 'AI-generated from nonprofit classification'}
              {org.mission_source === 'ai_haiku' && 'AI-synthesized from public data'}
              {org.mission_source === 'ai_web' && 'AI-extracted from their website'}
              {org.mission_source === 'lucido' && 'From nonprofit directory'}
              {org.mission_source === 'claimed' && "Organization's own description"}
              {org.latest_tax_year && ` · FY ${org.latest_tax_year}`}
            </p>
          )}
        </div>
      )}

      {/* Program descriptions from enrichment */}
      {hasPrograms && org.programs && org.programs.program_descriptions && (
        <div className="mb-8">
          <h3 className="font-body text-small font-semibold text-deep-navy mb-4">Program areas</h3>
          <ul className="space-y-3">
            {org.programs.program_descriptions.map((desc, i) => (
              <li key={i} className="flex gap-3">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-soft-gold/30 flex items-center justify-center mt-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-deep-gold"></span>
                </span>
                <span className="font-body text-base text-deep-navy">{desc}</span>
              </li>
            ))}
          </ul>
          {org.programs.programs_verified_date && (
            <p className="font-body text-caption text-cool-grey mt-4">
              Last verified {new Date(org.programs.programs_verified_date).toLocaleDateString('en-US', {
                month: 'short',
                year: 'numeric'
              })}
            </p>
          )}
        </div>
      )}

      {/* IRS program narrative (from actual 990 filing) */}
      {hasIrsPrograms && org.irs_program_narrative![0]?.text && (
        <div>
          <h3 className="font-body text-small font-semibold text-deep-navy mb-3">In their own words</h3>
          <p className="font-body text-base text-deep-navy leading-relaxed mb-2">
            {org.irs_program_narrative![0].text}
          </p>
          {org.irs_program_narrative![0].year && (
            <p className="font-body text-caption text-cool-grey">
              From IRS Form 990, {org.irs_program_narrative![0].year} filing
            </p>
          )}
        </div>
      )}
    </section>
  )
}
