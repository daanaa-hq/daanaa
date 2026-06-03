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
            detail="Same operating model (Direct Service, Mission Infrastructure, Asset Stewards, or Endowment & Capital) plus similar revenue size."
          />
          <FlowStep
            kicker="Step 2 · Weigh"
            title="Measure financial scale"
            detail="Reserve strength and program spending, weighted by operating model. What counts as healthy reserves for a food bank differs from what counts for a land trust."
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
    'How peer financial context is calculated',
    'Daanaa scores 501(c)(3) tax-deductible nonprofits on peer financial context. Every organization is compared only against true peers — same operating model, same revenue size. 1.6 million organizations indexed. Full methodology documented here.'
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
            <span className="font-body text-[12px] text-muted-cream">How peer financial context is calculated</span>
          </div>
          <h1 className="font-display italic text-warm-cream leading-[1.05] tracking-[-0.01em]" style={{ fontSize: 'clamp(32px, 5vw, 64px)' }}>
            How peer financial context is calculated
          </h1>
          <p className="mt-4 font-body text-[18px] leading-[1.6] text-muted-cream max-w-[640px]">
            Peer financial context is an optional public-data signal. It does not measure impact, trustworthiness, leadership, governance, program quality, or whether a group deserves support. Every number compares a nonprofit against others doing similar work at a similar size, using public IRS filings. No black boxes. Everything is documented below.
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
                Data refresh · updates as new reports come in
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

          {/* Plain-English summary — for anyone who doesn't need the full formula */}
          <div className="py-10 border-b border-light-grey">
            <div className="max-w-[680px]">
              <h2 className="font-display italic text-deep-navy leading-tight mb-4" style={{ fontSize: 'clamp(22px, 2.8vw, 30px)' }}>
                The short version
              </h2>
              <p className="font-body text-[16px] text-cool-grey leading-[1.7]">
                Each nonprofit is scored only against organizations doing similar work at a similar size, using public IRS filings. The score, 0 to 100, shows where an organization stands within that peer group — not against all nonprofits.
              </p>
              <p className="mt-3 font-body text-[15px] text-cool-grey leading-[1.7]">
                All of this comes from annual IRS filings — the same public documents every registered 501(c)(3) submits. Organizations without detailed filing data are shown without a score. We never fabricate what we cannot measure.
              </p>
              <div className="mt-4 p-4 rounded-xl bg-deep-navy/5 border border-deep-navy/10">
                <p className="font-body text-[13px] text-cool-grey leading-[1.6]">
                  <strong className="text-deep-navy">Current scoring (v1.0):</strong> Peer groups use IRS NTEE category and revenue band. Formula: 0.65 × revenue percentile + 0.35 × reserve ratio, within each peer group.
                  <strong className="text-deep-navy ml-2">Coming in v2.0:</strong> Cause-aware operating model groups replace NTEE-only grouping. The four groups documented on this page reflect our research and planned methodology — not the live scorer.
                </p>
              </div>
              <div className="mt-5 flex flex-wrap gap-2">
                {[
                  { label: 'IRS Form 990 filings', href: 'https://projects.propublica.org/nonprofits/', note: 'FY 2019–2024' },
                  { label: 'IRS Statistics of Income', href: null, note: 'sector benchmarks' },
                  { label: 'ProPublica Nonprofit Explorer', href: 'https://projects.propublica.org/nonprofits/', note: 'data access' },
                  { label: 'NCCS', href: null, note: 'supplementary data' },
                ].map(s => (
                  <span key={s.label} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-deep-navy/5 border border-deep-navy/10 font-body text-[12px] text-cool-grey">
                    {s.href ? (
                      <a href={s.href} target="_blank" rel="noopener noreferrer" className="hover:text-soft-gold transition-colors inline-flex items-center gap-1">
                        {s.label}
                        <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                      </a>
                    ) : s.label}
                    <span className="text-cool-grey/50">· {s.note}</span>
                  </span>
                ))}
              </div>
              <p className="mt-5 font-body text-[13px] text-cool-grey/60">
                Want to understand exactly how each part is calculated? The sections below walk through every step.
              </p>
            </div>
          </div>

          <ScoreFlow />

          <Section label="Step 1 · The peer group" title="How we define 'similar'">
            <p>
              We never compare a food bank to a hospital. Every nonprofit is scored only against organizations doing the same kind of work, at a similar size, in the same part of the country. A peer group is three things:
            </p>
            <ul className="list-none space-y-2 mt-2">
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">1</span></span>
                <span><strong className="text-deep-navy font-medium">Operating model.</strong> How the organization actually runs — whether it spends everything on direct service, owns physical assets central to its mission, or holds long-term capital. Four groups, described below.</span>
              </li>
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">2</span></span>
                <span><strong className="text-deep-navy font-medium">Revenue size.</strong> One of six bands, from Nano (under $25K) to Major ($50M+). A grassroots group and a regional hospital live in different worlds even when they serve the same cause.</span>
              </li>
            </ul>
            <p className="mt-4">
              Together these create 24 peer cells. A peer cell needs at least 30 organizations to be statistically meaningful. Cells that are too thin fall back to the operating model group without a size constraint.
            </p>
          </Section>

          <Section label="Step 1 · Operating models" title="Four groups, not one size fits all">
            <p>
              We analyzed 356,000 tax-deductible nonprofits with complete financial filings and found four statistically distinct operating models (ANOVA F = 9,781, p &lt; 0.001, η² = 9.2%). Each group has a different relationship between reserves, assets, and program spending — so each group gets its own benchmarks.
            </p>

            <div className="mt-6 space-y-4">
              {[
                {
                  name: 'Direct Service',
                  orgs: '157,816',
                  reserve: '9.7 months',
                  prog: '48%',
                  ai: '0.96×',
                  desc: 'Human services, food, mental health, employment, international, recreation, youth development, religion. These organizations earn and spend — thin reserves are a feature of the model, not a weakness. A food bank with minimal savings may be deploying every dollar into its mission.',
                  color: 'bg-emerald-50 border-emerald-200',
                  badge: 'text-emerald-700 bg-emerald-100',
                },
                {
                  name: 'Mission Infrastructure',
                  orgs: '133,369',
                  reserve: '13 months',
                  prog: '39%',
                  ai: '1.33×',
                  desc: 'Education, health, arts, environment, community development, science. Moderate assets support program delivery — a school owns classrooms, a clinic owns equipment. Reserves sit in the middle range.',
                  color: 'bg-blue-50 border-blue-200',
                  badge: 'text-blue-700 bg-blue-100',
                },
                {
                  name: 'Asset Stewards',
                  orgs: '51,627',
                  reserve: '29.9 months',
                  prog: '36%',
                  ai: '3.03×',
                  desc: 'Housing, public safety (fire departments, EMS), cultural heritage, libraries, museums, animal welfare, sports, higher education. Physical assets — land, buildings, equipment — are central to mission delivery. Higher asset intensity and reserves are normal for this model.',
                  color: 'bg-amber-50 border-amber-200',
                  badge: 'text-amber-700 bg-amber-100',
                },
                {
                  name: 'Endowment & Capital',
                  orgs: '13,396',
                  reserve: '39+ months',
                  prog: '19%',
                  ai: '3.57×',
                  desc: 'Grantmaking foundations, conservation land trusts, scholarship funds, historical preservation, disease research. These organizations hold and deploy capital. Their low program spending percentage reflects their model — grants going out are their program. Reserve comparisons use net asset growth rather than a fixed-month benchmark.',
                  color: 'bg-purple-50 border-purple-200',
                  badge: 'text-purple-700 bg-purple-100',
                },
              ].map(g => (
                <div key={g.name} className={`p-5 rounded-xl border ${g.color}`}>
                  <div className="flex flex-wrap items-center gap-3 mb-3">
                    <span className={`font-body text-[12px] font-semibold px-2 py-0.5 rounded-full ${g.badge}`}>{g.name}</span>
                    <span className="font-body text-[12px] text-cool-grey">{g.orgs} organizations</span>
                  </div>
                  <p className="font-body text-[14px] text-cool-grey leading-[1.6] mb-3">{g.desc}</p>
                  <div className="flex flex-wrap gap-4">
                    {[
                      { label: 'Median reserve', value: g.reserve },
                      { label: 'Program spend', value: g.prog },
                      { label: 'Asset intensity', value: g.ai },
                    ].map(stat => (
                      <div key={stat.label}>
                        <p className="font-body text-[10px] font-medium tracking-[0.08em] text-cool-grey/60 uppercase">{stat.label}</p>
                        <p className="font-body text-[14px] font-semibold text-deep-navy">{stat.value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <Callout>
              Cause types are assigned to operating model groups based on their statistical financial fingerprint, not just their name. Where a cause type's financial behavior differs by size (for example, a small community health clinic vs. a major hospital system), the revenue band captures that difference within the group.
            </Callout>
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
              <BandRow band="Nano"   range="< $25K"         orgs="111,158"  note="grassroots, newly formed — many file 990-N postcards" />
              <BandRow band="Micro"  range="$25K to $100K"  orgs="164,502"  />
              <BandRow band="Small"  range="$100K to $500K" orgs="205,133"  />
              <BandRow band="Medium" range="$500K to $5M"   orgs="133,733"  />
              <BandRow band="Large"  range="$5M to $50M"    orgs="40,186"   />
              <BandRow band="Major"  range="$50M+"          orgs="8,605"    note="hospitals, universities, major foundations" />
            </div>
            <Callout>
              Nano and Micro are kept separate so a $5K volunteer group and a $90K community organization are not treated as the same kind of operation. Organizations in the Nano band filing a 990-N postcard (under $50K) may not have detailed financial data available — they are indexed and visible, but scored only when full filing data exists.
            </Callout>
          </Section>

          <Section label="Step 2 · The formula" title="Two rankings, one number">
            <p className="font-body text-[13px] text-cool-grey/70 italic mb-4">Current live formula (v1.0). See version history below for planned v2.0 changes.</p>
            <FormulaBlock>
              <div className="text-deep-navy/80">score = <span className="text-deep-navy font-semibold">0.65</span> × revenue_percentile</div>
              <div className="text-deep-navy/80 ml-[54px]">+ <span className="text-deep-navy font-semibold">0.35</span> × reserve_percentile</div>
              <div className="mt-3 text-[13px] text-cool-grey/70">
                revenue_percentile: rank by total annual revenue within peer group (0 = smallest, 100 = largest)<br />
                reserve_percentile: rank by total assets ÷ total revenue within peer group (0 = thinnest, 100 = strongest)<br />
                Both computed within the peer group — NTEE category + revenue band.
              </div>
            </FormulaBlock>
            <p>
              The middle organization in every peer group scores 50. A 75 means the same thing for a food bank as for a hospital system: top quarter of its peers. Revenue carries more weight because scale is the clearest signal of reach. Reserves carry the rest because a thin balance sheet is a real risk that revenue alone hides.
            </p>
            <Callout>
              In the planned v2.0 methodology, weights will vary by operating model group — Direct Service organizations will have reserves weighted differently than Endowment organizations, reflecting that thin reserves in a food bank and thin reserves in a land trust mean different things. The four operating model groups on this page document that research. Scores will be recomputed when v2.0 is deployed.
            </Callout>
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

          <Section label="What we don't yet measure" title="Known dimensions not yet in the score">
            <p>
              Financial filings are a narrow window. They tell us about revenue, assets, and spending — not about people, impact, or community presence. Several important dimensions exist outside what IRS data can show. We document them here so donors can weigh them independently.
            </p>
            <ul className="space-y-4 mt-4 list-none">
              {[
                {
                  label: 'Volunteer labor',
                  detail: 'IRS Form 990 Part I asks for the number of volunteers. For the organizations where this is reported, volunteer hours represent a form of donated labor equivalent in economic value to cash giving. The Independent Sector values a volunteer hour at $31.80 (2023). A food pantry with 300 volunteers giving 80 hours each contributes an estimated $763,200 in community labor — often several times its cash budget. We will surface this as a supplemental display once broader 990 data coverage allows it.',
                },
                {
                  label: 'Program outcomes and impact',
                  detail: 'IRS filings require financial disclosure, not impact measurement. No rating system that claims to measure program effectiveness from 990 data alone should be trusted. Daanaa does not make this claim.',
                },
                {
                  label: 'Governance and leadership',
                  detail: 'Board composition, term limits, conflict-of-interest policies, and leadership quality are not in IRS filings at scale. Some is available in 990 Part VI for larger filers.',
                },
                {
                  label: 'Community trust',
                  detail: 'Local reputation, relationships, and the depth of community roots are not measurable from public records. A highly trusted neighborhood organization may score modestly on financial metrics while doing irreplaceable work.',
                },
              ].map(item => (
                <li key={item.label} className="flex gap-3 items-start">
                  <span className="shrink-0 mt-[6px] w-1.5 h-1.5 rounded-full bg-soft-gold/50" />
                  <span><strong className="text-deep-navy font-medium">{item.label}.</strong> {item.detail}</span>
                </li>
              ))}
            </ul>
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
              A lower financial scale score may reflect organizational structure rather than weakness. Organizations that pass funding through to other groups, national chapters that report revenue centrally, and newly founded organizations regularly score in the lower half. That accurately describes their position among peers, not their quality or worth.
            </Callout>
            <p>
              Outcome data, the measure donors most want, is not measurable from public filings at sector wide scale. No rating system that claims to measure program effectiveness from 990 data alone should be trusted. Daanaa does not make this claim.
            </p>
          </Section>

          <Section label="Score availability" title="Three levels of data — three levels of display">
            <p>
              Not every organization has the same amount of public financial data. Daanaa displays what exists — and only what exists.
            </p>
            <div className="mt-4 space-y-3">
              {[
                {
                  tier: 'Scored',
                  count: '386,000 organizations',
                  desc: 'Complete IRS 990 filing data. Full 0–100 peer financial context score, operating model group, and reserve profile.',
                  color: 'border-emerald-300 bg-emerald-50',
                },
                {
                  tier: 'Revenue-placed',
                  count: '~115,000 organizations',
                  desc: 'IRS BMF summary revenue data only. Revenue band and operating model shown. No financial health score — detailed filing data is not available.',
                  color: 'border-amber-300 bg-amber-50',
                },
                {
                  tier: 'Visible',
                  count: '~1.1 million organizations',
                  desc: 'IRS-recognized 501(c)(3), tax-deductible. No financial filing data available — most file a 990-N postcard (under $50K gross receipts) or are churches exempt from 990 filing. Shown with IRS standing, cause type, and profile information. No financial score.',
                  color: 'border-cool-grey/30 bg-warm-cream',
                },
              ].map(t => (
                <div key={t.tier} className={`flex gap-4 p-4 rounded-xl border ${t.color}`}>
                  <div className="shrink-0 w-28">
                    <p className="font-body text-[13px] font-semibold text-deep-navy">{t.tier}</p>
                    <p className="font-body text-[11px] text-cool-grey/70 mt-0.5">{t.count}</p>
                  </div>
                  <p className="font-body text-[14px] text-cool-grey leading-[1.6]">{t.desc}</p>
                </div>
              ))}
            </div>
            <Callout>
              The absence of a score is not a negative signal. Most nonprofits in the United States are small volunteer-run organizations that file a postcard return. They are real, IRS-recognized, tax-deductible, and doing real work. Daanaa shows them — it just does not pretend to measure what it cannot see.
            </Callout>
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
                version="v2.0"
                date="2026-06-03"
                description="Cause-aware peer groups. Four operating model groups (Direct Service, Mission Infrastructure, Asset Stewards, Endowment & Capital) × six revenue bands = 24 peer cells. Universe restricted to tax-deductible 501(c)(3)s only. Corrected band counts from deductible-only population. Volunteer human capital acknowledged as future signal."
              />
              <VersionRow
                version="v1.0"
                date="2026-05-20"
                description="Initial public methodology. NTEE subcategory plus revenue band peer groups. Six revenue bands (Nano through Major). 0.65 revenue / 0.35 reserve composite."
              />
            </div>
            <Callout>
              Future methodology changes will appear here with a new version tag and a plain-English summary of what changed and why. Score recomputations against fresh IRS data are not methodology changes and do not bump the version.
            </Callout>
            <p className="mt-6">
              Historical inputs are preserved in our scoring records. When the methodology does change, prior-period inputs can be rescored under the new formula, enabling consistent comparisons over time, the same approach used for CPI and home price indices.
            </p>
          </Section>

          <Section label="Data sources" title="Where the data comes from">
            <p>
              Daanaa draws exclusively from public records. We do not solicit, purchase, or accept data from the organizations we index.
            </p>
            <div className="mt-4">
              <SourceRow
                source="IRS nonprofit registration list"
                detail="Tax-exempt status, organization name, state, and category code. Updated quarterly by the IRS. Daanaa indexes all active 501(c)(3) organizations where donations are tax-deductible — 1.63 million organizations. Non-deductible 501(c)(4), (c)(6), and other subsections are excluded from scoring."
              />
              <SourceRow
                source="IRS published financial data"
                detail="Financial data from aggregated annual filings, including total revenue and total assets. Available for approximately 483,000 organizations with recent data."
              />
              <SourceRow
                source="ProPublica Nonprofit Explorer"
                detail="Mission statements, website URLs, and annual filing detail. Used to fill in financial data and confirm profile completeness for the lamp tier."
              />
              <SourceRow
                source="NCCS (Urban Institute)"
                detail="Supplementary category codes and historical filing data."
              />
            </div>
            <Callout>
              Data currency varies by source. The IRS registration list is updated quarterly. 990 financials reflect the most recent filing on record, which may be 1 to 3 years behind the current fiscal year. Score dates reflect when Daanaa last processed the available data, not when the organization filed.
            </Callout>
          </Section>

          {/* Footer nav */}
          <div className="py-14 flex flex-col sm:flex-row items-start sm:items-center gap-6 justify-between">
            <div>
              <p className="font-body text-[13px] text-cool-grey">Questions about the methodology?</p>
              <Link to="/feedback" className="font-body text-[14px] text-soft-gold hover:text-bright-gold transition-colors mt-1 inline-block">
                Contact the Daanaa team →
              </Link>
            </div>
            <div className="flex gap-6">
              <Link to="/how-it-works" className="font-body text-[14px] text-cool-grey hover:text-deep-navy transition-colors">
                How It Works
              </Link>
              <Link to="/tiers" className="font-body text-[14px] text-cool-grey hover:text-deep-navy transition-colors">
                Visibility Levels
              </Link>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
