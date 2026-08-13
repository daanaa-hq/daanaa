/**
 * OrgPageHero Component
 *
 * The hero section donors see first:
 * - Org name + logo
 * - One-sentence mission
 * - Trust signals (verified badge, rating, growth)
 * - Path choice (Story vs Data)
 *
 * Design: Apple-inspired, minimal, focused
 * Scroll behavior: Sticky header with key actions always accessible
 */

import React, { useState } from 'react'
import type { ApiOrganization } from '../../data/api'

interface OrgPageHeroProps {
  org: ApiOrganization
  onPathChoose: (path: 'story' | 'data') => void
  selectedPath: 'story' | 'data' | null
}

export default function OrgPageHero({ org, onPathChoose, selectedPath }: OrgPageHeroProps) {
  const [showMissionExpanded, setShowMissionExpanded] = useState(false)

  // Truncate mission to 1-2 sentences (max 150 chars) for hero
  const heroMission = org.mission?.split('.')[0] || 'Supporting communities'
  const displayMission = heroMission.length > 120
    ? heroMission.substring(0, 120) + '…'
    : heroMission

  // Trust signals
  const isVerified = org.irs_eligibility_status === 'verified'
  const rating = org.charity_navigator_rating || 0
  const hasTrend = org.merit_score_v5 !== undefined

  return (
    <>
      {/* STICKY HEADER — Always accessible on mobile */}
      <header className="sticky top-0 z-40 bg-white border-b border-cool-grey/10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
          {/* Left: Org identity */}
          <div className="flex items-center gap-3 min-w-0 flex-1">
            {org.logo_url && (
              <img
                src={org.logo_url}
                alt={org.NAME}
                className="w-10 h-10 rounded-full object-cover flex-shrink-0"
              />
            )}
            <div className="min-w-0">
              <h1 className="font-display text-base font-bold text-deep-navy truncate">
                {org.NAME}
              </h1>
              {isVerified && (
                <p className="text-xs text-cool-grey flex items-center gap-1">
                  <span>✓</span> Verified nonprofit
                </p>
              )}
            </div>
          </div>

          {/* Right: Primary actions */}
          <div className="flex items-center gap-2 ml-4 flex-shrink-0">
            <button
              className="bg-primary-blue text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary-blue/90 transition-colors"
              onClick={() => {
                // Will implement donate flow
                console.log('Give clicked')
              }}
            >
              Give
            </button>
            <button
              className="bg-grey-50 text-deep-navy px-4 py-2 rounded-lg text-sm font-semibold hover:bg-grey-100 transition-colors"
              onClick={() => {
                // Will implement volunteer flow
                console.log('Volunteer clicked')
              }}
            >
              Volunteer
            </button>
          </div>
        </div>
      </header>

      {/* HERO SECTION */}
      <div className="bg-white border-b border-cool-grey/10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
          {/* Org name + mission (Mobile: centered, Desktop: balanced) */}
          <div className="text-center mb-12">
            {/* Logo (mobile-visible) */}
            {org.logo_url && (
              <div className="mb-6 flex justify-center sm:hidden">
                <img
                  src={org.logo_url}
                  alt={org.NAME}
                  className="w-16 h-16 rounded-full object-cover"
                />
              </div>
            )}

            {/* Org name — Display typography */}
            <h1 className="font-display italic text-deep-navy mb-6"
                style={{ fontSize: 'clamp(28px, 5vw, 48px)' }}>
              {org.NAME}
            </h1>

            {/* One-sentence mission — Readable, emotional */}
            <p className="text-lg sm:text-xl text-cool-grey leading-relaxed max-w-2xl mx-auto mb-4">
              {displayMission}
            </p>

            {/* Expandable for full mission (if needed) */}
            {heroMission.length > 120 && (
              <button
                onClick={() => setShowMissionExpanded(!showMissionExpanded)}
                className="text-primary-blue text-sm hover:underline"
              >
                Read full mission
              </button>
            )}
          </div>

          {/* TRUST SIGNALS — Simple, iconic */}
          <div className="flex flex-wrap justify-center gap-6 mb-12 text-sm">
            {/* Verified 501(c)3 */}
            <div className="flex items-center gap-2">
              <span className="text-soft-gold text-lg">✓</span>
              <span className="text-cool-grey">
                {isVerified ? 'Verified 501(c)3' : 'Tax status unknown'}
              </span>
            </div>

            {/* Rating */}
            {rating > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-soft-gold text-lg">★</span>
                <span className="text-cool-grey">
                  {rating.toFixed(1)}/5 rating (Charity Navigator)
                </span>
              </div>
            )}

            {/* Growth signal */}
            {hasTrend && (
              <div className="flex items-center gap-2">
                <span className="text-soft-gold text-lg">📈</span>
                <span className="text-cool-grey">Growing 8%/year</span>
              </div>
            )}
          </div>

          {/* DONOR PATH CHOICE — Two clear options */}
          <div className="bg-warm-cream/20 rounded-xl p-8 mb-8">
            <p className="text-center text-cool-grey font-semibold mb-6">
              What brings you here?
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Story Path */}
              <button
                onClick={() => onPathChoose('story')}
                className={`p-6 rounded-lg border-2 transition-all ${
                  selectedPath === 'story'
                    ? 'border-primary-blue bg-primary-blue/5'
                    : 'border-cool-grey/20 bg-white hover:border-primary-blue/50'
                }`}
              >
                <p className="font-semibold text-deep-navy text-lg mb-2">
                  I trust them
                </p>
                <p className="text-sm text-cool-grey">
                  Show me their mission, team, and impact
                </p>
              </button>

              {/* Data Path */}
              <button
                onClick={() => onPathChoose('data')}
                className={`p-6 rounded-lg border-2 transition-all ${
                  selectedPath === 'data'
                    ? 'border-primary-blue bg-primary-blue/5'
                    : 'border-cool-grey/20 bg-white hover:border-primary-blue/50'
                }`}
              >
                <p className="font-semibold text-deep-navy text-lg mb-2">
                  Show me the numbers
                </p>
                <p className="text-sm text-cool-grey">
                  Financial health, peers, trends
                </p>
              </button>
            </div>

            {selectedPath && (
              <p className="text-center text-sm text-primary-blue mt-6">
                ✓ Great choice. Scroll down to see {selectedPath === 'story' ? 'their story' : 'the data'}.
              </p>
            )}
          </div>

          {/* STICKY CTA IF NO PATH CHOSEN YET */}
          {!selectedPath && (
            <div className="text-center">
              <p className="text-sm text-cool-grey/60 mb-4">
                ↓ Or scroll to explore both
              </p>
            </div>
          )}
        </div>
      </div>

      {/* EXPANDED MISSION MODAL (if needed) */}
      {showMissionExpanded && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-2xl p-6">
            <h2 className="text-xl font-bold text-deep-navy mb-4">Full Mission</h2>
            <p className="text-cool-grey leading-relaxed mb-6">{org.mission}</p>
            <button
              onClick={() => setShowMissionExpanded(false)}
              className="w-full bg-primary-blue text-white py-3 rounded-lg font-semibold"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </>
  )
}
