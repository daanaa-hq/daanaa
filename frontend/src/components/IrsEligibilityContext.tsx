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

import React, { useEffect, useRef, useState } from 'react';

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
    // Copy reworked 2026-08-08 (founder-approved). Lead with the reassurance:
    // every org we list is IRS deductibility code 1 and absent from the daily
    // Auto-Revocation sync, so hedging language ("not verified") was describing
    // a gap in our own data while reading as an accusation about the nonprofit.
    verified: { icon: '✓', label: 'Tax deductible', color: 'irs-badge-verified' },
    unverified: { icon: '✓', label: 'Tax deductible', color: 'irs-badge-verified' },
    revoked: { icon: '✗', label: 'IRS revocation record found', color: 'irs-badge-revoked' },
    // Reworked 2026-08-09: this used to share the reassuring "Tax deductible"
    // treatment above, on the reasoning that every listed org is already
    // deductibility-code 1. That held when 'unknown' meant only-Daanaa's-own-
    // check-is-pending. After migrating off the dead irs_eligibility_status
    // field to org.tax_deductible, 'unknown' now means we have no computed
    // signal at all for this org (a genuine data gap, most often the search.db
    // fallback path — which is specifically where revoked orgs' pages live).
    // Reassuring copy on that path is exactly backwards.
    unknown: { icon: 'ℹ', label: 'Tax status not available', color: 'irs-badge-exception' },
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
    // Plain language, sourced and dated. We say what IRS records show and when
    // we last checked, not what will happen on the donor's own tax return.
    verified: 'The IRS lists donations to this nonprofit as tax deductible. IRS status checked nightly; this organization is not on the IRS auto-revocation list.',
    unverified: 'The IRS lists donations to this nonprofit as tax deductible. IRS status checked nightly; this organization is not on the IRS auto-revocation list.',
    revoked: 'Do not assume a contribution is tax deductible without confirming the current IRS status.',
    unknown: 'We do not have current IRS deductibility data for this organization. Confirm directly with the organization or IRS before assuming a contribution is tax deductible.',
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
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    dialogRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onCancel();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  const warningConfig = {
    unverified: {
      title: "Tax Deductibility Not Verified",
      message: `Daanaa does not have complete current IRS evidence for ${organizationName || "this organization"}.`,
      details: [
        "We cannot confirm whether donations are tax-deductible",
        "You should verify directly with the organization or IRS",
        "Keep your own records of the donation for tax purposes",
      ],
    },
    unknown: {
      title: "Tax Status Not Verified",
      message: "We do not have complete current IRS evidence for this organization.",
      details: [
        "We cannot verify the current tax status",
        "Check with the organization directly",
        "Keep your own records of any donation",
      ],
    },
    revoked: {
      title: "IRS Revocation Record Found",
      message: `${organizationName || "This organization"} appears on the IRS auto-revocation list.`,
      details: [
        "Donations made after the revocation date are NOT tax-deductible",
        "Check the organization directly for reinstatement status",
        "You may be able to donate to an updated organization",
      ],
    },
  };

  const config = warningConfig[status as "unverified" | "unknown" | "revoked"];
  if (!config) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" role="presentation" onMouseDown={onCancel}>
      <div
        ref={dialogRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="irs-warning-title"
        aria-describedby="irs-warning-message"
        className="irs-modal rounded-lg p-6 max-w-md w-full mx-4"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <h2 id="irs-warning-title" className="text-lg font-bold mb-2 irs-modal-title">{config.title}</h2>
        <p id="irs-warning-message" className="text-sm mb-4 irs-modal-message">{config.message}</p>
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
            type="button"
            onClick={onCancel}
            className="flex-1 px-4 py-2 irs-modal-cancel rounded font-medium transition"
          >
            Cancel
          </button>
          <button
            type="button"
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
