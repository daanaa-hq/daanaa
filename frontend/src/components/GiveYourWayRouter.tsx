/**
 * GiveYourWayRouter — donor picks how they want to give, we format the path.
 *
 * 96% of orgs have a verified street address. This component serves those with
 * no donate link + no website (the 80% case) by offering: DAF, check, bank bill
 * pay, employer match, org's own site (if available).
 *
 * Selection stays client-side. No amounts suggested (that's shaping the ask).
 * Methods listed neutrally, alphabetical on providers.
 */

import React, { useState } from 'react'

interface GiveMethodProps {
  ein: string | null | undefined
  organizationName: string | null | undefined
  streetAddress?: string | null
  city?: string | null
  state?: string | null
  donateUrl?: string | null
  donateUrlStatus?: 'beta' | 'claimed' | null | string
  website?: string | null
  websiteStatus?: 'ok' | null | string
}

type GiveMethod = 'daf' | 'check' | 'billpay' | 'employermatch' | 'site'

interface MethodConfig {
  id: GiveMethod
  label: string
  description: string
  available: (props: GiveMethodProps) => boolean
  render: (props: GiveMethodProps) => React.ReactNode
  priority: number // lower = prefer first
}

const methods: MethodConfig[] = [
  {
    id: 'site',
    label: "Organization's website",
    description: 'Give directly on their site',
    available: (p) => !!(p.donateUrl && p.donateUrlStatus && ['beta', 'claimed'].includes(String(p.donateUrlStatus))),
    render: (p) => (
      <div className="text-xs">
        <a
          href={p.donateUrl || ''}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block px-3 py-2 bg-deep-navy text-warm-cream rounded text-xs hover:bg-soft-gold transition-colors"
        >
          Go to donation page →
        </a>
      </div>
    ),
    priority: 1,
  },
  {
    id: 'daf',
    label: 'Donor-advised fund (DAF)',
    description: 'Fidelity, Schwab, Vanguard, or your fund manager',
    available: (p) => !!(p.ein && p.streetAddress),
    render: (p) => (
      <div className="text-xs space-y-2">
        <p className="text-deep-navy font-medium">Enter in your DAF provider:</p>
        <div className="bg-slate-100 border border-slate-300 p-2 rounded font-mono text-xs text-deep-navy space-y-1">
          <div>EIN: {p.ein}</div>
          {p.streetAddress && <div className="text-slate-600">{p.streetAddress}</div>}
        </div>
        <button
          onClick={() => navigator.clipboard.writeText(`${p.ein}`)}
          className="text-xs text-soft-gold hover:text-gold font-medium"
        >
          Copy EIN
        </button>
      </div>
    ),
    priority: 2,
  },
  {
    id: 'check',
    label: 'Check by mail',
    description: 'Make a check payable to the organization',
    available: (p) => !!(p.ein && p.streetAddress),
    render: (p) => (
      <div className="text-xs space-y-2">
        <p className="text-deep-navy font-medium">Make check payable to:</p>
        <div className="bg-slate-100 border border-slate-300 p-2 rounded text-deep-navy text-xs space-y-0.5">
          <div className="font-semibold">{p.organizationName}</div>
          {p.streetAddress && (
            <>
              <div className="text-slate-600">{p.streetAddress}</div>
              {p.city && p.state && <div className="text-slate-600">{p.city}, {p.state}</div>}
            </>
          )}
        </div>
      </div>
    ),
    priority: 3,
  },
  {
    id: 'billpay',
    label: 'Bank bill pay',
    description: 'Send a payment through your bank',
    available: (p) => !!(p.ein && p.streetAddress),
    render: (p) => (
      <div className="text-xs space-y-2">
        <p className="text-deep-navy font-medium">Add as payee in bill pay:</p>
        <div className="bg-slate-100 border border-slate-300 p-2 rounded text-deep-navy text-xs space-y-0.5">
          <div className="font-semibold">{p.organizationName}</div>
          {p.streetAddress && (
            <>
              <div className="text-slate-600">{p.streetAddress}</div>
              {p.city && p.state && <div className="text-slate-600">{p.city}, {p.state}</div>}
            </>
          )}
        </div>
      </div>
    ),
    priority: 4,
  },
  {
    id: 'employermatch',
    label: 'Employer match',
    description: 'File a grant recommendation with your company',
    available: (p) => !!p.ein,
    render: (p) => (
      <div className="text-xs space-y-2">
        <p className="text-deep-navy font-medium">Enter in company platform:</p>
        <div className="bg-slate-100 border border-slate-300 p-2 rounded font-mono text-xs text-deep-navy space-y-1">
          <div>EIN: {p.ein}</div>
          <div className="text-slate-600">Org: {p.organizationName}</div>
        </div>
        <button
          onClick={() => navigator.clipboard.writeText(`${p.ein}`)}
          className="text-xs text-soft-gold hover:text-gold font-medium"
        >
          Copy EIN
        </button>
      </div>
    ),
    priority: 5,
  },
]

export default function GiveYourWayRouter(props: GiveMethodProps) {
  const [expanded, setExpanded] = React.useState<GiveMethod | null>(null)
  const available = methods.filter((m) => m.available(props)).sort((a, b) => a.priority - b.priority)

  if (available.length === 0) {
    return null
  }

  return (
    <div className="mt-4 space-y-2">
      {/* All methods as compact expandable cards */}
      {available.map((method) => (
        <button
          key={method.id}
          onClick={() => setExpanded(expanded === method.id ? null : method.id)}
          className={`w-full text-left p-3 rounded border transition-all ${
            expanded === method.id
              ? 'border-soft-gold bg-warm-cream/60'
              : 'border-light-grey bg-white hover:bg-warm-cream/20'
          }`}
        >
          {/* Method header */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex-1">
              <div className="font-medium text-deep-navy text-sm">{method.label}</div>
              <div className="text-xs text-cool-grey">{method.description}</div>
            </div>
            <span className="text-soft-gold text-lg flex-shrink-0 font-light">
              {expanded === method.id ? '▼' : '▶'}
            </span>
          </div>

          {/* Method details (expandable) */}
          {expanded === method.id && (
            <div className="mt-3 pt-3 border-t border-light-grey/50">
              {method.render(props)}
            </div>
          )}
        </button>
      ))}
    </div>
  )
}
