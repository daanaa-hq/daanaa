import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

const EFFECTIVE_DATE = 'June 30, 2026'

export default function Privacy() {
  usePageMeta(
    'Privacy Policy — Daanaa',
    'How Daanaa collects, uses, stores, and protects information. Includes data retention schedule and user rights under CCPA and other state privacy laws.'
  )

  return (
    <div className="min-h-[100dvh]">
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-12 pb-10">
          <div className="flex items-center gap-2 mb-4">
            <Link to="/" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <Link to="/legal" className="font-body text-[12px] text-muted-cream hover:text-warm-cream transition-colors">Legal</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-[12px] text-muted-cream">Privacy Policy</span>
          </div>
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]"
              style={{ fontSize: 'clamp(36px, 5vw, 56px)' }}>
            Privacy Policy
          </h1>
          <p className="mt-3 font-body text-[14px] text-muted-cream">
            Effective {EFFECTIVE_DATE}. Attorney review in progress.
          </p>
        </div>
      </div>

      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[800px] mx-auto px-6 md:px-12 space-y-14 font-body text-[16px] text-cool-grey leading-[1.7]">

          {/* Top-level notice */}
          <div className="p-5 bg-deep-navy/5 border border-deep-navy/10 rounded-xl">
            <p className="font-body text-[15px] font-semibold text-deep-navy">
              We do not sell your personal information. We do not share it for advertising. We do not use it to train AI models.
            </p>
          </div>

          {/* 1. Who we are */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] md:text-[28px] mb-4">Who we are</h2>
            <p>
              Daanaa (daanaa.org) is a public directory of nonprofit organizations operated by <strong className="text-deep-navy">EcoMargins Consulting LLC</strong>, a Texas limited liability company doing business as Daanaa. Daanaa is not a nonprofit organization. We are not affiliated with the IRS, the federal government, or any nonprofit rating agency.
            </p>
            <p className="mt-3">
              We built Daanaa to help people discover organizations they care about using public information. Privacy is a design principle here, not an afterthought. We collect as little as possible, we do not track you across the web, and we do not sell your personal information.
            </p>
            <p className="mt-3">
              Questions about this policy:{' '}
              <a href="mailto:privacy@daanaa.org" className="text-deep-navy underline hover:text-deep-navy/70 font-medium">privacy@daanaa.org</a>
            </p>
          </section>

          {/* 2. What we collect */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] md:text-[28px] mb-4">What we collect — and what we don't</h2>
            <p>We collect different information depending on how you interact with Daanaa.</p>

            <div className="mt-6 space-y-6">

              <div className="bg-white border border-light-grey rounded-xl p-6">
                <h3 className="font-display text-deep-navy text-[17px] mb-2">Browsing the directory</h3>
                <p className="text-[14px]">
                  No account is required to browse, search, or view any organization page. We do not use cookies for tracking. We use <strong className="text-deep-navy">Plausible Analytics</strong> — a privacy-first analytics tool — to count page views and understand which features are used. Plausible does not use cookies, does not collect any personal information, does not track you across other websites, and does not build advertising profiles. The aggregate data Plausible collects (page views, country, device type, referrer) is never shared with or sold to any third party. You can learn more at <a href="https://plausible.io/privacy" target="_blank" rel="noopener noreferrer" className="text-deep-navy underline hover:text-deep-navy/70">plausible.io/privacy</a>.
                </p>
              </div>

              <div className="bg-white border border-light-grey rounded-xl p-6">
                <h3 className="font-display text-deep-navy text-[17px] mb-2">The Giving Wallet</h3>
                <p className="text-[14px]">
                  The Giving Wallet stores organizations you've bookmarked and giving intent you've logged. <strong className="text-deep-navy">No account is required.</strong> By default, wallet data is stored locally on your device using your browser's localStorage. It does not leave your device, and we cannot access it.
                </p>
                <p className="mt-3 text-[14px]">
                  You may optionally sign in with Google to enable sync across your devices. Signing in is not required to use the wallet. When you sign in, Google shares your name and email address with us solely to identify your account for sync purposes. Your wallet data (bookmarks and giving intent only — never transaction records) is synced to our servers and is never shown publicly, never used for marketing or outreach, and can be deleted in full at any time from your account settings.
                </p>
              </div>

              <div className="bg-white border border-light-grey rounded-xl p-6">
                <h3 className="font-display text-deep-navy text-[17px] mb-2">Feedback and contact forms</h3>
                <p className="text-[14px]">
                  When you submit a feedback form or contact us by email, we receive your email address and the content of your message. We use this only to respond to your request. We do not add you to a mailing list, and we do not share your contact information with third parties.
                </p>
              </div>

              <div className="bg-white border border-light-grey rounded-xl p-6">
                <h3 className="font-display text-deep-navy text-[17px] mb-2">Claiming an organization page</h3>
                <p className="text-[14px]">
                  When you claim your organization's page, we collect your name, title, email address, and phone number. We use these to verify by phone that you represent the organization. None of this information is shown publicly. We keep a record of your claim, the attestations you agreed to, and our verification for as long as the claim is active and for up to <strong className="text-deep-navy">three years after it is closed</strong>, because a claim carries legal weight and both parties benefit from a documented record.
                </p>
              </div>

              <div className="bg-white border border-light-grey rounded-xl p-6">
                <h3 className="font-display text-deep-navy text-[17px] mb-2">Volunteer submissions</h3>
                <p className="text-[14px]">
                  When you submit a volunteer opportunity through Daanaa, we collect the contact information you provide (name, email, organization). This is used to route the submission to the relevant organization and to confirm receipt. We retain volunteer submission records for up to <strong className="text-deep-navy">one year</strong> after a match is completed or the opportunity closes.
                </p>
              </div>

              <div className="bg-white border border-light-grey rounded-xl p-6">
                <h3 className="font-display text-deep-navy text-[17px] mb-2">Nonprofit accounts and partner inquiries</h3>
                <p className="text-[14px]">
                  Nonprofits who create an account to manage their page sign in via Google. We receive your name and email from Google for account identification only. Partner and network inquiries submitted through our site go to our inbox so we can respond — we do not add you to any list.
                </p>
              </div>

              <div className="bg-white border border-light-grey rounded-xl p-6">
                <h3 className="font-display text-deep-navy text-[17px] mb-2">What we never collect</h3>
                <ul className="text-[14px] space-y-1.5 mt-1">
                  {[
                    'Donation or payment information of any kind',
                    'Your giving history (that stays on your device)',
                    'Browsing behavior tracked across websites or advertising identifiers',
                    'Location data beyond the country level (from Plausible aggregate analytics)',
                    'Data from children under 13 (see Children\'s Privacy below)',
                  ].map(item => (
                    <li key={item} className="flex items-start gap-2">
                      <span className="text-cool-grey/50 mt-1">—</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

            </div>
          </section>

          {/* 3. How we use information */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] md:text-[28px] mb-4">How we use information</h2>
            <p>We use the information we collect only for the purposes it was collected for:</p>
            <ul className="mt-4 space-y-2">
              {[
                'To respond to feedback, questions, and data correction requests',
                'To verify organization claims before a page goes live',
                'To enable wallet sync across devices for users who choose to sign in with Google',
                'To understand aggregate usage patterns so we can improve the platform (via Plausible)',
                'To maintain accurate records of claims and attestations for dispute resolution',
                'To route volunteer submissions to the relevant organizations',
              ].map(item => (
                <li key={item} className="flex items-start gap-3">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" className="shrink-0 mt-1">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            <p className="mt-4">
              We do not use personal information for marketing, do not create behavioral profiles, and do not use it to train AI models. AI mission generation runs locally on our own servers using publicly available IRS filing data — personal data you submit to Daanaa is never used as AI training input.
            </p>
          </section>

          {/* 4. Data retention */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] md:text-[28px] mb-4">Data retention</h2>
            <p>We retain information only as long as needed for the purpose it was collected. Below is the schedule for each category:</p>
            <div className="mt-6 overflow-x-auto">
              <table className="w-full text-[14px] border-collapse">
                <thead>
                  <tr className="border-b-2 border-deep-navy/20">
                    <th className="text-left py-3 pr-6 font-semibold text-deep-navy">Data type</th>
                    <th className="text-left py-3 pr-6 font-semibold text-deep-navy">Retention period</th>
                    <th className="text-left py-3 font-semibold text-deep-navy">Basis</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-light-grey">
                  {[
                    ['Feedback and contact messages', '2 years from receipt', 'Respond to requests, resolve disputes'],
                    ['Claim records (active)', 'Duration of claim', 'Operational necessity'],
                    ['Claim records (closed)', '3 years after closure', 'Legal documentation of attestation'],
                    ['Google sign in (wallet sync)', 'Until account deleted or access revoked', 'Account sync functionality'],
                    ['Giving Wallet (on your device)', 'Indefinitely, under your control', 'Stored only on your device; we have no copy'],
                    ['Volunteer submissions', '1 year after match completes or opportunity closes', 'Coordination and confirmation'],
                    ['Waitlist email addresses', 'Until feature launches or you unsubscribe', 'Feature notification'],
                    ['Plausible analytics', '12 months rolling (aggregate only)', 'Usage analysis; no personal data retained'],
                    ['Nonprofit account (Google)', 'Until account deleted', 'Account management'],
                  ].map(([type, period, basis]) => (
                    <tr key={type}>
                      <td className="py-3 pr-6 font-medium text-deep-navy align-top">{type}</td>
                      <td className="py-3 pr-6 text-cool-grey align-top">{period}</td>
                      <td className="py-3 text-cool-grey align-top">{basis}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-4 text-[14px]">
              To request early deletion of any information we hold about you, email{' '}
              <a href="mailto:privacy@daanaa.org" className="text-deep-navy underline hover:text-deep-navy/70 font-medium">privacy@daanaa.org</a>.
              We will respond within 30 days.
            </p>
          </section>

          {/* 5. Third parties */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] md:text-[28px] mb-4">Third parties and data sharing</h2>
            <p>We do not sell personal information. We share information only in the following limited circumstances:</p>
            <div className="mt-4 space-y-4">
              <div>
                <p className="font-semibold text-deep-navy">Google (optional wallet sync)</p>
                <p className="mt-1">If you sign in with Google, Google's OAuth service authenticates your identity and shares your name and email with us. Google's privacy policy governs what Google collects during that process.</p>
              </div>
              <div>
                <p className="font-semibold text-deep-navy">Plausible Analytics</p>
                <p className="mt-1">We use Plausible to count page views and understand feature usage. Plausible does not receive any personal information and does not use cookies. See <a href="https://plausible.io/data-policy" target="_blank" rel="noopener noreferrer" className="text-deep-navy underline hover:text-deep-navy/70">plausible.io/data-policy</a>.</p>
              </div>
              <div>
                <p className="font-semibold text-deep-navy">Legal requirements</p>
                <p className="mt-1">We may disclose information if required by a valid court order, subpoena, or other legal process, or to protect the safety of our users or the public. We will notify you of any such request if legally permitted to do so.</p>
              </div>
              <div>
                <p className="font-semibold text-deep-navy">Business transfer</p>
                <p className="mt-1">If Daanaa is acquired, merged, or its assets transferred, user data may be transferred as part of that transaction. We would notify users beforehand and require the successor to honor the commitments in this policy.</p>
              </div>
            </div>
          </section>

          {/* 6. Cookies */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] md:text-[28px] mb-4">Cookies</h2>
            <p>
              Daanaa does not use advertising cookies or behavioral tracking cookies. We do not build profiles of your browsing behavior. The only cookies or browser storage we use are:
            </p>
            <ul className="mt-4 space-y-3">
              {[
                { type: 'localStorage (Giving Wallet)', purpose: 'Stores your wallet data locally on your device. Never transmitted to us unless you opt in to Google sync.', required: true },
                { type: 'Session authentication cookie', purpose: 'Set when you sign in with Google to keep you logged in during your session. Expires when you sign out or your session ends.', required: true },
              ].map(c => (
                <li key={c.type} className="flex gap-4 p-4 bg-white border border-light-grey rounded-lg text-[14px]">
                  <div>
                    <p className="font-semibold text-deep-navy">{c.type}</p>
                    <p className="mt-1">{c.purpose}</p>
                  </div>
                </li>
              ))}
            </ul>
            <p className="mt-4">
              No cookie consent banner is shown because we do not place tracking or advertising cookies. If this changes, we will update this policy and add a consent mechanism.
            </p>
          </section>

          {/* 7. Children */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] md:text-[28px] mb-4">Children's privacy</h2>
            <p>
              Daanaa is not directed at children under 13. We do not knowingly collect personal information from anyone under 13 years old. If we become aware that a child under 13 has submitted personal information to us, we will delete it promptly. If you believe a child under 13 has provided us with personal information, please contact{' '}
              <a href="mailto:privacy@daanaa.org" className="text-deep-navy underline hover:text-deep-navy/70 font-medium">privacy@daanaa.org</a>.
            </p>
          </section>

          {/* 8. State rights */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] md:text-[28px] mb-4">Your privacy rights</h2>
            <p>
              Depending on where you live, you may have rights over your personal information. We honor these rights regardless of which state law applies:
            </p>

            <div className="mt-6 space-y-6">
              <div>
                <p className="font-semibold text-deep-navy">Right to know</p>
                <p className="mt-1">You may request a description of the personal information we hold about you, including the categories, sources, and purposes for which it is used.</p>
              </div>
              <div>
                <p className="font-semibold text-deep-navy">Right to delete</p>
                <p className="mt-1">You may request deletion of personal information we hold about you, subject to exceptions required by law (such as retaining claim records for dispute resolution).</p>
              </div>
              <div>
                <p className="font-semibold text-deep-navy">Right to correct</p>
                <p className="mt-1">You may request correction of inaccurate personal information we hold about you.</p>
              </div>
              <div>
                <p className="font-semibold text-deep-navy">Right to opt out of sale or sharing</p>
                <p className="mt-1">We do not sell personal information and we do not share it for behavioral advertising. There is nothing to opt out of, but you have this right and we will honor it.</p>
              </div>
              <div>
                <p className="font-semibold text-deep-navy">Right to equal treatment</p>
                <p className="mt-1">Exercising any of these rights will not result in different service, different pricing, or any other negative treatment.</p>
              </div>
            </div>

            <div className="mt-6 space-y-4 p-5 bg-white border border-light-grey rounded-xl text-[14px]">
              <p><strong className="text-deep-navy">California (CCPA / CPRA).</strong> California residents may exercise the rights above. We respond within 45 days of a verifiable request. We do not sell or share personal information as those terms are defined under California law.</p>
              <p><strong className="text-deep-navy">Virginia (VCDPA), Colorado (CPA), Connecticut (CTDPA).</strong> Residents of these states have the rights described above. We respond within 45 days. You may appeal a denial by emailing <a href="mailto:privacy@daanaa.org" className="text-deep-navy underline hover:text-deep-navy/70">privacy@daanaa.org</a> with "Privacy Appeal" in the subject line.</p>
              <p><strong className="text-deep-navy">Texas (TDPSA).</strong> Texas residents have the rights described above. We respond within 60 days. You may appeal a denial by emailing <a href="mailto:privacy@daanaa.org" className="text-deep-navy underline hover:text-deep-navy/70">privacy@daanaa.org</a> with "Privacy Appeal" in the subject line.</p>
              <p><strong className="text-deep-navy">EU and UK (GDPR / UK GDPR).</strong> Daanaa is a U.S.-directed service focused on U.S. nonprofit data. EcoMargins Consulting LLC is the data controller for any personal data submitted to us by EU or UK residents. Our lawful basis for processing varies by activity: for claim data, our basis is Article 6(1)(b) — processing necessary to take steps at the data subject's request prior to entering into an agreement; for contact and inquiry data, our basis is Article 6(1)(f) — legitimate interest in responding to requests. We do not use your data for profiling or automated decision-making. You have the rights to access, correct, erase, restrict, and port your data, and to object to processing. We respond within 30 days. You may also lodge a complaint with your local supervisory authority.</p>
            </div>

            <p className="mt-4">
              To exercise any of these rights, email{' '}
              <a href="mailto:privacy@daanaa.org" className="text-deep-navy underline hover:text-deep-navy/70 font-medium">privacy@daanaa.org</a>{' '}
              with your name, the right you wish to exercise, and enough information for us to locate your data. We may ask you to verify your identity before fulfilling the request.
            </p>
          </section>

          {/* 9. Security */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] md:text-[28px] mb-4">Security</h2>
            <p>
              We use HTTPS for all data in transit and store personal data on servers protected by access controls and passwords, with access limited to authorized personnel. We maintain a responsible disclosure policy for security researchers at{' '}
              <Link to="/security" className="text-deep-navy underline hover:text-deep-navy/70 font-medium">daanaa.org/security</Link>.
            </p>
            <p className="mt-3">
              No method of transmission or storage is 100% secure. If we become aware of a breach affecting your personal information, we will notify you as required by applicable law.
            </p>
          </section>

          {/* 10. Changes */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] md:text-[28px] mb-4">Changes to this policy</h2>
            <p>
              We may update this policy as the platform evolves or as laws change. When we make material changes, we will update the effective date at the top of this page. We will notify users who have provided an email address of any change that materially affects how we handle their personal information.
            </p>
          </section>

          {/* Contact */}
          <section>
            <h2 className="font-display italic text-deep-navy text-[24px] md:text-[28px] mb-4">Contact</h2>
            <p>
              Privacy requests and questions:{' '}
              <a href="mailto:privacy@daanaa.org" className="text-deep-navy underline hover:text-deep-navy/70 font-medium">privacy@daanaa.org</a>
            </p>
            <p className="mt-2">
              EcoMargins Consulting LLC d/b/a Daanaa<br />
              Austin, Texas, United States
            </p>
          </section>

          <div className="pt-6 border-t border-light-grey flex flex-wrap gap-6">
            <Link to="/legal" className="font-body text-[13px] text-deep-navy/70 hover:text-deep-navy">Terms of Use →</Link>
            <Link to="/legal#data-sources" className="font-body text-[13px] text-deep-navy/70 hover:text-deep-navy">Data Sources →</Link>
            <Link to="/about" className="font-body text-[13px] text-deep-navy/70 hover:text-deep-navy">About Daanaa →</Link>
            <Link to="/feedback" className="font-body text-[13px] text-deep-navy/70 hover:text-deep-navy">Contact →</Link>
          </div>

          <p className="text-[12px] text-cool-grey pt-2 border-t border-light-grey">
            Effective {EFFECTIVE_DATE}. Attorney review in progress. This policy covers daanaa.org and services operated by EcoMargins Consulting LLC d/b/a Daanaa.
          </p>

        </div>
      </div>
    </div>
  )
}
