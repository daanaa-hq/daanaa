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
        <div className="flex items-center gap-2 pb-3 border-b border-warm-cream/20">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-soft-gold">
            <path d="M9 12l2 2 4-4M7 20H5a2 2 0 01-2-2V7a2 2 0 012-2h14a2 2 0 012 2v10a2 2 0 01-2 2h-2" />
          </svg>
          <h3 className="font-display text-body text-warm-cream font-semibold">Public Record</h3>
          <span className="text-xs text-muted-cream/60 ml-auto">IRS • ProPublica • NCCS</span>
        </div>
        
        <div className="grid gap-2 text-sm">
          {/* EIN + Tax Status */}
          <div className="flex justify-between">
            <span className="text-muted-cream/70">Tax ID (EIN)</span>
            <span className="font-mono text-warm-cream">{org.EIN}</span>
          </div>

          {/* Latest Tax Year */}
          {org.latest_tax_year && (
            <div className="flex justify-between">
              <span className="text-muted-cream/70">Latest Filing Year</span>
              <span className="text-warm-cream">{org.latest_tax_year}</span>
            </div>
          )}

          {/* Location */}
          {org.CITY && org.STATE && (
            <div className="flex justify-between">
              <span className="text-muted-cream/70">Location</span>
              <span className="text-warm-cream">{org.CITY}, {org.STATE}</span>
            </div>
          )}

          {/* Total Revenue from 990 */}
          {org.total_revenue && (
            <div className="flex justify-between">
              <span className="text-muted-cream/70">Annual Revenue (990 Filing)</span>
              <span className="text-warm-cream">${(org.total_revenue / 1_000_000).toFixed(2)}M</span>
            </div>
          )}

          {/* NTEE Category */}
          {org.NTEE1 && (
            <div className="flex justify-between">
              <span className="text-muted-cream/70">Category (NTEE)</span>
              <span className="text-warm-cream">{org.NTEE1}</span>
            </div>
          )}
        </div>

        <p className="text-xs text-muted-cream/50 mt-3">
          Data from IRS Form 990 filings (typically 12–18 months old) and verified via ProPublica Nonprofit Explorer.
        </p>
      </div>

      {/* Layer 2: Nonprofit-Supplied — Claimed profile, if any */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 pb-3 border-b border-warm-cream/20">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-soft-gold">
            <path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          <h3 className="font-display text-body text-warm-cream font-semibold">Nonprofit-Supplied</h3>
          <span className="text-xs text-muted-cream/60 ml-auto">From their profile</span>
        </div>

        <div className="grid gap-2 text-sm">
          {/* Website */}
          {org.website ? (
            <div className="flex justify-between">
              <span className="text-muted-cream/70">Website</span>
              <a href={org.website} target="_blank" rel="noopener noreferrer" className="text-soft-gold hover:underline">
                {org.website.replace(/^https?:\/\/(www\.)?/, '')}
              </a>
            </div>
          ) : (
            <div className="flex justify-between text-muted-cream/50">
              <span>Website</span>
              <span>Not listed</span>
            </div>
          )}

          {/* Mission (if nonprofit-supplied) */}
          {org.mission && org.mission_source !== 'ai_generated' && (
            <div className="space-y-1">
              <span className="text-muted-cream/70 block">Mission Statement</span>
              <p className="text-warm-cream text-xs leading-relaxed italic">"{org.mission}"</p>
            </div>
          )}
        </div>

        <p className="text-xs text-muted-cream/50 mt-3">
          Information the nonprofit provides on their website and verified listings.
        </p>
      </div>

      {/* Layer 3: Daanaa Inferred — Peer context, health signals */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 pb-3 border-b border-warm-cream/20">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-soft-gold">
            <path d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <h3 className="font-display text-body text-warm-cream font-semibold">Daanaa Inferred</h3>
          <span className="text-xs text-muted-cream/60 ml-auto">Our analysis</span>
        </div>

        <div className="grid gap-2 text-sm">
          {/* Peer Percentile */}
          {org.ntee1_percentile !== undefined && org.ntee1_percentile !== null && (
            <div className="flex justify-between">
              <span className="text-muted-cream/70">Peer Percentile</span>
              <span className="text-warm-cream">{Math.round(org.ntee1_percentile)}th (within category)</span>
            </div>
          )}

          {/* Scoring Tier */}
          {org.scoring_tier && (
            <div className="flex justify-between">
              <span className="text-muted-cream/70">Financial Context Tier</span>
              <span className="text-warm-cream">{org.scoring_tier.replace(/_/g, ' ')}</span>
            </div>
          )}

          {/* Peer Group Size */}
          {org.peer_group_size_v6 && (
            <div className="flex justify-between">
              <span className="text-muted-cream/70">Peer Group Size</span>
              <span className="text-warm-cream">{org.peer_group_size_v6} similar orgs</span>
            </div>
          )}
        </div>

        <p className="text-xs text-muted-cream/50 mt-3">
          Financial context derived from comparing this org to peer organizations with similar size, category, and funding model. See our <a href="/methodology" className="text-soft-gold hover:underline">methodology</a> for details.
        </p>
      </div>

      {/* Transparency Footer */}
      <div className="pt-4 border-t border-warm-cream/10">
        <p className="text-xs text-muted-cream/60 leading-relaxed">
          <strong>Why these layers?</strong> We believe donors should know the source of every claim. Some data comes directly from the IRS (certain), some from the nonprofit's own website (claimed), and some from our analysis (inferred). All three matter for making informed decisions.
        </p>
      </div>
    </div>
  )
}
