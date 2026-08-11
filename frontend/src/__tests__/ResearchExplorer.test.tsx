import React from 'react'
import { render, screen, waitFor, within } from '@testing-library/react'
import '@testing-library/jest-dom'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import ResearchDashboard from '../pages/ResearchDashboard'
import ResearchExplorer from '../pages/ResearchExplorer'

const snapshot = {
  metadata: {
    total_organizations: 1740806,
    data_period: '2026-06-01',
    version: 'v1.0',
    generated_at: '2026-08-11T03:30:43.269127',
    disclaimer: 'This dashboard reflects public data available to Daanaa at the time of processing.',
  },
  revenue_bands: [
    { operating_model: 'Activity_Programming', revenue_band_number: 0, count: 9138, pct_of_total: 0.5, avg_peer_percentile: 50.0, avg_months_reserve: 47.4 },
    { operating_model: 'Activity_Programming', revenue_band_number: 1, count: 8845, pct_of_total: 0.49, avg_peer_percentile: 50.0, avg_months_reserve: 37.5 },
  ],
  categories: [
    { ntee1: 'B', ntee_label: 'Education', count: 189928, pct_of_total: 10.4, avg_revenue: 6565723.6, avg_peer_percentile: 51.9 },
  ],
  states: [
    { state: 'CA', count: 195161, pct: 10.7, avg_revenue: 7617647.5, avg_peer_percentile: 48.4 },
    { state: 'TX', count: 142668, pct: 7.8, avg_revenue: 4953486.5, avg_peer_percentile: 50.3 },
  ],
  spending: [
    { tier: '1_Full_Context', tier_name: 'Full Context', count: 363141, median_program_spend: 77.4, p25_program_spend: 21.3, p75_program_spend: 91.6 },
  ],
  entity_types: {
    total: 1740806,
    public_charity: 1389420,
    private_foundation: 127325,
    unclassified: 224061,
    pct_public_charity: 79.8,
    pct_private_foundation: 7.3,
    pct_unclassified: 12.9,
  },
  v6: {
    total_active: 1740806,
    total_placed: 1737032,
    unscored_count: 3774,
    placement_coverage_pct: 99.8,
    tiers: [
      { key: '1_Full_Context', name: 'Full Context', description: 'Compared with organizations of similar type, size, and region.', has_peer_comparison: true, count: 452733, pct: 26.0, avg_peer_group_size: 840.0, avg_program_pct: 60.8, avg_months_reserve: 29.4 },
      { key: '4_Archetype_Only', name: 'Archetype Only', description: 'We can describe the kind of work, but the public record does not yet support a peer comparison.', has_peer_comparison: false, count: 431762, pct: 24.8, avg_peer_group_size: null, avg_program_pct: 66.7, avg_months_reserve: 23.4 },
    ],
  },
  monthly_changes: [
    { month: '2026-06', new_registrations: 8050, revocations: 0, net: 8050, is_batch_revocation: false },
  ],
}

function mockSnapshot() {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => snapshot,
  } as Response)
}

beforeEach(() => {
  mockSnapshot()
  ;(window as unknown as { ResizeObserver: typeof ResizeObserver }).ResizeObserver = class {
    observe() {}
    disconnect() {}
    unobserve() {}
  }
  ;(window as unknown as { IntersectionObserver: typeof IntersectionObserver }).IntersectionObserver = class {
    observe() {}
    disconnect() {}
    unobserve() {}
    takeRecords() {
      return []
    }
  }
})

describe('research explorer handoff', () => {
  it('shows a prominent explorer link from the research library page', async () => {
    render(
      <MemoryRouter initialEntries={['/research']}>
        <Routes>
          <Route path="/research" element={<ResearchDashboard />} />
        </Routes>
      </MemoryRouter>
    )

    expect(await screen.findByRole('link', { name: /open the explorer/i })).toHaveAttribute(
      'href',
      '/research/explorer'
    )
  })

  it('renders the states view from the static research snapshot', async () => {
    render(
      <MemoryRouter initialEntries={['/research/explorer?view=states']}>
        <Routes>
          <Route path="/research/explorer" element={<ResearchExplorer />} />
        </Routes>
      </MemoryRouter>
    )

    expect(await screen.findByRole('button', { name: 'States' })).toBeInTheDocument()
    const table = screen.getByRole('region', { name: /visible aggregate rows/i })
    await waitFor(() => expect(within(table).getAllByText('CA').length).toBeGreaterThan(0))
    expect(screen.getByRole('button', { name: /download csv/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /copy share link/i })).toBeInTheDocument()
  })
})
