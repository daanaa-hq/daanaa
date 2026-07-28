import React from 'react'
import { render, screen } from '@testing-library/react'
import AnswerCard from '../components/AnswerCard'
import type { ApiOrganization } from '../data/api'

// Minimal-but-complete fixture -- every required ApiOrganization field gets a
// safe default, tests override only what they're exercising. Matches the
// factory pattern the project doesn't have yet for this large interface;
// kept local to this file since AnswerCard is the only consumer so far.
function makeOrg(overrides: Partial<ApiOrganization> = {}): ApiOrganization {
  return {
    EIN: '123456789',
    organization_name: 'Save the World Inc',
    NTEE1: 'P',
    NTEECC: 'P20',
    CITY: 'Austin',
    STATE: 'TX',
    total_revenue: 500000,
    total_revenue_formatted: '$500,000',
    source: 'propublica',
    revenue_band: 'Small',
    peer_percentile: null,
    peer_rank: null,
    peer_total: null,
    peer_group: null,
    latest_tax_year: 2024,
    data_source: 'propublica',
    updated_at: '2026-01-01T00:00:00Z',
    has_mission: true,
    has_website: true,
    months_of_reserve: 6,
    net_assets: 100000,
    total_expenses: 450000,
    total_liabilities: 20000,
    employee_count: 5,
    ruling_date: null,
    zipcode: '78701',
    street_address: '123 Main St',
    program_expense_pct: 84,
    nccs_year: 2024,
    v5_context: null,
    cohort_context: null,
    org_status: null,
    irs_revoked: null,
    ...overrides,
  } as ApiOrganization
}

describe('AnswerCard', () => {
  describe('revoked branch', () => {
    it('shows the revoked banner when org_status is revoked', () => {
      render(<AnswerCard org={makeOrg({ org_status: 'revoked' })} />)
      expect(screen.getByText(/tax-exempt status was automatically revoked/i)).toBeInTheDocument()
      expect(screen.getByText(/would not be tax-deductible/i)).toBeInTheDocument()
    })

    it('shows the revoked banner when irs_revoked is 1 (org_status not yet synced)', () => {
      render(<AnswerCard org={makeOrg({ org_status: 'active', irs_revoked: 1 })} />)
      expect(screen.getByText(/tax-exempt status was automatically revoked/i)).toBeInTheDocument()
    })

    it('links to the IRS/ProPublica record, not a donate action', () => {
      render(<AnswerCard org={makeOrg({ org_status: 'revoked', EIN: '987654321' })} />)
      const link = screen.getByText(/view the irs record/i).closest('a')
      expect(link).toHaveAttribute('href', expect.stringContaining('987654321'))
      expect(screen.queryByText(/donate/i)).not.toBeInTheDocument()
    })

    it('revoked status takes priority even if the org also has a v5 score (defensive -- should never happen upstream, but the card must not show a health signal for a revoked org)', () => {
      render(<AnswerCard org={makeOrg({
        org_status: 'revoked',
        v5_context: {
          archetype: { key: 'a', label: 'A' },
          band: { key: 'b', label: 'B' },
          peer_group: { label: 'P', org_count: 10 },
          score: { percentile: 80, health_signal: 'HEALTHY' },
          benchmarks: { reserves_months: { p25: 1, p50: 2, p75: 3, your_value: 2 }, healthy_rate_peer: 50 },
          donor_explanation: 'x',
        },
      })} />)
      expect(screen.getByText(/tax-exempt status was automatically revoked/i)).toBeInTheDocument()
      expect(screen.queryByText(/financially steady/i)).not.toBeInTheDocument()
    })
  })

  describe('scored branch (health signal chips)', () => {
    const withScore = (health_signal: 'HEALTHY' | 'STABLE' | 'CAUTION', percentile = 75) => makeOrg({
      v5_context: {
        archetype: { key: 'a', label: 'A' },
        band: { key: 'b', label: 'B' },
        peer_group: { label: 'P', org_count: 10 },
        score: { percentile, health_signal },
        benchmarks: { reserves_months: { p25: 1, p50: 2, p75: 3, your_value: 2 }, healthy_rate_peer: 50 },
        donor_explanation: 'x',
      },
    })

    it('HEALTHY renders "Financially steady" -- never the raw enum word', () => {
      render(<AnswerCard org={withScore('HEALTHY')} />)
      expect(screen.getByText('Financially steady')).toBeInTheDocument()
      expect(screen.queryByText(/healthy/i)).not.toBeInTheDocument()
    })

    it('STABLE renders "Managing well"', () => {
      render(<AnswerCard org={withScore('STABLE')} />)
      expect(screen.getByText('Managing well')).toBeInTheDocument()
    })

    it('CAUTION renders "Could use community support" -- never the word CAUTION (research-copy-voice rule)', () => {
      render(<AnswerCard org={withScore('CAUTION')} />)
      expect(screen.getByText('Could use community support')).toBeInTheDocument()
      expect(screen.queryByText(/caution/i)).not.toBeInTheDocument()
    })

    it('shows the peer percentile alongside the health signal', () => {
      render(<AnswerCard org={withScore('HEALTHY', 90)} />)
      expect(screen.getByText(/top 10%/i)).toBeInTheDocument()
    })

    it('shows the program-expense-pct chip when present', () => {
      render(<AnswerCard org={withScore('HEALTHY')} />)
      expect(screen.getByText('84¢')).toBeInTheDocument()
    })
  })

  describe('no-data branch (the majority case, ~82% of public orgs)', () => {
    it('shows the dignity-layer copy, not a blank space, when v5_context is null', () => {
      render(<AnswerCard org={makeOrg({ v5_context: null })} />)
      expect(screen.getByText(/appears in our nonprofit records/i)).toBeInTheDocument()
      expect(screen.getByText(/common for smaller and local organizations/i)).toBeInTheDocument()
    })

    it('does not show a health-signal chip or the word CAUTION/HEALTHY/STABLE', () => {
      render(<AnswerCard org={makeOrg({ v5_context: null })} />)
      expect(screen.queryByText(/financially steady/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/managing well/i)).not.toBeInTheDocument()
    })

    it('appends "Doing the work since {year}" when ruling_date is present', () => {
      render(<AnswerCard org={makeOrg({ v5_context: null, ruling_date: '1994-03-15' })} />)
      expect(screen.getByText(/doing the work since 1994/i)).toBeInTheDocument()
    })

    it('omits the "since" sentence entirely when ruling_date is null -- no "since null" or empty year', () => {
      render(<AnswerCard org={makeOrg({ v5_context: null, ruling_date: null })} />)
      expect(screen.queryByText(/doing the work since/i)).not.toBeInTheDocument()
    })

    it('handles a malformed ruling_date gracefully (no crash, no garbage year)', () => {
      render(<AnswerCard org={makeOrg({ v5_context: null, ruling_date: 'not-a-date' })} />)
      expect(screen.queryByText(/doing the work since/i)).not.toBeInTheDocument()
    })

    it('renders the no-data branch even when v5_context is present but score is missing (malformed/partial data, defensive)', () => {
      // TS wouldn't normally allow this shape, but the API is an external
      // boundary -- verify the component degrades safely if the backend
      // ever sends a v5_context without a score sub-object.
      const org = makeOrg({ v5_context: { archetype: { key: 'a', label: 'A' } } as never })
      render(<AnswerCard org={org} />)
      expect(screen.getByText(/appears in our nonprofit records/i)).toBeInTheDocument()
    })
  })
})
