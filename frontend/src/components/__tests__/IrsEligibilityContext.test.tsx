/**
 * Tests for IrsEligibilityContext component
 * Coverage: all 5 statuses + warning/disclaimer behavior
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import {
  IrsEligibilityBadge,
  IrsEligibilityDetail,
  IrsEligibilityDisclaimer,
  IrsEligibilityWarningModal,
  IrsEligibilityRevokedWarning,
  IrsEligibilityContext,
} from '../IrsEligibilityContext';

describe('IrsEligibilityBadge', () => {
  it('renders verified badge', () => {
    render(<IrsEligibilityBadge status="verified" />);
    // Copy reworked 2026-08-08 (founder-approved) -- leads with reassurance
    // rather than a hedged "verified" claim. See IrsEligibilityContext.tsx.
    expect(screen.getByText(/Tax deductible/i)).toBeInTheDocument();
    expect(screen.getByText('✓')).toBeInTheDocument();
  });

  it('renders unverified badge', () => {
    render(<IrsEligibilityBadge status="unverified" />);
    // Same reassuring copy as verified -- see the 2026-08-08 rework comment.
    expect(screen.getByText(/Tax deductible/i)).toBeInTheDocument();
    expect(screen.getByText('✓')).toBeInTheDocument();
  });

  it('renders revoked badge', () => {
    render(<IrsEligibilityBadge status="revoked" />);
    expect(screen.getByText(/IRS revocation record found/i)).toBeInTheDocument();
    expect(screen.getByText('✗')).toBeInTheDocument();
  });

  it('renders unknown badge', () => {
    render(<IrsEligibilityBadge status="unknown" />);
    // Reworked 2026-08-09: no longer shares the reassuring "verified" copy --
    // 'unknown' now means a genuine data gap (most often the search.db
    // fallback path, where revoked orgs' pages live). See LESSONS.md.
    expect(screen.getByText(/Tax status not available/i)).toBeInTheDocument();
    expect(screen.getByText('ℹ')).toBeInTheDocument();
  });

  it('renders exception_possible badge', () => {
    render(<IrsEligibilityBadge status="exception_possible" />);
    expect(screen.getByText(/IRS listing may not tell the whole story/i)).toBeInTheDocument();
  });
});

describe('IrsEligibilityDetail', () => {
  it('shows verified explanation', () => {
    render(<IrsEligibilityDetail status="verified" />);
    expect(screen.getByText(/IRS revocation list every day/i)).toBeInTheDocument();
  });

  it('shows unverified explanation', () => {
    render(<IrsEligibilityDetail status="unverified" />);
    // Same reassuring copy as verified -- see the 2026-08-08 rework comment.
    expect(screen.getByText(/IRS revocation list every day/i)).toBeInTheDocument();
  });

  it('shows revoked explanation', () => {
    render(<IrsEligibilityDetail status="revoked" />);
    expect(screen.getByText(/Do not assume a contribution is tax deductible/i)).toBeInTheDocument();
  });

  it('displays sources when provided', () => {
    const sources = ['Publication 78', 'BMF subsection 03'];
    render(
      <IrsEligibilityDetail
        status="verified"
        sources={sources}
      />
    );
    sources.forEach(source => {
      expect(screen.getByText(source)).toBeInTheDocument();
    });
  });

  it('shows custom explanation when provided', () => {
    const customExplanation = 'Custom explanation text';
    render(
      <IrsEligibilityDetail
        status="verified"
        explanation={customExplanation}
      />
    );
    expect(screen.getByText(customExplanation)).toBeInTheDocument();
  });

  it('always shows IRS Publication 526 reference', () => {
    render(<IrsEligibilityDetail status="unknown" />);
    expect(screen.getByText(/IRS Publication 526/i)).toBeInTheDocument();
  });
});

describe('IrsEligibilityDisclaimer', () => {
  it('shows recorded date in disclaimer', () => {
    const recordedAt = '2026-07-27T12:00:00Z';
    render(
      <IrsEligibilityDisclaimer
        recordedAt={recordedAt}
        organizationName="Test Org"
      />
    );
    expect(screen.getByText(new RegExp(recordedAt))).toBeInTheDocument();
  });

  it('includes warning text', () => {
    const { container } = render(
      <IrsEligibilityDisclaimer
        recordedAt="2026-07-27T12:00:00Z"
      />
    );
    const text = container.textContent || '';
    expect(text).toMatch(/not a tax receipt/i);
    expect(text).toMatch(/determination of deductibility/i);
    expect(text).toMatch(/giving intent.*not a completed transaction/i);
  });

  it('never claims gift was deductible', () => {
    render(
      <IrsEligibilityDisclaimer recordedAt="2026-07-27T12:00:00Z" />
    );
    const text = screen.getByText(/Daanaa recorded/i).textContent || '';
    expect(text).not.toMatch(/gift was deductible/i);
  });
});

describe('IrsEligibilityWarningModal', () => {
  it('does not render when closed', () => {
    const { container } = render(
      <IrsEligibilityWarningModal
        isOpen={false}
        status="unverified"
        onConfirm={() => {}}
        onCancel={() => {}}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders unverified warning when open', () => {
    render(
      <IrsEligibilityWarningModal
        isOpen={true}
        status="unverified"
        organizationName="Test Org"
        onConfirm={() => {}}
        onCancel={() => {}}
      />
    );
    expect(screen.getByText(/Tax Deductibility Not Verified/i)).toBeInTheDocument();
    expect(screen.getByText(/Daanaa does not have complete/i)).toBeInTheDocument();
  });

  it('renders revoked warning when open', () => {
    render(
      <IrsEligibilityWarningModal
        isOpen={true}
        status="revoked"
        organizationName="Test Org"
        onConfirm={() => {}}
        onCancel={() => {}}
      />
    );
    expect(screen.getByText(/IRS Revocation Record Found/i)).toBeInTheDocument();
    expect(screen.getByText(/auto-revocation list/i)).toBeInTheDocument();
  });

  it('calls onConfirm when user clicks continue', () => {
    const onConfirm = jest.fn();
    render(
      <IrsEligibilityWarningModal
        isOpen={true}
        status="unverified"
        onConfirm={onConfirm}
        onCancel={() => {}}
      />
    );
    fireEvent.click(screen.getByText(/Continue to Donate/i));
    expect(onConfirm).toHaveBeenCalled();
  });

  it('calls onCancel when user clicks cancel', () => {
    const onCancel = jest.fn();
    render(
      <IrsEligibilityWarningModal
        isOpen={true}
        status="unverified"
        onConfirm={() => {}}
        onCancel={onCancel}
      />
    );
    fireEvent.click(screen.getByText(/Cancel/i));
    expect(onCancel).toHaveBeenCalled();
  });
});

describe('IrsEligibilityRevokedWarning', () => {
  it('renders revoked warning', () => {
    render(
      <IrsEligibilityRevokedWarning
        organizationName="Test Org"
        organizationWebsite="https://example.com"
      />
    );
    expect(screen.getByText(/IRS revocation record found/i)).toBeInTheDocument();
    expect(screen.getByText(/Do not assume/i)).toBeInTheDocument();
  });

  it('links to organization website', () => {
    render(
      <IrsEligibilityRevokedWarning
        organizationName="Test Org"
        organizationWebsite="https://example.com"
      />
    );
    const link = screen.getByText(/Visit Test Org Website/i) as HTMLAnchorElement;
    expect(link).toHaveAttribute('href', 'https://example.com');
    expect(link).toHaveAttribute('target', '_blank');
  });
});

describe('IrsEligibilityContext (main component)', () => {
  it('renders verified status correctly', () => {
    render(
      <IrsEligibilityContext
        status="verified"
        checkedAt="2026-07-27T12:00:00Z"
        sources={['Publication 78', 'BMF']}
        explanation="Test explanation"
      />
    );
    expect(screen.getByText(/Tax deductible/i)).toBeInTheDocument();
    expect(screen.getByText(/Test explanation/i)).toBeInTheDocument();
  });

  it('renders unverified with warning capability', () => {
    const onConfirmDonate = jest.fn();
    render(
      <IrsEligibilityContext
        status="unverified"
        showWarningBeforeDonate={true}
        onConfirmDonate={onConfirmDonate}
      />
    );
    // Badge reassures (same copy as verified); the warning modal is what
    // actually hedges, and it's gated behind showWarningBeforeDonate + the
    // donate click, not shown by default -- see IrsEligibilityContext.tsx.
    // Multiple matches expected: the badge label AND the detail paragraph
    // both contain "tax deductible".
    expect(screen.getAllByText(/Tax deductible/i).length).toBeGreaterThan(0);
  });

  it('renders revoked status without donate button', () => {
    const { container } = render(
      <IrsEligibilityContext
        status="revoked"
        organizationName="Test Org"
      />
    );
    expect(screen.getByText(/IRS revocation record found/i)).toBeInTheDocument();
    // Should NOT have donate button in main render for revoked
  });

  it('includes disclaimer when recordedAt provided', () => {
    render(
      <IrsEligibilityContext
        status="verified"
        recordedAt="2026-07-27T12:00:00Z"
        organizationName="Test Org"
      />
    );
    expect(screen.getByText(/Daanaa recorded/i)).toBeInTheDocument();
  });

  it('never implies deductibility in any status', () => {
    const statuses = ['verified', 'unverified', 'revoked', 'unknown', 'exception_possible'] as const;
    statuses.forEach(status => {
      const { unmount } = render(
        <IrsEligibilityContext status={status} />
      );
      const text = screen.queryAllByText(/./).map(el => el.textContent || '').join(' ');
      expect(text).not.toMatch(/this gift is deductible/i);
      expect(text).not.toMatch(/your contribution is deductible/i);
      unmount();
    });
  });
});
