import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useGivingList } from '../hooks/useGivingList'
import { submitLinkFeedback } from '../data/api'

/**
 * LinkedIn-jobs pattern: after the donor clicks an external give link and
 * comes back, ask "did you give?" — yes moves it to the Given (tax) records,
 * "not yet" leaves it as an ongoing intent. MERIT never sees the money.
 *
 * Mounted once at app root. Triggers when the MERIT tab regains focus (the
 * donor returned from the org's site) or on a later visit.
 */
export default function GiveConfirmPrompt() {
  const { pendingGive, confirmGiven, dismissPending } = useGivingList()
  const [show, setShow] = useState(false)
  const [showReasons, setShowReasons] = useState(false)
  const [savedConfirm, setSavedConfirm] = useState(false)
  const [gaveConfirm, setGaveConfirm] = useState(false)

  const maybeShow = useCallback((minAgeMs: number) => {
    if (!pendingGive) { setShow(false); return }
    const age = Date.now() - new Date(pendingGive.at).getTime()
    if (age >= minAgeMs) setShow(true)
  }, [pendingGive])

  useEffect(() => {
    // Returned from giving on the same session: focus/visibility, >3s since click.
    const onFocus = () => maybeShow(3000)
    const onVis = () => { if (document.visibilityState === 'visible') maybeShow(3000) }
    window.addEventListener('focus', onFocus)
    document.addEventListener('visibilitychange', onVis)
    // Came back in a later visit: a clearly-stale pending give.
    maybeShow(30000)
    return () => {
      window.removeEventListener('focus', onFocus)
      document.removeEventListener('visibilitychange', onVis)
    }
  }, [maybeShow])

  useEffect(() => {
    if (!show) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') { dismissPending(); setShow(false) } }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [show, dismissPending])

  if (!show || !pendingGive) return null

  const yes = () => {
    confirmGiven()
    setGaveConfirm(true)
    setTimeout(() => { setShow(false); setGaveConfirm(false) }, 1800)
  }
  const notYet = () => setShowReasons(true)
  const dismiss = () => { dismissPending(); setShow(false); setShowReasons(false); setSavedConfirm(false) }

  const saveThenDismiss = () => {
    // markPending already saved the org to the wallet when the give CTA was clicked,
    // so this is a visual confirmation rather than a new write. Brief flash then close.
    setSavedConfirm(true)
    setTimeout(() => { dismissPending(); setShow(false); setShowReasons(false); setSavedConfirm(false) }, 1600)
  }

  const reasons: { label: string; action: () => void }[] = [
    {
      label: "Couldn't find their donate page",
      action: () => { if (pendingGive) submitLinkFeedback(pendingGive.ein, 'not_found'); dismiss() },
    },
    {
      label: 'Site looked broken or off',
      action: () => { if (pendingGive) submitLinkFeedback(pendingGive.ein, 'broken'); dismiss() },
    },
    { label: "I'll give later", action: saveThenDismiss },
    { label: 'Changed my mind', action: dismiss },
  ]

  return (
    <div
      role="dialog"
      aria-label={`Did you give to ${pendingGive.orgName}?`}
      className="fixed bottom-5 left-1/2 -translate-x-1/2 z-[80] w-[calc(100%-2rem)] max-w-[420px]
                 rounded-2xl border border-soft-gold/30 bg-deep-navy shadow-2xl
                 px-6 py-5 animate-[fadeIn_0.25s_ease-out]"
    >
      {gaveConfirm ? (
        <div className="flex items-center gap-3">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
          <p className="font-display italic text-warm-cream text-[18px] leading-tight">
            Recorded in your Giving Wallet. Thank you.
          </p>
        </div>
      ) : savedConfirm ? (
        <div className="flex items-center gap-3">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C9A96E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
          <p className="font-display italic text-warm-cream text-[18px] leading-tight">
            Saved to your giving list
          </p>
        </div>
      ) : !showReasons ? (
        <>
          <p className="font-display italic text-warm-cream text-[20px] leading-tight">
            Did you give to {pendingGive.orgName}?
          </p>
          <p className="mt-2 font-body text-[13px] text-muted-cream/70 leading-[1.55]">
            We&rsquo;ll keep it in your Giving Wallet for your own tax records. MERIT never sees
            the gift and never shares it.
          </p>
          <div className="mt-4 flex items-center gap-3">
            <button
              onClick={yes}
              className="font-body text-[14px] font-semibold bg-soft-gold text-deep-navy px-5 py-2.5 rounded-full hover:bg-bright-gold transition-colors"
            >
              Yes, I gave
            </button>
            <button
              onClick={notYet}
              className="font-body text-[14px] text-muted-cream/80 hover:text-warm-cream transition-colors px-3 py-2.5"
            >
              Not yet
            </button>
            <Link
              to="/wallet"
              onClick={() => setShow(false)}
              className="ml-auto font-body text-[12px] text-soft-gold/80 hover:text-soft-gold transition-colors"
            >
              Open Wallet
            </Link>
          </div>
        </>
      ) : (
        <>
          <p className="font-display italic text-warm-cream text-[20px] leading-tight">
            What got in the way?
          </p>
          <p className="mt-1 font-body text-[13px] text-muted-cream/70">
            Helps us flag sites that need a fix. Nothing is tied to you.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {reasons.map(({ label, action }) => (
              <button
                key={label}
                onClick={action}
                className="font-body text-[13px] text-warm-cream border border-soft-gold/30 rounded-full px-4 py-2 hover:border-soft-gold hover:bg-soft-gold/10 transition-colors"
              >
                {label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

