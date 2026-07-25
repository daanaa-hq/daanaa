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
      <div className="text-sm space-y-2">
        <p>In your DAF provider (Fidelity, Schwab, Vanguard, etc.), enter:</p>
        <div className="bg-light-grey p-3 rounded font-mono text-xs">
          <div>EIN: {p.ein}</div>
          {p.streetAddress && <div>Address: {p.streetAddress}</div>}
        </div>
        <button
          onClick={() => navigator.clipboard.writeText(`${p.ein}`)}
          className="text-xs text-soft-gold hover:underline"
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
      <div className="text-sm space-y-2">
        <p>Make a check payable to:</p>
        <div className="bg-light-grey p-3 rounded">
          <div className="font-semibold">{p.organizationName}</div>
          {p.streetAddress && (
            <>
              <div>{p.streetAddress}</div>
              {p.city && p.state && <div>{p.city}, {p.state}</div>}
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
      <div className="text-sm space-y-2">
        <p>In your bank's bill pay, add this payee:</p>
        <div className="bg-light-grey p-3 rounded">
          <div className="font-semibold">{p.organizationName}</div>
          {p.streetAddress && (
            <>
              <div>{p.streetAddress}</div>
              {p.city && p.state && <div>{p.city}, {p.state}</div>}
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
      <div className="text-sm space-y-2">
        <p>In your company's giving platform (Benevity, YourCause, etc.):</p>
        <div className="bg-light-grey p-3 rounded font-mono text-xs">
          <div>Organization EIN: {p.ein}</div>
          <div>Name: {p.organizationName}</div>
        </div>
        <button
          onClick={() => navigator.clipboard.writeText(`${p.ein}`)}
          className="text-xs text-soft-gold hover:underline"
        >
          Copy EIN
        </button>
      </div>
    ),
    priority: 5,
  },
]

export default function GiveYourWayRouter(props: GiveMethodProps) {
  const available = methods.filter((m) => m.available(props)).sort((a, b) => a.priority - b.priority)

  if (available.length === 0) {
    return null
  }

  const [selected, setSelected] = useState<GiveMethod>(available[0].id)
  const selectedMethod = methods.find((m) => m.id === selected)!
  const primary = available.slice(0, 2)
  const secondary = available.slice(2)

  return (
    <div className="mt-8 p-6 border border-soft-gold rounded bg-warm-cream space-y-4">
      <div>
        <h3 className="font-semibold text-deep-navy mb-4">How would you like to give?</h3>

        {/* Primary methods — visible by default */}
        <div className="space-y-2 mb-4">
          {primary.map((method) => (
            <label key={method.id} className="flex items-start gap-3 cursor-pointer">
              <input
                type="radio"
                name="give-method"
                value={method.id}
                checked={selected === method.id}
                onChange={() => setSelected(method.id)}
                className="mt-1"
              />
              <div className="flex-1">
                <div className="font-medium text-deep-navy">{method.label}</div>
                <div className="text-sm text-cool-grey">{method.description}</div>
              </div>
            </label>
          ))}
        </div>

        {/* Secondary methods — behind disclosure */}
        {secondary.length > 0 && (
          <details className="text-sm">
            <summary className="text-soft-gold hover:underline cursor-pointer">
              Other ways to give ({secondary.length})
            </summary>
            <div className="space-y-2 mt-3 pl-4">
              {secondary.map((method) => (
                <label key={method.id} className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name="give-method"
                    value={method.id}
                    checked={selected === method.id}
                    onChange={() => setSelected(method.id)}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-deep-navy">{method.label}</div>
                    <div className="text-xs text-cool-grey">{method.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </details>
        )}
      </div>

      {/* Render the selected method's instructions */}
      <div className="pt-4 border-t border-soft-gold">{selectedMethod?.render(props)}</div>
    </div>
  )
}
