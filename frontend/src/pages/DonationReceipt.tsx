import React from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function DonationReceipt() {
  usePageMeta('Giving Record | Daanaa', 'Your personal giving record from your Daanaa wallet')

  const [searchParams] = useSearchParams()
  const orgName = searchParams.get('org') || ''
  const ein = searchParams.get('ein') || ''
  const date = searchParams.get('date') || ''

  return (
    <div className="min-h-screen bg-soft-cream p-6">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="font-display text-3xl text-deep-navy mb-2">Giving Record</h1>
          <p className="text-cool-grey">Your personal note from your Daanaa wallet</p>
        </div>

        <div className="bg-white rounded-lg p-8 border border-light-grey space-y-6">
          {orgName && (
            <div className="bg-soft-cream rounded p-4">
              <p className="text-xs text-cool-grey uppercase tracking-wide mb-1">Organization</p>
              <p className="font-display text-xl text-deep-navy">{orgName}</p>
              {ein && <p className="text-sm text-cool-grey mt-0.5">EIN: {ein}</p>}
              {date && (
                <p className="text-sm text-cool-grey">
                  {new Date(date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
                </p>
              )}
            </div>
          )}

          <div className="border border-amber-200 bg-amber-50 rounded-lg p-5 space-y-3">
            <p className="font-semibold text-amber-900 text-sm">For your official tax receipt</p>
            <p className="text-sm text-amber-800 leading-relaxed">
              Daanaa is a discovery platform — we don't process donations or issue tax documentation.
              Your official receipt for tax purposes comes directly from the nonprofit you gave to.
            </p>
            <p className="text-sm text-amber-800 leading-relaxed">
              Contact {orgName || 'the organization'} directly and reference their EIN
              {ein ? <strong> ({ein})</strong> : ''} to request an acknowledgment letter.
              For gifts of $250 or more, the IRS requires a written acknowledgment from the organization itself — not from a third party.
            </p>
          </div>

          <div className="border-t border-light-grey pt-6 space-y-2">
            <p className="text-xs text-cool-grey leading-relaxed">
              This wallet entry is a personal record you created. It is stored only on your device
              and not shared with Daanaa or any third party.
            </p>
            <p className="text-xs text-cool-grey">
              IRS Publication 526 covers charitable contribution rules. For deductibility,
              always verify the organization's 501(c)(3) status at{' '}
              <a
                href="https://apps.irs.gov/app/eos/"
                target="_blank"
                rel="noopener noreferrer"
                className="underline"
              >
                IRS Tax Exempt Organization Search
              </a>.
            </p>
          </div>

          <div className="border-t border-light-grey pt-6">
            <Link
              to="/wallet"
              className="inline-flex items-center gap-2 font-body text-sm text-soft-gold hover:text-bright-gold transition-colors"
            >
              ← Back to your wallet
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
