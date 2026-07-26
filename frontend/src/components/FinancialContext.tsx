import React from 'react'
import type { ApiOrganization } from '../data/api'

interface FinancialContextProps {
  org: ApiOrganization
}

export default function FinancialContext({ org }: FinancialContextProps) {
  const tier = org.scoring_tier
  if (!tier) return null

  if (tier === '1_Full_Context' || tier === '2_Regional_Context') {
    const isT1 = tier === '1_Full_Context'
    return (
      <div className="rounded-lg border border-cool-grey/20 bg-cool-grey/5 p-6 mb-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold">Financial Context</h2>
          <span className={`text-xs px-2 py-1 rounded ${isT1 ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
            {isT1 ? 'High' : 'Good'} Confidence
          </span>
        </div>
        <div className="grid grid-cols-3 gap-6">
          <div>
            <p className="text-xs font-semibold text-gray-500 mb-1">Funding Model</p>
            <p className="font-semibold mb-2">{org.merit_archetype_v5_label}</p>
            <p className="text-xs text-gray-600">Peer Group: {org.peer_group_size} orgs</p>
            <p className="text-xs text-gray-500 italic">{org.peer_group_description}</p>
          </div>
          {org.months_of_reserve !== null ? (
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-1">Reserves</p>
              <p className="font-semibold text-lg">{org.months_of_reserve.toFixed(1)} mo</p>
              <p className="text-xs text-gray-600 mt-3">Signal</p>
              <p className="text-sm font-semibold">{org.merit_health_signal_v5}</p>
            </div>
          ) : null}
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
        {!isT1 && <p className="text-xs text-amber-700 mt-4 pt-4 border-t">⚠ National group spans all regions</p>}
      </div>
    )
  }

  if (tier === '3_Broad_Category') {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 mb-8">
        <h2 className="text-lg font-semibold mb-3">Funding Model Context</h2>
        <p className="text-xs text-amber-800 mb-3">⚠ Peer group includes all sizes. Small scale operates differently.</p>
        <p className="text-xs text-gray-700 mb-2"><strong>Ask them:</strong> Emergency reserve? Funding mix? Growth vision?</p>
      </div>
    )
  }

  if (tier === '4_Archetype_Only') {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-6 mb-8">
        <h2 className="text-lg font-semibold mb-3">We're Still Learning</h2>
        <p className="text-xs text-gray-700 mb-2">No financial data yet — not a quality issue. Many grassroots orgs file simplified forms.</p>
        <p className="text-xs text-gray-600"><strong>Ask them:</strong> Operating reserve? Funding sources? Financial goals?</p>
      </div>
    )
  }

  return null
}
