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
            detail="How well-known is this organization? Ranges from Spark to Beacon (most visible). This tier is about discovery — helps you find orgs you didn't know about."
          />
          <FlowStep
            kicker="Scale 2 · Financial Health"
            title="Find its true peers"
            detail="Same operating model (Food bank, School, Hospital, Foundation, etc.) plus similar revenue size. Creates peer groups where comparison actually makes sense."
          />
          <FlowStep
            kicker="Scale 2 · Measure"
            title="Within-group position"
            detail="Strong = composite above 67 (roughly 18% of orgs). Stable = composite 33–67 (roughly 64%). Inspiring = below 33 (roughly 18%) — doing meaningful work within real constraints. Meaning depends on the model."
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
    'Daanaa scores nonprofits on peer financial context. Every organization is compared only against true peers with the same operating model and revenue size. 1.8 million organizations indexed. Full methodology documented here.'
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
          <p className="mt-3 font-body text-[13px] leading-[1.6] text-soft-gold/80 max-w-[620px] font-medium tracking-[0.01em]">
            Daanaa covers only 501(c)(3) organizations where donor contributions are tax-deductible. Every organization, score, and statistic on this page reflects that universe exclusively.
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
                <span><strong className="text-deep-navy font-medium">Operating model.</strong> How the organization actually runs — whether it delivers direct services, runs programming, holds reserves for surges, or redistributes capital. Nine groups, described below.</span>
              </li>
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">2</span></span>
                <span><strong className="text-deep-navy font-medium">Revenue size.</strong> Five to eight revenue bands, set separately for each operating model from its own distribution. A $20K volunteer group and a $20M healthcare network are not financial peers even if they serve the same community.</span>
              </li>
            </ul>
            <p className="mt-4">
              Together these create 54 peer cells. Every cell has at least 75 organizations — in practice most have thousands. Cells that are too thin use the operating model group as fallback.
            </p>
          </Section>

          <Section label="Step 2a · Operating models" title="Nine groups: sector-specific peer context">
            <p>
              We analyzed 368,000+ tax-deductible nonprofits with financial filings and identified nine operating model groups based on NTEE sector classification and actual financial behavior. Each group has its own financial fingerprint — reserves, program spending, and asset intensity all differ by type of work.
            </p>
            <p className="mt-3">
              Within each operating model, Financial Health tiers have model-specific meanings. This means the system honors how organizations actually work, not how we might assume they should.
            </p>

            <div className="mt-6 space-y-4">
              {[
                {
                  name: 'Activity & Programming',
                  model: 'Activity_Programming',
                  ntee: 'NTEE: A · B · N',
                  orgs: '120,508',
                  reserve: '13.1 mo',
                  prog: '80.1%',
                  desc: 'Schools, museums, theaters, sports leagues, YMCAs, libraries, and cultural venues. Driven by participation revenue, programming fees, and community donations. Strong means broad programming reach and sustained community engagement.',
                  color: 'bg-blue-50 border-blue-200',
                  badge: 'text-blue-700 bg-blue-100',
                  strong: 'Broad programming reach, strong participation-driven revenue',
                },
                {
                  name: 'Direct Delivery',
                  model: 'Direct_Delivery',
                  ntee: 'NTEE: I · J · L',
                  orgs: '34,235',
                  reserve: '13.2 mo',
                  prog: '84.9%',
                  desc: 'Legal aid, employment training, housing providers, and social service agencies funded primarily by government grants and contracts. Every dollar goes toward direct delivery. Strong means solid program efficiency and financial runway for the mission.',
                  color: 'bg-rose-50 border-rose-200',
                  badge: 'text-rose-700 bg-rose-100',
                  strong: 'Solid program efficiency and financial runway for the mission',
                },
                {
                  name: 'Community & Human Services',
                  model: 'Community_Human_Services',
                  ntee: 'NTEE: O · P · S',
                  orgs: '78,812',
                  reserve: '11.5 mo',
                  prog: '81.3%',
                  desc: 'Youth development, family services, community improvement, and broad human service organizations. Donation and grant-funded, serving diverse community needs. Strong means program efficiency and financial resilience across service lines.',
                  color: 'bg-emerald-50 border-emerald-200',
                  badge: 'text-emerald-700 bg-emerald-100',
                  strong: 'Program efficiency, financial resilience across service lines',
                },
                {
                  name: 'Clinical & Health',
                  model: 'Clinical_Reimbursement',
                  ntee: 'NTEE: E · F · G · H',
                  orgs: '37,932',
                  reserve: '11.0 mo',
                  prog: '83.5%',
                  desc: 'Hospitals, clinics, mental health centers, disease organizations, and medical research bodies. Revenue flows from insurance reimbursements and Medicaid. Capital-intensive and regulated. Strong means stable reimbursement coverage and healthy operating reserves.',
                  color: 'bg-indigo-50 border-indigo-200',
                  badge: 'text-indigo-700 bg-indigo-100',
                  strong: 'Strong reimbursement coverage and healthy operating reserves',
                },
                {
                  name: 'Emergency & Logistics',
                  model: 'Emergency_Logistics',
                  ntee: 'NTEE: K · M',
                  orgs: '15,828',
                  reserve: '26.8 mo',
                  prog: '86.0%',
                  desc: 'Food banks, food pantries, disaster relief organizations, and public safety nonprofits. Revenue cycles around grants and emergency funding. Higher reserves fund surge capacity — holding buffer is part of the mission. Strong means strong surge capacity and reserve depth for response cycles.',
                  color: 'bg-orange-50 border-orange-200',
                  badge: 'text-orange-700 bg-orange-100',
                  strong: 'Strong surge capacity and reserve depth for response cycles',
                },
                {
                  name: 'Cause, Advocacy & Research',
                  model: 'Cause_Advocacy_Research',
                  ntee: 'NTEE: C · D · Q · R · U · V',
                  orgs: '28,745',
                  reserve: '13.9 mo',
                  prog: '81.0%',
                  desc: 'Environmental groups, animal welfare organizations, international development, civil rights advocates, think tanks, and scientific research bodies. Donation-driven with advocacy overhead. Strong means well-resourced mission and strong organizational staying power.',
                  color: 'bg-cyan-50 border-cyan-200',
                  badge: 'text-cyan-700 bg-cyan-100',
                  strong: 'Well-resourced mission and strong organizational staying power',
                },
                {
                  name: 'Intermediary & Philanthropy',
                  model: 'Intermediary_Public_Benefit',
                  ntee: 'NTEE: T · W',
                  orgs: '25,822',
                  reserve: '22.2 mo',
                  prog: '82.9%',
                  desc: 'Community foundations, United Way affiliates, grantmaking bodies, and public benefit intermediaries. Hold and deploy capital on behalf of the charitable sector. Strong means effective grant deployment and strong organizational reserves.',
                  color: 'bg-purple-50 border-purple-200',
                  badge: 'text-purple-700 bg-purple-100',
                  strong: 'Effective grant deployment with strong organizational reserves',
                },
                {
                  name: 'Faith Community',
                  model: 'Faith_Community',
                  ntee: 'NTEE: X',
                  orgs: '16,691',
                  reserve: '12.3 mo',
                  prog: '84.8%',
                  desc: 'Congregations, parishes, religious ministries, and mission-driven faith-based organizations. Funded primarily through congregational giving. Community-anchored with member support. Strong means mission vitality supported by sustained congregational giving.',
                  color: 'bg-amber-50 border-amber-200',
                  badge: 'text-amber-700 bg-amber-100',
                  strong: 'Mission vitality supported by sustained congregational giving',
                },
                {
                  name: 'Membership & Mutual Benefit',
                  model: 'Membership_Mutual_Benefit',
                  ntee: 'NTEE: Y · Z',
                  orgs: '9,785',
                  reserve: '34.5 mo',
                  prog: '67.6%',
                  desc: 'Fraternal orders, mutual benefit societies, and civic membership organizations. Member-driven revenue with long-term capital preservation. High reserves are the norm — these organizations hold assets on behalf of their members. Strong means active member engagement and long-term reserve depth.',
                  color: 'bg-slate-50 border-slate-200',
                  badge: 'text-slate-700 bg-slate-100',
                  strong: 'Active member-driven revenue and long-term reserve depth',
                },
              ].map(g => (
                <div key={g.name} className={`p-5 rounded-xl border ${g.color}`}>
                  <div className="flex flex-wrap items-center gap-3 mb-3">
                    <span className={`font-body text-[12px] font-semibold px-2 py-0.5 rounded-full ${g.badge}`}>{g.name}</span>
                    <span className="font-body text-[11px] text-cool-grey/60 font-mono">{g.model}</span>
                    <span className="font-body text-[11px] text-cool-grey/50">{g.ntee}</span>
                    <span className="ml-auto font-body text-[12px] text-cool-grey">{g.orgs} organizations</span>
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

          <Section label="Step 2b · Revenue bands" title="Model-specific bands, not universal sizes">
            <p>
              Revenue bands are model-specific. Larger models (Activity &amp; Programming, Direct Delivery, Community &amp; Human Services) have eight bands for finer peer resolution. Smaller models have five. Breakpoints are derived from each model's own distribution — so sector realities, not arbitrary thresholds, set the groupings.
            </p>
            <p className="mt-3">
              Notice how the thresholds shift across models. A $300K community org sits in band 6; a clinical org at the same revenue is in band 3. Scroll right to explore all nine models.
            </p>

            <div className="mt-6 overflow-x-auto rounded-xl border border-light-grey bg-white">
              <table className="text-left border-collapse" style={{ minWidth: '1060px' }}>
                <thead>
                  <tr className="border-b border-light-grey bg-deep-navy/[0.02]">
                    <th className="py-3 px-3 font-body text-[10px] font-semibold tracking-[0.06em] text-cool-grey/60 uppercase whitespace-nowrap sticky left-0 bg-deep-navy/[0.02] z-10">Band</th>
                    {[
                      { label: 'Activity', color: 'text-blue-600' },
                      { label: 'Direct Svc', color: 'text-rose-600' },
                      { label: 'Community', color: 'text-emerald-600' },
                      { label: 'Clinical', color: 'text-indigo-600' },
                      { label: 'Emergency', color: 'text-orange-600' },
                      { label: 'Cause/Research', color: 'text-cyan-600' },
                      { label: 'Intermediary', color: 'text-purple-600' },
                      { label: 'Faith', color: 'text-amber-600' },
                      { label: 'Membership', color: 'text-slate-600' },
                    ].map(h => (
                      <th key={h.label} className={`py-3 px-3 font-body text-[10px] font-semibold tracking-[0.06em] uppercase whitespace-nowrap ${h.color}`}>{h.label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { band: '1', vals: ['under $27K','under $46K','under $31K','under $57K','under $60K','under $42K','under $50K','under $47K','under $45K'] },
                    { band: '2', vals: ['$27K–$52K','$46K–$83K','$31K–$61K','$57K–$137K','$60K–$106K','$42K–$91K','$50K–$117K','$47K–$92K','$45K–$100K'] },
                    { band: '3', vals: ['$52K–$76K','$83K–$134K','$61K–$100K','$137K–$356K','$106K–$187K','$91K–$173K','$117K–$278K','$92K–$157K','$100K–$258K'] },
                    { band: '4', vals: ['$76K–$110K','$134K–$228K','$100K–$162K','$356K–$1.86M','$187K–$459K','$173K–$460K','$278K–$1.33M','$157K–$373K','$258K–$1.54M'] },
                    { band: '5', vals: ['$110K–$165K','$228K–$416K','$162K–$271K','over $1.86M','over $459K','over $460K','over $1.33M','over $373K','over $1.54M'] },
                    { band: '6', vals: ['$165K–$284K','$416K–$903K','$271K–$514K','—','—','—','—','—','—'] },
                    { band: '7', vals: ['$284K–$828K','$903K–$2.25M','$514K–$1.38M','—','—','—','—','—','—'] },
                    { band: '8', vals: ['over $828K','over $2.25M','over $1.38M','—','—','—','—','—','—'] },
                  ].map((r, i) => (
                    <tr key={r.band} className={`border-b border-light-grey last:border-0 ${i % 2 === 1 ? 'bg-deep-navy/[0.015]' : ''}`}>
                      <td className={`py-2 px-3 font-body text-[12px] font-semibold text-deep-navy whitespace-nowrap sticky left-0 z-10 ${i % 2 === 1 ? 'bg-[#f5f4f0]' : 'bg-white'}`}>
                        {i === 0 ? '1 · Smallest' : i === 7 ? '8 · Largest' : r.band}
                      </td>
                      {r.vals.map((v, j) => (
                        <td key={j} className={`py-2 px-3 font-body text-[12px] whitespace-nowrap ${v === '—' ? 'text-cool-grey/30' : 'text-cool-grey'}`}>{v}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 font-body text-[13px] text-cool-grey/70">
              Breakpoints are computed in log-revenue space from each model's own distribution. Models with 5 bands have smaller populations — five bands still produce balanced, meaningful peer cells.
            </p>

            <Callout>
              Larger models use 8 bands (Activity, Direct Service, Community); smaller models use 5. All are computed in log-revenue space, which ensures:
              <ul className="list-none mt-2 space-y-1">
                <li className="flex gap-2 text-[14px]"><span>•</span> <span>Balanced peer cells (roughly equal populations per band)</span></li>
                <li className="flex gap-2 text-[14px]"><span>•</span> <span>Outliers don't distort boundaries (log-space math)</span></li>
                <li className="flex gap-2 text-[14px]"><span>•</span> <span>Sector-specific breakpoints — sector realities, not artificial thresholds</span></li>
              </ul>
            </Callout>
          </Section>

          <Section label="Step 3 · The formula" title="Composite score to Financial Health tiers">
            <p>
              Each metric (program ratio, reserves, revenue sustainability, asset intensity) is ranked as a percentile within the peer cell. A weighted composite of those four metric percentiles is then thresholded to produce the Financial Health tier:
            </p>
            <FormulaBlock>
              <div className="text-deep-navy/80 mb-3 text-[13px] font-semibold text-cool-grey/60 uppercase tracking-wider">Financial Health tiers (composite score 0–100)</div>
              <div className="text-[13px] text-cool-grey/80 mb-2"><strong>Strong (composite ≥ 67):</strong> above-average on the weighted metric blend — roughly 18% of scored orgs</div>
              <div className="text-[13px] text-cool-grey/80 mb-2"><strong>Stable (composite 33–67):</strong> typical range — roughly 64% of scored orgs</div>
              <div className="text-[13px] text-cool-grey/80"><strong>Inspiring (composite &lt; 33):</strong> constrained resources relative to peers — roughly 18% of scored orgs</div>
              <div className="mt-4 text-[13px] text-cool-grey/70 font-semibold uppercase tracking-wider mb-2">Metrics used</div>
              <div className="text-[13px] text-cool-grey/80">program_ratio    — what share of spending goes directly to the mission (vs. admin and overhead)</div>
              <div className="text-[13px] text-cool-grey/80">reserves_ratio   — how many months the org could run if all revenue stopped (capped at 100)</div>
              <div className="text-[13px] text-cool-grey/80">revenue_ratio    — whether revenue covers expenses this year; above 1.0 means the org is not drawing down reserves</div>
              <div className="text-[13px] text-cool-grey/80">asset_intensity  — total assets relative to revenue; high means capital-heavy (land trust, hospital); low means lean delivery (capped at 100)</div>
              <div className="mt-4 text-[13px] text-cool-grey/70 font-semibold uppercase tracking-wider mb-2">Metric weights</div>
              <div className="text-[13px] text-cool-grey/80">program_ratio    35%</div>
              <div className="text-[13px] text-cool-grey/80">reserves_ratio   25%</div>
              <div className="text-[13px] text-cool-grey/80">revenue_ratio    20%</div>
              <div className="text-[13px] text-cool-grey/80">asset_intensity  20%</div>
              <div className="mt-3 text-[12px] text-cool-grey/50">Weights are the same for every operating model. What changes is the peer group: each org is ranked only against true peers, so "Strong" means composite above 67 within that org's exact model and revenue band — roughly the top 18%.</div>
              <div className="mt-2 text-[12px] text-cool-grey/50 italic">Why "Inspiring"? Constrained resources relative to peers do not mean constrained impact. Organizations working within real financial limits often do the most essential community work. The name honors that honestly.</div>
            </FormulaBlock>
            <p className="mt-4">
              The key insight: <strong>comparisons are always within the peer cell.</strong> A food bank with $200K in revenue compares only to other food banks in its revenue band. The top composite score in that peer group gets "Strong" — regardless of absolute revenue size. A $100M hospital follows the same logic: highest composite in its peer group gets "Strong."
            </p>
            <Callout>
              <strong>What about the 0–100 number you might see?</strong> That's the peer rank percentile — where this org stands on overall financial size relative to its peer group. The human-facing tiers (Strong / Stable / Inspiring) use the composite metric score. Both are shown on the profile; they measure different things.
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

          <Section label="Data completeness" title="Four data tiers — transparency about data quality">
            <p>
              Not every organization has the same amount of public financial data. Daanaa scores what exists — and only what exists. No fabrication. Three scoring tiers, plus an unscored group, reflect actual data availability:
            </p>
            <div className="mt-4 space-y-3">
              {[
                {
                  tier: 'Scored: Complete Data',
                  count: '75,733 organizations',
                  desc: 'Full financial fingerprint from IRS Form 990: revenue, expenses, assets, net assets, reserves, program spending %. All four metrics present. Financial Health tier assigned with full confidence. All are tax-deductible 501(c)(3) organizations.',
                  color: 'border-emerald-300 bg-emerald-50',
                },
                {
                  tier: 'In Pipeline: Partial Data',
                  count: '~496,000 organizations',
                  desc: 'Revenue and expense data on file from IRS records, but not yet run through the scoring pipeline. All are tax-deductible 501(c)(3) organizations. Scoring is ongoing — these organizations will receive a Financial Health tier as the pipeline processes them.',
                  color: 'border-amber-300 bg-amber-50',
                },
                {
                  tier: 'Unscored: No Financial Data',
                  count: '~1.25 million organizations',
                  desc: 'Indexed by IRS but lacking revenue and expense data. Shown with name, location, mission, and cause type. No Financial Health tier is assigned — we never fabricate what we cannot measure. Organizations can claim their page and add financial data to get scored.',
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
              <strong>Help us score the unscored:</strong> Organizations in the unscored group can{' '}
              <Link to="/for-nonprofits" className="text-soft-gold hover:text-bright-gold transition-colors font-medium">claim their page and add financial data</Link>. Once verified, they receive a Financial Health tier and appear in scored search results.
            </p>
          </Section>

          <Section label="How we built this" title="The research behind nine operating models">
            <p>
              The nine operating model groups were discovered, not invented. We analyzed 368,000+ tax-deductible nonprofits with financial filings and measured their actual financial behavior — reserves, program spending, and asset intensity — across NTEE sector classifications.
            </p>
            <p>
              The methodology is rigorous and transparent:
            </p>
            <ul className="list-none space-y-3 mt-3">
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">1</span></span>
                <span><strong>Operating models:</strong> We identified nine distinct groups based on their financial fingerprints (reserves, program spending, asset intensity) and NTEE sector structure.</span>
              </li>
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">2</span></span>
                <span><strong>Revenue bands:</strong> Larger models get eight bands; smaller models get five. All computed in log-revenue space — balanced peer cells, outliers don't distort boundaries.</span>
              </li>
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">3</span></span>
                <span><strong>Peer cells:</strong> Each (model, band) combination is a peer cell — 54 total. Every cell has at least 75 organizations, enough to make composite scores meaningful and stable.</span>
              </li>
              <li className="flex gap-3">
                <span className="shrink-0 w-5 h-5 rounded-full bg-soft-gold/20 flex items-center justify-center mt-[2px]"><span className="text-[10px] font-semibold text-soft-gold">4</span></span>
                <span><strong>Financial Health tiers:</strong> The weighted composite score (0–100) is thresholded at 67 and 33. Above 67 = Strong, 33–67 = Stable, below 33 = Inspiring. Natural distribution is approximately 18% / 64% / 18% — not forced equal thirds.</span>
              </li>
            </ul>
            <p className="mt-4">
              <strong>Why this matters:</strong> A small food bank (Inspiring tier) is doing meaningful work within real constraints — compared only to other food banks at a similar size. A $2 million food bank can be Strong within its own peer group without diminishing the smaller one. No universal yardstick. Context for every org.
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
                detail="Tax-exempt status, organization name, state, and category code. Updated quarterly by the IRS. Daanaa indexes 1.8 million active 501(c)(3) nonprofits where donor contributions are tax-deductible. Organizations in any other tax-exempt category are not included."
              />
              <SourceRow
                source="IRS published financial data"
                detail="Financial data from aggregated annual filings, including total revenue and total assets. Available for approximately 471,000 organizations with recent data."
              />
              <SourceRow
                source="ProPublica Nonprofit Explorer"
                detail="Mission statements, website URLs, and annual filing detail. Used to fill in financial data and confirm profile completeness for the visibility tier."
              />
              <SourceRow
                source="NCCS (Urban Institute)"
                detail="Supplementary category codes and historical filing data."
              />
              <SourceRow
                source="IRS Automatic Revocation List"
                detail="The IRS publishes a list of organizations whose tax-exempt status was automatically revoked for failure to file for three or more consecutive years. Daanaa checks every indexed organization against this list monthly. Revoked organizations are removed from donation paths."
              />
            </div>
            <Callout>
              Data currency varies by source. The IRS registration list is updated quarterly. 990 financials reflect the most recent filing on record, which may be 1 to 3 years behind the current fiscal year. Score dates reflect when Daanaa last processed the available data, not when the organization filed.
            </Callout>
          </Section>

          <Section label="Apply this" title="Reading a profile — what you'll see">
            <p>
              Every concept in this methodology maps directly to something visible on an organization's profile page. Here's how to read what you find:
            </p>
            <div className="mt-5 space-y-3">
              {[
                {
                  what: 'Lamp tier (Beacon, Torch, Candle, Spark)',
                  means: 'How much public data backs this profile today. Beacon = complete (financials, mission, website, current 990). Torch = strong public data (financials, recent filings). Candle = moderate data (some financial info, organizational records). Spark = recognized nonprofit with minimal public records. It is a journey signal, not a quality verdict.',
                },
                {
                  what: 'Financial Health tier (Strong / Stable / Inspiring)',
                  means: 'Where this organization stands within its exact peer group on a weighted composite of four metrics. Always peer-relative — a Strong food bank is strong among food banks at the same revenue size, not compared to hospitals. Roughly 18% Strong, 64% Stable, 18% Inspiring.',
                },
                {
                  what: 'Peer rank (0–100 number)',
                  means: 'Financial scale relative to the peer group. 90 means this org is financially larger than 90% of similar organizations. Separate from Financial Health — a large org can be Inspiring; a small org can be Strong.',
                },
                {
                  what: 'Months net assets cover costs',
                  means: 'Net assets divided by monthly expenses. This measures financial depth relative to the operating model — not a pure liquidity signal. Assets are part of how organizations carry out their work (a hospital\'s building, a land trust\'s holdings). High is not always better; it depends on the model.',
                },
                {
                  what: 'IRS status verified [Month Year]',
                  means: 'The date Daanaa last confirmed this organization against the IRS automatic revocation list. Active nonprofit status verified as of that date. Organizations with revoked status are removed from all donation paths.',
                },
                {
                  what: 'Data source and year',
                  means: 'Every financial figure on the profile is labeled with its source (IRS, ProPublica) and the tax year it reflects. Older data is always flagged — you are never guessing how current the information is.',
                },
              ].map(item => (
                <div key={item.what} className="flex gap-4 p-4 bg-white rounded-lg border border-light-grey">
                  <div className="shrink-0 w-2 h-2 mt-[7px] rounded-full bg-soft-gold" />
                  <div>
                    <p className="font-body text-[14px] font-semibold text-deep-navy">{item.what}</p>
                    <p className="font-body text-[14px] text-cool-grey mt-1 leading-[1.6]">{item.means}</p>
                  </div>
                </div>
              ))}
            </div>
            <Callout>
              The methodology exists so you can trust what you read. Every signal on a profile is traceable back to a public IRS record or a documented calculation. If something looks wrong, the feedback link at the bottom of every profile goes straight to us.
            </Callout>
            <div className="mt-6 flex flex-wrap gap-6">
              <Link
                to="/directory"
                className="inline-flex items-center gap-1.5 font-body text-[14px] font-semibold text-soft-gold hover:text-bright-gold transition-colors"
              >
                Browse the directory →
              </Link>
              <Link
                to="/how-it-works"
                className="inline-flex items-center gap-1.5 font-body text-[14px] font-semibold text-cool-grey hover:text-deep-navy transition-colors"
              >
                Back to How It Works →
              </Link>
            </div>
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
              <Link to="/directory" className="font-body text-[14px] text-cool-grey hover:text-deep-navy transition-colors">
                Browse Directory
              </Link>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
