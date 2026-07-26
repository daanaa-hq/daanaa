import { Link } from 'react-router-dom'

export default function Legal() {

  return (
    <div className="min-h-[100dvh]">
      {/* Hero */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-12 pb-10">
          <div className="flex items-center gap-2 mb-4">
            <Link to="/" className="font-body text-caption text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-caption text-muted-cream">Legal & Data Attribution</span>
          </div>
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]">
            Legal & Data Attribution
          </h1>
        </div>
      </div>

      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[800px] mx-auto px-6 md:px-12">

        <div className="space-y-12 font-body text-lead text-cool-grey leading-[1.7]">

          {/* Data Sources */}
          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg md:text-headline mb-4">Data Sources</h2>
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
                  <p className="mt-1 text-small">{detail}</p>
                </li>
              ))}
            </ul>
          </section>

          {/* Data Accuracy */}
          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg md:text-headline mb-4">Data Accuracy & Freshness</h2>
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
              Daanaa peer financial context scores are recalculated whenever the underlying data is updated. Scores are relative. A score reflects an organization's reserve position among its true peers — same funding model and similar revenue size — not an absolute quality rating.
            </p>
          </section>

          {/* AI-generated & automatically-collected content */}
          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg md:text-headline mb-4">AI Assisted & Automatically-Collected Content</h2>
            <p>
              To make organizations easier to find, Daanaa fills gaps in the public record using
              automated tools. Two kinds of content are produced this way, and both are labeled in the
              interface so you always know what you are looking at.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">AI assisted text.</strong> Some mission summaries and
              search tags are written by an AI model from public IRS category and filing data, not by the
              organization. These carry an <strong className="text-deep-navy">AI assisted</strong> label. They are
              a starting point, may be incomplete or inaccurate, and are not the organization's official
              statement of its mission.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">Automatically-collected links.</strong> Some website
              links are found by automated search of public web pages, not provided by the
              organization. These carry a <strong className="text-deep-navy">discovered</strong> label. We
              run basic checks that a link is live and appears to match the organization, but a discovered label
              is not an endorsement. Confirm you are on the correct organization's official page.
              Daanaa never receives or processes any donation, and never collects donor payment information.
            </p>
            <p className="mt-3">
              An organization can claim its page to replace AI assisted text and automatically-collected
              links with its own verified information. Claimed content is labeled accordingly. If you find
              an error, contact us and we will correct or remove it.
            </p>
          </section>

          {/* Privacy */}
          <section id="privacy">
            <h2 className="font-display italic text-deep-navy text-title-lg md:text-headline mb-4">Privacy Policy</h2>
            <p className="mb-4 p-4 bg-white border border-light-grey rounded-lg text-body">
              This is a summary. The full privacy policy — including the data retention schedule and your state privacy rights — is at{' '}
              <Link to="/privacy" className="text-soft-gold hover:text-bright-gold font-medium">daanaa.org/privacy</Link>.
            </p>
            <p>
              Daanaa is a public directory of tax-exempt organizations. All organization data
              displayed on this platform originates from IRS public filings and is required to be
              publicly disclosed under 26 U.S.C. § 6104.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">We do not use tracking cookies or build advertising profiles.</strong> We
              do not sell or share user data with third parties. We use <strong className="text-deep-navy">Plausible Analytics</strong> — a cookieless, privacy-respecting service — to collect anonymous page-view counts. Plausible does not identify individual visitors, does not use cookies, and does not track you across sites. No personal data is collected by analytics.
            </p>
            <p className="mt-3">
              When you voluntarily submit information — such as an email address in the claim form, feedback form, or waitlist — we store that information to respond to your request. We do not use it for marketing, share it with third parties, or connect it to your browsing activity.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">When you register for an event</strong> through a nonprofit's event page, your name and email are shared with the organizing nonprofit and stored by Daanaa to manage your reservation and process cancellations. We do not use this information for marketing. You can cancel at any time using the link in your confirmation email, and your information will be removed within 30 days of cancellation or event completion.
            </p>
            <p className="mt-3">
              <strong className="text-deep-navy">When you log an impact record</strong> (such as volunteer hours or a donation note) through an organization's page, that record is stored in your device wallet and — if synced — associated with your account. Impact records are personal notes for your own reference; they are never shared publicly or with the nonprofit without your explicit action.
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
              <strong className="text-deep-navy">The Giving Wallet requires no account.</strong> Wallet data
              is stored on your device by default. You may optionally sign in with Google to enable cross-device
              sync. Your wallet holds bookmarks and giving intent only — never transaction records, event registrations,
              or impact reports. It is never shown publicly, never used for marketing or outreach, and can be deleted in
              full at any time. We do not track your browsing activity on the site.
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
              information to us, EcoMargins Consulting LLC is the data controller. You have the right to access,
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
            <h2 className="font-display italic text-deep-navy text-title-lg md:text-headline mb-4">Terms of Use</h2>

            <p className="font-semibold text-deep-navy">Informational use only</p>
            <p className="mt-2">
              Everything on Daanaa is provided for informational and research purposes only. Nothing
              on this platform constitutes legal, financial, investment, tax, or charitable advice.
              Daanaa does not endorse, recommend, certify, or verify any nonprofit organization.
              Using this platform does not create any fiduciary, advisory, or professional relationship
              between you and Daanaa or EcoMargins Consulting LLC.
            </p>

            <p className="mt-5 font-semibold text-deep-navy">No warranties</p>
            <p className="mt-2">
              All data is drawn from IRS and third-party public records and is provided as-is. Daanaa
              makes no warranties, express or implied, about the accuracy, completeness, timeliness,
              or fitness for any particular purpose of information on this platform. Public records may
              be delayed, incomplete, or contain errors. Independently verify any organization before
              donating, volunteering, or making decisions based on information found here.
            </p>

            <p className="mt-5 font-semibold text-deep-navy">AI assisted content</p>
            <p className="mt-2">
              Some mission summaries, category tags, and descriptions are generated by automated
              tools from public IRS records. They may be inaccurate or incomplete and are not the
              organization's official statement. See the AI Assisted &amp; Automatically-Collected
              Content section above for details. Daanaa is not liable for errors in AI assisted content.
            </p>

            <p className="mt-5 font-semibold text-deep-navy">External links</p>
            <p className="mt-2">
              Daanaa may display links to nonprofit websites and donation pages discovered from public
              sources. These links point to third-party sites that Daanaa does not own, operate, or
              control. Daanaa does not guarantee the accuracy, safety, or legitimacy of any external
              site. Always confirm you are on the correct organization's official website before
              donating. Daanaa never receives, processes, or holds any donation funds.
            </p>

            <p className="mt-5 font-semibold text-deep-navy">Permitted use</p>
            <p className="mt-2">
              You may use organization profiles and peer financial context data freely for personal,
              academic, journalistic, or nonprofit research purposes with attribution to Daanaa
              (daanaa.org). Commercial redistribution of Daanaa data in bulk without written
              permission is not permitted. Automated access at a rate that degrades service for
              other users is prohibited.
            </p>

            <p className="mt-5 font-semibold text-deep-navy">Intellectual property</p>
            <p className="mt-2">
              The Daanaa name, logo, platform design, scoring methodology, and original written
              content are owned by EcoMargins Consulting LLC. Organization names, tax filings, and
              financial data are public records and remain in the public domain. AI assisted summaries
              generated by Daanaa are the property of EcoMargins Consulting LLC.
            </p>

            <p className="mt-5 font-semibold text-deep-navy">Copyright and DMCA takedown procedure</p>
            <p className="mt-2">
              Daanaa responds to valid copyright infringement notices under the Digital Millennium Copyright Act (17 U.S.C. § 512). Our designated copyright agent is registered with the U.S. Copyright Office.
            </p>
            <p className="mt-3 font-medium text-deep-navy">To submit a takedown notice, send the following to <a href="mailto:legal@daanaa.org" className="text-soft-gold hover:underline">legal@daanaa.org</a>:</p>
            <ul className="mt-2 space-y-1.5 list-none text-body-lg">
              {[
                'Your physical or electronic signature',
                'Identification of the copyrighted work you believe has been infringed',
                'The URL or specific location on Daanaa where the allegedly infringing material appears',
                'Your name, address, telephone number, and email address',
                'A statement that you have a good faith belief that the use is not authorized by the copyright owner, its agent, or the law',
                'A statement, made under penalty of perjury, that the information in your notice is accurate and that you are the copyright owner or authorized to act on their behalf',
              ].map(item => (
                <li key={item} className="flex items-start gap-2">
                  <span className="shrink-0 text-soft-gold mt-1">·</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            <p className="mt-4 font-medium text-deep-navy">Counter-notification</p>
            <p className="mt-2">
              If you believe your content was removed by mistake or misidentification, you may submit a counter-notification to <a href="mailto:legal@daanaa.org" className="text-soft-gold hover:underline">legal@daanaa.org</a> including: your physical or electronic signature; identification of the removed material and where it appeared; a statement under penalty of perjury that the removal was a mistake or misidentification; your name, address, phone number, email; and consent to jurisdiction in Travis County, Texas. We will forward your counter-notification to the original complainant. If they do not file a court action within 10 to 14 business days, we may restore the material.
            </p>
            <p className="mt-4 font-medium text-deep-navy">Repeat infringers</p>
            <p className="mt-2">
              Daanaa will terminate access for users or organizations who are found to be repeat copyright infringers, consistent with our obligations under 17 U.S.C. § 512(i).
            </p>

            <p className="mt-5 font-semibold text-deep-navy">Limitation of liability</p>
            <p className="mt-2">
              To the maximum extent permitted by law, Daanaa and EcoMargins Consulting LLC are not
              liable for any direct, indirect, incidental, consequential, or punitive damages arising
              from your use of this platform or reliance on information provided here. Our total
              liability for any claim arising out of your use of Daanaa will not exceed one hundred
              US dollars ($100).
            </p>

            <p className="mt-5 font-semibold text-deep-navy">Governing law</p>
            <p className="mt-2">
              These terms are governed by the laws of the State of Texas, without regard to conflict
              of law principles. Any dispute arising from your use of this platform will be resolved
              exclusively in the state or federal courts located in Travis County, Texas, and you
              consent to personal jurisdiction there.
            </p>

            <p className="mt-5 font-semibold text-deep-navy">Changes to these terms</p>
            <p className="mt-2">
              We may update these terms at any time. Continued use of the platform after changes
              are posted constitutes your acceptance of the revised terms. The date at the bottom
              of this page reflects when terms were last updated.
            </p>
          </section>

          {/* Contact */}
          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg md:text-headline mb-4">Contact</h2>
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
            <h2 className="font-display italic text-deep-navy text-title-lg md:text-headline mb-4">Who operates Daanaa</h2>
            <p>
              Daanaa is operated by <strong>EcoMargins Consulting LLC</strong>, a for-profit Texas limited liability company doing business as Daanaa. Daanaa is not a 501(c)(3) charity or a nonprofit organization. We are not affiliated with the IRS or any government agency.
            </p>
            <p className="mt-3">
              Daanaa does not receive, hold, solicit, or process charitable gifts. We are a public-data directory. All giving happens directly between donors and the nonprofits they choose. We never touch the money.
            </p>
          </section>

          <p className="text-caption text-cool-grey pt-4 border-t border-light-grey">
            Last updated: June 30, 2026. Attorney review in progress.
          </p>
        </div>
        </div>
      </div>
    </div>
  )
}
