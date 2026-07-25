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
      <div className="text-sm space-y-2">
        <p>Give directly on their website:</p>
        <a
          href={p.donateUrl || ''}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block px-3 py-2 bg-deep-navy text-warm-cream rounded hover:bg-soft-gold"
        >
          Open donation page →
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
      <div className="text-sm space-y-3">
        <p className="text-deep-navy">In your DAF provider (Fidelity, Schwab, Vanguard, etc.), enter:</p>
        <div className="bg-slate-100 border border-slate-300 p-4 rounded font-mono text-sm text-deep-navy">
          <div className="font-semibold">EIN: {p.ein}</div>
          {p.streetAddress && <div className="text-slate-700 mt-2">Address: {p.streetAddress}</div>}
        </div>
        <button
          onClick={() => navigator.clipboard.writeText(`${p.ein}`)}
          className="text-sm text-soft-gold hover:text-gold font-medium transition-colors"
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
      <div className="text-sm space-y-3">
        <p className="text-deep-navy">Make a check payable to:</p>
        <div className="bg-slate-100 border border-slate-300 p-4 rounded text-deep-navy">
          <div className="font-semibold text-base">{p.organizationName}</div>
          {p.streetAddress && (
            <>
              <div className="text-slate-700 mt-2">{p.streetAddress}</div>
              {p.city && p.state && <div className="text-slate-700">{p.city}, {p.state}</div>}
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
      <div className="text-sm space-y-3">
        <p className="text-deep-navy">In your bank's bill pay, add this payee:</p>
        <div className="bg-slate-100 border border-slate-300 p-4 rounded text-deep-navy">
          <div className="font-semibold text-base">{p.organizationName}</div>
          {p.streetAddress && (
            <>
              <div className="text-slate-700 mt-2">{p.streetAddress}</div>
              {p.city && p.state && <div className="text-slate-700">{p.city}, {p.state}</div>}
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
      <div className="text-sm space-y-3">
        <p className="text-deep-navy">In your company's giving platform (Benevity, YourCause, etc.):</p>
        <div className="bg-slate-100 border border-slate-300 p-4 rounded font-mono text-sm text-deep-navy">
          <div className="font-semibold">EIN: {p.ein}</div>
          <div className="text-slate-700 mt-2">Name: {p.organizationName}</div>
        </div>
        <button
          onClick={() => navigator.clipboard.writeText(`${p.ein}`)}
          className="text-sm text-soft-gold hover:text-gold font-medium transition-colors"
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
    <div className="mt-8 space-y-4">
      <h3 className="font-semibold text-deep-navy text-lg">How would you like to give?</h3>

      {/* All methods as expandable cards */}
      <div className="space-y-3">
        {available.map((method) => (
          <button
            key={method.id}
            onClick={() => setExpanded(expanded === method.id ? null : method.id)}
            className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
              expanded === method.id
                ? 'border-soft-gold bg-warm-cream'
                : 'border-light-grey bg-white hover:border-soft-gold/50'
            }`}
          >
            {/* Method header (always visible) */}
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="font-semibold text-deep-navy">{method.label}</div>
                <div className="text-sm text-cool-grey mt-1">{method.description}</div>
              </div>
              <span className="text-soft-gold text-xl flex-shrink-0">
                {expanded === method.id ? '−' : '+'}
              </span>
            </div>

            {/* Method details (expandable) */}
            {expanded === method.id && (
              <div className="mt-4 pt-4 border-t border-light-grey">
                {method.render(props)}
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  )
}
