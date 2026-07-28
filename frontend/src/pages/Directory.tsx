import React, { useState, useEffect, useRef } from 'react'
import { usePageMeta } from '../hooks/usePageMeta'
import { useSearchParams, Link } from 'react-router-dom'
import OrgCard, { OrgCardRow } from '../components/OrgCard'
import FilterSheet from '../components/FilterSheet'
import SearchBar from '../components/SearchBar'
import Breadcrumb from '../components/Breadcrumb'
import { useApi } from '../hooks/useApi'
import { getOrganizations, getFusedSearch, getStats } from '../data/api'
import type { ApiOrganization } from '../data/api'
import { getTierSummary, getTierFromOrg } from '../components/TrustBadge'
import LampMark from '../components/LampMark'
import type { TierName } from '../components/TrustBadge'
import { RAIL_CATEGORIES, ALL_CATEGORIES, NTEE_SUBCATEGORIES } from '../data/categories'
import { US_STATES, US_TERRITORIES, US_MILITARY } from '../data/locations'
import { trackSearchMetrics } from '../lib/analytics'
import { parseLocationQuery } from '../utils/locationQuery'

const FILTER_CATEGORIES = [
  { id: 'all', label: 'All' },
  ...ALL_CATEGORIES,
]

const SCORES_ENABLED = import.meta.env.VITE_ENABLE_SCORES !== 'false'

// Neutral default (2026-07-04 stewardship fix): name A to Z, never a score
// ranking. Peer Financial Context stays available as an explicit opt-in sort.
// P7 Stewardship: Only neutral sorts. Revenue is data (not ranking).
// (2026-07-24: Removed score-based 'Top Performers' ranking; kept revenue sort for transparency)
const SORT_OPTIONS = [
  { id: 'random', label: 'Shuffle' },  // Discovery-first (2026-07-24)
  { id: 'organization_name', label: 'Name A to Z' },  // Neutral control, no ranking
  { id: 'total_revenue', label: 'By Total Revenue' },  // Data transparency, not ranking
]

function hasKnownDataSource(src: string | null) {
  return src === 'propublica' || src === 'irs_soi'
}

