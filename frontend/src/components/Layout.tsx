import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Navigation from './Navigation'
import Footer from './Footer'
import BottomNav from './BottomNav'
import CompareBar from './CompareBar'
import BetaBanner from './BetaBanner'
import WalletAutoSave from './WalletAutoSave'
import { trackPageview, trackDwell } from '../lib/analytics'
import { useStandalone } from '../hooks/useStandalone'

export default function Layout() {
  const location = useLocation()
  // Installed-app posture: the bottom tab bar is the navigation; the website
  // sitemap footer is browser-tab chrome and stays out of the way. Every page
  // remains reachable (top nav + in-page links) — nothing is removed, only
  // the shell slims down.
  const standalone = useStandalone()

  // Aggregate, privacy-first pageview tracking on every route change.
  useEffect(() => {
    trackPageview(location.pathname)
    return () => trackDwell(location.pathname)
  }, [location.pathname])

  // Hide footer on giving flow pages (cleaner confirmation UX)
  const hideFooter = ['/giving-list/review', '/giving-list/confirmation'].includes(location.pathname)

  return (
    <div className="min-h-[100dvh] flex flex-col">
      <WalletAutoSave />
      <BetaBanner />
      <Navigation solid />
      <main className="flex-1 pb-[60px] md:pb-0 pt-[36px]">
        <Outlet />
      </main>
      {!hideFooter && !standalone && <Footer />}
      <CompareBar />
      <BottomNav />
    </div>
  )
}
