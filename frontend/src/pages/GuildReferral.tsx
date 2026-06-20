import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

interface VendorDeal {
  id: number
  vendor_name: string
  category: string
  description: string
  discount_label: string
  website_url: string
  how_to_use: string
}

export default function GuildReferral() {
  const { slug } = useParams<{ slug: string }>()
  const [vendor, setVendor] = useState<VendorDeal | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  usePageMeta(
    vendor ? `${vendor.vendor_name} — Daanaa Guild` : 'Daanaa Guild',
    vendor
      ? `${vendor.vendor_name} offers Daanaa guild members ${vendor.discount_label}. Claim your free Daanaa page to access this and other guild benefits.`
      : 'Daanaa Guild member benefits.',
  )

  useEffect(() => {
    if (!slug) return
    fetch(`/api/guild/referral/${slug}`)
      .then(r => {
        if (!r.ok) { setNotFound(true); setLoading(false); return null }
        return r.json()
      })
      .then(data => {
        if (data) setVendor(data)
        setLoading(false)
      })
      .catch(() => { setNotFound(true); setLoading(false) })
  }, [slug])

  if (loading) {
    return (
      <div className="min-h-[100dvh] bg-warm-cream flex items-center justify-center">
        <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
      </div>
    )
  }

  if (notFound || !vendor) {
    return (
      <div className="min-h-[100dvh] bg-warm-cream flex items-center justify-center px-6">
        <div className="text-center max-w-[400px]">
          <h1 className="font-display italic text-[28px] text-deep-navy mb-3">Link not found</h1>
          <p className="font-body text-[15px] text-cool-grey mb-6 leading-[1.7]">
            This partner link may have changed or expired. Visit the Daanaa Guild to see all
            current member benefits.
          </p>
          <Link
            to="/for-nonprofits"
            className="inline-block px-6 py-3 bg-soft-gold text-deep-navy font-body text-[14px] font-semibold rounded-xl hover:bg-bright-gold transition-colors"
          >
            Claim your free page
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[100dvh] bg-warm-cream">

      {/* Hero */}
      <div className="bg-deep-navy pt-[108px] pb-20 px-6">
        <div className="max-w-[680px] mx-auto text-center">
          <p className="font-body text-[12px] font-medium tracking-[0.12em] text-soft-gold uppercase mb-5">
            Daanaa Guild: Exclusive Member Benefit
          </p>
          <h1
            className="font-display italic text-warm-cream leading-[1.1] mb-6"
            style={{ fontSize: 'clamp(28px, 4.5vw, 48px)' }}
          >
            {vendor.vendor_name}<br />
            <span className="text-soft-gold">{vendor.discount_label}</span>
          </h1>
          <p className="font-body text-[16px] text-warm-cream/80 leading-[1.7] mb-8">
            {vendor.description}
          </p>
          {vendor.website_url && (
            <a
              href={vendor.website_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block px-8 py-3.5 bg-soft-gold text-deep-navy font-body text-[15px] font-semibold rounded-xl hover:bg-bright-gold transition-colors"
            >
              Visit {vendor.vendor_name}
            </a>
          )}
        </div>
      </div>

      <div className="max-w-[680px] mx-auto px-6 py-14">

        {/* How to access */}
        {vendor.how_to_use && (
          <div className="bg-white rounded-2xl border border-light-grey p-7 mb-8">
            <h2 className="font-body text-[15px] font-semibold text-deep-navy mb-3">
              How to access this benefit
            </h2>
            <p className="font-body text-[15px] text-cool-grey leading-[1.7]">
              {vendor.how_to_use}
            </p>
          </div>
        )}

        {/* CTA for non-members */}
        <div className="bg-deep-navy rounded-2xl p-8 text-center mb-8">
          <p className="font-body text-[12px] font-medium tracking-[0.12em] text-soft-gold uppercase mb-4">
            Not a Daanaa member yet?
          </p>
          <h2 className="font-display italic text-[26px] text-warm-cream mb-3">
            Claim your free page to unlock this and more.
          </h2>
          <p className="font-body text-[14px] text-warm-cream/70 leading-[1.7] mb-6 max-w-[480px] mx-auto">
            The Daanaa Guild brings {vendor.vendor_name} and other community partners together
            for nonprofits like yours. Free to join. Better rates for everyone as the
            guild grows.
          </p>
          <Link
            to="/for-nonprofits"
            className="inline-block px-8 py-3.5 bg-soft-gold text-deep-navy font-body text-[15px] font-semibold rounded-xl hover:bg-bright-gold transition-colors"
          >
            Claim your free Daanaa page
          </Link>
        </div>

        {/* What the guild is */}
        <div className="space-y-3 mb-10">
          {[
            {
              title: 'One contract, one code',
              body: 'Every Daanaa member uses the same discount code. No individual signups or negotiations.',
            },
            {
              title: 'Rates improve as the guild grows',
              body: 'Milestone pricing is built into every partner contract. The more members use the guild, the better the rates get, for everyone, automatically.',
            },
            {
              title: 'Free for nonprofits, always',
              body: 'Guild membership is free. Partners pay a standard contract administration fee. You never pay Daanaa anything.',
            },
          ].map(({ title, body }) => (
            <div key={title} className="flex gap-4 bg-white rounded-xl border border-light-grey p-5">
              <span className="shrink-0 mt-1 w-5 h-5 rounded-full bg-soft-gold/15 flex items-center justify-center">
                <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                  <path d="M1 4L3.5 6.5L9 1" stroke="#C9A96E" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </span>
              <div>
                <p className="font-body text-[14px] font-semibold text-deep-navy mb-0.5">{title}</p>
                <p className="font-body text-[13px] text-cool-grey leading-[1.6]">{body}</p>
              </div>
            </div>
          ))}
        </div>

        <p className="text-center font-body text-[13px] text-cool-grey">
          Questions?{' '}
          <a href="mailto:hello@daanaa.org" className="text-soft-gold hover:underline">
            hello@daanaa.org
          </a>
          {' · '}
          <Link to="/principles" className="text-soft-gold hover:underline">
            Our stewardship commitment
          </Link>
        </p>
      </div>
    </div>
  )
}
