// Guided discovery state management, URL encoding, and result building

export interface DiscoveryState {
  step: 1 | 2 | 3 | 4 | 5
  intent: string[]
  causes: string[]
  place: string
  connection: string[]
  mix: 'focused' | 'broad'
}

export interface DiscoveryFilters {
  ntee?: string
  state?: string
  near?: string
  radius_mi?: number
  has_website?: boolean
  open_to_volunteers?: boolean
  revenue_band?: string[]
}

// URL encode/decode
export function encodeDiscoveryState(state: DiscoveryState): URLSearchParams {
  const params = new URLSearchParams()
  if (state.intent.length > 0) params.set('intent', state.intent.join(','))
  if (state.causes.length > 0) params.set('causes', state.causes.join(','))
  if (state.place) params.set('place', state.place)
  if (state.connection.length > 0) params.set('connection', state.connection.join(','))
  if (state.mix) params.set('mix', state.mix)
  return params
}

export function decodeDiscoveryState(params: URLSearchParams): Partial<DiscoveryState> {
  const state: Partial<DiscoveryState> = {
    step: 1,
    intent: [],
    causes: [],
    place: 'nationwide',
    connection: [],
    mix: 'focused',
  }

  const intent = params.get('intent')
  if (intent) state.intent = intent.split(',').filter(Boolean)

  const causes = params.get('causes')
  if (causes) state.causes = causes.split(',').filter(Boolean)

  const place = params.get('place')
  if (place) state.place = place

  const connection = params.get('connection')
  if (connection) state.connection = connection.split(',').filter(Boolean)

  const mix = params.get('mix')
  if (mix === 'broad' || mix === 'focused') state.mix = mix

  return state
}

// Map discovery choices to API filters
export function mapToDirectoryFilters(state: DiscoveryState): DiscoveryFilters {
  const filters: DiscoveryFilters = {}

  // Cause mapping (NTEE1 codes)
  if (state.causes.length > 0) {
    filters.ntee = state.causes.join(',')
  }

  // Place mapping
  if (state.place === 'nationwide') {
    // no location filter
  } else if (state.place === 'near-me') {
    // TODO: Get user's geolocation coordinates and pass as near param
    // For now, this would require client-side geolocation API call
  } else if (state.place.startsWith('custom-zip:')) {
    const zipOrCity = state.place.replace('custom-zip:', '')
    filters.near = zipOrCity
    filters.radius_mi = 25
  } else if (state.place.startsWith('custom-state:')) {
    const stateCode = state.place.replace('custom-state:', '')
    filters.state = stateCode
  } else if (state.place.startsWith('zip:')) {
    // Legacy format
    const zip = state.place.replace('zip:', '')
    filters.near = zip
    filters.radius_mi = 25
  } else if (state.place.startsWith('state:')) {
    // Legacy format
    const stateCode = state.place.replace('state:', '')
    filters.state = stateCode
  }

  // Connection filters
  if (state.connection.includes('website')) {
    filters.has_website = true
  }
  if (state.connection.includes('volunteer')) {
    filters.open_to_volunteers = true
  }
  if (state.connection.includes('smaller')) {
    // Revenue bands 0-1: Micro (<150K), Professional (150K-700K)
    filters.revenue_band = ['0', '1']
  }

  return filters
}

// Explain why an organization appears
export function explainInclusion(
  org: any,
  state: DiscoveryState,
  causeLabelMap: Record<string, string>
): string {
  const parts: string[] = []

  // Add place
  if (state.place === 'nationwide') {
    parts.push('nationwide')
  } else if (state.place.startsWith('zip:')) {
    const zip = state.place.replace('zip:', '')
    parts.push(`in the ${zip} area`)
  } else if (state.place.startsWith('state:')) {
    const stateCode = state.place.replace('state:', '')
    parts.push(`in ${stateCode}`)
  }

  // Add causes
  if (state.causes.length > 0) {
    const labels = state.causes
      .map((c) => causeLabelMap[c] || c)
      .filter(Boolean)
    if (labels.length > 0) {
      parts.push(labels.join(', '))
    }
  }

  // Add connection preference if specific
  const connectionLabels: string[] = []
  if (state.connection.includes('website') && org.website_status === 'ok') {
    connectionLabels.push('has a website')
  }
  if (state.connection.includes('volunteer') && org.open_to_volunteers) {
    connectionLabels.push('has volunteer opportunities')
  }
  if (state.connection.includes('smaller') && org.revenue_band <= 1) {
    connectionLabels.push('is a smaller, community-rooted organization')
  }

  if (connectionLabels.length > 0) {
    parts.push(connectionLabels.join(' and '))
  }

  if (parts.length === 0) {
    return 'Matches your criteria'
  }

  return `Included because ${parts.join(' and ')}.`
}

// Count how many criteria an organization matches
export function countCriteriaMatch(org: any, state: DiscoveryState): number {
  let count = 0

  // Location match
  if (
    state.place !== 'nationwide' &&
    (org.state === state.place.replace('state:', '') ||
      org.zipcode === state.place.replace('zip:', ''))
  ) {
    count += 1
  }

  // Connection matches
  if (state.connection.includes('website') && org.website_status === 'ok') {
    count += 1
  }
  if (state.connection.includes('volunteer') && org.open_to_volunteers) {
    count += 1
  }
  if (state.connection.includes('smaller') && org.revenue_band <= 1) {
    count += 1
  }
  if (state.connection.includes('recent-filing') && org.tax_prd_yr >= 2024 - 1) {
    count += 1
  }

  return count
}

// Build shortlist from organizations
export function buildShortlist(
  allOrgs: any[],
  state: DiscoveryState,
  maxResults: number = 25
): {
  closeMatches: any[]
  nearbyMatches: any[]
  discoveryMix: any[]
  total: number
} {
  if (allOrgs.length === 0) {
    return {
      closeMatches: [],
      nearbyMatches: [],
      discoveryMix: [],
      total: 0,
    }
  }

  // Score each org by criteria match count
  const scored = allOrgs.map((org) => ({
    org,
    score: countCriteriaMatch(org, state),
  }))

  // Sort by score descending
  scored.sort((a, b) => b.score - a.score)

  // Split into groups
  const closeMatches = scored
    .filter((s) => s.score >= 2)
    .map((s) => s.org)
    .slice(0, Math.ceil(maxResults * 0.5))

  const nearbyMatches = scored
    .filter((s) => s.score === 1)
    .map((s) => s.org)
    .slice(0, Math.ceil(maxResults * 0.35))

  let discoveryMix: any[] = []
  if (state.mix === 'broad' && closeMatches.length + nearbyMatches.length < maxResults) {
    // Fill with some random orgs from the same cause/location
    const remaining = scored
      .filter((s) => s.score === 0)
      .map((s) => s.org)
    const fillSpace = maxResults - (closeMatches.length + nearbyMatches.length)
    discoveryMix = remaining.slice(0, Math.ceil(fillSpace))
  }

  return {
    closeMatches,
    nearbyMatches,
    discoveryMix,
    total: closeMatches.length + nearbyMatches.length + discoveryMix.length,
  }
}
