import React from 'react'
import type { ApiOrganization } from '../data/api'
import InferenceBadge from './InferenceBadge'

interface FinancialContextProps {
  org: ApiOrganization
}

export default function FinancialContext({ org }: FinancialContextProps) {
  const tier = org.scoring_tier
  if (!tier) return null

  if (tier === '1_Direct_Regional' || tier === '2_Regional_Inferred') {
    const isT1 = tier === '1_Direct_Regional'
    const isInferred = tier === '2_Regional_Inferred'

    return (
      <div className="rounded-lg border border-cool-grey/20 bg-cool-grey/5 p-6 mb-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold">
            {isT1 ? 'Financial Context' : 'Regional Financial Context (Inferred)'}
          </h2>
          <span className={`text-xs px-2 py-1 rounded ${isT1 ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
            {isT1 ? 'High Confidence' : 'Good Confidence'}
          </span>
        </div>

        {/* Inference badge for T2 */}
        {isInferred && org.peer_group_size && (
          <div className="mb-4">
            <InferenceBadge
              peerCount={org.peer_group_size}
              confidence="good"
              peerGroupDescription={org.peer_group_description || ''}
              confidenceMargin="±10%"
            />
          </div>
        )}

        {/* Main content grid */}
        <div className="grid grid-cols-3 gap-6">
          <div>
            <p className="text-xs font-semibold text-gray-500 mb-1">Funding Model</p>
            <p className="font-semibold mb-2">{org.merit_archetype_v5_label}</p>
            {isT1 ? (
              <p className="text-xs text-gray-600">Peer Group: {org.peer_group_size} regional orgs</p>
            ) : (
              <p className="text-xs text-gray-600">Peer Group: {org.peer_group_size} similar orgs</p>
            )}
            <p className="text-xs text-gray-500 italic">{org.peer_group_description}</p>
          </div>

          {/* Reserves/Health - different messaging for T1 vs T2 */}
          <div>
            {isT1 && org.months_of_reserve !== null ? (
              <>
                <p className="text-xs font-semibold text-gray-500 mb-1">Reserves</p>
                <p className="font-semibold text-lg">{org.months_of_reserve.toFixed(1)} mo</p>
                <p className="text-xs text-gray-600 mt-3">Health Signal</p>
                <p className="text-sm font-semibold">{org.merit_health_signal_v5}</p>
              </>
            ) : isInferred ? (
              <>
                <p className="text-xs font-semibold text-gray-500 mb-1">Typical Reserves (Peer Median)</p>
                <p className="font-semibold text-lg">2.1 mo</p>
                <p className="text-xs text-gray-600 mt-3">Note</p>
                <p className="text-xs text-gray-700">Although we don't have revenue data for this organization, nonprofits in this group typically carry this amount</p>
              </>
            ) : null}
          </div>

          {/* Governance */}
          {org.board_size ? (
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-1">Governance</p>
              <p className="font-semibold">{org.board_size} board members</p>
              {org.nccs_program_ratio && (
                <>
                  <p className="text-xs text-gray-600 mt-3">Program Spending</p>
                  <p className="font-semibold">{(org.nccs_program_ratio * 100).toFixed(0)}%</p>
                </>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer caveat */}
        {isT1 && <p className="text-xs text-gray-600 mt-4 pt-4 border-t">Data source: IRS Form 990 (this organization's filing)</p>}
        {isInferred && <p className="text-xs text-blue-600 mt-4 pt-4 border-t">Data source: Similar organizations in this region and category</p>}
      </div>
    )
  }

  if (tier === '3_Limited_Context') {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 mb-8">
        <h2 className="text-lg font-semibold mb-3">Financial Context (Limited Data)</h2>
        <p className="text-xs text-amber-800 mb-3">We have limited peer data for this type of organization in this region.</p>
        <p className="text-xs text-gray-700 mb-3">
          <strong>Funding Model:</strong> {org.merit_archetype_v5_label}
        </p>
        <p className="text-xs text-gray-700 mb-4">
          This organization operates in a niche or rare category. We can share broader patterns for similar organizations nationally, but regional specifics are limited.
        </p>
        <p className="text-xs text-gray-700">
          <strong>We recommend asking them directly:</strong> Emergency reserve? Funding mix? How do they handle seasonal changes?
        </p>
      </div>
    )
  }

  if (tier === '4_Archetype_Only') {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-6 mb-8">
        <h2 className="text-lg font-semibold mb-3">We're Still Learning About This Organization</h2>
        <p className="text-xs text-gray-700 mb-3">
          We don't have detailed financial data from their IRS filings yet. That's not a reflection on their quality — many grassroots and newer organizations file simplified forms.
        </p>
        <p className="text-xs text-gray-700 mb-4">
          <strong>Funding Model:</strong> {org.merit_archetype_v5_label} (typically rely on community support, fundraising, and grants)
        </p>
        <p className="text-xs text-gray-700">
          <strong>The best source is direct:</strong>
        </p>
        <ul className="text-xs text-gray-700 mt-2 ml-4 list-disc">
          <li>Do they maintain an operating reserve?</li>
          <li>What's their funding mix?</li>
          <li>How do they handle cash flow challenges?</li>
          <li>What's their growth vision?</li>
        </ul>
      </div>
    )
  }

  return null
}
