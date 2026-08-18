import React from 'react'
import { render, screen } from '@testing-library/react'
import WhatTheyDo from '../components/WhatTheyDo'
import WhyTrustThem from '../components/WhyTrustThem'
import HowToHelp from '../components/HowToHelp'
import type { ApiOrganization } from '../data/api'

// Task #16 (Codex suggestion #2): cover missing-data null-safety returns,
// provenance labels, mission casing, expense-percentage branch logic for
// WhatTheyDo/WhyTrustThem/HowToHelp -- the three narrative sections that
// make up the org page's What/Why/How structure. Fixture mirrors the
// minimal-but-complete pattern from AnswerCard.test.tsx; only the fields
// these three components actually read are given real values, everything
// else defaults to a safe null/undefined via the cast.
function makeOrg(overrides: Partial<ApiOrganization> = {}): ApiOrganization {
  return {
    EIN: '123456789',
    organization_name: 'Save the World Inc',
    NTEE1: 'P',
    NTEECC: 'P20',
    CITY: 'Austin',
    STATE: 'TX',
    total_revenue: null,
    total_revenue_formatted: null,
    revenue_display: null,
    revenue_display_is_estimate: false,
    source: 'propublica',
    revenue_band: null,
    peer_percentile: null,
    peer_rank: null,
    peer_total: null,
    peer_group: null,
    latest_tax_year: 2024,
    data_source: 'propublica',
    updated_at: '2026-01-01T00:00:00Z',
    has_mission: false,
    has_website: false,
    months_of_reserve: null,
    net_assets: null,
    total_expenses: null,
    total_liabilities: null,
    employee_count: null,
    ruling_date: null,
    zipcode: '78701',
    street_address: '123 Main St',
    program_expense_pct: null,
    nccs_year: null,
    v5_context: null,
    cohort_context: null,
    org_status: null,
    irs_revoked: null,
    mission: null,
    mission_source: null,
    programs: null,
    irs_program_narrative: null,
    leadership_info: null,
    program_expenses: null,
    management_expenses: null,
    fundraising_expenses: null,
    ...overrides,
  } as ApiOrganization
}

describe('WhatTheyDo', () => {
  it('returns null when there is no mission, programs, or IRS narrative', () => {
    const { container } = render(<WhatTheyDo org={makeOrg()} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders a shouted ALL-CAPS mission in sentence case', () => {
    render(<WhatTheyDo org={makeOrg({
      mission: 'TO IMPLEMENT AND ADMINISTER VARIOUS COMMUNITY ACTION PROGRAMS DESIGNED TO COMBAT POVERTY.',
      mission_source: 'irs_990',
    })} />)
    expect(screen.getByText(/To implement and administer/)).toBeInTheDocument()
    expect(screen.queryByText(/TO IMPLEMENT/)).not.toBeInTheDocument()
  })

  it('leaves an already-normal-case mission untouched', () => {
    const text = 'Supports global outreach programs rooted in community service.'
    render(<WhatTheyDo org={makeOrg({ mission: text, mission_source: 'claimed' })} />)
    expect(screen.getByText(text)).toBeInTheDocument()
  })

  it('shows a provenance label for AI-generated missions', () => {
    render(<WhatTheyDo org={makeOrg({
      mission: 'A community organization.',
      mission_source: 'ai_ntee',
    })} />)
    expect(screen.getByText(/AI-generated from nonprofit classification/)).toBeInTheDocument()
  })

  it('shows no provenance badge text for irs_990-sourced missions (task #13)', () => {
    render(<WhatTheyDo org={makeOrg({
      mission: 'A community organization.',
      mission_source: 'irs_990',
    })} />)
    // None of the known AI/claimed/directory labels should render for irs_990
    expect(screen.queryByText(/AI-generated|AI-synthesized|AI-extracted|nonprofit directory|own description/)).not.toBeInTheDocument()
  })
})

describe('WhyTrustThem', () => {
  it('returns null when there is no financial, governance, or verification data', () => {
    const { container } = render(<WhyTrustThem org={makeOrg({ latest_tax_year: null })} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('does not claim "solid financial position" when there is no supporting data', () => {
    // total_revenue null, months_of_reserve null, but revenue_display_is_estimate
    // true -- this is exactly the false-confidence bug fixed in e6e1173f67d:
    // the old fallback copy defaulted to a positive claim whenever
    // months_of_reserve was null, regardless of whether ANY data backed it.
    render(<WhyTrustThem org={makeOrg({
      revenue_display: 'Under $50,000',
      revenue_display_is_estimate: true,
    })} />)
    expect(screen.queryByText(/solid financial position/)).not.toBeInTheDocument()
    expect(screen.getByText(/don't know enough/)).toBeInTheDocument()
  })

  it('shows the real revenue figure when total_revenue is present, not the estimate', () => {
    render(<WhyTrustThem org={makeOrg({
      total_revenue: 750000,
      months_of_reserve: 4,
    })} />)
    // formatCurrency abbreviates ($750K, not $750,000) -- match the label
    // text, not a hardcoded expectation of the exact formatted string.
    expect(screen.getByText('Annual revenue').nextSibling).toHaveTextContent('$750K')
    expect(screen.queryByText('Under $50,000')).not.toBeInTheDocument()
  })

  it('shows peer comparison only when peer_total and peer_percentile are both present', () => {
    const { rerender } = render(<WhyTrustThem org={makeOrg({ peer_total: null, peer_percentile: 80 })} />)
    expect(screen.queryByText('Peer group size')).not.toBeInTheDocument()

    rerender(<WhyTrustThem org={makeOrg({ peer_total: 100, peer_percentile: 80, peer_group: 'Human Services' })} />)
    expect(screen.getByText('Peer group size')).toBeInTheDocument()
  })
})

describe('HowToHelp', () => {
  it('returns null when there is no allocation data', () => {
    const { container } = render(<HowToHelp org={makeOrg()} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('hides the expense breakdown when parts do not reconcile with total_expenses', () => {
    // Regression guard for the 2026-08-16/17 incident (LESSONS.md): parts
    // summing to ~2x total_expenses must never render as if they were
    // real percentages.
    render(<HowToHelp org={makeOrg({
      program_expenses: 18_000_000,
      management_expenses: 15_900_000,
      fundraising_expenses: 178_600,
      total_expenses: 17_950_000,
      program_expense_pct: 89,
    })} />)
    expect(screen.queryByText(/Where your money goes/)).not.toBeInTheDocument()
  })

  it('shows the expense breakdown when parts reconcile with total_expenses', () => {
    render(<HowToHelp org={makeOrg({
      program_expenses: 800_000,
      management_expenses: 150_000,
      fundraising_expenses: 50_000,
      total_expenses: 1_000_000,
      program_expense_pct: 80,
    })} />)
    expect(screen.getByText(/Where your money goes/)).toBeInTheDocument()
    expect(screen.getByText('80%')).toBeInTheDocument()
  })
})
