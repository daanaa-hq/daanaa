import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import * as Sentry from '@sentry/react'

// Sentry — activate by setting VITE_SENTRY_DSN in .env.production
if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN as string,
    environment: import.meta.env.MODE,
    tracesSampleRate: 0.1,
    // Never capture user PII — wallet data stays on device, never in Sentry
    sendDefaultPii: false,
    integrations: [
      Sentry.browserTracingIntegration(),
    ],
    // Ignore known benign errors
    ignoreErrors: [
      'ResizeObserver loop limit exceeded',
      'Non-Error exception captured',
    ],
  })
}

// Register service worker for offline app shell
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js', { scope: '/' })
      .catch(() => { /* SW registration is best-effort */ });
  });
}
import '@fontsource/playfair-display/400.css'
import '@fontsource/playfair-display/400-italic.css'
import '@fontsource/inter/400.css'
import '@fontsource/inter/500.css'
import '@fontsource/inter/600.css'
import '@fontsource/inter/700.css'
import './index.css'
import App from './App.tsx'
import { GivingListProvider } from './contexts/GivingListContext'
import { WalletProvider } from './contexts/WalletContext'
import ScrollToTop from './components/ScrollToTop'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <WalletProvider>
        <GivingListProvider>
          <ScrollToTop />
          <App />
        </GivingListProvider>
      </WalletProvider>
    </BrowserRouter>
  </StrictMode>,
)
