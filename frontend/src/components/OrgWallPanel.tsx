import { Link } from 'react-router-dom'
import SupportIntent from './SupportIntent'

interface OrgWallPanelProps {
  orgName: string
  ein: string
}

export default function OrgWallPanel({ orgName, ein }: OrgWallPanelProps) {

  return (
    <div
      className="rounded-2xl border overflow-hidden"
      style={{ background: '#FAFAF8', borderColor: '#E5E0DB' }}
    >
      {/* Section label */}
      <div className="px-5 py-4 border-b" style={{ borderColor: '#E5E0DB' }}>
        <span className="font-body text-micro tracking-[0.08em] text-cool-grey uppercase font-medium">
          Their Page
        </span>
      </div>

      {/* Unclaimed state + copy */}
      <div className="px-5 py-8 flex flex-col items-center text-center gap-4">
        <div
          className="w-14 h-14 rounded-full flex items-center justify-center"
          style={{ background: 'rgba(201,169,110,0.08)' }}
        >
          <svg
            width={26} height={26} viewBox="0 0 24 24" fill="none"
            stroke="rgba(201,169,110,0.65)" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"
            aria-hidden="true"
            style={{ display: 'block' }}
          >
            <path d="M3 21h18" />
            <path d="M5 21V7l7-4 7 4v14" />
            <path d="M9 9h.01M15 9h.01M9 13h.01M15 13h.01" />
          </svg>
        </div>

        <div>
          <p className="font-body text-body text-deep-navy font-medium leading-[1.5]">
            This corner belongs to {orgName}.
          </p>
          <p className="mt-1 font-body text-small text-cool-grey leading-[1.55]">
            They haven&rsquo;t claimed their page yet.
          </p>
        </div>

        <p className="font-body text-small text-cool-grey leading-[1.55]">
          Are you with this organization?{' '}
          <Link
            to={`/claim/verify?ein=${encodeURIComponent(ein)}`}
            className="text-link-gold hover:text-deep-gold transition-colors underline underline-offset-2"
          >
            Claim this page for free.
          </Link>
        </p>

        <div className="w-full pt-4 mt-1 border-t" style={{ borderColor: '#E5E0DB' }}>
          <SupportIntent orgName={orgName} ein={ein} />
        </div>
      </div>

      {/* Phase 2 teaser */}
      <div className="px-5 py-4 border-t" style={{ borderColor: '#E5E0DB' }}>
        <p className="font-body text-label text-cool-grey leading-[1.55] text-center">
          When they join: their updates, upcoming events, and what they need most right now.
        </p>
      </div>
    </div>
  )
}
