import { useEffect, useState, type ReactNode } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  BarChart,
  Bar,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import RelatedPages from '../components/RelatedPages'
import { loadResearchSnapshot, type ResearchSnapshot } from '../data/researchSnapshot'
import { usePageMeta } from '../hooks/usePageMeta'

type ExplorerView = 'coverage' | 'causes' | 'states' | 'revenue' | 'movement'

type ExportRow = {
  key: string
  label: string
  detail: string
  count: number
  share: number
  metricA: string
  metricB: string
  metricC: string
  color: string
  bar: number
}

type ExplorerConfig = {
  key: ExplorerView
  label: string
  description: string
  noDataLabel: string
  buildRows: (snapshot: ResearchSnapshot) => ExportRow[]
  chartKind: 'horizontal' | 'monthly'
  metricALabel: string
  metricBLabel: string
  metricCLabel: string
  note: string
}

const VIEW_ORDER: ExplorerView[] = ['coverage', 'causes', 'states', 'revenue', 'movement']

const VIEW_LABELS: Record<ExplorerView, string> = {
  coverage: 'V6 context',
  causes: 'Cause areas',
  states: 'States',
  revenue: 'Revenue bands',
  movement: 'Monthly movement',
}

const COLORS = {
  navy: '#0A1628',
  cream: '#F5F0EB',
  gold: '#C9A96E',
  goldBright: '#D4B87A',
  goldSoft: '#E8D5A3',
  slate: '#4B5563',
  cool: '#A0AFC3',
  green: '#4ADE80',
  amber: '#F59E0B',
  red: '#EF4444',
}

function parseView(value: string | null): ExplorerView {
  if (value === 'causes' || value === 'states' || value === 'revenue' || value === 'movement') {
    return value
  }
  return 'coverage'
}

function prettyNumber(value: number): string {
  return value.toLocaleString('en-US')
}

function prettyPct(value: number): string {
  return `${value.toFixed(1)}%`
}

function prettyDecimal(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return value.toFixed(digits)
}

function prettyMoney(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: value >= 1000 ? 0 : 1,
  }).format(value)
}

function titleCase(value: string): string {
  return value
    .replace(/_/g, ' ')
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0]?.toUpperCase() + part.slice(1).toLowerCase())
    .join(' ')
}

function searchRow(row: ExportRow, term: string): boolean {
  if (!term) return true
  const haystack = `${row.label} ${row.detail} ${row.metricA} ${row.metricB} ${row.metricC}`
    .toLowerCase()
  return haystack.includes(term.toLowerCase())
}

function csvEscape(value: string): string {
  if (value.includes('"') || value.includes(',') || value.includes('\n')) {
    return `"${value.replace(/"/g, '""')}"`
  }
  return value
}

function makeCsv(viewLabel: string, rows: ExportRow[], snapshot: ResearchSnapshot) {
  const headers = ['view', 'label', 'detail', 'count', 'share', 'metric_a', 'metric_b', 'metric_c']
  const lines = [
    headers.join(','),
    ...rows.map((row) =>
      [
        viewLabel,
        row.label,
        row.detail,
        String(row.count),
        row.share.toFixed(1),
        row.metricA,
        row.metricB,
        row.metricC,
      ]
        .map(csvEscape)
        .join(',')
    ),
  ]
  return [
    '# Daanaa research explorer export',
    `# Snapshot date: ${snapshot.metadata.data_period}`,
    `# Denominator: ${snapshot.metadata.total_organizations}`,
    ...lines,
  ].join('\n')
}

function saveCsv(filename: string, content: string) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.rel = 'noopener'
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function chartColor(index: number, total: number): string {
  if (total <= 1) return COLORS.gold
  const ramp = [COLORS.gold, COLORS.goldBright, COLORS.goldSoft, '#C8A55F', '#D9A876']
  return ramp[index % ramp.length]
}

function buildCoverageRows(snapshot: ResearchSnapshot): ExportRow[] {
  return (snapshot.v6?.tiers || []).map((tier, index) => ({
    key: tier.key,
    label: tier.name,
    detail: tier.description,
    count: tier.count,
    share: tier.pct,
    metricA: tier.has_peer_comparison ? 'Yes' : 'No',
    metricB: tier.avg_peer_group_size ? prettyNumber(Math.round(tier.avg_peer_group_size)) : '—',
    metricC: prettyDecimal(tier.avg_program_pct),
    color: chartColor(index, snapshot.v6?.tiers.length || 1),
    bar: tier.count,
  }))
}

