import { Link } from 'react-router-dom'
import LampMark from '../components/LampMark'
import { TIER_COLORS } from '../components/TrustBadge'
import type { TierName } from '../components/TrustBadge'
import { usePageMeta } from '../hooks/usePageMeta'

function Section({ label, title, children }: { label: string; title: string; children: React.ReactNode }) {
  return (
    <div className="py-14 md:py-20 border-b border-light-grey last:border-0">
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
  usePageMeta('How It Works', 'Learn how MERIT scores 430,000+ nonprofits using IRS data, peer-group benchmarking, and real Form 990 financials.')
  return (
    <div className="min-h-[100dvh]">
      {/* Header */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-12 pb-16">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] tracking-[0.02em] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream/50">/</span>
            <span className="font-body text-[12px] text-muted-cream">How It Works</span>
          </div>
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 64px)' }}>
            How MERIT Works
          </h1>
          <p className="mt-4 font-body text-[18px] leading-[1.6] text-muted-cream max-w-[640px]">
            We don't score nonprofits on our opinion. We surface publicly available data, place each organization alongside its true peers, and let you decide.
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="bg-warm-cream">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">

          <Section label="Our foundation" title="What MERIT is — and isn't">
            <p>
              MERIT is an independent civic platform. We are not affiliated with the IRS, the federal government, or any nonprofit rating agency. We don't accept payments from organizations to influence their listing or score.
            </p>
            <p>
              We index every 501(c)(3) organization in the United States from IRS public records — over 430,000 of them — and give donors a searchable, honest view of the sector. Our role is to surface information, not to judge missions.
            </p>
            <Callout>
              A high MERIT score means an organization is financially strong relative to similar nonprofits of similar size. It does not measure impact, goodness of purpose, or how efficiently a dollar reaches a beneficiary. Those things matter enormously — they are also much harder to measure, and we won't pretend otherwise.
            </Callout>
          </Section>

          <Section label="Data sources" title="Where the data comes from">
            <p>Every organization listing is built from multiple layers of public data:</p>
            <div className="mt-2 space-y-3">
              {[
                { source: 'IRS Business Master File (BMF)', what: 'Legal name, EIN, NTEE category, state of incorporation, 501(c)(3) status. Updated by the IRS continuously.' },
                { source: 'IRS 990 XML Filings', what: 'Annual financial returns filed with the IRS. Source of mission statements, program descriptions, leadership, and detailed financials.' },
                { source: 'IRS Statistics of Income (SOI)', what: 'IRS-published financial extracts covering FY2019–2024. Revenue figures for ~340,000 organizations.' },
                { source: 'ProPublica Nonprofit Explorer', what: 'Enriched financial data for ~42,000 organizations with verified FY2022–2024 figures.' },
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
              Every listing shows a data timestamp — "FY 2023 · Source: IRS" — so you always know how recent the information is.
            </p>
          </Section>

          <Section label="The financial picture" title="How the financial number works">
            <p>
              This number sits quietly behind the lamp. It is not a grade and it is not a judgment. It says nothing about the quality of the work, the people, or the good they do. All it does is compare one organization's financial size to other groups doing similar work at a similar scale. The lamp is the journey. This is just one fact along the way.
            </p>
            <p>
              We use two dimensions to define "similar":
            </p>
            <div className="mt-2 space-y-3">
              <div className="p-4 bg-white rounded-lg border border-light-grey">
                <p className="font-body text-[14px] font-semibold text-deep-navy">NTEE Subcategory</p>
                <p className="font-body text-[14px] text-cool-grey mt-1">
                  The IRS assigns each nonprofit an NTEE code — a two-letter subcategory within a broader sector. "B24" means Special Education; "E21" means Community Health Centers. We compare within subcategory, not just the broad sector. A small folk arts museum is not a peer of the Metropolitan Museum of Art.
                </p>
              </div>
              <div className="p-4 bg-white rounded-lg border border-light-grey">
                <p className="font-body text-[14px] font-semibold text-deep-navy">Revenue Band</p>
                <p className="font-body text-[14px] text-cool-grey mt-1">
                  A nonprofit raising $60,000 a year operates in a completely different reality from one raising $5 million. We group organizations into six revenue bands — Nano, Micro, Small, Medium, Large, and Major — and score within each band. Your $80K community garden is ranked against other similarly-sized community gardens.
                </p>
              </div>
            </div>
            <p className="mt-4">
              If a subcategory + size group has fewer than 30 organizations nationally, we step up to the broader sector. If that's still too small, we use the full sector with no size filter. You'll always see which peer group the score reflects.
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
          </Section>

          <Section label="Trust tiers" title="The lamp: a visibility journey, not a grade">
            <p>
              Every listing displays a lamp tier — and it is a journey, not a verdict. The lamp shows how much public data backs a profile <em>today</em>, never our opinion of the organization's work. Most U.S. nonprofits are small, community-rooted, and nearly invisible in public data — and they are exactly who we built MERIT for. A fainter lamp isn't a judgment; it's an invitation. Any organization can raise its flame by adding its mission, website, and financial detail — and that path stays free and open, always.
            </p>
            <div className="mt-4 space-y-3">
              {([
                {
                  tier: 'Beacon' as TierName,
                  what: 'Peer score in the top quartile (≥ 75th percentile), current 990, mission statement, and active website — all verified from public records.',
                },
                {
                  tier: 'Lantern' as TierName,
                  what: 'Current 990, mission statement, and active website all on public record. Peer score on file.',
                },
                {
                  tier: 'Flame' as TierName,
                  what: 'Current 990 on file and peer-benchmarked. Mission statement or website not yet in public records.',
                },
                {
                  tier: 'Ember' as TierName,
                  what: 'IRS-confirmed 501(c)(3) with some financial data on record. Peer score not yet computable.',
                },
                {
                  tier: 'Spark' as TierName,
                  what: 'Registered 501(c)(3) in the IRS master file. No financial detail in our index yet — many 990-N filers (under $50K revenue) fall here.',
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
              A lower tier is not a negative judgment. It reflects what public data is available — not the organization's character, impact, or importance. A 990-N filer doing extraordinary community work will show as Spark. That may change as more data enters the public record.
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
                <p className="font-body text-[12px] tracking-[0.06em] text-soft-gold uppercase font-medium mb-2">MERIT's data</p>
                <p className="font-body text-[13px] text-cool-grey leading-[1.6]">
                  Sourced from IRS public records. Objective, auditable, timestamped. Organizations cannot edit this layer.
                </p>
                <ul className="mt-3 space-y-1 font-body text-[13px] text-cool-grey">
                  {['Legal name & EIN', 'NTEE category', 'Revenue from IRS filings', 'MERIT peer score', 'Data source & tax year'].map(i => (
                    <li key={i} className="flex items-center gap-2">
                      <span className="w-1 h-1 rounded-full bg-cool-grey shrink-0" />{i}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="p-5 bg-white rounded-xl border-2 border-dashed border-soft-gold/30">
                <p className="font-body text-[12px] tracking-[0.06em] text-soft-gold uppercase font-medium mb-2">Organization's data</p>
                <p className="font-body text-[13px] text-cool-grey leading-[1.6]">
                  Added directly by the organization. Clearly labeled as self-reported. Coming soon — claim your page.
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
              This separation is fundamental to trust. You always know whether you're reading IRS-sourced data or an organization's own description of itself — and both are valuable for different reasons.
            </p>
          </Section>

          <Section label="Updates" title="How data stays current">
            <p>
              We run automated refreshes on a regular cadence:
            </p>
            <div className="mt-2 space-y-2">
              {[
                { freq: 'Weekly', what: 'ProPublica enrichment for organizations with new 990 filings' },
                { freq: 'Monthly', what: 'IRS SOI extract download and ingestion for newly published tax years' },
                { freq: 'Ongoing', what: 'Peer percentile recomputation after any bulk revenue update' },
              ].map(({ freq, what }) => (
                <div key={freq} className="flex gap-4 items-start">
                  <span className="shrink-0 font-body text-[13px] font-semibold text-soft-gold w-20">{freq}</span>
                  <span className="font-body text-[14px] text-cool-grey">{what}</span>
                </div>
              ))}
            </div>
            <p className="mt-4">
              Every organization's detail page shows the data vintage — the tax year and source — so you're never guessing how old the information is.
            </p>
          </Section>

          {/* CTA */}
          <div className="py-12">
            <div className="bg-deep-navy rounded-2xl p-8 md:p-12 text-center">
              <h3 className="font-display italic text-warm-cream text-[28px] leading-[1.1]">Questions or corrections?</h3>
              <p className="mt-3 font-body text-[16px] text-muted-cream max-w-[480px] mx-auto leading-[1.6]">
                If you represent a listed organization and want to update or claim your page, or if you spot an error in our data, we want to hear from you.
              </p>
              <a
                href="mailto:hello@meritgiving.org"
                className="mt-6 inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-soft-gold text-deep-navy font-body text-[14px] font-semibold hover:bg-bright-gold transition-colors"
              >
                Contact us
              </a>
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
