import { useEffect, useState } from 'react'
import { useWallet } from '../contexts/WalletContext'
import { useStandalone } from '../hooks/useStandalone'

// Ask-once install nudge. Shows only when: the browser offers install
// (beforeinstallprompt), the user has saved at least one org (a meaningful
// moment — never on first landing), we're not already installed, and it
// hasn't been dismissed before. Dismissal is permanent (localStorage) —
// nagging donors to install is exactly the pressure P5 prohibits.
const LS_DISMISSED = 'daanaa_install_dismissed'

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export default function InstallPrompt() {
  const { entries } = useWallet()
  const standalone = useStandalone()
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null)
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem(LS_DISMISSED) === '1'
  )

  useEffect(() => {
    const onPrompt = (e: Event) => {
      e.preventDefault()
      setDeferred(e as BeforeInstallPromptEvent)
    }
    window.addEventListener('beforeinstallprompt', onPrompt)
    return () => window.removeEventListener('beforeinstallprompt', onPrompt)
  }, [])

  if (standalone || dismissed || !deferred || entries.length === 0) return null

  const dismiss = () => {
    localStorage.setItem(LS_DISMISSED, '1')
    setDismissed(true)
  }

  return (
    <div className="fixed bottom-[68px] left-3 right-3 z-40 md:hidden bg-deep-navy text-warm-cream rounded-2xl px-5 py-4 shadow-xl flex items-center gap-3"
      style={{ marginBottom: 'env(safe-area-inset-bottom, 0px)' }}>
      <div className="flex-1">
        <p className="font-body text-[14px] font-semibold">Keep Daanaa on your home screen</p>
        <p className="font-body text-[12px] opacity-80 mt-0.5">Your saved orgs, one tap away — works offline too.</p>
      </div>
      <button
        onClick={async () => {
          await deferred.prompt()
          const choice = await deferred.userChoice
          if (choice.outcome === 'dismissed') dismiss()
          setDeferred(null)
        }}
        className="px-4 py-2.5 rounded-xl bg-soft-gold text-deep-navy font-body text-[13px] font-semibold"
      >
        Add
      </button>
      <button onClick={dismiss} aria-label="Dismiss install prompt"
        className="w-8 h-8 flex items-center justify-center rounded-full text-warm-cream/70 hover:text-warm-cream">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
  )
}
