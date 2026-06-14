import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function Terms() {
  usePageMeta(
    'Terms of Service — Daanaa',
    'Terms governing use of daanaa.org, operated by EcoMargins Consulting LLC.',
  )

  return (
    <div className="min-h-[100dvh] bg-warm-cream">
      <div className="max-w-[800px] mx-auto px-6 lg:px-12 py-24">
        <Link to="/" className="font-body text-[12px] tracking-[0.02em] text-cool-grey hover:text-deep-navy transition-colors">
          ← Back to Home
        </Link>

        <h1 className="font-display italic text-deep-navy mt-6 leading-[0.95] tracking-[-0.02em]"
            style={{ fontSize: 'clamp(32px, 5vw, 56px)' }}>
          Terms of Service
        </h1>
        <p className="mt-4 font-body text-[13px] text-muted-cream">
          Effective June 14, 2026 · Operated by EcoMargins Consulting LLC
        </p>

        <div className="mt-12 space-y-12 font-body text-[15px] text-cool-grey leading-[1.7]">

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">1. Who we are and what Daanaa is</h2>
            <p>
              Daanaa is operated by <strong className="text-deep-navy">EcoMargins Consulting LLC</strong>, a for-profit Texas
              limited liability company. Daanaa is not a nonprofit organization. We are not affiliated with the IRS
              or any government agency.
            </p>
            <p className="mt-3">
              Daanaa is a public-data directory of U.S. 501(c)(3) organizations. We aggregate publicly available
              information from IRS filings, ProPublica, and the National Center for Charitable Statistics, and present
              it in a searchable format. Our purpose is to help people discover and learn about nonprofits —
              particularly smaller organizations with limited public visibility.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">2. What Daanaa does not do</h2>
            <p>
              <strong className="text-deep-navy">We never handle money.</strong> Daanaa does not receive, process,
              hold, transmit, or facilitate charitable donations. All giving happens directly between donors and the
              nonprofits they choose — through the nonprofit's own payment processor, bank account, or a third-party
              giving service. We are not a merchant of record, not a payment intermediary, not an escrow service, and
              not a fundraising platform.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">We are not a charity.</strong> Daanaa is a for-profit data platform.
              We cannot receive tax-deductible contributions and do not make grants.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">3. Acceptance of these terms</h2>
            <p>
              By accessing or using daanaa.org, you agree to be bound by these Terms of Service. If you do not agree,
              please do not use the site.
            </p>
            <p className="mt-3">
              Use of the site by a person under 13 is not permitted. If you are between 13 and 18, you represent that
              you have your parent's or guardian's permission to use the site.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">4. The Giving Wallet</h2>
            <p>
              The Giving Wallet is a free bookmarking tool that requires a Google account to use. Sign in with
              Google to save organizations and access your wallet across devices. Your wallet holds bookmarks and
              giving intent only — never transaction records. It is never shown publicly, never used for marketing
              or outreach, and can be deleted in full at any time. Browsing the directory does not require an
              account.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">5. Claimed organization pages</h2>
            <p>
              Organizations that have claimed their page on Daanaa have provided their name, title, email, and phone
              number for verification. Claimed content is labeled accordingly. A claim does not constitute Daanaa's
              endorsement of an organization's programs, financial health, or charitable effectiveness.
            </p>
            <p className="mt-3">
              The information an organization provides when claiming its page is subject to their representation that
              it is accurate. Daanaa verifies identity, not the accuracy of every statement an organization makes.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">6. Accuracy of data</h2>
            <p>
              Financial data on Daanaa is derived from IRS Form 990 filings. The most recent filing available may
              lag the current fiscal year by 12–24 months. Daanaa peer financial context scores are a relative
              benchmark — they indicate how an organization compares to similar organizations in the same NTEE category
              and revenue range based on public filing data. A score is not an audit, a recommendation, a rating of
              organizational quality, or an endorsement. It is a data point.
            </p>
            <p className="mt-3">
              Mission summaries and search tags marked <strong className="text-deep-navy">beta</strong> are generated
              by AI from public IRS category and filing data. They are a starting point, may be incomplete or
              inaccurate, and are not the organization's own statement of its mission.
            </p>
            <p className="mt-3">
              Website links marked <strong className="text-deep-navy">beta</strong> were discovered by automated
              search and have not been provided by the organization. Confirm you are on the correct organization's
              official page before submitting any personal or financial information.
            </p>
            <p className="mt-3">
              Daanaa makes no warranty about the completeness, accuracy, timeliness, or fitness for any purpose of
              any data displayed on the site. We are not liable for decisions made based on information provided here.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">7. Acceptable use</h2>
            <p>
              You may use daanaa.org for personal, academic, journalistic, or nonprofit research purposes. You may
              quote and cite Daanaa data with attribution (daanaa.org) under those purposes.
            </p>
            <p className="mt-3">You may not:</p>
            <ul className="mt-2 ml-4 space-y-1 list-disc">
              <li>Scrape the site at a rate that degrades service for other users</li>
              <li>Use Daanaa data to build commercial prospect lists or donor databases for resale</li>
              <li>Redistribute Daanaa data in bulk for commercial purposes without our written permission</li>
              <li>Attempt to gain unauthorized access to any system, database, or account</li>
              <li>Use the site in any way that violates applicable law</li>
            </ul>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">8. Volunteer events</h2>
            <p>
              Nonprofit organizations that have claimed their page may post volunteer opportunities. Daanaa is a
              listing service only. We do not organize, coordinate, supervise, staff, insure, or guarantee any
              volunteer event. The relationship is entirely between the volunteer and the nonprofit. Daanaa is not
              liable for any harm, injury, damage, or loss arising from participation in any event listed on the site.
            </p>
            <p className="mt-3">
              Organizations that post volunteer events represent that they are responsible for the safety of those
              events, including appropriate insurance and compliance with applicable local requirements.
            </p>
            <p className="mt-3">
              If an event involves minors or requires parental supervision, it is the organization's responsibility
              to state so clearly in their listing. Parents and guardians are responsible for determining whether an
              event is appropriate for minors in their care. Daanaa does not screen volunteer listings for
              age-appropriateness or child-safety compliance.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">9. Impact Network and partner benefits</h2>
            <p>
              Daanaa operates an Impact Network that connects nonprofits with businesses offering services at
              preferential rates. Vendor participation — including any fees paid to Daanaa — never affects how any
              organization appears in search results, its financial context score, its tier, or any other trust signal
              on the platform. This principle is absolute and is embedded in our{' '}
              <Link to="/stewardship" className="text-soft-gold hover:underline">
                Founding Stewardship Commitment
              </Link>.
            </p>
            <p className="mt-3">
              Vendor benefits are listed for informational purposes. Daanaa does not warranty the accuracy,
              availability, or quality of any vendor's product or service. Transactions are directly between the
              nonprofit and the vendor. Daanaa is not a party to those transactions.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">10. Intellectual property</h2>
            <p>
              Daanaa's original expression — including our scoring methodology descriptions, platform design, and
              editorial content — is protected by copyright and owned by EcoMargins Consulting LLC.
            </p>
            <p className="mt-3">
              Organization data (names, addresses, EINs, financial figures from 990 filings) is derived from
              public-domain government filings. Daanaa does not claim copyright in that underlying government data.
            </p>
            <p className="mt-3">
              You may not reproduce or distribute Daanaa's original expression or platform design in any commercial
              context without our prior written permission.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">11. Third-party links</h2>
            <p>
              Daanaa links to nonprofit websites, donation pages, and vendor sites. We do not control those sites
              and are not responsible for their content, privacy practices, or availability. A link is not an
              endorsement.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">12. Privacy</h2>
            <p>
              Our full privacy practices are described on our{' '}
              <Link to="/legal" className="text-soft-gold hover:underline">Legal & Data Attribution page</Link>.
              Key facts:
            </p>
            <ul className="mt-3 ml-4 space-y-1 list-disc">
              <li>We do not use cookies for tracking and do not run behavioral analytics.</li>
              <li>We do not sell personal information.</li>
              <li>The Giving Wallet requires a free Google account. Wallet data is never shown publicly and can be deleted at any time.</li>
              <li>If you submit personal information (claim form, feedback form), we use it only to respond to your request.</li>
              <li>California residents have CCPA rights as described on our Legal page.</li>
              <li>EU and UK residents have GDPR rights as described on our Legal page. Daanaa is a U.S.-directed service; EcoMargins Consulting LLC is the data controller.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">13. Disclaimer of warranties</h2>
            <p className="uppercase text-[13px] tracking-[0.01em]">
              Daanaa is provided "as is" without warranty of any kind. EcoMargins Consulting LLC disclaims all warranties,
              express or implied, including warranties of merchantability, fitness for a particular purpose, and
              non-infringement.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">14. Limitation of liability</h2>
            <p className="uppercase text-[13px] tracking-[0.01em]">
              To the maximum extent permitted by applicable law, EcoMargins Consulting LLC's total liability to you for any
              claim arising from or related to use of Daanaa is limited to $100. EcoMargins Consulting LLC is not liable for
              indirect, incidental, consequential, punitive, or special damages.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">15. Indemnification</h2>
            <p>
              You agree to indemnify, defend, and hold harmless EcoMargins Consulting LLC, its members, managers, officers,
              employees, and agents from any claim, liability, loss, or expense (including reasonable attorneys' fees)
              arising from your use of daanaa.org in violation of these Terms or applicable law.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">16. Governing law and disputes</h2>
            <p>
              These Terms are governed by the laws of the State of Texas, without regard to conflict-of-law
              principles.
            </p>
            <p className="mt-3">
              Disputes that cannot be resolved informally within 30 days of written notice will be submitted to
              binding arbitration in Texas under the rules of the American Arbitration Association, with one
              arbitrator. The prevailing party is entitled to recover its reasonable attorneys' fees. You waive any
              right to a jury trial or to participate in a class action.
            </p>
            <p className="mt-3">
              Nothing in this section limits either party's right to seek injunctive or other equitable relief.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">17. Changes to these terms</h2>
            <p>
              We may update these Terms at any time. Material changes will be posted on this page with a new
              effective date. Continued use of the site after the effective date constitutes acceptance of the
              updated Terms.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-[22px] mb-4">18. Contact</h2>
            <p>
              Legal questions:{' '}
              <a href="mailto:legal@daanaa.org" className="text-soft-gold hover:underline">legal@daanaa.org</a>
              {' · '}
              Privacy and data requests:{' '}
              <a href="mailto:privacy@daanaa.org" className="text-soft-gold hover:underline">privacy@daanaa.org</a>
              {' · '}
              Data corrections:{' '}
              <a href="mailto:trust@daanaa.org" className="text-soft-gold hover:underline">trust@daanaa.org</a>
            </p>
            <p className="mt-2 text-[13px] text-muted-cream">
              EcoMargins Consulting LLC · Operating as Daanaa · daanaa.org
            </p>
          </section>

          <p className="text-[12px] text-cool-grey pt-4 border-t border-light-grey">
            Last updated: June 2026
          </p>
        </div>
      </div>
    </div>
  )
}