function buildCauseRows(snapshot: ResearchSnapshot): ExportRow[] {
  return [...(snapshot.categories || [])]
    .sort((a, b) => b.count - a.count)
    .map((row, index) => ({
      key: row.ntee1,
      label: row.ntee_label,
      detail: `NTEE ${row.ntee1}`,
      count: row.count,
      share: row.pct_of_total,
      metricA: prettyMoney(row.avg_revenue),
      metricB: prettyDecimal(row.avg_peer_percentile),
      metricC: row.ntee1,
      color: chartColor(index, snapshot.categories.length || 1),
      bar: row.count,
    }))
}

function buildStateRows(snapshot: ResearchSnapshot): ExportRow[] {
  return [...(snapshot.states || [])]
    .sort((a, b) => b.count - a.count)
    .map((row, index) => ({
      key: row.state,
      label: row.state,
      detail: 'State rollup',
      count: row.count,
      share: row.pct,
      metricA: prettyMoney(row.avg_revenue),
      metricB: prettyDecimal(row.avg_peer_percentile),
      metricC: row.state,
      color: chartColor(index, snapshot.states.length || 1),
      bar: row.count,
    }))
}

function buildRevenueRows(snapshot: ResearchSnapshot): ExportRow[] {
  return [...(snapshot.revenue_bands || [])]
    .sort((a, b) => {
      if (a.operating_model === b.operating_model) return a.revenue_band_number - b.revenue_band_number
      return titleCase(a.operating_model).localeCompare(titleCase(b.operating_model))
    })
    .map((row, index) => ({
      key: `${row.operating_model}-${row.revenue_band_number}`,
      label: `${titleCase(row.operating_model)} · Band ${row.revenue_band_number}`,
      detail: 'Operating-model band rollup',
      count: row.count,
      share: row.pct_of_total,
      metricA: prettyDecimal(row.avg_peer_percentile),
      metricB: prettyDecimal(row.avg_months_reserve),
      metricC: titleCase(row.operating_model),
      color: chartColor(index, snapshot.revenue_bands.length || 1),
      bar: row.count,
    }))
}

function buildMovementRows(snapshot: ResearchSnapshot): ExportRow[] {
  return [...(snapshot.monthly_changes || [])].map((row, index) => ({
    key: row.month,
    label: row.month,
    detail: row.is_batch_revocation ? 'IRS batch revocation month' : 'Monthly activity',
    count: row.new_registrations,
    share: row.net,
    metricA: prettyNumber(row.new_registrations),
    metricB: prettyNumber(row.revocations),
    metricC: row.is_batch_revocation ? 'Batch revocation' : 'Standard month',
    color: row.is_batch_revocation ? COLORS.red : chartColor(index, snapshot.monthly_changes?.length || 1),
    bar: row.new_registrations,
  }))
}

