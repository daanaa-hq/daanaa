// API client for Daanaa backend — maps to daanaa_api.py (Flask, port 5000)
export const API_BASE = import.meta.env.VITE_API_URL || '';

// All API calls route to home server (droplet is stateless — frontend only).
// On localhost, port 5000 is daanaa_api.py (Flask). On production, Cloudflare
// routes /api/* to the home server backend (never to the droplet).
const getApiBase = (path: string): string => {
  if (path.startsWith('/api/')) {
    if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
      return 'http://localhost:5000';
    }
    // On production, fetch through same origin — Cloudflare worker routes /api/* to home
    return '';
  }
  return API_BASE;
};

// Hard cap on every request: a slow or hung backend must surface as an error
// the UI can show, never an indefinite blank loading state.
const REQUEST_TIMEOUT_MS = 10_000;

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const { headers: extraHeaders, ...rest } = options ?? {};
  let response: Response;
  const apiBase = getApiBase(path);
  try {
    response = await fetch(`${apiBase}${path}`, {
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
  // v5.0 peer-based financial context (archetype × revenue band). Present only
  // for orgs we have financials for; null otherwise (then cohort_context fills in).
  v5_context?: {
    archetype: { key: string; label: string };
    band: { key: string; label: string };
    peer_group: { label: string; org_count: number };
    score: { percentile: number; health_signal: 'HEALTHY' | 'STABLE' | 'CAUTION' };
    benchmarks: {
      reserves_months: { p25: number; p50: number; p75: number; your_value: number | null };
      healthy_rate_peer: number;
    };
    donor_explanation: string;
  } | null;
  // Cause-cohort context for UNSCORED orgs (no v5_context of their own).
  // The typical financial shape of this org's NTEE cause-cohort, drawn from
  // scored orgs — NOT a statement about this org's own finances.
  cohort_context?: {
    median_reserve: number;
    p25: number;
    p75: number;
    healthy_rate: number;
    n: number;                       // scored orgs the typical rests on
    level: 'subcategory' | 'broad';  // how narrow the cause-cohort is
    ntee_code: string;
  } | null;
  // v4.0 Financial Health — separate scale from visibility
  financial_health?: 'Strong' | 'Stable' | 'Inspiring' | null;  // relative to peer model+band
  operating_model?: string | null;   // 'Direct_Service' | 'Mission_Infrastructure' | etc. (8 models)
  peer_cell_size?: number | null;    // number of orgs in peer cell for ranking
  v4_revenue_band?: number | null;   // numeric band 0-7 (model-specific)
  v4_metrics?: Record<string, unknown> | null;        // detailed metrics (optional)
  v4_percentiles?: Record<string, unknown> | null;    // percentile data (optional)
  has_mission: boolean | null;
  has_website: boolean | null;
  is_hidden_gem?: boolean | null;
  // ProPublica enrichment fields
  months_of_reserve: number | null;   // (net_assets / total_expenses) * 12
  net_assets: number | null;          // totnetassetend = assets - liabilities
  total_expenses: number | null;      // totfuncexpns
  total_liabilities: number | null;
  employee_count: number | null;      // W-3 form employee count (NCCS)
  ruling_date: string | null;         // IRS ruling date for tax-exempt status
  zipcode: string | null;
  street_address: string | null;
  // Only present on the search.db-fallback path (revoked orgs never get a
  // precomputed file -- precompute_orgs.py filters org_status='active' at
  // the source, so a revoked org's page is only reachable via this fallback).
  org_status?: string | null;
  irs_revoked?: number | null;
  activ1: string | null;              // NTEE activity code 1 (NCCS)
  activ2: string | null;
  activ3: string | null;
  program_expense_pct: number | null; // program revenue as % of total expenses
  revenue_3yr_avg?: number | null;   // 3-year average revenue (smooths grant cycles)
  nccs_year: number | null;
  cause_tags?: string[] | null;           // LLM-extracted cause tags (3-5 per org)
  // Fused search annotation (from /api/search only)
  match_sources?: ('keyword' | 'semantic')[] | null;
  rrf_score?: number | null;
  mission?: string | null;               // truncated at 300 chars in list view; full text in detail
  mission_source?: string | null;        // 'ai_ntee'|'ai_haiku'|'ai_web'|'lucido'|'claimed'|null
  website?: string | null;
  website_status?: string | null;        // 'ok' = verified live & on-domain; else fall back to EIN record
  donate_url?: string | null;            // Donation link -- ONLY render if donate_url_status is 'beta' or 'claimed'
  donate_url_status?: string | null;     // real values seen in prod: dead|no_link_found|blocked_or_restricted|
                                          // mismatch|rejected|withheld|human_review|unknown|beta|claimed (2026-07-10:
                                          // comment corrected -- 'ai_suggested' never appears in the live data)
  donate_confidence?: number | null;     // 0-100; NULL for ~99.7% of orgs -- do not gate on this, use status instead
  volunteer_url?: string | null;         // Volunteer signup/interest link (added 2026-07-10, pipeline-sourced)
  phone?: string | null;                 // Organization phone number from 990
  // Data provenance — which fields are AI-generated vs verified
  data_badges?: {
    mission?: string | null;   // 'ai_ntee' | 'scraped' | 'claimed' | null
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
  // Governance & volunteerism
  seeking_board_members?: boolean | null;
  // Events (claimed orgs with posted volunteer events)
  upcoming_events_count?: number | null;
  // Phase 2 enrichment: contact & programs signals (AI-assisted)
  contact?: {
    email?: string;
    phone?: string;
    street_address?: string;
    executive_name?: string;
    board_size?: number;
    contact_verified_date?: string;
    contact_sources?: string[];
  } | null;
  programs?: {
    program_descriptions?: string[];
    service_area?: string;
    years_active?: number;
    accreditations?: string[];
    programs_verified_date?: string;
    program_sources?: string[];
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

export async function getSectorHealth(): Promise<{ generated_at?: string; sectors: ApiSectorHealth[] }> {
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
  tier?: string;              // visibility level: 'beacon' | 'torch' | 'candle' | 'spark'
  has_website?: boolean;      // true = only orgs with a verified, live website
  verified_revenue?: boolean; // true = only orgs with verified revenue data (exclude unknown)
  hidden_gem?: boolean;       // true = only hidden gems (small, healthy, low-profile)
  needs_funding?: boolean;    // true = only orgs with under 6 months of reserve
  open_to_volunteers?: boolean; // true = only orgs with a claimed volunteer contact
  cause?: string;             // matches a cause tag (e.g. "food bank", "mental health")
  near?: string;              // zip or "City, ST" — filters by proximity
  radius_mi?: number;         // radius in miles (default 25)
}): Promise<{
  organizations: ApiOrganization[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
  // Present only when zero-result rescue via typo correction happened (P3)
  corrected_query?: string;
  // Search Phase 2: query intent classification for routing/instrumentation
  search_intent?: {
    query: string;
    intent: 'cause' | 'organization' | 'ambiguous';
    confidence: number;
    reason: string;
    suggested_path: 'semantic_embedding' | 'fts_exact' | 'fts_with_semantic_rerank';
  };
  // Present only when the API resolved a `near` location; its absence while
  // `near` was sent means the location could not be resolved (show feedback,
  // never silently drop the filter).
  nearby?: { city: string; state: string; radius_mi: number };
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
  if (params?.tier) sp.set('tier', params.tier);
  if (params?.has_website) sp.set('has_website', '1');
  if (params?.verified_revenue) sp.set('verified_revenue', '1');
  if (params?.hidden_gem) sp.set('hidden_gem', '1');
  if (params?.needs_funding) sp.set('needs_funding', '1');
  if (params?.open_to_volunteers) sp.set('open_to_volunteers', '1');
  if (params?.cause) sp.set('cause', params.cause);
  if (params?.near) sp.set('near', params.near);
  if (params?.radius_mi) sp.set('radius_mi', String(params.radius_mi));
  return fetchJson(`/api/organizations?${sp.toString()}`);
}

// GET /api/organizations/:ein
export async function getOrganization(ein: string, options?: { includeEnrichment?: boolean }): Promise<ApiOrganization> {
  const url = options?.includeEnrichment ? `/api/organizations/${ein}?include_enrichment=1` : `/api/organizations/${ein}`;
  return fetchJson(url);
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
  // true = same city/state match (Tiers 1-3); false = nationwide NTEE1
  // fallback (Tier 4) with no locality guarantee -- the UI must not claim
  // "near [CITY]" when this is false (2026-07-10 eng review, cross-model
  // tension 2). Optional because precompute_similar_orgs.py needs a full
  // production run to backfill every org; older cached entries lack it.
  is_local?: boolean;
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

// --- Guild ---

export interface VendorBenefit {
  id: number
  vendor_name: string
  category: string
  code: string
  description: string
  discount_label: string
  website_url: string | null
  how_to_use: string | null
  milestone_tier: number
}

export async function getGuildBenefits(): Promise<VendorBenefit[]> {
  return fetchJson('/api/guild/benefits')
}

export async function getGuildMemberCount(): Promise<{ member_count: number }> {
  return fetchJson('/api/guild/member-count')
}

export async function submitGuildWaitlist(email: string, ein?: string): Promise<void> {
  try {
    await fetchJson('/api/waitlist', {
      method: 'POST',
      body: JSON.stringify({ email, source: 'guild_waitlist', ein }),
    })
  } catch (e: unknown) {
    // 409 = already on list — not an error from UX perspective
    if (e instanceof Error && e.message.includes('409')) return
    throw e
  }
}

// ── Service area ────────────────────────────────────────────────────────────

export type ServiceAreaType = 'local' | 'regional' | 'statewide' | 'nationwide' | 'international'

export interface ServiceArea {
  area_type: ServiceAreaType | null
  area_values: string[]
  updated_at: string | null
}

export async function getServiceArea(ein: string): Promise<ServiceArea> {
  return fetchJson(`${API_BASE}/api/org/${ein}/service-area`)
}

export async function putServiceArea(
  ein: string,
  token: string,
  area_type: ServiceAreaType,
  area_values: string[],
): Promise<{ ok: boolean }> {
  return fetchJson(`${API_BASE}/api/org/${ein}/service-area`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ verification_token: token, area_type, area_values }),
  })
}

// ── Volunteer events ────────────────────────────────────────────────────────

export type EventType = 'volunteer' | 'community' | 'fundraiser' | 'networking'

export interface VolunteerEvent {
  id: number
  ein: string
  title: string
  description: string | null
  event_date: string          // YYYY-MM-DD
  start_time: string | null   // HH:MM
  end_time: string | null
  location_city: string | null
  location_state: string | null
  location_zip: string | null
  is_virtual: boolean
  signup_url: string | null
  contact_email: string | null
  capacity: number | null
  status: 'active' | 'filled' | 'cancelled' | 'expired'
  event_type: EventType
  short_id: string | null
  min_age: number | null
  expected_hours: number | null
  skill_level: 'any' | 'beginner' | 'intermediate' | 'skilled' | null
  what_to_bring: string | null
  waiver_url: string | null
  parking_info: string | null
  coordinator_name: string | null
  signup_count: number
  org_name?: string | null
  org_mission?: string | null
  created_at: string
  updated_at: string
  source_url?: string | null
  source_checked_at?: string | null
  discovery_status?: 'confirmed' | 'unconfirmed'
  ai_generated?: boolean
}

export interface EventAttendee {
  name: string
  age_group: 'child' | 'teen' | 'adult' | 'senior'
}

export interface EventSignupResult {
  ok: boolean
  booking_token: string
  total_count: number
  cancel_url: string
  idempotent?: boolean
}

export interface OrgSignup {
  id: number
  contact_name: string
  contact_email: string
  attendees: EventAttendee[]
  total_count: number
  status: 'confirmed' | 'cancelled' | 'attended' | 'no_show'
  hours_verified: number | null
  hours_verified_at: string | null
  created_at: string
}

export interface OrgContacts {
  general_email?: string
  general_phone?: string
  mailing_address?: string
  volunteer_name?: string
  volunteer_email?: string
  volunteer_phone?: string
  donor_name?: string
  donor_email?: string
  events_name?: string
  events_email?: string
  media_name?: string
  media_email?: string
  website?: string
  facebook_url?: string
  instagram_url?: string
  linkedin_url?: string
  twitter_url?: string
  youtube_url?: string
}

export interface VolunteerEventSearchParams {
  zip?: string
  city?: string
  state?: string
  date_from?: string
  date_to?: string
  ntee?: string
  event_type?: EventType
  virtual?: boolean
  limit?: number
  offset?: number
}

export async function searchVolunteerEvents(
  params: VolunteerEventSearchParams,
): Promise<{ events: VolunteerEvent[]; count: number }> {
  const q = new URLSearchParams()
  if (params.zip)        q.set('zip', params.zip)
  if (params.city)       q.set('city', params.city)
  if (params.state)      q.set('state', params.state)
  if (params.date_from)  q.set('date_from', params.date_from)
  if (params.date_to)    q.set('date_to', params.date_to)
  if (params.ntee)       q.set('ntee', params.ntee)
  if (params.event_type) q.set('event_type', params.event_type)
  if (params.virtual)    q.set('virtual', '1')
  if (params.limit)      q.set('limit', String(params.limit))
  if (params.offset)     q.set('offset', String(params.offset))
  return fetchJson(`${API_BASE}/api/volunteer-events?${q}`)
}

export async function getEventDetail(id: number): Promise<VolunteerEvent> {
  return fetchJson(`${API_BASE}/api/events/${id}`)
}

export async function signupForEvent(
  eventId: number,
  payload: {
    contact_name: string
    contact_email: string
    attendees?: EventAttendee[]
    idempotency_key?: string
  },
): Promise<EventSignupResult> {
  return fetchJson(`${API_BASE}/api/events/${eventId}/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function cancelEventSignup(
  eventId: number,
  bookingToken: string,
): Promise<{ ok: boolean }> {
  return fetchJson(`${API_BASE}/api/events/${eventId}/cancel-booking`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ booking_token: bookingToken }),
  })
}

export async function getOrgContactsPublic(ein: string): Promise<{ contacts: OrgContacts }> {
  return fetchJson(`${API_BASE}/api/org/${ein}/contacts`)
}

export async function getPortalContacts(
  ein: string,
  idToken: string,
): Promise<{ contacts: OrgContacts }> {
  return fetchJson(`${API_BASE}/api/portal/contacts?ein=${ein}`, {
    headers: { Authorization: `Bearer ${idToken}` },
  })
}

export async function updatePortalContacts(
  ein: string,
  contacts: Partial<OrgContacts>,
  idToken: string,
): Promise<{ contacts: OrgContacts }> {
  return fetchJson(`${API_BASE}/api/portal/contacts`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${idToken}` },
    body: JSON.stringify({ ein, ...contacts }),
  })
}

export async function getPortalEvents(
  ein: string,
  idToken: string,
  all?: boolean,
): Promise<{ events: VolunteerEvent[] }> {
  const q = all ? '?all=1' : ''
  return fetchJson(`${API_BASE}/api/portal/events?ein=${ein}${all ? '&all=1' : ''}`, {
    headers: { Authorization: `Bearer ${idToken}` },
  })
}

export async function createPortalEvent(
  ein: string,
  event: Partial<VolunteerEvent> & { title: string; event_date: string },
  idToken: string,
): Promise<VolunteerEvent> {
  return fetchJson(`${API_BASE}/api/portal/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${idToken}` },
    body: JSON.stringify({ ein, ...event }),
  })
}

