import { Outlet, useLocation } from 'react-router-dom'
import Navigation from './Navigation'
import Footer from './Footer'
import BottomNav from './BottomNav'
import CompareBar from './CompareBar'
import BetaBanner from './BetaBanner'

export default function Layout() {
  const location = useLocation()

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
