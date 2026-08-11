import { initializeApp, getApps } from 'firebase/app'
import { getAuth } from 'firebase/auth'

const firebaseConfig = {
  apiKey:     import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId:  import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId:      import.meta.env.VITE_FIREBASE_APP_ID,
}

const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0]
export const auth = getAuth(app)

// Analytics via Plausible (privacy-first, no third-party tracking)
// Stewardship P2 aligned: no cookies, no advertising profiles, aggregate only
export function logEvent(eventName: string, eventParams?: Record<string, any>) {
  if (typeof window !== 'undefined' && window.plausible) {
    try {
      window.plausible(eventName, { props: eventParams })
    } catch (e) {
      console.debug('Plausible event logging failed:', e instanceof Error ? e.message : e)
    }
  }
}
