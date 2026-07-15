import React from 'react'

export function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto prose prose-slate dark:prose-invert">
        <h1>Privacy Policy</h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">Last updated: July 15, 2026</p>

        <h2>Our Commitment to Privacy</h2>
        <p>
          Daanaa is built on trust. We collect minimal data, we never track giving activity, and we don't sell or share
          personal information with third parties. This privacy policy explains how we handle the data you share with us.
        </p>

        <h2>What We Collect</h2>
        <p>
          When you use Daanaa, we collect only what's necessary to help you discover nonprofits and understand financial context:
        </p>
        <ul>
          <li><strong>Browsing data</strong>: Which organizations you view, search queries (via anonymous analytics only)</li>
          <li><strong>Giving Wallet data</strong>: Your bookmarked organizations and giving intent (stored on your device by default)</li>
          <li><strong>Optional account data</strong>: If you create an account, we store your email and wallet preferences for cross-device sync</li>
          <li><strong>Nonprofit claims data</strong>: If you represent a nonprofit, we collect your organization EIN, email, and any corrections you submit</li>
        </ul>

        <h2>What We Don't Collect</h2>
        <ul>
          <li>Your giving history or donation amounts</li>
          <li>Your identity or personal information beyond what you voluntarily provide</li>
          <li>Cookies that track you across the web</li>
          <li>Location data or IP addresses</li>
          <li>Payment information (we never process donations)</li>
          <li>Third-party tracking pixels or advertising data</li>
        </ul>

        <h2>How We Use Your Data</h2>
        <p>We use data only for:</p>
        <ul>
          <li><strong>Search and discovery</strong>: Help you find nonprofits by name, location, or cause</li>
          <li><strong>Giving Wallet</strong>: Store your bookmarks and giving intent (so you remember what matters to you)</li>
          <li><strong>Analytics</strong>: Understand which causes interest our users (aggregated, anonymized only)</li>
          <li><strong>Nonprofit claims</strong>: Process corrections nonprofits submit about their own data</li>
          <li><strong>Service improvement</strong>: Fix bugs and make Daanaa better</li>
        </ul>

        <p>We never use your data for marketing, targeting, or any purpose beyond what's listed above.</p>

        <h2>Your Rights</h2>
        <ul>
          <li><strong>Access</strong>: You can request a copy of the data we hold about you</li>
          <li><strong>Delete</strong>: You can delete your Giving Wallet at any time (one click)</li>
          <li><strong>Opt-out</strong>: You can disable analytics in your browser settings</li>
          <li><strong>Portability</strong>: You can export your Giving Wallet data</li>
        </ul>

        <p>To exercise any of these rights, email <a href="mailto:hello@daanaa.org">hello@daanaa.org</a>.</p>

        <h2>Data Security</h2>
        <p>
          Your data is encrypted in transit (HTTPS). Wallet data is stored on your device by default. If you sign in,
          we store encrypted backups on our server. We don't sell data, and we don't share it with vendors except where
          necessary to operate the service (and only under strict contracts).
        </p>

        <h2>Analytics</h2>
        <p>
          We use Plausible Analytics, a privacy-respecting analytics service that doesn't use cookies and doesn't
          build tracking profiles. We can see that users visited a page, but we can't see who they are or track them
          across the web.
        </p>

        <h2>Nonprofit Claims</h2>
        <p>
          If you represent a nonprofit and submit a claim to correct your organization's data:
        </p>
        <ul>
          <li>We verify your email matches your organization's domain</li>
          <li>We store your claim with an audit trail</li>
          <li>We don't share your email publicly</li>
          <li>You can request deletion of your claim at any time</li>
        </ul>

        <h2>Third-Party Links</h2>
        <p>
          Daanaa includes links to nonprofit websites and donation pages. We don't control those sites, and they have
          their own privacy policies. We're not responsible for their data practices.
        </p>

        <h2>Children's Privacy</h2>
        <p>
          Daanaa is not intended for children under 13. We don't knowingly collect data from children. If we learn
          we've done so, we'll delete it immediately.
        </p>

        <h2>Changes to This Policy</h2>
        <p>
          We may update this privacy policy if our practices change. We'll notify you of material changes via email
          if you've created an account, or by updating the "last updated" date if you haven't.
        </p>

        <h2>Questions?</h2>
        <p>
          If you have questions about this privacy policy or how we handle your data, email
          <a href="mailto:hello@daanaa.org"> hello@daanaa.org</a>.
        </p>

        <hr className="my-8" />

        <p className="text-sm text-gray-600 dark:text-gray-400">
          <strong>Our Founding Promise:</strong> Daanaa is built on Stewardship principles that prioritize donor
          privacy, nonprofit fairness, and trust. Read our full <a href="/charter">Stewardship Charter</a> to
          understand our commitments.
        </p>
      </div>
    </div>
  )
}
