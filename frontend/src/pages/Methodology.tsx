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
          How the two scales work
        </h2>
        <p className="font-body text-[16px] text-cool-grey leading-[1.7] mb-9">
          Visibility shows prominence. Financial Health shows peer context. Together they give a complete picture.
        </p>
        <div className="flex flex-col items-center">
          <FlowStep
            kicker="Scale 1 · Visibility"
            title="Public prominence"
            detail="How well-known is this organization? Ranges from Just Starting to Blazing (most visible). This tier is about discovery — helps you find orgs you didn't know about."
          />
          <FlowStep
            kicker="Scale 2 · Financial Health"
            title="Find its true peers"
            detail="Same operating model (Food bank, School, Hospital, Foundation, etc.) plus similar revenue size. Creates peer groups where comparison actually makes sense."
          />
          <FlowStep
            kicker="Scale 2 · Measure"
            title="Within-group position"
            detail="Strong = top third of peer group. Stable = middle third. Inspiring = bottom third — doing remarkable work within constraints. Meaning depends on the model."
          />
          <FlowStep
            kicker="Together"
            title="Context, not verdict"
            detail="A famous org that's struggling. An overlooked org that's thriving. Two scales show both sides."
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
    'Daanaa scores nonprofits on peer financial context. Every organization is compared only against true peers with the same operating model and revenue size. 1.6 million organizations indexed. Full methodology documented here.'
  )
  const { data: stats } = useApi(() => getStats(), [])
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
            Every nonprofit is measured only against its true peers — organizations with the same operating model and similar revenue size. A food bank is compared to food banks, not hospitals. A foundation is compared to foundations. Financial Health tiers reflect where each org stands within its actual peer group. No universal yardstick. Everything is based on IRS public data.
          </p>
          <div className="mt-7">
            <p className="font-body text-[10px] font-medium tracking-[0.12em] text-soft-gold/60 uppercase mb-1.5">
              Scores last computed
            </p>
            <span className="font-mono text-[14px] text-warm-cream bg-white/5 px-3 py-1 rounded-full border border-white/10">
              {scoresUpdated}
            </span>
          </div>
          <p className="mt-5 font-body text-[13px] leading-[1.6] text-muted-cream/70 max-w-[620px]">
            Scores are recomputed as new IRS filings become available. A new score date reflects fresh data, not a formula change.
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
                Every nonprofit gets two independent scales. The first (Visibility) shows public prominence. The second (Financial Health) shows where it stands within its peer group.
              </p>
              <p className="mt-3 font-body text-[16px] text-cool-grey leading-[1.7]">
                <strong className="text-deep-navy font-medium">Financial Health tiers</strong> have model-specific meanings. For a food bank, "Strong" means high program efficiency and resource leverage. For a foundation, "Strong" means active, sustained grant deployment. Same word, different context — because the organizations are genuinely different.
              </p>
              <p className="mt-3 font-body text-[15px] text-cool-grey leading-[1.7]">
                All data comes from annual IRS filings — the same public documents every registered 501(c)(3) submits. Organizations without detailed filing data are shown without a score. We never fabricate what we cannot measure.
              </p>
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
              We never compare a food bank to a hospital, or a grassroots group to a major university. Every nonprofit is scored only against organizations with the same operating model at a similar size. A peer group is two things:
            </p>
            <ul className="list-none space-y-2 mt-2">
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">1</span></span>
                <span><strong className="text-deep-navy font-medium">Operating model.</strong> How the organization actually runs — whether it spends everything on direct service delivery, owns physical assets central to its mission, or holds capital over many years. Four groups, described below.</span>
              </li>
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">2</span></span>
                <span><strong className="text-deep-navy font-medium">Revenue size.</strong> One of six bands from Nano (under $25K) to Major ($50M+). A $20K volunteer group and a $20M healthcare network are not financial peers even if they serve the same community.</span>
              </li>
            </ul>
            <p className="mt-4">
              Together these create 24 peer cells. Every cell has at least 30 organizations — in practice most have thousands. Cells that are too thin use the operating model group as fallback.
            </p>
          </Section>

          <Section label="Step 2 · Operating models" title="Eight groups: sector-specific peer context">
            <p>
              We analyzed 71,473 nonprofits with complete financial filings and found eight statistically distinct operating models. Each group has its own financial fingerprint — reserves, program spending, asset intensity all differ by type of work.
            </p>
            <p className="mt-3">
              Within each operating model, Financial Health tiers have model-specific meanings. This means the system honors how organizations actually work, not how we might assume they should work.
            </p>

            <div className="mt-6 space-y-4">
              {[
                {
                  name: 'Direct Service',
                  orgs: '22,916',
                  reserve: '10.3 mo',
                  prog: '37.3%',
                  desc: 'Food banks, job training, animal rescue, emergency response, mental health services. Lean by design — deploys resources directly into programs. Strong means high program efficiency. Inspiring means doing remarkable work within constraints.',
                  color: 'bg-emerald-50 border-emerald-200',
                  badge: 'text-emerald-700 bg-emerald-100',
                  strong: 'High program efficiency, resource leverage',
                },
                {
                  name: 'Mission Infrastructure',
                  orgs: '26,413',
                  reserve: '13.4 mo',
                  prog: '40.4%',
                  desc: 'Schools, hospitals, health systems, arts organizations, libraries. Assets support program delivery. Strong means reserves supporting stable operations. Inspiring means visionary impact within constraints.',
                  color: 'bg-blue-50 border-blue-200',
                  badge: 'text-blue-700 bg-blue-100',
                  strong: 'Reserves support stable operations',
                },
                {
                  name: 'Research & Academia',
                  orgs: '10,729',
                  reserve: '8.8 mo',
                  prog: '66.1%',
                  desc: 'Universities, medical research, scientific institutions. Program-heavy (includes grant passthrough). Strong means well-funded pipelines. Inspiring means innovative work on limited resources.',
                  color: 'bg-indigo-50 border-indigo-200',
                  badge: 'text-indigo-700 bg-indigo-100',
                  strong: 'Well-funded pipelines, stable base',
                },
                {
                  name: 'Foundations',
                  orgs: '3,266',
                  reserve: '34.3 mo',
                  prog: '34.2%',
                  desc: 'Grantmakers, endowments, philanthropies. Hold and deploy capital. Strong means active, sustained grant deployment. Inspiring means emerging foundations building capacity.',
                  color: 'bg-purple-50 border-purple-200',
                  badge: 'text-purple-700 bg-purple-100',
                  strong: 'Active, sustained grant deployment',
                },
                {
                  name: 'Membership & Advocacy',
                  orgs: '2,940',
                  reserve: '8.4 mo',
                  prog: '33.1%',
                  desc: 'Member organizations, advocacy networks, voluntarism centers. Revenue driven by membership support. Strong means healthy member-revenue base. Inspiring means growing member engagement.',
                  color: 'bg-rose-50 border-rose-200',
                  badge: 'text-rose-700 bg-rose-100',
                  strong: 'Healthy member-revenue base',
                },
                {
                  name: 'Religion & Spiritual',
                  orgs: '3,764',
                  reserve: '20.2 mo',
                  prog: '14.2%',
                  desc: 'Faith communities, congregations, spiritual organizations. Often volunteer-heavy. Strong means strong financial reserves and impact. Inspiring means growing congregation and mission.',
                  color: 'bg-amber-50 border-amber-200',
                  badge: 'text-amber-700 bg-amber-100',
                  strong: 'Strong financial reserves, impact',
                },
                {
                  name: 'International Development',
                  orgs: '601',
                  reserve: '9.5 mo',
                  prog: '27.2%',
                  desc: 'Cross-border development, humanitarian aid, international relief. Strong means efficient cross-border delivery. Inspiring means scaling operations with vision.',
                  color: 'bg-cyan-50 border-cyan-200',
                  badge: 'text-cyan-700 bg-cyan-100',
                  strong: 'Efficient cross-border delivery',
                },
                {
                  name: 'Asset Stewards',
                  orgs: '844',
                  reserve: '11.4 mo',
                  prog: '42.3%',
                  desc: 'Nursing homes, hospitals, facilities. Physical assets are central. Strong means well-maintained assets and healthy reserves. Inspiring means growing asset base with impact.',
                  color: 'bg-orange-50 border-orange-200',
                  badge: 'text-orange-700 bg-orange-100',
                  strong: 'Assets well-maintained, healthy reserves',
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
                      { label: 'Strong means', value: g.strong, wide: true },
                    ].map(stat => (
                      <div key={stat.label} className={stat.wide ? 'flex-grow' : ''}>
                        <p className="font-body text-[10px] font-medium tracking-[0.08em] text-cool-grey/60 uppercase">{stat.label}</p>
                        <p className="font-body text-[13px] text-deep-navy">{stat.value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <Callout>
              Financial Health is always peer-relative. An organization's tier shows how it compares to others in its exact group. An "Inspiring" food bank doing $100K in revenue is within its true peers — not being judged against hospitals. This is how fairness works.
            </Callout>
          </Section>

          <Section label="Step 2 · Revenue bands" title="Eight model-specific bands, not universal sizes">
            <p>
              Revenue bands are now model-specific. Each operating model gets its own eight revenue breakpoints based on its natural distribution. This means a "Small" food bank is sized appropriately compared to other food banks — not forced into brackets built for hospitals.
            </p>
            <p className="mt-3">
              For example, Direct Service bands range from under $27.5K to over $1.47M. Foundations bands range from under $23.7K to over $692K. Different sectors, different natural breaking points. Same principle: organizations are grouped only with true peers.
            </p>
            <Callout>
              All revenue bands are octile-based (8 equal percentiles in log-revenue space). This ensures:
              <ul className="list-none mt-2 space-y-1">
                <li className="flex gap-2 text-[14px]"><span>•</span> <span>Roughly 12.5% of orgs per band (balanced peer cells)</span></li>
                <li className="flex gap-2 text-[14px]"><span>•</span> <span>Outliers don't distort boundaries (log-space math)</span></li>
                <li className="flex gap-2 text-[14px]"><span>•</span> <span>Sector-specific breakpoints (sector realities, not artificial)</span></li>
              </ul>
            </Callout>
            <p className="mt-4">
              See <Link to="/" className="text-soft-gold hover:text-bright-gold transition-colors">Operating-Models-V4.md</Link> documentation for complete band tables per model.
            </p>
          </Section>

          <Section label="Step 3 · The formula" title="Percentile rank to Financial Health tiers">
            <p>
              Each organization receives a percentile rank within its exact peer cell (operating model + revenue band). This percentile is then mapped to a Financial Health tier:
            </p>
            <FormulaBlock>
              <div className="text-deep-navy/80 mb-3 text-[13px] font-semibold text-cool-grey/60 uppercase tracking-wider">Financial Health tiers</div>
              <div className="text-[13px] text-cool-grey/80 mb-2"><strong>Top third (67–100th percentile):</strong> Strong</div>
              <div className="text-[13px] text-cool-grey/80 mb-2"><strong>Middle third (33–67th percentile):</strong> Stable</div>
              <div className="text-[13px] text-cool-grey/80"><strong>Bottom third (0–33rd percentile):</strong> Inspiring</div>
              <div className="mt-4 text-[13px] text-cool-grey/70 font-semibold uppercase tracking-wider mb-2">Metrics used</div>
              <div className="text-[13px] text-cool-grey/80">program_ratio    — program expenses as % of total spending</div>
              <div className="text-[13px] text-cool-grey/80">reserves_ratio   — months of operating reserves (capped at 100)</div>
              <div className="text-[13px] text-cool-grey/80">revenue_ratio    — revenue vs. expenses (sustainability)</div>
              <div className="text-[13px] text-cool-grey/80">asset_intensity  — total assets relative to revenue (capped at 100)</div>
              <div className="mt-4 text-[13px] text-cool-grey/70 font-semibold uppercase tracking-wider mb-2">Weights by operating model</div>
              <div className="text-[13px] text-cool-grey/80">Direct Service        program 35%  reserve 25%  revenue 20%  assets 20%</div>
              <div className="text-[13px] text-cool-grey/80">Mission Infrastructure program 35%  reserve 25%  revenue 20%  assets 20%</div>
              <div className="text-[13px] text-cool-grey/80">Research / Academia   program 35%  reserve 25%  revenue 20%  assets 20%</div>
              <div className="text-[13px] text-cool-grey/80">All other models      program 35%  reserve 25%  revenue 20%  assets 20%</div>
              <div className="mt-3 text-[12px] text-cool-grey/50">Weights are consistent across all models. Peer-relative percentiles ensure that a "Strong" tier always means top-third within that org's true peers.</div>
            </FormulaBlock>
            <p className="mt-4">
              The key insight: <strong>percentile ranks are outlier-proof.</strong> A food bank with $200K in revenue compares only to other $100K–$500K food banks. The top quarter of that peer group gets "Strong" — regardless of absolute revenue size. A $100M hospital follows the same logic: top quarter of its peer group gets "Strong."
            </p>
            <Callout>
              <strong>What about the 0–100 number you might see?</strong> That's a percentile rank (0–100 scale) for technical purposes. The human-facing tiers are Strong / Stable / Inspiring. Both show the same information — one is granular, one is simplified.
            </Callout>
          </Section>

          <Section label="Scope and limits" title="What the score does and doesn't measure">
            <p>
              The score is a narrow measure of financial resources relative to true peers — nothing more. It does not measure, and should not be used to judge:
            </p>
            <ul className="space-y-2 mt-3 list-none">
              {[
                'Program quality, outcomes, or actual impact in the community',
                'Governance, board composition, or leadership quality',
                'Community trust or local reputation',
                'Overhead ratio — the sector formally retired this metric in 2013 (GuideStar, Charity Navigator, BBB Wise Giving Alliance joint letter)',
              ].map(item => (
                <li key={item} className="flex gap-3 items-start">
                  <span className="shrink-0 mt-[7px] w-1.5 h-1.5 rounded-full bg-soft-gold/50" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            <Callout>
              A lower score may reflect how an organization is built, not how well it serves its mission. Pass-through funders, national chapters reporting revenue centrally, and newly formed organizations regularly score in the lower half. That is an accurate description of their position among peers — not a judgment of their worth.
            </Callout>
            <p className="mt-4">
              Several important dimensions exist that IRS data cannot capture. We plan to surface them as supplemental signals over time:
            </p>
            <ul className="space-y-3 mt-3 list-none">
              {[
                {
                  label: 'Volunteer labor',
                  detail: 'IRS 990 Part I reports volunteer counts. The Independent Sector values a volunteer hour at $31.80 (2023). A food pantry with 300 volunteers giving 80 hours each contributes an estimated $763,200 in community labor — often several times its cash budget.',
                },
                {
                  label: 'Community trust and local relationships',
                  detail: 'Not measurable from public records. A deeply trusted neighborhood organization may score modestly on financial metrics while doing irreplaceable work.',
                },
              ].map(item => (
                <li key={item.label} className="flex gap-3 items-start">
                  <span className="shrink-0 mt-[6px] w-1.5 h-1.5 rounded-full bg-soft-gold/30" />
                  <span><strong className="text-deep-navy font-medium">{item.label}.</strong> {item.detail}</span>
                </li>
              ))}
            </ul>
          </Section>

          <Section label="Data completeness" title="Three scoring tiers — transparency about data quality">
            <p>
              Not every organization has the same amount of public financial data. Daanaa scores what exists — and only what exists. No fabrication. Three tiers reflect actual data availability:
            </p>
            <div className="mt-4 space-y-3">
              {[
                {
                  tier: 'Tier A: Complete Data',
                  count: '71,473 organizations',
                  desc: 'Full financial fingerprint from IRS Form 990: revenue, expenses, assets, net assets, reserves, program spending %. All metrics present. Scored with maximum confidence across all four dimensions.',
                  color: 'border-emerald-300 bg-emerald-50',
                },
                {
                  tier: 'Tier B: Deductible, Partial Data',
                  count: '308,517 organizations',
                  desc: 'Revenue + expenses from IRS Form 990, but program expense breakdown missing. Program % derived from sector benchmarks (NTEE-level defaults). Donor-deductible. Fair peer-based Financial Health tier within operating model + revenue band.',
                  color: 'border-amber-300 bg-amber-50',
                },
                {
                  tier: 'Tier C: Non-Deductible, Partial Data',
                  count: '158,243 organizations',
                  desc: 'Revenue + expenses present, but not donor-deductible (unions, professional associations, health plans, mutual benefit orgs). Program % derived from sector benchmarks. Same peer-based methodology as Tier B. Scored fairly within non-deductible peer groups.',
                  color: 'border-rose-300 bg-rose-50',
                },
                {
                  tier: 'Unscored: No Financial Data',
                  count: '~1.2 million organizations',
                  desc: 'Indexed by IRS but lacking revenue/expense data. Shown with: name, location, mission, cause type. Can submit financial data to get scored (self-reporting). Users encouraged to verify directly with organization.',
                  color: 'border-cool-grey/30 bg-warm-cream',
                },
              ].map(t => (
                <div key={t.tier} className={`flex gap-4 p-4 rounded-xl border ${t.color}`}>
                  <div className="shrink-0 w-48">
                    <p className="font-body text-[13px] font-semibold text-deep-navy">{t.tier}</p>
                    <p className="font-body text-[11px] text-cool-grey/70 mt-0.5">{t.count}</p>
                  </div>
                  <p className="font-body text-[14px] text-cool-grey leading-[1.6]">{t.desc}</p>
                </div>
              ))}
            </div>
            <Callout>
              <strong>The absence of a score is honest, not negative.</strong> Tier A is more confident than Tier B/C (fewer estimates). Tier B/C are more confident than unscored (at least we have revenue data). Unscored is always better than fabricated. We show what we know, label what we estimate, and never invent what we don't have.
            </Callout>
            <p className="mt-4">
              <strong>Help us score the unscored:</strong> Organizations in the unscored group can submit their financial data at daanaa.org/submit-data. Once verified (5–7 days), they receive a Financial Health tier and appear in scored search results.
            </p>
          </Section>

          <Section label="How we built this" title="The research behind eight operating models">
            <p>
              The eight operating model groups were discovered, not invented. We analyzed 71,473 nonprofits with complete financial filings — the most complete set available — and measured their actual financial behavior.
            </p>
            <p>
              The methodology is rigorous and transparent:
            </p>
            <ul className="list-none space-y-3 mt-3">
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">1</span></span>
                <span><strong>Operating models:</strong> We identified eight distinct groups based on their financial fingerprints (reserves, program spending, asset intensity).</span>
              </li>
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">2</span></span>
                <span><strong>Revenue bands:</strong> Within each model, we created eight revenue breakpoints (octiles in log-revenue space). This ensures balanced peer cells and prevents outliers from distorting boundaries.</span>
              </li>
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">3</span></span>
                <span><strong>Peer cells:</strong> Each (model, band) combination is a peer cell. All 64 cells have at least 75 organizations — enough to make percentile ranks meaningful and stable.</span>
              </li>
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">4</span></span>
                <span><strong>Financial Health tiers:</strong> Percentile ranks within peer cells are mapped to terciles (thirds): top third = Strong, middle = Stable, bottom = Inspiring. This ensures fair, honest tier distribution.</span>
              </li>
            </ul>
            <p className="mt-4">
              <strong>Why this matters:</strong> A small food bank (Inspiring tier) is inspiring because it's in the bottom third of food bank financial profiles — doing remarkable work within real constraints. A $2 million food bank can be Strong (top third of its peers) without diminishing the smaller one.  No universal yardstick. Context for every org.
            </p>
            <Callout>
              <strong>Fairness is structural in this design.</strong> Every organization is measured only against true peers. No sector dominates the tiers. No size band is pushed to the bottom. The system honors how organizations actually work, not how we might assume they should work.
            </Callout>
          </Section>

          <Section label="Data sources" title="Where the data comes from">
            <p>
              Daanaa draws exclusively from public records. We do not solicit, purchase, or accept data from the organizations we index.
            </p>
            <div className="mt-4">
              <SourceRow
                source="IRS nonprofit registration list"
                detail="Tax-exempt status, organization name, state, and category code. Updated quarterly by the IRS. Daanaa indexes 1.63 million active nonprofits where donations are eligible for a tax deduction. Organizations in other categories are not included in scoring."
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

          <Section label="Future: Interactive discovery" title="Visualizations we're planning">
            <p>
              The methodology behind peer groups is powerful but abstract. We're exploring interactive visualizations that make the structure tangible:
            </p>
            <div className="mt-6 space-y-4">
              {[
                {
                  name: '8×8 Discovery Matrix',
                  desc: 'An interactive grid where each cell is an (operating model × revenue band) peer group. Hover to see peer group size. Click to explore orgs in that cell. Highlighted squares show where searches cluster. Visual proof that small and large orgs exist in every quadrant.',
                  color: 'text-emerald-700',
                },
                {
                  name: 'Manhattan-Style 3D Visualization',
                  desc: 'Each operating model is a "building neighborhood" in 3D space. Floors represent revenue bands. "Tenants" (organizations) are parcels on each floor sized by revenue. Click a floor to see all orgs in that peer group. Rotate the neighborhood to compare models. Shows simultaneously: peer group structure, org size, distribution, and density.',
                  color: 'text-blue-700',
                },
              ].map(v => (
                <div key={v.name} className="p-5 rounded-xl border border-soft-gold/20 bg-soft-gold/5">
                  <p className={`font-body text-[14px] font-semibold ${v.color} mb-2`}>{v.name}</p>
                  <p className="font-body text-[14px] text-cool-grey leading-[1.6]">{v.desc}</p>
                </div>
              ))}
            </div>
            <Callout>
              Both visualizations serve the same purpose: make peer groups visible and queryable. The methodology is defensible; the visualization is what makes it intuitive. We're building these so users can explore the structure themselves instead of reading about it.
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
