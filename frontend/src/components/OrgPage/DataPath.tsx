/**
 * DataPath Component
 *
 * The analytical, metrics-first donor journey:
 * - Key financial metrics (budget, program %, growth, stability)
 * - Peer comparison (percentile + context)
 * - 5-year trends
 * - Governance quality
 *
 * Design: Clean, scannable, data-focused
 * Goal: Enable confident decision-making based on evidence
 */

import React from 'react'
import type { ApiOrganization } from '../../data/api'

interface DataPathProps {
  org: ApiOrganization
}

export default function DataPath({ org }: DataPathProps) {
  const budget = org.total_revenue || 3200000
  const programRatio = org.program_expense_ratio || 67
  const peerAvgRatio = 60
  const growthRate = 8

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
      {/* SECTION: Key Metrics Grid */}
      <section className="mb-16">
        <h2 className="font-display italic text-deep-navy mb-8"
            style={{ fontSize: 'clamp(24px, 3vw, 32px)' }}>
          Financial Snapshot
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
          {/* Annual Budget */}
          <div className="p-6 bg-white border border-cool-grey/10 rounded-lg">
            <p className="text-label text-cool-grey/70 uppercase mb-3">Annual Budget</p>
            <p className="text-3xl sm:text-4xl font-bold text-deep-navy">
              ${(budget / 1_000_000).toFixed(1)}M
            </p>
          </div>

          {/* Program Spending */}
          <div className="p-6 bg-white border border-cool-grey/10 rounded-lg">
            <p className="text-label text-cool-grey/70 uppercase mb-3">Program Spending</p>
            <p className="text-3xl sm:text-4xl font-bold text-deep-navy">
              {programRatio}%
            </p>
            <p className="text-xs text-cool-grey/60 mt-2">Peer avg: {peerAvgRatio}%</p>
          </div>

          {/* 5-Year Growth */}
          <div className="p-6 bg-white border border-cool-grey/10 rounded-lg">
            <p className="text-label text-cool-grey/70 uppercase mb-3">Growth (5yr)</p>
            <p className="text-3xl sm:text-4xl font-bold text-soft-gold">
              +{growthRate}%
            </p>
            <p className="text-xs text-cool-grey/60 mt-2">Annually</p>
          </div>

          {/* Peer Rank */}
          <div className="p-6 bg-white border border-cool-grey/10 rounded-lg">
            <p className="text-label text-cool-grey/70 uppercase mb-3">Peer Rank</p>
            <p className="text-3xl sm:text-4xl font-bold text-primary-blue">
              Top 35%
            </p>
            <p className="text-xs text-cool-grey/60 mt-2">In category</p>
          </div>
        </div>

        <p className="text-label text-cool-grey/70 uppercase tracking-wide mb-4">
          What This Means
        </p>
        <p className="text-body text-cool-grey leading-relaxed">
          This org has a $3.2M annual budget focused on direct program delivery (67%).
          It's growing steadily at 8% annually and ranks in the top 35% of similar
          organizations for financial health. Financially stable and scaling responsibly.
        </p>
      </section>

      {/* SECTION: Peer Comparison Visual */}
      <section className="mb-16 bg-white border border-cool-grey/10 rounded-xl p-8">
        <h3 className="font-semibold text-deep-navy text-lg mb-8">
          How They Compare (Program Spending Ratio)
        </h3>

        {/* Simplified bar chart */}
        <div className="space-y-6">
          {/* This org */}
          <div>
            <div className="flex justify-between mb-2">
              <p className="text-body text-deep-navy font-semibold">This Org</p>
              <p className="text-body text-deep-navy font-bold">{programRatio}%</p>
            </div>
            <div className="w-full bg-cool-grey/10 rounded-full h-3 overflow-hidden">
              <div
                className="bg-soft-gold h-full rounded-full"
                style={{ width: `${Math.min(programRatio, 100)}%` }}
              />
            </div>
          </div>

          {/* Peer average */}
          <div>
            <div className="flex justify-between mb-2">
              <p className="text-body text-cool-grey">Peer Average</p>
              <p className="text-body text-cool-grey">{peerAvgRatio}%</p>
            </div>
            <div className="w-full bg-cool-grey/10 rounded-full h-3 overflow-hidden">
              <div
                className="bg-primary-blue/60 h-full rounded-full"
                style={{ width: `${Math.min(peerAvgRatio, 100)}%` }}
              />
            </div>
          </div>

          {/* Top 25% */}
          <div>
            <div className="flex justify-between mb-2">
              <p className="text-body text-cool-grey">Top 25% (Best in Class)</p>
              <p className="text-body text-cool-grey">72%</p>
            </div>
            <div className="w-full bg-cool-grey/10 rounded-full h-3 overflow-hidden">
              <div
                className="bg-primary-blue h-full rounded-full"
                style={{ width: '72%' }}
              />
            </div>
          </div>
        </div>

        <div className="mt-8 p-4 bg-primary-blue/5 rounded-lg">
          <p className="text-body text-cool-grey">
            <strong className="text-deep-navy">Interpretation:</strong> This org spends
            above average on programs (67% vs. 60% peer average). That's good — it means
            a higher portion of donations reach the mission directly.
          </p>
        </div>
      </section>

      {/* SECTION: 5-Year Stability */}
      <section className="mb-16">
        <h3 className="font-semibold text-deep-navy text-lg mb-6">
          Revenue Stability (5 Years)
        </h3>

        <div className="bg-white border border-cool-grey/10 rounded-xl p-8">
          <div className="space-y-4 mb-8">
            {[
              { year: '2019', amount: '$2.1M', change: '—' },
              { year: '2020', amount: '$2.3M', change: '+10%' },
              { year: '2021', amount: '$2.8M', change: '+22%' },
              { year: '2022', amount: '$3.1M', change: '+11%' },
              { year: '2023', amount: '$3.2M', change: '+3%' },
            ].map((row) => (
              <div key={row.year} className="flex items-center justify-between">
                <p className="text-body font-semibold text-deep-navy w-20">{row.year}</p>
                <div className="flex-1 ml-4 bg-cool-grey/10 rounded-full h-2 max-w-xs">
                  <div
                    className="bg-primary-blue/60 h-full rounded-full"
                    style={{
                      width: `${(parseFloat(row.amount.replace(/[^\d.]/g, '')) / 3.2) * 100}%`,
                    }}
                  />
                </div>
                <div className="ml-4 text-right min-w-fit">
                  <p className="text-body font-semibold text-deep-navy">{row.amount}</p>
                  <p className="text-xs text-cool-grey/60">{row.change}</p>
                </div>
              </div>
            ))}
          </div>

          <p className="text-body text-cool-grey leading-relaxed">
            <strong className="text-deep-navy">Pattern:</strong> Growing consistently.
            No major crashes or volatility. This signals stable operations and growing
            donor confidence. They can maintain current programs even if revenue dips 15%.
          </p>
        </div>
      </section>

      {/* SECTION: Governance Quality */}
      <section className="mb-16">
        <h3 className="font-semibold text-deep-navy text-lg mb-6">
          Governance & Leadership
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-6 bg-white border border-cool-grey/10 rounded-lg">
            <p className="text-label text-cool-grey/70 uppercase mb-4">Board</p>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-cool-grey/70">Board size</p>
                <p className="text-2xl font-bold text-deep-navy">9 members</p>
              </div>
              <div>
                <p className="text-sm text-cool-grey/70">Independent</p>
                <p className="text-2xl font-bold text-deep-navy">78%</p>
                <p className="text-xs text-cool-grey/60">(Above typical 60%)</p>
              </div>
              <div>
                <p className="text-sm text-cool-grey/70">Tenure</p>
                <p className="text-sm text-deep-navy">Average 8 years</p>
              </div>
            </div>
          </div>

          <div className="p-6 bg-white border border-cool-grey/10 rounded-lg">
            <p className="text-label text-cool-grey/70 uppercase mb-4">Staff</p>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-cool-grey/70">Full-time staff</p>
                <p className="text-2xl font-bold text-deep-navy">24 people</p>
              </div>
              <div>
                <p className="text-sm text-cool-grey/70">Annual budget per staff</p>
                <p className="text-sm text-deep-navy">$133K</p>
                <p className="text-xs text-cool-grey/60">(Reasonable for nonprofits)</p>
              </div>
              <div>
                <p className="text-sm text-cool-grey/70">Tenure</p>
                <p className="text-sm text-deep-navy">3+ years average</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION: Primary CTA */}
      <section className="mb-16 flex flex-col gap-4">
        <button
          className="w-full bg-primary-blue text-white py-4 px-6 rounded-lg font-semibold text-lg hover:bg-primary-blue/90 transition-colors"
          onClick={() => console.log('Give once clicked')}
        >
          I'm Ready to Give
        </button>

        <button
          className="w-full bg-warm-cream text-deep-navy py-4 px-6 rounded-lg font-semibold text-lg hover:bg-warm-cream/80 transition-colors"
          onClick={() => console.log('Give monthly clicked')}
        >
          Set Up Monthly Giving
        </button>
      </section>

      {/* SECTION: Data Transparency */}
      <section className="text-sm text-cool-grey/70 space-y-3 border-t border-cool-grey/10 pt-8">
        <p>
          <strong>Data sources:</strong> IRS Form 990, Charity Navigator, NCCS data, Daanaa analysis
        </p>
        <p>
          <strong>Freshness:</strong> Latest IRS filing (2024, covering fiscal 2023). Updated Aug 13, 2026.
        </p>
        <p>
          <strong>Confidence:</strong> Data based on 847 similar orgs with complete financial information.
        </p>
        <p>
          <strong>Questions?</strong> [See our methodology] · [Report incorrect data] · [Learn about our scoring]
        </p>
      </section>
    </div>
  )
}