const VIEW_CONFIGS: Record<ExplorerView, ExplorerConfig> = {
  coverage: {
    key: 'coverage',
    label: 'V6 context',
    description:
      'See how many organizations receive a peer comparison, a broader comparison, or only descriptive context.',
    noDataLabel: 'No V6 coverage data is available in this snapshot.',
    buildRows: buildCoverageRows,
    chartKind: 'horizontal',
    metricALabel: 'Peer comparison',
    metricBLabel: 'Avg peer group size',
    metricCLabel: 'Avg program %',
    note:
      'This view is the closest thing to a fairness check: it shows how often the method can reach a usable comparison and when it has to stop short.',
  },
  causes: {
    key: 'causes',
    label: 'Cause areas',
    description:
      'Review the largest public cause-area groups and compare their average revenue and peer context.',
    noDataLabel: 'No cause-area data is available in this snapshot.',
    buildRows: buildCauseRows,
    chartKind: 'horizontal',
    metricALabel: 'Avg revenue',
    metricBLabel: 'Avg peer percentile',
    metricCLabel: 'NTEE code',
    note:
      'Cause-area counts help explain coverage because some categories produce denser public records than others.',
  },
  states: {
    key: 'states',
    label: 'States',
    description:
      'Compare the ten state rollups in the snapshot and see how the distribution changes by geography.',
    noDataLabel: 'No state rollup is available in this snapshot.',
    buildRows: buildStateRows,
    chartKind: 'horizontal',
    metricALabel: 'Avg revenue',
    metricBLabel: 'Avg peer percentile',
    metricCLabel: 'State',
    note:
      'The snapshot includes state rollups, not a separate regional model. State differences here are descriptive, not causal.',
  },
  revenue: {
    key: 'revenue',
    label: 'Revenue bands',
    description:
      'Inspect the operating-model by revenue-band matrix that underlies the small-org fairness view.',
    noDataLabel: 'No revenue-band data is available in this snapshot.',
    buildRows: buildRevenueRows,
    chartKind: 'horizontal',
    metricALabel: 'Avg peer percentile',
    metricBLabel: 'Avg reserve months',
    metricCLabel: 'Operating model',
    note:
      'Lower revenue bands are a proxy for smaller organizations in the snapshot. The band numbers are kept numeric because this export does not carry a public dollar threshold.',
  },
  movement: {
    key: 'movement',
    label: 'Monthly movement',
    description:
      'Track registrations and revocations over time to understand how the registry changed across the snapshot period.',
    noDataLabel: 'No monthly movement data is available in this snapshot.',
    buildRows: buildMovementRows,
    chartKind: 'monthly',
    metricALabel: 'New registrations',
    metricBLabel: 'Revocations',
    metricCLabel: 'Net',
    note:
      'This view is operational history, not a performance signal. The batch-revocation month is called out explicitly so it cannot be misread as organic growth.',
  },
}

function SummaryCard({
  label,
  value,
  detail,
}: {
  label: string
  value: string
  detail: string
}) {
  return (
    <div className="rounded-2xl border border-white/15 bg-white/8 p-4 backdrop-blur-sm">
      <p className="font-body text-[11px] uppercase tracking-[0.12em] text-warm-cream/75">{label}</p>
      <p className="mt-2 font-display italic text-3xl leading-none text-warm-cream">{value}</p>
      <p className="mt-2 text-sm leading-[1.6] text-warm-cream/75">{detail}</p>
    </div>
  )
}

function PillButton({
  active,
  children,
  onClick,
}: {
  active: boolean
  children: ReactNode
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'min-h-11 rounded-full border px-4 py-2 text-sm font-medium transition-colors',
        active
          ? 'border-deep-navy bg-deep-navy text-warm-cream shadow-[0_8px_24px_rgba(10,22,40,0.12)]'
          : 'border-light-grey bg-white text-deep-navy hover:border-soft-gold hover:text-soft-gold',
      ].join(' ')}
    >
      {children}
    </button>
  )
}

