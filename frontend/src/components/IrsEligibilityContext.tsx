/**
 * IrsEligibilityContext — Reusable component for displaying IRS eligibility status
 *
 * Supports all 5 statuses:
 * - verified: Pub78 + BMF + not revoked
 * - unverified: BMF-only, not in Pub78
 * - revoked: IRS auto-revocation record found
 * - unknown: Manifest stale or missing
 * - exception_possible: Churches/group-ruling indicators
 */

import React, { useState } from 'react';
import type { ReactNode } from 'react';

type EligibilityStatus = 'verified' | 'unverified' | 'revoked' | 'unknown' | 'exception_possible';

interface IrsEligibilityContextProps {
  status: EligibilityStatus;
  checkedAt?: string | null;
  sources?: string[];
  explanation?: string;
  recordedAt?: string | null;
  organizationName?: string;
  showWarningBeforeDonate?: boolean;
  onConfirmDonate?: () => void;
}

/**
 * Badge component — compact status indicator
 */
export const IrsEligibilityBadge: React.FC<{ status: EligibilityStatus }> = ({ status }) => {
  const badgeConfig = {
    verified: { icon: '✓', label: 'IRS eligibility verified', color: 'irs-badge-verified' },
    unverified: { icon: '⚠', label: 'Tax deductibility not verified', color: 'irs-badge-unverified' },
    revoked: { icon: '✗', label: 'IRS revocation record found', color: 'irs-badge-revoked' },
    unknown: { icon: '?', label: 'Tax status not verified', color: 'irs-badge-unknown' },
    exception_possible: { icon: 'ℹ', label: 'IRS listing may not tell the whole story', color: 'irs-badge-exception' },
  };

  const config = badgeConfig[status];
  return (
    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded text-sm font-medium ${config.color}`}>
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </div>
  );
};

/**
 * Detail component — full explanation
 */
export const IrsEligibilityDetail: React.FC<{
  status: EligibilityStatus;
  explanation?: string;
  sources?: string[];
}> = ({ status, explanation, sources }) => {
  const defaultExplanations = {
    verified: 'Current IRS BMF, Publication 78, and revocation records support tax-deductible eligibility.',
    unverified: 'The latest IRS evidence does not include a complete verification. Check the IRS before giving.',
    revoked: 'Do not assume a contribution is tax-deductible without confirming the current IRS status.',
    unknown: 'We do not have complete current IRS evidence for a tax-deductibility statement.',
    exception_possible: 'Some eligible churches and group-ruling subordinates may not appear in Publication 78. Confirm directly with the organization or IRS.',
  };

  return (
    <div className="text-sm text-warm-cream irs-detail-text">
      <p className="mb-2">{explanation || defaultExplanations[status]}</p>
      {sources && sources.length > 0 && (
        <div className="text-xs text-muted-cream irs-detail-sources">
          <p className="font-semibold mb-1">Sources:</p>
          <ul className="list-disc pl-5">
            {sources.map((source, idx) => <li key={idx}>{source}</li>)}
          </ul>
        </div>
      )}
      <p className="text-xs text-muted-cream mt-2 irs-detail-footer">
        See IRS Publication 526 for rules on charitable contributions.
      </p>
    </div>
  );
};

/**
 * Disclaimer component — for wallet historical entries
 */
export const IrsEligibilityDisclaimer: React.FC<{
  recordedAt?: string | null;
  organizationName?: string;
}> = ({ recordedAt, organizationName }) => {
  return (
    <div className="irs-disclaimer">
      <p className="mb-2">
        Daanaa recorded this organization as not revoked on <strong>{recordedAt || 'an unknown date'}</strong>.
        This is not a tax receipt, a determination of deductibility, or proof that a donation occurred.
        See IRS Publication 526 for rules on charitable contributions.
      </p>
      <p className="text-xs">
        This is your giving intent, not a completed transaction. To make an actual donation, visit the organization's website directly.
      </p>
    </div>
  );
};

/**
 * Warning modal — shown before donation for unknown/unverified
 */
export const IrsEligibilityWarningModal: React.FC<{
  isOpen: boolean;
  status: EligibilityStatus;
  organizationName?: string;
  onConfirm: () => void;
  onCancel: () => void;
}> = ({ isOpen, status, organizationName, onConfirm, onCancel }) => {
  if (!isOpen) return null;

  const warningConfig = {
    unverified: {
      title: 'Tax Deductibility Not Verified',
      message: `Daanaa does not have complete current IRS evidence for ${organizationName || 'this organization'}.`,
      details: [
        'We cannot confirm whether donations are tax-deductible',
        'You should verify directly with the organization or IRS',
        'Keep your own records of the donation for tax purposes',
      ],
    },
    unknown: {
      title: 'Tax Status Not Verified',
      message: 'We do not have complete current IRS evidence for this organization.',
      details: [
        'We cannot verify the current tax status',
        'Check with the organization directly',
        'Keep your own records of any donation',
      ],
    },
    revoked: {
      title: 'IRS Revocation Record Found',
      message: `${organizationName || 'This organization'} appears on the IRS auto-revocation list.`,
      details: [
        'Donations made after the revocation date are NOT tax-deductible',
        'Check the organization directly for reinstatement status',
        'You may be able to donate to an updated organization',
      ],
    },
  };

  const config = warningConfig[status as 'unverified' | 'unknown' | 'revoked'];
  if (!config) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="irs-modal rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-lg font-bold mb-2 irs-modal-title">{config.title}</h2>
        <p className="text-sm mb-4 irs-modal-message">{config.message}</p>
        <div className="irs-modal-details rounded p-4 mb-6">
          <p className="text-sm font-semibold mb-2">This means:</p>
          <ul className="text-sm space-y-1">
            {config.details.map((detail, idx) => (
              <li key={idx} className="flex">
                <span className="mr-2">•</span>
                <span>{detail}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 irs-modal-cancel rounded font-medium transition"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 irs-modal-confirm text-white rounded font-medium transition"
          >
            Continue to Donate
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * Revoked warning — shown instead of donate button
 */
export const IrsEligibilityRevokedWarning: React.FC<{
  organizationName?: string;
  organizationWebsite?: string;
}> = ({ organizationName, organizationWebsite }) => {
  return (
    <div className="irs-revoked-warning rounded p-4 text-sm">
      <p className="font-semibold mb-2">IRS revocation record found</p>
      <p className="mb-3">
        Do not assume a contribution is tax-deductible without confirming the current IRS status.
      </p>
      {organizationWebsite && (
        <a
          href={organizationWebsite}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block px-4 py-2 irs-revoked-link text-white rounded font-medium transition"
        >
          Visit {organizationName || 'Organization'} Website
        </a>
      )}
    </div>
  );
};

/**
 * Hook to manage warning modal state for donation flows
 */
export const useIrsEligibilityWarning = (status: EligibilityStatus) => {
  const [showWarning, setShowWarning] = useState(false);

  const openWarning = () => {
    if (status === 'unverified' || status === 'unknown') {
      setShowWarning(true);
    }
  };

  return { showWarning, setShowWarning, openWarning };
};

/**
 * Main component — renders appropriate UI based on status
 */
export const IrsEligibilityContext: React.FC<IrsEligibilityContextProps> = ({
  status,
  checkedAt,
  sources,
  explanation,
  recordedAt,
  organizationName,
  showWarningBeforeDonate = false,
  onConfirmDonate,
}) => {
  const warning = useIrsEligibilityWarning(status);

  if (status === 'revoked') {
    return <IrsEligibilityRevokedWarning organizationName={organizationName} />;
  }

  return (
    <>
      <div className="space-y-3">
        <IrsEligibilityBadge status={status} />
        <IrsEligibilityDetail status={status} explanation={explanation} sources={sources} />
        {recordedAt && <IrsEligibilityDisclaimer recordedAt={recordedAt} organizationName={organizationName} />}
      </div>

      {showWarningBeforeDonate && (status === 'unverified' || status === 'unknown') && (
        <IrsEligibilityWarningModal
          isOpen={warning.showWarning}
          status={status}
          organizationName={organizationName}
          onConfirm={() => {
            warning.setShowWarning(false);
            onConfirmDonate?.();
          }}
          onCancel={() => warning.setShowWarning(false)}
        />
      )}
    </>
  );
};
