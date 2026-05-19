const LAMP_PATH = [
  'M 12,1.5',
  'C 12.4,1.6 13.8,7.2 13.9,7.4',
  'C 14.6,8.0 19.8,11.5 20,12',
  'C 19.8,12.5 14.6,16.0 13.9,16.6',
  'C 13.7,16.8 12.6,20.5 12,22.5',
  'C 11.4,20.5 10.3,16.8 10.1,16.6',
  'C 9.4,16.0 4.2,12.5 4,12',
  'C 4.2,11.5 9.4,8.0 10.1,7.4',
  'C 10.2,7.2 11.6,1.6 12,1.5',
  'Z',
].join(' ')

interface OrgWallPanelProps {
  orgName: string
  ein: string
}

export default function OrgWallPanel({ orgName, ein }: OrgWallPanelProps) {
  const mailtoHref = `mailto:hello@meritgiving.com?subject=Raise our flame for ${encodeURIComponent(orgName)}&body=Hi%2C%20I%27d%20like%20to%20claim%20the%20MERIT%20page%20for%20${encodeURIComponent(orgName)}%20(EIN%20${encodeURIComponent(ein)}).%20Please%20help%20us%20get%20started.`

  return (
    <div
      className="rounded-2xl border overflow-hidden"
      style={{ background: '#FAFAF8', borderColor: '#E5E0DB' }}
    >
      {/* Section label */}
      <div className="px-5 py-4 border-b" style={{ borderColor: '#E5E0DB' }}>
        <span className="font-body text-[10px] tracking-[0.08em] text-cool-grey uppercase font-medium">
          Their Page
        </span>
      </div>

      {/* Unlit lamp + copy */}
      <div className="px-5 py-8 flex flex-col items-center text-center gap-4">
        <div
          className="w-14 h-14 rounded-full flex items-center justify-center"
          style={{ background: 'rgba(201,169,110,0.08)' }}
        >
          <svg
            viewBox="0 0 24 24"
            width={28}
            height={28}
            fill="rgba(201,169,110,0.30)"
            aria-hidden="true"
            style={{ display: 'block' }}
          >
            <path d={LAMP_PATH} />
          </svg>
        </div>

        <div>
          <p className="font-body text-[14px] text-deep-navy font-medium leading-[1.5]">
            This corner belongs to {orgName}.
          </p>
          <p className="mt-1 font-body text-[13px] text-cool-grey leading-[1.55]">
            Their flame hasn&rsquo;t reached here yet.
          </p>
        </div>

        <p className="font-body text-[13px] text-cool-grey leading-[1.55]">
          Are you with this organization?{' '}
          <a
            href={mailtoHref}
            className="text-soft-gold hover:text-bright-gold transition-colors underline underline-offset-2"
          >
            Raise your flame.
          </a>
          {' '}It&rsquo;s free.
        </p>
      </div>

      {/* Phase 2 teaser */}
      <div className="px-5 py-4 border-t" style={{ borderColor: '#E5E0DB' }}>
        <p className="font-body text-[11px] text-cool-grey/70 leading-[1.55] text-center">
          When they join: their updates, upcoming events, and what they need most right now.
        </p>
      </div>
    </div>
  )
}
