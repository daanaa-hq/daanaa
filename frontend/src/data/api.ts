// API client for Daanaa backend — maps to daanaa_api.py (Flask, port 5000)
const API_BASE = import.meta.env.VITE_API_URL || '';

// Hard cap on every request: a slow or hung backend must surface as an error
// the UI can show, never an indefinite blank loading state.
const REQUEST_TIMEOUT_MS = 10_000;

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const { headers: extraHeaders, ...rest } = options ?? {};
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(extraHeaders ?? {}) },
      ...rest,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch (err) {
    if (err instanceof DOMException && (err.name === 'TimeoutError' || err.name === 'AbortError')) {
      throw new Error('The server is taking too long to respond. Please try again.');
    }
    throw err;
  }
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

// Matches registry_enriched columns returned by daanaa_api.py
export interface ApiOrganization {
  EIN: string;
  organization_name: string;
  NTEE1: string | null;
  NTEECC: string | null;             // full subcategory code e.g. "B24"
  CITY: string | null;
  STATE: string | null;
  total_revenue: number | null;
  total_revenue_formatted: string | null;
  ntee1_percentile: number | null;   // broad NTEE1 percentile (legacy compat)
  ntee1_total_orgs: number | null;   // total orgs in NTEE1 peer group
  source: string | null;
  // Peer-group scoring (NTEECC + revenue band)
  revenue_band: string | null;       // 'Micro' | 'Small' | 'Medium' | 'Large' | 'Major'
  peer_percentile: number | null;    // percentile within best-fit peer group
  peer_rank: number | null;          // rank within peer group (1 = top)
  peer_total: number | null;         // total orgs in peer group
  peer_group: string | null;         // e.g. "B24:Medium" or "B:Medium" or "B"
  // Data provenance
  latest_tax_year: number | null;
  data_source: string | null;        // 'propublica' | 'irs_soi' | 'nccs' | '' etc.
  updated_at: string | null;         // ISO timestamp of last DB write
  merit_tier?: string | null;        // 'Beacon' | 'Torch' | 'Candle' | 'Spark'
  merit_score?: number | null;       // 0-100 financial-health score
  merit_band?: string | null;        // journey band e.g. 'Blazing' | 'Burning Bright' | 'Steady Flame' | 'Growing' | 'Just Starting'
  score_tier?: string | null;        // 'full' | 'partial' | 'revenue_only' — data confidence level
  // v4.0 Financial Health — separate scale from visibility
  financial_health?: 'Strong' | 'Stable' | 'Inspiring' | null;  // relative to peer model+band
  operating_model?: string | null;   // 'Direct_Service' | 'Mission_Infrastructure' | etc. (8 models)
  peer_cell_size?: number | null;    // number of orgs in peer cell for ranking
  v4_revenue_band?: number | null;   // numeric band 0-7 (model-specific)
  v4_metrics?: Record<string, unknown> | null;        // detailed metrics (optional)
  v4_percentiles?: Record<string, unknown> | null;    // percentile data (optional)
  has_mission: boolean | null;
  has_website: boolean | null;
  // ProPublica enrichment fields
  months_of_reserve: number | null;   // (net_assets / total_expenses) * 12
  net_assets: number | null;          // totnetassetend = assets - liabilities
  total_expenses: number | null;      // totfuncexpns
  total_liabilities: number | null;
  employee_count: number | null;      // W-3 form employee count (NCCS)
  ruling_date: string | null;         // IRS ruling date for tax-exempt status
  zipcode: string | null;
  address: string | null;
  activ1: string | null;              // NTEE activity code 1 (NCCS)
  activ2: string | null;
  activ3: string | null;
  program_expense_pct: number | null; // program revenue as % of total expenses
  revenue_3yr_avg?: number | null;   // 3-year average revenue (smooths grant cycles)
  nccs_year: number | null;
  cause_tags?: string[] | null;           // LLM-extracted cause tags (3-5 per org)
  donate_url?: string | null;             // direct giving page found on org site (Donorbox, etc.)
  donate_platform?: string | null;        // 'donorbox' | 'networkforgood' | 'classy' | 'mightycause' | 'paypal'
  donate_url_status?: string | null;      // 'ok' | 'dead' | 'unknown' — null = not yet checked
  // Fused search annotation (from /api/search only)
  match_sources?: ('keyword' | 'semantic')[] | null;
  rrf_score?: number | null;
  mission?: string | null;               // truncated at 300 chars in list view; full text in detail
  mission_source?: string | null;        // 'ai_ntee'|'ai_haiku'|'ai_web'|'lucido'|'claimed'|null
  website?: string | null;
  website_status?: string | null;        // 'ok' = verified live & on-domain; else fall back to EIN record
  // Data provenance — which fields are AI-generated vs verified
  data_badges?: {
    mission?: string | null;   // 'ai_ntee' | 'scraped' | 'claimed' | null
    donate?: string | null;    // 'beta' | 'provider' | 'claimed' | null
    website?: string | null;   // 'ok' | 'redirected' | null
    tags?: string | null;      // 'ai_generated' (beta) | 'claimed' | null
  } | null;
  // Claim status — 'pending' | 'letter_sent' | 'verified' | 'active' | null
  claim_status?: string | null;
  irs_status_verified_at?: string | null;
  similar_organizations?: ApiOrganization[];
  category_rank?: number;
  category_total?: number;
  state_category_rank?: number;
  state_category_total?: number;
  ntee1_rank?: number | null;
  state_ntee1_percentile?: number | null;
  // Financial context — stewardship-aligned assessment (P3, P4, P5, P6, P9)
  financial_context?: {
    status: 'DATA_INCOMPLETE' | 'VERIFIED_HEALTHY' | 'FINANCIAL_NOTE';
    confidence: 'LOW' | 'MEDIUM' | 'HIGH';
    months_reserve: number | null;
    peer_model: string;
    peer_baseline: number;
    peer_healthy_range: [number, number];
    gap_from_baseline: number | null;
    explanation: string;
    data_issues: string[];
  } | null;
}

