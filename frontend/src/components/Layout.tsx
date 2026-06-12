import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Navigation from './Navigation'
import Footer from './Footer'
import BottomNav from './BottomNav'
import CompareBar from './CompareBar'
import BetaBanner from './BetaBanner'
import { trackPageview, trackDwell } from '../lib/analytics'

export default function Layout() {
  const location = useLocation()

  // Aggregate, privacy-first pageview tracking on every route change.
  useEffect(() => {
    trackPageview(location.pathname)
    return () => trackDwell(location.pathname)
  }, [location.pathname])

  // Hide footer on giving flow pages (cleaner confirmation UX)
  const hideFooter = ['/giving-list/review', '/giving-list/confirmation'].includes(location.pathname)

  return (
    <div className="min-h-[100dvh] flex flex-col">
      <BetaBanner />
      <Navigation solid />
      <main className="flex-1 pb-[60px] md:pb-0 pt-[36px]">
        <Outlet />
      </main>
      {!hideFooter && <Footer />}
      <CompareBar />
      <BottomNav />
    </div>
  )
}
