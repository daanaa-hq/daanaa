import { Outlet, useLocation } from 'react-router-dom'
import Navigation from './Navigation'
import Footer from './Footer'
import BottomNav from './BottomNav'
import CompareBar from './CompareBar'

export default function Layout() {
  const location = useLocation()

  // Hide footer on giving flow pages (cleaner confirmation UX)
  const hideFooter = ['/giving-list/review', '/giving-list/confirmation'].includes(location.pathname)

  return (
    <div className="min-h-[100dvh] flex flex-col">
      <Navigation solid />
      <main className="flex-1 pb-[60px] md:pb-0">
        <Outlet />
      </main>
      {!hideFooter && <Footer />}
      <CompareBar />
      <BottomNav />
    </div>
  )
}
