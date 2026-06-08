import { Link } from 'react-router-dom'
import LampMark from '../components/LampMark'
import { TIER_COLORS } from '../components/TrustBadge'
import type { TierName } from '../components/TrustBadge'
import { usePageMeta } from '../hooks/usePageMeta'

function Section({ label, title, children }: { label: string; title: string; children: React.ReactNode }) {
  return (
    <div className="py-10 md:py-14 lg:py-20 border-b border-light-grey last:border-0">
      <div className="max-w-[760px]">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-6 h-px bg-soft-gold/50" />
          <span className="font-body text-[11px] font-medium tracking-[0.10em] text-soft-gold uppercase">{label}</span>
        </div>
        <h2 className="font-display italic text-deep-navy leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(26px, 3.5vw, 42px)' }}>
          {title}
        </h2>
        <div className="mt-7 space-y-4 font-body text-[16px] text-cool-grey leading-[1.7]">
          {children}
        </div>
      </div>
    </div>
  )
}

function Callout({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-6 p-5 rounded-xl bg-soft-gold/10 border border-soft-gold/20">
      <p className="font-body text-[15px] text-deep-navy leading-[1.6]">{children}</p>
    </div>
  )
}

function TierRow({ score, label, description }: { score: string; label: string; description: string }) {
  // Financial scale is not a danger gradient. Larger scale gets a gentle green;
  // everything else is calm slate. A smaller organization is not "worse".
  const color = label === 'Among the largest like it' || label === 'Larger than most like it'
    ? '#5a9e6f'
    : '#8a8f98'
  return (
    <div className="flex items-start gap-4 py-3 border-b border-light-grey last:border-0">
      <span className="shrink-0 w-20 font-body text-[13px] font-semibold" style={{ color }}>{score}</span>
      <span className="shrink-0 w-48 font-body text-[14px] font-medium text-deep-navy">{label}</span>
      <span className="font-body text-[14px] text-cool-grey">{description}</span>
    </div>
  )
}

