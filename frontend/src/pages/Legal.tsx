import { Link } from 'react-router-dom'

export default function Legal() {
  return (
    <div className="min-h-[100dvh] bg-warm-cream">
      <div className="max-w-[800px] mx-auto px-6 lg:px-12 py-24">
        <Link to="/" className="font-body text-[12px] tracking-[0.02em] text-cool-grey hover:text-deep-navy transition-colors">
          ← Back to Home
        </Link>

        <h1 className="font-display italic text-deep-navy mt-6 leading-[0.95] tracking-[-0.02em]"
            style={{ fontSize: 'clamp(36px, 6vw, 64px)' }}>
          Legal & Data Attribution
        </h1>

        <div className="mt-12 space-y-12 font-body text-[15px] text-cool-grey leading-[1.7]">

          {/* Data Sources */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] mb-4">Data Sources</h2>
            <p>
              Daanaa aggregates publicly available data from the following sources. We do not collect,
              store, or distribute any information beyond what these sources make available to the public.
            </p>
            <ul className="mt-4 space-y-3 list-none">
              {[
                {
                  name: "IRS Business Master File (BMF)",
                  detail: "Published by the U.S. Internal Revenue Service. Contains basic registration data for all recognized tax exempt organizations. Public domain, no restrictions on use.",
                  url: "https://www.irs.gov/charities-non-profits/exempt-organizations-business-master-file-extract-eo-bmf",
                },
                {
                  name: "IRS Form 990 XML Filings",
                  detail: "Annual information returns filed by 501(c)(3) organizations with the IRS. Released as bulk XML under the Freedom of Information Act. Public domain.",
                  url: "https://www.irs.gov/charities-non-profits/form-990-series-downloads",
                },
                {
                  name: "IRS Automatic Revocation List",
                  detail: "The IRS publishes a list of organizations whose tax-exempt status was automatically revoked for failure to file for three or more consecutive years. Daanaa checks every indexed organization against this list monthly. Organizations with revoked status are flagged and removed from browse and search.",
                  url: "https://apps.irs.gov/pub/epostcard/data-download-revocation.zip",
                },
                {
                  name: "NCCS Core Data Files",
                  detail: "Structured extracts of 990 financial data compiled by the National Center for Charitable Statistics at the Urban Institute. Provided for nonprofit research and public benefit.",
                  url: "https://nccs-data.urban.org/",
                },
                {
                  name: "ProPublica Nonprofit Explorer",
                  detail: "Normalized 990 data and organization profiles compiled by ProPublica. Used under ProPublica's open data terms for nonprofit research.",
                  url: "https://projects.propublica.org/nonprofits/",
                },
              ].map(({ name, detail, url }) => (
                <li key={name} className="border border-light-grey rounded-lg p-5 bg-white">
                  <a href={url} target="_blank" rel="noopener noreferrer"
                     className="font-medium text-deep-navy hover:text-soft-gold transition-colors">
                    {name} →
                  </a>
                  <p className="mt-1 text-[13px]">{detail}</p>
                </li>
              ))}
            </ul>
          </section>

          {/* Data Accuracy */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] mb-4">Data Accuracy & Freshness</h2>
            <p>
              Financial figures shown on Daanaa are derived from IRS Form 990 filings. The most
              recent filing available for each organization may lag the current fiscal year by
              12–24 months. Revenue and asset figures represent the latest tax year on record.
            </p>
            <p className="mt-3">
              Each organization page displays a <strong className="text-deep-navy">data source</strong> and
              <strong className="text-deep-navy"> fiscal year</strong> badge indicating the vintage of the
              financial data shown. Daanaa refreshes data from ProPublica and IRS sources monthly, and supplements with NCCS extracts as they become available.
            </p>
            <p className="mt-3">
              Daanaa scores and peer group rankings are recalculated whenever the underlying data is updated. Rankings are relative. A score reflects an organization's position among its true peers — same operating model and similar revenue size — not an absolute quality rating.
            </p>
          </section>

          {/* AI-generated & automatically-collected content */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] mb-4">AI-Generated & Automatically-Collected Content</h2>
            <p>
              To make organizations easier to find, Daanaa fills gaps in the public record using
              automated tools. Two kinds of content are produced this way, and both are labeled in the
              interface so you always know what you are looking at.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">AI-generated text.</strong> Some mission summaries and
              search tags are written by an AI model from public IRS category and filing data, not by the
              organization. These carry a <strong className="text-deep-navy">beta</strong> label. They are
              a starting point, may be incomplete or inaccurate, and are not the organization's official
              statement of its mission.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">Automatically-collected links.</strong> Some website
              links are discovered by automated search of public web pages, not provided by the
              organization. These also carry a <strong className="text-deep-navy">beta</strong> label. We
              run basic checks that a link is live and appears to match the organization, but a beta label
              is not an endorsement. Confirm you are on the correct organization's official page.
              Daanaa never receives or processes any donation, and never collects donor payment information.
            </p>
            <p className="mt-3">
              An organization can claim its page to replace AI-generated text and automatically-collected
              links with its own verified information. Claimed content is labeled accordingly. If you find
              an error, contact us and we will correct or remove it.
            </p>
          </section>

          {/* Privacy */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] mb-4">Privacy Policy</h2>
            <p>
              Daanaa is a public directory of tax-exempt organizations. All organization data
              displayed on this platform originates from IRS public filings and is required to be
              publicly disclosed under 26 U.S.C. § 6104.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">We do not passively collect personal information from visitors.</strong> We
              do not use cookies for tracking, do not run behavioral analytics, and do not sell or
              share any user data with third parties.
            </p>
            <p className="mt-3">
              When you voluntarily submit information — such as an email address in the claim form, feedback form, or waitlist — we store that information to respond to your request. We do not use it for marketing, share it with third parties, or connect it to your browsing activity.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">When you claim your organization's page</strong>, we collect your
              name, title, email address, and phone number. We use them for one purpose: to verify by
              phone that you represent the organization before your page goes live. None of this
              information is ever shown publicly. We keep a record of your claim, the statements you
              agreed to, and our verification call for as long as your claim is active and for up to
              three years after it is closed, because claiming a page carries legal weight and both
              sides benefit from a clear record. To correct, update, or request deletion of your claim
              information, email{' '}
              <a href="mailto:privacy@daanaa.org" className="text-soft-gold hover:underline">privacy@daanaa.org</a>
              {' '}and we will respond within 30 days.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">The Giving Wallet requires a free account.</strong> To save
              organizations to your wallet, sign in with Google. Your wallet holds bookmarks and giving intent
              only — never transaction records. It is never shown publicly, never used for marketing or outreach,
              and can be deleted in full at any time. We do not track your browsing activity on the site.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">Partner inquiries</strong> sent through our partners page go to our
              inbox as email so we can reply. We do not add you to any list.
            </p>
            <p className="mt-3">
              If your organization's information on Daanaa is incorrect, you may request a correction
              by contacting us. In most cases, corrections require updating the underlying IRS 990
              filing, which is the authoritative source.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">California residents (CCPA).</strong> If you have
              submitted personal information to Daanaa — such as an email address through the claim
              form or feedback form — you have the right to know what information we hold, the right
              to request deletion, and the right to opt out of any sale of your personal information.
              We do not sell personal information. To exercise any of these rights, email{' '}
              <a href="mailto:privacy@daanaa.org" className="text-soft-gold hover:underline">privacy@daanaa.org</a>{' '}
              and we will respond within 45 days.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">EU and UK residents (GDPR / UK GDPR).</strong>{' '}
              Daanaa is a U.S.-directed service focused on U.S. nonprofit organizations. If you are
              located in the European Union or United Kingdom and have voluntarily submitted personal
              information to us, EcoMargins LLC is the data controller. You have the right to access,
              correct, erase, restrict processing of, and port your personal data, and to object to
              processing. We do not use your data for profiling or automated decision-making. Our
              lawful basis for processing claim and contact data is legitimate interest in verifying
              identity and responding to inquiries. To exercise any of these rights, email{' '}
              <a href="mailto:privacy@daanaa.org" className="text-soft-gold hover:underline">privacy@daanaa.org</a>.
              We aim to respond within 30 days. You also have the right to lodge a complaint with your
              local supervisory authority.
            </p>
          </section>

          {/* Terms of Use */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] mb-4">Terms of Use</h2>
            <p>
              Daanaa data is provided for informational and research purposes. You may use organization
              profiles, Daanaa scores, and ranking data freely for personal, academic, journalistic,
              or nonprofit research purposes with attribution to Daanaa (daanaa.org).
            </p>
            <p className="mt-3">
              Commercial redistribution of Daanaa data in bulk without written permission is not
              permitted. Automated scraping at a rate that degrades service for other users is
              prohibited.
            </p>
            <p className="mt-3">
              Daanaa makes no warranties about the completeness or accuracy of data and is not
              liable for decisions made based on information provided on this platform.
            </p>
          </section>

          {/* Contact */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] mb-4">Contact</h2>
            <p>
              Legal questions and takedown requests:{' '}
              <a href="mailto:legal@daanaa.org"
                 className="text-soft-gold hover:text-bright-gold transition-colors">
                legal@daanaa.org
              </a>. Data corrections:{' '}
              <a href="mailto:trust@daanaa.org"
                 className="text-soft-gold hover:text-bright-gold transition-colors">
                trust@daanaa.org
              </a>. Privacy and data requests:{' '}
              <a href="mailto:privacy@daanaa.org"
                 className="text-soft-gold hover:text-bright-gold transition-colors">
                privacy@daanaa.org
              </a>. Partnerships:{' '}
              <a href="mailto:partners@daanaa.org"
                 className="text-soft-gold hover:text-bright-gold transition-colors">
                partners@daanaa.org
              </a>.
            </p>
          </section>

          {/* Entity disclosure — required before public launch */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] mb-4">Who operates Daanaa</h2>
            <p>
              Daanaa is operated by <strong>EcoMargins Consulting LLC</strong>, a for-profit company. Daanaa is not a 501(c)(3) charity or a nonprofit organization. We are not affiliated with the IRS or any government agency.
            </p>
            <p className="mt-3">
              Daanaa does not receive, hold, solicit, or process charitable gifts. We are a public-data directory. All giving happens directly between donors and the nonprofits they choose. We never touch the money.
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
