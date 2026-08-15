import React from 'react'
import type { ApiOrganization } from '../data/api'

interface FinancialContextProps {
  org: ApiOrganization
}

// Real values from registry_enriched.scoring_tier, written by
// scripts/merit_scorer_v6_0.py. This must stay in sync with that scorer's
// vocabulary, not any other tier naming used elsewhere in the codebase.
//
// Uses org.tier_label for the peer group description, not
// org.peer_group_size/peer_group_description. The droplet's v6_context table
// only ships scoring_tier/tier_label/confidence -- its peer_group_size_v6/
// peer_group_description_v6 columns are a separate, unrelated pipeline
// (verified disagreeing with the real numbers: 95 vs 22 peers for the same
// EIN). No verified-correct peer count is available yet. tier_label is
// confirmed correct and descriptive ("Donation-Funded Programs, Established,
// national"), so it carries the peer-group description here instead of a
// numeric count until a corrected table ships. See TODOS.md.
export default function FinancialContext({ org }: FinancialContextProps) {
  const tier = org.scoring_tier
  if (!tier) return null

  if (tier === '1_Full_Context' || tier === '2_Regional_Context') {
    const isT1 = tier === '1_Full_Context'

    return (
      <div className="rounded-lg border border-cool-grey/20 bg-cool-grey/5 p-6 mb-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold">
            {isT1 ? 'Financial Context' : 'Financial Context (Broader Comparison)'}
          </h2>
          <span className={`text-xs px-2 py-1 rounded ${isT1 ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
            {isT1 ? 'High confidence' : 'Good confidence'}
          </span>
        </div>

        {/* Main content grid */}
        <div className="grid grid-cols-3 gap-6">
          <div>
            <p className="text-xs font-semibold text-gray-500 mb-1">Funding Model</p>
            <p className="font-semibold mb-2">{org.merit_archetype_v5_label}</p>
            <p className="text-xs text-gray-500 italic">{org.tier_label}</p>
          </div>

          {/* Reserves */}
          <div>
            {org.months_of_reserve !== null && org.months_of_reserve !== undefined && (
              <>
                <p className="text-xs font-semibold text-gray-500 mb-1">Reserves</p>
                <p className="font-semibold text-lg">{org.months_of_reserve.toFixed(1)} mo</p>
                <p className="text-xs text-gray-500 mt-1">Months of operating expenses covered by unrestricted net assets</p>
              </>
            )}
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
        {isT1 && <p className="text-xs text-gray-600 mt-4 pt-4 border-t">Data source: IRS Form 990 (this organization's filing), compared against similar organizations of the same type, size, and region.</p>}
        {!isT1 && <p className="text-xs text-blue-600 mt-4 pt-4 border-t">Data source: IRS Form 990 (this organization's filing), compared against similar organizations nationally (the regional group was too small).</p>}
      </div>
    )
  }

  if (tier === '3_Broad_Category' || tier === '3b_Broad_Category') {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 mb-8">
        <h2 className="text-lg font-semibold mb-3">Peer context (broader comparison)</h2>
        <p className="text-xs text-amber-800 mb-3">The peer group for this organization's exact type and size was too small, so this compares against a wider category instead.</p>
        <p className="text-xs text-gray-700 mb-3">
          <strong>Funding Model:</strong> {org.merit_archetype_v5_label}
        </p>
        {org.tier_label && (
          <p className="text-xs text-gray-700 mb-3">
            <strong>Comparison group:</strong> {org.tier_label}
          </p>
        )}
        <p className="text-xs text-gray-700">
          <strong>We recommend asking them directly:</strong> Emergency reserve? Funding mix? How do they handle seasonal changes?
        </p>
      </div>
    )
  }

  if (tier === '4_Archetype_Only') {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-6 mb-8">
        <h2 className="text-lg font-semibold mb-3">Descriptive context only</h2>
        <p className="text-xs text-gray-700 mb-3">
          We don't have enough detailed financial data from their IRS filings for a peer comparison yet. That's not a reflection on their quality — many grassroots and newer organizations file simplified forms.
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