export async function updatePortalEvent(
  eventId: number,
  updates: Partial<VolunteerEvent>,
  idToken: string,
): Promise<VolunteerEvent> {
  return fetchJson(`${API_BASE}/api/portal/events/${eventId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${idToken}` },
    body: JSON.stringify(updates),
  })
}

export async function cancelPortalEvent(
  eventId: number,
  reason: string,
  idToken: string,
): Promise<{ ok: boolean; notified: number }> {
  return fetchJson(`${API_BASE}/api/portal/events/${eventId}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${idToken}` },
    body: JSON.stringify({ reason }),
  })
}

export async function getEventAttendees(
  eventId: number,
  idToken: string,
): Promise<{ signups: OrgSignup[]; total: number }> {
  return fetchJson(`${API_BASE}/api/portal/events/${eventId}/attendees`, {
    headers: { Authorization: `Bearer ${idToken}` },
  })
}

export async function verifyEventHours(
  eventId: number,
  verifications: Array<{ signup_id: number; hours: number; attended: boolean }>,
  idToken: string,
): Promise<{ ok: boolean; updated: number }> {
  return fetchJson(`${API_BASE}/api/portal/events/${eventId}/verify-hours`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${idToken}` },
    body: JSON.stringify({ verifications }),
  })
}

export async function getOrgVolunteerEvents(
  ein: string,
  opts?: { all?: boolean },
): Promise<{ events: VolunteerEvent[] }> {
  const q = opts?.all ? '?all=1' : ''
  return fetchJson(`${API_BASE}/api/org/${ein}/volunteer-events${q}`)
}

export async function createVolunteerEvent(
  ein: string,
  token: string,
  event: Pick<VolunteerEvent, 'title' | 'event_date'> & Partial<Omit<VolunteerEvent, 'id' | 'ein' | 'status' | 'org_name' | 'created_at' | 'updated_at'>>,
): Promise<VolunteerEvent> {
  return fetchJson(`${API_BASE}/api/org/${ein}/volunteer-events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...event, verification_token: token }),
  })
}

