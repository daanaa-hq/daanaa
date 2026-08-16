/**
 * Tests for FinancialContext.
 *
 * Regression coverage for the 2026-08-08 bug: this component was checking
 * org.scoring_tier against '1_Direct_Regional' / '2_Regional_Inferred' /
 * '3_Limited_Context' -- a vocabulary that only ever existed on the separate,
 * disjoint scoring_tier_v6_inference column. org.scoring_tier's real values
 * (written by scripts/merit_scorer_v6_0.py) are '1_Full_Context' /
 * '2_Regional_Context' / '3_Broad_Category' / '4_Archetype_Only', so the
 * component silently rendered nothing for ~75% of organizations. These tests
 * pin the real vocabulary so that mismatch can't reappear unnoticed.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import FinancialContext from '../FinancialContext';
import type { ApiOrganization } from '../../data/api';

function makeOrg(overrides: Partial<ApiOrganization>): ApiOrganization {
  return {
    EIN: '123456789',
    organization_name: 'Test Org',
    ...overrides,
  } as ApiOrganization;
}

describe('FinancialContext', () => {
  it('renders nothing when scoring_tier, category, and revenue are all missing', () => {
    const { container } = render(<FinancialContext org={makeOrg({ scoring_tier: null })} />);
    expect(container).toBeEmptyDOMElement();
  });

  // 2026-08-16: 114,675 orgs (5.6% of the registry) have no scoring_tier --
  // verified as an eligibility/coverage gap in the v6 scorer's loader, not a
  // sign of financial weakness (see daanaa_scorer.py). Show category context
  // instead of a blank section, clearly labeled as not a peer score.
  it('renders category context, not a peer score, when the tier is missing', () => {
    render(
      <FinancialContext
        org={makeOrg({
          scoring_tier: null,
          NTEE1: 'P',
          total_revenue: 750_000,
        })}
      />
    );

    expect(screen.getByText('Category context')).toBeInTheDocument();
    // Text spans a <strong> tag ("A <strong>Human Services</strong> organization."),
    // so match on the bolded sector name rather than a regex across node boundaries.
    expect(screen.getByText('Human Services')).toBeInTheDocument();
    expect(screen.getByText(/\$750,000/)).toBeInTheDocument();
    expect(
      screen.getByText(/not a peer comparison or financial score/i)
    ).toBeInTheDocument();
  });

  it('renders revenue context without an NTEE category when the tier is missing', () => {
    render(
      <FinancialContext
        org={makeOrg({
          scoring_tier: null,
          NTEE1: null,
          total_revenue: 100_000,
        })}
      />
    );

    expect(screen.getByText('Category context')).toBeInTheDocument();
    expect(screen.getByText(/\$100,000/)).toBeInTheDocument();
  });

  it('renders nothing when tier, category, and positive revenue are all unavailable', () => {
    const { container } = render(
      <FinancialContext
        org={makeOrg({
          scoring_tier: null,
          NTEE1: null,
          total_revenue: null,
        })}
      />
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('renders the high-confidence card for 1_Full_Context', () => {
    render(
      <FinancialContext
        org={makeOrg({
          scoring_tier: '1_Full_Context',
          peer_group_size: 392,
          peer_group_description: 'Donation-Funded Programs, Established, Midwest region',
          months_of_reserve: 6.2,
          merit_archetype_v5_label: 'Donation-Funded Programs',
        })}
      />
    );
    expect(screen.getByText('Financial Context')).toBeInTheDocument();
    expect(screen.getByText('High confidence')).toBeInTheDocument();
    expect(screen.getByText('6.2 mo')).toBeInTheDocument();
  });

  it('renders the widened-comparison card for 2_Regional_Context using tier_label, not a peer count', () => {
    render(
      <FinancialContext
        org={makeOrg({
          scoring_tier: '2_Regional_Context',
          tier_label: 'Donation-Funded Programs, Small, national',
          merit_archetype_v5_label: 'Donation-Funded Programs',
        })}
      />
    );
    expect(screen.getByText('Financial Context (Broader Comparison)')).toBeInTheDocument();
    expect(screen.getByText('Donation-Funded Programs, Small, national')).toBeInTheDocument();
  });

  it('renders the broad-category card for 3_Broad_Category using tier_label, not a peer count', () => {
    render(
      <FinancialContext
        org={makeOrg({
          scoring_tier: '3_Broad_Category',
          tier_label: 'Donation-Funded Programs, all sizes',
          merit_archetype_v5_label: 'Donation-Funded Programs',
        })}
      />
    );
    expect(screen.getByText('Peer context (broader comparison)')).toBeInTheDocument();
    expect(screen.getByText(/Donation-Funded Programs, all sizes/)).toBeInTheDocument();
  });

  it('renders the descriptive-only card for 4_Archetype_Only with no peer group claim', () => {
    render(
      <FinancialContext
        org={makeOrg({
          scoring_tier: '4_Archetype_Only',
          peer_group_size: null,
          merit_archetype_v5_label: 'Donation-Funded Programs',
        })}
      />
    );
    expect(screen.getByText('Descriptive context only')).toBeInTheDocument();
  });

  it('never checks the retired scoring_tier_v6_inference vocabulary', () => {
    // A tier value that only exists in the disjoint _v6_inference pipeline
    // must not be treated as a valid scoring_tier.
    const { container } = render(
      <FinancialContext org={makeOrg({ scoring_tier: '1_Direct_Regional' as any })} />
    );
    expect(container).toBeEmptyDOMElement();
  });
});
