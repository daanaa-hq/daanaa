/**
 * ProvenanceLayers Component
 *
 * Separates org data into three transparent layers:
 * 1. Public Record (IRS, ProPublica, NCCS)
 * 2. Nonprofit-Supplied (claimed profile)
 * 3. Daanaa Inferred (peer context, health signals)
 *
 * Implements Batch 2 Phase 2: Clear sourcing for decision-grade org pages.
 * Stewardship P3: Trust signals are evidence-based and honestly stated.
 *
 * Color fix (2026-08-15): this component was authored with the dark-hero
 * palette (text-warm-cream/text-muted-cream — light text meant for the navy
 * hero background) but is mounted directly on the page's light warm-cream
 * body (OrganizationDetail.tsx renders it in a plain div, no dark wrapper).
 * Measured contrast before the fix: several values (e.g. the EIN,
 * "Public Record" heading) rendered as rgb(245,240,235) text on an
 * rgb(245,240,235) background — literal 1:1 contrast, invisible. Rewritten
 * to the light-background token set: text-deep-navy for headings/values,
 * text-slate for row labels, text-cool-grey for tertiary/meta text,
 * border-light-grey for dividers — matching DESIGN.md's documented roles
 * for those tokens. text-soft-gold (icons, links) is unchanged; it was
 * already correct on either background.
 */

import type { ApiOrganization } from '../data/api'

interface ProvenanceLayersProps {
  org: ApiOrganization
}

export default function ProvenanceLayers({ org }: ProvenanceLayersProps) {
  return (
    <div className="space-y-8">
      {/* Layer 1: Public Record — IRS + ProPublica + NCCS data */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 pb-3 border-b border-light-grey">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-soft-gold">
            <path d="M9 12l2 2 4-4M7 20H5a2 2 0 01-2-2V7a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2h-2" />
          </svg>
          <h3 className="font-display text-body text-deep-navy font-semibold">Public Record</h3>
          <span className="text-xs text-cool-grey ml-auto">IRS • ProPublica • NCCS</span>
        </div>
        
        <div className="grid gap-2 text-sm">
          {/* EIN + Tax Status */}
          <div className="flex justify-between">
            <span className="text-slate">Tax ID (EIN)</span>
            <span className="font-mono text-deep-navy">{org.EIN}</span>
          </div>

          {/* Latest Tax Year */}
          {org.latest_tax_year && (
            <div className="flex justify-between">
              <span className="text-slate">Latest Filing Year</span>
              <span className="text-deep-navy">{org.latest_tax_year}</span>
            </div>
          )}

          {/* Location */}
          {org.CITY && org.STATE && (
            <div className="flex justify-between">
              <span className="text-slate">Location</span>
              <span className="text-deep-navy">{org.CITY}, {org.STATE}</span>
            </div>
          )}

          {/* Total Revenue from 990 */}
          {org.total_revenue && (
            <div className="flex justify-between">
              <span className="text-slate">Annual Revenue (990 Filing)</span>
              <span className="text-deep-navy">${(org.total_revenue / 1_000_000).toFixed(2)}M</span>
            </div>
          )}

          {/* NTEE Category */}
          {org.NTEE1 && (
            <div className="flex justify-between">
              <span className="text-slate">Category (NTEE)</span>
              <span className="text-deep-navy">{org.NTEE1}</span>
            </div>
          )}
        </div>

        <p className="text-xs text-cool-grey mt-3">
          Data from IRS Form 990 filings (typically 12–18 months old) and verified via ProPublica Nonprofit Explorer.
        </p>
      </div>

      {/* Layer 2: Nonprofit-Supplied — Claimed profile, if any */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 pb-3 border-b border-light-grey">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-soft-gold">
            <path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          <h3 className="font-display text-body text-deep-navy font-semibold">Nonprofit-Supplied</h3>
          <span className="text-xs text-cool-grey ml-auto">From their profile</span>
        </div>

        <div className="grid gap-2 text-sm">
          {/* Website */}
          {org.website ? (
            <div className="flex justify-between">
              <span className="text-slate">Website</span>
              <a href={org.website} target="_blank" rel="noopener noreferrer" className="text-soft-gold hover:underline">
                {org.website.replace(/^https?:\/\/(www\.)?/, '')}
              </a>
            </div>
          ) : (
            <div className="flex justify-between text-cool-grey">
              <span>Website</span>
              <span>Not listed</span>
            </div>
          )}

          {/* Mission (if nonprofit-supplied) */}
          {org.mission && org.mission_source !== 'ai_generated' && (
            <div className="space-y-1">
              <span className="text-slate block">Mission Statement</span>
              <p className="text-deep-navy text-xs leading-relaxed italic">"{org.mission}"</p>
            </div>
          )}
        </div>

        <p className="text-xs text-cool-grey mt-3">
          Information the nonprofit provides on their website and verified listings.
        </p>
      </div>

      {/* Layer 3: Daanaa Inferred — Peer context, health signals */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 pb-3 border-b border-light-grey">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-soft-gold">
            <path d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <h3 className="font-display text-body text-deep-navy font-semibold">Daanaa Inferred</h3>
          <span className="text-xs text-cool-grey ml-auto">Our analysis</span>
        </div>

        <div className="grid gap-2 text-sm">
          {/* Peer Percentile */}
          {org.ntee1_percentile !== undefined && org.ntee1_percentile !== null && (
            <div className="flex justify-between">
              <span className="text-slate">Peer Percentile</span>
              <span className="text-deep-navy">{Math.round(org.ntee1_percentile)}th (within category)</span>
            </div>
          )}

          {/* Scoring Tier */}
          {org.scoring_tier && (
            <div className="flex justify-between">
              <span className="text-slate">Financial Context Tier</span>
              <span className="text-deep-navy">{org.scoring_tier.replace(/_/g, ' ')}</span>
            </div>
          )}

          {/* Peer Group Size */}
          {org.peer_group_size_v6 && (
            <div className="flex justify-between">
              <span className="text-slate">Peer Group Size</span>
              <span className="text-deep-navy">{org.peer_group_size_v6} similar orgs</span>
            </div>
          )}
        </div>

        <p className="text-xs text-cool-grey mt-3">
          Financial context derived from comparing this org to peer organizations with similar size, category, and funding model. See our <a href="/methodology" className="text-soft-gold hover:underline">methodology</a> for details.
        </p>
      </div>

      {/* Transparency Footer */}
      <div className="pt-4 border-t border-light-grey">
        <p className="text-xs text-cool-grey leading-relaxed">
          <strong>Why these layers?</strong> We believe donors should know the source of every claim. Some data comes directly from the IRS (certain), some from the nonprofit's own website (claimed), and some from our analysis (inferred). All three matter for making informed decisions.
        </p>
      </div>
    </div>
  )
}
