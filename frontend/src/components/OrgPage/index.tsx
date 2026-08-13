/**
 * OrgPage Wrapper Component
 *
 * Orchestrates the complete org detail page:
 * 1. Hero + Path Choice (always shown)
 * 2. Story Path OR Data Path (based on user choice)
 * 3. Claimed Items (both paths see this)
 * 4. Detailed Financials (expandable)
 * 5. Team & Leadership
 * 6. Report Mistake
 *
 * Two-sided design:
 * - Donor-facing: Clear decision flow (90 seconds)
 * - Nonprofit-facing: Same page with edit overlays + analytics
 */

import React, { useState } from 'react'
import type { ApiOrganization } from '../../data/api'
import OrgPageHero from './OrgPageHero'
import StoryPath from './StoryPath'
import DataPath from './DataPath'

interface OrgPageProps {
  org: ApiOrganization
  isNonprofitDashboard?: boolean // When true, show edit overlays + analytics
}

export default function OrgPage({ org, isNonprofitDashboard = false }: OrgPageProps) {
  const [selectedPath, setSelectedPath] = useState<'story' | 'data' | null>(null)
  const [showExpandedFinancials, setShowExpandedFinancials] = useState(false)

  return (
    <div className="bg-white min-h-screen">
      {/* HERO SECTION — Path Choice */}
      <OrgPageHero
        org={org}
        onPathChoose={setSelectedPath}
        selectedPath={selectedPath}
      />

      {/* DONOR EXPERIENCE — Story or Data Path */}
      {selectedPath === 'story' && <StoryPath org={org} />}
      {selectedPath === 'data' && <DataPath org={org} />}

      {/* If no path chosen, show summary of both */}
      {!selectedPath && (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center text-cool-grey">
          <p>Choose a path above to explore ↑</p>
        </div>
      )}

      {/* CLAIMED ITEMS SECTION — Both paths see this */}
      <section className="bg-white border-t border-cool-grey/10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <h2 className="font-display italic text-deep-navy mb-4"
              style={{ fontSize: 'clamp(24px, 3vw, 32px)' }}>
            What This Org Brings to the Table
          </h2>
          <p className="text-body text-cool-grey mb-12">
            Transparency matters. Here's what this nonprofit has verified on their page:
          </p>

          {/* Claimed items categories */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Governance & Transparency */}
            <div>
              <h3 className="font-semibold text-deep-navy mb-4">
                ✓ Governance & Transparency
              </h3>
              <ul className="space-y-2 text-sm text-cool-grey">
                <li>✓ Board Member List (Verified 2024)</li>
                <li>✓ COI Policy (Verified 2024)</li>
                <li>✓ Annual Report 2023 (Verified)</li>
                <li>ⓘ DEI Commitment (Claimed 2024)</li>
              </ul>
              <button className="text-primary-blue text-sm mt-3 hover:underline">
                View All →
              </button>
            </div>

            {/* Programs & Impact */}
            <div>
              <h3 className="font-semibold text-deep-navy mb-4">
                ✓ Programs & Impact
              </h3>
              <ul className="space-y-2 text-sm text-cool-grey">
                <li>✓ K–12 Tutoring Program (Verified 2024)</li>
                <li>✓ Teacher Professional Development (Verified 2024)</li>
                <li>✓ Community Partnerships (Verified 2024)</li>
                <li>ⓘ Summer Camp Pilot (Claimed 2024)</li>
              </ul>
              <button className="text-primary-blue text-sm mt-3 hover:underline">
                View All →
              </button>
            </div>

            {/* Volunteer Opportunities */}
            <div>
              <h3 className="font-semibold text-deep-navy mb-4">
                ✓ Volunteer Opportunities
              </h3>
              <ul className="space-y-2 text-sm text-cool-grey">
                <li>✓ Tutor (1-on-1 support)</li>
                <li>✓ Event Planning (Fundraisers)</li>
                <li>✓ Board Committee (Governance)</li>
              </ul>
              <button className="text-primary-blue text-sm mt-3 hover:underline">
                [Interested in Any?] →
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* TEAM & LEADERSHIP */}
      <section className="bg-warm-cream/10 border-t border-cool-grey/10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <h2 className="font-display italic text-deep-navy mb-12"
              style={{ fontSize: 'clamp(24px, 3vw, 32px)' }}>
            Team & Leadership
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
            {/* Executive Director */}
            <div className="text-center sm:text-left">
              <p className="font-semibold text-deep-navy text-lg">
                Jane Smith
              </p>
              <p className="text-label text-primary-blue uppercase tracking-wide mb-3">
                Executive Director
              </p>
              <p className="text-body text-cool-grey mb-4">
                20 years nonprofit experience. Led three organizations to scale.
                Mission-driven educator.
              </p>
              <p className="text-sm text-cool-grey/60">
                Joined 2016 · Works directly with programs & strategy
              </p>
            </div>

            {/* CFO */}
            <div className="text-center sm:text-left">
              <p className="font-semibold text-deep-navy text-lg">
                Robert Chen
              </p>
              <p className="text-label text-primary-blue uppercase tracking-wide mb-3">
                Chief Financial Officer
              </p>
              <p className="text-body text-cool-grey mb-4">
                Former teacher turned nonprofit finance expert. Ensures every dollar
                reaches the mission.
              </p>
              <p className="text-sm text-cool-grey/60">
                Joined 2018 · Oversees budget, grants, compliance
              </p>
            </div>
          </div>

          <button className="mt-8 text-primary-blue font-semibold hover:underline">
            See all board members & staff →
          </button>
        </div>
      </section>

      {/* EXPANDED FINANCIALS (Optional) */}
      {showExpandedFinancials && (
        <section className="bg-white border-t border-cool-grey/10">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
            <h2 className="font-display italic text-deep-navy mb-12"
                style={{ fontSize: 'clamp(24px, 3vw, 32px)' }}>
              Detailed Financial Information
            </h2>
            {/* Component placeholder for ExpenseBreakdown, FinancialTrends, etc. */}
            <p className="text-cool-grey">
              [ExpenseBreakdown component] [FinancialTrends component] [Peer Comparison]
            </p>
          </div>
        </section>
      )}

      {/* REPORT MISTAKE */}
      <section className="bg-warm-cream/5 border-t border-cool-grey/10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
          <p className="text-body text-cool-grey mb-3">
            Did we get something wrong?
          </p>
          <button className="text-primary-blue font-semibold hover:underline">
            Report a Mistake →
          </button>
        </div>
      </section>

      {/* FOOTER NOTE */}
      <footer className="bg-white border-t border-cool-grey/10 py-8 text-center text-xs text-cool-grey/60">
        <p>
          Data from IRS Form 990 (2024) · Last updated Aug 13, 2026 ·
          {' '}
          <a href="/methodology" className="text-primary-blue hover:underline">
            How We Calculate This
          </a>
        </p>
      </footer>
    </div>
  )
}
