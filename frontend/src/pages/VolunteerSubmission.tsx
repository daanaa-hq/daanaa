import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'

export default function VolunteerSubmission() {
  usePageMeta('Log Volunteer Hours | Daanaa', 'Volunteer hour logging is coming soon to Daanaa.')

  return (
    <div className="min-h-screen bg-warm-cream flex items-center justify-center px-4 py-16">
      <div className="max-w-md w-full text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-soft-gold/15 mb-6">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#B8902F" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>
        <h1 className="font-display italic text-deep-navy text-[28px] mb-3">
          Volunteer hour logging is coming soon
        </h1>
        <p className="font-body text-[16px] text-cool-grey leading-[1.7] mb-6">
          This feature requires a verified nonprofit account, which we are still building.
          Once live, nonprofit staff will be able to review and approve volunteer hours
          submitted through their organization page.
        </p>
        <p className="font-body text-[14px] text-cool-grey mb-8">
          No information submitted here would be processed. Please do not enter personal data.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            to="/volunteer"
            className="inline-flex items-center justify-center px-6 py-2.5 rounded-full bg-deep-navy text-warm-cream font-body text-[14px] font-semibold hover:bg-navy-mid transition-colors"
          >
            Browse volunteer opportunities
          </Link>
          <Link
            to="/"
            className="inline-flex items-center justify-center px-6 py-2.5 rounded-full border border-soft-gold/40 text-soft-gold font-body text-[14px] font-semibold hover:bg-soft-gold/10 transition-colors"
          >
            Back to home
          </Link>
        </div>
      </div>
    </div>
  )
}