export interface ApiCategory {
  code: string;
  name: string;
  count: number;
  avg_revenue: number;
}

export interface ApiStats {
  total_organizations: number;
  with_revenue: number;
  total_revenue_sum: number;
  avg_revenue: number;
  top_states: { STATE: string; count: number }[];
  methodology_version: string;
  scores_last_updated: string | null;
  financial_records: number;
  with_reserve_data: number;
  reserve_health: {
    insolvent: number;
    at_risk: number;
    minimal: number;
    healthy: number;
  } | null;
  irs_status_verified_at?: string | null;
}

export interface ApiSectorHealth {
  code: string;
  name: string;
  total_orgs: number;
  has_reserve: number;
  avg_months_reserve: number | null;
  insolvent: number;
  at_risk: number;
  minimal: number;
  healthy: number;
  at_risk_pct: number;
  avg_program_pct: number | null;
  avg_revenue: number | null;
}

export async function getSectorHealth(): Promise<{ sectors: ApiSectorHealth[] }> {
  return fetchJson('/api/sector-health');
}

// GET /api/organizations
export async function getOrganizations(params?: {
  ntee?: string;           // NTEE1 major letter filter
  sub?: string;            // NTEECC subcategory prefix, e.g. 'E21'
  state?: string;          // 2-letter state abbreviation
  q?: string;              // name / EIN / city search — tokenized, word-order-independent
  sort?: string;           // 'total_revenue' | 'organization_name' | 'ntee1_percentile'
  order?: string;          // 'asc' | 'desc'
  page?: number;
  per_page?: number;
  min_revenue?: number;
  max_revenue?: number;
  min_percentile?: number;    // legacy — filter by ntee1_percentile >= value
  min_tier?: string;          // 'Beacon' | 'Torch' | 'Candle' | 'Spark'
  direct_link?: boolean;      // true = only orgs with a detected donate URL
  has_website?: boolean;      // true = only orgs with a verified, live website
  recent?: boolean;           // true = only orgs whose latest filing is 2022 or later
  cause?: string;             // matches a cause tag (e.g. "food bank", "mental health")
}): Promise<{
  organizations: ApiOrganization[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}> {
  const sp = new URLSearchParams();
  if (params?.ntee)     sp.set('ntee', params.ntee);
  if (params?.sub)      sp.set('sub', params.sub);
  if (params?.state)    sp.set('state', params.state);
  if (params?.q)        sp.set('q', params.q);
  if (params?.sort)     sp.set('sort', params.sort);
  if (params?.order)    sp.set('order', params.order);
  if (params?.page)            sp.set('page', String(params.page));
  if (params?.per_page)        sp.set('per_page', String(params.per_page));
  if (params?.min_revenue != null) sp.set('min_revenue', String(params.min_revenue));
  if (params?.max_revenue != null) sp.set('max_revenue', String(params.max_revenue));
  if (params?.min_percentile != null) sp.set('min_percentile', String(params.min_percentile));
  if (params?.min_tier) sp.set('min_tier', params.min_tier);
  if (params?.direct_link) sp.set('direct_link', '1');
  if (params?.has_website) sp.set('has_website', '1');
  if (params?.recent) sp.set('recent', '1');
  if (params?.cause) sp.set('cause', params.cause);
  return fetchJson(`/api/organizations?${sp.toString()}`);
}

// GET /api/organizations/:ein
export async function getOrganization(ein: string): Promise<ApiOrganization> {
  return fetchJson(`/api/organizations/${ein}`);
}

// GET /api/search/semantic — vector similarity search
export async function getSemanticOrganizations(q: string, limit = 25): Promise<{
  results: ApiOrganization[];
  query: string;
  mode: string;
  total: number;
}> {
  const sp = new URLSearchParams({ q, limit: String(limit) });
  return fetchJson(`/api/search/semantic?${sp.toString()}`);
}

// GET /api/search — RRF-fused keyword + semantic search with match_sources
export async function getFusedSearch(q: string): Promise<{
  results: ApiOrganization[];
  query: string;
  mode: string;
  total: number;
}> {
  const sp = new URLSearchParams({ q });
  return fetchJson(`/api/search?${sp.toString()}`);
}

// GET /api/organizations/:ein/financials
export interface ApiFinancialRecord {
  tax_prd_yr: number;
  totrevenue: number | null;
  totfuncexpns: number | null;
  totassetsend: number | null;
  totliabend: number | null;
  totnetassetend: number | null;
  totcntrbgfts: number | null;
  totprgmrevnue: number | null;
  compnsatncurrofcr: number | null;
  pdf_url: string | null;
}

export async function getFinancials(ein: string): Promise<{
  ein: string;
  financials: ApiFinancialRecord[];
  total: number;
}> {
  return fetchJson(`/api/organizations/${ein}/financials`);
}

// GET /api/organizations/:ein/score-history
export interface ScoreSnapshot {
  snapshot_date: string;
  peer_percentile: number;
  rev_pct: number;
  rsv_pct: number;
  reserve_ratio: number;
  total_revenue: number | null;
  total_assets: number | null;
  peer_group: string | null;
  group_key: string | null;
  group_size: number | null;
  scorer_version: string;
}

export async function getScoreHistory(ein: string): Promise<{
  ein: string;
  history: ScoreSnapshot[];
  total: number;
}> {
  return fetchJson(`/api/organizations/${ein}/score-history`);
}

// GET /api/ntee-categories
export async function getCategories(): Promise<{ categories: ApiCategory[] }> {
  return fetchJson('/api/ntee-categories');
}

// GET /api/stats
export async function getStats(): Promise<ApiStats> {
  return fetchJson('/api/stats');
}

export interface NteeCoverage {
  code: string;
  total: number;
  with_mission: number;
  scored: number;
  visible: number;
  coverage: number;
}

// GET /api/ntee-coverage
export async function getNteeCoverage(): Promise<{ categories: NteeCoverage[] }> {
  return fetchJson('/api/ntee-coverage');
}

// --- Waitlist ---

export interface WaitlistEntry {
  id: number;
  email: string;
  ein: string | null;
  source: 'newsletter' | 'claiming';
  status: 'new' | 'contacted' | 'converted' | 'dismissed';
  notes: string | null;
  created_at: string;
}

export async function submitWaitlist(
  email: string,
  source: 'newsletter' | 'claiming',
  ein?: string,
): Promise<void> {
  await fetchJson('/api/waitlist', {
    method: 'POST',
    body: JSON.stringify({ email, source, ein }),
  });
}

// Anonymous org-findability feedback. Sends ONLY ein + reason. No donor
// data. Fire-and-forget — a failed beacon must never block the donor.
export async function submitLinkFeedback(
  ein: string,
  reason: 'not_found' | 'broken',
): Promise<void> {
  try {
    await fetch(`${API_BASE}/api/link-feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ein, reason }),
      keepalive: true,
    });
  } catch { /* anonymous best-effort; never surface to the donor */ }
}

export async function getAdminWaitlist(
  adminKey: string,
  params?: { source?: string; status?: string },
): Promise<{ entries: WaitlistEntry[]; total: number }> {
  const sp = new URLSearchParams();
  if (params?.source) sp.set('source', params.source);
  if (params?.status) sp.set('status', params.status);
  return fetchJson(`/api/admin/waitlist?${sp}`, {
    headers: { 'X-Admin-Key': adminKey },
  });
}

export async function updateWaitlistEntry(
  id: number,
  updates: { status?: string; notes?: string },
  adminKey: string,
): Promise<WaitlistEntry> {
  return fetchJson(`/api/admin/waitlist/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
    headers: { 'X-Admin-Key': adminKey },
  });
}

export async function deleteWaitlistEntry(id: number, adminKey: string): Promise<void> {
  await fetchJson(`/api/admin/waitlist/${id}`, {
    method: 'DELETE',
    headers: { 'X-Admin-Key': adminKey },
  });
}

export interface SimilarResult extends ApiOrganization {
  similarity_score: number;
}

export async function getSimilarOrgs(ein: string, options?: {
  limit?: number;
  diamonds?: boolean;
}): Promise<{ results: SimilarResult[]; mode: string; diamonds_only: boolean }> {
  const params = new URLSearchParams();
  if (options?.limit) params.set('limit', String(options.limit));
  if (options?.diamonds) params.set('diamonds', '1');
  return fetchJson(`/api/organizations/${ein}/similar?${params}`);
}

export async function submitFeedback(
  message: string,
  opts?: { email?: string; page?: string; category?: string },
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      email: opts?.email || '',
      page: opts?.page || '',
      category: opts?.category || '',
    }),
  });
  if (!res.ok && res.status !== 204) throw new Error('feedback failed');
}