function OrgCardApi({ org, listView = false }: { org: ApiOrganization; listView?: boolean }) {
  const scored = hasKnownDataSource(org.data_source) && (org.peer_percentile ?? org.ntee1_percentile) !== null
  const cardOrg = {
    id: org.EIN,
    name: org.organization_name,
    ein: org.EIN,
    city: org.CITY || '',
    state: org.STATE || '',
    category: org.NTEE1 || '',
    subcategory: org.NTEECC || org.NTEE1 || '',
    meritScore: Math.round(org.peer_percentile ?? org.ntee1_percentile ?? 0),
    hasScore: scored,
    revenueBand: org.revenue_band ?? null,
    dataSource: org.data_source ?? null,
    latestTaxYear: org.latest_tax_year ?? null,
    ntee1TotalOrgs: org.ntee1_total_orgs ?? null,
    hasMission: org.has_mission ?? null,
    hasWebsite: org.has_website ?? null,
    revenue: org.total_revenue ?? 0,
    assets: 0,
    employees: 0,
    founded: 0,
    mission: org.mission || '',
    programs: [] as string[],
    leadership: [] as { name: string; title: string; initials: string }[],
    boardSize: 0,
    revenueTrend: [] as { year: number; amount: number }[],
    programEfficiency: 0,
    fundraisingRatio: 0,
    operatingReserve: 0,
    transparencyScore: 0,
  }
  const summary = getTierSummary(getTierFromOrg(org), org)
  const props = { org: cardOrg, apiOrg: org, trustSummary: summary }
  return listView ? <OrgCardRow {...props} /> : <OrgCard {...props} />
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Directory() {
  const [searchParams, setSearchParams] = useSearchParams()
  const categoryParam = searchParams.get('ntee') || searchParams.get('category') || 'all'
  const subParam      = searchParams.get('sub') || ''
  const qParam        = searchParams.get('q') || ''
  usePageMeta(
    qParam ? `"${qParam}" · Causes & Organizations` : 'Explore Causes & Organizations',
    'Search 1.8 million+ tax-deductible 501(c)(3) organizations recognized by the IRS, by cause, category, and location.'
  )
  const stateParam    = searchParams.get('state') || ''
  const minRevenueParam = Number(searchParams.get('min_revenue') || '0')
  const maxRevenueParam = Number(searchParams.get('max_revenue') || '500000000')

  const [searchQuery, setSearchQuery] = useState(qParam)
  const [debouncedQuery, setDebouncedQuery] = useState(qParam)
  const subParamList = subParam.split(',').map(s => s.trim()).filter(Boolean)
  const [activeFilters, setActiveFilters] = useState<string[]>(() => {
    // Categories = explicit ?category= plus the parent letter of any ?sub= code
    const fromCats = (!categoryParam || categoryParam === 'all') ? [] : categoryParam.split(',').filter(c => c && c !== 'all')
    const fromSubs = subParamList.map(s => s[0])
    return Array.from(new Set([...fromCats, ...fromSubs]))
  })
  const [subFilters, setSubFilters] = useState<string[]>(subParamList)
  const [stateFilter, setStateFilter] = useState(stateParam)
  const [showOnlyWithRevenue, setShowOnlyWithRevenue] = useState(false)  // Toggle: filter to orgs with revenue data
  // Discovery default (2026-07-24): seeded random shuffle for engagement + fairness.
  // Users can opt to 'organization_name' (A-Z) or other sorts. Shuffle is P7-compliant:
  // random order is neutral (equal probability for all orgs, no ranking by size/name/score).
  // Seed makes shuffle deterministic per session (same seed = same results).
  const [sortBy, setSortBy] = useState('random')
  // Session seed for seeded shuffle (deterministic random per session)
  const sessionShuffleRef = useRef(
    typeof window !== 'undefined'
      ? localStorage.getItem('daanaa_session_seed') || Math.random().toString(36).slice(2, 11)
      : Math.random().toString(36).slice(2, 11)
  )
  // Persist session seed for consistency across reloads
  useEffect(() => {
    localStorage.setItem('daanaa_session_seed', sessionShuffleRef.current)
  }, [])

  // Sync filter state with URL params whenever they change
  useEffect(() => {
    const newFromCats = (!categoryParam || categoryParam === 'all') ? [] : categoryParam.split(',').filter(c => c && c !== 'all')
    const newFromSubs = subParamList.map(s => s[0])
    setActiveFilters(Array.from(new Set([...newFromCats, ...newFromSubs])))
    setSubFilters(subParamList)
    setStateFilter(stateParam)
  }, [categoryParam, subParam, stateParam])
  const [minRevenue, setMinRevenue] = useState(minRevenueParam)
  const [maxRevenue, setMaxRevenue] = useState(maxRevenueParam)
  const [hasWebsite, setHasWebsite] = useState(searchParams.get('has_website') === '1')
  const [verifiedRevenueOnly, setVerifiedRevenueOnly] = useState(searchParams.get('verified_revenue') === '1')
  // Hidden gems are off by default (user must explicitly toggle them on)
  const [hiddenGem, setHiddenGem] = useState(
    searchParams.has('hidden_gem') ? searchParams.get('hidden_gem') === '1' : false
  )
  const [needsSupport, setNeedsSupport] = useState(searchParams.get('needs_funding') === '1')
  const [near, setNear] = useState(searchParams.get('near') || '')
  const [nearInput, setNearInput] = useState(searchParams.get('near') || '')
  const [radiusMi, setRadiusMi] = useState(Number(searchParams.get('radius_mi') || '25'))
  // True when `near` was auto-detected from the main search bar (vs the
  // explicit advanced zip/city field or "use my location" button) — so
  // clearing the main box also clears the location, without stomping on an
  // intentional advanced-field value.
  const nearFromSearchBarRef = useRef(false)
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc')
  const [randomizeCount, setRandomizeCount] = useState(0)  // Trigger refetch when randomize button clicked
  const [cause, setCause] = useState(searchParams.get('cause') || '')
  const [debouncedCause, setDebouncedCause] = useState(cause)
  const [currentPage, setCurrentPage] = useState(1)
  const [filterSheetOpen, setFilterSheetOpen] = useState(false)
  // Default view follows the viewport: the grid only reads as a grid once it
  // goes 3-up at lg, so that same breakpoint picks the default. Phones and
  // tablets start on the list, where one column per row stays scannable.
  // Initial value only — once the reader touches the toggle, their choice wins.
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return 'list'
    return window.matchMedia('(min-width: 1024px)').matches ? 'grid' : 'list'
  })
  const [filtersExpanded, setFiltersExpanded] = useState(false)
  const searchMode = 'browse'
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const itemsPerPage = viewMode === 'list' ? 25 : 18

  // Sync search query from URL on mount (e.g. coming from homepage search)
  useEffect(() => {
    if (qParam && qParam !== searchQuery) {
      setSearchQuery(qParam)
      setDebouncedQuery(qParam)
      setCurrentPage(1)
    }
  }, [qParam])

  // Debounce search query — 320ms after typing stops
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      const trimmed = searchQuery.trim()
      const asLocation = parseLocationQuery(trimmed)
      if (asLocation) {
        // Route to the real proximity engine instead of keyword FTS — a zip
        // or "City, ST" gets distance-ranked results, not a generic text match.
        nearFromSearchBarRef.current = true
        setNear(asLocation)
        setNearInput(asLocation)
        setDebouncedQuery('')
      } else {
        if (nearFromSearchBarRef.current) {
          nearFromSearchBarRef.current = false
          setNear('')
          setNearInput('')
        }
        // Normalize EIN format: "46-3120432" → "463120432" so the API matches
        const normalized = /^\d{2}-\d{7}$/.test(trimmed)
          ? searchQuery.replace(/-/g, '')
          : searchQuery
        setDebouncedQuery(normalized)
      }
      setCurrentPage(1)
    }, 320)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [searchQuery])

  // Debounce cause filter — same 320ms feel as search
  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedCause(cause)
      setCurrentPage(1)
    }, 320)
    return () => clearTimeout(t)
  }, [cause])


  // A search query, or an explicit location filter, means the user is asking
  // "what's here" — so the gems-default lens is dropped (otherwise a zip/city
  // search would silently narrow to the ~34k gems subset and often return
  // few or zero results near a given location, a bad first impression).
  const effectiveHiddenGem = hiddenGem && !debouncedQuery.trim() && !near

  // Fused search mode: any meaningful query with no active structured filters
  const hasRevenueFilter = minRevenue > 0 || maxRevenue < 500_000_000
  const hasAnyFilter = activeFilters.length > 0 || subFilters.length > 0 || !!stateFilter || hasRevenueFilter || hasWebsite || needsSupport || !!debouncedCause.trim()
  const isFusedMode = !hasAnyFilter && debouncedQuery.trim().length >= 2

  // Categories the user drilled into (picked specific subcats) are represented by
  // those subcats; remaining selected categories are sent whole. Backend ORs them.
  const catsWithSubs = new Set(subFilters.map(s => s[0]))
  const nteeToSend = activeFilters.filter(c => !catsWithSubs.has(c))

  const { data: orgsData, loading: orgsLoading, error: orgsError } = useApi(
    () => getOrganizations({
      ntee: nteeToSend.length ? nteeToSend.join(',') : undefined,
      sub: subFilters.length ? subFilters.join(',') : undefined,
      state: stateFilter || undefined,
      q: debouncedQuery || undefined,
      sort: sortBy,
      seed: sortBy === 'random' ? sessionShuffleRef.current : undefined,  // Pass seed for seeded shuffle
      order: sortOrder,
      page: currentPage,
      per_page: itemsPerPage,
      min_revenue: minRevenue > 0 ? minRevenue : undefined,
      max_revenue: maxRevenue < 500_000_000 ? maxRevenue : undefined,
      verified_revenue: verifiedRevenueOnly || undefined,
      has_revenue: showOnlyWithRevenue || undefined,  // Filter to orgs with revenue data
      has_website: hasWebsite || undefined,
      hidden_gem: effectiveHiddenGem || undefined,
      needs_funding: needsSupport || undefined,
      cause: debouncedCause.trim() || undefined,
      near: near || undefined,
      radius_mi: near ? radiusMi : undefined,
    }),
    [activeFilters, subFilters, stateFilter, debouncedQuery, sortBy, sortOrder, currentPage, minRevenue, maxRevenue, verifiedRevenueOnly, hasWebsite, effectiveHiddenGem, needsSupport, debouncedCause, itemsPerPage, near, radiusMi, randomizeCount]
  )

  const { data: fusedData, loading: fusedLoading, error: fusedError } = useApi(
    () => isFusedMode ? getFusedSearch(debouncedQuery) : Promise.resolve(null),
    [debouncedQuery, isFusedMode]
  )

  // Data-freshness line under the results count ("last checked <date>")
  const { data: statsData } = useApi(getStats, [])

  const scrollTop = () => window.scrollTo({ top: 0, behavior: 'smooth' })

  const handleFilterChange = (filterId: string) => {
    let next: string[]
    if (filterId === 'all') {
      next = []
    } else {
      const already = activeFilters.includes(filterId)
      next = already ? activeFilters.filter(f => f !== filterId) : [...activeFilters, filterId]
    }
    setActiveFilters(next)
    // Drop any selected subcategories whose parent category is no longer active
    const prunedSubs = subFilters.filter(s => next.includes(s[0]))
    if (prunedSubs.length !== subFilters.length) {
      setSubFilters(prunedSubs)
      if (prunedSubs.length) searchParams.set('sub', prunedSubs.join(',')); else searchParams.delete('sub')
    }
    setCurrentPage(1)
    scrollTop()
    if (next.length === 0) {
      searchParams.delete('ntee')
    } else {
      searchParams.set('ntee', next.join(','))
    }
    setSearchParams(searchParams)
  }

  const handleSubChange = (code: string) => {
    const next = subFilters.includes(code) ? subFilters.filter(s => s !== code) : [...subFilters, code]
    setSubFilters(next)
    if (next.length) searchParams.set('sub', next.join(',')); else searchParams.delete('sub')
    setSearchParams(searchParams)
    setCurrentPage(1)
    scrollTop()
  }

  const handleStateChange = (s: string) => {
    setStateFilter(s)
    setCurrentPage(1)
    scrollTop()
    if (s) { searchParams.set('state', s) } else { searchParams.delete('state') }
    setSearchParams(searchParams)
  }

  const handleMinRevenueChange = (value: number) => {
    setMinRevenue(value)
    setCurrentPage(1)
    scrollTop()
    setSearchParams((sp) => {
      if (value > 0) { sp.set('min_revenue', String(value)) } else { sp.delete('min_revenue') }
      return sp
    })
  }

  const handleMaxRevenueChange = (value: number) => {
    setMaxRevenue(value)
    setCurrentPage(1)
    scrollTop()
    setSearchParams((sp) => {
      if (value < 500_000_000) { sp.set('max_revenue', String(value)) } else { sp.delete('max_revenue') }
      return sp
    })
  }



  // Clear all filters returns to the default landing (hidden gems on).
  const handleClearAll = () => {
    setSearchQuery('')
    setDebouncedQuery('')
    setActiveFilters([])
    setSubFilters([])
    setStateFilter('')
    setSortBy('organization_name')
    setSortOrder('asc')
    setMinRevenue(0)
    setMaxRevenue(500_000_000)
    setHasWebsite(false)
    setNeedsSupport(false)
    setNear(''); setNearInput('')
    setRadiusMi(25)
    setHiddenGem(true)
    setCause('')
    setDebouncedCause('')
    setCurrentPage(1)
    searchParams.delete('ntee')
    searchParams.delete('sub')
    searchParams.delete('q')
    searchParams.delete('state')
    searchParams.delete('min_revenue')
    searchParams.delete('max_revenue')
    searchParams.delete('min_tier')
    searchParams.delete('tier')
    searchParams.delete('has_website')
    searchParams.delete('hidden_gem')
    searchParams.delete('needs_funding')
    searchParams.delete('near')
    searchParams.delete('radius_mi')
    setSearchParams(searchParams)
  }

  // "See all" — leave the gems lens and browse the full directory.
  const handleSeeAll = () => {
    setHiddenGem(false)
    setNeedsSupport(false)
    setCurrentPage(1)
    scrollTop()
    searchParams.set('hidden_gem', '0')
    setSearchParams(searchParams)
  }

  // Deterministic shuffle using session ID as seed. Produces same order within
  // a session, but different order on each fresh visit to browse-all (no filters).
  const seededShuffle = (arr: any[], seed: string): any[] => {
    const result = [...arr]
    let hash = 0
    for (let i = 0; i < seed.length; i++) {
      hash = ((hash << 5) - hash) + seed.charCodeAt(i)
      hash = hash & hash // Convert to 32-bit integer
    }
    const random = (index: number): number => {
      const x = Math.sin(hash + index) * 10000
      return x - Math.floor(x)
    }
    for (let i = result.length - 1; i > 0; i--) {
      const j: number = Math.floor(random(i) * (i + 1))
      ;[result[i], result[j]] = [result[j], result[i]]
    }
    return result
  }

  // Use fused results when available, fall back to FTS5 keyword
  const fusedResults = fusedData?.results
  const useFusedResults = isFusedMode && !!fusedResults && fusedResults.length >= 1
  let organizations = useFusedResults ? fusedResults : (orgsData?.organizations || [])

  // Apply shuffle when browsing all orgs with no filters/search (discover mode)
  const shouldShuffle = effectiveHiddenGem && !useFusedResults && !debouncedQuery.trim() && activeFilters.length === 0 && !stateFilter && !hasRevenueFilter
  if (shouldShuffle && organizations.length > 0) {
    organizations = seededShuffle(organizations, sessionShuffleRef.current)
  }

  const total = useFusedResults ? fusedResults.length : (orgsData?.total || 0)
  const totalPages = useFusedResults ? 1 : (orgsData?.pages || 1)
  const activeLoading = useFusedResults ? fusedLoading : orgsLoading
  // Fused failures degrade to the keyword results that already loaded; only
  // surface an error when there is genuinely nothing to show the user.
  const activeError = useFusedResults
    ? null
    : (orgsError ?? (isFusedMode && fusedError && organizations.length === 0 ? fusedError : null))

  // Readable label for any subcategory code (searches across all categories)
  const subLabelOf = (code: string): string => {
    for (const arr of Object.values(NTEE_SUBCATEGORIES)) {
      const m = arr.find(s => s.code === code)
      if (m) return m.label
    }
    return code
  }

  // Readable label for active revenue filter
  const formatRevenue = (val: number) => {
    if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(0)}M`
    if (val >= 1_000) return `$${(val / 1_000).toFixed(0)}K`
    return `$${val}`
  }
  const revLabel = hasRevenueFilter ? `${formatRevenue(minRevenue)}–${formatRevenue(maxRevenue)}` : ''

  // Readable label for active score tier

  const activeFilterCount = [
    activeFilters.length > 0,
    subFilters.length > 0,
    !!stateFilter,
    hasRevenueFilter,
    hasWebsite,
    needsSupport,
    sortBy !== 'organization_name',
  ].filter(Boolean).length

  // T12 Phase 1: Track search metrics for zero-result analysis and query patterns
  useEffect(() => {
    if (!activeLoading && (debouncedQuery || hasAnyFilter)) {
      trackSearchMetrics({
        query_length: debouncedQuery.length,
        result_count: total,
        zero_results: total === 0 ? 'yes' : 'no',
        filters_applied: activeFilterCount,
        mode: useFusedResults ? 'fused' : (hasAnyFilter ? 'filtered' : 'keyword'),
      })
    }
  }, [total, debouncedQuery, activeFilterCount, hasAnyFilter, activeLoading, useFusedResults])

  return (
    <div className="min-h-[100dvh]">
      <Breadcrumb items={[{ label: 'Home', href: '/' }, { label: 'Directory' }]} />
      {/* Page Header */}
      <div className="bg-white border-b border-light-grey pt-nav">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12 pt-10 pb-10">

          <h1 className="font-display italic text-deep-navy leading-[1.05] tracking-[-0.01em]">
            Explore Causes &amp; Organizations
          </h1>
          <p className="mt-3 font-body text-lead leading-[1.6] text-cool-grey">
            Search public records, cause tags, and locations across the United States.
          </p>

          {/* Search */}
          <SearchBar
            value={searchQuery}
            onChange={v => { setSearchQuery(v); setCurrentPage(1) }}
            onSearch={q => { setSearchQuery(q); setDebouncedQuery(q); setCurrentPage(1) }}
            placeholder="Search by cause, city, community, name, or EIN…"
            className="mt-7 max-w-[640px]"
          />

          {/* Filters collapse/expand toggle.
              Phones get the full-screen FilterSheet (scrollable, thumb-sized
              controls); desktop expands the inline section. */}
          {searchMode === 'browse' && (
            <button
              onClick={() => {
                if (window.matchMedia('(max-width: 1023px)').matches) {
                  setFilterSheetOpen(true)
                } else {
                  setFiltersExpanded(!filtersExpanded)
                }
              }}
              className="mt-7 inline-flex items-center gap-2 px-4 py-2 rounded-full font-body text-small font-medium border transition-all duration-150"
              style={{
                backgroundColor: filtersExpanded || activeFilterCount > 0 ? '#F8F5F0' : 'transparent',
                borderColor: filtersExpanded || activeFilterCount > 0 ? '#E5E0DB' : '#E5E0DB',
                color: '#0A1628',
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="4" y1="6" x2="20" y2="6"/><line x1="8" y1="12" x2="16" y2="12"/><line x1="11" y1="18" x2="13" y2="18"/>
              </svg>
              Filters
              {activeFilterCount > 0 && (
                <span className="min-w-[16px] h-4 flex items-center justify-center bg-deep-navy text-soft-gold text-micro font-bold rounded-full px-1">
                  {activeFilterCount}
                </span>
              )}
              <svg
                width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                style={{ transform: filtersExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 150ms' }}
              >
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
          )}

          {/* Filters section — desktop inline expansion. No max-height clip:
              the old max-h-[500px] silently hid every control that wrapped
              past 500px (27 category pills + selects easily exceed it). */}
          <div className={filtersExpanded ? 'mt-4' : 'hidden'}>
            {/* Top filter toolbar — all breakpoints. Full filter set lives in the
                drawer (Filters button); the discovery toggles are surfaced here
                because they're the point of the directory. */}
            {searchMode === 'browse' && <div className="flex items-center gap-2 flex-wrap pb-4">
            {/* Discovery toggles — each keeps its own color (even when off) + a tooltip */}
            {[
              { key: 'hg', label: 'Hidden gems', tip: 'Small, financially healthy, lower profile orgs. A fresh set each week.', on: hiddenGem, color: '#C9A96E', textOn: '#0A1628',
                icon: <><path d="M6 3h12l4 6-10 13L2 9z"/><path d="M11 3 8 9l4 13 4-13-3-6"/><path d="M2 9h20"/></>,
                toggle: () => { setHiddenGem(!hiddenGem); setCurrentPage(1); scrollTop() } },
              { key: 'ns', label: 'Lower reported reserve', tip: 'Show organizations with a lower reported reserve metric. This is context, not a judgment of the work.', on: needsSupport, color: '#7C3AED', textOn: '#FFFFFF',
                icon: <><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 1 0-7.78 7.78L12 21.23l8.84-8.84a5.5 5.5 0 0 0 0-7.78z"/></>,
                toggle: () => { setNeedsSupport(!needsSupport); setCurrentPage(1); scrollTop() } },
              { key: 'rev', label: 'Has revenue data', tip: 'Show only orgs with reported financial data.', on: showOnlyWithRevenue, color: '#059669', textOn: '#FFFFFF',
                icon: <><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z"/></>,
                toggle: () => { setShowOnlyWithRevenue(!showOnlyWithRevenue); setCurrentPage(1); scrollTop() } },
            ].map(t => (
              <button
                key={t.key}
                onClick={t.toggle}
                title={t.tip}
                aria-pressed={t.on}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full font-body text-[12.5px] font-medium border transition-all duration-150"
                style={{
                  backgroundColor: t.on ? t.color : `${t.color}12`,
                  color: t.on ? t.textOn : '#374151',
                  borderColor: t.on ? t.color : `${t.color}59`,
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={t.on ? t.textOn : t.color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  {t.icon}
                </svg>
                {t.label}
              </button>
            ))}

            {activeFilterCount > 0 && (
              <button onClick={handleClearAll} className="font-body text-caption text-cool-grey hover:text-cool-grey transition-colors ml-1">
                Clear all
              </button>
            )}
          </div>}

          {/* Category quick-pills + state — all breakpoints */}
          {searchMode === 'browse' && <div className="mt-3 flex items-center gap-2 flex-wrap">
            {FILTER_CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => handleFilterChange(cat.id)}
                className="px-4 py-[6px] rounded-full font-body text-caption tracking-[0.02em] transition-all duration-150 border"
                style={{
                  backgroundColor: (cat.id === 'all' ? activeFilters.length === 0 : activeFilters.includes(cat.id)) ? '#C9A96E' : 'transparent',
                  color: (cat.id === 'all' ? activeFilters.length === 0 : activeFilters.includes(cat.id)) ? '#0A1628' : '#4B5563',
                  borderColor: (cat.id === 'all' ? activeFilters.length === 0 : activeFilters.includes(cat.id)) ? '#C9A96E' : '#E5E0DB',
                }}
              >
                {'emoji' in cat && cat.emoji ? `${cat.emoji} ` : ''}{cat.label}
              </button>
            ))}
            <div className="sm:ml-auto flex flex-wrap items-center gap-2">
              {/* Has a website */}
              <button
                onClick={() => { setHasWebsite(!hasWebsite); setCurrentPage(1); scrollTop() }}
                title="A working website you can visit to learn more"
                aria-pressed={hasWebsite}
                className="inline-flex items-center gap-1.5 h-[34px] px-3.5 rounded-full font-body text-caption font-medium border transition-all duration-150"
                style={{
                  backgroundColor: hasWebsite ? '#0EA5E9' : '#0EA5E912',
                  color: hasWebsite ? '#FFFFFF' : '#374151',
                  borderColor: hasWebsite ? '#0EA5E9' : '#0EA5E959',
                }}
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={hasWebsite ? '#FFFFFF' : '#0EA5E9'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                </svg>
                Has a website
              </button>
              {/* Open to volunteers — coming soon */}
              <div
                title="Volunteer listings are coming soon. Claim your organization to be among the first."
                className="inline-flex items-center gap-1.5 h-[34px] px-3.5 rounded-full font-body text-caption font-medium border border-dashed border-cool-grey/50 text-cool-grey/70 cursor-default select-none"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M18 11V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12"/><path d="M14 22l4-4-4-4"/><line x1="14" y1="18" x2="22" y2="18"/>
                </svg>
                Open to volunteers
                <span className="ml-0.5 px-1.5 py-0.5 rounded-full bg-soft-gold/20 text-micro font-semibold text-deep-gold leading-none">Soon</span>
              </div>
              {/* Proximity search */}
              <div className="inline-flex items-center gap-1 h-[34px]">
                <div className="relative inline-flex">
                  <input
                    type="text"
                    value={nearInput}
                    onChange={e => setNearInput(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter') {
                        const v = nearInput.trim()
                        setNear(v); setCurrentPage(1); scrollTop()
                        if (v) { searchParams.set('near', v); searchParams.set('radius_mi', String(radiusMi)) }
                        else { searchParams.delete('near'); searchParams.delete('radius_mi') }
                        setSearchParams(searchParams)
                      }
                      if (e.key === 'Escape') {
                        setNearInput(''); setNear(''); setCurrentPage(1); scrollTop()
                        searchParams.delete('near'); searchParams.delete('radius_mi')
                        setSearchParams(searchParams)
                      }
                    }}
                    onBlur={() => {
                      const v = nearInput.trim()
                      if (v !== near) {
                        setNear(v); setCurrentPage(1); scrollTop()
                        if (v) { searchParams.set('near', v); searchParams.set('radius_mi', String(radiusMi)) }
                        else { searchParams.delete('near'); searchParams.delete('radius_mi') }
                        setSearchParams(searchParams)
                      }
                    }}
                    placeholder="Zip or city, state"
                    aria-label="Filter by location (zip code or city, state)"
                    className="h-[34px] pl-3 pr-8 w-[148px] rounded-l-full font-body text-caption border outline-none transition-all duration-150"
                    style={{
                      backgroundColor: near ? '#C9A96E15' : 'transparent',
                      color: '#374151',
                      borderColor: near ? '#C9A96E' : '#E5E0DB',
                      borderRight: 'none',
                    }}
                  />
                  {/* Use my location button */}
                  <button
                    type="button"
                    title="Use my current location"
                    aria-label="Use my current location"
                    onClick={() => {
                      if (!navigator.geolocation) {
                        alert('Geolocation not available in your browser')
                        return
                      }
                      navigator.geolocation.getCurrentPosition(
                        ({ coords }) => {
                          fetch(`https://nominatim.openstreetmap.org/reverse?lat=${coords.latitude}&lon=${coords.longitude}&format=json`, {
                            headers: { 'Accept-Language': 'en', 'User-Agent': 'daanaa.org nonprofit directory' }
                          })
                            .then(r => r.json())
                            .then(d => {
                              const city = d.address?.city || d.address?.town || d.address?.village || ''
                              const state = d.address?.state_code || d.address?.state || ''
                              const loc = city && state ? `${city}, ${state}` : d.address?.postcode || ''
                              if (!loc) {
                                alert('Could not determine location from coordinates')
                                return
                              }
                              setNearInput(loc)
                              setNear(loc)
                              searchParams.set('near', loc)
                              searchParams.set('radius_mi', String(radiusMi))
                              setSearchParams(searchParams)
                              setCurrentPage(1)
                              scrollTop()
                            })
                            .catch(err => {
                              console.error('Reverse geocoding failed:', err)
                              alert('Location lookup failed. Try typing your city name.')
                            })
                        },
                        (error) => {
                          console.warn('Geolocation permission denied or unavailable:', error.message)
                          alert('Permission denied. Allow location access to use this feature.')
                        }
                      )
                    }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-cool-grey/40 hover:text-soft-gold transition-colors"
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="3"/>
                      <path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>
                      <path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z" strokeWidth="1.5"/>
                    </svg>
                  </button>
                </div>
                <select
                  value={radiusMi}
                  onChange={e => {
                    const r = Number(e.target.value)
                    setRadiusMi(r)
                    if (near) {
                      searchParams.set('radius_mi', String(r))
                      setSearchParams(searchParams)
                    }
                  }}
                  aria-label="Search radius in miles"
                  className="h-[34px] pl-2 pr-6 rounded-r-full font-body text-caption border outline-none appearance-none cursor-pointer transition-all duration-150"
                  style={{
                    backgroundColor: near ? '#C9A96E15' : 'transparent',
                    color: near ? '#0A1628' : '#9CA3AF',
                    borderColor: near ? '#C9A96E' : '#E5E0DB',
                    borderLeft: '1px solid',
                    borderLeftColor: near ? '#C9A96E80' : '#E5E0DB',
                  }}
                >
                  <option value={5}>5mi</option>
                  <option value={10}>10mi</option>
                  <option value={25}>25mi</option>
                  <option value={50}>50mi</option>
                </select>
              </div> {/* end proximity */}
              {/* Visibility-tier filter removed 2026-07-17 (founder + board:
                  tiers retired from all donor-facing surfaces — see
                  docs/BOARD_SIMULATION_2026_07_17_EVENING.md) */}
              {/* Revenue band */}
              <div className="inline-flex gap-3">
                <div>
                  <select
                    value={minRevenue}
                    onChange={(e) => handleMinRevenueChange(parseInt(e.target.value, 10))}
                    className="h-[34px] px-3 rounded-full bg-warm-cream border border-light-grey font-body text-caption font-semibold text-deep-navy outline-none focus:border-soft-gold transition-colors cursor-pointer"
                    title="Minimum annual revenue"
                  >
                    <option value={0}>$0</option>
                    <option value={150_000}>$150K</option>
                    <option value={700_000}>$700K</option>
                    <option value={5_000_000}>$5M</option>
                    <option value={25_000_000}>$25M</option>
                    <option value={100_000_000}>$100M</option>
                  </select>
                </div>
                <span className="text-cool-grey text-caption flex items-center">to</span>
                <div>
                  <select
                    value={maxRevenue === 500_000_000 ? 'unlimited' : maxRevenue}
                    onChange={(e) => handleMaxRevenueChange(e.target.value === 'unlimited' ? 500_000_000 : parseInt(e.target.value, 10))}
                    className="h-[34px] px-3 rounded-full bg-warm-cream border border-light-grey font-body text-caption font-semibold text-deep-navy outline-none focus:border-soft-gold transition-colors cursor-pointer"
                    title="Maximum annual revenue"
                  >
                    <option value={150_000}>$150K</option>
                    <option value={700_000}>$700K</option>
                    <option value={5_000_000}>$5M</option>
                    <option value={25_000_000}>$25M</option>
                    <option value={100_000_000}>$100M</option>
                    <option value="unlimited">No limit</option>
                  </select>
                </div>
              </div>
              {/* State */}
              <div className="relative">
                <select
                  value={stateFilter}
                  onChange={e => handleStateChange(e.target.value)}
                  aria-label="Filter by state"
                  className="appearance-none h-[34px] pl-3 pr-8 rounded-full font-body text-caption tracking-[0.02em] border transition-all duration-150 outline-none cursor-pointer"
                  style={{
                    backgroundColor: stateFilter ? '#C9A96E' : 'transparent',
                    color: stateFilter ? '#0A1628' : '#4B5563',
                    borderColor: stateFilter ? '#C9A96E' : '#E5E0DB',
                  }}
                >
                  <option value="">All States & Territories</option>
                  {US_STATES.map(([abbr, name]) => (
                    <option key={abbr} value={abbr}>{abbr} · {name}</option>
                  ))}
                  <optgroup label="Other Territories">
                    {US_TERRITORIES.map(([abbr, name]) => (
                      <option key={abbr} value={abbr}>{abbr} · {name}</option>
                    ))}
                  </optgroup>
                  <optgroup label="Armed Forces">
                    {US_MILITARY.map(([abbr, name]) => (
                      <option key={abbr} value={abbr}>{abbr} · {name}</option>
                    ))}
                  </optgroup>
                </select>
                <svg className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="6 9 12 15 18 9"/></svg>
              </div>
            </div>
          </div>}
          </div>

          {/* Subcategory pills — appear for every selected category, multi-select */}
          {searchMode === 'browse' && activeFilters.some(c => (NTEE_SUBCATEGORIES[c]?.length ?? 0) > 0) && (
            <div className="mt-3 space-y-2">
              {activeFilters.filter(c => (NTEE_SUBCATEGORIES[c]?.length ?? 0) > 0).map(catId => (
                <div key={catId} className="flex items-center gap-1.5 flex-wrap">
                  <span className="font-body text-micro uppercase tracking-[0.06em] text-cool-grey mr-1 shrink-0">
                    {FILTER_CATEGORIES.find(c => c.id === catId)?.label ?? catId}
                  </span>
                  {NTEE_SUBCATEGORIES[catId].map(sub => {
                    const on = subFilters.includes(sub.code)
                    return (
                      <button
                        key={sub.code}
                        onClick={() => handleSubChange(sub.code)}
                        className="px-3 py-1 rounded-full font-body text-label transition-all duration-150 border"
                        style={{
                          backgroundColor: on ? '#0A1628' : 'transparent',
                          color: on ? '#F5F0EB' : '#6B7280',
                          borderColor: on ? '#0A1628' : '#E5E0DB',
                        }}
                      >
                        {sub.label}
                      </button>
                    )
                  })}
                </div>
              ))}
            </div>
          )}

          {/* Clear all — always visible when any filter is active */}
          {activeFilterCount > 0 && (
            <div className="mt-2">
              <button
                onClick={handleClearAll}
                className="font-body text-caption text-cool-grey hover:text-cool-grey transition-colors"
              >
                Clear all filters
              </button>
            </div>
          )}

          {/* FilterSheet — mobile only */}
          <FilterSheet
            open={filterSheetOpen}
            onClose={() => setFilterSheetOpen(false)}
            activeCategory={activeFilters[0] ?? 'all'}
            stateFilter={stateFilter}
            sortBy={sortBy}
            sortOrder={sortOrder}
            minRevenue={minRevenue}
            maxRevenue={maxRevenue}
            verifiedRevenueOnly={verifiedRevenueOnly}
            cause={cause}
            onCategoryChange={(id) => { handleFilterChange(id) }}
            onStateChange={handleStateChange}
            onSortChange={(s) => {
              setSortBy(s)
              // Same rule as the desktop select: name reads A-Z,
              // score/revenue read high-first
              setSortOrder(s === 'organization_name' ? 'asc' : 'desc')
              setCurrentPage(1); scrollTop()
            }}
            onSortOrderChange={() => { setSortOrder(o => o === 'asc' ? 'desc' : 'asc'); setCurrentPage(1) }}
            onMinRevenueChange={handleMinRevenueChange}
            onMaxRevenueChange={handleMaxRevenueChange}
            onVerifiedRevenueChange={(checked) => { setVerifiedRevenueOnly(checked); setCurrentPage(1) }}
            onCauseChange={setCause}
            onClearAll={handleClearAll}
            resultCount={total}
          />
        </div>
      </div>

      {/* Results */}
      <div className="bg-warm-cream py-12 md:py-16">
        <div className="max-w-[1200px] mx-auto px-6 lg:px-12">

          {/* Browse mode — filters now live in the top toolbar, results full-width */}
          {searchMode === 'browse' && (
          <div>

            {/* Results column */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-4 mb-8 flex-wrap">
                <div>
                  <span className="font-body text-title font-semibold tracking-[-0.02em] text-deep-navy">
                    {total.toLocaleString()} {effectiveHiddenGem ? 'orgs you may not have heard of' : (searchQuery || activeFilters.length > 0 || stateFilter ? 'results' : 'organizations')}
                  </span>
                  {effectiveHiddenGem && (
                    <p className="font-body text-caption text-cool-grey mt-1 flex items-center flex-wrap gap-x-2 gap-y-1">
                      <span>Small, overlooked organizations · a fresh set each week.</span>
                      <button onClick={handleSeeAll} className="font-semibold text-soft-gold hover:text-bright-gold transition-colors">
                        See all 1.7M →
                      </button>
                    </p>
                  )}
                  {/* Location feedback: an unresolved location must never fail
                      silently — the results would look filtered while being
                      nationwide (2026-07-10 "Houston Texas" incident). */}
                  {near && !orgsLoading && orgsData && !orgsData.nearby && (
                    <p className="font-body text-caption text-alert-amber mt-1" role="status">
                      We couldn't find "{near}" — showing results without the location filter.
                      Try "City, ST" (like Houston, TX) or a zip code.
                    </p>
                  )}
                  {near && !orgsLoading && orgsData?.nearby && (
                    <p className="font-body text-caption text-cool-grey mt-1 flex items-center gap-2" role="status">
                      <span>
                        Near {orgsData.nearby.city}, {orgsData.nearby.state} · within {orgsData.nearby.radius_mi} mi
                      </span>
                      <button
                        onClick={() => {
                          nearFromSearchBarRef.current = false
                          setNear(''); setNearInput(''); setSearchQuery(''); setCurrentPage(1)
                        }}
                        className="font-semibold text-soft-gold hover:text-bright-gold transition-colors"
                      >
                        Clear
                      </button>
                    </p>
                  )}
                  {orgsData?.corrected_query && (
                    <p className="font-body text-caption text-cool-grey mt-1" role="status">
                      Showing results for "{orgsData.corrected_query}" — we didn't find any matches for "{searchQuery}"
                    </p>
                  )}
                  {hasRevenueFilter && !verifiedRevenueOnly && !effectiveHiddenGem && (
                    <p className="font-body text-caption text-cool-grey mt-1" role="status">
                      Includes organizations that haven't reported revenue — smaller nonprofits often file
                      a simpler return.{' '}
                      <button
                        onClick={() => { setVerifiedRevenueOnly(true); setCurrentPage(1) }}
                        className="font-semibold text-soft-gold hover:text-bright-gold transition-colors"
                      >
                        Show only reported revenue
                      </button>
                    </p>
                  )}
                  {(statsData?.irs_status_verified_at || statsData?.scores_last_updated) && (
                    <p className="font-body text-caption text-cool-grey mt-1">
                      Built from public IRS data
                      {statsData?.scores_last_updated && (
                        <> · Financial data as of {new Date(statsData.scores_last_updated).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</>
                      )}
                      {statsData?.irs_status_verified_at && (
                        <> · IRS status checked {new Date(statsData.irs_status_verified_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</>
                      )}
                    </p>
                  )}

                  {/* Active filter chips */}
                  {(searchQuery || activeFilters.length > 0 || subFilters.length > 0 || stateFilter || hasRevenueFilter || near) && (
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      {searchQuery && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-navy-mid/8 text-deep-navy font-body text-label">
                          "{searchQuery}"
                        </span>
                      )}
                      {useFusedResults && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-soft-gold/15 text-soft-gold font-body text-label" title="Results ranked by combining keyword matching and meaning, not by size or revenue">
                          Name + meaning
                        </span>
                      )}
                      {activeFilters.map(f => (
                        <button
                          key={f}
                          onClick={() => handleFilterChange(f)}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-soft-gold/10 text-soft-gold font-body text-label hover:bg-soft-gold/20 transition-colors"
                        >
                          {RAIL_CATEGORIES.find(c => c.id === f)?.label} ×
                        </button>
                      ))}
                      {subFilters.map(code => (
                        <button
                          key={code}
                          onClick={() => handleSubChange(code)}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-deep-navy/8 text-deep-navy font-body text-label hover:bg-deep-navy/15 transition-colors"
                        >
                          {subLabelOf(code)} ×
                        </button>
                      ))}
                      {stateFilter && (
                        <button
                          onClick={() => handleStateChange('')}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-soft-gold/10 text-soft-gold font-body text-label hover:bg-soft-gold/20 transition-colors"
                        >
                          {stateFilter} ×
                        </button>
                      )}
                      {hasRevenueFilter && (
                        <button
                          onClick={() => { handleMinRevenueChange(0); handleMaxRevenueChange(500_000_000) }}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-soft-gold/10 text-soft-gold font-body text-label hover:bg-soft-gold/20 transition-colors"
                        >
                          {revLabel} ×
                        </button>
                      )}
                      {near && (
                        <button
                          onClick={() => {
                            setNear(''); setNearInput(''); setCurrentPage(1); scrollTop()
                            searchParams.delete('near'); searchParams.delete('radius_mi')
                            setSearchParams(searchParams)
                          }}
                          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-soft-gold/10 text-soft-gold font-body text-label hover:bg-soft-gold/20 transition-colors"
                        >
                          {near} · {radiusMi}mi ×
                        </button>
                      )}
                      <button onClick={handleClearAll} className="font-body text-label text-cool-grey hover:text-deep-navy transition-colors">
                        Clear all
                      </button>
                    </div>
                  )}
                  {subFilters.includes('X70') && (
                    <p className="mt-1.5 font-body text-label text-cool-grey">
                      The IRS classifies Hindu, Sikh, Jain, and other non-Western faith traditions under this code. This reflects official IRS data, not our own categorization.
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  {/* Sort + direction — hidden while gems is on (static weekly order) */}
                  {effectiveHiddenGem ? (
                    <span className="hidden sm:inline font-body text-small text-cool-grey italic">Shuffled weekly</span>
                  ) : (
                    <div className="hidden sm:flex items-center gap-2">
                      <span className="font-body text-body text-cool-grey">Sort:</span>
                      <select
                        value={sortBy}
                        onChange={(e) => {
                          setSortBy(e.target.value)
                          // Shuffle is random (no sort order); Name reads A-Z; score/revenue read high-first
                          setSortOrder(e.target.value === 'organization_name' || e.target.value === 'random' ? 'asc' : 'desc')
                          setCurrentPage(1)
                        }}
                        aria-label="Sort organizations by"
                        className="bg-transparent font-body text-body text-deep-navy outline-none cursor-pointer"
                      >
                        {SORT_OPTIONS.map(opt => (
                          <option key={opt.id} value={opt.id}>{opt.label}</option>
                        ))}
                      </select>
                      <button
                        onClick={() => { setSortOrder(o => o === 'asc' ? 'desc' : 'asc'); setCurrentPage(1) }}
                        title={sortOrder === 'asc' ? 'Ascending: tap to reverse' : 'Descending: tap to reverse'}
                        aria-label={`Sort direction: ${sortOrder === 'asc' ? 'ascending' : 'descending'}`}
                        className="inline-flex items-center justify-center w-7 h-7 rounded-md border border-light-grey text-cool-grey hover:text-deep-navy hover:border-cool-grey transition-colors"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                          style={{ transform: sortOrder === 'asc' ? 'rotate(180deg)' : 'none', transition: 'transform 150ms' }}>
                          <line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/>
                        </svg>
                      </button>
                      {sortBy === 'random' && (
                        <button
                          onClick={() => {
                            // Generate a new shuffle seed while keeping filters
                            const newSeed = Math.random().toString(36).slice(2, 11)
                            sessionShuffleRef.current = newSeed
                            localStorage.setItem('daanaa_session_seed', newSeed)
                            // Increment counter to trigger refetch with new seed
                            setRandomizeCount(c => c + 1)
                          }}
                          title="Randomize the list with a new shuffle"
                          aria-label="Randomize list"
                          className="inline-flex items-center justify-center px-3 py-1 rounded-md border border-light-grey text-cool-grey hover:text-deep-navy hover:border-cool-grey transition-colors font-body text-small whitespace-nowrap"
                        >
                          Randomize
                        </button>
                      )}
                    </div>
                  )}
                  {/* Grid/List toggle */}
                  <div className="hidden md:flex items-center gap-1 border border-light-grey rounded-lg p-1">
                    <button
                      onClick={() => setViewMode('grid')}
                      title="Grid view"
                      aria-label="Grid view"
                      className="p-1.5 rounded transition-colors"
                      style={{ backgroundColor: viewMode === 'grid' ? '#E5E0DB' : 'transparent' }}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={viewMode === 'grid' ? '#0A1628' : '#A89F94'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
                      </svg>
                    </button>
                    <button
                      onClick={() => setViewMode('list')}
                      title="List view"
                      aria-label="List view"
                      className="p-1.5 rounded transition-colors"
                      style={{ backgroundColor: viewMode === 'list' ? '#E5E0DB' : 'transparent' }}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={viewMode === 'list' ? '#0A1628' : '#A89F94'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/>
                        <line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              {/* Results grid / list */}
              {activeLoading ? (
                viewMode === 'list' ? (
                  <div className="flex flex-col gap-2">
                    {Array.from({ length: 10 }).map((_, i) => (
                      <div key={i} className="bg-white border border-light-grey rounded-xl px-5 py-4 animate-pulse flex items-center gap-4">
                        <div className="w-[110px] space-y-1.5">
                          <div className="h-5 w-20 bg-light-grey rounded-full" />
                          <div className="h-5 w-10 bg-light-grey rounded-full" />
                        </div>
                        <div className="flex-1 space-y-1.5">
                          <div className="h-4 w-3/4 bg-light-grey rounded" />
                          <div className="h-3 w-1/2 bg-light-grey rounded" />
                        </div>
                        <div className="hidden md:block w-[130px] space-y-1.5 text-right">
                          <div className="h-3 w-20 bg-light-grey rounded ml-auto" />
                          <div className="h-3 w-16 bg-light-grey rounded ml-auto" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {Array.from({ length: 9 }).map((_, i) => (
                      <div key={i} className="bg-white border border-light-grey rounded-xl p-5 animate-pulse">
                        <div className="flex items-center gap-2 mb-3">
                          <div className="h-5 w-20 bg-light-grey rounded-full" />
                          <div className="h-5 w-10 bg-light-grey rounded-full ml-auto" />
                        </div>
                        <div className="h-5 w-3/4 bg-light-grey rounded mb-2" />
                        <div className="h-4 w-1/2 bg-light-grey rounded mb-4" />
                        <div className="h-4 w-24 bg-light-grey rounded-full mb-4" />
                        <div className="h-3 w-full bg-light-grey rounded" />
                        <div className="h-3 w-2/3 bg-light-grey rounded mt-2" />
                      </div>
                    ))}
                  </div>
                )
              ) : activeError ? (
                <div className="text-center py-16">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#6B7280" strokeWidth="1.5" className="mx-auto mb-4">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  <p className="font-body text-lead text-cool-grey">Unable to load organizations.</p>
                  <p className="font-body text-body text-cool-grey mt-2">Check that the API is running, then refresh.</p>
                </div>
              ) : organizations.length > 0 ? (
                <>
                  {viewMode === 'list' ? (
                    <div className="flex flex-col gap-2">
                      {organizations.map((org) => (
                        <OrgCardApi key={org.EIN} org={org} listView />
                      ))}
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                      {organizations.map((org) => (
                        <OrgCardApi key={org.EIN} org={org} />
                      ))}
                    </div>
                  )}

                  {/* Pagination */}
                  {totalPages > 1 && (
                    <div className="mt-12 flex items-center justify-center gap-2">
                      <button
                        onClick={() => { setCurrentPage(p => Math.max(1, p - 1)); scrollTop() }}
                        disabled={currentPage === 1}
                        aria-label="Previous page"
                        className="w-8 h-8 flex items-center justify-center rounded-full text-cool-grey hover:text-deep-navy disabled:opacity-30 transition-colors"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
                      </button>
                      {(() => {
                        const pages: (number | '…')[] = []
                        if (totalPages <= 7) {
                          for (let i = 1; i <= totalPages; i++) pages.push(i)
                        } else {
                          pages.push(1)
                          if (currentPage > 3) pages.push('…')
                          for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) pages.push(i)
                          if (currentPage < totalPages - 2) pages.push('…')
                          pages.push(totalPages)
                        }
                        return pages.map((page, idx) =>
                          page === '…' ? (
                            <span key={`ellipsis-${idx}`} className="w-8 h-8 flex items-center justify-center font-body text-body text-cool-grey">…</span>
                          ) : (
                            <button
                              key={page}
                              onClick={() => { setCurrentPage(page); scrollTop() }}
                              className="w-8 h-8 flex items-center justify-center rounded-full font-body text-body transition-all duration-150"
                              style={{
                                backgroundColor: currentPage === page ? '#C9A96E' : 'transparent',
                                color: currentPage === page ? '#0A1628' : '#6B7280',
                              }}
                            >
                              {page}
                            </button>
                          )
                        )
                      })()}
                      <button
                        onClick={() => { setCurrentPage(p => Math.min(totalPages, p + 1)); scrollTop() }}
                        disabled={currentPage === totalPages}
                        aria-label="Next page"
                        className="w-8 h-8 flex items-center justify-center rounded-full text-cool-grey hover:text-deep-navy disabled:opacity-30 transition-colors"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-16 max-w-[420px] mx-auto">
                  <div className="w-14 h-14 rounded-full bg-light-grey/60 flex items-center justify-center mx-auto mb-5">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#A89F94" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />
                    </svg>
                  </div>
                  <p className="font-body text-title-sm font-semibold text-deep-navy mb-2">Nothing matched those filters</p>
                  <p className="font-body text-body text-cool-grey mb-6 leading-relaxed">
                    Try removing a filter, shortening the keyword, or browsing by cause instead.
                  </p>
                  <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                    <button
                      onClick={handleClearAll}
                      className="px-5 py-2.5 rounded-xl bg-soft-gold text-deep-navy font-body text-small font-semibold hover:bg-bright-gold transition-colors"
                    >
                      Clear all filters
                    </button>
                    <Link
                      to="/"
                      className="px-5 py-2.5 rounded-xl border border-light-grey text-cool-grey font-body text-small font-medium hover:border-soft-gold/40 hover:text-deep-navy transition-colors"
                    >
                      Browse by cause
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </div>
          )} {/* end browse mode */}

        </div>
      </div>
    </div>
  )
}
