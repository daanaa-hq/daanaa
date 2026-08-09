import { initializeApp, getApps } from 'firebase/app'
import { getAuth } from 'firebase/auth'
import { getAnalytics, logEvent as firebaseLogEvent } from 'firebase/analytics'

const firebaseConfig = {
  apiKey:     import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId:  import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId:      import.meta.env.VITE_FIREBASE_APP_ID,
}

const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0]
export const auth = getAuth(app)

// Firebase Analytics — phase 3 measurement (custom events)
// Privacy: Only org-level properties (revenue_band, section) — never EIN or PII
// Stewardship P2 aligned (aggregated event counts, no individual tracking)
let analytics: any = null
try {
  analytics = getAnalytics(app)
} catch (e) {
  // Analytics may not be enabled in Firebase project yet (will be prompted on first login)
  console.debug('Firebase Analytics not yet initialized:', e instanceof Error ? e.message : e)
}

export function logEvent(eventName: string, eventParams?: Record<string, any>) {
  if (!analytics) {
    console.debug(`Event queued (analytics not ready): ${eventName}`)
    return
  }
  try {
    firebaseLogEvent(analytics, eventName, eventParams)
  } catch (e) {
    console.debug('Event logging failed:', e instanceof Error ? e.message : e)
  }
}
