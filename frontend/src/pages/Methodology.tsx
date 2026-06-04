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
            Peer financial context is a public data signal. It does not measure impact, trustworthiness, leadership, governance, program quality, or whether a group deserves support. Every number compares a nonprofit against others doing similar work at a similar size, using public IRS filings. No black boxes. Everything is documented below.
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
                Each nonprofit is scored only against organizations with the same operating model and similar revenue size. A food bank is measured against other food banks — not hospitals. A conservation land trust is measured against other land trusts — not community centers. The score, 0 to 100, shows where an organization stands within that peer group.
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

          <Section label="Step 1 · Operating models" title="Four groups, not one size fits all">
            <p>
              We analyzed 356,000 nonprofits with complete financial filings and found four statistically distinct operating models (ANOVA F = 9,781, p &lt; 0.001, η² = 9.2%). Each group has a different relationship between reserves, assets, and program spending — so each group gets its own benchmarks.
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

          <Section label="Step 2 · The formula" title="How the score is built">
            <p>
              Each org receives up to four percentile ranks within its peer cell — how it compares to its peers on revenue, reserves, assets, and program spending. These are combined into a single 0–100 score using weights that vary by operating model.
            </p>
            <FormulaBlock>
              <div className="text-deep-navy/80 mb-2 text-[13px] font-semibold text-cool-grey/60 uppercase tracking-wider">Metrics used</div>
              <div className="text-deep-navy/80">revenue_rank     — total annual revenue within peer cell</div>
              <div className="text-deep-navy/80">reserve_rank     — operating reserves (months of expenses covered)</div>
              <div className="text-deep-navy/80">asset_rank       — total assets relative to revenue</div>
              <div className="text-deep-navy/80">program_rank     — share of spending that goes to programs</div>
              <div className="mt-4 text-[13px] text-cool-grey/70 font-semibold uppercase tracking-wider mb-2">Weights by operating model</div>
              <div className="text-[13px] text-cool-grey/80">Direct Service      revenue 30%  reserve 25%  assets 10%  programs 35%</div>
              <div className="text-[13px] text-cool-grey/80">Mission Infra.      revenue 30%  reserve 35%  assets 10%  programs 25%</div>
              <div className="text-[13px] text-cool-grey/80">Asset Stewards      revenue 30%  reserve 15%  assets 40%  programs 15%</div>
              <div className="text-[13px] text-cool-grey/80">Endowment &amp; Capital revenue 30%  reserve  0%  assets 55%  programs 15%</div>
              <div className="mt-3 text-[12px] text-cool-grey/50">Reserve excluded from Endowment & Capital scoring — the IRS data caps reserves at 120 months, masking the true depth of endowment holdings.</div>
            </FormulaBlock>
            <p>
              The middle organization in every peer cell scores 50. A 75 means the same thing across all groups: top quarter of true peers. Weights reflect what financial health actually means for each model — a food bank with thin reserves may be doing exactly what it should, while a land trust with thin reserves may have a real problem.
            </p>
            <Callout>
              When program spending data is unavailable for an org (not all 990 filings include this breakdown), its weight is redistributed across the other metrics. The score is always based only on data that actually exists.
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

          <Section label="Score availability" title="Three levels of data — three levels of display">
            <p>
              Not every organization has the same amount of public financial data. Daanaa displays what exists — and only what exists.
            </p>
            <div className="mt-4 space-y-3">
              {[
                {
                  tier: 'Scored',
                  count: '458,000 organizations',
                  desc: 'Complete IRS 990 filing data. Full 0–100 peer financial context score, operating model group, and financial profile.',
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
                  desc: 'IRS recognized and donation eligible. No detailed financial filing data available — most are small organizations that file a simplified postcard return, or churches that are not required to file. Shown with IRS standing, cause type, and profile information. No financial score.',
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

          <Section label="How we built this" title="The research behind the peer groups">
            <p>
              The four operating model groups did not come from assumption. We looked at 356,000 nonprofits with complete financial filings and measured their actual financial behavior across three dimensions: how many months of expenses their reserves would cover, how much of their balance sheet is tied up in assets relative to revenue, and how much of their spending goes directly to programs.
            </p>
            <p>
              The data clustered naturally into four groups with statistically distinct financial profiles. A one-way analysis of variance across the groups produced an F statistic of 9,781 with p below 0.001, confirming that the differences between groups are real and not the result of chance. The groups explain about 9 percent of the total variation in reserve behavior across the sector — meaningful for a classification built entirely from financial ratios.
            </p>
            <p>
              Each cause type was assigned to the group whose financial fingerprint it most closely matched. Where a cause spans multiple models by size (a small volunteer fire department looks very different from a large professional emergency service), the revenue band captures that within the group. The assignment is based on data, not editorial judgment.
            </p>
            <Callout>
              This methodology will be reviewed quarterly as IRS data refreshes. If the financial fingerprint of a cause type shifts meaningfully over time, its group assignment will be updated and all affected scores recomputed. The goal is that the peer groups always reflect how organizations actually operate, not how we expect them to.
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