export default function ResearchExplorer() {
  usePageMeta(
    'Research Explorer',
    'Interactive explorer for Daanaa’s static research snapshot. Inspect V6 context, cause areas, states, revenue bands, and monthly movement with charts, tables, CSV export, and a shareable URL.'
  )

  const [snapshot, setSnapshot] = useState<ResearchSnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [searchParams, setSearchParams] = useSearchParams()

  const view = parseView(searchParams.get('view'))
  const query = (searchParams.get('q') || '').trim()
  const limit = Math.min(Math.max(Number(searchParams.get('limit') || '12') || 12, 6), 24)

  useEffect(() => {
    let alive = true

    loadResearchSnapshot()
      .then((snap) => {
        if (!alive) return
        setSnapshot(snap)
        setError(null)
      })
      .catch((err) => {
        if (!alive) return
        setError(err instanceof Error ? err.message : 'research snapshot failed to load')
      })
      .finally(() => {
        if (!alive) return
        setLoading(false)
      })

    return () => {
      alive = false
    }
  }, [])

  const config = VIEW_CONFIGS[view]
  const allRows = snapshot ? config.buildRows(snapshot) : []
  const filteredRows = query ? allRows.filter((row) => searchRow(row, query)) : allRows
  const chartRows = filteredRows.slice(0, limit)
  const lowerBandCount =
    snapshot?.revenue_bands?.filter((band) => band.revenue_band_number <= 2).reduce((sum, band) => sum + band.count, 0) || 0
  const lowerBandTotal = snapshot?.revenue_bands?.reduce((sum, band) => sum + band.count, 0) || 0
  const lowerBandShare = lowerBandTotal ? (lowerBandCount / lowerBandTotal) * 100 : 0

  const updateParams = (next: Partial<Record<'view' | 'q' | 'limit', string>>) => {
    const params = new URLSearchParams(searchParams)
    Object.entries(next).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') {
        params.delete(key)
      } else {
        params.set(key, value)
      }
    })
    setSearchParams(params, { replace: true })
  }

  const copyShareLink = async () => {
    if (typeof window === 'undefined' || !window.navigator.clipboard) return
    await window.navigator.clipboard.writeText(window.location.href)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1800)
  }

  const downloadCsv = () => {
    if (!snapshot) return
    const csv = makeCsv(config.label, filteredRows, snapshot)
    saveCsv(`daanaa-research-${config.key}.csv`, csv)
  }

  const chartDescriptionId = `research-explorer-${view}-description`
  const tableShareLabel = view === 'movement' ? 'Net' : 'Share'

  return (
    <div className="min-h-[100dvh] bg-warm-cream">
      <header className="bg-deep-navy text-warm-cream">
        <div className="mx-auto max-w-[1200px] px-6 py-8 lg:px-12 lg:py-10">
          <div className="mb-6 flex flex-wrap items-center gap-2 text-sm text-warm-cream/70">
            <Link to="/research" className="transition-colors hover:text-warm-cream">
              Research
            </Link>
            <span aria-hidden="true">/</span>
            <span>Explorer</span>
          </div>

          <div className="grid gap-8 lg:grid-cols-[minmax(0,1.5fr)_minmax(320px,0.95fr)] lg:items-end">
            <div className="max-w-3xl">
              <p className="mb-3 font-body text-label uppercase tracking-[0.14em] text-soft-gold">
                Public aggregate snapshot
              </p>
              <h1 className="max-w-3xl font-display italic text-[clamp(2.8rem,6vw,5rem)] leading-[0.92] tracking-[-0.03em] text-warm-cream">
                Research explorer
              </h1>
              <p className="mt-5 max-w-2xl text-lg leading-[1.75] text-warm-cream/80">
                Inspect the static research snapshot behind Daanaa’s research brief. Switch
                between V6 context, cause areas, states, revenue bands, and monthly movement,
                then compare the chart with an accessible table of the visible rows.
              </p>
              <p className="mt-4 max-w-2xl text-sm leading-[1.7] text-warm-cream/70">
                This page stays within a single dated snapshot. It does not read live database
                tables, change scoring logic, or add new public claims.
              </p>
            </div>

            {snapshot ? (
              <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
                <SummaryCard
                  label="Snapshot date"
                  value={new Date(snapshot.metadata.data_period).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                  detail={`Generated ${new Date(snapshot.metadata.generated_at).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}`}
                />
                <SummaryCard
                  label="Denominator"
                  value={prettyNumber(snapshot.metadata.total_organizations)}
                  detail="Organizations in the active snapshot denominator."
                />
                <SummaryCard
                  label="V6 coverage"
                  value={snapshot.v6 ? prettyPct(snapshot.v6.placement_coverage_pct) : '—'}
                  detail={snapshot.v6 ? `${prettyNumber(snapshot.v6.unscored_count)} orgs remain unplaced` : 'Coverage data unavailable.'}
                />
              </div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
                <SummaryCard label="Snapshot date" value="—" detail="Loading data." />
                <SummaryCard label="Denominator" value="—" detail="Loading data." />
                <SummaryCard label="V6 coverage" value="—" detail="Loading data." />
              </div>
            )}
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={copyShareLink}
              className="inline-flex min-h-11 items-center rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium text-warm-cream transition-colors hover:bg-white/15 focus:outline-none focus-visible:ring-2 focus-visible:ring-soft-gold"
            >
              {copied ? 'Link copied' : 'Copy share link'}
            </button>
            <button
              type="button"
              onClick={downloadCsv}
              className="inline-flex min-h-11 items-center rounded-full border border-soft-gold/40 bg-soft-gold px-4 py-2 text-sm font-medium text-deep-navy transition-colors hover:bg-bright-gold focus:outline-none focus-visible:ring-2 focus-visible:ring-soft-gold"
            >
              Download CSV
            </button>
            <a
              href="/research"
              className="inline-flex min-h-11 items-center rounded-full border border-white/20 px-4 py-2 text-sm font-medium text-warm-cream transition-colors hover:border-soft-gold hover:text-soft-gold focus:outline-none focus-visible:ring-2 focus-visible:ring-soft-gold"
            >
              Read the narrative
            </a>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1200px] px-6 py-10 lg:px-12 lg:py-12">
        {loading && (
          <div className="rounded-2xl border border-light-grey bg-white p-8 text-center text-cool-grey shadow-[0_8px_30px_rgba(10,22,40,0.05)]">
            Loading research snapshot…
          </div>
        )}

        {error && !loading && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-900">
            <p className="font-semibold">The explorer could not load the snapshot.</p>
            <p className="mt-2 text-sm leading-[1.7]">{error}</p>
          </div>
        )}

        {!loading && !error && snapshot && (
          <div className="grid gap-8 xl:grid-cols-[300px_minmax(0,1fr)]">
            <aside className="space-y-6">
              <section className="rounded-2xl border border-light-grey bg-white p-5 shadow-[0_8px_30px_rgba(10,22,40,0.05)]">
                <p className="font-body text-label uppercase tracking-[0.12em] text-cool-grey">
                  Explore
                </p>
                <h2 className="mt-2 font-display italic text-2xl text-deep-navy">
                  Switch the lens
                </h2>
                <div className="mt-4 flex flex-wrap gap-2">
                  {VIEW_ORDER.map((item) => (
                    <PillButton
                      key={item}
                      active={view === item}
                      onClick={() => updateParams({ view: item })}
                    >
                      {VIEW_LABELS[item]}
                    </PillButton>
                  ))}
                </div>
              </section>

              <section className="rounded-2xl border border-light-grey bg-white p-5 shadow-[0_8px_30px_rgba(10,22,40,0.05)]">
                <p className="font-body text-label uppercase tracking-[0.12em] text-cool-grey">
                  Filter
                </p>
                <label
                  htmlFor="research-explorer-search"
                  className="mt-2 block text-sm font-medium text-deep-navy"
                >
                  Search visible rows
                </label>
                <input
                  id="research-explorer-search"
                  type="search"
                  value={query}
                  onChange={(event) => updateParams({ q: event.target.value })}
                  placeholder="Try California, education, band 0, or 2026-07"
                  className="mt-3 w-full rounded-xl border border-light-grey bg-warm-cream px-4 py-3 text-sm text-deep-navy placeholder:text-cool-grey focus:border-soft-gold focus:outline-none focus:ring-2 focus:ring-soft-gold/20"
                />
                <p className="mt-3 text-sm leading-[1.65] text-cool-grey">
                  Search is local and stays within the current snapshot view.
                </p>
                <label
                  htmlFor="research-explorer-limit"
                  className="mt-4 block text-sm font-medium text-deep-navy"
                >
                  Chart rows
                </label>
                <input
                  id="research-explorer-limit"
                  type="range"
                  min={6}
                  max={24}
                  value={limit}
                  onChange={(event) => updateParams({ limit: event.target.value })}
                  className="mt-3 w-full accent-[rgb(201_169_110)]"
                />
                <div className="mt-2 flex items-center justify-between text-xs text-cool-grey">
                  <span>6</span>
                  <span>{limit} visible rows</span>
                  <span>24</span>
                </div>
              </section>

              <section className="rounded-2xl border border-light-grey bg-white p-5 shadow-[0_8px_30px_rgba(10,22,40,0.05)]">
                <p className="font-body text-label uppercase tracking-[0.12em] text-cool-grey">
                  Small-org fairness
                </p>
                <h2 className="mt-2 font-display italic text-2xl text-deep-navy">
                  Lower bands stay visible
                </h2>
                <div className="mt-4 space-y-3">
                  <div className="rounded-xl bg-warm-cream p-4">
                    <p className="text-xs uppercase tracking-[0.12em] text-cool-grey">Lower bands 0-2</p>
                    <p className="mt-1 font-display italic text-3xl text-deep-navy">
                      {prettyNumber(lowerBandCount)}
                    </p>
                    <p className="mt-1 text-sm leading-[1.65] text-cool-grey">
                      {prettyPct(lowerBandShare)} of the revenue-band matrix rows in this snapshot.
                    </p>
                  </div>
                  <div className="rounded-xl bg-warm-cream p-4">
                    <p className="text-xs uppercase tracking-[0.12em] text-cool-grey">
                      Peer-comparison tiers
                    </p>
                    <p className="mt-1 font-display italic text-3xl text-deep-navy">
                      {snapshot.v6 ? `${snapshot.v6.tiers.filter((tier) => tier.has_peer_comparison).length}/4` : '—'}
                    </p>
                    <p className="mt-1 text-sm leading-[1.65] text-cool-grey">
                      Tiers with an actual peer comparison.
                    </p>
                  </div>
                  <div className="rounded-xl bg-warm-cream p-4">
                    <p className="text-xs uppercase tracking-[0.12em] text-cool-grey">
                      Unplaced orgs
                    </p>
                    <p className="mt-1 font-display italic text-3xl text-deep-navy">
                      {snapshot.v6 ? prettyNumber(snapshot.v6.unscored_count) : '—'}
                    </p>
                    <p className="mt-1 text-sm leading-[1.65] text-cool-grey">
                      Organizations with no usable V6 placement in the snapshot.
                    </p>
                  </div>
                </div>
              </section>
            </aside>

            <section className="space-y-8">
              <article className="rounded-3xl border border-light-grey bg-white p-5 shadow-[0_8px_30px_rgba(10,22,40,0.05)] lg:p-6">
                <div className="flex flex-wrap items-start justify-between gap-6">
                  <div className="max-w-3xl">
                    <p className="font-body text-label uppercase tracking-[0.12em] text-cool-grey">
                      {config.label}
                    </p>
                    <h2 className="mt-2 font-display italic text-3xl text-deep-navy">
                      {config.description}
                    </h2>
                    <p id={chartDescriptionId} className="mt-3 max-w-3xl text-sm leading-[1.75] text-cool-grey">
                      {config.note}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-deep-navy px-4 py-3 text-warm-cream">
                    <p className="text-[11px] uppercase tracking-[0.12em] text-warm-cream/70">Visible rows</p>
                    <p className="mt-1 font-display italic text-3xl leading-none">{prettyNumber(filteredRows.length)}</p>
                    <p className="mt-1 text-sm text-warm-cream/75">Filtered from the current snapshot</p>
                  </div>
                </div>

                <div className="mt-6">
                  {allRows.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-light-grey bg-warm-cream p-8 text-center">
                      <p className="font-display italic text-2xl text-deep-navy">
                        {config.noDataLabel}
                      </p>
                    </div>
                  ) : filteredRows.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-light-grey bg-warm-cream p-8 text-center">
                      <p className="font-display italic text-2xl text-deep-navy">
                        No rows match this search.
                      </p>
                      <p className="mt-2 text-sm leading-[1.7] text-cool-grey">
                        Try clearing the search or switching views.
                      </p>
                    </div>
                  ) : config.chartKind === 'horizontal' ? (
                    <div className="h-[420px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={chartRows}
                          layout="vertical"
                          margin={{ top: 8, right: 24, bottom: 8, left: 12 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(10,22,40,0.08)" />
                          <XAxis
                            type="number"
                            tick={{ fill: COLORS.cool, fontSize: 11 }}
                            axisLine={{ stroke: 'rgba(10,22,40,0.12)' }}
                            tickLine={false}
                            tickFormatter={(value) => prettyNumber(Number(value))}
                          />
                          <YAxis
                            type="category"
                            dataKey="label"
                            width={220}
                            tick={{ fill: COLORS.navy, fontSize: 12 }}
                            axisLine={false}
                            tickLine={false}
                          />
                          <Tooltip
                            cursor={{ fill: 'rgba(201,169,110,0.08)' }}
                            content={({ active, payload }) => {
                              if (!active || !payload?.length) return null
                              const row = payload[0]?.payload as ExportRow
                              return (
                                <div className="max-w-[280px] rounded-2xl border border-soft-gold/30 bg-deep-navy px-4 py-3 text-warm-cream shadow-[0_16px_36px_rgba(10,22,40,0.24)]">
                                  <p className="font-semibold text-soft-gold">{row.label}</p>
                                  <p className="mt-1 text-xs leading-[1.6] text-warm-cream/75">{row.detail}</p>
                                  <div className="mt-2 space-y-1 text-xs text-warm-cream/80">
                                    <p>Count: {prettyNumber(row.count)}</p>
                                    <p>Share: {prettyPct(row.share)}</p>
                                    <p>{config.metricALabel}: {row.metricA}</p>
                                    <p>{config.metricBLabel}: {row.metricB}</p>
                                    <p>{config.metricCLabel}: {row.metricC}</p>
                                  </div>
                                </div>
                              )
                            }}
                          />
                          <Bar dataKey="bar" radius={[0, 12, 12, 0]} fill={COLORS.gold}>
                            {chartRows.map((row, index) => (
                              <Cell key={row.key} fill={row.color || chartColor(index, chartRows.length || 1)} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="h-[360px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={chartRows.map((row) => ({
                            ...row,
                            revocationsNegative: -Number(row.metricB.replace(/,/g, '')) || 0,
                          }))}
                          margin={{ top: 8, right: 24, bottom: 24, left: 0 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(10,22,40,0.08)" />
                          <XAxis
                            dataKey="label"
                            tick={{ fill: COLORS.cool, fontSize: 11 }}
                            axisLine={{ stroke: 'rgba(10,22,40,0.12)' }}
                            tickLine={false}
                          />
                          <YAxis
                            tick={{ fill: COLORS.cool, fontSize: 11 }}
                            axisLine={{ stroke: 'rgba(10,22,40,0.12)' }}
                            tickLine={false}
                            tickFormatter={(value) => prettyNumber(Math.abs(Number(value)))}
                          />
                          <Tooltip
                            cursor={{ fill: 'rgba(201,169,110,0.08)' }}
                            content={({ active, payload }) => {
                              if (!active || !payload?.length) return null
                              const row = payload[0]?.payload as ExportRow & { revocationsNegative?: number }
                              return (
                                <div className="max-w-[280px] rounded-2xl border border-soft-gold/30 bg-deep-navy px-4 py-3 text-warm-cream shadow-[0_16px_36px_rgba(10,22,40,0.24)]">
                                  <p className="font-semibold text-soft-gold">{row.label}</p>
                                  <p className="mt-1 text-xs leading-[1.6] text-warm-cream/75">{row.detail}</p>
                                  <div className="mt-2 space-y-1 text-xs text-warm-cream/80">
                                    <p>New registrations: {prettyNumber(row.count)}</p>
                                    <p>Revocations: {row.metricB}</p>
                                    <p>Net: {prettyNumber(Number(row.share))}</p>
                                    <p>{config.metricCLabel}: {row.metricC}</p>
                                  </div>
                                </div>
                              )
                            }}
                          />
                          <Legend />
                          <Bar dataKey="count" name="New registrations" fill={COLORS.gold} radius={[8, 8, 0, 0]} />
                          <Bar dataKey="revocationsNegative" name="Revocations" fill={COLORS.red} radius={[8, 8, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>
              </article>

              <article className="rounded-3xl border border-light-grey bg-white p-5 shadow-[0_8px_30px_rgba(10,22,40,0.05)] lg:p-6">
                <div className="flex flex-wrap items-end justify-between gap-4">
                  <div>
                    <p className="font-body text-label uppercase tracking-[0.12em] text-cool-grey">
                      Visible table
                    </p>
                    <h2 className="mt-2 font-display italic text-3xl text-deep-navy">
                      Accessible fallback for the chart
                    </h2>
                  </div>
                  <p className="max-w-2xl text-sm leading-[1.7] text-cool-grey">
                    The table always shows the same filtered rows as the chart, so keyboard and screen-reader users do not lose the data.
                  </p>
                </div>

                <div className="mt-6 overflow-x-auto" tabIndex={0} role="region" aria-label="Visible aggregate rows">
                  <table className="min-w-full border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-light-grey bg-deep-navy/[0.02]">
                        <th className="px-4 py-3 text-left font-semibold text-deep-navy">Row</th>
                        <th className="px-4 py-3 text-left font-semibold text-deep-navy">Detail</th>
                        <th className="px-4 py-3 text-right font-semibold text-deep-navy">Count</th>
                        <th className="px-4 py-3 text-right font-semibold text-deep-navy">{tableShareLabel}</th>
                        <th className="px-4 py-3 text-right font-semibold text-deep-navy">
                          {config.metricALabel}
                        </th>
                        <th className="px-4 py-3 text-right font-semibold text-deep-navy">
                          {config.metricBLabel}
                        </th>
                        <th className="px-4 py-3 text-right font-semibold text-deep-navy">
                          {config.metricCLabel}
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredRows.map((row) => (
                        <tr key={row.key} className="border-b border-light-grey/70 last:border-0">
                          <td className="px-4 py-3 font-medium text-deep-navy">{row.label}</td>
                          <td className="px-4 py-3 text-cool-grey">{row.detail}</td>
                          <td className="px-4 py-3 text-right font-mono text-deep-navy">
                            {prettyNumber(row.count)}
                          </td>
                          <td className="px-4 py-3 text-right font-mono text-deep-navy">
                            {view === 'movement' ? prettyNumber(row.share) : prettyPct(row.share)}
                          </td>
                          <td className="px-4 py-3 text-right font-mono text-deep-navy">
                            {row.metricA}
                          </td>
                          <td className="px-4 py-3 text-right font-mono text-deep-navy">
                            {row.metricB}
                          </td>
                          <td className="px-4 py-3 text-right font-mono text-deep-navy">
                            {row.metricC}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </article>

              <article className="grid gap-6 md:grid-cols-2">
                <div className="rounded-3xl border border-light-grey bg-white p-5 shadow-[0_8px_30px_rgba(10,22,40,0.05)]">
                  <p className="font-body text-label uppercase tracking-[0.12em] text-cool-grey">
                    What this shows
                  </p>
                  <ul className="mt-4 space-y-3 text-sm leading-[1.7] text-cool-grey">
                    <li>Reported aggregate counts from one static snapshot.</li>
                    <li>Peer context, cause areas, states, revenue bands, and monthly movement.</li>
                    <li>Tables and charts that stay in sync with the same filtered rows.</li>
                    <li>Snapshot date, denominator, and source note at the top of the page.</li>
                  </ul>
                </div>

                <div className="rounded-3xl border border-light-grey bg-white p-5 shadow-[0_8px_30px_rgba(10,22,40,0.05)]">
                  <p className="font-body text-label uppercase tracking-[0.12em] text-cool-grey">
                    What this does not show
                  </p>
                  <ul className="mt-4 space-y-3 text-sm leading-[1.7] text-cool-grey">
                    <li>Live database reads or private nonprofit data.</li>
                    <li>Mission impact, quality, or organizational worth.</li>
                    <li>Any claim that a missing row is a negative signal.</li>
                    <li>Public methodology changes beyond the approved research brief.</li>
                  </ul>
                </div>
              </article>

              {snapshot && (
                <footer className="rounded-3xl border border-light-grey bg-white p-5 shadow-[0_8px_30px_rgba(10,22,40,0.05)]">
                  <p className="text-xs uppercase tracking-[0.12em] text-cool-grey">Snapshot details</p>
                  <p className="mt-3 text-sm leading-[1.8] text-cool-grey">
                    Data period: {new Date(snapshot.metadata.data_period).toLocaleDateString('en-US', {
                      month: 'long',
                      day: 'numeric',
                      year: 'numeric',
                    })}{' '}
                    · Generated: {new Date(snapshot.metadata.generated_at).toLocaleDateString('en-US', {
                      month: 'long',
                      day: 'numeric',
                      year: 'numeric',
                    })}{' '}
                    · Denominator: {prettyNumber(snapshot.metadata.total_organizations)}
                  </p>
                  <p className="mt-3 max-w-4xl text-sm leading-[1.8] text-cool-grey">
                    {snapshot.metadata.disclaimer}
                  </p>
                </footer>
              )}

              <RelatedPages
                links={[
                  { to: '/research', label: 'Research library' },
                  { to: '/methodology', label: 'Public methodology' },
                  { to: '/about', label: 'About Daanaa' },
                ]}
              />
            </section>
          </div>
        )}
      </main>
    </div>
  )
}
