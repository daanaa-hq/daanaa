import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

/**
 * Protected route wrapper for the nonprofit portal.
 * Redirects to /nonprofit/login if the user is not Firebase-authenticated.
 *
 * Usage in App.tsx:
 *   <Route element={<NonprofitRoute />}>
 *     <Route path="/nonprofit/my-orgs" element={<MyOrgsPage />} />
 *     ...
 *   </Route>
 */
export default function NonprofitRoute() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-[100dvh] bg-warm-cream flex items-center justify-center">
        <div className="w-6 h-6 rounded-full border-2 border-soft-gold border-t-transparent animate-spin" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/nonprofit/login" replace />
  }

  return <Outlet />
}
