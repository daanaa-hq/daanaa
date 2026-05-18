import { Link } from 'react-router-dom'
import { usePageMeta } from '../hooks/usePageMeta'
import { useApi } from '../hooks/useApi'
import { getStats } from '../data/api'

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

function FormulaBlock({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-6 p-6 rounded-xl bg-deep-navy/[0.03] border border-deep-navy/10 font-mono text-[15px] text-deep-navy leading-[1.8]">
      {children}
    </div>
  )
}

function FlowStep({ kicker, title, detail, last }: { kicker: string; title: string; detail: string; last?: boolean }) {
  return (
    <div className="flex flex-col items-center">
      <div className="w-full max-w-[440px] rounded-xl border border-soft-gold/30 bg-white px-6 py-5 text-center shadow-[0_1px_3px_rgba(11,25,41,0.04)]">
        <p className="font-body text-[10px] font-semibold tracking-[0.14em] text-soft-gold uppercase mb-1.5">{kicker}</p>
        <p className="font-display italic text-deep-navy text-[20px] leading-tight">{title}</p>
        <p className="font-body text-[13px] text-cool-grey mt-1.5 leading-[1.5]">{detail}</p>
      </div>
      {!last && (
        <svg width="20" height="34" viewBox="0 0 20 34" fill="none" className="my-1.5" aria-hidden="true">
          <line x1="10" y1="0" x2="10" y2="26" stroke="#C9A84C" strokeWidth="1.5" />
          <path d="M4 24 L10 32 L16 24" stroke="#C9A84C" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
    </div>
  )
}

function ScoreFlow() {
  return (
    <div className="py-14 md:py-16 border-b border-light-grey">
      <div className="max-w-[760px]">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-6 h-px bg-soft-gold/50" />
          <span className="font-body text-[11px] font-medium tracking-[0.10em] text-soft-gold uppercase">The whole picture</span>
        </div>
        <h2 className="font-display italic text-deep-navy leading-[1.05] tracking-[-0.01em] mb-2" style={{ fontSize: 'clamp(26px, 3.5vw, 42px)' }}>
          How a score is made
        </h2>
        <p className="font-body text-[16px] text-cool-grey leading-[1.7] mb-9">
          Four steps. Every detail below this is just a closer look at one of them.
        </p>
        <div className="flex flex-col items-center">
          <FlowStep
            kicker="Step 1 · Group"
            title="Find its true peers"
            detail="Same kind of work, similar size, same part of the country."
          />
          <FlowStep
            kicker="Step 2 · Weigh"
            title="Measure financial scale"
            detail="Revenue rank ×0.65  +  reserve strength ×0.35, all within that peer group."
          />
          <FlowStep
            kicker="Step 3 · Place"
            title="A score from 0 to 100"
            detail="Where it sits among its true peers. 50 is the middle of every group."
          />
          <FlowStep
            kicker="Step 4 · Light"
            title="It feeds the lamp"
            detail="One quiet signal on the visibility journey. Never a grade, never a verdict."
            last
          />
        </div>
      </div>
    </div>
  )
}

function BandRow({ band, range, orgs, note }: { band: string; range: string; orgs: string; note?: string }) {
  return (
    <div className="flex items-start gap-4 py-3 border-b border-light-grey last:border-0">
      <span className="shrink-0 w-20 font-body text-[14px] font-semibold text-deep-navy">{band}</span>
      <span className="shrink-0 w-40 font-body text-[14px] text-cool-grey">{range}</span>
      <span className="shrink-0 w-28 font-body text-[13px] text-cool-grey/70">{orgs}</span>
      {note && <span className="font-body text-[13px] text-soft-gold/80 italic">{note}</span>}
    </div>
  )
}

function VersionRow({ version, date, description }: { version: string; date: string; description: string }) {
  return (
    <div className="flex items-start gap-4 py-3 border-b border-light-grey last:border-0">
      <span className="shrink-0 w-20 font-mono text-[13px] font-medium text-deep-navy">{version}</span>
      <span className="shrink-0 w-28 font-body text-[13px] text-cool-grey">{date}</span>
      <span className="font-body text-[14px] text-cool-grey">{description}</span>
    </div>
  )
}

function SourceRow({ source, detail }: { source: string; detail: string }) {
  return (
    <div className="flex items-start gap-4 py-3 border-b border-light-grey last:border-0">
      <span className="shrink-0 w-56 font-body text-[14px] font-medium text-deep-navy">{source}</span>
      <span className="font-body text-[14px] text-cool-grey">{detail}</span>
    </div>
  )
}

export default function Methodology() {
  usePageMeta(
    'Scoring Methodology',
    'The complete formula MERIT uses to score 430,000+ nonprofits. Peer groups, regional benchmarks, reserve ratio, and scorer versioning. Openly published.'
  )
  const { data: stats } = useApi(() => getStats(), [])
  const methodologyVersion = stats?.methodology_version ?? 'v1'
  const scoresUpdated = stats?.scores_last_updated ?? '—'

  return (
    <div className="min-h-[100dvh]">
      {/* Header */}
      <div className="bg-deep-navy pt-[72px]">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-12 pb-16">
          <div className="flex items-center gap-2 mb-6">
            <Link to="/" className="font-body text-[12px] tracking-[0.02em] text-muted-cream hover:text-warm-cream transition-colors">Home</Link>
            <span className="text-muted-cream/50">/</span>
            <span className="font-body text-[12px] text-muted-cream">Scoring Methodology</span>
          </div>
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 64px)' }}>
            Scoring Methodology
          </h1>
          <p className="mt-4 font-body text-[18px] leading-[1.6] text-muted-cream max-w-[640px]">
            The complete formula, openly published. No black boxes. Every input, weight, and design decision is documented here.
          </p>
          <div className="mt-7 flex flex-col sm:flex-row gap-4 sm:gap-10">
            <div>
              <p className="font-body text-[10px] font-medium tracking-[0.12em] text-soft-gold/60 uppercase mb-1.5">
                Formula version · changes rarely
              </p>
              <span className="font-mono text-[14px] text-warm-cream bg-white/5 px-3 py-1 rounded-full border border-white/10">
                Methodology {methodologyVersion}
              </span>
            </div>
            <div>
              <p className="font-body text-[10px] font-medium tracking-[0.12em] text-soft-gold/60 uppercase mb-1.5">
                Data refresh · updates as new 990s are filed
              </p>
              <span className="font-mono text-[14px] text-warm-cream bg-white/5 px-3 py-1 rounded-full border border-white/10">
                Scores last computed: {scoresUpdated}
              </span>
            </div>
          </div>
          <p className="mt-5 font-body text-[13px] leading-[1.6] text-muted-cream/70 max-w-[620px]">
            The methodology is the formula. It is versioned and changes rarely. Scores are
            recomputed as new IRS filings become available. A new score date does not mean
            the formula changed.
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="bg-warm-cream">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">

          <ScoreFlow />

          <Section label="Step 1 · The peer group" title="How we define 'similar'">
            <p>
              We never compare a food bank to a hospital. Every nonprofit is scored only against organizations doing the same kind of work, at a similar size, in the same part of the country. A peer group is three things:
            </p>
            <ul className="list-none space-y-2 mt-2">
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">1</span></span>
                <span><strong className="text-deep-navy font-medium">Kind of work.</strong> The IRS gives every 501(c)(3) a fine mission code (Food Banks, Hospitals, Parent-teacher groups, and 400 more). We match within it.</span>
              </li>
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">2</span></span>
                <span><strong className="text-deep-navy font-medium">Size.</strong> One of six revenue bands (below). A $40K group and a $40M one live in different worlds.</span>
              </li>
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">3</span></span>
                <span><strong className="text-deep-navy font-medium">Region.</strong> One of four US Census regions. Cost of living and giving culture vary by region.</span>
              </li>
            </ul>
            <p>
              A regional group needs at least 30 organizations to be meaningful. If it is too thin, the national group for that work and size is used instead. About 88% of organizations are scored against a regional peer group.
            </p>
          </Section>

          <Section label="Step 1 · Size bands" title="The six revenue bands">
            <p>
              Size comes from the most recent annual revenue on file. The six bands:
            </p>
            <div className="mt-4">
              <div className="flex items-start gap-4 py-2 border-b border-light-grey">
                <span className="shrink-0 w-20 font-body text-[11px] font-semibold tracking-[0.06em] text-cool-grey/60 uppercase">Band</span>
                <span className="shrink-0 w-40 font-body text-[11px] font-semibold tracking-[0.06em] text-cool-grey/60 uppercase">Revenue range</span>
                <span className="shrink-0 w-28 font-body text-[11px] font-semibold tracking-[0.06em] text-cool-grey/60 uppercase">Orgs</span>
                <span className="font-body text-[11px] font-semibold tracking-[0.06em] text-cool-grey/60 uppercase">Notes</span>
              </div>
              <BandRow band="Nano"   range="< $25K"         orgs="77,486"   note="grassroots, newly formed" />
              <BandRow band="Micro"  range="$25K to $100K"  orgs="139,419"  />
              <BandRow band="Small"  range="$100K to $500K" orgs="168,323"  />
              <BandRow band="Medium" range="$500K to $5M"   orgs="119,943"  />
              <BandRow band="Large"  range="$5M to $50M"    orgs="37,992"   />
              <BandRow band="Major"  range="$50M+"          orgs="8,220"    note="hospitals, universities" />
            </div>
            <Callout>
              Nano and Micro are kept separate so a $5K volunteer group and a $90K community organization are not treated as the same kind of operation.
            </Callout>
          </Section>

          <Section label="Step 2 · The formula" title="Two rankings, one number">
            <FormulaBlock>
              <div className="text-deep-navy/80">composite = <span className="text-deep-navy font-semibold">0.65</span> × revenue_percentile</div>
              <div className="text-deep-navy/80 ml-[80px]">+ <span className="text-deep-navy font-semibold">0.35</span> × reserve_percentile</div>
              <div className="mt-3 text-[13px] text-cool-grey/70">
                revenue_percentile is rank by total annual revenue within the peer group (0 = smallest, 100 = largest)<br />
                reserve_percentile is rank by reserve ratio within the peer group (0 = thinnest reserves, 100 = strongest)
              </div>
            </FormulaBlock>
            <p>
              Revenue carries more weight because scale is the clearest signal of reach. Reserves carry the rest because a thin balance sheet is a real risk that revenue alone hides. Both rankings are computed inside the peer group, so the middle organization in every group scores 50, and a 75 means the same thing for a food bank as for a hospital: top quarter of its peers.
            </p>
          </Section>

          <Section label="Step 2 · The reserve half" title="Why reserves count">
            <FormulaBlock>
              reserve_ratio = total_assets ÷ total_revenue
            </FormulaBlock>
            <p>
              This stands in for the working capital ratio, which the research consistently names as the best single indicator of nonprofit financial health (Tuckman & Chang 1991, Bowman 2011, Calabrese 2013). It answers one question: could this organization survive a year where the money stopped? A low ratio means thin coverage. A high one usually means a large endowment, which is a legitimate model, not a flaw, so organizations with big endowments are ranked against each other.
            </p>
            <Callout>
              The exact working capital ratio needs liability data filed by only about 4,700 organizations. The version using total assets is available for all 542,000+ scored organizations and tracks closely for the vast majority. Negative net worth is treated as zero, and reserves are capped at the group maximum so no one is penalized for having a lot.
            </Callout>
          </Section>

          <Section label="Scope and limits" title="What the score does not measure">
            <p>
              The financial scale score is a narrow measure of financial resources relative to peer organizations. It does not measure, and should not be interpreted as measuring:
            </p>
            <ul className="space-y-2 mt-2 list-none">
              {[
                'Program quality or impact',
                'Governance practices or board composition',
                'Fundraising efficiency or donor retention',
                'Leadership quality or organizational culture',
                'Overhead ratio (see the 2013 Overhead Myth letter signed by GuideStar, Charity Navigator, and the BBB Wise Giving Alliance)',
                'Community trust or local reputation',
              ].map(item => (
                <li key={item} className="flex gap-3 items-start">
                  <span className="shrink-0 mt-[7px] w-1.5 h-1.5 rounded-full bg-soft-gold/50" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            <Callout>
              A lower financial scale score may reflect organizational structure rather than weakness. Pass through models, federated chapters that consolidate revenue at a national entity, and newly founded organizations regularly score in the lower half. That accurately describes their position in the peer distribution, not their quality or worth.
            </Callout>
            <p>
              Outcome data, the measure donors most want, is not measurable from public filings at sector wide scale. No rating system that claims to measure program effectiveness from 990 data alone should be trusted. MERIT does not make this claim.
            </p>
          </Section>

          <Section label="Version history" title="Scorer versioning and backward consistency">
            <p>
              Every time the scoring methodology changes, a new version is tagged. Raw inputs (total revenue, total assets, peer group, and region) are stored alongside each score, so any prior period can be recomputed under a newer formula.
            </p>
            <div className="mt-4">
              <div className="flex items-start gap-4 py-2 border-b border-light-grey">
                <span className="shrink-0 w-20 font-body text-[11px] font-semibold tracking-[0.06em] text-cool-grey/60 uppercase">Version</span>
                <span className="shrink-0 w-28 font-body text-[11px] font-semibold tracking-[0.06em] text-cool-grey/60 uppercase">Date</span>
                <span className="font-body text-[11px] font-semibold tracking-[0.06em] text-cool-grey/60 uppercase">What it is</span>
              </div>
              <VersionRow
                version={methodologyVersion}
                date={scoresUpdated}
                description="Initial public methodology. Regional peer groups (NTEE subcategory plus revenue band plus US Census region), six revenue bands (Nano through Major), and a 0.65 revenue / 0.35 reserve composite computed within each peer group."
              />
            </div>
            <Callout>
              Future methodology changes will appear here with a new version tag and a plain-English summary of what changed and why. Score recomputations against fresh IRS data are not methodology changes and do not bump the version.
            </Callout>
            <p className="mt-6">
              Historical input snapshots are preserved in the <code className="text-[14px] bg-deep-navy/[0.05] px-1.5 py-0.5 rounded">score_snapshots</code> table. When the methodology does change, prior-period inputs can be rescored under the new formula, enabling chain-linked time series — the same approach used for CPI and home price indices.
            </p>
          </Section>

          <Section label="Data sources" title="Where the data comes from">
            <p>
              MERIT draws exclusively from public records. We do not solicit, purchase, or accept data from the organizations we index.
            </p>
            <div className="mt-4">
              <SourceRow
                source="IRS Business Master File"
                detail="501(c)(3) registration status, EIN, organization name, state, NTEE code. Updated quarterly by the IRS. MERIT indexes the active 501(c)(3) public charity subset, over 430,000 organizations."
              />
              <SourceRow
                source="IRS Statistics of Income"
                detail="Financial data from aggregated 990 filings, including total revenue and total assets. Available for approximately 483,000 organizations with recent IRS extract data."
              />
              <SourceRow
                source="ProPublica Nonprofit Explorer"
                detail="Mission statements, website URLs, 990 filing detail. Used to supplement IRS SOI data and establish profile completeness for the lamp tier."
              />
              <SourceRow
                source="NCCS (Urban Institute)"
                detail="Supplementary NTEE subcategory codes and historical filing data."
              />
            </div>
            <Callout>
              Data currency varies by source. The IRS registration list is updated quarterly. 990 financials reflect the most recent filing on record, which may be 1 to 3 years behind the current fiscal year. Score dates reflect when MERIT last processed the available data, not when the organization filed.
            </Callout>
          </Section>

          {/* Footer nav */}
          <div className="py-14 flex flex-col sm:flex-row items-start sm:items-center gap-6 justify-between">
            <div>
              <p className="font-body text-[13px] text-cool-grey">Questions about the methodology?</p>
              <Link to="/about#contact" className="font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors mt-1 inline-block">
                Contact the MERIT team →
              </Link>
            </div>
            <div className="flex gap-6">
              <Link to="/how-it-works" className="font-body text-[14px] text-cool-grey hover:text-deep-navy transition-colors">
                How It Works
              </Link>
              <Link to="/tiers" className="font-body text-[14px] text-cool-grey hover:text-deep-navy transition-colors">
                Trust Tiers
              </Link>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