export default function HowItWorks() {
  usePageMeta('How It Works', 'Learn how Daanaa scores nonprofits using IRS data and peer group benchmarking across nine operating model groups. All organizations are tax-deductible 501(c)(3) nonprofits.')
  return (
    <div className="min-h-[100dvh]">
      {/* Header */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-8 pb-10 md:pt-12 md:pb-16">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] tracking-[0.02em] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream/50">/</span>
            <span className="font-body text-[12px] text-muted-cream">How It Works</span>
          </div>
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 64px)' }}>
            How Daanaa Works
          </h1>
          <p className="mt-4 font-body text-[18px] leading-[1.6] text-muted-cream max-w-[640px]">
            We don't score nonprofits on our opinion. We surface publicly available data, place each organization alongside its true peers, and let you decide.
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="bg-warm-cream">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">

          <Section label="Our foundation" title="What Daanaa is, and what it isn't">
            <p>
              Daanaa is an independent civic platform. We are not affiliated with the IRS, the federal government, or any nonprofit rating agency. We don't accept payments from organizations to influence their listing or score.
            </p>
            <p>
              We list every 501(c)(3) nonprofit the IRS recognizes where donations are eligible for a tax deduction. More than 1.8 million of them. Our role is to surface information, not to judge missions.
            </p>
            <Callout>
              Two signals work together on every profile. The peer financial context score (0–100) measures financial scale — how big this organization is relative to similar groups. The Financial Health tier (Strong, Stable, or Inspiring) measures how well it manages its resources within that peer group. Neither measures impact, mission quality, or whether a group deserves support. Daanaa is not a charity rating agency.
            </Callout>
          </Section>

          <Section label="Data sources" title="Where the data comes from">
            <p>Every organization listing is built from multiple layers of public data:</p>
            <div className="mt-2 space-y-3">
              {[
                { source: 'IRS nonprofit registration list', what: 'Legal name, category, state, and nonprofit status. Updated by the IRS continuously.' },
                { source: 'Annual financial reports (filed with the government)', what: 'Reports nonprofits file with the IRS each year. Source of mission statements, program descriptions, leadership, and detailed financials.' },
                { source: 'Government-published financial summaries', what: 'IRS financial data covering 2019–2024. Revenue and expense figures for about 530,000 organizations.' },
                { source: 'ProPublica nonprofit database (a public interest newsroom)', what: 'Financial data for about 42,000 organizations with verified 2022–2024 figures.' },
              ].map(({ source, what }) => (
                <div key={source} className="flex gap-4 p-4 bg-white rounded-lg border border-light-grey">
                  <div className="shrink-0 w-2 h-2 mt-2 rounded-full bg-soft-gold" />
                  <div>
                    <p className="font-body text-[14px] font-semibold text-deep-navy">{source}</p>
                    <p className="font-body text-[14px] text-cool-grey mt-1">{what}</p>
                  </div>
                </div>
              ))}
            </div>
            <p className="mt-4">
              Every listing shows when the data is from and where it came from, like "2023 · Source: IRS", so you always know how recent the information is.
            </p>
          </Section>

          <Section label="The financial picture" title="How peer financial context works">
            <p>
              This number sits quietly behind the lamp. It is not a grade and it is not a judgment. It says nothing about the quality of the work, the people, or the good they do. All it does is compare one organization's financial size to other groups doing similar work at a similar scale. The lamp is the journey. This is just one fact along the way.
            </p>
            <p>
              We use two dimensions to define "similar":
            </p>
            <div className="mt-2 space-y-3">
              <div className="p-4 bg-white rounded-lg border border-light-grey">
                <p className="font-body text-[14px] font-semibold text-deep-navy">Type of work</p>
                <p className="font-body text-[14px] text-cool-grey mt-1">
                  Each nonprofit is placed in one of nine operating model groups based on how it actually runs — Activity and Programming, Direct Delivery, Community and Human Services, Clinical and Health, Emergency and Logistics, Cause and Research, Intermediary and Philanthropy, Faith Community, and Membership and Mutual Benefit. A food bank is compared to other food banks at the same scale, not to universities or hospitals.
                </p>
              </div>
              <div className="p-4 bg-white rounded-lg border border-light-grey">
                <p className="font-body text-[14px] font-semibold text-deep-navy">Revenue Band</p>
                <p className="font-body text-[14px] text-cool-grey mt-1">
                  A nonprofit raising $60,000 a year operates in a completely different reality from one raising $5 million. Each operating model has five to eight revenue bands, set from that model's own distribution — so a small food bank is sized against other small food banks, not against small hospitals. Your $80K community garden is ranked against other community gardens of a similar size.
                </p>
              </div>
            </div>
            <p className="mt-4">
              Each peer cell needs at least 30 organizations to be meaningful. In practice, most cells have thousands. The metrics that matter differ by group: reserves are weighted less for food banks (where thin savings means mission delivery) and more for land trusts (where reserves are the mission).
            </p>

            <div className="mt-6">
              <p className="font-body text-[14px] font-semibold text-deep-navy mb-1">What the number means</p>
              <p className="font-body text-[13px] text-cool-grey mb-3 max-w-[640px]">
                It only tells you how big an organization is financially next to others doing similar work. A smaller organization is not a worse one. This number says nothing about the work, the people, or the good they do.
              </p>
              <div className="bg-white rounded-xl border border-light-grey p-4">
                <TierRow score="90 to 100" label="Among the largest like it" description="A bigger budget and stronger savings than almost every group doing similar work." />
                <TierRow score="75 to 89" label="Larger than most like it" description="Financially bigger than most groups doing similar work." />
                <TierRow score="60 to 74" label="A bit larger than most" description="A little bigger than the typical group doing this kind of work." />
                <TierRow score="40 to 59" label="About average in size" description="A normal size for the kind of work it does." />
                <TierRow score="0 to 39" label="Smaller than most like it" description="One of the smaller groups doing this work. Often newer, or running lean. It says nothing about how good the work is." />
              </div>
            </div>

            <p className="mt-5 font-body text-[15px] text-cool-grey leading-[1.7]">
              When you visit a profile, the primary signal you'll see is a <strong className="text-deep-navy font-medium">Financial Health tier</strong> — Strong, Stable, or Inspiring. That is a different measure from the 0–100 number above. The number shows financial scale. The tier shows how well the organization manages its resources within that peer group. A small org can be Strong. A large org can be Inspiring.
            </p>
            <p className="mt-3 font-body text-[15px] text-cool-grey leading-[1.7]">
              <strong className="text-deep-navy font-medium">Why "Inspiring"?</strong> Constrained financial resources don't mean constrained impact. Organizations working within tight means often do the most essential work in their communities. The name honors that — not a consolation, a recognition.
            </p>
            <div className="mt-4">
              <Link
                to="/methodology"
                className="inline-flex items-center gap-1.5 font-body text-[13px] font-semibold text-soft-gold hover:text-bright-gold transition-colors"
              >
                Full methodology: how Financial Health tiers are calculated →
              </Link>
            </div>
          </Section>

          <Section label="Visibility levels" title="Visibility levels: how much information is available">
            <p>
              Every listing displays a lamp tier, and it is a journey, not a verdict. The lamp shows how much public data backs a profile <em>today</em>, never our opinion of the organization's work. Most U.S. nonprofits are small, rooted in their communities, and nearly invisible in public data. They are exactly who we built Daanaa for. A fainter lamp isn't a judgment. It's an invitation. Any organization can raise its flame by adding its mission, website, and financial detail, and that path stays free and open, always.
            </p>
            <div className="mt-4 space-y-3">
              {([
                {
                  tier: 'Beacon' as TierName,
                  what: 'Mission, giving path, service area, and public financial data all on record. Complete profile confirmed from public records.',
                },
                {
                  tier: 'Lantern' as TierName,
                  what: 'Current annual report, mission statement, and active website all on public record. Financial ranking on file.',
                },
                {
                  tier: 'Flame' as TierName,
                  what: 'Current annual report on file with a financial ranking. Mission statement or website not yet in public records.',
                },
                {
                  tier: 'Glow' as TierName,
                  what: 'IRS-confirmed nonprofit with some financial data on record. Not enough data yet to assign a financial context ranking.',
                },
                {
                  tier: 'Seed' as TierName,
                  what: 'Registered nonprofit in the IRS list. No financial detail in our index yet. Many small organizations filing a simplified annual form (under $50K revenue) fall here.',
                },
              ] as const).map(({ tier, what }) => (
                <div key={tier} className="flex gap-4 p-4 bg-white rounded-lg border border-light-grey items-start">
                  <div className="shrink-0 flex flex-col items-center gap-1.5 pt-0.5">
                    <LampMark tier={tier} size="sm" />
                    <span className="font-body text-[10px] font-semibold tracking-[0.03em]" style={{ fontFamily: 'Cinzel, serif', color: TIER_COLORS[tier] }}>{tier}</span>
                  </div>
                  <p className="font-body text-[14px] text-cool-grey leading-[1.6]">{what}</p>
                </div>
              ))}
            </div>
            <Callout>
              A lower tier is not a negative judgment. It reflects what public data is available, not the organization's character or importance. A small organization filing a simplified annual form while doing extraordinary community work will show as Seed. That can change as more data enters the public record.
            </Callout>
            <div className="mt-6">
              <Link
                to="/tiers"
                className="inline-flex items-center gap-1.5 font-body text-[13px] font-semibold text-soft-gold hover:text-bright-gold transition-colors"
              >
                Full tier reference →
              </Link>
            </div>
          </Section>

          <Section label="Two-layer model" title="What the organization controls">
            <p>
              Every listing has two distinct layers:
            </p>
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-5 bg-white rounded-xl border border-light-grey">
                <p className="font-body text-[12px] tracking-[0.06em] text-soft-gold uppercase font-medium mb-2">Daanaa's data</p>
                <p className="font-body text-[13px] text-cool-grey leading-[1.6]">
                  Sourced from IRS public records. Objective, fact-checked, timestamped. Organizations cannot edit this layer.
                </p>
                <ul className="mt-3 space-y-1 font-body text-[13px] text-cool-grey">
                  {['Legal name', 'Nonprofit category', 'Revenue from IRS filings', 'Daanaa financial ranking', 'Data source & year'].map(i => (
                    <li key={i} className="flex items-center gap-2">
                      <span className="w-1 h-1 rounded-full bg-cool-grey shrink-0" />{i}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="p-5 bg-white rounded-xl border-2 border-dashed border-soft-gold/30">
                <p className="font-body text-[12px] tracking-[0.06em] text-soft-gold uppercase font-medium mb-2">Organization's data</p>
                <p className="font-body text-[13px] text-cool-grey leading-[1.6]">
                  Added directly by the organization. Clearly labeled as self reported. Claim your page to update this information.
                </p>
                <ul className="mt-3 space-y-1 font-body text-[13px] text-cool-grey">
                  {['Mission statement', 'Program descriptions', 'Leadership team', 'Photos & annual reports', 'Impact metrics'].map(i => (
                    <li key={i} className="flex items-center gap-2">
                      <span className="w-1 h-1 rounded-full bg-soft-gold/50 shrink-0" />{i}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <p className="mt-6">
              This separation is fundamental to trust. You always know whether you're reading data from the IRS or an organization's own description of itself. Both are valuable, for different reasons.
            </p>
          </Section>

          <Section label="Updates" title="How data stays current">
            <p>
              We run automated updates on a regular schedule:
            </p>
            <div className="mt-2 space-y-2">
              {[
                { freq: 'Monthly', what: 'ProPublica data for organizations with new financial reports' },
                { freq: 'Monthly', what: 'IRS financial data update for newly published years' },
                { freq: 'Monthly', what: 'IRS tax-exempt status check against the federal auto-revocation list' },
                { freq: 'Ongoing', what: 'Financial rankings recalculated after bulk revenue updates' },
              ].map(({ freq, what }) => (
                <div key={freq} className="flex gap-4 items-start">
                  <span className="shrink-0 font-body text-[13px] font-semibold text-soft-gold w-20">{freq}</span>
                  <span className="font-body text-[14px] text-cool-grey">{what}</span>
                </div>
              ))}
            </div>
            <p className="mt-4">
              Every organization's detail page shows when the data is from and where it came from, so you're never guessing how old the information is.
            </p>
          </Section>

          {/* CTA */}
          <div className="py-12">
            <div className="bg-deep-navy rounded-2xl p-8 md:p-12 text-center">
              <h3 className="font-display italic text-warm-cream text-[28px] leading-[1.1]">Questions or corrections?</h3>
              <p className="mt-3 font-body text-[16px] text-muted-cream max-w-[480px] mx-auto leading-[1.6]">
                If you represent a listed organization and want to update or claim your page, or if you spot an error in our data, we want to hear from you.
              </p>
              <Link
                to="/feedback"
                className="mt-6 inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors"
              >
                Contact us
              </Link>
              <div className="mt-6 flex items-center justify-center gap-6">
                <Link to="/directory" className="font-body text-[13px] text-muted-cream hover:text-warm-cream transition-colors">
                  Browse the directory →
                </Link>
                <Link to="/legal" className="font-body text-[13px] text-muted-cream hover:text-warm-cream transition-colors">
                  Data attribution →
                </Link>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
