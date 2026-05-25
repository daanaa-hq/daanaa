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
              financial data shown. Daanaa automatically refreshes data from ProPublica on a weekly
              schedule and supplements with NCCS extracts as they become available.
            </p>
            <p className="mt-3">
              Daanaa scores and percentile rankings are recalculated within NTEE peer groups whenever
              the underlying data is updated. Rankings are relative. A score reflects an
              organization's position among its registered peers, not an absolute quality rating.
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
              <strong className="text-deep-navy">We do not collect personal information from visitors.</strong> We
              do not use cookies for tracking, do not run behavioral analytics, and do not sell or
              share any user data with third parties.
            </p>
            <p className="mt-3">
              If your organization's information on Daanaa is incorrect, you may request a correction
              by contacting us. In most cases, corrections require updating the underlying IRS 990
              filing, which is the authoritative source.
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
              For data corrections, partnership inquiries, or legal questions, contact us at{' '}
              <a href="mailto:hello@daanaa.org"
                 className="text-soft-gold hover:text-bright-gold transition-colors">
                hello@daanaa.org
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

          <p className="text-[12px] text-cool-grey/60 pt-4 border-t border-light-grey">
            Last updated: May 2026
          </p>
        </div>
      </div>
    </div>
  )
}
