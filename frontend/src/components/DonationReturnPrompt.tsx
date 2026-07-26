import DonationLogger from './DonationLogger'
import type { DonationReturnPromptState } from '../hooks/useDonationReturnPrompt'

// The popup shown when a donor returns to the org page tab after clicking
// Donate. Self-reported intent only -- Daanaa has no way to confirm money
// actually moved and must never imply that it does. See
// hooks/useDonationReturnPrompt.ts for the trigger design.
export interface DonationReturnPromptProps {
  state: DonationReturnPromptState
  onDismiss: () => void
  onLogged: (amount?: number) => void
}

export default function DonationReturnPrompt({ state, onDismiss, onLogged }: DonationReturnPromptProps) {
  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4"
      onClick={onDismiss}
    >
      <div
        role="dialog"
        aria-label={`Log your donation to ${state.name}`}
        onClick={e => e.stopPropagation()}
        className="w-full sm:max-w-md sm:rounded-2xl rounded-t-2xl bg-white overflow-hidden"
      >
        <div className="px-6 pt-6 pb-2 flex items-start justify-between">
          <div>
            <p className="font-display text-lg italic text-deep-navy">Did you give to {state.name}?</p>
            <p className="font-body text-small text-cool-grey mt-1">
              We can't see what happens on their site — this just helps you track your own giving.
            </p>
          </div>
          <button
            onClick={onDismiss}
            aria-label="Dismiss"
            className="text-cool-grey hover:text-deep-navy transition-colors p-1.5 shrink-0"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
          </button>
        </div>
        <div className="px-6 pb-6">
          <DonationLoggerWithDismiss ein={state.ein} orgName={state.name} onLogged={onLogged} onSkip={onDismiss} />
        </div>
      </div>
    </div>
  )
}

// DonationLogger has its own internal success state but no onSuccess callback
// -- wrap it so the return-prompt can close itself once logging succeeds,
// and offer a "not now" skip that doesn't touch the wallet at all.
function DonationLoggerWithDismiss({ ein, orgName, onLogged, onSkip }: { ein: string; orgName: string; onLogged: (amount?: number) => void; onSkip: () => void }) {
  return (
    <div>
      <DonationLogger ein={ein} orgName={orgName} onLogged={onLogged} />
      <div className="flex gap-3 mt-2">
        <button
          onClick={onSkip}
          className="font-body text-small text-cool-grey hover:text-deep-navy transition-colors underline underline-offset-2"
        >
          Not now
        </button>
        <button
          onClick={() => onLogged()}
          className="font-body text-small text-cool-grey hover:text-deep-navy transition-colors underline underline-offset-2 ml-auto"
        >
          Done
        </button>
      </div>
    </div>
  )
}
