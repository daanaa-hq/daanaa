import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import { CompareProvider } from './contexts/CompareContext'
import { AuthProvider } from './contexts/AuthContext'

const Home = lazy(() => import('./pages/Home'))
const Directory = lazy(() => import('./pages/Directory'))
const CategoryPage = lazy(() => import('./pages/CategoryPage'))
const OrganizationDetail = lazy(() => import('./pages/OrganizationDetail'))
const ComparePage = lazy(() => import('./pages/ComparePage'))
const Legal = lazy(() => import('./pages/Legal'))
const HowItWorks = lazy(() => import('./pages/HowItWorks'))
const Wallet = lazy(() => import('./pages/Wallet'))
const ForNonprofits = lazy(() => import('./pages/ForNonprofits'))
// const GivingListPage = lazy(() => import('./pages/GivingListPage'))  // Giving List feature hidden
// const GivingReview = lazy(() => import('./pages/GivingReview'))  // Giving List feature hidden
// const GivingConfirmation = lazy(() => import('./pages/GivingConfirmation'))  // Giving List feature hidden
const TiersPage = lazy(() => import('./pages/TiersPage'))
const CauseSpotlight = lazy(() => import('./pages/CauseSpotlight'))
const Methodology = lazy(() => import('./pages/Methodology2'))
const SectorHealth = lazy(() => import('./pages/SectorHealth'))
const AdminPage = lazy(() => import('./pages/AdminPage'))
const Partners = lazy(() => import('./pages/Partners'))
const NotFound = lazy(() => import('./pages/NotFound'))
const Learn = lazy(() => import('./pages/Learn'))
const About = lazy(() => import('./pages/About'))
const Principles = lazy(() => import('./pages/Principles'))
const ClaimVerify = lazy(() => import('./pages/ClaimVerify'))
const OrgClaimEditor = lazy(() => import('./pages/OrgClaimEditor'))
const ClaimSuccess = lazy(() => import('./pages/ClaimSuccess'))
const ForVendors = lazy(() => import('./pages/ForVendors'))
const VendorPolicy = lazy(() => import('./pages/VendorPolicy'))
const Terms = lazy(() => import('./pages/Terms'))
const GuildReferral = lazy(() => import('./pages/GuildReferral'))
const MemberBenefits = lazy(() => import('./pages/MemberBenefits'))
const VolunteerSearch = lazy(() => import('./pages/VolunteerSearch'))
const Feedback = lazy(() => import('./pages/Feedback'))
const MeetInvisible = lazy(() => import('./pages/MeetInvisible'))
const ResearchDashboard = lazy(() => import('./pages/ResearchDashboard'))

function PageLoader() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
    <CompareProvider>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Home />} />
            <Route path="/directory" element={<Directory />} />
            <Route path="/category/:id" element={<CategoryPage />} />
            <Route path="/causes/:id" element={<CauseSpotlight />} />
            <Route path="/org/:id" element={<OrganizationDetail />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/legal" element={<Legal />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route path="/wallet" element={<Wallet />} />
            <Route path="/for-nonprofits" element={<ForNonprofits />} />
            <Route path="/about" element={<About />} />
            <Route path="/principles" element={<Principles />} />
            {/* Legacy routes for backward compatibility */}
            <Route path="/governance" element={<Principles />} />
            <Route path="/stewardship" element={<Principles />} />
            <Route path="/why-daanaa-exists" element={<About />} />
            {/* <Route path="/giving-list" element={<GivingListPage />} /> */}
            {/* <Route path="/giving-list/review" element={<GivingReview />} /> */}
            {/* <Route path="/giving-list/confirmation" element={<GivingConfirmation />} /> */}
            <Route path="/tiers" element={<TiersPage />} />
            <Route path="/methodology" element={<Methodology />} />
            <Route path="/sector-health" element={<SectorHealth />} />
            <Route path="/learn" element={<Learn />} />
            {/* Legacy routes for backward compatibility */}
            <Route path="/guides" element={<Learn />} />
            <Route path="/faq" element={<Learn />} />
            <Route path="/feedback" element={<Feedback />} />
            <Route path="/partners" element={<Partners />} />
            <Route path="/for-vendors" element={<ForVendors />} />
            <Route path="/vendor-policy" element={<VendorPolicy />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/guild/:slug" element={<GuildReferral />} />
            <Route path="/member/benefits" element={<MemberBenefits />} />
            <Route path="/volunteer" element={<VolunteerSearch />} />
          </Route>
          <Route path="/the-invisible-97" element={<MeetInvisible />} />
          <Route path="/invisible-preview" element={<MeetInvisible />} />
          <Route path="/research" element={<ResearchDashboard />} />
          <Route path="/claim/verify" element={<ClaimVerify />} />
          <Route path="/claim/edit" element={<OrgClaimEditor />} />
          <Route path="/claim/success" element={<ClaimSuccess />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </CompareProvider>
    </AuthProvider>
  )
}
