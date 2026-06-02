import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import { CompareProvider } from './contexts/CompareContext'

const Home = lazy(() => import('./pages/Home'))
const Directory = lazy(() => import('./pages/Directory'))
const CategoryPage = lazy(() => import('./pages/CategoryPage'))
const OrganizationDetail = lazy(() => import('./pages/OrganizationDetail'))
const ComparePage = lazy(() => import('./pages/ComparePage'))
const Legal = lazy(() => import('./pages/Legal'))
const HowItWorks = lazy(() => import('./pages/HowItWorks'))
const Wallet = lazy(() => import('./pages/Wallet'))
const ForNonprofits = lazy(() => import('./pages/ForNonprofits'))
const About = lazy(() => import('./pages/About'))
const GivingListPage = lazy(() => import('./pages/GivingListPage'))
const GivingReview = lazy(() => import('./pages/GivingReview'))
const GivingConfirmation = lazy(() => import('./pages/GivingConfirmation'))
const TiersPage = lazy(() => import('./pages/TiersPage'))
const GuidesPage = lazy(() => import('./pages/GuidesPage'))
const FAQPage = lazy(() => import('./pages/FAQPage'))
const Methodology = lazy(() => import('./pages/Methodology'))
const SectorHealth = lazy(() => import('./pages/SectorHealth'))
const AdminPage = lazy(() => import('./pages/AdminPage'))
const NotFound = lazy(() => import('./pages/NotFound'))
const ClaimVerify = lazy(() => import('./pages/ClaimVerify'))
const OrgClaimEditor = lazy(() => import('./pages/OrgClaimEditor'))
const Feedback = lazy(() => import('./pages/Feedback'))
const MeetInvisible = lazy(() => import('./pages/MeetInvisible'))

function PageLoader() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
    </div>
  )
}

export default function App() {
  return (
    <CompareProvider>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Home />} />
            <Route path="/directory" element={<Directory />} />
            <Route path="/category/:id" element={<CategoryPage />} />
            <Route path="/org/:id" element={<OrganizationDetail />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/legal" element={<Legal />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route path="/wallet" element={<Wallet />} />
            <Route path="/for-nonprofits" element={<ForNonprofits />} />
            <Route path="/about" element={<About />} />
            <Route path="/giving-list" element={<GivingListPage />} />
            <Route path="/giving-list/review" element={<GivingReview />} />
            <Route path="/giving-list/confirmation" element={<GivingConfirmation />} />
            <Route path="/tiers" element={<TiersPage />} />
            <Route path="/methodology" element={<Methodology />} />
            <Route path="/sector-health" element={<SectorHealth />} />
            <Route path="/guides" element={<GuidesPage />} />
            <Route path="/faq" element={<FAQPage />} />
            <Route path="/feedback" element={<Feedback />} />
          </Route>
          <Route path="/the-invisible-97" element={<MeetInvisible />} />
          <Route path="/invisible-preview" element={<MeetInvisible />} />
          <Route path="/claim/verify" element={<ClaimVerify />} />
          <Route path="/claim/edit" element={<OrgClaimEditor />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </CompareProvider>
  )
}
