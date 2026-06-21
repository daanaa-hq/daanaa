import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import { ErrorBoundary } from './components/ErrorBoundary'
import { CompareProvider } from './contexts/CompareContext'
import { AuthProvider } from './contexts/AuthContext'
import NonprofitRoute from './components/NonprofitRoute'

const Home = lazy(() => import('./pages/Home'))
const Directory = lazy(() => import('./pages/Directory'))
const CategoryPage = lazy(() => import('./pages/CategoryPage'))
const OrganizationDetail = lazy(() => import('./pages/OrganizationDetail'))
const ComparePage = lazy(() => import('./pages/ComparePage'))
const Legal = lazy(() => import('./pages/Legal'))
const HowItWorks = lazy(() => import('./pages/HowItWorks'))
const WalletPage = lazy(() => import('./pages/WalletPage'))
const NonprofitVerification = lazy(() => import('./pages/NonprofitVerification'))
const ForNonprofits = lazy(() => import('./pages/ForNonprofits'))
// const GivingListPage = lazy(() => import('./pages/GivingListPage'))  // Giving List feature hidden
// const GivingReview = lazy(() => import('./pages/GivingReview'))  // Giving List feature hidden
// const GivingConfirmation = lazy(() => import('./pages/GivingConfirmation'))  // Giving List feature hidden
const TiersPage = lazy(() => import('./pages/TiersPage'))
const CauseSpotlight = lazy(() => import('./pages/CauseSpotlight'))
const Methodology = lazy(() => import('./pages/Methodology2'))
const SectorHealth = lazy(() => import('./pages/SectorHealth'))
const AdminPage = lazy(() => import('./pages/AdminPage'))
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
const NonprofitDashboard = lazy(() => import('./pages/NonprofitDashboard'))
const NonprofitLogin = lazy(() => import('./pages/nonprofit/NonprofitLogin'))
const MyOrgsPage = lazy(() => import('./pages/nonprofit/MyOrgsPage'))
const NonprofitDashboardPage = lazy(() => import('./pages/nonprofit/NonprofitDashboardPage'))
const Partners = lazy(() => import('./pages/Partners'))
const PartnerDetail = lazy(() => import('./pages/PartnerDetail'))
const VendorLoginPage = lazy(() => import('./pages/vendor/VendorLoginPage'))
const VendorDashboardPage = lazy(() => import('./pages/vendor/VendorDashboardPage'))

function PageLoader() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
    </div>
  )
}

function WalletSyncBridge() {
  // Wallet sync bridge — placeholder for future server sync functionality
  return null
}

export default function App() {
  return (
    <ErrorBoundary>
    <AuthProvider>
    <WalletSyncBridge />
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
            <Route path="/wallet" element={<WalletPage />} />
            <Route path="/giving-wallet" element={<Navigate to="/wallet" replace />} />
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
            <Route path="/partners/:vendor_id" element={<PartnerDetail />} />
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
          <Route path="/nonprofit/verify-hours" element={<NonprofitVerification />} />
          <Route path="/nonprofit/login" element={<NonprofitLogin />} />
          <Route element={<NonprofitRoute />}>
            <Route path="/nonprofit/my-orgs" element={<MyOrgsPage />} />
            <Route path="/nonprofit/dashboard/:ein" element={<NonprofitDashboardPage />} />
          </Route>
          <Route path="/vendor/login" element={<VendorLoginPage />} />
          <Route path="/vendor/dashboard" element={<VendorDashboardPage />} />
          <Route path="/claim/verify" element={<ClaimVerify />} />
          <Route path="/claim/edit" element={<OrgClaimEditor />} />
          <Route path="/claim/success" element={<ClaimSuccess />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </CompareProvider>
    </AuthProvider>
    </ErrorBoundary>
  )
}