export async function updateVolunteerEvent(
  id: number,
  token: string,
  updates: Partial<Omit<VolunteerEvent, 'id' | 'ein' | 'org_name' | 'created_at' | 'updated_at'>>,
): Promise<VolunteerEvent> {
  return fetchJson(`${API_BASE}/api/volunteer-events/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...updates, verification_token: token }),
  })
}

export async function cancelVolunteerEvent(id: number, token: string): Promise<void> {
  await fetchJson(`${API_BASE}/api/volunteer-events/${id}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ verification_token: token }),
  })
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

// ── Nonprofit portal auth ────────────────────────────────────────────────────

export interface ClaimedOrg {
  ein: string
  claim_status: string
  verified_at: string | null
  organization_name: string | null
  city: string | null
  state: string | null
}

export async function linkFirebaseToClaim(
  ein: string,
  verification_token: string,
  idToken: string,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/claim/link-firebase`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${idToken}` },
    body: JSON.stringify({ ein, verification_token }),
  })
  if (!res.ok) throw new Error('link failed')
}

export async function getMyOrgs(idToken: string): Promise<ClaimedOrg[]> {
  const res = await fetch(`${API_BASE}/api/claim/my-orgs`, {
    headers: { Authorization: `Bearer ${idToken}` },
  })
  if (!res.ok) throw new Error('my-orgs failed')
  const data = await res.json()
  return data.orgs ?? []
}

export async function getPortalToken(ein: string, idToken: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/claim/portal-token?ein=${encodeURIComponent(ein)}`, {
    headers: { Authorization: `Bearer ${idToken}` },
  })
  if (!res.ok) throw new Error('portal-token failed')
  const data = await res.json()
  return data.verification_token
}

// Context & Recall System types/fetchers removed 2026-07-10 — the feature's
// UI (MacroContextCard, KnowledgeGraphCard) was cut after founder review:
// CPI index level was mislabeled as inflation %, and the "knowledge graph"
// entities were raw NTEE code letters. Backend tables + /recall endpoint
// still exist with no consumer; see memory finding-macro-context-card-crash.

