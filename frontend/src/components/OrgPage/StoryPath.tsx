/**
 * StoryPath Component
 *
 * The emotional, narrative-first donor journey:
 * - Mission (human language)
 * - One key impact metric ($50 = X outcome)
 * - Clear giving CTA
 * - Why this org matters
 *
 * Design: Warm, readable, minimal
 * Goal: Activate emotional connection → drive giving
 */

import React from 'react'
import type { ApiOrganization } from '../../data/api'

interface StoryPathProps {
  org: ApiOrganization
}

export default function StoryPath({ org }: StoryPathProps) {
  const impactMetric = org.cost_per_outcome || 50 // Default $50
  const outcomeDescription = 'hour of 1-on-1 tutoring' // TODO: derive from data

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
      {/* MISSION — Emotional core */}
      <section className="mb-16">
        <h2 className="font-display italic text-deep-navy mb-6"
            style={{ fontSize: 'clamp(24px, 3vw, 32px)' }}>
          The Story
        </h2>

        <div className="prose prose-lg text-cool-grey max-w-2xl">
          <p className="text-lg sm:text-xl leading-relaxed">
            {org.mission || 'Supporting communities through direct service and long-term change.'}
          </p>
        </div>

        <div className="mt-8 p-6 rounded-lg bg-warm-cream/20">
          <p className="text-body text-cool-grey">
            <strong>What they're solving:</strong> Many students in under-resourced schools lack access to quality tutoring and mentorship. Teachers work in schools with limited professional development. This org bridges that gap with direct, measurable support.
          </p>
        </div>
      </section>

      {/* KEY IMPACT METRIC — Crystal clear */}
      <section className="mb-16 bg-primary-blue/5 border border-primary-blue/20 rounded-xl p-8 sm:p-12">
        <p className="text-label text-primary-blue uppercase tracking-wide mb-6">
          Your Impact
        </p>

        <div className="text-center">
          <div className="text-5xl sm:text-6xl font-bold text-deep-navy mb-2">
            ${impactMetric}
          </div>
          <p className="text-xl sm:text-2xl text-cool-grey leading-relaxed">
            equals<br />
            <strong className="text-deep-navy">1 {outcomeDescription}</strong>
          </p>
        </div>

        <div className="mt-8 space-y-4 text-body text-cool-grey">
          <div className="flex gap-3">
            <span className="text-soft-gold text-lg flex-shrink-0">✓</span>
            <span>Reaches 1 student directly</span>
          </div>
          <div className="flex gap-3">
            <span className="text-soft-gold text-lg flex-shrink-0">✓</span>
            <span>Measurable (reading improvement tracked)</span>
          </div>
          <div className="flex gap-3">
            <span className="text-soft-gold text-lg flex-shrink-0">✓</span>
            <span>Goes to mission, not overhead</span>
          </div>
        </div>
      </section>

      {/* SOCIAL PROOF (Light) */}
      <section className="mb-16 text-center">
        <p className="text-label text-cool-grey/60 uppercase tracking-wide mb-4">
          Joined by donors like you
        </p>
        <p className="text-3xl font-bold text-deep-navy mb-2">
          3,847 people
        </p>
        <p className="text-body text-cool-grey">
          have supported this org (including recurring donors)
        </p>

        {/* Optional: Show recent donor activity (aggregate only, no names default) */}
        <div className="mt-6 text-sm text-cool-grey space-y-1">
          <p>12 people gave this month</p>
          <p>24 expressed volunteer interest</p>
        </div>
      </section>

      {/* PRIMARY CTA — Clear, high-contrast */}
      <section className="mb-16 flex flex-col gap-4">
        <button
          className="w-full bg-primary-blue text-white py-4 px-6 rounded-lg font-semibold text-lg hover:bg-primary-blue/90 transition-colors active:bg-primary-blue/80"
          onClick={() => console.log('Give once clicked')}
        >
          Give Once
        </button>

        <button
          className="w-full bg-warm-cream text-deep-navy py-4 px-6 rounded-lg font-semibold text-lg hover:bg-warm-cream/80 transition-colors active:bg-warm-cream/70"
          onClick={() => console.log('Give monthly clicked')}
        >
          Give Monthly
          <span className="text-sm ml-2 opacity-75">(Recommended)</span>
        </button>

        <button
          className="w-full bg-transparent text-primary-blue py-3 px-6 rounded-lg font-semibold border border-primary-blue hover:bg-primary-blue/5 transition-colors"
          onClick={() => console.log('Other ways to help clicked')}
        >
          Other Ways to Help
        </button>
      </section>

      {/* WHY THIS ORG — Trust building */}
      <section className="mb-16 bg-white border border-cool-grey/10 rounded-lg p-6 sm:p-8">
        <h3 className="font-display italic text-deep-navy text-xl mb-6">
          Why Give Here
        </h3>

        <div className="space-y-4">
          <div>
            <p className="font-semibold text-deep-navy mb-1">
              ✓ Proven Impact
            </p>
            <p className="text-body text-cool-grey">
              Students in their programs improve reading proficiency 23% faster than peers (internal evaluation, 2024).
            </p>
          </div>

          <div>
            <p className="font-semibold text-deep-navy mb-1">
              ✓ Transparent & Verified
            </p>
            <p className="text-body text-cool-grey">
              Verified 501(c)3, ★★★★☆ rating, published annual reports, and open governance.
            </p>
          </div>

          <div>
            <p className="font-semibold text-deep-navy mb-1">
              ✓ Efficient
            </p>
            <p className="text-body text-cool-grey">
              67% of budget goes directly to programs. Administrative costs are 9% (below nonprofit average of 15%).
            </p>
          </div>

          <div>
            <p className="font-semibold text-deep-navy mb-1">
              ✓ Growing Steadily
            </p>
            <p className="text-body text-cool-grey">
              Revenue up 8% annually. Reaching more students each year while maintaining quality.
            </p>
          </div>
        </div>
      </section>

      {/* VOLUNTEER INTEREST */}
      <section className="mb-16 p-8 bg-primary-blue/5 border border-primary-blue/20 rounded-xl">
        <h3 className="font-semibold text-deep-navy text-lg mb-3">
          Want to help in other ways?
        </h3>
        <p className="text-body text-cool-grey mb-6">
          Beyond giving, this org is looking for volunteers: tutors, event planners, and board members.
        </p>
        <button
          className="w-full sm:w-auto px-6 py-3 bg-primary-blue text-white rounded-lg font-semibold hover:bg-primary-blue/90 transition-colors"
          onClick={() => console.log('Volunteer interest clicked')}
        >
          Express Interest
        </button>
      </section>

      {/* TAX INFO */}
      <section className="text-sm text-cool-grey/70 space-y-2">
        <p>
          <strong>Tax-deductible:</strong> Your gift is 100% tax-deductible (EIN: 04-1234567)
        </p>
        <p>
          <strong>Donor privacy:</strong> We don't track or share your giving activity. Your donation is between you and the nonprofit.
        </p>
        <p>
          <strong>Giving platforms:</strong> DAF · Direct ACH · Credit card · Corporate matching
        </p>
      </section>
    </div>
  )
}
