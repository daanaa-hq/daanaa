import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function VendorPolicy() {
  usePageMeta(
    'Impact Network Partner Policy — Daanaa',
    'The rules governing participation in the Daanaa Impact Network for community partners and network partners.',
  )

  return (
    <div className="min-h-[100dvh] bg-warm-cream">
      <div className="max-w-[800px] mx-auto px-6 lg:px-12 py-24">
        <Link to="/for-vendors" className="font-body text-caption tracking-[0.02em] text-cool-grey hover:text-deep-navy transition-colors">
          ← Back to Partners
        </Link>

        <h1 className="font-display italic text-deep-navy mt-6 leading-[0.95] tracking-[-0.02em]">
          Daanaa Impact Network<br />Partner Policy
        </h1>
        <p className="mt-4 font-body text-small text-muted-cream">
          Effective June 14, 2026 · Operated by EcoMargins Consulting LLC
        </p>

        <div className="mt-12 space-y-12 font-body text-body-lg text-cool-grey leading-[1.7]">

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg mb-4">What the Daanaa Impact Network is</h2>
            <p>
              Daanaa is an independent nonprofit discovery platform. The Daanaa Impact Network is a
              voluntary program that connects businesses and service providers with the nonprofit
              organizations that use Daanaa to manage their public profile.
            </p>
            <p className="mt-3">
              The goal is simple: make it easier for nonprofits to access services, tools, and
              resources at fair prices. Participation is a values commitment, not just a commercial
              transaction. Partners join because they believe in supporting the sector.
            </p>
            <p className="mt-3">The network has two tiers:</p>
            <ul className="mt-3 space-y-2 ml-4 list-disc">
              <li><strong className="text-deep-navy">Community Partners:</strong> Any business that offers a genuine benefit to nonprofits. No formal contract required. Applications are reviewed by Daanaa staff and activated at Daanaa's discretion.</li>
              <li><strong className="text-deep-navy">Network Partners:</strong> Businesses that have entered into a formal Collective Action Framework (CAF) agreement with EcoMargins Consulting LLC. Network partners agree to reporting requirements and milestone-based pricing commitments.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg mb-4">What partners agree to</h2>
            <ol className="space-y-4 ml-4 list-decimal">
              <li>
                <strong className="text-deep-navy">Accuracy.</strong> Every offer, discount, code,
                or benefit you list must be real, currently available, and honored without additional
                barriers not disclosed in your listing. If a deal expires or changes, notify Daanaa
                immediately.
              </li>
              <li>
                <strong className="text-deep-navy">Honest description.</strong> Your listing must
                describe what you offer, what the benefit is, and how a nonprofit accesses it.
                Inflated prices, fake discounts, and bait-and-switch terms are grounds for immediate
                removal.
              </li>
              <li>
                <strong className="text-deep-navy">No solicitation of donations.</strong>{' '}
                Participation does not authorize you to solicit charitable contributions on Daanaa's
                behalf or in Daanaa's name. You are not a fundraising agent for Daanaa or any
                nonprofit.
              </li>
              <li>
                <strong className="text-deep-navy">Respect for nonprofits.</strong> Nonprofits that
                access your benefits through Daanaa must not be enrolled in marketing lists,
                retargeted, or contacted for sales purposes beyond the service relationship they
                initiate. You may not use Daanaa membership to build prospect lists.
              </li>
              <li>
                <strong className="text-deep-navy">Values alignment.</strong> Daanaa operates under
                a{' '}
                <Link to="/stewardship" className="text-soft-gold hover:underline">
                  Founding Stewardship Commitment
                </Link>
                . Partners whose business practices are in material conflict with those principles are
                not eligible to participate and may be removed.
              </li>
            </ol>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg mb-4">What Daanaa commits to</h2>
            <p>
              <strong className="text-deep-navy">Independence is non-negotiable.</strong> Partner
              participation, including the payment of any fees, never affects how an organization
              appears in Daanaa search results, its V6 public context, or any other trust signal
              on the platform. No partner may pay for placement.
              This principle is absolute and derives directly from{' '}
              <Link to="/stewardship" className="text-soft-gold hover:underline">Principle 7</Link>{' '}
              of the Founding Stewardship Commitment.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">Fair review.</strong> Applications are reviewed on
              values fit and benefit quality, not on the size of the partner.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">Disclosure.</strong> Daanaa discloses to nonprofits
              that the network includes partner relationships and that those relationships contribute
              to platform sustainability. Partner relationships are never presented as endorsements of
              individual organizations.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg mb-4">Data and privacy</h2>
            <p>
              Daanaa does not share donor data, giving history, wallet contents, or any user-level
              behavioral data with partners. Ever.
            </p>
            <p className="mt-3">
              When a nonprofit accesses a partner benefit through Daanaa, the only information Daanaa
              may confirm to the partner for verification purposes is the organization's name, EIN,
              and claimed status on the platform. No financial data, no giving data, no donor
              information.
            </p>
            <p className="mt-3">
              Partners may not use EIN-level information obtained through the Daanaa Impact Network
              to build commercial databases, enrich third-party lists, or resell organization data.
              This obligation survives the end of your participation.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg mb-4">Daanaa's role and limits</h2>
            <p>
              Daanaa is the convener of the network. Daanaa is not a party to any transaction between
              a partner and a nonprofit. When a nonprofit uses a code, accesses a benefit, or enters a
              service relationship with a partner, that relationship is directly between the nonprofit
              and the partner.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">Daanaa makes no warranty</strong>, express, implied,
              or otherwise, that any listed benefit is available, accurate, of merchantable quality,
              or fit for any particular purpose. Nonprofits use partner benefits at their own
              discretion.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg mb-4">Liability and indemnification</h2>
            <p>
              You are responsible for the accuracy and legality of every listing you submit.
            </p>
            <p className="mt-3">
              You agree to indemnify, defend, and hold harmless EcoMargins Consulting LLC, its officers, agents,
              and representatives from any claim, liability, loss, damage, or expense (including
              reasonable legal fees) arising from: (a) the inaccuracy or misrepresentation of your
              listing; (b) your failure to fulfill a listed offer; (c) your use of nonprofit data
              obtained through the network; or (d) any violation of applicable law in connection with
              your participation.
            </p>
            <p className="mt-3">
              To the maximum extent permitted by applicable law, EcoMargins Consulting LLC's total liability to
              any partner shall not exceed the fees paid by that partner in the twelve months preceding
              the claim. Community partners participating at no cost acknowledge that Daanaa's
              liability is zero.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg mb-4">Removal and disputes</h2>
            <p>
              Daanaa may remove any partner listing at any time, for any reason, including values
              misalignment, inaccurate listings, nonprofit complaints, or changes in platform
              direction.
            </p>
            <p className="mt-3">
              If you believe a removal was made in error, write to{' '}
              <a href="mailto:partners@daanaa.org" className="text-soft-gold hover:underline">
                partners@daanaa.org
              </a>
              . Daanaa will respond within ten business days. The outcome is final.
            </p>
            <p className="mt-3">
              Daanaa does not mediate disputes between partners and nonprofits. Those disputes are
              between the parties directly.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg mb-4">Governing terms</h2>
            <p>
              This policy is governed by the laws of the State of Texas, without regard to
              conflict-of-law principles, reflecting the jurisdiction of EcoMargins Consulting LLC.
            </p>
            <p className="mt-3">
              Daanaa may update this policy at any time. Material changes will be communicated to
              active partners by email at least 14 days before taking effect. Continued participation
              after the effective date constitutes acceptance.
            </p>
            <p className="mt-3">
              This policy is not a contract on its own. Network Partners operate under a separate
              Collective Action Framework agreement that incorporates this policy by reference.
              Community Partners accept this policy through the application process.
            </p>
            <p className="mt-3">
              In any conflict between this policy and the{' '}
              <Link to="/stewardship" className="text-soft-gold hover:underline">
                Founding Stewardship Commitment
              </Link>
              , the Stewardship Commitment governs.
            </p>
          </section>

          <section className="pt-4 border-t border-light-grey">
            <p className="font-body text-small text-muted-cream">
              Partnership inquiries:{' '}
              <a href="mailto:partners@daanaa.org" className="text-soft-gold hover:underline">partners@daanaa.org</a>
              {' · '}
              Policy questions:{' '}
              <a href="mailto:legal@daanaa.org" className="text-soft-gold hover:underline">legal@daanaa.org</a>
              {' · '}
              EcoMargins Consulting LLC · Operating as Daanaa · daanaa.org
            </p>
          </section>

        </div>
      </div>
    </div>
  )
}
