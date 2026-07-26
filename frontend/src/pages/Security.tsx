import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function Security() {
  usePageMeta(
    'Security Disclosure — Daanaa',
    'How to report a security vulnerability to Daanaa. Our responsible disclosure policy and safe harbor commitment for security researchers acting in good faith.'
  )

  return (
    <div className="min-h-[100dvh]">
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1120px] mx-auto px-6 md:px-12 pt-12 pb-10">
          <div className="flex items-center gap-2 mb-4">
            <Link to="/" className="font-body text-caption text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream">/</span>
            <span className="font-body text-caption text-muted-cream">Security</span>
          </div>
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]">
            Security Disclosure
          </h1>
          <p className="mt-3 font-body text-body-lg text-muted-cream max-w-[600px]">
            We take security seriously. If you find a vulnerability, please tell us privately so we can fix it before it affects anyone.
          </p>
        </div>
      </div>

      <div className="bg-warm-cream py-16 md:py-20">
        <div className="max-w-[800px] mx-auto px-6 md:px-12 space-y-12 font-body text-lead text-cool-grey leading-[1.7]">

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg md:text-headline mb-4">How to report a vulnerability</h2>
            <p>
              Email a description of the issue to{' '}
              <a href="mailto:security@daanaa.org" className="text-deep-navy underline hover:text-deep-navy/70 font-medium">security@daanaa.org</a>.
              Please include enough detail for us to reproduce and understand the scope — the URL or feature affected, the steps to reproduce, the potential impact, and any supporting material such as screenshots or proof of concept code.
            </p>
            <p className="mt-3">
              We aim to acknowledge every report within two business days and to provide a status update within seven days. We will let you know when the issue is resolved and, if you would like, we will credit you by name or handle in our disclosure.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg md:text-headline mb-4">Our commitment to you</h2>
            <p>If you report a vulnerability to us in good faith, we commit to:</p>
            <ul className="mt-4 space-y-3">
              {[
                'Respond to your report promptly and treat it seriously',
                'Not pursue legal action against you for research and disclosure conducted in good faith',
                'Work with you to understand and resolve the issue before any public disclosure',
                'Credit you for the discovery if you would like to be recognized',
                'Keep you informed as we investigate and fix the issue',
              ].map(item => (
                <li key={item} className="flex items-start gap-3">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" className="shrink-0 mt-1">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg md:text-headline mb-4">What we ask of researchers</h2>
            <p>To keep this safe for everyone, please:</p>
            <ul className="mt-4 space-y-3">
              {[
                'Do not access, modify, or delete data belonging to other users',
                'Do not disrupt or degrade the platform for other users',
                'Do not use the vulnerability beyond what is needed to demonstrate the issue',
                'Do not publicly disclose details before we have had a reasonable opportunity to fix it',
                'Do not conduct automated scans or denial of service tests against production',
              ].map(item => (
                <li key={item} className="flex items-start gap-3">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#D1D5DB" strokeWidth="2.5" className="shrink-0 mt-1">
                    <line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg md:text-headline mb-4">In scope</h2>
            <p>We are interested in reports related to daanaa.org and its API, including:</p>
            <ul className="mt-3 space-y-2 text-body-lg">
              {[
                'Authentication and session management issues',
                'Injection vulnerabilities (SQL, command, etc.)',
                'Cross site scripting and cross site request forgery',
                'Sensitive data exposure',
                'Access control failures that would allow one user to access another\'s data',
                'Security misconfigurations with real world impact',
              ].map(item => (
                <li key={item} className="flex items-start gap-2">
                  <span className="text-soft-gold mt-1">·</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg md:text-headline mb-4">Out of scope</h2>
            <ul className="mt-3 space-y-2 text-body-lg">
              {[
                'Issues that require physical access to a user\'s device',
                'Reports of missing security headers with no demonstrated impact',
                'Username or email enumeration with no evidence of practical exploit',
                'Issues in third party services we do not control',
                'Theoretical vulnerabilities with no realistic attack path',
              ].map(item => (
                <li key={item} className="flex items-start gap-2">
                  <span className="text-cool-grey/40 mt-1">·</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg md:text-headline mb-4">Safe harbor</h2>
            <p>
              Daanaa considers good faith security research conducted under this policy to be authorized conduct. We will not initiate legal action against researchers who discover and responsibly report security vulnerabilities in accordance with this policy. If legal action is initiated by a third party against a researcher who has followed this policy, we will make clear that the research was conducted with our knowledge and in good faith.
            </p>
            <p className="mt-3">
              This policy is not a blanket authorization to conduct any security testing. It applies only to research conducted within the scope described above, in good faith, and reported to us before public disclosure.
            </p>
          </section>

          <section>
            <h2 className="font-display italic text-deep-navy text-title-lg md:text-headline mb-4">Contact</h2>
            <p>
              <a href="mailto:security@daanaa.org" className="text-deep-navy underline hover:text-deep-navy/70 font-medium">security@daanaa.org</a>
            </p>
            <p className="mt-2">
              For data corrections, legal questions, or general feedback, see{' '}
              <Link to="/legal" className="text-deep-navy underline hover:text-deep-navy/70 font-medium">daanaa.org/legal</Link>.
            </p>
          </section>

          <p className="text-caption text-cool-grey pt-4 border-t border-light-grey">
            Last updated: June 30, 2026. Attorney review in progress.
          </p>

        </div>
      </div>
    </div>
  )
}
