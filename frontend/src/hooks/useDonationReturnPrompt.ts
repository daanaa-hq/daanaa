import { useCallback, useEffect, useRef, useState } from 'react'

// Closes the loop: the only time a donor leaves daanaa.org is to give on the
// org's own processor (Daanaa never touches funds). When they come back to
// this tab, ask once -- "did you give?" -- and if yes, hand off to the
// existing DonationLogger/logDonation flow (frontend/src/contexts/WalletContext.tsx).
// This is a self-reported intent log, never a transaction record -- Daanaa has
// no way to know if money actually moved, and must not imply otherwise.
//
// Design doc: STEWARDSHIP.md P8 ("Add to Giving Wallet prompt after the
// hand-off is a planned UX improvement to close the loop without touching
// funds"). Scope locked 2026-07-10: Donate clicks only, not Website/Volunteer
// (a Website click is usually just browsing -- "did you give?" would be
// wrong most of the time).
//
//   trackDonateClick(ein, name)
//     |  (user's browser opens the donate link in a new tab; this tab stays
//     |   mounted the whole time since target="_blank" doesn't navigate away)
//     v
//   document visibilitychange -> 'visible', >= MIN_AWAY_MS since click
//     |
//     v
//   promptState = { ein, name }  -- caller renders the "did you give?" bar
//     |
//     +-- dismiss()        -> promptState = null, no log
//     +-- (caller logs via useWallet().logDonation, then calls dismiss())

const MIN_AWAY_MS = 3_000 // ignore instant switches back (e.g. popup blocked)
const SESSION_KEY = 'daanaa_pending_donate_prompt'

interface PendingClick {
  ein: string
  name: string
  clickedAt: number
}

export interface DonationReturnPromptState {
  ein: string
  name: string
}

export function useDonationReturnPrompt() {
  const [promptState, setPromptState] = useState<DonationReturnPromptState | null>(null)
  const pendingRef = useRef<PendingClick | null>(null)

  // Survive a full page reload while the donor is away (rare, but the tab
  // can get refreshed) by round-tripping through sessionStorage.
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(SESSION_KEY)
      if (raw) pendingRef.current = JSON.parse(raw) as PendingClick
    } catch {
      // ignore malformed/blocked storage
    }
  }, [])

  const trackDonateClick = useCallback((ein: string, name: string) => {
    const pending: PendingClick = { ein, name, clickedAt: Date.now() }
    pendingRef.current = pending
    try {
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(pending))
    } catch {
      // sessionStorage unavailable (private mode etc) -- in-memory ref still works
    }
  }, [])

  const dismiss = useCallback(() => {
    setPromptState(null)
    pendingRef.current = null
    try {
      sessionStorage.removeItem(SESSION_KEY)
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    function handleVisibilityChange() {
      if (document.visibilityState !== 'visible') return
      const pending = pendingRef.current
      if (!pending) return
      if (Date.now() - pending.clickedAt < MIN_AWAY_MS) return
      setPromptState({ ein: pending.ein, name: pending.name })
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [])

  return { trackDonateClick, promptState, dismiss }
}
